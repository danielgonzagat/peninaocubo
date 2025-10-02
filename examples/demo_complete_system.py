"""
PENIN-Ω Complete System Demo

Demonstrates full end-to-end workflow:
1. Multi-LLM Router with budget tracking
2. WORM Ledger for audit trail
3. Self-RAG for retrieval
4. Ω-META for auto-evolution
5. Σ-Guard for ethical gates
6. Complete champion-challenger cycle

Run with:
    python examples/demo_complete_system.py
"""

import asyncio
import sys
from pathlib import Path

# Add penin to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from penin.core.caos import CAOSComponents, compute_caos_plus
from penin.guard.sigma_guard_complete import GateMetrics, SigmaGuard
from penin.ledger.worm_ledger_complete import create_pcag, create_worm_ledger
from penin.math.linf_complete import compute_linf
from penin.math.sr_omega_infinity import SRComponents, compute_sr_score
from penin.meta.omega_meta_complete import MutationType, create_omega_meta
from penin.providers.base import BaseProvider, LLMResponse
from penin.rag.self_rag_complete import Document, create_self_rag
from penin.router import MultiLLMRouterComplete, RouterMode

# ============================================================================
# Mock Provider for Demo
# ============================================================================


class MockProvider(BaseProvider):
    """Mock LLM provider for demo."""

    def __init__(self, name: str, cost_per_token: float = 0.00001):
        self.name = name
        self.cost_per_token = cost_per_token
        self.provider_id = name

    async def chat(
        self,
        messages: list,
        tools: list | None = None,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Mock chat completion."""
        await asyncio.sleep(0.05)  # Simulate latency

        content = f"[Mock response from {self.name}]"
        tokens_in = 100
        tokens_out = 50
        cost = (tokens_in + tokens_out) * self.cost_per_token

        return LLMResponse(
            content=content,
            provider=self.name,
            cost_usd=cost,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_s=0.05,
        )


# ============================================================================
# Demo Functions
# ============================================================================


async def demo_router():
    """Demonstrate Multi-LLM Router."""
    print("\n" + "=" * 60)
    print("1. MULTI-LLM ROUTER DEMO")
    print("=" * 60)

    # Create mock providers
    providers = [
        MockProvider("openai", cost_per_token=0.00002),
        MockProvider("anthropic", cost_per_token=0.00003),
        MockProvider("gemini", cost_per_token=0.00001),
    ]

    # Create router
    router = MultiLLMRouterComplete(
        providers=providers,
        daily_budget_usd=10.0,
        enable_circuit_breaker=True,
        enable_cache=True,
        mode=RouterMode.PRODUCTION,
    )

    # Make requests
    print("\n📡 Making 5 LLM requests...")
    for i in range(5):
        messages = [{"role": "user", "content": f"Test query {i+1}"}]
        response = await router.ask(messages)
        print(f"  Request {i+1}: {response.provider} (${response.cost_usd:.6f})")

    # Show statistics
    stats = router.get_analytics()
    print("\n💰 Budget Status:")
    print(f"  Daily Budget: ${stats['budget']['daily_budget_usd']:.2f}")
    print(f"  Spent: ${stats['budget']['daily_spend_usd']:.6f}")
    print(f"  Remaining: ${stats['budget']['budget_remaining_usd']:.6f}")
    print(f"  Usage: {stats['budget']['budget_used_pct']:.2f}%")

    print("\n📊 Provider Statistics:")
    for provider_id, provider_stats in stats["providers"].items():
        print(f"  {provider_id}:")
        print(f"    Requests: {provider_stats['total_requests']}")
        print(f"    Success Rate: {provider_stats['success_rate']*100:.1f}%")
        print(f"    Avg Latency: {provider_stats['avg_latency_s']:.3f}s")
        print(f"    Total Cost: ${provider_stats['total_cost_usd']:.6f}")

    if stats.get("cache"):
        print("\n🗂️  Cache Statistics:")
        print(f"  Hit Rate: {stats['cache']['hit_rate']*100:.1f}%")
        print(f"  L1 Size: {stats['cache']['l1_size']}")
        print(f"  L2 Size: {stats['cache']['l2_size']}")

    return router


def demo_worm_ledger():
    """Demonstrate WORM Ledger."""
    print("\n" + "=" * 60)
    print("2. WORM LEDGER DEMO")
    print("=" * 60)

    # Create ledger
    ledger = create_worm_ledger("/tmp/penin_demo_ledger.jsonl")

    print("\n📝 Appending events to ledger...")

    # Append some events
    events = [
        ("system_init", "demo_session", {"version": "1.0.0"}),
        ("mutation_proposed", "mut_001", {"type": "parameter_tuning"}),
        ("shadow_evaluation", "mut_001", {"delta_linf": 0.025}),
        ("canary_evaluation", "mut_001", {"traffic_pct": 5.0}),
    ]

    for event_type, event_id, payload in events:
        event = ledger.append(event_type, event_id, payload)
        print(f"  ✓ {event_type}:{event_id} → {event.event_hash[:8]}...")

    # Create and append PCAg
    print("\n🔐 Creating Proof-Carrying Artifact...")
    pcag = create_pcag(
        decision_id="mut_001",
        decision_type="promote",
        metrics={"delta_linf": 0.025, "caos_plus": 22.0, "sr_score": 0.87},
        gates={"sigma_guard": True, "ir_ic": True},
        reason="All gates passed, promoting to champion",
    )
    ledger.append_pcag(pcag)
    print(f"  ✓ PCAg created: {pcag.artifact_hash[:8]}...")

    # Verify chain
    print("\n🔍 Verifying ledger integrity...")
    is_valid, error = ledger.verify_chain()
    if is_valid:
        print("  ✅ Ledger chain is valid!")
    else:
        print(f"  ❌ Chain error: {error}")

    # Show statistics
    stats = ledger.get_statistics()
    print("\n📊 Ledger Statistics:")
    print(f"  Total Events: {stats['total_events']}")
    print(f"  Merkle Root: {stats['merkle_root'][:16]}...")
    print(f"  Ledger Size: {stats['ledger_size_bytes']} bytes")
    print(f"  Event Types: {stats['event_types']}")

    return ledger


def demo_self_rag():
    """Demonstrate Self-RAG."""
    print("\n" + "=" * 60)
    print("3. SELF-RAG DEMO")
    print("=" * 60)

    # Create Self-RAG
    rag = create_self_rag(
        chunk_size=512,
        top_k=5,
        use_embeddings=False,  # Use BM25 only for demo (no deps)
    )

    print("\n📚 Adding documents to corpus...")

    # Add sample documents
    docs = [
        Document(
            doc_id="doc_001",
            content=(
                "PENIN-Ω is a self-evolving AI system implementing the Master Equation "
                "with CAOS+, SR-Ω∞, and L∞ aggregation for ethical, auditable, and "
                "production-ready machine learning operations."
            ),
            source="README.md",
        ),
        Document(
            doc_id="doc_002",
            content=(
                "The Σ-Guard implements fail-closed security gates with non-compensatory "
                "validation. It ensures that no single metric can compensate for failure "
                "in another, using harmonic mean aggregation."
            ),
            source="docs/sigma_guard.md",
        ),
        Document(
            doc_id="doc_003",
            content=(
                "CAOS+ is the core evolution engine that measures Consistency, "
                "Autoevolution, Incognoscível (epistemic uncertainty), and Silêncio "
                "(signal quality). The formula is CAOS+ = (1 + κ·C·A)^(O·S)."
            ),
            source="docs/equations.md",
        ),
    ]

    for doc in docs:
        rag.add_document(doc)
        print(f"  ✓ Added {doc.doc_id} ({len(doc.content)} chars)")

    # Fit RAG
    print("\n🔧 Fitting retrieval system...")
    rag.fit()

    stats = rag.get_statistics()
    print(f"  Documents: {stats['num_documents']}")
    print(f"  Chunks: {stats['num_chunks']}")

    # Search
    print("\n🔍 Searching corpus...")
    queries = [
        "What is CAOS+?",
        "How does Sigma-Guard work?",
        "What is PENIN-Ω?",
    ]

    for query in queries:
        results = rag.search(query, top_k=2, method="bm25")
        print(f"\n  Query: '{query}'")
        for i, result in enumerate(results, 1):
            print(f"    {i}. [{result.chunk.doc_id}] Score: {result.score:.4f}")
            print(f"       {result.chunk.content[:100]}...")

    return rag


async def demo_omega_meta():
    """Demonstrate Ω-META."""
    print("\n" + "=" * 60)
    print("4. Ω-META DEMO")
    print("=" * 60)

    # Create Ω-META
    meta = create_omega_meta(
        ledger_path="/tmp/penin_demo_omega_ledger.jsonl",
        beta_min=0.01,
        seed=42,
    )

    print("\n🧬 Generating mutation...")

    # Generate mutation
    mutation = meta.generate_mutation(
        MutationType.PARAMETER_TUNING,
        function_name="compute_caos_plus",
        parameters={"kappa": 20.0, "epsilon": 1e-3},
        perturbation=0.1,
    )

    print(f"  Mutation ID: {mutation.mutation_id}")
    print(f"  Type: {mutation.mutation_type.value}")
    print(f"  Description: {mutation.description}")
    print(f"  Expected Gain: {mutation.expected_gain:.4f}")
    print(f"  Estimated Cost: {mutation.estimated_cost:.2f}")

    # Propose and evaluate
    print("\n🔬 Evaluating challenger...")
    print("  Phase 1: Shadow evaluation (0% traffic)...")
    await asyncio.sleep(0.1)

    evaluation = await meta.propose_and_evaluate(
        mutation,
        shadow_samples=100,
        run_canary=True,
    )

    print(f"\n  Phase 2: Canary evaluation ({evaluation.traffic_percentage*100}% traffic)...")
    await asyncio.sleep(0.1)

    # Show results
    print("\n📊 Evaluation Results:")
    print(f"  ΔL∞: {evaluation.delta_linf:.4f}")
    print(f"  CAOS⁺: {evaluation.caos_plus:.2f}")
    print(f"  SR: {evaluation.sr_score:.2f}")
    print(f"  Latency (avg): {evaluation.latency_avg:.3f}s")
    print(f"  Error Rate: {evaluation.error_rate*100:.2f}%")
    print(f"  Cost Delta: {evaluation.cost_delta*100:.1f}%")
    print(f"  Samples: {evaluation.sample_count}")

    # Decision
    print("\n🎯 Decision:")
    if evaluation.promote:
        print(f"  ✅ PROMOTE: {evaluation.reason}")
    else:
        print(f"  ❌ ROLLBACK: {evaluation.reason}")

    # Promote or rollback
    print("\n⚡ Executing decision...")
    pcag = await meta.promote_or_rollback(evaluation)
    print(f"  PCAg created: {pcag.artifact_hash[:8]}...")
    print(f"  Decision type: {pcag.decision_type}")

    # Show statistics
    stats = meta.get_statistics()
    print("\n📈 Ω-META Statistics:")
    champion = stats["framework"]["champion"]
    if champion:
        print(f"  Champion: {champion['mutation_id']}")
        print(f"  Traffic: {champion['traffic_percentage']*100:.0f}%")
    print(f"  Challengers: {stats['framework']['num_challengers']}")
    print(f"  Evaluations: {stats['framework']['num_evaluations']}")

    return meta


def demo_sigma_guard():
    """Demonstrate Σ-Guard."""
    print("\n" + "=" * 60)
    print("5. Σ-GUARD DEMO")
    print("=" * 60)

    # Create Σ-Guard
    guard = SigmaGuard()

    print("\n🛡️  Testing gate validation...")

    # Test cases
    test_cases = [
        {
            "name": "Perfect metrics (should PASS)",
            "metrics": GateMetrics(
                rho=0.95,
                ece=0.005,
                rho_bias=1.02,
                sr_score=0.90,
                omega_g=0.90,
                delta_linf=0.03,
                caos_plus=25.0,
                cost_increase=0.05,
                kappa=22.0,
                consent=True,
                eco_ok=True,
            ),
        },
        {
            "name": "Bad contratividade (should FAIL)",
            "metrics": GateMetrics(
                rho=1.05,  # > 1.0 (not contractive)
                ece=0.005,
                rho_bias=1.02,
                sr_score=0.90,
                omega_g=0.90,
                delta_linf=0.03,
                caos_plus=25.0,
                cost_increase=0.05,
                kappa=22.0,
                consent=True,
                eco_ok=True,
            ),
        },
        {
            "name": "Low ΔL∞ (should FAIL)",
            "metrics": GateMetrics(
                rho=0.95,
                ece=0.005,
                rho_bias=1.02,
                sr_score=0.90,
                omega_g=0.90,
                delta_linf=0.005,  # < β_min
                caos_plus=25.0,
                cost_increase=0.05,
                kappa=22.0,
                consent=True,
                eco_ok=True,
            ),
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test {i}: {test_case['name']}")
        result = guard.validate(test_case["metrics"])

        if result.allow:
            print("    ✅ PASS")
        else:
            print("    ❌ FAIL")
            print(f"    Failed gates: {', '.join(result.failed_gates)}")
            for reason in result.reasons:
                print(f"      - {reason}")

    return guard


def demo_equations():
    """Demonstrate core equations."""
    print("\n" + "=" * 60)
    print("6. CORE EQUATIONS DEMO")
    print("=" * 60)

    print("\n🧮 Computing core metrics...")

    # L∞
    metrics = [0.85, 0.78, 0.92]
    weights = [0.4, 0.4, 0.2]
    cost_norm = 0.15
    lambda_c = 0.5
    ethical_ok = True

    linf = compute_linf(metrics, weights, cost_norm, lambda_c, ethical_ok)
    print("\n  L∞ (Meta-Function):")
    print(f"    Metrics: {metrics}")
    print(f"    Weights: {weights}")
    print(f"    Cost: {cost_norm}")
    print(f"    Result: {linf:.4f}")

    # CAOS⁺
    components = CAOSComponents(
        consistency=0.88,
        autoevolution=0.40,
        incognoscivel=0.35,
        silencio=0.82,
    )
    kappa = 20.0

    caos_plus = compute_caos_plus(components, kappa)
    print("\n  CAOS⁺ (Evolution Engine):")
    print(f"    C: {components.consistency:.2f}")
    print(f"    A: {components.autoevolution:.2f}")
    print(f"    O: {components.incognoscivel:.2f}")
    print(f"    S: {components.silencio:.2f}")
    print(f"    κ: {kappa}")
    print(f"    Result: {caos_plus:.4f}")

    # SR-Ω∞
    sr_components = SRComponents(
        awareness=0.92,
        ethics_ok=True,
        autocorrection=0.88,
        metacognition=0.67,
    )

    sr_score = compute_sr_score(sr_components)
    print("\n  SR-Ω∞ (Self-Reflection):")
    print(f"    Awareness: {sr_components.awareness:.2f}")
    print(f"    Ethics: {'✓' if sr_components.ethics_ok else '✗'}")
    print(f"    Autocorrection: {sr_components.autocorrection:.2f}")
    print(f"    Metacognition: {sr_components.metacognition:.2f}")
    print(f"    Result: {sr_score:.4f}")


# ============================================================================
# Main Demo
# ============================================================================


async def main():
    """Run complete demo."""
    print("\n" + "=" * 60)
    print("PENIN-Ω COMPLETE SYSTEM DEMONSTRATION")
    print("=" * 60)
    print("\nThis demo showcases:")
    print("  • Multi-LLM Router with budget tracking")
    print("  • WORM Ledger for immutable audit trail")
    print("  • Self-RAG for retrieval augmentation")
    print("  • Ω-META for autonomous evolution")
    print("  • Σ-Guard for ethical gates")
    print("  • Core mathematical equations")

    try:
        # Run demos
        await demo_router()
        demo_worm_ledger()
        demo_self_rag()
        await demo_omega_meta()
        demo_sigma_guard()
        demo_equations()

        # Final summary
        print("\n" + "=" * 60)
        print("DEMO COMPLETE ✅")
        print("=" * 60)
        print("\nAll systems operational:")
        print("  ✓ Multi-LLM Router")
        print("  ✓ WORM Ledger")
        print("  ✓ Self-RAG")
        print("  ✓ Ω-META")
        print("  ✓ Σ-Guard")
        print("  ✓ Core Equations")

        print("\n📁 Artifacts created:")
        print("  • /tmp/penin_demo_ledger.jsonl")
        print("  • /tmp/penin_demo_omega_ledger.jsonl")
        print("  • ~/.penin_router_complete_state.json")

        print("\n🎉 PENIN-Ω is ready for production!")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
