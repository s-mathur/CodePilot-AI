from utils.session_manager import SessionManager, SessionExpiredError
from utils.execution_tracker import ExecutionTracker
from utils.render_response import render_response
from utils.helper import save_uploaded_zip
from utils.agent_map import AGENT_MAP

from tools.file_tool import get_file_metadata, extract_zip, get_python_files, get_project_tree, chunk_python_file
from tools.project_insights_analyzer import ProjectInsightsAnalyzer
from tools.dependency_tree_builder import DependencyTreeBuilder
from tools.project_tree_builder import ProjectTreeBuilder
from tools.dependency_tool import DependencyTool
from tools.cache_tool import delete_caches
from tools.graph_tool import GraphTool

from agents.similarity_search_agent import SimilaritySearchAgent
from agents.documentation_agent import DocumentationAgent
from agents.assistant_agent import AssistantAgent
from agents.unit_test_agent import UnitTestAgent
from agents.agent_manager import AgentManager
from agents.debug_agent import DebugAgent

import streamlit as st
import os

st.set_page_config(page_title="CodePilot AI", layout="wide")

SessionManager.cleanup_expired_sessions()
# Sidebar
st.sidebar.title("CodePilot AI")
page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Upload Project",
        "Project Detail Analyzer",
        "Project Similarity Search",
        "Chat with Codebase",
        "Dependency Graph",
        "Debug Assistant",
        "Code Generator",
        "Unit Test Generator",
        "Documentation Generator",
    ]
)

session_id = st.session_state.get("session_id")
if session_id:
    if "project_name" in st.session_state:
        st.sidebar.write(f"**File: {st.session_state['project_name']}**")
    with st.sidebar:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete All Cache"):
                delete_caches(session_id)
                st.sidebar.success("Cache Deleted.")
        with col2:
            if st.button("Delete Project"):
                SessionManager.delete_session(session_id)
                st.session_state.clear()
                st.rerun()
with st.sidebar:
    st.write("---")
    with open("sample_test_code.zip", "rb") as file:
        st.download_button(
            label="Download Sample Test Code",
            data=file,
            file_name="sample_test_code.zip",
            mime="application/zip"
        )

if page == "Home":
    st.title("CodePilot AI - AI Software Engineering Assistant")
    st.write("""
             AI-powered codebase analysis and development assistant.\n
             Analyze, search, debug, review, generate, and document Python projects

             **The data will be sent to the LLM model in some operations. Please upload dummy or sample data. The uploaded document will be removed after 30 min automatically.**

            **Features:**
            - Project analysis
            - Codebase search
            - Dependency visualization
            - AI-powered debugging
            - Code generation
            - Unit test generation
            - Documentation generation
            """
    )
elif page == "Upload Project":
    st.title("Upload Python Project")
    st.write("""Upload a Python project as a ZIP file. The system extracts the project, ignores unnecessary folders,
             identifies Python files, and prepares the codebase for analysis.""")
    uploaded_file = st.file_uploader("Upload ZIP file", type=["zip"])
    if uploaded_file:
        zip_path = save_uploaded_zip(uploaded_file)
        session_id = SessionManager.create_session()
        project_path = SessionManager.get_project_path(session_id)
        extract_zip(zip_path, project_path)
        st.session_state.project_uploaded = True
        st.session_state.project_path = os.path.join(project_path, os.path.splitext(uploaded_file.name)[0])
        st.session_state['session_id'] = session_id
        st.session_state["project_name"] = uploaded_file.name

        st.success("Project Uploaded Successfully")

        python_files = get_python_files(st.session_state['project_path'])
        
        st.header("Project Details")

        st.session_state.python_files = python_files
        st.info(f"**Total Python Files:** {len(python_files)}")

        st.subheader("Project Files")
        tree = get_project_tree(st.session_state['project_path'])
        st.code(tree, language="text")

        st.subheader("Python File Metadata")
        for file in python_files:
            metadata = get_file_metadata(file)
            st.write(metadata)

        chunks = []
        for file in python_files:
            chunks.extend(chunk_python_file(file))
        st.session_state["chunks"] = chunks

