from utils.execution_tracker import ExecutionTracker
from utils.agent_map import AGENT_MAP

from tools.parser_tool import PythonParser

import os


class DependencyTool:
    def __init__(self, python_files):
        self.python_files = python_files

    def extract_dependencies(self, parent=None):
        dependencies = {}
        depend_id = ExecutionTracker.log(
            AGENT_MAP.dependencies, "RUNNING", "Retrieving All Dependencies", parent=parent)
        for file_path in self.python_files:
            parser = PythonParser(file_path)
            imports = parser.get_imports()
            file_name = os.path.basename(file_path)
            dependencies[file_name] = imports
        ExecutionTracker.update(depend_id, "COMPLETED", details="Retrieved All Dependencies")
        
        return dependencies