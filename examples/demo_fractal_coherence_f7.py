#!/usr/bin/env python3
"""
Example demonstration of F7 Fractal Coherence feature in PENIN-Ω

This script demonstrates:
1. Building a fractal decision tree
2. Computing fractal coherence locally
3. Using the SR-Ω∞ Service endpoint
4. Monitoring via Prometheus metrics
"""

from fastapi.testclient import TestClient

from penin.omega.fractal import build_fractal, fractal_coherence, propagate_update
from penin.sr.sr_service import app


def demo_local_computation():
    """Demonstrate local fractal coherence computation"""
    print("=" * 60)
    print("F7 FRACTAL COHERENCE - LOCAL COMPUTATION")
    print("=" * 60)

    # Create a decision tree with perfect coherence
    print("\n1. Creating decision tree with perfect coherence...")
    root_config = {"alpha": 0.001, "beta": 0.9, "kappa": 25, "threshold": 0.85}
    tree = build_fractal(root_config, depth=3, branching=2)
    coherence = fractal_coherence(tree)
    print(f"   Root config: {root_config}")
    print(f"   Tree depth: 3, branching: 2")
    print(f"   Fractal coherence: {coherence:.4f} (perfect)")

    # Introduce divergence
    print("\n2. Introducing divergence in one branch...")
    if tree.children:
        tree.children[0].config["alpha"] = 0.002  # Change first child
    coherence_diverged = fractal_coherence(tree)
    print(f"   Modified first child's alpha to 0.002")
    print(f"   Fractal coherence: {coherence_diverged:.4f} (diverged)")

    # Restore coherence via propagation
    print("\n3. Restoring coherence via propagate_update...")
    propagate_update(tree, {"alpha": 0.0015})
    coherence_restored = fractal_coherence(tree)
    print(f"   Propagated alpha=0.0015 to all nodes")
    print(f"   Fractal coherence: {coherence_restored:.4f} (restored)")

    # Interpretation
    print("\n4. Interpreting results:")
    for fc_value, interpretation in [
        (1.0, "Excellent - Perfect coherence"),
        (0.95, "Excellent - Very high coherence"),
        (0.87, "Good - Adequate coherence"),
        (0.75, "Acceptable - Monitor for drift"),
        (0.65, "Critical - Significant divergence"),
    ]:
        print(f"   FC = {fc_value:.2f}: {interpretation}")


def demo_service_endpoint():
    """Demonstrate SR-Ω∞ Service endpoint usage"""
    print("\n" + "=" * 60)
    print("F7 FRACTAL COHERENCE - SERVICE ENDPOINT")
    print("=" * 60)

    client = TestClient(app)

    # Test 1: Simple request
    print("\n1. Simple fractal coherence request...")
    response = client.post(
        "/sr/fractal_coherence",
        json={"root_config": {"alpha": 0.001, "beta": 0.9}, "depth": 2, "branching": 2},
    )
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Fractal Coherence: {data['fractal_coherence']}")
    print(f"   Tree nodes: {data['total_nodes']}")
    print(f"   Metric name: {data['metric_name']}")

    # Test 2: Complex tree
    print("\n2. Complex tree with multiple levels...")
    response = client.post(
        "/sr/fractal_coherence",
        json={"root_config": {"param_a": 1.0, "param_b": 2.0, "param_c": 3.0}, "depth": 4, "branching": 3},
    )
    data = response.json()
    print(f"   Depth: {data['tree_depth']}, Branching: {data['branching_factor']}")
    print(f"   Total nodes: {data['total_nodes']}")
    print(f"   Fractal Coherence: {data['fractal_coherence']}")

    # Test 3: Check Prometheus metrics
    print("\n3. Checking Prometheus metrics...")
    response = client.get("/metrics")
    lines = [line for line in response.text.split("\n") if "penin_fractal_coherence" in line]
    print("   Prometheus metrics:")
    for line in lines:
        if not line.startswith("#"):
            print(f"     {line}")


def demo_use_cases():
    """Demonstrate practical use cases"""
    print("\n" + "=" * 60)
    print("F7 FRACTAL COHERENCE - USE CASES FOR IA³")
    print("=" * 60)

    print("\n1. Champion-Challenger Gate:")
    print("   - Measure FC before promotion")
    print("   - Require FC ≥ 0.85 to promote challenger")
    print("   - Reject if configuration drift detected")

    print("\n2. Distributed Coherence (Phase 2 - Federation):")
    print("   - Compare FC across multiple instances")
    print("   - Detect policy drift in swarm")
    print("   - Trigger synchronization when needed")

    print("\n3. Auto-Architecture (Phase 3):")
    print("   - Validate architectural changes via FC")
    print("   - Ensure new microservices maintain coherence")
    print("   - Auto-rollback if FC drops below threshold")

    print("\n4. Auditability:")
    print("   - Log FC scores in WORM ledger")
    print("   - Track coherence trends over time")
    print("   - Generate PCAg with FC attestations")

    print("\n5. Meta-Learning:")
    print("   - Analyze FC patterns for successful mutations")
    print("   - Optimize CAOS+ strategy based on FC history")
    print("   - Predict stability from FC trajectories")


if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  PENIN-Ω: F7 FRACTAL COHERENCE DEMONSTRATION".center(58) + "█")
    print("█" + "  Feature: Implementar a base da Coerência Fractal".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60 + "\n")

    demo_local_computation()
    demo_service_endpoint()
    demo_use_cases()

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("✓ Fractal coherence measures consistency across decision scales")
    print("✓ Implemented in penin/omega/fractal.py and penin/sr/sr_service.py")
    print("✓ Exposed as Prometheus metric: penin_fractal_coherence")
    print("✓ Available via REST API: POST /sr/fractal_coherence")
    print("✓ Documented in docs/architecture.md")
    print("✓ Tested in tests/test_fractal_coherence_f7.py")
    print("\nNext Steps:")
    print("- Integrate FC into Σ-Guard gates")
    print("- Add FC to Champion-Challenger promotion logic")
    print("- Create Grafana dashboard for FC monitoring")
    print("- Implement automatic coherence restoration")
    print()