elif page == "Project Detail Analyzer":
    st.title("Project Analyzer")
    st.write("Analyze the uploaded Python project and provide the details of all the files. **No LLM**.")
    if "chunks" not in st.session_state:
        st.warning("Please upload a project first.")
    if "session_id" in st.session_state:
        session_id = st.session_state["session_id"]

        if SessionManager.is_session_expired(session_id):
            SessionManager.delete_session(session_id)
            st.session_state.clear()
            st.error("Session expired. Please upload again.")

        elif "python_files" in st.session_state:
            ExecutionTracker.clear()
            trace = st.empty()
            ExecutionTracker.set_container(trace)

            project_insights = ProjectInsightsAnalyzer(st.session_state["project_path"])
            summary = project_insights.generate_summary()
            st.subheader("Project Folders")
            st.json(summary)

            project_tree = ProjectTreeBuilder(st.session_state.project_path).build()
            st.code(project_tree)

elif page == "Chat with Codebase":

    st.title("Chat with Python Codebase")
    st.write("""
             Allow users to ask natural-language questions about their uploaded project. 
             CodePilot AI analyze questions and accordingly performs based on the task identified.
             """)
    with st.expander("Example Questions"):
        st.write("""
                 - Explain the authentication flow.
                 - How does JWT work?
                 - Suggest improvements for this module.
                 - Explain the project architecture.
                 """)
    if "chunks" not in st.session_state:
        st.warning("Please upload a project first.")
    else:
        if "session_id" in st.session_state:
            session_id = st.session_state["session_id"]
            if SessionManager.is_session_expired(session_id):
                SessionManager.delete_session(session_id)
                st.session_state.clear()
                st.error("Session expired. Please upload again.")
            else:
                query = st.text_input("Ask your question")
                if query:
                    ExecutionTracker.clear()
                    trace = st.empty()
                    ExecutionTracker.set_container(trace)
                    try:
                        response = AgentManager().execute(
                            st.session_state["session_id"], query, 
                            st.session_state["project_path"], st.session_state["chunks"]
                        )
                        render_response(response)
                    except SessionExpiredError as e:
                        st.error(str(e))
                        # Don't continue processing
                        st.stop()
                    
elif page == "Project Similarity Search":
    st.title("Similarity Search")
    st.write("""
             Find the most relevant code snippets/files from the project based on semantic similarity using embeddings and FAISS (**No LLM**).

             Example Queries:

            - Where is JWT implemented?
            - Which file handles database operations?
            - Show all FastAPI routes.
            - Find login functionality.
             """)
    if "chunks" not in st.session_state:
        st.warning("Please upload a project first.")
    else:
        if "session_id" in st.session_state:
            session_id = st.session_state["session_id"]
            if SessionManager.is_session_expired(session_id):
                SessionManager.delete_session(session_id)
                st.session_state.clear()
                st.error("Session expired. Please upload again.")

            else:
                query = st.text_input("Ask anything about the codebase")
                if query:
                    ExecutionTracker.clear()
                    trace = st.empty()
                    ExecutionTracker.set_container(trace)
                    try:
                        similarity_search_agent = SimilaritySearchAgent()
                        response = similarity_search_agent.execute(query, st.session_state["chunks"])
                        render_response(response)
                    except SessionExpiredError as e:
                        st.error(str(e))
                        # Don't continue processing
                        st.stop()

elif page == "Dependency Graph":

    st.title("Dependency Graph")
    st.write("""
                Visually represent relationships between project files/modules. **No LLM**
            """)
    if "chunks" not in st.session_state:
        st.warning("Please upload a project first.")
    if "session_id" in st.session_state:
        session_id = st.session_state["session_id"]
        if SessionManager.is_session_expired(session_id):
            SessionManager.delete_session(session_id)
            st.session_state.clear()
            st.error("Session expired. Please upload again.")

        elif "python_files" not in st.session_state:
            st.warning("Please upload a project first.")

        else:
            ExecutionTracker.clear()
            trace = st.empty()
            ExecutionTracker.set_container(trace)

            dependency_tool = DependencyTool(st.session_state["python_files"])
            dependencies = dependency_tool.extract_dependencies()

            st.subheader("Dependencies")
            dependency_tree_builder = DependencyTreeBuilder(st.session_state.project_path)
            dependency_tree = dependency_tree_builder.build()
            st.code(dependency_tree)

            graph_id = ExecutionTracker.log(AGENT_MAP.graph, "RUNNING", "Generating graph")
            graph_tool = GraphTool()
            graph = graph_tool.create_graph(dependencies)
            figure = graph_tool.plot_graph(graph)
            st.pyplot(figure)
            ExecutionTracker.update(graph_id, "COMPLETED", "Graph Generated")

