"""
PENIN-Ω Evaluators Module
=========================

Implements evaluation batteries for U/S/C/L metrics (Utility, Stability, Cost, Learning).
Provides deterministic tasks and scoring for model assessment.
"""

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class EvaluationResult:
    """Result of an evaluation"""

    task_id: str
    metric_type: str  # U, S, C, or L
    score: float  # Normalized [0,1]
    raw_metrics: dict[str, Any]
    evidence: dict[str, Any]
    latency_ms: float
    cost_usd: float


@dataclass
class TaskBatteryConfig:
    """Configuration for evaluation tasks"""

    seed: int = 42
    timeout_seconds: int = 30
    max_tasks_per_metric: int = 5
    include_synthetic: bool = True
    include_real_world: bool = True


class UtilityEvaluator:
    """Evaluates utility (U) - accuracy, correctness, helpfulness"""

    def __init__(self, config: TaskBatteryConfig = None):
        self.config = config or TaskBatteryConfig()

    def evaluate_utility(
        self, model_fn, tasks: list[dict] = None
    ) -> list[EvaluationResult]:
        """Evaluate model utility across tasks"""
        if tasks is None:
            tasks = self._get_default_utility_tasks()

        results = []
        for task in tasks[: self.config.max_tasks_per_metric]:
            start_time = time.time()

            try:
                # Run model on task
                response = model_fn(task["input"])
                latency_ms = (time.time() - start_time) * 1000

                # Score response
                score = self._score_utility_response(response, task)

                # Create result
                result = EvaluationResult(
                    task_id=task["id"],
                    metric_type="U",
                    score=score,
                    raw_metrics={
                        "exact_match": score,
                        "response_length": len(str(response)),
                    },
                    evidence={"task_type": task["type"], "expected": task["expected"]},
                    latency_ms=latency_ms,
                    cost_usd=0.001,  # Estimated
                )
                results.append(result)

            except Exception as e:
                # Failed task gets 0 score
                result = EvaluationResult(
                    task_id=task["id"],
                    metric_type="U",
                    score=0.0,
                    raw_metrics={"error": str(e)},
                    evidence={"task_type": task["type"], "failed": True},
                    latency_ms=(time.time() - start_time) * 1000,
                    cost_usd=0.001,
                )
                results.append(result)

        return results

    def _get_default_utility_tasks(self) -> list[dict]:
        """Get default utility evaluation tasks"""
        return [
            {
                "id": "math_basic",
                "type": "arithmetic",
                "input": "What is 15 + 27?",
                "expected": "42",
            },
            {
                "id": "json_extract",
                "type": "structured",
                "input": 'Extract the name from: {"user": {"name": "Alice", "age": 30}}',
                "expected": "Alice",
            },
            {
                "id": "text_summary",
                "type": "summarization",
                "input": "Summarize in one sentence: The quick brown fox jumps over the lazy dog. This is a common pangram used in typing practice.",
                "expected": "pangram",  # Key concept should be mentioned
            },
        ]

    def _score_utility_response(self, response: str, task: dict) -> float:
        """Score utility response"""
        response_str = str(response).lower().strip()
        expected = str(task["expected"]).lower().strip()

        if task["type"] == "arithmetic":
            # Exact match for math
            return 1.0 if expected in response_str else 0.0
        elif task["type"] == "structured":
            # Check if expected value is extracted
            return 1.0 if expected in response_str else 0.0
        elif task["type"] == "summarization":
            # Check if key concept is mentioned
            return 1.0 if expected in response_str else 0.5
        else:
            # Default: partial credit for containing expected
            return 1.0 if expected in response_str else 0.0


