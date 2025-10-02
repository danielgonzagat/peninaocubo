#!/usr/bin/env python3
"""
Example: PENIN-Ω Persistence System
====================================

Demonstrates the state serialization and persistence features.
"""

import tempfile
from pathlib import Path

from penin.core import NumericVectorArtifact, OmegaMetaOrchestrator


def example_basic_persistence():
    """Basic persistence example."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Persistence")
    print("=" * 60 + "\n")

    # Create temporary file for state
    state_file = Path(tempfile.gettempdir()) / "penin_example_state.json"

    print("📝 Creating orchestrator and adding data...")
    orchestrator = OmegaMetaOrchestrator()

    # Add some knowledge
    orchestrator.add_knowledge(
        "user_profile_1",
        NumericVectorArtifact(
            vector=[0.8, 0.6, 0.9],
            metadata={"user_id": "user123", "type": "profile_embedding"}
        )
    )

    orchestrator.add_knowledge(
        "document_1",
        NumericVectorArtifact(
            vector=[0.3, 0.7, 0.5],
            metadata={"doc_id": "doc456", "type": "document_embedding"}
        )
    )

    # Add task history
    orchestrator.add_task({
        "task_id": 1,
        "type": "embedding_generation",
        "status": "completed",
        "duration_ms": 150
    })

    orchestrator.add_task({
        "task_id": 2,
        "type": "similarity_search",
        "status": "completed",
        "duration_ms": 80
    })

    # Add performance scores
    orchestrator.add_score(0.85)
    orchestrator.add_score(0.90)
    orchestrator.add_score(0.88)

    print("\n📊 Current state:")
    stats = orchestrator.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Save state
    print(f"\n💾 Saving state to {state_file}...")
    orchestrator.save_state(str(state_file))
    print("✅ State saved successfully!")

    # Create new orchestrator and load state
    print("\n🔄 Creating new orchestrator and loading state...")
    new_orchestrator = OmegaMetaOrchestrator()
    loaded = new_orchestrator.load_state(str(state_file))

    if loaded:
        print("✅ State loaded successfully!")
        print("\n📊 Loaded state:")
        stats = new_orchestrator.get_statistics()
        for key, value in stats.items():
            print(f"   {key}: {value}")

        # Verify knowledge base
        print("\n🧠 Knowledge base contents:")
        for key, artifact in new_orchestrator.knowledge_base.items():
            print(f"   {key}: vector={artifact.vector}, metadata={artifact.metadata}")

    # Cleanup
    state_file.unlink()
    print("\n🧹 Cleaned up temporary files")


def example_history_maxlen():
    """Example showing history maxlen behavior."""
    print("\n" + "=" * 60)
    print("Example 2: History MaxLen")
    print("=" * 60 + "\n")

    print("📝 Creating orchestrator with maxlen=5...")
    orchestrator = OmegaMetaOrchestrator(history_maxlen=5)

    # Add more items than maxlen
    print("   Adding 10 tasks and scores...")
    for i in range(10):
        orchestrator.add_task({"task_id": i})
        orchestrator.add_score(float(i) / 10)

    print("\n📊 History sizes:")
    print(f"   Task history: {len(orchestrator.task_history)} (maxlen: 5)")
    print(f"   Score history: {len(orchestrator.score_history)} (maxlen: 5)")

    print("\n📜 Retained tasks (last 5):")
    for task in orchestrator.task_history:
        print(f"   - Task ID: {task['task_id']}")

    print("\n📈 Retained scores (last 5):")
    for score in orchestrator.score_history:
        print(f"   - Score: {score:.2f}")


def example_persistence_cycle():
    """Example showing multiple persistence cycles."""
    print("\n" + "=" * 60)
    print("Example 3: Multiple Persistence Cycles")
    print("=" * 60 + "\n")

    state_file = Path(tempfile.gettempdir()) / "penin_cycle_state.json"

    # Cycle 1: Initialize
    print("🔄 Cycle 1: Initialize")
    orch1 = OmegaMetaOrchestrator()
    orch1.add_knowledge("k1", NumericVectorArtifact(vector=[0.1]))
    orch1.add_score(0.5)
    orch1.save_state(str(state_file))
    print(f"   Knowledge: {len(orch1.knowledge_base)}, Scores: {len(orch1.score_history)}")

    # Cycle 2: Load and extend
    print("\n🔄 Cycle 2: Load and extend")
    orch2 = OmegaMetaOrchestrator()
    orch2.load_state(str(state_file))
    orch2.add_knowledge("k2", NumericVectorArtifact(vector=[0.2]))
    orch2.add_score(0.6)
    orch2.save_state(str(state_file))
    print(f"   Knowledge: {len(orch2.knowledge_base)}, Scores: {len(orch2.score_history)}")

    # Cycle 3: Load and extend again
    print("\n🔄 Cycle 3: Load and extend again")
    orch3 = OmegaMetaOrchestrator()
    orch3.load_state(str(state_file))
    orch3.add_knowledge("k3", NumericVectorArtifact(vector=[0.3]))
    orch3.add_score(0.7)
    orch3.save_state(str(state_file))
    print(f"   Knowledge: {len(orch3.knowledge_base)}, Scores: {len(orch3.score_history)}")

    # Final verification
    print("\n🔍 Final verification:")
    orch_final = OmegaMetaOrchestrator()
    orch_final.load_state(str(state_file))
    stats = orch_final.get_statistics()
    print(f"   Total knowledge: {stats['knowledge_base_size']}")
    print(f"   Total scores: {stats['score_history_size']}")
    print(f"   Average score: {stats['avg_score']:.2f}")

    # Cleanup
    state_file.unlink()
    print("\n🧹 Cleaned up temporary files")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PENIN-Ω Persistence System Examples")
    print("=" * 60)

    example_basic_persistence()
    example_history_maxlen()
    example_persistence_cycle()

    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
