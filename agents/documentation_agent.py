from tools.documentation_tool import DocumentationTool
from utils.execution_tracker import ExecutionTracker
from utils.session_manager import session_required
from utils.prompt_builder import documentation_prompt
from utils.agent_map import AGENT_MAP

from tools.gemini_tool import GeminiTool


class DocumentationAgent:
    @session_required
    def execute(self, session_id,  project_path):
        document_id = ExecutionTracker.log(AGENT_MAP.documention_agent, "RUNNING")

        context = DocumentationTool().generate_context(project_path)

        prompt = documentation_prompt(context)

        gemini = GeminiTool()
        llm_response = gemini.generate_response(
            "documentation", session_id=session_id,
            prompt=prompt, parent_log=document_id)

        ExecutionTracker.update(document_id, "COMPLETED")
        response = {
            "task": "documentation",
            "agent": AGENT_MAP.documention_agent,
            "success": llm_response.get('success'),
            "title": llm_response.get('title', 'Response Generated'),
            "message": llm_response.get('message'),
            "response_type": llm_response.get('response_type'),
            "response": llm_response.get('response'),
            "metadata": llm_response.get('metadata')
        }
        return response
