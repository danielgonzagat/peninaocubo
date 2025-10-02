#!/usr/bin/env python3
"""
PENIN-Ω Cryptographic Attestation - Complete Integration Example
================================================================

This example demonstrates the full end-to-end flow of cryptographic
attestation for model promotions.

Flow:
1. Candidate model is evaluated by SR-Ω∞
2. Candidate is validated by Σ-Guard
3. Both services create cryptographic attestations
4. Attestations are chained together
5. ACFA League validates the chain before promotion
6. Complete proof is stored in WORM Ledger
"""

import importlib.util
import json
import time
from pathlib import Path


# Load modules directly
def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load required modules
attestation = load_module('attestation', 'penin/omega/attestation.py')

print("=" * 80)
print("PENIN-Ω CRYPTOGRAPHIC ATTESTATION - COMPLETE INTEGRATION EXAMPLE")
print("=" * 80)
print()

# ==============================================================================
# Phase 1: Candidate Evaluation
# ==============================================================================
print("Phase 1: Candidate Evaluation")
print("-" * 80)

candidate_id = f"model_v2_{int(time.time())}"
print(f"Evaluating candidate: {candidate_id}")
print()

# Simulated SR-Ω∞ evaluation
print("1.1 SR-Ω∞ Evaluation")
sr_components = {
    "awareness": 0.92,
    "ethics": 1.0,
    "autocorrection": 0.87,
    "metacognition": 0.89
}
sr_score = min(sr_components.values())  # Simplified: min for non-compensatory
sr_passed = sr_score >= 0.80

print(f"  Awareness:      {sr_components['awareness']:.3f}")
print(f"  Ethics:         {sr_components['ethics']:.3f}")
print(f"  Autocorrection: {sr_components['autocorrection']:.3f}")
print(f"  Metacognition:  {sr_components['metacognition']:.3f}")
print(f"  SR-Ω∞ Score:    {sr_score:.3f}")
print(f"  Result:         {'✓ PASS' if sr_passed else '✗ FAIL'}")
print()

# Create SR attestation
sr_verdict = "pass" if sr_passed else "fail"
sr_attestation = attestation.create_sr_attestation(
    verdict=sr_verdict,
    candidate_id=candidate_id,
    sr_score=sr_score,
    components=sr_components
)

print("  ✓ SR-Ω∞ attestation created and signed")
print(f"    Signature: {sr_attestation.signature[:32]}...")
print(f"    Timestamp: {sr_attestation.timestamp}")
print()

# Simulated Σ-Guard evaluation
print("1.2 Σ-Guard Evaluation")
gates = [
    {"name": "contractividade", "value": 0.95, "threshold": 0.99, "passed": True},
    {"name": "calibration", "value": 0.006, "threshold": 0.01, "passed": True},
    {"name": "bias", "value": 1.03, "threshold": 1.05, "passed": True},
    {"name": "self_reflection", "value": sr_score, "threshold": 0.80, "passed": True},
    {"name": "coherence", "value": 0.89, "threshold": 0.85, "passed": True},
    {"name": "improvement", "value": 0.03, "threshold": 0.01, "passed": True},
    {"name": "cost", "value": 0.08, "threshold": 0.10, "passed": True},
    {"name": "kappa", "value": 24.5, "threshold": 20.0, "passed": True},
    {"name": "consent", "value": 1.0, "threshold": 1.0, "passed": True},
    {"name": "ecological", "value": 1.0, "threshold": 1.0, "passed": True},
]

all_gates_passed = all(g["passed"] for g in gates)
aggregate_score = sum(g["value"]/g["threshold"] for g in gates) / len(gates)

for gate in gates:
    status = "✓" if gate["passed"] else "✗"
    print(f"  {status} {gate['name']:20s} {gate['value']:.3f} / {gate['threshold']:.3f}")

print(f"  Aggregate Score: {aggregate_score:.3f}")
print(f"  Result:          {'✓ PASS' if all_gates_passed else '✗ FAIL'}")
print()

# Create Σ-Guard attestation
guard_verdict = "pass" if all_gates_passed else "fail"
guard_attestation = attestation.create_sigma_guard_attestation(
    verdict=guard_verdict,
    candidate_id=candidate_id,
    gates=gates,
    aggregate_score=aggregate_score
)

print("  ✓ Σ-Guard attestation created and signed")
print(f"    Signature: {guard_attestation.signature[:32]}...")
print(f"    Timestamp: {guard_attestation.timestamp}")
print()

# ==============================================================================
# Phase 2: Attestation Chain Construction
# ==============================================================================
print("Phase 2: Attestation Chain Construction")
print("-" * 80)

chain = attestation.AttestationChain(candidate_id=candidate_id)

# Add attestations
chain.add_attestation(sr_attestation)
print("✓ Added SR-Ω∞ attestation to chain")

chain.add_attestation(guard_attestation)
print("✓ Added Σ-Guard attestation to chain")

print()
print("Chain Information:")
print(f"  Candidate ID:  {chain.candidate_id}")
print(f"  Attestations:  {len(chain.attestations)}")
print(f"  Chain Hash:    {chain.chain_hash}")
print(f"  Created:       {chain.created_at}")
print()

# ==============================================================================
# Phase 3: Chain Verification
# ==============================================================================
print("Phase 3: Chain Verification")
print("-" * 80)

# Verify individual attestations
print("3.1 Individual Attestation Verification")
for i, att in enumerate(chain.attestations, 1):
    is_valid = att.verify()
    status = "✓ VALID" if is_valid else "✗ INVALID"
    print(f"  {i}. {att.service_type.value:15s} {status}")

print()

