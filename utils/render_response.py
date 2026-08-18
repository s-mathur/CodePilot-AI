import streamlit as st


def render_response(response):
    if response["title"]:
        st.subheader(response["title"])

    if response["message"]:
        st.caption(response["message"])

    response_type = response["response_type"]
    response = response['response']

    if response_type == "markdown":
        st.markdown(response)

    elif response_type == "similar_search":
        for result in response:
            st.subheader(result["file_name"])
            st.code(result["content"], language="python")

    elif response_type == "project_insights":
    
        if response.get("project_name"):
            st.markdown(f"## 📁 Project: {response['project_name']}")

        statistics = response.get("statistics")

        if statistics:
            st.markdown("### 📊 Project Statistics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Python Files", statistics.get("python_files", 0))

            with col2:
                st.metric("Classes", statistics.get("classes", 0))

            with col3:
                st.metric("Functions", statistics.get("functions", 0))

            with col4:
                st.metric("Methods", statistics.get("methods", 0))

        project_structure = response.get("project_structure")
        if project_structure:
            st.markdown("### 🌳 Project Structure")
            st.code(project_structure, language="text")

        dependencies = response.get("dependencies")
        if dependencies:
            st.markdown("### 📦 Dependencies")
            st.code(dependencies)

        files = response.get("files", {})
        if files:
            st.markdown("### 🐍 Python Files")
            for file_path, file_data in files.items():
                with st.expander(f"📄 {file_path}"):
                    if file_data.get("error"):
                        st.error(file_data["error"])
                        continue
                    tree = file_data.get("tree")
                    if tree:
                        st.code(tree, language="text")
                    else:
                        st.json(file_data)
    if response_type == "documentation":
    
        st.markdown(f"# {response['project_name']}")

        st.markdown("## Project Structure")
        st.write("The project structure can be analyzed using the available source files.")
        st.code(response["project_structure"], language="text")

        st.markdown("## Technologies & Dependencies")
        st.write("Please review the project dependencies and source files for the complete technology stack.")
        st.code(response["dependencies"])

        st.markdown("## Status")
        st.warning(response["status"])