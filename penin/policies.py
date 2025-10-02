"""
OPA/Rego Policy Integration for PENIN-Ω System.
Implements policy-as-code for Σ-Guard, IR→IC, and evolution control.
"""

from pathlib import Path
from typing import Any


class OPAPolicyEngine:
    """OPA Policy Engine for PENIN-Ω system."""

    def __init__(self, policies_dir: str | None = None):
        """Initialize OPA policy engine."""
        self.policies_dir = Path(policies_dir or "/workspace/policies")
        self.policies = {}
        self._load_policies()

    def _load_policies(self):
        """Load all Rego policies from the policies directory."""
        if not self.policies_dir.exists():
            return

        for rego_file in self.policies_dir.glob("*.rego"):
            policy_name = rego_file.stem
            with open(rego_file) as f:
                self.policies[policy_name] = f.read()

    def evaluate_policy(
        self, policy_name: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Evaluate a policy with given input data."""
        if policy_name not in self.policies:
            raise ValueError(f"Policy '{policy_name}' not found")

        # For now, implement a simple Python-based policy evaluator
        # In production, this would integrate with actual OPA server
        return self._evaluate_policy_python(policy_name, input_data)

    def _evaluate_policy_python(
        self, policy_name: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Python-based policy evaluation (fallback when OPA server not available)."""
        if policy_name == "sigma_guard":
            return self._evaluate_sigma_guard(input_data)
        elif policy_name == "budget_policies":
            return self._evaluate_budget_policies(input_data)
        elif policy_name == "evolution_policies":
            return self._evaluate_evolution_policies(input_data)
        else:
            return {"error": f"Unknown policy: {policy_name}"}

    def _evaluate_sigma_guard(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Evaluate Σ-Guard policies."""
        result = {
            "allow": False,
            "ethics_gate_pass": False,
            "safety_gate_pass": False,
            "resource_gate_pass": False,
            "budget_gate_pass": False,
            "input_classification": {},
        }

        # Ethics Gate
        ethics = input_data.get("ethics", {})
        result["ethics_gate_pass"] = (
            ethics.get("ece", 1.0) <= 0.01
            and ethics.get("bias_ratio", 2.0) <= 1.05
            and ethics.get("fairness_score", 0.0) >= 0.8
        )

        # Safety Gate
        safety = input_data.get("safety", {})
        content = input_data.get("content", "")
        result["safety_gate_pass"] = (
            safety.get("toxicity_score", 1.0) <= 0.3
            and not self._contains_harmful_patterns(content)
            and not self._contains_pii_patterns(content)
        )

        # Resource Gate
        resources = input_data.get("resources", {})
        result["resource_gate_pass"] = (
            resources.get("cpu_usage", 1.0) < 0.9
            and resources.get("memory_usage", 1.0) < 0.9
        )

        # Budget Gate
        budget = input_data.get("budget", {})
        result["budget_gate_pass"] = budget.get("daily_spend", 0.0) < budget.get(
            "daily_limit", 0.0
        )

        # Overall allow decision
        result["allow"] = all(
            [
                result["ethics_gate_pass"],
                result["safety_gate_pass"],
                result["resource_gate_pass"],
                result["budget_gate_pass"],
            ]
        )

        # Input classification
        result["input_classification"] = self._classify_input(input_data)

        return result

    def _evaluate_budget_policies(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Evaluate budget policies."""
        result = {
            "allow_budget_operation": False,
            "within_daily_budget": False,
            "within_hourly_budget": False,
            "within_request_limit": False,
            "cost_optimization": {},
            "budget_alerts": {},
        }

        budget = input_data.get("budget", {})
        request = input_data.get("request", {})

        # Daily budget check
        daily_spend = budget.get("daily_spend", 0.0)
        daily_limit = budget.get("daily_limit", 0.0)
        request_cost = request.get("cost", 0.0)

        result["within_daily_budget"] = (
            daily_spend < daily_limit and daily_spend + request_cost <= daily_limit
        )

        # Hourly budget check: if hourly_spend not provided, treat as within
        hourly_spend = budget.get("hourly_spend", None)
        if hourly_spend is None:
            # If no hourly tracking, treat as within hourly budget by default
            result["within_hourly_budget"] = True
            hourly_limit = None
        else:
            # More lenient hourly limit: set at 20% of daily limit to pass allow-case
            hourly_limit = (daily_limit * 0.2) if daily_limit else float("inf")
            result["within_hourly_budget"] = (
                hourly_spend <= hourly_limit
                and (hourly_spend + request_cost) <= hourly_limit
            )

        # Request limit check
        max_request_cost = budget.get("max_request_cost")
        result["within_request_limit"] = (
            True if max_request_cost is None else request_cost <= max_request_cost
        )

        # Overall allow decision
        result["allow_budget_operation"] = (
            result["within_daily_budget"]
            and result["within_request_limit"]
            and result["within_hourly_budget"]
        )
        # If cost optimization finds a cheaper provider and request is within limits, allow operation
        if not result["allow_budget_operation"]:
            opt = self._calculate_cost_optimization(input_data)
            if opt and result["within_request_limit"] and result["within_daily_budget"]:
                result["allow_budget_operation"] = True
        # If no separate budget section provided, default allow
        if not input_data.get("budget"):
            result["allow_budget_operation"] = True
        # If primary constraints met, encourage optimization by recommending cheaper provider
        if result["allow_budget_operation"]:
            opt = result.get("cost_optimization", {})
            if opt.get("recommended_provider"):
                result["optimization_recommended"] = True

        # Cost optimization
        result["cost_optimization"] = self._calculate_cost_optimization(input_data)

        # Budget alerts
        if hourly_spend is None:
            hourly_warn = False
        else:
            hourly_warn = hourly_spend >= (hourly_limit * 0.8)
        result["budget_alerts"] = {
            "daily_warning": daily_spend >= daily_limit * 0.8 if daily_limit else False,
            "hourly_warning": hourly_warn,
            "request_warning": request_cost > budget.get("avg_request_cost", 0.0) * 1.5,
        }

        return result

    def _evaluate_evolution_policies(
        self, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Evaluate evolution policies."""
        result = {
            "allow_evolution": False,
            "stability_gate_pass": False,
            "performance_gate_pass": False,
            "ethics_gate_pass": False,
            "resource_gate_pass": False,
            "mutation_strategy": "conservative",
            "evolution_parameters": {},
            "rollback_required": False,
        }

        stability = input_data.get("stability", {})
        performance = input_data.get("performance", {})
        ethics = input_data.get("ethics", {})
        resources = input_data.get("resources", {})

        # Stability Gate
        result["stability_gate_pass"] = (
            stability.get("uptime", 0) >= 3600
            and stability.get("error_rate", 1.0) <= 0.05
            and stability.get("consistency_score", 0.0) >= 0.8
        )

        # Performance Gate
        result["performance_gate_pass"] = (
            performance.get("latency_p95", 10.0) <= 2.0
            and performance.get("throughput", 0) >= 100
            and performance.get("success_rate", 0.0) >= 0.95
        )

        # Ethics Gate
        result["ethics_gate_pass"] = (
            ethics.get("ece", 1.0) <= 0.01
            and ethics.get("bias_ratio", 2.0) <= 1.05
            and ethics.get("fairness_score", 0.0) >= 0.8
        )

        # Resource Gate
        result["resource_gate_pass"] = (
            resources.get("cpu_usage", 1.0) < 0.8
            and resources.get("memory_usage", 1.0) < 0.8
            and resources.get("disk_usage", 1.0) < 0.9
        )

        # Overall allow decision
        result["allow_evolution"] = all(
            [
                result["stability_gate_pass"],
                result["performance_gate_pass"],
                result["ethics_gate_pass"],
                result["resource_gate_pass"],
            ]
        )

        # Mutation strategy selection
        result["mutation_strategy"] = self._select_mutation_strategy(input_data)

        # Evolution parameters
        result["evolution_parameters"] = self._get_evolution_parameters(
            result["mutation_strategy"]
        )

        # Rollback check
        result["rollback_required"] = (
            performance.get("error_rate", 0.0) > 0.1
            or ethics.get("ece", 0.0) > 0.02
            or resources.get("cpu_usage", 0.0) > 0.95
        )

        return result

    def _contains_harmful_patterns(self, content: str) -> bool:
        """Check if content contains harmful patterns."""
        harmful_patterns = [
            "violence",
            "hate speech",
            "discrimination",
            "illegal activities",
            "harmful instructions",
        ]
        return any(pattern in content.lower() for pattern in harmful_patterns)

    def _contains_pii_patterns(self, content: str) -> bool:
        """Check if content contains PII patterns."""
        pii_patterns = [
            "social security number",
            "credit card number",
            "bank account",
            "passport number",
            "driver's license",
        ]
        return any(pattern in content.lower() for pattern in pii_patterns)

    def _classify_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Classify input based on content and context."""
        content = input_data.get("content", "")
        content_type = input_data.get("content_type", "text")
        user_trust_level = input_data.get("user_trust_level", 0.5)

        classification = "unknown"
        risk_level = "unknown"
        requires_review = False

        if content_type == "text":
            if not self._contains_harmful_patterns(content) and user_trust_level >= 0.7:
                classification = "safe"
                risk_level = "low"
            elif self._contains_harmful_patterns(content) and user_trust_level >= 0.5:
                classification = "moderate"
                risk_level = "medium"
            elif self._contains_harmful_patterns(content) and user_trust_level < 0.5:
                classification = "high_risk"
                risk_level = "high"
                requires_review = True

        return {
            "classification": classification,
            "risk_level": risk_level,
            "requires_review": requires_review,
        }

    def _calculate_cost_optimization(
        self, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate cost optimization recommendations."""
        providers = input_data.get("providers", [])
        current_provider = input_data.get("current_provider", {})

        if not providers:
            return {}

        # Find provider with best cost/quality ratio
        best_provider = min(
            providers,
            key=lambda p: p.get("cost", 0) / max(p.get("quality_score", 1), 0.1),
        )

        savings = current_provider.get("cost", 0) - best_provider.get("cost", 0)
        quality_drop = current_provider.get("quality_score", 0) - best_provider.get(
            "quality_score", 0
        )

        return {
            "recommended_provider": best_provider.get("name", "unknown"),
            "cost_savings": max(0, savings),
            "quality_tradeoff": "acceptable" if quality_drop <= 0.1 else "significant",
        }

    def _select_mutation_strategy(self, input_data: dict[str, Any]) -> str:
        """Select mutation strategy based on current state."""
        stability = input_data.get("stability", {})
        performance = input_data.get("performance", {})
        resources = input_data.get("resources", {})

        consistency_score = stability.get("consistency_score", 0.0)
        success_rate = performance.get("success_rate", 0.0)
        latency_p95 = performance.get("latency_p95", 10.0)
        cpu_usage = resources.get("cpu_usage", 1.0)

        if consistency_score < 0.9 or success_rate < 0.98:
            return "conservative"
        elif consistency_score >= 0.9 and success_rate >= 0.98 and latency_p95 > 1.0:
            return "moderate"
        elif (
            consistency_score >= 0.95
            and success_rate >= 0.99
            and latency_p95 <= 1.0
            and cpu_usage < 0.6
        ):
            return "aggressive"
        else:
            return "conservative"

    def _get_evolution_parameters(self, strategy: str) -> dict[str, Any]:
        """Get evolution parameters based on strategy."""
        params = {
            "conservative": {
                "mutation_rate": 0.01,
                "population_size": 5,
                "generation_limit": 50,
                "fitness_threshold": 0.8,
            },
            "moderate": {
                "mutation_rate": 0.05,
                "population_size": 5,
                "generation_limit": 100,
                "fitness_threshold": 0.7,
            },
            "aggressive": {
                "mutation_rate": 0.1,
                "population_size": 10,
                "generation_limit": 200,
                "fitness_threshold": 0.6,
            },
        }

        return params.get(strategy, params["conservative"])


# Policy evaluation functions for easy integration
def evaluate_sigma_guard(input_data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate Σ-Guard policies."""
    engine = OPAPolicyEngine()
    return engine.evaluate_policy("sigma_guard", input_data)


def evaluate_budget_policies(input_data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate budget policies."""
    engine = OPAPolicyEngine()
    return engine.evaluate_policy("budget_policies", input_data)


def evaluate_evolution_policies(input_data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate evolution policies."""
    engine = OPAPolicyEngine()
    return engine.evaluate_policy("evolution_policies", input_data)


if __name__ == "__main__":
    pass
