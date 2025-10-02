from penin.policies import (
    evaluate_budget_policies,
    evaluate_evolution_policies,
    evaluate_sigma_guard,
)


def test_sigma_guard_allow():
    """Test Σ-Guard policy allowing valid input."""
    input_data = {
        "ethics": {"ece": 0.005, "bias_ratio": 1.02, "fairness_score": 0.85},
        "safety": {"toxicity_score": 0.2},
        "resources": {"cpu_usage": 0.7, "memory_usage": 0.6},
        "budget": {"daily_spend": 2.0, "daily_limit": 5.0},
        "content": "This is a normal text message",
        "content_type": "text",
        "user_trust_level": 0.8,
    }

    result = evaluate_sigma_guard(input_data)

    assert result["allow"] is True
    assert result["ethics_gate_pass"] is True
    assert result["safety_gate_pass"] is True
    assert result["resource_gate_pass"] is True
    assert result["budget_gate_pass"] is True
    assert result["input_classification"]["classification"] == "safe"
    assert result["input_classification"]["risk_level"] == "low"


def test_sigma_guard_deny_ethics():
    """Test Σ-Guard policy denying due to ethics violations."""
    input_data = {
        "ethics": {
            "ece": 0.02,  # Too high
            "bias_ratio": 1.02,
            "fairness_score": 0.85,
        },
        "safety": {"toxicity_score": 0.2},
        "resources": {"cpu_usage": 0.7, "memory_usage": 0.6},
        "budget": {"daily_spend": 2.0, "daily_limit": 5.0},
        "content": "This is a normal text message",
        "content_type": "text",
        "user_trust_level": 0.8,
    }

    result = evaluate_sigma_guard(input_data)

    assert result["allow"] is False
    assert result["ethics_gate_pass"] is False
    assert result["safety_gate_pass"] is True
    assert result["resource_gate_pass"] is True
    assert result["budget_gate_pass"] is True


def test_sigma_guard_deny_safety():
    """Test Σ-Guard policy denying due to safety violations."""
    input_data = {
        "ethics": {"ece": 0.005, "bias_ratio": 1.02, "fairness_score": 0.85},
        "safety": {"toxicity_score": 0.5},  # Too high
        "resources": {"cpu_usage": 0.7, "memory_usage": 0.6},
        "budget": {"daily_spend": 2.0, "daily_limit": 5.0},
        "content": "This message contains violence and hate speech",
        "content_type": "text",
        "user_trust_level": 0.8,
    }

    result = evaluate_sigma_guard(input_data)

    assert result["allow"] is False
    assert result["ethics_gate_pass"] is True
    assert result["safety_gate_pass"] is False
    assert result["resource_gate_pass"] is True
    assert result["budget_gate_pass"] is True


def test_budget_policies_allow():
    """Test budget policies allowing operation."""
    input_data = {
        "budget": {
            "daily_spend": 2.0,
            "daily_limit": 5.0,
            "hourly_spend": 0.1,
            "max_request_cost": 0.5,
            "avg_request_cost": 0.2,
        },
        "request": {"cost": 0.3},
        "providers": [
            {"name": "provider1", "cost": 0.2, "quality_score": 0.9, "available": True},
            {"name": "provider2", "cost": 0.3, "quality_score": 0.95, "available": True},
        ],
        "current_provider": {"name": "provider2", "cost": 0.3, "quality_score": 0.95},
    }

    result = evaluate_budget_policies(input_data)

    assert result["allow_budget_operation"] is True
    assert result["within_daily_budget"] is True
    assert result["within_hourly_budget"] is True
    assert result["within_request_limit"] is True


def test_budget_policies_deny_daily_limit():
    """Test budget policies denying due to daily limit."""
    input_data = {
        "budget": {
            "daily_spend": 4.8,  # Close to limit
            "daily_limit": 5.0,
            "hourly_spend": 0.1,
            "max_request_cost": 0.5,
            "avg_request_cost": 0.2,
        },
        "request": {"cost": 0.5},  # Would exceed daily limit
    }

    result = evaluate_budget_policies(input_data)

    assert result["allow_budget_operation"] is False
    assert result["within_daily_budget"] is False
    assert result["budget_alerts"]["daily_warning"] is True


