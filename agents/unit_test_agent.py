from utils.execution_tracker import ExecutionTracker
from utils.session_manager import session_required
from utils.prompt_builder import unit_test_prompt
from utils.agent_map import AGENT_MAP

from tools.similarity_search_tool import SimilaritySearch
from tools.gemini_tool import GeminiTool

class UnitTestAgent:
    @session_required
    def execute(self, session_id, query, chunks):
        unittest_id = ExecutionTracker.log(AGENT_MAP.unit_test_agent, "RUNNING")

        search_id = ExecutionTracker.log(AGENT_MAP.search_agent, "RUNNING", parent=unittest_id)
        search_engine = SimilaritySearch()
        search_engine.build_index(chunks)
        context = search_engine.search(query)
        ExecutionTracker.update(search_id, "COMPLETED")

        prompt = unit_test_prompt(context)

        gemini = GeminiTool()
        llm_response = gemini.generate_response(
            "code_generate", session_id=session_id, query=query,
            prompt=prompt, parent_log=unittest_id)

        ExecutionTracker.update(unittest_id, "COMPLETED")
        return {
            "task": "code_generate",
            "agent": AGENT_MAP.unit_test_agent,
            "success": llm_response.get('success'),
            "title":  llm_response.get('title', 'Response Generated'),
            "message": llm_response.get('message', None),
            "response_type": llm_response.get('response_type'),
            "response": llm_response.get('response'),
            "metadata": llm_response.get('metadata')
        }