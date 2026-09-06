"""
kb/parser/cmake_parser.py
CMakeLists.txt parser for AppAI Knowledge Base.

Extracts:
  - Project name & version (project(...))
  - Required packages & Qt modules (find_package(Qt5/Qt6 ...))
  - Executable and library targets (add_executable, add_library)
  - Target link libraries (target_link_libraries)
  - Qt UI form files referenced (*.ui)
  - CMAKE_AUTOMOC / CMAKE_AUTOUIC settings
  - Subdirectories (add_subdirectory)

Generates chunks tagged as:
  - content_type="source_code": Detailed build & linking structure (for developers)
  - content_type="ui_description": High-level architecture, executable name, UI files list
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class CMakeParser:
    """Parses CMakeLists.txt files into structured Knowledge Base chunks."""

    def __init__(self):
        pass

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a CMakeLists.txt file from disk."""
        path = Path(file_path)
        if not path.is_file():
            logger.warning("CMakeParser: File not found: %s", file_path)
            return []

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return self.parse_content(content, source_name=str(path))
        except Exception as e:
            logger.error("CMakeParser: Failed to read %s: %s", file_path, e)
            return []

    def parse_content(self, content: str, source_name: str = "CMakeLists.txt") -> List[Dict[str, Any]]:
        """Parse CMakeLists.txt content string into structured KB chunks."""
        # Strip comments for parsing commands
        clean_lines = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            clean_lines.append(line)
        clean_text = "\n".join(clean_lines)

        # 1. Project name & version
        project_match = re.search(r'project\s*\(\s*([A-Za-z0-9_-]+)(.*?\))', clean_text, re.IGNORECASE | re.DOTALL)
        project_name = project_match.group(1) if project_match else "UnknownProject"

        # 2. Qt and Third-party packages
        find_packages = []
        for m in re.finditer(r'find_package\s*\(\s*([^\)]+)\)', clean_text, re.IGNORECASE):
            pkg_str = " ".join(m.group(1).split())
            find_packages.append(pkg_str)

        # 3. Automation flags (MOC, UIC, RCC)
        has_autouic = bool(re.search(r'set\s*\(\s*CMAKE_AUTOUIC\s+ON\s*\)', clean_text, re.IGNORECASE))
        has_automoc = bool(re.search(r'set\s*\(\s*CMAKE_AUTOMOC\s+ON\s*\)', clean_text, re.IGNORECASE))
        has_autorcc = bool(re.search(r'set\s*\(\s*CMAKE_AUTORCC\s+ON\s*\)', clean_text, re.IGNORECASE))

        # 4. Targets (executables and libraries)
        executables = []
        for m in re.finditer(r'add_executable\s*\(\s*([A-Za-z0-9_-]+)(.*?\))', clean_text, re.IGNORECASE | re.DOTALL):
            exe_name = m.group(1)
            raw_sources = m.group(2)
            sources = [s for s in raw_sources.split() if not s.endswith(")")]
            executables.append({"target": exe_name, "sources": sources})

        libraries = []
        for m in re.finditer(r'add_library\s*\(\s*([A-Za-z0-9_-]+)(.*?\))', clean_text, re.IGNORECASE | re.DOTALL):
            lib_name = m.group(1)
            raw_sources = m.group(2)
            sources = [s for s in raw_sources.split() if not s.endswith(")")]
            libraries.append({"target": lib_name, "sources": sources})

        # 5. UI form files referenced (*.ui)
        ui_files = re.findall(r'[A-Za-z0-9_\-/\\]+\.ui\b', clean_text, re.IGNORECASE)
        ui_files = list(set(ui_files))

        # 6. Target link libraries
        links = {}
        for m in re.finditer(r'target_link_libraries\s*\(\s*([A-Za-z0-9_-]+)(.*?\))', clean_text, re.IGNORECASE | re.DOTALL):
            tgt = m.group(1)
            libs = [l for l in m.group(2).split() if l not in ("PRIVATE", "PUBLIC", "INTERFACE", ")")]
            links[tgt] = libs

        # 7. Subdirectories
        subdirs = re.findall(r'add_subdirectory\s*\(\s*([A-Za-z0-9_\-/\\]+)\s*\)', clean_text, re.IGNORECASE)

        chunks: List[Dict[str, Any]] = []

        # ── High-level UI / Architecture summary ──────────────────────────
        summary_lines = [
            f"Project: {project_name}",
            f"Build Configuration: {source_name}"
        ]
        if executables:
            summary_lines.append(f"Application Targets: {', '.join(e['target'] for e in executables)}")
        if find_packages:
            summary_lines.append(f"Dependencies: {'; '.join(find_packages)}")
        if ui_files:
            summary_lines.append(f"Qt UI Form Screens ({len(ui_files)}): {', '.join(ui_files)}")
        if has_autouic:
            summary_lines.append("Qt UI compiler (CMAKE_AUTOUIC): Enabled")

        chunks.append({
            "content": "\n".join(summary_lines),
            "metadata": {
                "content_type": "ui_description",
                "source": source_name,
                "language": "cmake",
                "project": project_name,
                "kind": "project_architecture"
            }
        })

        # ── Detailed Technical Build Specification ───────────────────────
        detail_lines = [
            f"CMake Target Definition for {project_name} ({source_name})",
            f"Executables: {', '.join(e['target'] for e in executables) if executables else 'None'}",
            f"Libraries: {', '.join(l['target'] for l in libraries) if libraries else 'None'}",
            f"Automation: AUTOMOC={has_automoc}, AUTOUIC={has_autouic}, AUTORCC={has_autorcc}",
            f"Package Requirements:\n  - " + "\n  - ".join(find_packages) if find_packages else "Packages: None",
        ]
        for tgt, liblist in links.items():
            detail_lines.append(f"Link Libraries ({tgt}): {', '.join(liblist)}")
        if subdirs:
            detail_lines.append(f"Subdirectories: {', '.join(subdirs)}")

        chunks.append({
            "content": "\n".join(detail_lines),
            "metadata": {
                "content_type": "source_code",
                "source": source_name,
                "language": "cmake",
                "project": project_name,
                "kind": "build_specification"
            }
        })

        return chunks
