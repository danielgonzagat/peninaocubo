"""
Swarm Cognitive System - Gossip Protocol
=======================================

Implements local gossip between logical nodes using SQLite/WORM persistence.
Aggregates global state from heartbeats for coherence calculation.
"""

import os
import sqlite3
import time
import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class HeartbeatStatus(Enum):
    """Heartbeat status"""
    ACTIVE = "active"
    STALE = "stale"
    DEAD = "dead"


@dataclass
class Heartbeat:
    """Heartbeat data structure"""
    node_id: str
    timestamp: float
    payload: Dict[str, Any]
    status: HeartbeatStatus = HeartbeatStatus.ACTIVE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "status": self.status.value
        }


class SwarmDatabase:
    """SQLite database for swarm heartbeats"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS heartbeats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT DEFAULT 'active'
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
    
    def insert_heartbeat(self, heartbeat: Heartbeat) -> int:
        """Insert heartbeat into database"""
        with sqlite3.connect(self.db_path) as con:
            cursor = con.execute("""
                INSERT INTO heartbeats (node_id, timestamp, payload, status)
                VALUES (?, ?, ?, ?)
            """, (
                heartbeat.node_id,
                heartbeat.timestamp,
                json.dumps(heartbeat.payload),
                heartbeat.status.value
            ))
            return cursor.lastrowid
    
    def get_recent_heartbeats(self, window_s: float = 60.0) -> List[Heartbeat]:
        """Get recent heartbeats within window"""
        cutoff_time = time.time() - window_s
        
        with sqlite3.connect(self.db_path) as con:
            cursor = con.execute("""
                SELECT node_id, timestamp, payload, status
                FROM heartbeats
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff_time,))
            
            heartbeats = []
            for row in cursor.fetchall():
                heartbeat = Heartbeat(
                    node_id=row[0],
                    timestamp=row[1],
                    payload=json.loads(row[2]),
                    status=HeartbeatStatus(row[3])
                )
                heartbeats.append(heartbeat)
            
            return heartbeats
    
    def get_node_heartbeats(self, node_id: str, limit: int = 10) -> List[Heartbeat]:
        """Get recent heartbeats for specific node"""
        with sqlite3.connect(self.db_path) as con:
            cursor = con.execute("""
                SELECT node_id, timestamp, payload, status
                FROM heartbeats
                WHERE node_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (node_id, limit))
            
            heartbeats = []
            for row in cursor.fetchall():
                heartbeat = Heartbeat(
                    node_id=row[0],
                    timestamp=row[1],
                    payload=json.loads(row[2]),
                    status=HeartbeatStatus(row[3])
                )
                heartbeats.append(heartbeat)
            
            return heartbeats
    
    def cleanup_old_heartbeats(self, max_age_s: float = 3600.0) -> int:
        """Clean up old heartbeats"""
        cutoff_time = time.time() - max_age_s
        
        with sqlite3.connect(self.db_path) as con:
            cursor = con.execute("""
                DELETE FROM heartbeats
                WHERE timestamp < ?
            """, (cutoff_time,))
            
            return cursor.rowcount


class SwarmAggregator:
    """Aggregates swarm heartbeats into global state"""
    
    def __init__(self, aggregation_window_s: float = 60.0):
        self.aggregation_window_s = aggregation_window_s
    
    def aggregate_heartbeats(self, heartbeats: List[Heartbeat]) -> Dict[str, Any]:
        """
        Aggregate heartbeats into global state
        
        Args:
            heartbeats: List of heartbeats
            
        Returns:
            Aggregated global state
        """
        if not heartbeats:
            return {"nodes_count": 0, "global_coherence": 0.0}
        
        # Group by node
        node_data = {}
        for hb in heartbeats:
            if hb.node_id not in node_data:
                node_data[hb.node_id] = []
            node_data[hb.node_id].append(hb)
        
        # Aggregate metrics
        aggregated = {
            "nodes_count": len(node_data),
            "total_heartbeats": len(heartbeats),
            "timestamp": time.time()
        }
        
        # Aggregate common metrics
        metrics_to_aggregate = ["phi", "sr", "G", "alpha_eff", "caos_phi"]
        
        for metric in metrics_to_aggregate:
            values = []
            for hb in heartbeats:
                if metric in hb.payload:
                    try:
                        values.append(float(hb.payload[metric]))
                    except (ValueError, TypeError):
                        continue
            
            if values:
                aggregated[f"{metric}_mean"] = sum(values) / len(values)
                aggregated[f"{metric}_min"] = min(values)
                aggregated[f"{metric}_max"] = max(values)
                aggregated[f"{metric}_count"] = len(values)
        
        # Calculate global coherence as harmonic mean of individual G values
        g_values = []
        for hb in heartbeats:
            if "G" in hb.payload:
                try:
                    g_val = float(hb.payload["G"])
                    if g_val > 0:
                        g_values.append(g_val)
                except (ValueError, TypeError):
                    continue
        
        if g_values:
            # Harmonic mean
            aggregated["global_coherence"] = len(g_values) / sum(1.0 / g for g in g_values)
        else:
            aggregated["global_coherence"] = 0.0
        
        return aggregated
    
    def detect_anomalies(self, heartbeats: List[Heartbeat]) -> List[Dict[str, Any]]:
        """Detect anomalous heartbeats"""
        anomalies = []
        
        # Check for stale nodes
        current_time = time.time()
        stale_threshold = 300.0  # 5 minutes
        
        node_last_seen = {}
        for hb in heartbeats:
            if hb.node_id not in node_last_seen or hb.timestamp > node_last_seen[hb.node_id]:
                node_last_seen[hb.node_id] = hb.timestamp
        
        for node_id, last_seen in node_last_seen.items():
            if current_time - last_seen > stale_threshold:
                anomalies.append({
                    "type": "stale_node",
                    "node_id": node_id,
                    "last_seen": last_seen,
                    "stale_duration": current_time - last_seen
                })
        
        # Check for metric anomalies
        for metric in ["phi", "sr", "G", "alpha_eff"]:
            values = []
            for hb in heartbeats:
                if metric in hb.payload:
                    try:
                        values.append(float(hb.payload[metric]))
                    except (ValueError, TypeError):
                        continue
            
            if len(values) > 2:
                mean_val = sum(values) / len(values)
                std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5
                
                for hb in heartbeats:
                    if metric in hb.payload:
                        try:
                            val = float(hb.payload[metric])
                            if abs(val - mean_val) > 3 * std_val:
                                anomalies.append({
                                    "type": "metric_anomaly",
                                    "node_id": hb.node_id,
                                    "metric": metric,
                                    "value": val,
                                    "mean": mean_val,
                                    "std": std_val
                                })
                        except (ValueError, TypeError):
                            continue
        
        return anomalies


class SwarmNode:
    """Individual swarm node"""
    
    def __init__(self, node_id: str, swarm_db: SwarmDatabase):
        self.node_id = node_id
        self.swarm_db = swarm_db
        self.last_heartbeat_time = 0
        self.heartbeat_interval = 30.0  # seconds
    
    def send_heartbeat(self, payload: Dict[str, Any]) -> int:
        """Send heartbeat to swarm"""
        heartbeat = Heartbeat(
            node_id=self.node_id,
            timestamp=time.time(),
            payload=payload
        )
        
        heartbeat_id = self.swarm_db.insert_heartbeat(heartbeat)
        self.last_heartbeat_time = heartbeat.timestamp
        
        return heartbeat_id
    
    def should_heartbeat(self) -> bool:
        """Check if node should send heartbeat"""
        return time.time() - self.last_heartbeat_time > self.heartbeat_interval
    
    def get_global_state(self, window_s: float = 60.0) -> Dict[str, Any]:
        """Get aggregated global state"""
        heartbeats = self.swarm_db.get_recent_heartbeats(window_s)
        aggregator = SwarmAggregator()
        return aggregator.aggregate_heartbeats(heartbeats)


class SwarmManager:
    """Manages the entire swarm"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.swarm_db = SwarmDatabase(db_path)
        self.aggregator = SwarmAggregator()
        self.nodes: Dict[str, SwarmNode] = {}
    
    def create_node(self, node_id: str) -> SwarmNode:
        """Create a new swarm node"""
        node = SwarmNode(node_id, self.swarm_db)
        self.nodes[node_id] = node
        return node
    
    def get_node(self, node_id: str) -> Optional[SwarmNode]:
        """Get existing node"""
        return self.nodes.get(node_id)
    
    def heartbeat(self, node_id: str, payload: Dict[str, Any]) -> int:
        """Send heartbeat from node"""
        node = self.get_node(node_id)
        if not node:
            node = self.create_node(node_id)
        
        return node.send_heartbeat(payload)
    
    def sample_global_state(self, window_s: float = 60.0) -> Dict[str, Any]:
        """Sample global state from recent heartbeats"""
        heartbeats = self.swarm_db.get_recent_heartbeats(window_s)
        return self.aggregator.aggregate_heartbeats(heartbeats)
    
    def detect_anomalies(self, window_s: float = 300.0) -> List[Dict[str, Any]]:
        """Detect anomalies in swarm"""
        heartbeats = self.swarm_db.get_recent_heartbeats(window_s)
        return self.aggregator.detect_anomalies(heartbeats)
    
    def cleanup(self, max_age_s: float = 3600.0) -> int:
        """Clean up old heartbeats"""
        return self.swarm_db.cleanup_old_heartbeats(max_age_s)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get swarm statistics"""
        heartbeats = self.swarm_db.get_recent_heartbeats(300.0)  # 5 minutes
        global_state = self.sample_global_state(300.0)
        anomalies = self.detect_anomalies(300.0)
        
        return {
            "active_nodes": len(self.nodes),
            "recent_heartbeats": len(heartbeats),
            "global_coherence": global_state.get("global_coherence", 0.0),
            "anomalies_count": len(anomalies),
            "anomalies": anomalies,
            "global_state": global_state
        }


# Global swarm instance
_global_swarm: Optional[SwarmManager] = None


def get_global_swarm() -> SwarmManager:
    """Get global swarm instance"""
    global _global_swarm
    
    if _global_swarm is None:
        # Use default path
        root_path = Path.home() / ".penin_omega" / "state"
        root_path.mkdir(parents=True, exist_ok=True)
        db_path = str(root_path / "heartbeats.db")
        
        _global_swarm = SwarmManager(db_path)
    
    return _global_swarm


def heartbeat(node_id: str, payload: Dict[str, Any]) -> int:
    """Convenience function to send heartbeat"""
    swarm = get_global_swarm()
    return swarm.heartbeat(node_id, payload)


def sample_global_state(window_s: float = 60.0) -> Dict[str, Any]:
    """Convenience function to sample global state"""
    swarm = get_global_swarm()
    return swarm.sample_global_state(window_s)


def test_swarm_system() -> Dict[str, Any]:
    """Test swarm system"""
    swarm = get_global_swarm()
    
    # Create test nodes
    node_a = swarm.create_node("node-A")
    node_b = swarm.create_node("node-B")
    node_c = swarm.create_node("node-C")
    
    # Send heartbeats
    node_a.send_heartbeat({"phi": 0.7, "sr": 0.85, "G": 0.9, "alpha_eff": 0.02})
    node_b.send_heartbeat({"phi": 0.8, "sr": 0.82, "G": 0.88, "alpha_eff": 0.025})
    node_c.send_heartbeat({"phi": 0.75, "sr": 0.87, "G": 0.92, "alpha_eff": 0.023})
    
    # Sample global state
    global_state = swarm.sample_global_state()
    
    # Detect anomalies
    anomalies = swarm.detect_anomalies()
    
    # Get stats
    stats = swarm.get_stats()
    
    return {
        "global_state": global_state,
        "anomalies": anomalies,
        "stats": stats
    }