# Verify complete chain
print("3.2 Complete Chain Verification")
is_valid, message = chain.verify_chain()
print(f"  Chain validity:    {'✓ VALID' if is_valid else '✗ INVALID'}")
if not is_valid:
    print(f"  Error message:     {message}")
print()

# Check requirements
print("3.3 Requirement Checks")
has_all_required = chain.has_all_required()
all_passed = chain.all_passed()

print(f"  All required:      {'✓ YES' if has_all_required else '✗ NO'}")
print(f"  All passed:        {'✓ YES' if all_passed else '✗ NO'}")
print()

# ==============================================================================
# Phase 4: Promotion Decision
# ==============================================================================
print("Phase 4: Promotion Decision (ACFA League)")
print("-" * 80)

# Simulate ACFA League decision logic
can_promote = is_valid and has_all_required and all_passed

if can_promote:
    print("✓ ALL CHECKS PASSED - PROMOTING CANDIDATE")
    print()
    print("  Checks:")
    print("    ✓ Attestation chain is cryptographically valid")
    print("    ✓ All required attestations present (SR-Ω∞, Σ-Guard)")
    print("    ✓ All validation services approved (pass verdicts)")
    print("    ✓ Mathematical proof of decision stored")

    chain.final_decision = "promote"

    # Create ACFA attestation for promotion
    acfa_attestation = attestation.create_acfa_attestation(
        verdict="promote",
        candidate_id=candidate_id,
        promotion_decision={
            "decision": "promote",
            "reason": "All attestations valid and passed",
            "sr_score": sr_score,
            "guard_aggregate": aggregate_score,
            "chain_hash": chain.chain_hash
        }
    )

    print()
    print("  ✓ ACFA League attestation created")
    print(f"    Verdict:   {acfa_attestation.verdict}")
    print(f"    Signature: {acfa_attestation.signature[:32]}...")

else:
    print("✗ CHECKS FAILED - PROMOTION DENIED")
    print()
    print("  Failed checks:")
    if not is_valid:
        print(f"    ✗ Chain validation failed: {message}")
    if not has_all_required:
        print("    ✗ Missing required attestations")
    if not all_passed:
        print("    ✗ Some validations did not pass")

    chain.final_decision = "reject"

print()

# ==============================================================================
# Phase 5: WORM Ledger Storage
# ==============================================================================
print("Phase 5: WORM Ledger Storage")
print("-" * 80)

# Serialize attestation chain for storage
chain_data = chain.to_dict()

# Simulate WORM ledger record
ledger_record = {
    "run_id": f"run_{int(time.time())}",
    "timestamp": time.time(),
    "candidate_id": candidate_id,
    "decision": {
        "verdict": chain.final_decision,
        "reason": "Cryptographic attestation chain validated",
        "confidence": 1.0 if can_promote else 0.0,
        "delta_linf": 0.03,
        "delta_score": 0.02,
        "beta_min_met": True,
        "attestation_chain": chain_data  # Complete cryptographic proof
    },
    "metrics": {
        "sr_score": sr_score,
        "guard_aggregate": aggregate_score
    }
}

print("✓ Ledger record prepared")
print(f"  Record size:       {len(json.dumps(ledger_record))} bytes")
print(f"  Attestations:      {len(chain_data['attestations'])}")
print(f"  Chain hash:        {chain_data['chain_hash'][:32]}...")
print()

# Save to file for demonstration
output_dir = Path("examples/output")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / f"attestation_chain_{candidate_id}.json"
with open(output_file, 'w') as f:
    json.dump(ledger_record, f, indent=2)

print(f"✓ Saved to: {output_file}")
print()

# ==============================================================================
# Phase 6: Independent Verification
# ==============================================================================
print("Phase 6: Independent Verification (Audit)")
print("-" * 80)

# Load from file (simulating external auditor)
print("Simulating external auditor loading attestation chain...")
with open(output_file) as f:
    loaded_record = json.load(f)

# Reconstruct chain
loaded_chain = attestation.AttestationChain.from_dict(
    loaded_record['decision']['attestation_chain']
)

# Verify
print()
print("Auditor verification:")
is_valid, message = loaded_chain.verify_chain()
print(f"  Chain validity:    {'✓ VALID' if is_valid else '✗ INVALID'}")
print(f"  Attestations:      {len(loaded_chain.attestations)}")
print(f"  Decision:          {loaded_chain.final_decision.upper()}")
print()

# Verify each attestation
print("  Individual attestations:")
for att in loaded_chain.attestations:
    is_valid = att.verify()
    status = "✓" if is_valid else "✗"
    print(f"    {status} {att.service_type.value:15s} {att.verdict:8s} @ {att.timestamp}")

print()

# ==============================================================================
# Summary
# ==============================================================================
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("This example demonstrated:")
print()
print("1. ✓ Model evaluation by SR-Ω∞ service with cryptographic attestation")
print("2. ✓ Gate validation by Σ-Guard service with cryptographic attestation")
print("3. ✓ Attestation chain construction and verification")
print("4. ✓ Promotion decision based on verified attestation chain")
print("5. ✓ Storage of complete cryptographic proof in WORM ledger")
print("6. ✓ Independent verification by external auditor")
print()
print("Key Properties:")
print()
print("  • Non-repudiation:  Services cannot deny their verdicts")
print("  • Tamper-evident:   Any modification breaks signatures")
print("  • Mathematically verifiable: Ed25519 public-key cryptography")
print("  • Audit trail:      Complete proof stored in WORM ledger")
print("  • Independent:      Can be verified without system access")
print()
print("=" * 80)
print("INTEGRATION COMPLETE ✓")
print("=" * 80)
