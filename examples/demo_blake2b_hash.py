#!/usr/bin/env python3
"""
WORM Ledger BLAKE2b Demo

Demonstrates the improved WORM Ledger with BLAKE2b hash algorithm.
Shows performance improvements and new features.
"""

import tempfile
import time
from pathlib import Path

from penin.ledger.hash_utils import (
    HASH_ALGORITHM,
    benchmark_hash_algorithms,
    compute_hash,
    hash_json,
    keyed_hash,
)
from penin.ledger.worm_ledger import (
    LEDGER_VERSION,
    create_pcag,
    create_worm_ledger,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def demo_hash_algorithm():
    """Demonstrate the new hash algorithm."""
    print_section("Hash Algorithm: BLAKE2b-256")

    print("\n📊 Current Configuration:")
    print(f"   Algorithm: {HASH_ALGORITHM}")
    print(f"   Ledger Version: {LEDGER_VERSION}")
    print("   Security Level: 256 bits")

    # Show hash examples
    print("\n🔑 Hash Examples:")
    test_data = b"PENIN-Omega WORM Ledger"

    blake2b_hash = compute_hash(test_data, algorithm="blake2b")
    sha256_hash = compute_hash(test_data, algorithm="sha256")

    print(f"   Data: {test_data.decode()}")
    print(f"   BLAKE2b: {blake2b_hash}")
    print(f"   SHA-256: {sha256_hash}")
    print("   Both:    64 characters (256-bit)")


def demo_performance():
    """Demonstrate performance improvements."""
    print_section("Performance Benchmark")

    # Create realistic test data
    test_data = hash_json({
        "event_type": "evaluate",
        "event_id": "test-event-001",
        "timestamp": "2024-01-15T10:30:00Z",
        "payload": {
            "metrics": {"U": 0.85, "S": 0.90, "C": 0.75, "L": 0.80},
            "gates": {"sigma_guard_ok": True, "ir_ic_ok": True},
            "decision": {"verdict": "promote", "reason": "metrics improved"}
        }
    }).encode()

    print(f"\n⏱️  Benchmarking with {len(test_data)} bytes of data...")
    print("   Running 10,000 iterations for each algorithm...")

    results = benchmark_hash_algorithms(test_data, iterations=10000)

    # Sort by speed
    sorted_results = sorted(results.items(), key=lambda x: x[1])

    print("\n📈 Results:")
    for i, (algo, time_taken) in enumerate(sorted_results, 1):
        speedup = sorted_results[-1][1] / time_taken
        print(f"   {i}. {algo:12s}: {time_taken:.6f}s  ({speedup:.2f}x faster than slowest)")


def demo_worm_ledger():
    """Demonstrate WORM ledger with BLAKE2b."""
    print_section("WORM Ledger Operations")

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "demo_ledger.jsonl"

        print(f"\n📝 Creating ledger at: {ledger_path}")
        ledger = create_worm_ledger(ledger_path)

        # Append events
        print("\n✏️  Appending events...")
        start_time = time.time()

        events = []
        for i in range(10):
            event = ledger.append(
                event_type="demo",
                event_id=f"evt-{i:03d}",
                payload={
                    "cycle": i,
                    "action": "evaluate",
                    "score": 0.8 + i * 0.01,
                    "data": f"Event {i} with BLAKE2b hash"
                }
            )
            events.append(event)

        elapsed = time.time() - start_time
        print(f"   ✓ Appended {len(events)} events in {elapsed:.4f}s")
        print(f"   ✓ Average: {elapsed/len(events):.6f}s per event")

        # Show hash chain
        print("\n🔗 Hash Chain Sample:")
        for i, event in enumerate(events[:3]):
            print(f"   Event {i}: {event.event_hash[:16]}... -> {event.previous_hash[:16] if event.previous_hash else 'genesis'}...")
        print("   ...")

        # Verify chain
        print("\n🔍 Verifying hash chain...")
        is_valid, error = ledger.verify_chain()
        if is_valid:
            print("   ✅ Chain verified successfully!")
        else:
            print(f"   ❌ Chain verification failed: {error}")

        # Compute Merkle root
        print("\n🌳 Computing Merkle root...")
        merkle_root = ledger.compute_merkle_root()
        print(f"   Root: {merkle_root}")

        # Show statistics
        stats = ledger.get_statistics()
        print("\n📊 Ledger Statistics:")
        print(f"   Total events: {stats['total_events']}")
        print(f"   Last sequence: {stats['last_sequence']}")
        print(f"   Last hash: {stats['last_hash'][:16]}...")
        print(f"   Merkle root: {stats['merkle_root'][:16]}...")
        print(f"   Chain valid: {stats['chain_valid']}")
        print(f"   File size: {stats['ledger_size_bytes']} bytes")


def demo_proof_carrying_artifact():
    """Demonstrate Proof-Carrying Artifacts."""
    print_section("Proof-Carrying Artifacts (PCAg)")

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "pcag_ledger.jsonl"
        ledger = create_worm_ledger(ledger_path)

        print("\n🎯 Creating PCAg for decision tracking...")

        # Create PCAg
        pcag = create_pcag(
            decision_id="promote-001",
            decision_type="promote",
            metrics={
                "U": 0.92,  # Utility
                "S": 0.88,  # Stability
                "C": 0.70,  # Cost
                "L": 0.85   # Learning
            },
            gates={
                "sigma_guard_ok": True,
                "ir_ic_ok": True,
                "sr_gate_ok": True,
                "caos_gate_ok": True
            },
            reason="All gates passed, metrics improved significantly",
            metadata={
                "model": "gpt-4",
                "provider": "openai",
                "version": "v1.0"
            }
        )

        print(f"   ✓ PCAg created: {pcag.decision_type}:{pcag.decision_id}")
        print(f"   ✓ Hash: {pcag.artifact_hash[:32]}...")
        print(f"   ✓ Timestamp: {pcag.timestamp}")

        # Verify PCAg
        print("\n🔍 Verifying PCAg hash...")
        is_valid = pcag.verify_hash()
        print(f"   {'✅' if is_valid else '❌'} Hash verification: {'PASSED' if is_valid else 'FAILED'}")

        # Append to ledger
        print("\n📝 Appending PCAg to ledger...")
        event = ledger.append_pcag(pcag)
        print(f"   ✓ Appended as event: {event.event_id}")
        print(f"   ✓ Event hash: {event.event_hash[:32]}...")


def demo_keyed_hashing():
    """Demonstrate keyed hashing for authentication."""
    print_section("Keyed Hashing (Authentication)")

    print("\n🔐 BLAKE2b supports native keyed hashing (like HMAC)...")

    data = b"Sensitive ledger data"
    secret_key = b"my_secret_key_12345"

    # Create authenticated hash
    auth_hash = keyed_hash(data, secret_key, algorithm="blake2b")

    print(f"   Data: {data.decode()}")
    print(f"   Key:  {secret_key.decode()}")
    print(f"   Auth Hash: {auth_hash}")

    # Try different key
    wrong_key = b"wrong_key"
    wrong_hash = keyed_hash(data, wrong_key, algorithm="blake2b")

    print("\n🔑 Testing with different keys:")
    print(f"   Correct key: {auth_hash[:32]}...")
    print(f"   Wrong key:   {wrong_hash[:32]}...")
    print(f"   Match: {'❌ NO' if auth_hash != wrong_hash else '✅ YES'}")


def demo_comparison():
    """Demonstrate comparison with legacy SHA-256."""
    print_section("BLAKE2b vs SHA-256 Comparison")

    print("\n📊 Feature Comparison:")
    print(f"   {'Feature':<25} {'BLAKE2b':<15} {'SHA-256':<15}")
    print(f"   {'-' * 55}")
    print(f"   {'Hash Length':<25} {'64 chars':<15} {'64 chars':<15}")
    print(f"   {'Security Level':<25} {'256 bits':<15} {'256 bits':<15}")
    print(f"   {'Year Released':<25} {'2012':<15} {'2001':<15}")
    print(f"   {'SHA-3 Finalist':<25} {'✅ Yes':<15} {'❌ No':<15}")
    print(f"   {'Keyed Hashing':<25} {'✅ Native':<15} {'⚠️  HMAC':<15}")
    print(f"   {'Hardware Accel':<25} {'✅ Modern':<15} {'✅ Legacy':<15}")
    print(f"   {'Quantum Resistant':<25} {'✅ Better':<15} {'✅ Good':<15}")

    print("\n✅ Why BLAKE2b?")
    print("   • More modern cryptographic design")
    print("   • Better performance in optimized implementations")
    print("   • Native keyed hashing support")
    print("   • Growing adoption in blockchain/distributed systems")
    print("   • Same security level as SHA-256")

    print("\n🔄 Backward Compatibility:")
    print("   • Legacy ledgers continue using SHA-256")
    print("   • New ledgers automatically use BLAKE2b")
    print("   • No breaking changes to API")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  PENIN-Ω WORM Ledger: BLAKE2b Hash Algorithm Demo")
    print("=" * 70)
    print("\n  Demonstrating improved hash algorithm for immutable audit trail")

    demo_hash_algorithm()
    demo_performance()
    demo_worm_ledger()
    demo_proof_carrying_artifact()
    demo_keyed_hashing()
    demo_comparison()

    print("\n" + "=" * 70)
    print("  ✅ Demo Complete!")
    print("=" * 70)
    print("\n  For more information:")
    print("  📖 docs/HASH_ALGORITHM_MIGRATION.md")
    print("  🧪 tests/test_hash_utils.py")
    print("  🧪 tests/test_worm_ledger_blake2b.py")
    print()


if __name__ == "__main__":
    main()
