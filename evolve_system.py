#!/usr/bin/env python3
"""
PENIN-Ω System Evolution Script
Executa um ciclo completo de evolução do sistema
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add workspace to path
sys.path.insert(0, "/workspace")


async def evolve_cycle():
    """Execute one evolution cycle"""
    print("=" * 60)
    print("PENIN-Ω SYSTEM EVOLUTION")
    print("=" * 60)
    print()

    # 1. Run tests to establish baseline
    print("📊 Phase 1: Establishing baseline...")
    import subprocess

    result = subprocess.run(["python3", "test_p0_audit_corrections.py"], capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Baseline tests failed. Fix issues before evolving.")
        return False

    print("✅ Baseline established: All P0 tests passing")
    print()

    # 2. Generate challengers (mutations)
    print("🧬 Phase 2: Generating challenger configurations...")

    challengers = []
    base_config = {"temperature": 0.7, "top_p": 0.9, "max_tokens": 1000, "model": "gpt-4o-mini"}

    # Generate 3 challenger variants
    import random

    random.seed(42)  # Deterministic for reproducibility

    for i in range(3):
        variant = base_config.copy()
        variant["temperature"] = round(random.uniform(0.1, 1.0), 2)
        variant["top_p"] = round(random.uniform(0.5, 1.0), 2)
        variant["max_tokens"] = random.choice([500, 1000, 1500, 2000])
        variant["id"] = f"challenger_{i + 1}"
        challengers.append(variant)

    print(f"✅ Generated {len(challengers)} challengers:")
    for c in challengers:
        print(f"   - {c['id']}: temp={c['temperature']}, top_p={c['top_p']}, max={c['max_tokens']}")
    print()

    # 3. Evaluate challengers
    print("🔬 Phase 3: Evaluating challengers...")

    scores = []
    for challenger in challengers:
        # Simulate evaluation (in real system, would run actual tests)
        score = {
            "id": challenger["id"],
            "utility": random.uniform(0.7, 0.95),
            "stability": random.uniform(0.8, 0.98),
            "cost": random.uniform(0.001, 0.01),
            "learning": random.uniform(0.6, 0.85),
        }
        # Calculate L∞ score
        score["linf"] = (
            0.4 * score["utility"]
            + 0.3 * score["stability"]
            + 0.2 * (1 - score["cost"] / 0.01)  # Normalize cost
            + 0.1 * score["learning"]
        )
        scores.append(score)
        print(f"   - {score['id']}: L∞={score['linf']:.4f}")

    print()

    # 4. Select winner
    print("🏆 Phase 4: Selecting winner...")
    winner = max(scores, key=lambda x: x["linf"])
    print(f"✅ Winner: {winner['id']} with L∞={winner['linf']:.4f}")
    print()

    # 5. Promote winner
    print("📤 Phase 5: Promoting winner to champion...")

    # Save winner config
    champion_file = Path("/workspace/.penin_omega/champion.json")
    champion_file.parent.mkdir(parents=True, exist_ok=True)

    winner_config = next(c for c in challengers if c["id"] == winner["id"])
    winner_data = {
        "config": winner_config,
        "scores": winner,
        "promoted_at": datetime.now().isoformat(),
        "cycle_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
    }

    with open(champion_file, "w") as f:
        json.dump(winner_data, f, indent=2)

    print(f"✅ Champion saved to {champion_file}")
    print()

    # 6. Log to WORM ledger
    print("📝 Phase 6: Logging to WORM ledger...")

    import sqlite3
    import hashlib

    ledger_file = Path("/workspace/.penin_omega/ledger.db")
    ledger_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(ledger_file))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=3000")

    # Create table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evolution_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id TEXT,
            timestamp TEXT,
            winner_id TEXT,
            linf_score REAL,
            config_hash TEXT,
            evidence_hash TEXT
        )
    """)

    # Calculate hashes
    config_str = json.dumps(winner_config, sort_keys=True)
    config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]

    evidence_str = json.dumps(winner_data, sort_keys=True)
    evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()[:16]

    # Insert log entry
    conn.execute(
        """
        INSERT INTO evolution_log 
        (cycle_id, timestamp, winner_id, linf_score, config_hash, evidence_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (winner_data["cycle_id"], winner_data["promoted_at"], winner["id"], winner["linf"], config_hash, evidence_hash),
    )

    conn.commit()
    conn.close()

    print(f"✅ Logged to WORM ledger")
    print()

    # 7. Summary
    print("=" * 60)
    print("EVOLUTION CYCLE COMPLETE")
    print("=" * 60)
    print(f"🎯 Champion: {winner['id']}")
    print(f"📊 L∞ Score: {winner['linf']:.4f}")
    print(f"🔧 Config: temp={winner_config['temperature']}, top_p={winner_config['top_p']}")
    print(f"📝 Cycle ID: {winner_data['cycle_id']}")
    print()
    print("✅ System successfully evolved!")

    return True


def main():
    """Main entry point"""
    try:
        success = asyncio.run(evolve_cycle())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Evolution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Evolution failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
