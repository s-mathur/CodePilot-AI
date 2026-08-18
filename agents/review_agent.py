from utils.execution_tracker import ExecutionTracker
from utils.session_manager import session_required
from utils.prompt_builder import review_prompt
from utils.agent_map import AGENT_MAP

from tools.similarity_search_tool import SimilaritySearch
from tools.gemini_tool import GeminiTool

class ReviewAgent:
    @session_required
    def execute(self, session_id, query, chunks):
        review_id = ExecutionTracker.log(AGENT_MAP.review_agent, "RUNNING")

        search_id = ExecutionTracker.log(AGENT_MAP.search_agent, "RUNNING", parent=review_id)

        search_engine = SimilaritySearch()
        search_engine.build_index(chunks)
        context = search_engine.search(query)

        ExecutionTracker.update(search_id, "COMPLETED",details={"Chunks": len(context)})

        prompt = review_prompt(query, context)

        gemini = GeminiTool()
        llm_response = gemini.generate_response(
            "review", session_id=session_id, query=query,
            prompt=prompt, parent_log=review_id)

        ExecutionTracker.update(review_id, "COMPLETED")

        return {
            "task": "code_review",
            "agent": AGENT_MAP.review_agent,
            "success": llm_response.get('success'),
            "title": "Code Review",
            "message": llm_response.get("message", None),
            "response_type": llm_response.get('response_type'),
            "response": llm_response.get('response'),
            "metadata": llm_response.get('metadata')
        }