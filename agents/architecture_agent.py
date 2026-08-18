from utils.execution_tracker import ExecutionTracker
from utils.prompt_builder import architecture_prompt
from utils.agent_map import AGENT_MAP

from tools.project_insights_analyzer import ProjectInsightsAnalyzer
from tools.gemini_tool import GeminiTool

class ArchitectureAgent:

    def execute(self, session_id, query, project_path):

        architecture_logid = ExecutionTracker.log(AGENT_MAP.architecture_agent, "RUNNING")

        project_analyzer = ProjectInsightsAnalyzer(project_path)
        architecture = project_analyzer.analyze()

        prompt = architecture_prompt(query, architecture)

        gemini = GeminiTool()
        llm_response = gemini.generate_response(
            "architecture", session_id=session_id, query=query,
            prompt=prompt, parent_log=architecture_logid)
        ExecutionTracker.update(architecture_logid, "COMPLETED")

        return {
            "task": "architecture",
            "agent": AGENT_MAP.architecture_agent,
            "success": llm_response.get('success'),
            "title": llm_response.get('title', 'Response Generated'),
            "message": llm_response.get("message", None),
            "response_type": llm_response.get('response_type'),
            "response": llm_response.get('response'),
            "metadata": llm_response.get('metadata')
        }