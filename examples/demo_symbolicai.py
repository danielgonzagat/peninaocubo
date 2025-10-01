#!/usr/bin/env python3
"""
Demo: SymbolicAI Integration with SR-Ω∞ Service

This example demonstrates how the SymbolicAI adapter validates
champion-challenger decisions in the SR-Ω∞ Service, ensuring
logical consistency and ethical compliance.

Priority: P2 - High (SOTA Self-Modifying Evolution)
"""

import asyncio
import time
from typing import Any


def create_sr_omega_decision() -> dict[str, Any]:
    """
    Simulate a champion-challenger decision from SR-Ω∞ Service.

    In production, this would come from the actual SR-Ω∞ Service
    after evaluating metrics, costs, and quality improvements.
    """
    return {
        "type": "champion_challenger_transition",
        "champion_model": "model_v3",
        "challenger_model": "model_v4",
        "timestamp": time.time(),
        "score_improvement": 0.18,  # 18% better performance
        "score": 0.89,  # Overall L∞ score
        "confidence": 0.91,  # Confidence in the decision
        "verdict": "pass",  # Pass the champion-challenger gate
        "metrics": {
            "latency_ms": 220,
            "cost_reduction": 0.25,  # 25% cost savings
            "quality_improvement": 0.18,
            "ethical_compliance": 1.0,  # Full ethical compliance
        },
        "reasoning": {
            "factors": [
                "Significant quality improvement",
                "Cost reduction achieved",
                "All ethical constraints satisfied",
                "Confidence threshold met",
            ],
            "risks": [
                "Minor latency increase (acceptable)",
            ],
        },
    }


