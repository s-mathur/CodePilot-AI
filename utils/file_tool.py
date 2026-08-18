from config import SUPPORTED_EXTENSIONS, IGNORE_FOLDERS

from tools.parser_tool import PythonParser

from pathlib import Path
import zipfile
import shutil
import os

def clean_workspace(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

def should_ignore(path):
    for folder in IGNORE_FOLDERS:
        if folder in path:
            return True
    return False

def get_python_files(project_path):
    python_files = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
        for file in files:
            if file.endswith(tuple(SUPPORTED_EXTENSIONS)):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    return python_files

def get_file_metadata(file_path):
    metadata = {}

    path = Path(file_path)
    parts = path.parts
    project_index = parts.index("project")
    path = str(Path(*parts[project_index + 1:]))

    metadata["file_name"] = os.path.basename(file_path)
    metadata["size"] = os.path.getsize(file_path)
    metadata["extension"] = os.path.splitext(file_path)[1]
    metadata["path"] = path
    return metadata

def get_project_tree(directory):
    directory = Path(directory)

    def build_tree(path, prefix=""):
        lines = []

        items = sorted(
            path.iterdir(),
            key=lambda x: (x.is_file(), x.name.lower())
        )

        for i, item in enumerate(items):
            is_last = i == len(items) - 1

            connector = " └── " if is_last else " ├── "
            lines.append(f"{prefix}{connector} {item.name}")

            if item.is_dir():
                extension = "     " if is_last else " │   "
                lines.extend(build_tree(item, prefix + extension))

        return lines

    tree = directory.name + "/\n"
    tree += "\n".join(build_tree(directory))

    return tree

def chunk_python_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
    return [{
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "content": code
    }]

def analyze(python_files):
    result = []
    for file in python_files:

        parser = PythonParser(file)
        result.append(parser.get_tree_structure())

    return result