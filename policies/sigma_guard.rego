# Σ-Guard OPA/Rego Policy
# ========================
#
# Fail-closed policy for PENIN-Ω evolution gates.
# All conditions must be satisfied for promotion.

package penin.guard

import future.keywords.if
import future.keywords.in

# Default deny (fail-closed)
default allow := false

# Main allow rule: ALL gates must pass
allow if {
    input.contractivity.rho < input.thresholds.rho_max
    input.calibration.ece <= input.thresholds.ece_max
    input.bias.rho_bias <= input.thresholds.rho_bias_max
    input.reflexivity.sr_score >= input.thresholds.sr_min
    input.coherence.G >= input.thresholds.G_min
    input.improvement.delta_Linf >= input.thresholds.delta_Linf_min
    input.cost.increase <= input.thresholds.cost_max_increase
    input.caos.kappa >= input.thresholds.kappa_min
    consent_granted
    ecological_ok
}

# Consent check
consent_granted if {
    input.consent == true
}

consent_granted if {
    not input.consent_required
}

# Ecological constraints check
ecological_ok if {
    input.eco_ok == true
}

ecological_ok if {
    not input.eco_ok_required
}

# Contractivity gate (IR→IC)
contractivity_ok if {
    input.contractivity.rho < input.thresholds.rho_max
}

# Calibration gate
calibration_ok if {
    input.calibration.ece <= input.thresholds.ece_max
}

# Bias gate
bias_ok if {
    input.bias.rho_bias <= input.thresholds.rho_bias_max
}

# Reflexivity gate (SR-Ω∞)
reflexivity_ok if {
    input.reflexivity.sr_score >= input.thresholds.sr_min
}

# Coherence gate (Ω-ΣEA)
coherence_ok if {
    input.coherence.G >= input.thresholds.G_min
}

# Improvement gate (Death equation)
improvement_ok if {
    input.improvement.delta_Linf >= input.thresholds.delta_Linf_min
}

# Cost control gate
cost_ok if {
    input.cost.increase <= input.thresholds.cost_max_increase
}

# CAOS⁺ kappa gate
kappa_ok if {
    input.caos.kappa >= input.thresholds.kappa_min
}

# Decision logic
decision := "promote" if {
    allow
} else := "canary" if {
    near_threshold
} else := "rollback"

# Near threshold (canary zone)
near_threshold if {
    input.improvement.delta_Linf >= (input.thresholds.delta_Linf_min * 0.95)
    input.contractivity.rho < input.thresholds.rho_max
    input.calibration.ece <= input.thresholds.ece_max
    input.bias.rho_bias <= input.thresholds.rho_bias_max
}

# Reasons for failure
failure_reasons[reason] {
    not contractivity_ok
    reason := sprintf("Contractivity: ρ=%.6f >= %.6f (IR→IC FAIL)", [input.contractivity.rho, input.thresholds.rho_max])
}

failure_reasons[reason] {
    not calibration_ok
    reason := sprintf("Calibration: ECE=%.6f > %.6f", [input.calibration.ece, input.thresholds.ece_max])
}

failure_reasons[reason] {
    not bias_ok
    reason := sprintf("Bias: ρ_bias=%.6f > %.6f", [input.bias.rho_bias, input.thresholds.rho_bias_max])
}

failure_reasons[reason] {
    not reflexivity_ok
    reason := sprintf("Reflexivity: SR=%.4f < %.4f", [input.reflexivity.sr_score, input.thresholds.sr_min])
}

failure_reasons[reason] {
    not coherence_ok
    reason := sprintf("Coherence: G=%.4f < %.4f", [input.coherence.G, input.thresholds.G_min])
}

failure_reasons[reason] {
    not improvement_ok
    reason := sprintf("Improvement: ΔL∞=%.6f < %.6f (DEATH)", [input.improvement.delta_Linf, input.thresholds.delta_Linf_min])
}

failure_reasons[reason] {
    not cost_ok
    reason := sprintf("Cost: increase=%.4f > %.4f", [input.cost.increase, input.thresholds.cost_max_increase])
}

failure_reasons[reason] {
    not kappa_ok
    reason := sprintf("Kappa: κ=%.2f < %.2f", [input.caos.kappa, input.thresholds.kappa_min])
}

failure_reasons[reason] {
    not consent_granted
    reason := "Consent: DENIED"
}

failure_reasons[reason] {
    not ecological_ok
    reason := "Ecological: FAIL"
}