elif page == "Debug Assistant":

    st.title("Debug Assistant")
    st.write("""
            Analyze Python errors, tracebacks, and problematic code using project context. **LLM Usage**
            """)
    if "session_id" not in st.session_state:
        st.warning("Please upload a project first.")

    else:
        error_text = st.text_area("Paste Stack Trace")
        if st.button("Analyze Error"):
            if not error_text:
                st.warning("Please provide an error.")
            else:
                ExecutionTracker.clear()
                trace = st.empty()
                ExecutionTracker.set_container(trace)
                try:
                    response = DebugAgent().execute(
                        st.session_state["session_id"],
                        error_text, st.session_state["chunks"]
                    )
                    render_response(response)
                except SessionExpiredError as e:
                    st.error(str(e))
                    # Don't continue processing
                    st.stop()

elif page == "Code Generator":

    st.title("Code Generator")
    st.write("""
            Generate new code or modify existing code based on user requirements. **LLM Usage**
            """)
    if "session_id" not in st.session_state:
        st.warning("Please upload a project first.")
    else:
        mode = st.selectbox(
            "Select Mode",
            [
                "Function",
                "Class",
                "FastAPI Endpoint",
                "Flask API",
                "Utility",
                "Refactor"
            ]
        )
        query = st.text_area("Describe your requirement")
        if st.button("Generate Code"):
            ExecutionTracker.clear()
            trace = st.empty()
            ExecutionTracker.set_container(trace)
            try:
                response = AssistantAgent().execute(mode, query, st.session_state["chunks"])
                render_response(response)
            except SessionExpiredError as e:
                st.error(str(e))
                # Don't continue processing
                st.stop()

elif page == "Documentation Generator":
    st.title("Documentation Generator")
    st.write("""
             Generates Readme file (**LLM**) which contains
             - Project Overview
             - Features
             - Folder Structure
             - Installation Steps or setup instructions
             - Architecture
             - Dependencies
             - Usage
             - Future Improvements
             """)
    if "session_id" not in st.session_state:
        st.warning("Please upload a project first.")
    else:

        if st.button("Generate README"):
            if "session_id" not in st.session_state:
                st.warning("Please upload a project first.")
            ExecutionTracker.clear()
            trace = st.empty()
            ExecutionTracker.set_container(trace)
            try:
                response = DocumentationAgent().execute(st.session_state["session_id"], st.session_state["project_path"])
                if response['metadata']['llm_used']:
                    readme_path = os.path.join(SessionManager.get_session_path(session_id), "generated_README.md")
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.write(response['response'])
                                
                    st.download_button("Download README", data=response['response'], 
                        file_name=os.path.basename(readme_path), mime="text/markdown"
                    )
                render_response(response)
            except SessionExpiredError as e:
                st.error(str(e))
                # Don't continue processing
                st.stop()

elif page == "Unit Test Generator":
    st.title("Unit Test Generator")
    if "session_id" not in st.session_state:
        st.warning("Please upload a project first.")

    else:
        query = st.text_input("Enter Function Name")
        if st.button("Generate Tests"):
            ExecutionTracker.clear()
            trace = st.empty()
            ExecutionTracker.set_container(trace)
            try:
                response = UnitTestAgent().execute(st.session_state["session_id"], query, st.session_state["chunks"])
                if response['metadata']['llm_used']:
                    path = os.path.join(SessionManager.get_session_path(session_id), f"unit_test.py")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(response['response'])
                    st.download_button(
                        "Download Test File",
                        response['response'],
                        file_name=f"test_{query}.py"
                    )
                render_response(response)
            except SessionExpiredError as e:
                st.error(str(e))
                # Don't continue processing
                st.stop()
