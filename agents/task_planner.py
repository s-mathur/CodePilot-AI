import config

class TaskPlanner:

    def classify_task(self, query):

        query_lower = query.lower()

        scores = {task: 0 for task in config.TASKS}

        for keywords, task, weight in config.keyword_rules:
            for word in keywords:
                if word.lower() in query_lower:
                    scores[task] += weight

        sorted_tasks = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        best_task = sorted_tasks[0][0]
        best_score = sorted_tasks[0][1]

        second_score = sorted_tasks[1][1] if len(sorted_tasks) > 1 else 0

        if best_score == 0:
            return {
                "task": "general",
                "confidence": 0.0,
                "scores": scores,
                "reason": "No rule matched"
            }

        confidence = min(0.55 + (best_score * 0.10), 0.95)

        if best_score == second_score:
            confidence *= 0.5
            reason = "Multiple tasks have equal scores"
        elif best_score - second_score <= 1:
            confidence *= 0.7
            reason = "Tasks have similar scores"
        else:
            reason = "Strong rule match"

        return {
            "task": best_task,
            "confidence": round(confidence, 2),
            "scores": scores,
            "reason": reason
        }