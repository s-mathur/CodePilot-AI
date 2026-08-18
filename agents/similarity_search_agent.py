from utils.execution_tracker import ExecutionTracker
from utils.session_manager import session_required
from utils.agent_map import AGENT_MAP

from tools.similarity_search_tool import SimilaritySearch


class SimilaritySearchAgent:
    @session_required
    def execute(self, query, chunks, parent_log=None):

        search_agent_id = ExecutionTracker.log(AGENT_MAP.search_agent, "RUNNING", parent=parent_log)

        search_engine = SimilaritySearch()
        search_engine.build_index(chunks)
        searched_result = search_engine.search(query)

        ExecutionTracker.update(search_agent_id, "COMPLETED")

        return {
            "task": "similar_search",
            "agent": AGENT_MAP.search_agent,
            "success": True,
            "response_type": "similar_search",
            "title": "Relevant Similar Code",
            "message": f"{len(searched_result)} matching snippets found.",
            "response": searched_result,
            "metadata": {
                "llm_used": False,
                "cache_used": False,
                "fallback_used": False
            }
        }