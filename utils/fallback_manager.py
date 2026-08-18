from utils.execution_tracker import ExecutionTracker
from utils.agent_map import AGENT_MAP

from agents.project_insights_agent import ProjectInsightsAgent

from tools.dependency_tree_builder import DependencyTreeBuilder
from tools.similarity_search_tool import SimilaritySearch
from tools.project_tree_builder import ProjectTreeBuilder
from tools.cache_tool import get_cached_response

import streamlit as st
import os

class FallbackManager:

    def __init__(self):
        self.search_engine = None
        self.project_result = None

    def get_fallback_chain(self, task):
        chains = {
            "code_review": ["cache", "similar_search", "project_analysis"],
            "refactor": ["cache", "similar_search", "project_analysis"],
            "debug": ["cache", "similar_search", "project_analysis"],
            "project_analysis": ["cache", "project_analysis"],
            "architecture": ["cache", "project_analysis"],
            "code_generate": ["cache", "similar_search"],
            "general": ["cache", "similar_search"],
            "documentation": ["template"]
        }
        return chains.get(task, ["cache", "similar_search"])

    def handle(self, task, session_id=None, query=None, parent_log=None):

        fallback_chain = self.get_fallback_chain(task)

        fallback_id = ExecutionTracker.log(AGENT_MAP.llm_fallback_agent, "RUNNING",
            details={
                "Task": task,
                "Fallback Chain": " → ".join(fallback_chain)
            },
            parent=parent_log)

        for fallback_type in fallback_chain:
            try:
                result = self._execute_fallback(
                    task=task, fallback_type=fallback_type, session_id=session_id,
                    query=query, parent_log=fallback_id)
                if result and result.get("success") is not None:
                    if result.get("fallback_success", False) is True:
                        ExecutionTracker.update(
                            fallback_id, "COMPLETED", details={"Fallback Success": fallback_type})
                        return result
            except Exception as e:
                ExecutionTracker.update(fallback_id, "WARNING", details={"Fallback": fallback_type})
                continue

        # No fallback worked
        ExecutionTracker.update(fallback_id, "FAILED",
            details="No fallback strategy succeeded")
        return self._llm_unavailable_response(task)

    def _execute_fallback(self, task, fallback_type, session_id, query, parent_log):

        handlers = {
            "cache": self._cache_fallback,
            "similar_search": self._similaritysearch_fallback,
            "project_analysis": self._project_fallback,
            "template": self._template_fallback
        }
        handler = handlers.get(fallback_type)
        if not handler:
            ExecutionTracker.update(parent_log, "WARNING",
                details={
                    "Fallback": fallback_type,
                    "Reason": "Unknown fallback"
                })
            return None

        return handler(task, session_id, query, parent_log)

    def _cache_fallback(self, task, session_id, query, parent_log):

        cache_logid = ExecutionTracker.log(
            AGENT_MAP.cache, "CHECKING", details="Checking exact and semantic cache", parent=parent_log)
        if not query:
            ExecutionTracker.update(cache_logid, "SKIPPED", details="No query/session available")
            return None

        cached_result = get_cached_response(session_id, query)
        if cached_result:
            cache_type = cached_result.get("cache_type")
            similarity = cached_result.get("similarity_percentage", 100)
            ExecutionTracker.update(cache_logid, "COMPLETED",
                details= {
                    "cache": cache_type,
                    "similarity": f"{similarity}%"
                })
            return {
                "success": True,
                "fallback_success": True,
                "title": "Cached Response",
                "message": "LLM unavailable. Returning previously generated response.",
                "response_type": cached_result['response_type'],
                "response": cached_result['response'],
                "metadata": {
                    "llm_used": False,
                    "fallback_used": True,
                    "cache_used": True
                }
            }

        ExecutionTracker.update(cache_logid, "SKIPPED", details="No Cache available")
        return None

    def _similaritysearch_fallback(self, task, session_id, query, parent_log):
        if not query:
            ExecutionTracker.log(
                AGENT_MAP.search_agent, "SKIPPED", details="No query available", parent=parent_log)
            return None
        try:
            search_logid = ExecutionTracker.log(AGENT_MAP.search_agent, "RUNNING",
                details="Searching project context", parent=parent_log)
            if self.search_engine is None:
                chunks = st.session_state.get("chunks", [])
                if not chunks:
                    ExecutionTracker.update(
                        search_logid, "SKIPPED", details="No project chunks available")
                    return None

                self.search_engine = SimilaritySearch()
                self.search_engine.build_index(chunks)

            results = self.search_engine.search(query)

            if not results:
                ExecutionTracker.update(
                    search_logid, "COMPLETED", details="No relevant code found")
                return None

            ExecutionTracker.update(search_logid, "COMPLETED", details={"Results": len(results)})

            return {
                "success": True,
                "fallback_success": True,
                "title": "LLM Unavailable - Relevant Code Found",
                "message": "The LLM is unavailable. Showing relevant code snippets instead.",
                "response_type": "similar_search",
                "response": results,
                "metadata": {
                    "llm_used": False,
                    "fallback_used": True,
                    "cache_used": False
                }
            }
        except Exception as e:
            ExecutionTracker.update(search_logid, "FAILED")
            return None

    def _project_fallback(self, task, session_id, query, parent_log):

        try:
            project_path = st.session_state.get("project_path", [])
            if not project_path:
                project_id = ExecutionTracker.log(AGENT_MAP.project_agent, "SKIPPED",
                    details="No Python files available", parent=parent_log)
                return None

            if self.project_result is None:
                self.project_result = ProjectInsightsAgent().execute(project_path, parent=parent_log)

            response = self.project_result['response']

            # if isinstance(response, dict):
            #     response = response.get("response", response.get("response", response))

            return {
                "success": True,
                "fallback_success": True,
                "title": "LLM Unavailable - Project Analysis",
                "message": "Showing deterministic project analysis generated using AST.",
                "response_type": "project_insights",
                "response": response,
                "metadata": {
                    "llm_used": False,
                    "fallback_used": True,
                    "cache_used": False,
                    "ast_used": True
                }
            }
        except Exception as e:
            ExecutionTracker.update(project_id, "FAILED")
            return None

    def _template_fallback(self, task, session_id, query, parent_log):

        template_id = ExecutionTracker.log(
            AGENT_MAP.template, "RUNNING", details={"Task": task}, parent=parent_log)

        dependency_tool = DependencyTreeBuilder(st.session_state["project_path"])
        dependencies = dependency_tool.build()
        tree_builder = ProjectTreeBuilder(st.session_state["project_path"])
        tree = tree_builder.build()

        if task in ("readme", "documentation"):
            project_name = os.path.basename(st.session_state["project_path"].rstrip(os.sep))
            response = {
                "project_name": project_name,
                "overview": "LLM generation is currently unavailable.",
                "project_structure": tree,
                "dependencies": dependencies,
                "status": "Documentation could not be fully generated because the LLM is currently unavailable."
            }
            ExecutionTracker.update(template_id, "COMPLETED",
                details="Static documentation template generated")
            return {
                "success": True,
                "fallback_success": True,
                "title": "README Documentation",
                "message": "LLM unavailable. Generated using project fallback.",
                "response_type": "documentation",
                "response": response,
                "metadata": {
                    "llm_used": False,
                    "fallback_used": True,
                    "cache_used": False,
                }
            }

        ExecutionTracker.update(template_id, "SKIPPED", details="No template available")
        return None

    def _llm_unavailable_response(self, task):

        return {
            "success": False,
            "fallback_success": False,
            "title": "LLM Unavailable",
            "message": "Please try again later or use a task that supports deterministic fallback processing.",
            "response_type": "warning",
            "response": f"The LLM is currently unavailable, so I could not complete the '{task}' task.",
            "metadata": {
                "llm_used": False,
                "fallback_used": False,
                "cache_used": False
            }
        }