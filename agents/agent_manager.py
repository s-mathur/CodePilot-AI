from utils.execution_tracker import ExecutionTracker
from utils.session_manager import session_required
from utils.agent_map import AGENT_MAP

from agents.similarity_search_agent import SimilaritySearchAgent
from agents.project_insights_agent import ProjectInsightsAgent
from agents.architecture_agent import ArchitectureAgent
from agents.llm_classification import LLMClassification
from agents.assistant_agent import AssistantAgent
from agents.review_agent import ReviewAgent
from agents.debug_agent import DebugAgent
from agents.task_planner import TaskPlanner

from tools.cache_tool import save_response


class AgentManager:
    CONFIDENCE_THRESHOLD = 0.80
    def __init__(self):
        self.architecture_agent = ArchitectureAgent()
        self.llm_classification = LLMClassification()
        self.search_agent = SimilaritySearchAgent()
        self.project_agent = ProjectInsightsAgent()
        self.assistant_agent = AssistantAgent()
        self.review_agent = ReviewAgent()
        self.taskplanner = TaskPlanner()
        self.debug_agent = DebugAgent()

    @session_required
    def execute(self, session_id, query, project_path, chunks):

        self.session_id = session_id

        agent_manager_logid = ExecutionTracker.log(AGENT_MAP.agent_manager, "RUNNING")

        agent_planner_id = ExecutionTracker.log(AGENT_MAP.task_planner, "RUNNING", parent=agent_manager_logid)

        classification = self.taskplanner.classify_task(query)

        task = classification["task"]
        confidence = classification["confidence"]

        ExecutionTracker.update(agent_planner_id, "COMPLETED",
            details={"Task": task, "Confidence": f"{confidence * 100:.0f}%"})

        if confidence < self.CONFIDENCE_THRESHOLD:
            task = self._llm_classification(query, task, confidence, agent_manager_logid)

        ExecutionTracker.update(agent_manager_logid, "COMPLETED", details=f"Task Identified - {task}")

        response = self._execute_agent(task, query, project_path, chunks)
        if response.get("metadata").get("cache_used") is False:
            save_response(self.session_id, query, response)
        return response

    def _llm_classification(self, query, initial_task, initial_confidence, agent_manager_logid):

        classifier_agent_id = ExecutionTracker.log(AGENT_MAP.classifier_agent, "RUNNING",
            details={
                "Reason": "Low routing confidence",
                "Initial Task": initial_task,
                "Confidence": f"{initial_confidence * 100:.0}%"
            },
            parent=agent_manager_logid
        )

        try:
            result = self.llm_classification.classify(
                query=query, session_id=self.session_id, parent_log=classifier_agent_id)

        except Exception as e:
            # This is for any failure apart from llm call failure
            ExecutionTracker.update(classifier_agent_id, "FAILED")
            return self._classification_fallback(initial_task, agent_manager_logid)

        # LLM returned failure
        if not result.get("success", False):
            ExecutionTracker.update(classifier_agent_id, "FAILED",
                details=result.get("reason", "LLM classification unavailable"))
            return self._classification_fallback(initial_task, agent_manager_logid)

        task = result["task"]
        confidence = result["confidence"]

        ExecutionTracker.update(classifier_agent_id, "COMPLETED",
            details={
                "Task": task,
                "Confidence": f"{confidence:.0%}"
            }
        )

        return task

    def _execute_agent(self, task, query, project_path, chunks):

        if task == "architecture":
            response = self.architecture_agent.execute(self.session_id, query, project_path)

        elif task == "project_analysis":
            response = self.project_agent.execute(project_path)

        elif task == "similar_search":
            response = self.search_agent.execute(query, chunks)

        elif task == "debug":
            response = self.debug_agent.execute(self.session_id, query, chunks)

        elif task == "code_review":
            response = self.review_agent.execute(self.session_id, query, chunks)

        else:
            response = self.assistant_agent.execute(self.session_id, query, chunks, task=task)

        return response

    def _classification_fallback(self, initial_task, agent_manager_id):

        ExecutionTracker.log(AGENT_MAP.llm_fallback_agent, "COMPLETED",
            details={
                "Strategy": "Rule-based routing",
                "Task": initial_task
            },
            parent=agent_manager_id
        )

        ExecutionTracker.update(agent_manager_id, "COMPLETED",
            details=f"Task Identified - {initial_task} (Rule Fallback)")

        return initial_task
