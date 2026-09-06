"""
kb/parser/code_ingestor.py
Codebase scanner and ingestion coordinator for AppAI Hub.

Scans application source trees for:
  - Python files (.py) via PythonParser (AST-based)
  - CMake build files (CMakeLists.txt, *.cmake) via CMakeParser
  - Qt UI form files (.ui) via xml.etree.ElementTree

Extracts code structure, UI definitions, and workflows.
Inserts chunks into ChromaDB via KBRetriever and populates ManifestStore.
"""

import os
import re
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

from kb.parser.python_parser import PythonParser
from kb.parser.cmake_parser import CMakeParser

logger = logging.getLogger(__name__)

# Directories to skip when scanning source trees
_IGNORE_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", "venv", ".venv", "env",
    "node_modules", "build", "dist", ".vs", "CMakeFiles",
    ".idea", ".vscode", "bin", "obj", "cmake-build-debug", "cmake-build-release"
}


class CodeIngestor:
    """Scans and ingests project source code and build files into AppAI KB."""

    def __init__(self, kb_retriever=None, manifest_store=None):
        self.kb_retriever = kb_retriever
        self.manifest_store = manifest_store
        self.python_parser = PythonParser()
        self.cmake_parser = CMakeParser()

    async def ingest_directory(
        self,
        app_id: str,
        directory_path: str,
        max_files: int = 200,
    ) -> Dict[str, Any]:
        """
        Recursively scan directory_path, parse all recognized files,
        and add the resulting chunks to the app's knowledge base.
        """
        root = Path(directory_path)
        if not root.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")

        all_docs: List[Dict[str, Any]] = []
        files_processed = {
            "python": 0,
            "cmake": 0,
            "qt_ui": 0,
            "total_files": 0,
            "total_chunks": 0,
            "widgets_extracted": 0,
        }

        for current_root, dirs, files in os.walk(root):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in _IGNORE_DIRS and not d.startswith(".")]

            for file_name in files:
                if files_processed["total_files"] >= max_files:
                    logger.warning("CodeIngestor: Reached max_files limit (%d)", max_files)
                    break

                file_path = os.path.join(current_root, file_name)
                rel_path = os.path.relpath(file_path, root)

                # 1. Python source files
                if file_name.endswith(".py"):
                    docs = self.python_parser.parse_file(file_path)
                    for d in docs:
                        d["metadata"]["rel_path"] = rel_path
                    all_docs.extend(docs)
                    files_processed["python"] += 1
                    files_processed["total_files"] += 1

                # 2. CMakeLists.txt & *.cmake
                elif file_name == "CMakeLists.txt" or file_name.endswith(".cmake"):
                    docs = self.cmake_parser.parse_file(file_path)
                    for d in docs:
                        d["metadata"]["rel_path"] = rel_path
                    all_docs.extend(docs)
                    files_processed["cmake"] += 1
                    files_processed["total_files"] += 1

                # 3. Qt Designer UI XML files (*.ui)
                elif file_name.endswith(".ui"):
                    ui_docs, widgets = self._parse_qt_ui(file_path, rel_path, app_id)
                    all_docs.extend(ui_docs)
                    files_processed["qt_ui"] += 1
                    files_processed["total_files"] += 1
                    files_processed["widgets_extracted"] += len(widgets)

                    # Store widgets in manifest if store is available
                    if self.manifest_store and widgets:
                        for w in widgets:
                            try:
                                await self.manifest_store.upsert_widget(
                                    app_id=app_id,
                                    widget_id=w["widget_id"],
                                    label=w["label"],
                                    widget_type=w.get("widget_type", "widget"),
                                    screen=w.get("screen", ""),
                                    description=w.get("description", ""),
                                )
                            except Exception as ex:
                                logger.error("CodeIngestor: Failed to upsert widget %s: %s", w["widget_id"], ex)

        files_processed["total_chunks"] = len(all_docs)

        # Ingest into ChromaDB via KBRetriever
        if self.kb_retriever and all_docs:
            await self.kb_retriever.add_documents(app_id=app_id, documents=all_docs)
            logger.info(
                "CodeIngestor: Ingested %d chunks for app=%s from %s",
                len(all_docs), app_id, directory_path
            )

        return {
            "app_id": app_id,
            "directory": directory_path,
            "stats": files_processed
        }

    def _parse_qt_ui(self, file_path: str, rel_path: str, app_id: str):
        """Extract widgets and layout from Qt Designer .ui XML files."""
        docs = []
        widgets = []
        try:
            tree = ET.parse(file_path)
            ui_root = tree.getroot()

            screen_name = Path(file_path).stem
            ui_class = ui_root.find(".//class")
            if ui_class is not None and ui_class.text:
                screen_name = ui_class.text

            widget_descriptions = []

            # Scan all <widget> nodes
            for w_node in ui_root.iter("widget"):
                name = w_node.get("name", "")
                w_class = w_node.get("class", "QWidget")

                # Look for label / text property
                text = ""
                for prop in w_node.findall("./property"):
                    if prop.get("name") in ("text", "title", "windowTitle"):
                        str_elem = prop.find("string")
                        if str_elem is not None and str_elem.text:
                            text = str_elem.text.strip()
                            break

                if name and text:
                    widgets.append({
                        "widget_id": name,
                        "label": text,
                        "widget_type": w_class,
                        "screen": screen_name,
                        "description": f"{w_class} '{text}' on screen {screen_name}"
                    })
                    widget_descriptions.append(f"- {w_class} '{name}': \"{text}\"")

            content_lines = [
                f"Qt UI Screen: {screen_name} ({rel_path})",
                f"Contains {len(widgets)} interactive UI elements:"
            ]
            content_lines.extend(widget_descriptions[:30])

            docs.append({
                "content": "\n".join(content_lines),
                "metadata": {
                    "content_type": "ui_description",
                    "source": rel_path,
                    "screen": screen_name,
                    "kind": "qt_ui_form"
                }
            })

        except Exception as e:
            logger.warning("CodeIngestor: Could not parse UI file %s: %s", file_path, e)

        return docs, widgets
