
from utils.execution_tracker import ExecutionTracker
from utils.fallback_manager import FallbackManager
from utils.agent_map import AGENT_MAP

from google import genai
from google.genai import types

from config import GEMINI_MODEL, TEMPERATURE
import streamlit as st


class GeminiTool:
    def __init__(self):
        self.client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

    def generate_response(self, task, session_id=None, query=None, prompt=None, parent_log=None):
        try:
            llm_logid = ExecutionTracker.log(AGENT_MAP.llm, "RUNNING", parent=parent_log)
            response = self.client.models.generate_content(
                model=GEMINI_MODEL, contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                )
            )
            ExecutionTracker.update(llm_logid, "COMPLETED")
            return {
                "success": True,
                "title": "Response Generated",
                "message": None,
                "response_type": "markdown",
                "response": response.text,
                "metadata": {
                    "llm_used": True,
                    "fallback_used": False,
                    "cache_used": False
                }
            }
        except Exception:
            ExecutionTracker.update(llm_logid, "FAILED")

            if task == "classification":
                return {
                    "success": False,
                    "title": "Classification LLM Unavailable",
                    "message": "LLM classification failed. Supervisor will use rule-based routing.",
                    "response": None,
                    "response_type": "classification_failure",
                    "metadata": {
                        "llm_used": False,
                        "fallback_used": False,
                        "cache_used": False
                    }
                }

            fallback_manager = FallbackManager()
            return fallback_manager.handle(task=task, query=query, session_id=session_id, parent_log=parent_log)