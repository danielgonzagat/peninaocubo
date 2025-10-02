#!/usr/bin/env python3
"""
Simple CLI demonstration for SR-Omega status queries

This demonstrates the CLI interface without the full framework dependencies.
"""

import json
import sys

from penin.omega.sr import SROmegaService


def format_mental_state(mental_state: dict) -> str:
    """Format mental state for text display"""
    output = []
    output.append("📊 Mental State Report")
    output.append("")

    # Pending recommendations
    pending = mental_state.get("pending_recommendations", [])
    output.append(f"📝 Pending Recommendations: {len(pending)}")
    if pending:
        for rec in pending[:5]:  # Show first 5
            age = rec.get("age_seconds", 0)
            output.append(f"   • ID: {rec.get('id', 'N/A')}")
            output.append(f"     Task: {rec.get('task', 'N/A')}")
            output.append(f"     Expected SR: {rec.get('expected_sr', 0):.2f}")
            output.append(f"     Age: {age:.1f}s")
            if rec.get("metadata"):
                output.append(f"     Metadata: {rec.get('metadata')}")
            output.append("")
        if len(pending) > 5:
            output.append(f"   ... and {len(pending) - 5} more")
            output.append("")

    # Recent outcomes
    outcomes = mental_state.get("recent_outcomes", [])
    output.append(f"✅ Recent Outcomes: {len(outcomes)}")
    if outcomes:
        success_count = sum(1 for o in outcomes if o.get("success"))
        output.append(f"   Success Rate: {success_count}/{len(outcomes)} ({success_count*100/len(outcomes):.1f}%)")
        output.append("")
        for outcome in outcomes[-3:]:  # Show last 3
            status = "✅" if outcome.get("success") else "❌"
            output.append(f"   {status} ID: {outcome.get('id', 'N/A')}")
            if outcome.get("actual_sr") is not None:
                output.append(f"     SR: {outcome.get('actual_sr'):.2f}")
            if outcome.get("message"):
                output.append(f"     Message: {outcome.get('message')}")
            output.append("")

    # Current concerns
    concerns = mental_state.get("current_concerns", [])
    output.append(f"⚠️  Current Concerns: {len(concerns)}")
    if concerns:
        for concern in concerns:
            severity = concern.get("severity", "medium")
            icon = "🔴" if severity == "high" else "🟡"
            output.append(f"   {icon} Task: {concern.get('task', 'N/A')}")
            output.append(f"     Success Rate: {concern.get('success_rate', 0)*100:.1f}%")
            output.append(f"     Total Attempts: {concern.get('total_attempts', 0)}")
            output.append("")

    # SR Statistics
    sr_stats = mental_state.get("sr_statistics", {})
    if sr_stats:
        output.append("📈 SR Statistics:")
        output.append(f"   Count: {sr_stats.get('count', 0)}")
        output.append(f"   Average SR: {sr_stats.get('avg_sr', 0):.3f}")
        if sr_stats.get("latest_sr") is not None:
            output.append(f"   Latest SR: {sr_stats.get('latest_sr', 0):.3f}")
        output.append(f"   Stability: {sr_stats.get('stability', 'unknown')}")

    return "\n".join(output)


def query_peer_status(peer_id: str, format_type: str = "text", timeout: float = 5.0) -> int:
    """Query peer status and display result"""
    print(f"🔍 Querying mental state of peer: {peer_id}")
    print("=" * 50)
    print()

    try:
        # Create a simulated peer node with some data for demonstration
        peer_service = SROmegaService()

        # Add some simulated data
        peer_service.add_recommendation("rec-001", "optimize_latency", expected_sr=0.85, metadata={"priority": "high"})
        peer_service.add_recommendation("rec-002", "reduce_cost", expected_sr=0.75, metadata={"priority": "medium"})

        # Simulate some outcomes
        peer_service.report_outcome("rec-003", success=True, actual_sr=0.88, message="Optimization successful")
        peer_service.report_outcome("rec-004", success=False, actual_sr=0.45, message="Cost reduction failed")
        peer_service.report_outcome("rec-005", success=True, actual_sr=0.92, message="Latency improved")

        # Create a task with concerns
        for i in range(5):
            peer_service.add_recommendation(f"rec-concern-{i}", "risky_task", 0.85)
            success = i == 0  # Only first one succeeds
            peer_service.report_outcome(f"rec-concern-{i}", success=success, actual_sr=0.8 if success else 0.3)

        # Get mental state
        mental_state = peer_service.get_mental_state()

        # Format output
        if format_type == "json":
            print(json.dumps(mental_state, indent=2))
        else:
            print(format_mental_state(mental_state))

        return 0

    except Exception as e:
        print(f"❌ Error querying peer status: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python demo_cli_query.py <peer_id> [--format json|text]")
        return 1

    peer_id = sys.argv[1]
    format_type = "text"

    # Parse format option
    if len(sys.argv) > 2 and sys.argv[2] == "--format":
        if len(sys.argv) > 3:
            format_type = sys.argv[3]

    print()
    print("🧠 PENIN-Ω SR-Omega Status Query")
    print()

    return query_peer_status(peer_id, format_type)


if __name__ == "__main__":
    sys.exit(main())
