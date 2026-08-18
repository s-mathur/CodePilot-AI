from tools.parser_tool import PythonParser

from config import IGNORE_FOLDERS
import os


class ProjectTreeBuilder:

    def __init__(self, project_path):
        self.project_path = os.path.abspath(project_path)

    def build(self):
        lines = []
        root_name = os.path.basename(self.project_path.rstrip(os.sep))

        lines.append(f"📁 {root_name}")

        self._walk(self.project_path, lines, prefix="")

        return "\n".join(lines)

    def _walk(self, current_path, lines, prefix):

        entries = sorted(
            os.listdir(current_path),
            key=lambda x: (not os.path.isdir(os.path.join(current_path, x)), x.lower())
        )

        # Ignore these
        entries = [x for x in entries if x not in IGNORE_FOLDERS]

        for index, entry in enumerate(entries):

            full_path = os.path.join(current_path, entry)

            is_last = index == len(entries) - 1

            connector = " └── " if is_last else " ├── "

            if os.path.isdir(full_path):

                lines.append(f"{prefix}{connector}📁 {entry}")

                child_prefix = prefix + "     " if is_last else prefix + " │   "

                self._walk(full_path, lines, child_prefix)

            elif entry.endswith(".py"):

                lines.append(f"{prefix}{connector}📄 {entry}")

                self._add_ast(full_path, lines, prefix, is_last)

            else:

                lines.append(f"{prefix}{connector}📄 {entry}")

    def _add_ast(self, file_path, lines, prefix, file_is_last):
        try:
            parser = PythonParser(file_path)
            data = parser.get_tree_structure()
        except Exception as e:
            lines.append(f"{prefix}     └── ❌ AST Error: {e}")
            return

        ast_prefix = prefix + ("     " if file_is_last else " │   ")

        if data.get("imports"):
            lines.append(f"{ast_prefix} ├── 📦 Imports")

            import_prefix = ast_prefix + " │   "

            for index, item in enumerate(data["imports"]):
                is_last = index == len(data["imports"]) - 1

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
                lines.append(f"{import_prefix}{connector}{dependency}")

        for class_index, cls in enumerate(data.get("classes", [])):

            class_is_last = class_index == len(data["classes"]) - 1

            connector = " └── " if class_is_last else " ├── "

            lines.append(f"{ast_prefix}{connector}🏛 Class: {cls['name']}")

            class_prefix = ast_prefix + ("     " if class_is_last else " │   ")

            if cls.get("inheritance"):

                lines.append(f"{class_prefix} ├── 🔗 Inheritance")

                inheritance_prefix = class_prefix + " │   "

                for base in cls["inheritance"]:

                    lines.append(f"{inheritance_prefix} └── {base}")

            methods = cls.get("methods", [])

            if methods:

                lines.append(f"{class_prefix} └── 🔧 Methods")

                method_prefix = class_prefix + "    "

                for method_index, method in enumerate(methods):

                    method_is_last = method_index == len(methods) - 1

                    method_connector = " └── " if method_is_last else " ├── "

                    lines.append(f"{method_prefix}{method_connector}🔧 {method['name']}")

                    arguments = method.get("arguments", [])

                    if arguments:

                        argument_prefix = method_prefix + ("     " if method_is_last else " │   ")

                        lines.append(f"{argument_prefix} └── Arguments")

                        args_prefix = argument_prefix + "    "

                        for arg_index, arg in enumerate(arguments):

                            arg_is_last = arg_index == len(arguments) - 1

                            arg_connector = " └── " if arg_is_last else " ├── "

                            # Support both dictionary and string
                            # argument formats

                            if isinstance(arg, dict):

                                arg_name = arg.get("name", "")

                                annotation = arg.get("annotation")

                                if annotation:
                                    arg_name += f": {annotation}"
                            else:
                                arg_name = str(arg)

                            lines.append(f"{args_prefix}{arg_connector}{arg_name}")

        functions = data.get("functions", [])

        for function_index, function in enumerate(functions):

            function_is_last = function_index == len(functions) - 1

            connector = " └── " if function_is_last else " ├── "

            lines.append(f"{ast_prefix}{connector}🔹 Function: {function['name']}")

            arguments = function.get("arguments", [])

            if arguments:

                function_prefix = ast_prefix + ("     " if function_is_last else " │   ")

                lines.append(f"{function_prefix} └── Arguments")

                args_prefix = function_prefix + "    "

                for arg_index, arg in enumerate(arguments):

                    arg_is_last = arg_index == len(arguments) - 1

                    arg_connector = " └── " if arg_is_last else " ├── "

                    if isinstance(arg, dict):

                        arg_name = arg.get("name", "")

                        annotation = arg.get("annotation")

                        if annotation:
                            arg_name += f": {annotation}"

                    else:

                        arg_name = str(arg)

                    lines.append(f"{args_prefix}{arg_connector}{arg_name}")