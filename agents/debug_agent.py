from utils.execution_tracker import ExecutionTracker
from utils.context_optimizer import optimize_context
from utils.session_manager import session_required
from utils.prompt_builder import debug_prompt
from utils.agent_map import AGENT_MAP

from tools.similarity_search_tool import SimilaritySearch
from tools.traceback_parser import TracebackParser
from tools.gemini_tool import GeminiTool


class DebugAgent:
    @session_required
    def execute(self, session_id, query, chunks):
        debug_id = ExecutionTracker.log(AGENT_MAP.debug_agent, "RUNNING")

        trace_id = ExecutionTracker.log("Traceback Parser", "RUNNING", parent=debug_id)
        traceback_parser = TracebackParser()
        traceback_info = traceback_parser.parse(query)
        ExecutionTracker.update(trace_id, "COMPLETED")
        
        search_id = ExecutionTracker.log(AGENT_MAP.search_agent, "RUNNING", parent=debug_id)

        search_engine = SimilaritySearch()
        search_engine.build_index(chunks)
        context = []
        for item in traceback_info["files"]:
            context.extend(search_engine.search(item))
        if not context:
            context = search_engine.search(traceback_info["exception"])

        ExecutionTracker.update(search_id, "COMPLETED")

        context_id = ExecutionTracker.log(AGENT_MAP.context_optimizer, "RUNNING", parent=debug_id)
        context = optimize_context(context)
        ExecutionTracker.update(context_id, "COMPLETED")

        prompt = debug_prompt(query, context)

        gemini = GeminiTool()
        llm_response = gemini.generate_response(
            "debug", session_id=session_id, query=query,
            prompt=prompt, parent_log=debug_id)

        ExecutionTracker.update(debug_id, "COMPLETED")

        return {
            "task": "debug",
            "agent": AGENT_MAP.debug_agent,
            "success": llm_response.get('success'),
            "title": llm_response.get('title'),
            "message": llm_response('message', None),
            "response_type": llm_response.get('response_type'),
            "response": llm_response.get('response'),
            "metadata": llm_response.get('metatdata')
        }