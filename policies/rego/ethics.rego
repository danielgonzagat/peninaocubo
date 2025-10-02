# PENIN-Ω Ethics Policy (ΣEA/LO-14)
# =====================================
# 
# Implements fail-closed ethical validation for all 14 Origin Laws.
# Based on penin/ethics/laws.py implementation.
#
# Reference: docs/ethics.md, PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md

package penin.ethics

import rego.v1

# Default deny - fail-closed
default allow := false

# ============================================================================
# MAIN ALLOW RULE - ALL CONDITIONS MUST BE TRUE
# ============================================================================

allow if {
    # Spiritual boundaries (LO-01, LO-02)
    not input.contains_religious_claims
    not input.contains_occult_content
    not input.claims_consciousness
    
    # Safety (LO-03, LO-04)
    input.physical_risk <= 0.01
    input.emotional_risk <= 0.05
    
    # Privacy & Transparency (LO-05, LO-06)
    input.privacy_score >= 0.95
    input.transparency_score >= 0.90
    input.has_pii == false or input.consent_obtained == true
    
    # Consent & Autonomy (LO-07, LO-08)
    input.consent_obtained == true
    input.autonomy_preserved == true
    
    # Fairness & Beneficence (LO-09, LO-10)
    input.fairness_score >= 0.95
    input.rho_bias <= 1.05
    input.benefits_others == true
    
    # Non-Maleficence & Responsibility (LO-11, LO-12)
    input.harm_potential <= 0.01
    input.accountability_clear == true
    input.audit_trail_exists == true
    
    # Sustainability & Humility (LO-13, LO-14)
    input.environmental_impact_acceptable == true
    input.uncertainty_acknowledged == true
    input.limitations_disclosed == true
}

# ============================================================================
# INDIVIDUAL LAW CHECKS (for detailed reporting)
# ============================================================================

# LO-01: Anti-Idolatria
violation_lo01 if {
    input.contains_religious_claims == true
}

violation_lo01 if {
    input.claims_consciousness == true
}

violation_lo01 if {
    contains(lower(input.decision_output), "worship")
}

violation_lo01 if {
    contains(lower(input.decision_output), "divine")
}

# LO-02: Anti-Ocultismo
violation_lo02 if {
    input.contains_occult_content == true
}

violation_lo02 if {
    contains(lower(input.decision_output), "magic")
}

violation_lo02 if {
    contains(lower(input.decision_output), "spell")
}

# LO-03: Anti-Dano Físico
violation_lo03 if {
    input.physical_risk > 0.01
}

violation_lo03 if {
    contains(lower(input.decision_output), "weapon")
}

violation_lo03 if {
    contains(lower(input.decision_output), "harm")
}

# LO-04: Anti-Dano Emocional
violation_lo04 if {
    input.emotional_risk > 0.05
}

violation_lo04 if {
    contains(lower(input.decision_output), "manipulate")
}

violation_lo04 if {
    contains(lower(input.decision_output), "coerce")
}

# LO-05: Privacidade
violation_lo05 if {
    input.privacy_score < 0.95
}

violation_lo05 if {
    input.has_pii == true
    input.consent_obtained == false
}

# LO-06: Transparência
violation_lo06 if {
    input.transparency_score < 0.90
}

violation_lo06 if {
    input.audit_trail_exists == false
}

# LO-07: Consentimento
violation_lo07 if {
    input.consent_obtained == false
}

violation_lo07 if {
    input.consent_informed == false
}

# LO-09: Justiça (Fairness)
violation_lo09 if {
    input.fairness_score < 0.95
}

violation_lo09 if {
    input.rho_bias > 1.05
}

# LO-11: Não-Maleficência
violation_lo11 if {
    input.harm_potential > 0.01
}

# LO-13: Sustentabilidade
violation_lo13 if {
    input.energy_kwh > 10.0
}

violation_lo13 if {
    input.carbon_kg > 1.0
}

# LO-14: Humildade
violation_lo14 if {
    input.uncertainty_acknowledged == false
}

violation_lo14 if {
    input.limitations_disclosed == false
}

# ============================================================================
# AGGREGATED VIOLATIONS
# ============================================================================

any_critical_violation if {
    violation_lo01
}

any_critical_violation if {
    violation_lo02
}

any_critical_violation if {
    violation_lo03
}

any_critical_violation if {
    violation_lo04
}

any_critical_violation if {
    violation_lo05
}

any_critical_violation if {
    violation_lo07
}

any_violation if {
    any_critical_violation
}

any_violation if {
    violation_lo06
}

any_violation if {
    violation_lo09
}

any_violation if {
    violation_lo11
}

any_violation if {
    violation_lo13
}

any_violation if {
    violation_lo14
}

# ============================================================================
# ENFORCEMENT ACTIONS
# ============================================================================

# Determine action based on violations
action := "rollback" if {
    any_critical_violation
}

action := "block" if {
    any_violation
    not any_critical_violation
}

action := "review" if {
    input.warnings_count > 0
    not any_violation
}

action := "promote" if {
    allow
}

# ============================================================================
# DETAILED VERDICT
# ============================================================================

verdict := {
    "allow": allow,
    "action": action,
    "critical_violations": count([v | some v; violation_lo01; v := "LO-01"]),
    "all_violations": count([v | some v; any_violation; v := "violation"]),
    "timestamp": time.now_ns(),
}
