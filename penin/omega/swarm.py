"""
Swarm Cognitive - Local Gossip Protocol
========================================

Implements local gossip/heartbeat protocol for swarm intelligence.
Uses SQLite for persistence and aggregates global state.
"""

import os
import sqlite3
import time
import random
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


ROOT = Path(os.getenv("PENIN_ROOT", Path.home() / ".penin_omega"))
DB = ROOT / "state" / "heartbeats.db"
DB.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class Heartbeat:
    """Heartbeat data from a swarm node"""
    node: str
    timestamp: float
    phi: float  # CAOS⁺ value
    sr: float   # SR-Ω∞ value
    g: float    # Global coherence
    health: float  # Node health
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.metadata is None:
            d["metadata"] = {}
        return d


def _init_db():
    """Initialize database schema"""
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS heartbeats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node TEXT NOT NULL,
                timestamp REAL NOT NULL,
                phi REAL,
                sr REAL,
                g REAL,
                health REAL,
                payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON heartbeats(timestamp DESC)
        """)
        con.execute("""
            CREATE INDEX IF NOT EXISTS idx_node 
            ON heartbeats(node)
        """)
        con.commit()


def heartbeat(node: str, payload: Dict[str, Any]) -> bool:
    """
    Record a heartbeat from a node.
    
    Args:
        node: Node identifier
        payload: Metrics payload (should contain phi, sr, g, health)
    
    Returns:
        True if successfully recorded
    """
    _init_db()
    
    try:
        hb = Heartbeat(
            node=node,
            timestamp=time.time(),
            phi=float(payload.get("phi", 0.0)),
            sr=float(payload.get("sr", 0.0)),
            g=float(payload.get("g", 0.0)),
            health=float(payload.get("health", 1.0)),
            metadata=payload.get("metadata", {})
        )
        
        with sqlite3.connect(DB) as con:
            con.execute("""
                INSERT INTO heartbeats(node, timestamp, phi, sr, g, health, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                hb.node, hb.timestamp, hb.phi, hb.sr, hb.g, hb.health,
                json.dumps(hb.to_dict())
            ))
            con.commit()
        
        return True
    except Exception as e:
        print(f"Heartbeat error: {e}")
        return False


def sample_global_state(window_s: float = 60.0) -> Dict[str, float]:
    """
    Sample and aggregate global state from recent heartbeats.
    
    Args:
        window_s: Time window in seconds
    
    Returns:
        Aggregated metrics dict
    """
    _init_db()
    
    t0 = time.time() - window_s
    
    with sqlite3.connect(DB) as con:
        cur = con.execute("""
            SELECT phi, sr, g, health, payload
            FROM heartbeats
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (t0,))
        
        rows = cur.fetchall()
    
    if not rows:
        return {
            "phi_avg": 0.0,
            "sr_avg": 0.0,
            "g_avg": 0.0,
            "health_avg": 0.0,
            "node_count": 0,
            "window_s": window_s
        }
    
    # Aggregate metrics
    phi_vals = [r[0] for r in rows if r[0] is not None]
    sr_vals = [r[1] for r in rows if r[1] is not None]
    g_vals = [r[2] for r in rows if r[2] is not None]
    health_vals = [r[3] for r in rows if r[3] is not None]
    
    def safe_avg(vals: List[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0
    
    # Non-compensatory: use harmonic mean for critical metrics
    def harmonic_mean(vals: List[float]) -> float:
        if not vals or any(v <= 0 for v in vals):
            return 0.0
        return len(vals) / sum(1.0 / v for v in vals)
    
    return {
        "phi_avg": safe_avg(phi_vals),
        "phi_harmonic": harmonic_mean(phi_vals),
        "sr_avg": safe_avg(sr_vals),
        "sr_harmonic": harmonic_mean(sr_vals),
        "g_avg": safe_avg(g_vals),
        "g_harmonic": harmonic_mean(g_vals),
        "health_avg": safe_avg(health_vals),
        "health_min": min(health_vals) if health_vals else 0.0,
        "node_count": len(set(r[4] for r in rows)),  # Unique nodes
        "sample_count": len(rows),
        "window_s": window_s
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
        cur = con.execute("""
            SELECT timestamp, phi, sr, g, health, payload
            FROM heartbeats
            WHERE node = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (node, limit))
        
        rows = cur.fetchall()
    
    return [
        {
            "timestamp": r[0],
            "phi": r[1],
            "sr": r[2],
            "g": r[3],
            "health": r[4],
            "payload": json.loads(r[5]) if r[5] else {}
        }
        for r in rows
    ]


