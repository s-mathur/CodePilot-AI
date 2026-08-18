from tools.parser_tool import PythonParser
from tools.project_tree_builder import ProjectTreeBuilder
from tools.dependency_tree_builder import DependencyTreeBuilder

from config import IGNORE_FOLDERS

from pathlib import Path
import os

class ProjectInsightsAnalyzer:

    def __init__(self, project_path):
        self.project_path = project_path
        self.python_files = []
        self.files = {}

    def analyze(self):

        self.python_files = self._get_python_files()
        self._analyze_files()
        return {
            "project_name": self._get_project_name(),
            "project_path": self.project_path,
            "project_structure": self._get_project_structure(),
            "dependencies": self._get_dependencies(),
            "files": self.files,
            "statistics": self._get_statistics()
        }

    def _get_project_name(self):
        return os.path.basename(os.path.normpath(self.project_path))

    def _get_python_files(self):

        python_files = []
        for root, dirs, files in os.walk(self.project_path):

            # Ignore Folder like virtual environments etc.
            dirs[:] = [directory for directory in dirs if directory not in IGNORE_FOLDERS]

            for filename in files:
                if not filename.endswith(".py"):
                    continue
                file_path = os.path.join(root, filename)
                python_files.append(file_path)

        return sorted(python_files)

    def generate_summary(self):
        summary = {}
        files = []
        self.python_files = self._get_python_files()
        for file in self.python_files:

            path = Path(file)
            parts = path.parts
            project_index = parts.index("project")
            files.append(str(Path(*parts[project_index + 1:])))
        summary = list(set(os.path.dirname(file) for file in files))
        return summary

    def _analyze_files(self):
        self.files = {}
        for file_path in self.python_files:
            relative_path = os.path.relpath(file_path, self.project_path)
            try:
                parser = PythonParser(file_path)
                structure = parser.get_tree_structure()
                tree_text = parser.get_tree_text()

                self.files[relative_path] = {
                    "file_name": structure.get("file_name", os.path.basename(file_path)),
                    "path": relative_path,
                    "imports": structure.get("imports", []),
                    "classes": structure.get("classes", []),
                    "functions": structure.get("functions", []),
                    "docstring": structure.get("docstring"),
                    "tree": tree_text,
                    "structure": structure
                }
            except Exception as exc:
                self.files[relative_path] = {
                    "file_name": os.path.basename(file_path),
                    "path": relative_path,
                    "error": str(exc)
                }

    def _get_project_structure(self):

        try:
            tree_builder = ProjectTreeBuilder(self.project_path)
            return tree_builder.build()
        except Exception as exc:
            return self._build_basic_tree()

    def _get_dependencies(self):

        try:
            dependency_builder = DependencyTreeBuilder(self.project_path)

            return dependency_builder.build()

        except Exception as exc:
            return {
                "error": str(exc)
            }

    def _get_statistics(self):

        statistics = {
            "python_files": 0,
            "classes": 0,
            "methods": 0,
            "functions": 0,
            "imports": 0
        }

        for file_data in self.files.values():

            if "error" in file_data:
                continue

            statistics["python_files"] += 1
            statistics["imports"] += len(file_data.get("imports", []))
            classes = file_data.get("classes", [])
            statistics["classes"] += len(classes)

            for class_data in classes:
                methods = class_data.get("methods", [])
                statistics["methods"] += len(methods)

            functions = file_data.get("functions", [])
            statistics["functions"] += len(functions)

        return statistics

    # =========================================================
    # BASIC FALLBACK TREE
    # =========================================================

    def _build_basic_tree(self):

        root_name = self._get_project_name()

        lines = [f"📁 {root_name}"]

        sorted_files = sorted(self.files.keys())

        for index, file_path in enumerate(sorted_files):

            is_last = index == len(sorted_files) - 1

            connector = "└──" if is_last else "├──"

            lines.append(f"{connector} 📄 {file_path}")

        return "\n".join(lines)