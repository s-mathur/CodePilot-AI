import streamlit as st
import uuid


class ExecutionTracker:

    container = None

    icons = {
        "RUNNING": "⏳",
        "COMPLETED": "✅",
        "FAILED": "❌",
        "WARNING": "⚠️",
        "CHECKING": "🔍",
        "HIT": "💾",
        "MISS": "📂"
    }

    @staticmethod
    def initialize():
        if "execution_trace" not in st.session_state:
            st.session_state.execution_trace = {}

    @staticmethod
    def clear():
        st.session_state.execution_trace = {}

    @staticmethod
    def set_container(container):
        ExecutionTracker.container = container

    @staticmethod
    def _generate_id(component):
        clean_name = str(component).lower().replace(" ", "_")
        return f"{clean_name}_{uuid.uuid4().hex[:8]}"

    # Find node by UNIQUE ID
    @staticmethod
    def find_node_by_id(tree, node_id):
        for key, node in tree.items():
            if key == node_id:
                return node
            result = ExecutionTracker.find_node_by_id(node["children"], node_id)
            if result:
                return result
        return None

    @staticmethod
    def find_node_by_component(tree, component):

        for node_id, node in tree.items():

            if node["name"] == component:
                return node
            result = ExecutionTracker.find_node_by_component(node["children"], component)

            if result:
                return result

        return None

    @staticmethod
    def log(component, status, details=None, parent=None):

        ExecutionTracker.initialize()

        trace = st.session_state.execution_trace

        # Create unique node ID
        node_id = ExecutionTracker._generate_id(component)

        node = {
            "id": node_id,
            "name": component,
            "status": status,
            "details": details,
            "children": {}
        }

        # ROOT NODE
        if parent is None:
            trace[node_id] = node

        # CHILD NODE
        else:
            parent_node = ExecutionTracker.find_node_by_id(trace, parent)
            if parent_node is None:
                parent_node = ExecutionTracker.find_node_by_component(trace, component=parent)

            if parent_node is None:
                # Parent doesn't exist.
                # Create it as a root node.
                parent_id = ExecutionTracker._generate_id(parent)

                parent_node = {
                    "id": parent_id,
                    "name": parent,
                    "status": "RUNNING",
                    "details": None,
                    "children": {}
                }

                trace[parent_id] = parent_node

            parent_node["children"][node_id] = node

        # Render
        ExecutionTracker.render()

        # Return unique execution ID
        return node_id

    # UPDATE EXISTING NODE
    @staticmethod
    def update(execution_id, status, details=None):

        trace = st.session_state.execution_trace
        node = ExecutionTracker.find_node_by_id(trace, execution_id)

        if node is None:
            return

        node["status"] = status

        if details is not None:
            node["details"] = details

        ExecutionTracker.render()

    # Render
    @staticmethod
    def render():
        if ExecutionTracker.container is None:
            return
        with ExecutionTracker.container.container():

            with st.expander("🚀 Live Execution", expanded=True):

                for node_id, node in st.session_state.execution_trace.items():
                    ExecutionTracker.render_node(node, level=0)

    # Recursive renderer
    @staticmethod
    def render_node(node, level=0):

        indent = "&nbsp;" * (level * 6)

        icon = ExecutionTracker.icons.get(node["status"], "ℹ️")

        status = node["status"]

        details = ""

        if node["details"]:

            if isinstance(node["details"], dict):

                details = " | ".join(f"{k}: {v}" for k, v in node["details"].items())

            else:
                details = str(node["details"])

        line = f"{indent} {icon} <b>{node['name']}</b> - <b>{status}</b>"

        if details:
            line += f" - <span style='color:#888'>({details})</span>"

        st.markdown(line, unsafe_allow_html=True)

        # Render children
        for child_id, child in node["children"].items():

            ExecutionTracker.render_node(child, level + 1)