class StabilityEvaluator:
    """Evaluates stability (S) - consistency, robustness, calibration"""

    def __init__(self, config: TaskBatteryConfig = None):
        self.config = config or TaskBatteryConfig()

    def evaluate_stability(
        self, model_fn, tasks: list[dict] = None
    ) -> list[EvaluationResult]:
        """Evaluate model stability"""
        if tasks is None:
            tasks = self._get_default_stability_tasks()

        results = []
        for task in tasks[: self.config.max_tasks_per_metric]:
            start_time = time.time()

            try:
                # Run same task multiple times
                responses = []
                for _ in range(3):  # 3 runs for consistency check
                    response = model_fn(task["input"])
                    responses.append(str(response))

                latency_ms = (time.time() - start_time) * 1000

                # Score consistency
                score = self._score_stability_responses(responses, task)

                result = EvaluationResult(
                    task_id=task["id"],
                    metric_type="S",
                    score=score,
                    raw_metrics={"consistency": score, "num_runs": len(responses)},
                    evidence={"task_type": task["type"], "responses": responses},
                    latency_ms=latency_ms,
                    cost_usd=0.003,  # 3 runs
                )
                results.append(result)

            except Exception as e:
                result = EvaluationResult(
                    task_id=task["id"],
                    metric_type="S",
                    score=0.0,
                    raw_metrics={"error": str(e)},
                    evidence={"task_type": task["type"], "failed": True},
                    latency_ms=(time.time() - start_time) * 1000,
                    cost_usd=0.003,
                )
                results.append(result)

        return results

    def _get_default_stability_tasks(self) -> list[dict]:
        """Get default stability tasks"""
        return [
            {
                "id": "deterministic_math",
                "type": "deterministic",
                "input": "What is 2 + 2?",
                "expected_consistency": True,
            },
            {
                "id": "classification",
                "type": "classification",
                "input": 'Classify sentiment: "I love this product!"',
                "expected_consistency": True,
            },
        ]

    def _score_stability_responses(self, responses: list[str], task: dict) -> float:
        """Score response consistency"""
        if len(responses) < 2:
            return 0.0

        # Simple consistency: all responses should be similar
        first_response = responses[0].lower().strip()
        consistent_count = sum(
            1 for r in responses if r.lower().strip() == first_response
        )

        return consistent_count / len(responses)


class CostEvaluator:
    """Evaluates cost (C) - efficiency, resource usage"""

    def __init__(self, config: TaskBatteryConfig = None):
        self.config = config or TaskBatteryConfig()

    def evaluate_cost(
        self, model_fn, tasks: list[dict] = None
    ) -> list[EvaluationResult]:
        """Evaluate model cost efficiency"""
        if tasks is None:
            tasks = self._get_default_cost_tasks()

        results = []
        for task in tasks[: self.config.max_tasks_per_metric]:
            start_time = time.time()

            try:
                response = model_fn(task["input"])
                latency_ms = (time.time() - start_time) * 1000

                # Score based on efficiency (lower latency = higher score)
                score = self._score_cost_efficiency(latency_ms, len(str(response)))

                result = EvaluationResult(
                    task_id=task["id"],
                    metric_type="C",
                    score=score,
                    raw_metrics={
                        "latency_ms": latency_ms,
                        "response_length": len(str(response)),
                    },
                    evidence={"task_type": task["type"]},
                    latency_ms=latency_ms,
                    cost_usd=latency_ms * 0.00001,  # Rough estimate
                )
                results.append(result)

            except Exception as e:
                result = EvaluationResult(
                    task_id=task["id"],
                    metric_type="C",
                    score=0.0,
                    raw_metrics={"error": str(e)},
                    evidence={"task_type": task["type"], "failed": True},
                    latency_ms=(time.time() - start_time) * 1000,
                    cost_usd=0.001,
                )
                results.append(result)

        return results

    def _get_default_cost_tasks(self) -> list[dict]:
        """Get default cost evaluation tasks"""
        return [
            {"id": "simple_query", "type": "simple", "input": "Hello"},
            {
                "id": "medium_query",
                "type": "medium",
                "input": "Explain the concept of machine learning in simple terms",
            },
        ]

    def _score_cost_efficiency(self, latency_ms: float, response_length: int) -> float:
        """Score cost efficiency (higher score = more efficient)"""
        # Normalize latency (assume 1000ms is baseline)
        latency_score = max(0.0, 1.0 - (latency_ms / 1000.0))

        # Normalize response length (assume 100 chars is good)
        length_score = min(1.0, response_length / 100.0) if response_length > 0 else 0.0

        # Combined score (efficiency vs quality trade-off)
        return (latency_score + length_score) / 2.0


