import ast
import os


class PythonParser:
    # This will analyze individual file and extracts AST informations

    def __init__(self, file_path):
        self.file_path = file_path
        with open(file_path, "r", encoding="utf-8") as f:
            self.code = f.read()

        self.tree = ast.parse(self.code, filename=file_path)

    @staticmethod
    def _get_arguments(node):

        arguments = []
        args = node.args

        # positional arguments
        positional = args.posonlyargs + args.args
        for arg in positional:
            arguments.append({
                "name": arg.arg,
                "annotation": ast.unparse(arg.annotation) if arg.annotation else None
            })

        # *args
        if args.vararg:
            arguments.append({
                "name": f"*{args.vararg.arg}",
                "annotation": ast.unparse(args.vararg.annotation) if args.vararg.annotation else None
            })

        # keyword-only arguments
        for arg in args.kwonlyargs:
            arguments.append({
                "name": arg.arg,
                "annotation": ast.unparse(arg.annotation) if arg.annotation else None
            })

        # **kwargs
        if args.kwarg:
            arguments.append({
                "name": f"**{args.kwarg.arg}",
                "annotation": ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None
            })

        return arguments

    def get_imports(self):
        imports = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append({
                        "type": "import",
                        "module": name.name,
                        "name": None,
                        "alias": name.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    imports.append({
                        "type": "from",
                        "module": module,
                        "name": name.name,
                        "alias": name.asname
                    })
        return imports

    def get_decorators(self, node):
        decorators = []
        for decorator in node.decorator_list:
            try:
                decorators.append(ast.unparse(decorator))
            except Exception:
                pass
        return decorators

    def get_return_type(self, node):
        if node.returns:
            try:
                return ast.unparse(node.returns)
            except Exception:
                pass
        return None

    def get_class_attributes(self, node):
        attributes = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
            elif isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    attributes.append(item.target.id)

        return attributes

    def get_nested_functions(self, node):
        functions = []
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({
                    "name": child.name,
                    "type": "async_function" if isinstance(child, ast.AsyncFunctionDef) else "function",
                    "arguments": self._get_arguments(child),
                    "return_type": self.get_return_type(child),
                    "decorators": self.get_decorators(child),
                    "docstring": ast.get_docstring(child)
                })

        return functions

    def get_instance_attributes(self, class_node):
    
        attributes = set()

        for node in ast.walk(class_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        attributes.add(target.attr)

            elif isinstance(node, ast.AnnAssign):
                target = node.target
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    attributes.add(target.attr)

        return sorted(attributes)

    def parse_class(self, node):
        inheritance = []
        for base in node.bases:
            try:
                inheritance.append(ast.unparse(base))
            except Exception:
                pass

        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self.parse_method(item))

        return {
            "name": node.name,
            "inheritance": inheritance,
            "decorators": self.get_decorators(node),
            "docstring": ast.get_docstring(node),
            "attributes": self.get_class_attributes(node),
            "instance_attributes": self.get_instance_attributes(node),
            "methods": methods
        }

    def parse_method(self, node):
        return {
            "name": node.name,
            "type": "async_method" if isinstance(node, ast.AsyncFunctionDef) else "method",
            "arguments": self._get_arguments(node),
            "return_type": self.get_return_type(node),
            "decorators": self.get_decorators(node),
            "docstring": ast.get_docstring(node),
            "nested_functions": self.get_nested_functions(node)
        }

    def parse_function(self, node):
        return {
            "name": node.name,
            "type": "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
            "arguments": self._get_arguments(node),
            "return_type": self.get_return_type(node),
            "decorators": self.get_decorators(node),
            "docstring": ast.get_docstring(node),
            "nested_functions": self.get_nested_functions(node)
        }

    def get_tree_structure(self):
        result = {
            "file_name": os.path.basename(self.file_path),
            "imports": self.get_imports(),
            "docstring": ast.get_docstring(self.tree),
            "classes": [],
            "functions": []
        }

        # Only inspecting top-level definitions to preserve hierarchy
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                result["classes"].append(self.parse_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result["functions"].append(self.parse_function(node))

        return result

    def get_tree_text(self):
        data = self.get_tree_structure()
        lines = []
        lines.append(f"📄 {data['file_name']}")

        if data["docstring"]:
            lines.append("├── 📝 File Description")
            lines.append(f"│   └── {data['docstring'].splitlines()[0]}")

        if data["imports"]:
            lines.append("├── 📦 Imports")
            for index, item in enumerate(data["imports"]):
                is_last = (index == len(data["imports"]) - 1)
                prefix = ("│   └──" if is_last else "│   ├──")
                module = item.get("module", "")
                name = item.get("name")
                alias = item.get("alias")

                if name:
                    value = f"from {module} import {name}"
                else:
                    value = f"import {module}"

                if alias:
                    value += f" as {alias}"

                lines.append(f"{prefix} {value}")

        for _, cls in enumerate(data["classes"]):

            lines.append(f"├── 🏛 Class: {cls['name']}")

            # Inheritance
            if cls["inheritance"]:
                lines.append("│   ├── 🔗 Inherits")

                for base_index, base in enumerate(cls["inheritance"]):
                    prefix = "│   │   └──" if base_index == len(cls["inheritance"]) - 1 else "│   │   ├──"
                    lines.append(f"{prefix} {base}")

            # Decorators
            if cls["decorators"]:
                lines.append("│   ├── 🎯 Decorators")

                for decorator in cls["decorators"]:
                    lines.append(f"│   │   └── @{decorator}")

            # Class docstring
            if cls["docstring"]:
                lines.append("│   ├── 📝 Description")
                description = cls["docstring"].splitlines()[0]

                lines.append(f"│   │   └── {description}")

            # Class attributes
            if cls["attributes"]:
                lines.append("│   ├── 📌 Attributes")

                for attr_index, attribute in enumerate(cls["attributes"]):
                    prefix = "│   │   └──" if attr_index == len(cls["attributes"]) - 1 else "│   │   ├──"
                    lines.append(f"{prefix} {attribute}")

            # Methods
            if cls["methods"]:
                lines.append("│   └── 🔧 Methods")

                for _, method in enumerate(cls["methods"]):
                    method_name = method["name"]

                    if method["type"] == "async_method":
                        method_name = f"async {method_name}"

                    lines.append(f"│       ├── 🔧 {method_name}")

                    # Decorators
                    for decorator in method["decorators"]:
                        lines.append(f"│       │   ├── @{decorator}")

                    # Arguments
                    if method["arguments"]:
                        lines.append("│       │   ├── Arguments")

                        for arg in method["arguments"]:

                            argument = arg["name"]

                            if arg["annotation"]:
                                argument += f": {arg['annotation']}"

                            lines.append(f"│       │   │   ├── {argument}")

                    # Return type
                    if method["return_type"]:
                        lines.append(f"│       │   ├── Return: {method['return_type']}")

                    # Docstring
                    if method["docstring"]:

                        description = method["docstring"].splitlines()[0]

                        lines.append(f"│       │   └── 📝 {description}")

        for function in data["functions"]:

            function_name = function["name"]

            if function["type"] == "async_function":
                function_name = f"async {function_name}"

            lines.append(f"└── 🔹 Function: {function_name}")

            # Decorators
            for decorator in function["decorators"]:
                lines.append(f"    ├── @{decorator}")

            # Arguments
            if function["arguments"]:
                lines.append("    ├── Arguments")

                for arg in function["arguments"]:
                    argument = arg["name"]
                    if arg["annotation"]:
                        argument += f": {arg['annotation']}"

                    lines.append(f"    │   ├── {argument}")

            # Return
            if function["return_type"]:

                lines.append(f"    ├── Return: {function['return_type']}")

            # Docstring
            if function["docstring"]:
                description = function["docstring"].splitlines()[0]

                lines.append(f"    └── 📝 {description}")

        return "\n".join(lines)

    def get_summary(self):

        return {
            "file_name": os.path.basename(self.file_path),
            "imports": self.get_imports(),
            "docstring": ast.get_docstring(self.tree),
            "classes": [cls["name"] for cls in self.get_tree_structure()["classes"]],
            "methods": {
                cls["name"]: [method["name"] for method in cls["methods"]]
                for cls in self.get_tree_structure()["classes"]
            },
            "functions": [func["name"] for func in self.get_tree_structure()["functions"]],
            "async_functions": [
                func["name"] for func in self.get_tree_structure()["functions"]
                if func["type"] == "async_function"
            ]
        }

def build_project_tree(python_files):

    lines = []

    root = "📁 Project"

    lines.append(root)

    for index, file in enumerate(python_files):

        parser = PythonParser(file)
        tree = parser.get_tree_structure()
        is_last_file = index == len(python_files) - 1

        file_prefix = "└──" if is_last_file else "├──"

        lines.append(f"{file_prefix} 📄 {tree['file_name']}")

        # Imports
        if tree["imports"]:
            for i, imp in enumerate(tree["imports"]):

                prefix = "    └──" if i == len(tree["imports"]) - 1 else "    ├──"

                lines.append(f"    {prefix} 📦 {imp}")

        # Classes
        for cls in tree["classes"]:
            lines.append(f"    ├── 🏛 Class: {cls['name']}")

            for method in cls["methods"]:
                lines.append(f"    │   ├── 🔧 Method: {method['name']}")

                for arg in method["arguments"]:
                    lines.append(f"    │   │   ├── Argument: {arg}")

        # Functions
        for function in tree["functions"]:

            lines.append(f"    └── 🔹 Function: {function['name']}")

            for arg in function["arguments"]:
                lines.append(f"        ├── Argument: {arg}")

    return "\n".join(lines)