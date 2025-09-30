"""
Swarm Cognitive System - Gossip Protocol
========================================

Implements cognitive swarm with gossip protocol for local coordination.
Uses SQLite/WORM for persistence and aggregation of global state.
"""

import os
import sqlite3
import time
import random
import json
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class NodeStatus(Enum):
    """Node status in swarm"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


@dataclass
class HeartbeatPayload:
    """Payload for heartbeat messages"""
    node_id: str
    timestamp: float
    metrics: Dict[str, float]
    status: str
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "status": self.status,
            "version": self.version
        }


class SwarmDatabase:
    """SQLite database for swarm state"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS heartbeats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL DEFAULT (julianday('now'))
                )
            """)
            
            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_node_timestamp 
                ON heartbeats(node_id, timestamp)
            """)
            
            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON heartbeats(timestamp)
            """)
            
            con.commit()
    
    def record_heartbeat(self, payload: HeartbeatPayload):
        """Record heartbeat in database"""
        with self.lock:
            with sqlite3.connect(self.db_path) as con:
                con.execute(
                    "INSERT INTO heartbeats (node_id, timestamp, payload) VALUES (?, ?, ?)",
                    (payload.node_id, payload.timestamp, json.dumps(payload.to_dict()))
                )
                con.commit()
    
    def get_recent_heartbeats(self, window_s: float = 60.0) -> List[Dict[str, Any]]:
        """Get recent heartbeats within time window"""
        cutoff_time = time.time() - window_s
        
        with self.lock:
            with sqlite3.connect(self.db_path) as con:
                cur = con.execute(
                    "SELECT payload FROM heartbeats WHERE timestamp >= ? ORDER BY timestamp DESC",
                    (cutoff_time,)
                )
                return [json.loads(row[0]) for row in cur.fetchall()]
    
    def get_node_heartbeats(self, node_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent heartbeats for specific node"""
        with self.lock:
            with sqlite3.connect(self.db_path) as con:
                cur = con.execute(
                    "SELECT payload FROM heartbeats WHERE node_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (node_id, limit)
                )
                return [json.loads(row[0]) for row in cur.fetchall()]
    
    def cleanup_old_heartbeats(self, max_age_s: float = 3600.0):
        """Clean up old heartbeats"""
        cutoff_time = time.time() - max_age_s
        
        with self.lock:
            with sqlite3.connect(self.db_path) as con:
                cur = con.execute(
                    "DELETE FROM heartbeats WHERE timestamp < ?",
                    (cutoff_time,)
                )
                deleted = cur.rowcount
                con.commit()
                return deleted


class SwarmNode:
    """Individual node in the cognitive swarm"""
    
    def __init__(self, node_id: str, swarm_db: SwarmDatabase):
        self.node_id = node_id
        self.swarm_db = swarm_db
        self.status = NodeStatus.ACTIVE
        self.last_heartbeat = 0.0
        self.heartbeat_interval = 10.0  # seconds
        self.metrics = {}
        
    def update_metrics(self, metrics: Dict[str, float]):
        """Update node metrics"""
        self.metrics.update(metrics)
        self.metrics["node_id"] = self.node_id
        self.metrics["status"] = self.status.value
        self.metrics["timestamp"] = time.time()
    
    def send_heartbeat(self) -> bool:
        """Send heartbeat to swarm"""
        try:
            payload = HeartbeatPayload(
                node_id=self.node_id,
                timestamp=time.time(),
                metrics=self.metrics.copy(),
                status=self.status.value
            )
            
            self.swarm_db.record_heartbeat(payload)
            self.last_heartbeat = time.time()
            return True
        except Exception as e:
            print(f"Node {self.node_id} heartbeat failed: {e}")
            return False
    
    def get_global_state(self, window_s: float = 60.0) -> Dict[str, Any]:
        """Get aggregated global state from swarm"""
        heartbeats = self.swarm_db.get_recent_heartbeats(window_s)
        
        if not heartbeats:
            return {"nodes": 0, "metrics": {}}
        
        # Aggregate metrics across all nodes
        all_metrics = {}
        node_count = 0
        
        for heartbeat in heartbeats:
            node_count += 1
            metrics = heartbeat.get("metrics", {})
            
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    if key not in all_metrics:
                        all_metrics[key] = []
                    all_metrics[key].append(value)
        
        # Compute aggregated values
        aggregated = {}
        for key, values in all_metrics.items():
            if values:
                aggregated[key] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        
        return {
            "nodes": node_count,
            "metrics": aggregated,
            "window_s": window_s,
            "timestamp": time.time()
        }