def detect_anomalies(threshold_stddev: float = 2.0) -> Dict[str, Any]:
    """
    Detect anomalies in swarm metrics.
    
    Args:
        threshold_stddev: Number of standard deviations for anomaly
    
    Returns:
        Dict with anomaly information
    """
    _init_db()
    
    # Get recent data (last 5 minutes)
    window_s = 300
    t0 = time.time() - window_s
    
    with sqlite3.connect(DB) as con:
        cur = con.execute("""
            SELECT node, phi, sr, g, health
            FROM heartbeats
            WHERE timestamp >= ?
        """, (t0,))
        
        rows = cur.fetchall()
    
    if len(rows) < 10:
        return {"anomalies": [], "message": "Insufficient data"}
    
    # Calculate statistics
    import statistics
    
    phi_vals = [r[1] for r in rows if r[1] is not None]
    sr_vals = [r[2] for r in rows if r[2] is not None]
    g_vals = [r[3] for r in rows if r[3] is not None]
    health_vals = [r[4] for r in rows if r[4] is not None]
    
    anomalies = []
    
    for metric_name, vals in [
        ("phi", phi_vals),
        ("sr", sr_vals),
        ("g", g_vals),
        ("health", health_vals)
    ]:
        if len(vals) < 2:
            continue
            
        mean = statistics.mean(vals)
        stddev = statistics.stdev(vals)
        
        if stddev > 0:
            for i, v in enumerate(vals):
                z_score = abs(v - mean) / stddev
                if z_score > threshold_stddev:
                    anomalies.append({
                        "metric": metric_name,
                        "value": v,
                        "z_score": z_score,
                        "node": rows[i][0] if i < len(rows) else "unknown"
                    })
    
    return {
        "anomalies": anomalies,
        "stats": {
            "phi": {"mean": statistics.mean(phi_vals), "stddev": statistics.stdev(phi_vals)} if len(phi_vals) > 1 else {},
            "sr": {"mean": statistics.mean(sr_vals), "stddev": statistics.stdev(sr_vals)} if len(sr_vals) > 1 else {},
            "g": {"mean": statistics.mean(g_vals), "stddev": statistics.stdev(g_vals)} if len(g_vals) > 1 else {},
            "health": {"mean": statistics.mean(health_vals), "stddev": statistics.stdev(health_vals)} if len(health_vals) > 1 else {},
        }
    }


def cleanup_old_heartbeats(days: int = 7) -> int:
    """
    Clean up old heartbeat records.
    
    Args:
        days: Keep records from last N days
    
    Returns:
        Number of deleted records
    """
    _init_db()
    
    cutoff = time.time() - (days * 24 * 3600)
    
    with sqlite3.connect(DB) as con:
        cur = con.execute("""
            DELETE FROM heartbeats
            WHERE timestamp < ?
        """, (cutoff,))
        deleted = cur.rowcount
        con.commit()
    
    return deleted


class SwarmOrchestrator:
    """High-level swarm orchestration"""
    
    def __init__(self, node_id: str = None):
        self.node_id = node_id or f"node-{os.getpid()}"
        _init_db()
    
    def emit_heartbeat(self, metrics: Dict[str, float]) -> bool:
        """Emit heartbeat with current metrics"""
        return heartbeat(self.node_id, metrics)
    
    def get_consensus(self, window_s: float = 60.0) -> Dict[str, Any]:
        """Get swarm consensus metrics"""
        state = sample_global_state(window_s)
        
        # Consensus requires minimum participation
        if state["node_count"] < 2:
            return {
                "consensus": False,
                "reason": "Insufficient nodes",
                "state": state
            }
        
        # Check metric convergence (low variance = consensus)
        anomalies = detect_anomalies(threshold_stddev=1.5)
        
        return {
            "consensus": len(anomalies["anomalies"]) == 0,
            "anomaly_count": len(anomalies["anomalies"]),
            "state": state,
            "stats": anomalies["stats"]
        }
    
    def should_promote(self, min_nodes: int = 3, min_consensus: float = 0.8) -> bool:
        """
        Decide if swarm agrees on promotion.
        
        Args:
            min_nodes: Minimum participating nodes
            min_consensus: Minimum consensus metrics
        
        Returns:
            True if swarm agrees on promotion
        """
        consensus = self.get_consensus()
        
        if not consensus["consensus"]:
            return False
        
        state = consensus["state"]
        
        # Non-compensatory checks
        if state["node_count"] < min_nodes:
            return False
        
        # All critical metrics must be above threshold
        if state["phi_harmonic"] < min_consensus:
            return False
        if state["sr_harmonic"] < min_consensus:
            return False
        if state["g_harmonic"] < min_consensus:
            return False
        if state["health_min"] < 0.7:
            return False
        
        return True