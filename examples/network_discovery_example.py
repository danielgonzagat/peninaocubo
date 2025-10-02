#!/usr/bin/env python3
"""
Example: PENIN Network Discovery
=================================

Demonstrates the peer discovery functionality allowing PENIN nodes
to discover each other on the local network.

This implements Phase 5: The Agora - curing "Social Isolation".
"""

import time
from pathlib import Path

from penin.core.orchestrator import OmegaMetaOrchestrator
from penin.p2p.node import PeninNode


def example_basic_discovery():
    """Basic peer discovery example with two nodes."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Peer Discovery")
    print("=" * 70 + "\n")

    # Create two nodes with discovery enabled
    node1 = PeninNode(node_id="node-alpha", enable_discovery=True)
    node2 = PeninNode(node_id="node-beta", enable_discovery=True)

    print("📡 Starting discovery service on both nodes...")
    node1.start_discovery()
    node2.start_discovery()

    print("⏳ Waiting for peer discovery (5 seconds)...")
    time.sleep(5)

    # Check discovered peers
    print(f"\n✅ Node Alpha discovered peers: {list(node1.peers.keys())}")
    print(f"✅ Node Beta discovered peers: {list(node2.peers.keys())}")

    # Stop services
    node1.stop_discovery()
    node2.stop_discovery()
    print("\n🛑 Discovery services stopped")


def example_discovery_with_orchestrator():
    """Example showing integration with orchestrator."""
    print("\n" + "=" * 70)
    print("Example 2: Discovery with Orchestrator Integration")
    print("=" * 70 + "\n")

    # Create orchestrator
    orchestrator = OmegaMetaOrchestrator()

    # Create nodes with orchestrator
    node1 = PeninNode(
        node_id="node-gamma",
        orchestrator=orchestrator,
        enable_discovery=True,
    )
    node2 = PeninNode(node_id="node-delta", enable_discovery=True)

    print("📡 Starting discovery service...")
    node1.start_discovery()
    node2.start_discovery()

    print("⏳ Waiting for peer discovery (5 seconds)...")
    time.sleep(5)

    # Check orchestrator's known peers
    print(f"\n✅ Orchestrator known peers: {orchestrator.known_peers}")
    print(f"   Total known peers: {len(orchestrator.known_peers)}")

    # Stop services
    node1.stop_discovery()
    node2.stop_discovery()
    print("\n🛑 Discovery services stopped")


def example_state_persistence():
    """Example showing state persistence with known peers."""
    print("\n" + "=" * 70)
    print("Example 3: State Persistence with Known Peers")
    print("=" * 70 + "\n")

    state_file = Path("/tmp/penin_discovery_state.json")

    # Create orchestrator and node
    orchestrator = OmegaMetaOrchestrator()
    node = PeninNode(
        node_id="node-epsilon",
        orchestrator=orchestrator,
        enable_discovery=True,
    )

    # Simulate some discovered peers
    orchestrator.known_peers.add("192.168.1.100:51515")
    orchestrator.known_peers.add("192.168.1.101:51515")

    print("💾 Saving state with known peers...")
    orchestrator.save_state(str(state_file))
    print(f"   Saved {len(orchestrator.known_peers)} known peers")

    # Create new orchestrator and load state
    orchestrator2 = OmegaMetaOrchestrator()
    orchestrator2.load_state(str(state_file))

    print(f"\n📂 Loaded state from file")
    print(f"   Restored known peers: {orchestrator2.known_peers}")
    print(f"   Total: {len(orchestrator2.known_peers)}")

    # Cleanup
    if state_file.exists():
        state_file.unlink()


def example_context_manager():
    """Example using context manager for lifecycle management."""
    print("\n" + "=" * 70)
    print("Example 4: Context Manager Lifecycle")
    print("=" * 70 + "\n")

    node = PeninNode(node_id="node-zeta", enable_discovery=True)

    print("📡 Using context manager for automatic lifecycle...")
    with node:
        print("   ✅ Discovery started automatically")
        print("   ⏳ Waiting 3 seconds...")
        time.sleep(3)
        print("   📊 Node info:", node.get_node_info())

    print("   🛑 Discovery stopped automatically on exit")


def example_multiple_nodes():
    """Example with multiple nodes discovering each other."""
    print("\n" + "=" * 70)
    print("Example 5: Multiple Nodes Discovery")
    print("=" * 70 + "\n")

    # Create multiple nodes
    nodes = [
        PeninNode(node_id=f"node-{i}", enable_discovery=True) for i in range(3)
    ]

    print(f"📡 Starting discovery on {len(nodes)} nodes...")
    for node in nodes:
        node.start_discovery()

    print("⏳ Waiting for peer discovery (5 seconds)...")
    time.sleep(5)

    # Report discovered peers for each node
    for i, node in enumerate(nodes):
        discovered = list(node.peers.keys())
        print(f"   Node-{i} discovered: {discovered} ({len(discovered)} peers)")

    # Stop all services
    for node in nodes:
        node.stop_discovery()

    print("\n🛑 All discovery services stopped")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("PENIN Network Discovery Examples")
    print("Phase 5: The Agora - Curing Social Isolation")
    print("=" * 70)

    try:
        example_basic_discovery()
        example_discovery_with_orchestrator()
        example_state_persistence()
        example_context_manager()
        example_multiple_nodes()

        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
