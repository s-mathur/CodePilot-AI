from tools.project_insights_analyzer import ProjectInsightsAnalyzer
# from tools.dependency_tool import DependencyTool

class DocumentationTool:

    def generate_context(self, project_path, parent=None):

        analyzer = ProjectInsightsAnalyzer(project_path)
        analysis = analyzer.analyze()

        # dependencies = DependencyTool(python_files).extract_dependencies(parent=parent)

        context = f"""
        Total Files: {len(analysis['files'])}

        Project Analysis: {analysis}

        Dependencies: {analysis['dependencies']}

        """

        return context
