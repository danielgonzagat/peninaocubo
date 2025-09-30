"""
Swarm Cognitive Module - Gossip Protocol & Global State Aggregation
===================================================================

Implements a lightweight swarm intelligence system where:
- Multiple logical nodes share state via heartbeat/gossip
- Global coherence (G) is computed from swarm consensus
- Uses local SQLite for persistence (single-node PoC, extensible to multi-node)

This enables distributed cognition while maintaining auditability.
"""

import os
import sqlite3
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


# Root directory for PENIN state
ROOT = Path(os.getenv("PENIN_ROOT", Path.home() / ".penin_omega"))
DB = ROOT / "state" / "heartbeats.db"


@dataclass
class SwarmNode:
    """Represents a node in the swarm"""
    node_id: str
    role: str  # "core", "explorer", "validator", etc.
    metrics: Dict[str, float]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "role": self.role,
            "metrics": self.metrics,
            "timestamp": self.timestamp
        }


def _init_db():
    """Initialize swarm database"""
    DB.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS hb (
                node TEXT,
                ts REAL,
                payload TEXT,
                role TEXT DEFAULT 'core'
            )
        """)
        con.commit()


def heartbeat(node: str, payload: Dict[str, Any], role: str = "core") -> None:
    """
    Record a heartbeat from a node.
    
    Args:
        node: Node identifier
        payload: Metrics payload (should contain phi, sr, G, etc.)
        role: Node role (core, explorer, validator)
    """
    _init_db()
    
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO hb(node, ts, payload, role) VALUES(?, ?, ?, ?)",
            (node, time.time(), json.dumps(payload), role)
        )
        con.commit()


def sample_global_state(window_s: float = 60.0) -> Dict[str, float]:
    """
    Sample global state from recent heartbeats.
    
    Args:
        window_s: Time window in seconds
        
    Returns:
        Dict with aggregated metrics (mean over window)
    """
    _init_db()
    
    t0 = time.time() - window_s
    
    with sqlite3.connect(DB) as con:
        cur = con.execute("SELECT payload FROM hb WHERE ts >= ?", (t0,))
        data = [json.loads(r[0]) for r in cur.fetchall()]
    
    if not data:
        return {}
    
    # Aggregate metrics (simple mean for now)
    agg = {}
    counts = {}
    
    for payload in data:
        for k, v in payload.items():
            try:
                v_float = float(v)
                agg[k] = agg.get(k, 0.0) + v_float
                counts[k] = counts.get(k, 0) + 1
            except (ValueError, TypeError):
                pass
    
    # Calculate means
    result = {}
    for k, total in agg.items():
        result[k] = total / max(1, counts[k])
    
    return result


def compute_global_coherence(window_s: float = 60.0) -> float:
    """
    Compute global coherence (G) from swarm state.
    
    G is computed as the harmonic mean of key metrics across all nodes.
    
    Args:
        window_s: Time window in seconds
        
    Returns:
        Global coherence score [0, 1]
    """
    state = sample_global_state(window_s)
    
    # Extract key metrics for coherence
    key_metrics = ["phi", "sr", "ece", "rho"]
    
    values = []
    for metric in key_metrics:
        if metric in state:
            # Normalize to [0, 1] if needed
            val = state[metric]
            if metric == "ece":
                val = max(0.0, 1.0 - val / 0.01)  # Lower ECE is better
            elif metric == "rho":
                val = max(0.0, 1.0 - val)  # Lower rho is better
            
            values.append(max(1e-9, min(1.0, val)))
    
    if not values:
        return 0.0
    
    # Harmonic mean (non-compensatory)
    return len(values) / sum(1.0 / v for v in values)


def get_swarm_health() -> Dict[str, Any]:
    """
    Get overall swarm health metrics.
    
    Returns:
        Dict with health indicators
    """
    _init_db()
    
    with sqlite3.connect(DB) as con:
        # Count nodes
        cur = con.execute("SELECT COUNT(DISTINCT node) FROM hb WHERE ts >= ?", 
                         (time.time() - 300,))
        active_nodes = cur.fetchone()[0]
        
        # Get roles distribution
        cur = con.execute(
            "SELECT role, COUNT(DISTINCT node) FROM hb WHERE ts >= ? GROUP BY role",
            (time.time() - 300,)
        )
        roles = dict(cur.fetchall())
        
        # Get total heartbeats
        cur = con.execute("SELECT COUNT(*) FROM hb WHERE ts >= ?",
                         (time.time() - 300,))
        total_hb = cur.fetchone()[0]
    
    G = compute_global_coherence(window_s=300)
    
    return {
        "active_nodes": active_nodes,
        "roles": roles,
        "total_heartbeats": total_hb,
        "global_coherence": G,
        "healthy": G >= 0.85 and active_nodes > 0
    }


def get_node_history(node: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get heartbeat history for a specific node.
    
    Args:
        node: Node identifier
        limit: Maximum number of records
        
    Returns:
        List of heartbeat records
    """
    _init_db()
    
    with sqlite3.connect(DB) as con:
        cur = con.execute(
            "SELECT ts, payload, role FROM hb WHERE node = ? ORDER BY ts DESC LIMIT ?",
            (node, limit)
        )
        
        records = []
        for ts, payload, role in cur.fetchall():
            records.append({
                "timestamp": ts,
                "payload": json.loads(payload),
                "role": role
            })
    
    return records


