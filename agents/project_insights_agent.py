from utils.execution_tracker import ExecutionTracker
from utils.agent_map import AGENT_MAP

from tools.project_insights_analyzer import ProjectInsightsAnalyzer

import os


class ProjectInsightsAgent:

    def execute(self, project_path, parent=None):

        project_agent_logid = ExecutionTracker.log(
            AGENT_MAP.project_agent, "RUNNING", parent=parent)

        try:
            project_insights = ProjectInsightsAnalyzer(project_path)
            insights = project_insights.analyze()

            ExecutionTracker.update(project_agent_logid, "COMPLETED")
            return {
                "task": "project_analysis",
                "agent": AGENT_MAP.project_agent,
                "success": True,
                "title": "Project Architecture",
                "message": "Project analyzed successfully.",
                "response_type": "project_insights",
                "response": insights,
                "metadata": {
                    "llm_used": False,
                    "cache_used": False,
                    "fallback_used": False
                }
            }
        except Exception as e:
            ExecutionTracker.update(project_agent_logid, "FAILED")
            return {
                "task": "project",
                "agent": AGENT_MAP.project_agent,
                "success": False,
                "title": "Project Analysis Failed",
                "message": str(e),
                "response_type": "project_insights",
                "response": None,
                "metadata": {
                    "llm_used": False,
                    "cache_used": False,
                    "fallback_used": False
                }
            }