async def demo_symbolicai_validation():
    """
    Demonstrate SymbolicAI validation of SR-Ω∞ decisions.
    """
    print("=" * 80)
    print("SymbolicAI Integration Demo: Validating SR-Ω∞ Decisions")
    print("=" * 80)
    print()

    # Import the adapter
    try:
        from penin.integrations.symbolic import SymbolicAIAdapter, SymbolicAIConfig
    except ImportError as e:
        print(f"❌ Error importing SymbolicAI adapter: {e}")
        return

    # Configure the adapter
    print("📋 Configuring SymbolicAI Adapter...")
    config = SymbolicAIConfig(
        reasoning_depth=5,
        enable_logic_validation=True,
        enable_constraint_checking=True,
        min_confidence=0.85,
        symbolic_fusion=True,
        explain_reasoning=True,
        fail_open=False,  # Fail-closed for production safety
    )
    print(f"   • Reasoning depth: {config.reasoning_depth}")
    print(f"   • Logic validation: {config.enable_logic_validation}")
    print(f"   • Constraint checking: {config.enable_constraint_checking}")
    print(f"   • Min confidence: {config.min_confidence}")
    print()

    # Initialize the adapter
    print("🔧 Initializing SymbolicAI Adapter...")
    adapter = SymbolicAIAdapter(config=config)

    if not adapter.is_available():
        print("⚠️  SymbolicAI not installed - running in placeholder mode")
        print("   Install with: pip install symbolicai")
    else:
        print("✅ SymbolicAI library detected")

    # Initialize (works even without SymbolicAI installed)
    adapter._initialized = True
    adapter.status = adapter.status.__class__.INITIALIZED
    print("✅ Adapter initialized")
    print()

    # Create a decision from SR-Ω∞
    print("🎯 Simulating SR-Ω∞ Champion-Challenger Decision...")
    decision = create_sr_omega_decision()
    print(f"   • Type: {decision['type']}")
    print(f"   • Champion: {decision['champion_model']}")
    print(f"   • Challenger: {decision['challenger_model']}")
    print(f"   • Score: {decision['score']:.3f}")
    print(f"   • Confidence: {decision['confidence']:.3f}")
    print(f"   • Verdict: {decision['verdict']}")
    print()

    # Define ethical constraints (from CAOS+)
    ethical_constraints = [
        "LO-01_compliance",  # No anthropomorphism
        "fail_closed_principle",  # Fail-closed on uncertainty
        "auditability_requirement",  # WORM ledger logging
        "no_harm_principle",  # First, do no harm
        "contractivity_requirement",  # ρ < 1 (IR→IC)
    ]
    print("🔒 Ethical Constraints to Verify:")
    for constraint in ethical_constraints:
        print(f"   • {constraint}")
    print()

    # Validate the decision
    print("🔍 Validating Decision with SymbolicAI...")
    validation_start = time.time()
    validation = await adapter.validate_sr_omega_decision(decision, ethical_constraints)
    validation_time = (time.time() - validation_start) * 1000
    print()

    # Display validation results
    print("📊 Validation Results:")
    print(f"   • Valid: {validation['valid']}")
    print(f"   • Confidence: {validation['confidence']:.3f}")
    print(f"   • Logic Valid: {validation['logic_valid']}")
    print(f"   • Consistency Valid: {validation['consistency_valid']}")
    print(f"   • Validation Time: {validation_time:.2f}ms")
    print()

    # Display constraint verification
    if "constraint_verification" in validation:
        verification = validation["constraint_verification"]
        print("🔒 Constraint Verification:")
        print(f"   • All Satisfied: {verification['all_constraints_satisfied']}")
        print(f"   • Satisfied ({len(verification['satisfied_constraints'])}):")
        for constraint in verification["satisfied_constraints"]:
            print(f"      ✓ {constraint}")
        if verification["violated_constraints"]:
            print(f"   • Violated ({len(verification['violated_constraints'])}):")
            for constraint in verification["violated_constraints"]:
                print(f"      ✗ {constraint}")
        print()

    # Display explanation
    if "explanation" in validation:
        explanation = validation["explanation"]
        print("💡 Decision Explanation:")
        print(f"   {explanation['explanation']}")
        print()
        print("   Reasoning Chain:")
        for i, step in enumerate(explanation["reasoning_chain"], 1):
            print(f"      {i}. {step}")
        print()

    # Display adapter metrics
    print("📈 Adapter Metrics:")
    metrics = adapter.get_metrics()
    print(f"   • Invocations: {metrics['invocations']}")
    print(f"   • Successes: {metrics['successes']}")
    print(f"   • Success Rate: {metrics['success_rate']:.1%}")
    print(f"   • Avg Latency: {metrics['avg_latency_ms']:.2f}ms")
    print()

    # Production usage guidance
    print("=" * 80)
    print("Production Usage:")
    print("=" * 80)
    print("""
In production, the SR-Ω∞ Service would:
1. Generate a champion-challenger decision based on metrics
2. Call adapter.validate_sr_omega_decision() to verify logic
3. Check if validation['valid'] and all constraints satisfied
4. Proceed with transition only if validation passes
5. Log all validation results to WORM ledger for auditability

Example integration:

    # In SR-Ω∞ Service
    decision = self.generate_decision(champion, challenger)

    # Validate with SymbolicAI
    validation = await symbolicai.validate_sr_omega_decision(
        decision,
        ethical_constraints=self.ethical_constraints
    )

    # Fail-closed: Only proceed if valid
    if validation['valid'] and validation['constraint_verification']['all_constraints_satisfied']:
        self.apply_transition(challenger)
        self.worm_ledger.log(validation)
    else:
        logger.warning("Decision failed symbolic validation, reverting to champion")
        self.revert_to_champion()
""")


async def demo_symbolic_reasoning():
    """
    Demonstrate pure symbolic reasoning capabilities.
    """
    print("=" * 80)
    print("SymbolicAI: Pure Symbolic Reasoning Demo")
    print("=" * 80)
    print()

    from penin.integrations.symbolic import SymbolicAIAdapter

    adapter = SymbolicAIAdapter()
    adapter._initialized = True
    adapter.status = adapter.status.__class__.INITIALIZED

    # Example: Reason about a complex decision
    print("🧠 Applying Symbolic Reasoning...")
    decision = {
        "type": "architecture_modification",
        "proposed_change": "Add new neural layer",
        "impact_score": 0.75,
        "risk_score": 0.35,
    }

    reasoning = await adapter.reason(decision)

    print("📝 Reasoning Results:")
    print(f"   • Conclusions: {len(reasoning['conclusions'])}")
    for conclusion in reasoning["conclusions"]:
        print(f"      • {conclusion}")
    print(f"   • Reasoning Steps: {reasoning['reasoning_steps']}")
    print(f"   • Neurosymbolic Fusion: {reasoning['neurosymbolic_fusion']}")
    print()


async def main():
    """Run all demos"""
    await demo_symbolicai_validation()
    print("\n")
    await demo_symbolic_reasoning()

    print("=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