def test_evolution_policies_allow():
    """Test evolution policies allowing evolution."""
    input_data = {
        "stability": {
            "uptime": 7200,  # 2 hours
            "error_rate": 0.02,
            "consistency_score": 0.9,
        },
        "performance": {"latency_p95": 1.5, "throughput": 150, "success_rate": 0.98},
        "ethics": {"ece": 0.005, "bias_ratio": 1.02, "fairness_score": 0.85},
        "resources": {"cpu_usage": 0.6, "memory_usage": 0.5, "disk_usage": 0.7},
    }

    result = evaluate_evolution_policies(input_data)

    assert result["allow_evolution"] is True
    assert result["stability_gate_pass"] is True
    assert result["performance_gate_pass"] is True
    assert result["ethics_gate_pass"] is True
    assert result["resource_gate_pass"] is True
    assert result["mutation_strategy"] == "moderate"


def test_evolution_policies_deny_stability():
    """Test evolution policies denying due to stability issues."""
    input_data = {
        "stability": {
            "uptime": 1800,  # Only 30 minutes
            "error_rate": 0.08,  # Too high
            "consistency_score": 0.7,  # Too low
        },
        "performance": {"latency_p95": 1.5, "throughput": 150, "success_rate": 0.98},
        "ethics": {"ece": 0.005, "bias_ratio": 1.02, "fairness_score": 0.85},
        "resources": {"cpu_usage": 0.6, "memory_usage": 0.5, "disk_usage": 0.7},
    }

    result = evaluate_evolution_policies(input_data)

    assert result["allow_evolution"] is False
    assert result["stability_gate_pass"] is False
    assert result["performance_gate_pass"] is True
    assert result["ethics_gate_pass"] is True
    assert result["resource_gate_pass"] is True
    assert result["mutation_strategy"] == "conservative"


def test_mutation_strategy_selection():
    """Test mutation strategy selection logic."""
    # Conservative strategy
    input_data_conservative = {
        "stability": {"consistency_score": 0.8},
        "performance": {"success_rate": 0.95},
        "resources": {"cpu_usage": 0.8},
    }

    result = evaluate_evolution_policies(input_data_conservative)
    assert result["mutation_strategy"] == "conservative"
    assert result["evolution_parameters"]["mutation_rate"] == 0.01

    # Moderate strategy
    input_data_moderate = {
        "stability": {"consistency_score": 0.95},
        "performance": {"success_rate": 0.99, "latency_p95": 1.2},
        "resources": {"cpu_usage": 0.7},
    }

    result = evaluate_evolution_policies(input_data_moderate)
    assert result["mutation_strategy"] == "moderate"
    assert result["evolution_parameters"]["mutation_rate"] == 0.05

    # Aggressive strategy
    input_data_aggressive = {
        "stability": {"consistency_score": 0.98},
        "performance": {"success_rate": 0.995, "latency_p95": 0.8},
        "resources": {"cpu_usage": 0.5},
    }

    result = evaluate_evolution_policies(input_data_aggressive)
    assert result["mutation_strategy"] == "aggressive"
    assert result["evolution_parameters"]["mutation_rate"] == 0.1


def test_rollback_conditions():
    """Test rollback condition detection."""
    input_data = {
        "performance": {"error_rate": 0.15},  # Too high
        "ethics": {"ece": 0.03},  # Too high
        "resources": {"cpu_usage": 0.98},  # Too high
    }

    result = evaluate_evolution_policies(input_data)
    assert result["rollback_required"] is True


def test_input_classification():
    """Test input classification logic."""
    # Safe input
    input_data_safe = {"content": "This is a normal message", "content_type": "text", "user_trust_level": 0.8}

    result = evaluate_sigma_guard(input_data_safe)
    classification = result["input_classification"]
    assert classification["classification"] == "safe"
    assert classification["risk_level"] == "low"
    assert classification["requires_review"] is False

    # High risk input
    input_data_risk = {
        "content": "This message contains violence and discrimination",
        "content_type": "text",
        "user_trust_level": 0.3,
    }

    result = evaluate_sigma_guard(input_data_risk)
    classification = result["input_classification"]
    assert classification["classification"] == "high_risk"
    assert classification["risk_level"] == "high"
    assert classification["requires_review"] is True


def test_cost_optimization():
    """Test cost optimization recommendations."""
    input_data = {
        "providers": [
            {"name": "cheap", "cost": 0.1, "quality_score": 0.8, "available": True},
            {"name": "expensive", "cost": 0.5, "quality_score": 0.95, "available": True},
        ],
        "current_provider": {"name": "expensive", "cost": 0.5, "quality_score": 0.95},
    }

    result = evaluate_budget_policies(input_data)
    optimization = result["cost_optimization"]

    assert optimization["recommended_provider"] == "cheap"
    assert optimization["cost_savings"] == 0.4
    assert optimization["quality_tradeoff"] == "significant"
