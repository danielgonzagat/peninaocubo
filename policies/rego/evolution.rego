# PENIN-Ω Auto-Evolution Policy
# ===============================
#
# Champion-Challenger pipeline decisions.
# Implements Liga ACFA promotion/rollback logic.

package penin.evolution

import rego.v1

# Default deny
default allow_promotion := false
default action := "rollback"

# ============================================================================
# PROMOTION CRITERIA (ALL MUST PASS)
# ============================================================================

# Equation validation
math_criteria_met if {
    # ΔL∞ ≥ β_min (Death Gate)
    input.metrics.delta_linf >= input.config.beta_min
    
    # CAOS+ improvement
    input.metrics.caos_plus_post > input.metrics.caos_plus_pre
    
    # SR-Ω∞ reflexivity
    input.metrics.sr_score >= 0.80
    
    # Global coherence
    input.metrics.omega_g >= 0.85
    
    # Kappa valid
    input.metrics.kappa >= 20.0
}

# Safety gates
safety_gates_pass if {
    # Contractivity
    input.metrics.rho < 1.0
    
    # Calibration
    input.metrics.ece <= 0.01
    
    # Bias
    input.metrics.rho_bias <= 1.05
    
    # Cost control
    input.metrics.cost_increase <= 0.10
}

# Ethics gates
ethics_gates_pass if {
    input.ethics.passed == true
    input.ethics.violations_count == 0
}

# Operational constraints
operational_ok if {
    # Error rate didn't increase
    input.metrics.error_rate_delta <= 0.05
    
    # Latency didn't blow up
    input.metrics.latency_increase <= 0.20
    
    # No crashes
    input.metrics.crash_count == 0
    
    # Canary successful
    input.canary.success_rate >= 0.95
}

# ============================================================================
# PROMOTION DECISION
# ============================================================================

allow_promotion if {
    math_criteria_met
    safety_gates_pass
    ethics_gates_pass
    operational_ok
}

action := "promote" if {
    allow_promotion
}

action := "rollback" if {
    not allow_promotion
    not safety_gates_pass
}

action := "quarantine" if {
    not allow_promotion
    not ethics_gates_pass
}

action := "review" if {
    not allow_promotion
    not operational_ok
    safety_gates_pass
    ethics_gates_pass
}

# ============================================================================
# SHADOW MODE
# ============================================================================

# Allow shadow deployment (no real traffic)
allow_shadow if {
    input.mode == "shadow"
    math_criteria_met  # Still need minimal quality
}

# Shadow to canary promotion
allow_shadow_to_canary if {
    input.shadow.observations >= 100  # Minimum observations
    input.shadow.delta_linf_avg >= input.config.beta_min
    input.shadow.error_rate < 0.05
}

# ============================================================================
# CANARY MODE
# ============================================================================

# Canary traffic control
canary_traffic_pct := pct if {
    allow_promotion
    pct := 0.05  # 5% default
}

canary_traffic_pct := 0.0 if {
    not allow_promotion
}

# Canary graduation criteria
allow_canary_graduation if {
    input.canary.observations >= 1000
    input.canary.success_rate >= 0.95
    input.canary.delta_linf_avg >= input.config.beta_min * 1.5  # 50% better than minimum
    input.canary.no_critical_failures == true
}

# ============================================================================
# ROLLBACK TRIGGERS
# ============================================================================

trigger_rollback if {
    input.metrics.delta_linf < 0  # Regression
}

trigger_rollback if {
    input.metrics.error_rate_delta > 0.10  # 10% error increase
}

trigger_rollback if {
    input.metrics.crash_count > 0
}

trigger_rollback if {
    not safety_gates_pass
}

trigger_rollback if {
    not ethics_gates_pass
}

# ============================================================================
# VERDICT
# ============================================================================

verdict := {
    "allow_promotion": allow_promotion,
    "action": action,
    "criteria": {
        "math": math_criteria_met,
        "safety": safety_gates_pass,
        "ethics": ethics_gates_pass,
        "operational": operational_ok,
    },
    "canary": {
        "traffic_pct": canary_traffic_pct,
        "can_graduate": allow_canary_graduation,
    },
    "triggers": {
        "rollback": trigger_rollback,
    },
    "timestamp": time.now_ns(),
}