def cleanup_old_heartbeats(max_age_s: float = 86400) -> int:
    """
    Clean up old heartbeat records.
    
    Args:
        max_age_s: Maximum age in seconds (default 24h)
        
    Returns:
        Number of records deleted
    """
    _init_db()
    
    cutoff = time.time() - max_age_s
    
    with sqlite3.connect(DB) as con:
        cur = con.execute("DELETE FROM hb WHERE ts < ?", (cutoff,))
        con.commit()
        return cur.rowcount


class SwarmOrchestrator:
    """
    Orchestrates swarm-based global coherence computation.
    
    This enables distributed decision-making where multiple nodes
    contribute to the global state, and coherence (G) reflects
    the consensus quality.
    """
    
    def __init__(self, node_id: str = "core-0", role: str = "core"):
        self.node_id = node_id
        self.role = role
        print(f"🐝 Swarm node {node_id} initialized (role={role})")
    
    def emit_heartbeat(self, metrics: Dict[str, float]) -> None:
        """Emit heartbeat with current metrics"""
        heartbeat(self.node_id, metrics, self.role)
    
    def get_global_coherence(self, window_s: float = 60.0) -> float:
        """Get current global coherence"""
        return compute_global_coherence(window_s)
    
    def get_health(self) -> Dict[str, Any]:
        """Get swarm health"""
        return get_swarm_health()
    
    def sync_state(self) -> Dict[str, Any]:
        """
        Synchronize with swarm and return global state.
        
        Returns:
            Dict with global metrics
        """
        state = sample_global_state(window_s=60.0)
        health = self.get_health()
        
        return {
            "global_state": state,
            "health": health,
            "node_id": self.node_id,
            "timestamp": time.time()
        }


# Quick test function
def quick_swarm_test():
    """Quick test of swarm functionality"""
    orch = SwarmOrchestrator("test-node-1", "core")
    
    # Emit some heartbeats
    for i in range(5):
        metrics = {
            "phi": 0.7 + i * 0.02,
            "sr": 0.85 + i * 0.01,
            "ece": 0.005 - i * 0.0001,
            "rho": 0.9 - i * 0.01
        }
        orch.emit_heartbeat(metrics)
        time.sleep(0.1)
    
    # Get global state
    state = orch.sync_state()
    print(f"Global state: {state}")
    
    # Get health
    health = orch.get_health()
    print(f"Swarm health: {health}")
    
    return orch