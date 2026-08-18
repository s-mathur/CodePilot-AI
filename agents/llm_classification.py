from tools.gemini_tool import GeminiTool

from config import TASKS
import json


class LLMClassification:
    def __init__(self):
        self.gemini = GeminiTool()

    def classify(self, query, session_id=None, parent_log=None):

        prompt = f"""
You are a task routing classifier for a software engineering AI assistant.

Classify the user's request into exactly ONE of these tasks:
{TASKS}

Return ONLY valid JSON:

{{
    "task": "debug",
    "confidence": 0.92,
    "reason": "The user is asking about an exception."
}}

User query:

{query}
"""
        
        result = self.gemini.generate_response(
            task="classification", query=query, prompt=prompt,
            session_id=session_id, parent_log=parent_log)
        if not result.get("success"):
            return {
                "success": False,
                "task": None,
                "confidence": 0,
                "reason": "LLM classification failed"
            }
        response = result["response"]
        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.replace("```json", "").replace("```", "").strip()

            response = json.loads(response)
            confidence = self.normalize_confidence(response.get("confidence", 0))
            return {
                "success": True,
                "task": response["task"],
                "confidence": confidence,
                "reason": response.get("reason")
            }
        except Exception as e:
            return {
                "success": False,
                "task": None,
                "confidence": 0,
                "reason": f"Invalid classifier response: {e}"
            }

    def normalize_confidence(self, value):
        try:
            confidence = float(value)

            # Gemini may return 80 instead of 0.80
            if confidence > 1:
                confidence = confidence / 100

            # Keep confidence between 0 and 1
            confidence = max(0.0, min(1.0, confidence))

            return confidence

        except (TypeError, ValueError):
            return 0.0