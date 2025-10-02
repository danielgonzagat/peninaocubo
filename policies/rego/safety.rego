# PENIN-Ω Safety Policy (Σ-Guard)
# ==================================
#
# Implements Σ-Guard fail-closed gates for:
# - Contractivity (ρ < 1)
# - Calibration (ECE ≤ 0.01)
# - Bias (ρ_bias ≤ 1.05)
# - Reflexivity (SR-Ω∞ ≥ 0.80)
# - Coherence (Ω-ΣEA ≥ 0.85)
# - Death Gate (ΔL∞ ≥ β_min)
# - Cost control
# - Kappa validation
# - Consent
# - Ecological impact
#
# Reference: Equation 15 (Σ-Guard Gate)

package penin.safety

import rego.v1

# Default deny - fail-closed
default allow := false
default gate_pass := false

# ============================================================================
# INDIVIDUAL GATES
# ============================================================================

# Gate 1: Contractivity (ρ < 1)
gate_contractivity_pass if {
    input.metrics.rho < 1.0
}

# Gate 2: Calibration (ECE ≤ 0.01)
gate_calibration_pass if {
    input.metrics.ece <= 0.01
}

# Gate 3: Bias (ρ_bias ≤ 1.05)
gate_bias_pass if {
    input.metrics.rho_bias <= 1.05
}

# Gate 4: Reflexivity (SR-Ω∞ ≥ 0.80)
gate_reflexivity_pass if {
    input.metrics.sr_score >= 0.80
}

# Gate 5: Coherence (Ω-ΣEA ≥ 0.85)
gate_coherence_pass if {
    input.metrics.omega_g >= 0.85
}

# Gate 6: Death Gate (ΔL∞ ≥ β_min)
gate_death_pass if {
    input.metrics.delta_linf >= input.config.beta_min
}

# Gate 7: Cost Control (increase ≤ 10%)
gate_cost_pass if {
    input.metrics.cost_increase <= 0.10
}

# Gate 8: Kappa Validation (κ ≥ 20)
gate_kappa_pass if {
    input.metrics.kappa >= 20.0
}

# Gate 9: Consent
gate_consent_pass if {
    input.consent == true
}

# Gate 10: Ecological
gate_ecological_pass if {
    input.eco_ok == true
}

gate_ecological_pass if {
    input.metrics.energy_kwh <= 10.0
    input.metrics.carbon_kg <= 1.0
}

# ============================================================================
# NON-COMPENSATORY AGGREGATION - ALL MUST PASS
# ============================================================================

all_gates_pass if {
    gate_contractivity_pass
    gate_calibration_pass
    gate_bias_pass
    gate_reflexivity_pass
    gate_coherence_pass
    gate_death_pass
    gate_cost_pass
    gate_kappa_pass
    gate_consent_pass
    gate_ecological_pass
}

# Main gate decision
gate_pass if {
    all_gates_pass
}

# Compatibility with allow
allow if {
    gate_pass
}

# ============================================================================
# GATE RESULTS (for detailed reporting)
# ============================================================================

gate_results := {
    "contractivity": gate_contractivity_pass,
    "calibration": gate_calibration_pass,
    "bias": gate_bias_pass,
    "reflexivity": gate_reflexivity_pass,
    "coherence": gate_coherence_pass,
    "death": gate_death_pass,
    "cost": gate_cost_pass,
    "kappa": gate_kappa_pass,
    "consent": gate_consent_pass,
    "ecological": gate_ecological_pass,
}

failed_gates := [name |
    some name, passed in gate_results
    passed == false
]

# ============================================================================
# ACTION DETERMINATION
# ============================================================================

# Determine action based on gate results
action := "promote" if {
    all_gates_pass
}

action := "rollback" if {
    not all_gates_pass
    count(failed_gates) > 0
}

action := "block" if {
    not all_gates_pass
    count(failed_gates) == 0  # Edge case: no gates evaluated
}

# ============================================================================
# VERDICT
# ============================================================================

verdict := {
    "passed": gate_pass,
    "action": action,
    "gates": gate_results,
    "failed_gates": failed_gates,
    "num_gates": count(gate_results),
    "num_failed": count(failed_gates),
    "timestamp": time.now_ns(),
}

# ============================================================================
# BUDGET CONTROL
# ============================================================================

budget_ok if {
    input.budget.used_pct < 0.95  # Soft cutoff
}

budget_hard_stop if {
    input.budget.used_pct >= 1.00  # Hard cutoff
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Check if value is within range
in_range(value, min_val, max_val) if {
    value >= min_val
    value <= max_val
}

# Validate threshold
exceeds_threshold(value, threshold) if {
    value > threshold
}

below_threshold(value, threshold) if {
    value < threshold
}