class LearningEvaluator:
    """Evaluates learning (L) - adaptation, improvement, tool use"""

    def __init__(self, config: TaskBatteryConfig = None):
        self.config = config or TaskBatteryConfig()

    def evaluate_learning(
        self, model_fn, tasks: list[dict] = None
    ) -> list[EvaluationResult]:
        """Evaluate model learning capabilities"""
        if tasks is None:
            tasks = self._get_default_learning_tasks()

        results = []
        for task in tasks[: self.config.max_tasks_per_metric]:
            start_time = time.time()

            try:
                response = model_fn(task["input"])
                latency_ms = (time.time() - start_time) * 1000

                # Score learning indicators
                score = self._score_learning_response(str(response), task)

                result = EvaluationResult(
                    task_id=task["id"],
                    metric_type="L",
                    score=score,
                    raw_metrics={"learning_score": score},
                    evidence={"task_type": task["type"]},
                    latency_ms=latency_ms,
                    cost_usd=0.001,
                )
                results.append(result)

            except Exception as e:
                result = EvaluationResult(
                    task_id=task["id"],
                    metric_type="L",
                    score=0.0,
                    raw_metrics={"error": str(e)},
                    evidence={"task_type": task["type"], "failed": True},
                    latency_ms=(time.time() - start_time) * 1000,
                    cost_usd=0.001,
                )
                results.append(result)

        return results

    def _get_default_learning_tasks(self) -> list[dict]:
        """Get default learning tasks"""
        return [
            {
                "id": "pattern_recognition",
                "type": "pattern",
                "input": "What comes next: 2, 4, 8, 16, ?",
                "learning_indicators": ["pattern", "sequence", "double"],
            },
            {
                "id": "tool_usage",
                "type": "tool",
                "input": "How would you calculate the square root of 144?",
                "learning_indicators": ["calculate", "math", "tool"],
            },
        ]

    def _score_learning_response(self, response: str, task: dict) -> float:
        """Score learning capabilities"""
        response_lower = response.lower()

        if "learning_indicators" in task:
            indicators = task["learning_indicators"]
            found_indicators = sum(
                1 for indicator in indicators if indicator in response_lower
            )
            return found_indicators / len(indicators)

        # Default: check for reasoning words
        reasoning_words = [
            "because",
            "therefore",
            "pattern",
            "rule",
            "method",
            "approach",
        ]
        found_reasoning = sum(1 for word in reasoning_words if word in response_lower)
        return min(1.0, found_reasoning / 3.0)  # Cap at 1.0


class TaskBattery:
    """Main evaluation orchestrator"""

    def __init__(self, config: TaskBatteryConfig = None):
        self.config = config or TaskBatteryConfig()
        self.utility_evaluator = UtilityEvaluator(config)
        self.stability_evaluator = StabilityEvaluator(config)
        self.cost_evaluator = CostEvaluator(config)
        self.learning_evaluator = LearningEvaluator(config)

    def evaluate_all_metrics(self, model_fn) -> dict[str, Any]:
        """Run complete evaluation battery"""
        results = {
            "U": self.utility_evaluator.evaluate_utility(model_fn),
            "S": self.stability_evaluator.evaluate_stability(model_fn),
            "C": self.cost_evaluator.evaluate_cost(model_fn),
            "L": self.learning_evaluator.evaluate_learning(model_fn),
        }

        # Calculate aggregate scores
        aggregates = {}
        for metric_type, evals in results.items():
            if evals:
                scores = [e.score for e in evals]
                aggregates[metric_type] = {
                    "mean": sum(scores) / len(scores),
                    "min": min(scores),
                    "max": max(scores),
                    "count": len(scores),
                }
            else:
                aggregates[metric_type] = {
                    "mean": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "count": 0,
                }

        return {
            "detailed_results": results,
            "aggregate_scores": aggregates,
            "overall_score": sum(agg["mean"] for agg in aggregates.values()) / 4.0,
        }


# Quick evaluation function
def quick_evaluate_model(model_fn, max_tasks: int = 2) -> dict[str, float]:
    """Quick model evaluation"""
    config = TaskBatteryConfig(max_tasks_per_metric=max_tasks)
    battery = TaskBattery(config)
    results = battery.evaluate_all_metrics(model_fn)

    return {
        "U": results["aggregate_scores"]["U"]["mean"],
        "S": results["aggregate_scores"]["S"]["mean"],
        "C": results["aggregate_scores"]["C"]["mean"],
        "L": results["aggregate_scores"]["L"]["mean"],
        "overall": results["overall_score"],
    }
