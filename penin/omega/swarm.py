"""
Swarm Cognitive - Gossip protocol for distributed cognition
Local SQLite-based gossip between logical nodes with heartbeat aggregation
"""

import os
import sqlite3
import time
import random
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


# Root directory for PENIN state
ROOT = Path(os.getenv("PENIN_ROOT", Path.home() / ".penin_omega"))
DB = ROOT / "state" / "heartbeats.db"
DB.parent.mkdir(parents=True, exist_ok=True)


def _init():
    """Initialize the heartbeat database"""
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS hb (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node TEXT NOT NULL,
                ts REAL NOT NULL,
                payload TEXT NOT NULL
            )
        """)
        # Create index for faster queries
        con.execute("CREATE INDEX IF NOT EXISTS idx_ts ON hb(ts)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_node ON hb(node)")
        con.commit()


def heartbeat(node: str, payload: dict) -> None:
    """
    Record a heartbeat from a node
    
    Parameters:
    -----------
    node: Node identifier
    payload: Metrics/state dictionary
    """
    _init()
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO hb(node, ts, payload) VALUES(?, ?, ?)",
            (node, time.time(), json.dumps(payload))
        )
        con.commit()


def sample_global_state(window_s: float = 60.0) -> Dict[str, float]:
    """
    Sample and aggregate global state from recent heartbeats
    
    Parameters:
    -----------
    window_s: Time window in seconds to consider
    
    Returns:
    --------
    Aggregated metrics dictionary
    """
    _init()
    t0 = time.time() - window_s
    
    with sqlite3.connect(DB) as con:
        cur = con.execute(
            "SELECT payload FROM hb WHERE ts >= ?",
            (t0,)
        )
        data = [json.loads(r[0]) for r in cur.fetchall()]
    
    if not data:
        return {}
    
    # Simple aggregation (mean of numeric values)
    agg = {}
    counts = {}
    
    for payload in data:
        for key, value in payload.items():
            try:
                val = float(value)
                agg[key] = agg.get(key, 0.0) + val
                counts[key] = counts.get(key, 0) + 1
            except (ValueError, TypeError):
                pass
    
    # Compute means
    result = {}
    for key in agg:
        if counts[key] > 0:
            result[key] = agg[key] / counts[key]
    
    return result


def get_node_history(node: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get heartbeat history for a specific node
    
    Parameters:
    -----------
    node: Node identifier
    limit: Maximum number of records to return
    
    Returns:
    --------
    List of heartbeat records
    """
    _init()
    with sqlite3.connect(DB) as con:
        cur = con.execute(
            "SELECT ts, payload FROM hb WHERE node = ? ORDER BY ts DESC LIMIT ?",
            (node, limit)
        )
        return [
            {"ts": r[0], "payload": json.loads(r[1])}
            for r in cur.fetchall()
        ]


def gossip_consensus(metric: str, window_s: float = 60.0, threshold: float = 0.1) -> Optional[float]:
    """
    Compute consensus value for a metric using gossip protocol
    
    Parameters:
    -----------
    metric: Metric name to compute consensus for
    window_s: Time window for consideration
    threshold: Maximum standard deviation for consensus
    
    Returns:
    --------
    Consensus value if nodes agree within threshold, None otherwise
    """
    _init()
    t0 = time.time() - window_s
    
    with sqlite3.connect(DB) as con:
        cur = con.execute(
            "SELECT payload FROM hb WHERE ts >= ?",
            (t0,)
        )
        data = [json.loads(r[0]) for r in cur.fetchall()]
    
    if not data:
        return None
    
    # Collect metric values
    values = []
    for payload in data:
        if metric in payload:
            try:
                values.append(float(payload[metric]))
            except (ValueError, TypeError):
                pass
    
    if len(values) < 2:
        return values[0] if values else None
    
    # Compute mean and standard deviation
    mean_val = sum(values) / len(values)
    variance = sum((x - mean_val) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5
    
    # Check if consensus is reached
    if std_dev <= threshold:
        return mean_val
    
    return None  # No consensus


def broadcast_update(update: Dict[str, Any], ttl: int = 3) -> None:
    """
    Broadcast an update to the swarm (simulated via DB)
    
    Parameters:
    -----------
    update: Update dictionary to broadcast
    ttl: Time-to-live (hops) for the update
    """
    _init()
    
    # Add metadata
    update["_broadcast"] = True
    update["_ttl"] = ttl
    update["_origin"] = f"node-{os.getpid()}"
    update["_ts"] = time.time()
    
    # Store as special broadcast entry
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO hb(node, ts, payload) VALUES(?, ?, ?)",
            ("_broadcast", time.time(), json.dumps(update))
        )
        con.commit()


