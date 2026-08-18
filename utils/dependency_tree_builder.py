from tools.parser_tool import PythonParser
from config import IGNORE_FOLDERS
import os

class DependencyTreeBuilder:

    def __init__(self, project_path):
        self.project_path = os.path.abspath(project_path)

    def build(self):
        lines = []
        root_name = os.path.basename(self.project_path.rstrip(os.sep))

        lines.append(f"📦 {root_name}")

        self._walk(self.project_path, lines, "")

        return "\n".join(lines)

    def _walk(self, current_path, lines, prefix):

        entries = sorted(
            os.listdir(current_path),
            key=lambda x: (not os.path.isdir(os.path.join(current_path, x)), x.lower())
        )

        entries = [x for x in entries if x not in IGNORE_FOLDERS]

        for index, entry in enumerate(entries):
            full_path = os.path.join(current_path, entry)

            is_last = index == len(entries) - 1

            connector = " └── " if is_last else " ├── "

            # DIRECTORY
            if os.path.isdir(full_path):
                lines.append(f"{prefix}{connector}📁 {entry}")
                next_prefix = prefix + "     " if is_last else prefix + " │   "
                self._walk(full_path, lines, next_prefix)

            # PYTHON FILE
            elif entry.endswith(".py"):
                self._add_file_dependencies(full_path, entry, lines, prefix, is_last)

    def _add_file_dependencies(self, file_path, file_name, lines, prefix, file_is_last):

        try:
            parser = PythonParser(file_path)
            imports = parser.get_imports()
        except Exception:
            return

        # Don't show file if it has no imports
        if not imports:
            return

        file_prefix = prefix + ("     " if file_is_last else " │   ")

        lines.append(f"{prefix}{' └── ' if file_is_last else ' ├── '}📄 {file_name}")

        dependency_prefix = file_prefix

        for index, item in enumerate(imports):
            is_last = index == len(imports) - 1

            connector = " └── " if is_last else " ├── "

            module = item["module"]
            name = item.get("name")
            alias = item.get("alias")

            if name:
                dependency = f"from {module} import {name}"
            else:
                dependency = f"import {module}"

            if alias:
                dependency += f" as {alias}"

            lines.append(f"{dependency_prefix}{connector}→ {dependency}")