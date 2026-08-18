from utils.execution_tracker import ExecutionTracker
from utils.session_manager import session_required
from utils.prompt_builder import assistant_prompt
from utils.agent_map import AGENT_MAP

from tools.gemini_tool import GeminiTool

from agents.similarity_search_agent import SimilaritySearchAgent


class AssistantAgent:
    @session_required
    def execute(self, session_id, query, chunks, task=None):
        assistant_id = ExecutionTracker.log(AGENT_MAP.general_agent, "RUNNING")
        context = SimilaritySearchAgent().execute(query, chunks, parent_log=assistant_id)

        prompt = assistant_prompt(task, query, context)

        gemini = GeminiTool()
        llm_response = gemini.generate_response(
            task, session_id=session_id, query=query,
            prompt=prompt, parent_log=assistant_id)

        ExecutionTracker.update(assistant_id, "COMPLETED")
        return {
            "task": task,
            "agent": AGENT_MAP.general_agent,
            "success": llm_response.get('success'),
            "title": llm_response.get('title'),
            "message": llm_response.get('message', None),
            "response_type": llm_response.get('response_type'),
            "response": llm_response.get('response'),
            "metadata": llm_response.get('metadata')
        }