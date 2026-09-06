"""
kb/parser/python_parser.py
AST-based Python source code parser for AppAI Knowledge Base.

Extracts:
  - Module docstrings & overview
  - Classes (names, base classes, docstrings)
  - Methods and Functions (signatures, docstrings, decorators)
  - UI event bindings / Qt signals (e.g., btn.clicked.connect(self.on_export))
  - Web framework routes (@app.get, @app.post, etc.)
  - Exception classes & error handlers

Generates structured chunks tagged as:
  - content_type="source_code": Detailed code structure & method signatures (for developers)
  - content_type="workflow": High-level user workflows / event flows derived from docstrings & UI connections
"""

import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class PythonParser:
    """Parses Python source files into structured Knowledge Base chunks."""

    def __init__(self):
        pass

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a Python file from disk."""
        path = Path(file_path)
        if not path.is_file():
            logger.warning("PythonParser: File not found: %s", file_path)
            return []

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
            return self.parse_code(code, source_name=str(path))
        except Exception as e:
            logger.error("PythonParser: Failed to read %s: %s", file_path, e)
            return []

    def parse_code(self, code: str, source_name: str = "script.py") -> List[Dict[str, Any]]:
        """Parse Python source code string and return structured KB documents."""
        try:
            tree = ast.parse(code, filename=source_name)
        except SyntaxError as e:
            logger.warning("PythonParser: Syntax error in %s (line %d): %s", source_name, e.lineno, e.msg)
            # Fallback: create raw code chunk
            return [{
                "content": f"Python File: {source_name}\n[Raw Content]\n{code[:4000]}",
                "metadata": {
                    "content_type": "source_code",
                    "source": source_name,
                    "language": "python",
                    "parse_status": "raw_syntax_error"
                }
            }]

        chunks: List[Dict[str, Any]] = []

        # 1. Module-level overview & docstring
        module_doc = ast.get_docstring(tree)
        overview_lines = [f"File: {source_name}"]
        if module_doc:
            overview_lines.append(f"Description: {module_doc.strip()}")

        # Extract top-level imports for context
        imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                names = ", ".join(a.name for a in node.names)
                imports.append(f"{mod}: {names}")

        if imports:
            overview_lines.append(f"Imports / Dependencies: {', '.join(imports[:15])}")

        chunks.append({
            "content": "\n".join(overview_lines),
            "metadata": {
                "content_type": "source_code",
                "source": source_name,
                "language": "python",
                "kind": "module_overview"
            }
        })

        if module_doc:
            # Also create a user_doc chunk if module docstring explains user-facing features
            chunks.append({
                "content": f"Module {Path(source_name).name}: {module_doc.strip()}",
                "metadata": {
                    "content_type": "user_doc",
                    "source": source_name,
                    "language": "python",
                    "kind": "module_docstring"
                }
            })

        # 2. Extract Classes & Methods
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._extract_class(node, source_name, chunks)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._extract_function(node, source_name, chunks, parent_class=None)

        return chunks

    def _extract_class(self, node: ast.ClassDef, source_name: str, chunks: List[Dict[str, Any]]):
        bases = [self._format_expr(b) for b in node.bases]
        class_doc = ast.get_docstring(node)
        base_str = f"({', '.join(bases)})" if bases else ""

        methods = []
        ui_connections = []

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)
                # Inspect method body for Qt signal connections (e.g. self.btn.clicked.connect)
                connections = self._find_signal_connections(item)
                ui_connections.extend(connections)

        class_summary = [
            f"Class: {node.name}{base_str}",
            f"Defined in: {source_name}"
        ]
        if class_doc:
            class_summary.append(f"Docstring: {class_doc.strip()}")
        if methods:
            class_summary.append(f"Methods: {', '.join(methods)}")
        if ui_connections:
            class_summary.append(f"UI Event Connections:\n  - " + "\n  - ".join(ui_connections))

        # Source code chunk
        chunks.append({
            "content": "\n".join(class_summary),
            "metadata": {
                "content_type": "source_code",
                "source": source_name,
                "language": "python",
                "kind": "class",
                "symbol": node.name
            }
        })

        # If it is a UI class (e.g., QMainWindow, QDialog, QWidget, Window, View)
        # or has UI connections, emit a workflow / ui_description chunk
        is_ui_class = any(b in ("QMainWindow", "QWidget", "QDialog", "QFrame", "Window", "View", "Form") for b in bases)
        if (is_ui_class or ui_connections) and class_doc:
            chunks.append({
                "content": f"UI View '{node.name}': {class_doc.strip()}" + (f"\nEvents: {', '.join(ui_connections)}" if ui_connections else ""),
                "metadata": {
                    "content_type": "ui_description",
                    "source": source_name,
                    "language": "python",
                    "symbol": node.name
                }
            })

        # Also extract individual methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._extract_function(item, source_name, chunks, parent_class=node.name)

    def _extract_function(self, node: Any, source_name: str, chunks: List[Dict[str, Any]], parent_class: Optional[str]):
        doc = ast.get_docstring(node)
        args = [a.arg for a in node.args.args if a.arg != "self"]
        decorators = [self._format_expr(d) for d in node.decorator_list]

        fn_prefix = f"{parent_class}.{node.name}" if parent_class else node.name
        sig = f"{fn_prefix}({', '.join(args)})"

        lines = [f"Function: {sig}"]
        if decorators:
            lines.append(f"Decorators: {', '.join(decorators)}")
        if doc:
            lines.append(f"Description: {doc.strip()}")

        # Look for route decorators (FastAPI, Flask)
        is_route = any("get" in d.lower() or "post" in d.lower() or "route" in d.lower() for d in decorators)

        # Technical code chunk
        chunks.append({
            "content": "\n".join(lines),
            "metadata": {
                "content_type": "source_code",
                "source": source_name,
                "language": "python",
                "kind": "function" if not parent_class else "method",
                "symbol": fn_prefix
            }
        })

        # If it's a documented API route or action, add to workflow / user_doc
        if doc and (is_route or "export" in node.name.lower() or "create" in node.name.lower() or "save" in node.name.lower() or "handle" in node.name.lower()):
            chunks.append({
                "content": f"Action / Handler '{fn_prefix}': {doc.strip()}",
                "metadata": {
                    "content_type": "workflow",
                    "source": source_name,
                    "language": "python",
                    "symbol": fn_prefix
                }
            })

    def _find_signal_connections(self, fn_node: ast.AST) -> List[str]:
        """Detect Qt-style .connect(...) and event listener calls."""
        connections = []
        for n in ast.walk(fn_node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "connect":
                # caller is like self.btnExport.clicked
                target = self._format_expr(n.func.value)
                handler = self._format_expr(n.args[0]) if n.args else "?"
                connections.append(f"{target} -> {handler}")
        return connections

    def _format_expr(self, node: ast.AST) -> str:
        """Format an AST expression node as string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._format_expr(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            func = self._format_expr(node.func)
            return f"{func}()"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        return ast.dump(node)