class SwarmOrchestrator:
    """Orchestrator for the cognitive swarm"""
    
    def __init__(self, root_dir: str = None):
        if root_dir is None:
            root_dir = os.getenv("PENIN_ROOT", str(Path.home() / ".penin_omega"))
        
        self.root_dir = Path(root_dir)
        self.state_dir = self.root_dir / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.state_dir / "heartbeats.db"
        self.swarm_db = SwarmDatabase(str(self.db_path))
        
        self.nodes: Dict[str, SwarmNode] = {}
        self.global_state_cache = {}
        self.cache_ttl = 5.0  # seconds
        
    def create_node(self, node_id: str) -> SwarmNode:
        """Create new swarm node"""
        node = SwarmNode(node_id, self.swarm_db)
        self.nodes[node_id] = node
        return node
    
    def heartbeat(self, node_id: str, payload: Dict[str, Any]) -> bool:
        """Send heartbeat from node"""
        if node_id not in self.nodes:
            self.create_node(node_id)
        
        node = self.nodes[node_id]
        node.update_metrics(payload)
        return node.send_heartbeat()
    
    def sample_global_state(self, window_s: float = 60.0) -> Dict[str, Any]:
        """Sample global state from swarm"""
        cache_key = f"global_state_{window_s}"
        now = time.time()
        
        # Check cache
        if cache_key in self.global_state_cache:
            cached_time, cached_data = self.global_state_cache[cache_key]
            if now - cached_time < self.cache_ttl:
                return cached_data
        
        # Compute fresh state
        heartbeats = self.swarm_db.get_recent_heartbeats(window_s)
        
        if not heartbeats:
            state = {"nodes": 0, "metrics": {}, "timestamp": now}
        else:
            # Aggregate metrics
            all_metrics = {}
            node_ids = set()
            
            for heartbeat in heartbeats:
                node_ids.add(heartbeat["node_id"])
                metrics = heartbeat.get("metrics", {})
                
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        if key not in all_metrics:
                            all_metrics[key] = []
                        all_metrics[key].append(value)
            
            # Compute aggregated values
            aggregated = {}
            for key, values in all_metrics.items():
                if values:
                    aggregated[key] = {
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "std": self._std_dev(values),
                        "count": len(values)
                    }
            
            state = {
                "nodes": len(node_ids),
                "node_ids": list(node_ids),
                "metrics": aggregated,
                "window_s": window_s,
                "timestamp": now
            }
        
        # Cache result
        self.global_state_cache[cache_key] = (now, state)
        return state
    
    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def get_node_status(self, node_id: str) -> Dict[str, Any]:
        """Get status of specific node"""
        heartbeats = self.swarm_db.get_node_heartbeats(node_id, limit=5)
        
        if not heartbeats:
            return {"status": "unknown", "last_seen": None, "heartbeats": 0}
        
        latest = heartbeats[0]
        last_seen = latest.get("timestamp", 0)
        time_since_last = time.time() - last_seen
        
        status = "active" if time_since_last < 30 else "inactive"
        
        return {
            "status": status,
            "last_seen": last_seen,
            "time_since_last": time_since_last,
            "heartbeats": len(heartbeats),
            "latest_metrics": latest.get("metrics", {})
        }
    
    def cleanup_old_data(self, max_age_s: float = 3600.0) -> int:
        """Clean up old heartbeat data"""
        return self.swarm_db.cleanup_old_heartbeats(max_age_s)
    
    def get_swarm_stats(self) -> Dict[str, Any]:
        """Get swarm statistics"""
        recent_state = self.sample_global_state(60.0)
        
        return {
            "active_nodes": recent_state["nodes"],
            "node_ids": recent_state.get("node_ids", []),
            "metrics_count": len(recent_state.get("metrics", {})),
            "db_path": str(self.db_path),
            "cache_size": len(self.global_state_cache),
            "timestamp": time.time()
        }


# Global swarm instance
_global_swarm: Optional[SwarmOrchestrator] = None


def get_global_swarm() -> SwarmOrchestrator:
    """Get global swarm instance"""
    global _global_swarm
    if _global_swarm is None:
        _global_swarm = SwarmOrchestrator()
    return _global_swarm


def heartbeat(node_id: str, payload: Dict[str, Any]) -> bool:
    """Send heartbeat to global swarm"""
    swarm = get_global_swarm()
    return swarm.heartbeat(node_id, payload)


def sample_global_state(window_s: float = 60.0) -> Dict[str, Any]:
    """Sample global state from swarm"""
    swarm = get_global_swarm()
    return swarm.sample_global_state(window_s)


def get_node_status(node_id: str) -> Dict[str, Any]:
    """Get status of specific node"""
    swarm = get_global_swarm()
    return swarm.get_node_status(node_id)


# Integration with Life Equation
def compute_global_coherence_G(swarm_state: Dict[str, Any]) -> float:
    """
    Compute global coherence G from swarm state
    
    G = harmonic mean of key metrics across all nodes
    """
    metrics = swarm_state.get("metrics", {})
    
    if not metrics:
        return 0.0
    
    # Key metrics for coherence
    key_metrics = ["phi", "sr", "alpha_eff", "L_inf"]
    values = []
    
    for metric in key_metrics:
        if metric in metrics:
            mean_val = metrics[metric].get("mean", 0.0)
            if mean_val > 0:
                values.append(mean_val)
    
    if not values:
        return 0.0
    
    # Harmonic mean
    return len(values) / sum(1.0 / v for v in values)


# Example usage
if __name__ == "__main__":
    # Create swarm
    swarm = SwarmOrchestrator()
    
    # Create nodes
    node1 = swarm.create_node("node-A")
    node2 = swarm.create_node("node-B")
    
    # Send heartbeats
    node1.update_metrics({"phi": 0.7, "sr": 0.85, "G": 0.9})
    node1.send_heartbeat()
    
    node2.update_metrics({"phi": 0.8, "sr": 0.82, "G": 0.88})
    node2.send_heartbeat()
    
    # Sample global state
    global_state = swarm.sample_global_state()
    print(f"Global state: {global_state}")
    
    # Compute global coherence
    G = compute_global_coherence_G(global_state)
    print(f"Global coherence G: {G:.3f}")
    
    # Get stats
    stats = swarm.get_swarm_stats()
    print(f"Swarm stats: {stats}")