def receive_broadcasts(since_ts: float = None) -> List[Dict[str, Any]]:
    """
    Receive broadcast updates from the swarm
    
    Parameters:
    -----------
    since_ts: Timestamp to receive broadcasts from (default: last 60s)
    
    Returns:
    --------
    List of broadcast updates
    """
    _init()
    
    if since_ts is None:
        since_ts = time.time() - 60.0
    
    with sqlite3.connect(DB) as con:
        cur = con.execute(
            "SELECT payload FROM hb WHERE node = '_broadcast' AND ts >= ? ORDER BY ts",
            (since_ts,)
        )
        return [json.loads(r[0]) for r in cur.fetchall()]


def compute_swarm_coherence(window_s: float = 60.0) -> float:
    """
    Compute overall swarm coherence (how aligned nodes are)
    
    Parameters:
    -----------
    window_s: Time window to consider
    
    Returns:
    --------
    Coherence score [0, 1] where 1 is perfect alignment
    """
    state = sample_global_state(window_s)
    
    if not state:
        return 0.0
    
    # Check key metrics for coherence
    coherence_metrics = ["phi", "sr", "G", "alpha_eff"]
    coherence_scores = []
    
    for metric in coherence_metrics:
        consensus = gossip_consensus(metric, window_s, threshold=0.1)
        if consensus is not None and metric in state:
            # Score based on how close consensus is to mean
            diff = abs(consensus - state[metric])
            score = max(0, 1.0 - diff)
            coherence_scores.append(score)
    
    if not coherence_scores:
        return 0.0
    
    return sum(coherence_scores) / len(coherence_scores)


def cleanup_old_heartbeats(days: int = 7) -> int:
    """
    Clean up old heartbeat records
    
    Parameters:
    -----------
    days: Number of days to keep
    
    Returns:
    --------
    Number of records deleted
    """
    _init()
    cutoff = time.time() - (days * 24 * 3600)
    
    with sqlite3.connect(DB) as con:
        cur = con.execute("DELETE FROM hb WHERE ts < ?", (cutoff,))
        deleted = cur.rowcount
        con.commit()
    
    return deleted


def quick_test():
    """Quick test of swarm system"""
    # Send some heartbeats
    nodes = ["node-A", "node-B", "node-C"]
    
    for i, node in enumerate(nodes):
        payload = {
            "phi": 0.7 + i * 0.05,
            "sr": 0.85 - i * 0.02,
            "G": 0.9,
            "alpha_eff": 0.001 * (1 + i * 0.1)
        }
        heartbeat(node, payload)
    
    # Sample global state
    state = sample_global_state(window_s=60.0)
    
    # Check consensus
    phi_consensus = gossip_consensus("phi", window_s=60.0)
    
    # Compute coherence
    coherence = compute_swarm_coherence(window_s=60.0)
    
    # Broadcast test
    broadcast_update({"action": "test", "value": 42})
    broadcasts = receive_broadcasts()
    
    return {
        "state": state,
        "phi_consensus": phi_consensus,
        "coherence": coherence,
        "broadcast_count": len(broadcasts)
    }


if __name__ == "__main__":
    result = quick_test()
    print(f"Swarm state: {result['state']}")
    print(f"Phi consensus: {result['phi_consensus']:.3f}" if result['phi_consensus'] else "No consensus")
    print(f"Swarm coherence: {result['coherence']:.3f}")
    print(f"Broadcasts received: {result['broadcast_count']}")