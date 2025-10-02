"""
PENIN-Ω Main Entry Point
=========================

Application entry point with state persistence lifecycle management.
"""

from __future__ import annotations

import signal
import sys

from penin.core import NumericVectorArtifact, OmegaMetaOrchestrator

# Default state file path
STATE_FILE_PATH = ".penin_omega/state.json"

# Global orchestrator instance
orchestrator: OmegaMetaOrchestrator | None = None


def signal_handler(signum: int, frame) -> None:
    """
    Handle graceful shutdown on SIGINT/SIGTERM.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    print(f"\n🛑 Received signal {signum}, saving state...")

    if orchestrator:
        try:
            orchestrator.save_state(STATE_FILE_PATH)
            print(f"✅ State saved to {STATE_FILE_PATH}")
        except Exception as e:
            print(f"❌ Failed to save state: {e}", file=sys.stderr)

    sys.exit(0)


def main() -> int:
    """
    Main application entry point.

    Returns:
        Exit code (0 for success)
    """
    global orchestrator

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🚀 Starting PENIN-Ω Orchestrator...")

    # Create orchestrator
    orchestrator = OmegaMetaOrchestrator()

    # Load state if exists
    try:
        if orchestrator.load_state(STATE_FILE_PATH):
            print(f"✅ State loaded from {STATE_FILE_PATH}")
            stats = orchestrator.get_statistics()
            print(f"   Knowledge base: {stats['knowledge_base_size']} items")
            print(f"   Task history: {stats['task_history_size']} entries")
            print(f"   Score history: {stats['score_history_size']} entries")
        else:
            print("ℹ️  No previous state found (first run)")
    except Exception as e:
        print(f"⚠️  Failed to load state: {e}", file=sys.stderr)
        print("   Starting with fresh state...")

    # Simulate some work
    try:
        # Add some knowledge
        orchestrator.add_knowledge(
            "embedding_1", NumericVectorArtifact(vector=[0.1, 0.2, 0.3])
        )
        orchestrator.add_knowledge(
            "embedding_2", NumericVectorArtifact(vector=[0.4, 0.5, 0.6])
        )

        # Add some tasks
        orchestrator.add_task(
            {"task_id": 1, "type": "evolution", "status": "completed"}
        )
        orchestrator.add_task(
            {"task_id": 2, "type": "evaluation", "status": "completed"}
        )

        # Add some scores
        orchestrator.add_score(0.85)
        orchestrator.add_score(0.87)
        orchestrator.add_score(0.90)

        print("\n📊 Current statistics:")
        stats = orchestrator.get_statistics()
        for key, value in stats.items():
            print(f"   {key}: {value}")

        # Save state
        orchestrator.save_state(STATE_FILE_PATH)
        print(f"\n💾 State saved to {STATE_FILE_PATH}")

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
