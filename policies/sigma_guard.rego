package penin.sigma_guard

# Σ-Guard: Ethics and Safety Gate Policies
# Implements fail-closed policies for PENIN-Ω system

import rego.v1

# Default deny policy
default allow := false

# Allow if all gates pass
allow if {
    ethics_gate_pass
    safety_gate_pass
    resource_gate_pass
    budget_gate_pass
}

# Ethics Gate: ECE ≤ 0.01, ρ-bias ≤ 1.05, fairness ≥ 0.8
ethics_gate_pass if {
    input.ethics.ece <= 0.01
    input.ethics.bias_ratio <= 1.05
    input.ethics.fairness_score >= 0.8
}

# Safety Gate: No harmful content, no PII leakage
safety_gate_pass if {
    not contains(input.content, "harmful_patterns")
    not contains(input.content, "pii_patterns")
    input.safety.toxicity_score <= 0.3
}

# Resource Gate: CPU < 90%, Memory < 90%
resource_gate_pass if {
    input.resources.cpu_usage < 0.9
    input.resources.memory_usage < 0.9
}

# Budget Gate: Daily spend < budget limit
budget_gate_pass if {
    input.budget.daily_spend < input.budget.daily_limit
}

# IR→IC (Input Request → Input Classification) policies
input_classification := {
    "classification": classify_input(input),
    "risk_level": assess_risk(input),
    "requires_review": requires_human_review(input)
}

# Classify input based on content and context
classify_input(input) := "safe" if {
    input.content_type == "text"
    not contains(input.content, "sensitive_keywords")
    input.user_trust_level >= 0.7
}

classify_input(input) := "moderate" if {
    input.content_type == "text"
    contains(input.content, "sensitive_keywords")
    input.user_trust_level >= 0.5
}

classify_input(input) := "high_risk" if {
    input.content_type == "text"
    contains(input.content, "sensitive_keywords")
    input.user_trust_level < 0.5
}

classify_input(input) := "unknown" if {
    input.content_type != "text"
}

# Assess risk level
assess_risk(input) := "low" if {
    classify_input(input) == "safe"
}

assess_risk(input) := "medium" if {
    classify_input(input) == "moderate"
}

assess_risk(input) := "high" if {
    classify_input(input) == "high_risk"
}

assess_risk(input) := "unknown" if {
    classify_input(input) == "unknown"
}

# Determine if human review is required
requires_human_review(input) := true if {
    classify_input(input) == "high_risk"
    input.user_trust_level < 0.3
}

requires_human_review(input) := true if {
    input.content_type != "text"
    input.user_trust_level < 0.5
}

requires_human_review(input) := false

# Helper functions
contains(str, pattern) := true if {
    regex.match(pattern, str)
}

# Sensitive keywords patterns
sensitive_keywords := [
    "personal information",
    "financial data",
    "medical records",
    "government secrets",
    "classified information"
]

# Harmful patterns
harmful_patterns := [
    "violence",
    "hate speech",
    "discrimination",
    "illegal activities",
    "harmful instructions"
]

# PII patterns
pii_patterns := [
    "social security number",
    "credit card number",
    "bank account",
    "passport number",
    "driver's license"
]