#!/usr/bin/env python3
"""
Demo script for SR-Omega Mental State Querying

This script demonstrates the complete functionality of the mental state querying system.
"""

import json
import sys


def demo_sr_omega_service():
    """Demonstrate SROmegaService functionality"""
    from penin.omega.sr import SROmegaService

    print("=" * 60)
    print("Demo 1: SROmegaService Mental State Tracking")
    print("=" * 60)
    print()

    # Create service
    service = SROmegaService()
    print("✓ Created SROmegaService")
    print()

    # Add recommendations
    print("Adding recommendations...")
    service.add_recommendation("rec-001", "optimize_latency", 0.85, {"priority": "high", "target_ms": 100})
    service.add_recommendation("rec-002", "reduce_cost", 0.75, {"priority": "medium", "target_pct": 10})
    service.add_recommendation("rec-003", "improve_accuracy", 0.90, {"priority": "high", "target_acc": 0.95})
    print("✓ Added 3 recommendations")
    print()

    # Report some outcomes
    print("Reporting outcomes...")
    service.report_outcome("rec-004", success=True, actual_sr=0.88, message="Latency optimization successful")
    service.report_outcome("rec-005", success=False, actual_sr=0.45, message="Cost reduction failed")
    service.report_outcome("rec-006", success=True, actual_sr=0.92, message="Accuracy improved")
    print("✓ Reported 3 outcomes")
    print()

    # Get mental state
    print("Getting mental state...")
    state = service.get_mental_state()
    print()
    print("Mental State:")
    print(json.dumps(state, indent=2, default=str))
    print()


def demo_p2p_status_query():
    """Demonstrate P2P status query"""
    import asyncio

    from penin.omega.sr import SROmegaService
    from penin.p2p.node import PeninNode

    print("=" * 60)
    print("Demo 2: P2P Status Query")
    print("=" * 60)
    print()

    async def run_demo():
        # Create two nodes
        print("Creating nodes...")
        service1 = SROmegaService()
        service1.add_recommendation("rec-001", "task-1", 0.85, {"priority": "high"})
        service1.report_outcome("rec-002", success=True, actual_sr=0.92, message="Success")

        node1 = PeninNode("node-001", service1)
        node2 = PeninNode("node-002", SROmegaService())
        print("✓ Created node-001 and node-002")
        print()

        # Node 2 queries Node 1
        print("Node-002 querying node-001...")
        query = node2.protocol.create_status_query("node-001")
        print("✓ Created status query message")
        print()

        # Simulate message passing
        print("Sending query and receiving response...")
        response = await node1.handle_message(query)
        await node2.handle_message(response)
        print("✓ Query handled and response received")
        print()

        # Display response
        mental_state = node2.status_responses["node-001"]["mental_state"]
        print("Received Mental State:")
        print(json.dumps(mental_state, indent=2, default=str))
        print()

    asyncio.run(run_demo())


def demo_concerns_detection():
    """Demonstrate concern detection"""
    from penin.omega.sr import SROmegaService

    print("=" * 60)
    print("Demo 3: Concerns Detection")
    print("=" * 60)
    print()

    service = SROmegaService()

    print("Creating a problematic task with low success rate...")
    task_name = "high_risk_optimization"
    for i in range(10):
        service.add_recommendation(f"rec-{i}", task_name, 0.85)
        # Only 20% success rate
        success = i % 5 == 0
        service.report_outcome(f"rec-{i}", success=success, actual_sr=0.8 if success else 0.3)

    print(f"✓ Simulated 10 attempts at '{task_name}' with 20% success rate")
    print()

    state = service.get_mental_state()
    concerns = state["current_concerns"]

    if concerns:
        print("⚠️  Concerns Detected:")
        for concern in concerns:
            print(f"   Task: {concern['task']}")
            print(f"   Success Rate: {concern['success_rate']*100:.1f}%")
            print(f"   Attempts: {concern['total_attempts']}")
            print(f"   Severity: {concern['severity']}")
            print()
    else:
        print("No concerns detected")


def main():
    """Run all demos"""
    print()
    print("🧠 SR-Omega Mental State Querying Demo")
    print()

    try:
        demo_sr_omega_service()
        print()
        demo_p2p_status_query()
        print()
        demo_concerns_detection()
        print()
        print("=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
