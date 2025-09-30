"""
Checkpoint & Repair - State Snapshots and Recovery
====================================================

Manages system state snapshots for rollback and recovery.
"""

from pathlib import Path
import time
import hashlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

try:
    import orjson
    json_dumps = lambda x: orjson.dumps(x, option=orjson.OPT_INDENT_2)
    json_loads = lambda x: orjson.loads(x)
except ImportError:
    import json
    json_dumps = lambda x: json.dumps(x, indent=2).encode()
    json_loads = lambda x: json.loads(x)


SNAP = Path.home() / ".penin_omega" / "snapshots"
SNAP.mkdir(parents=True, exist_ok=True)


@dataclass
class Snapshot:
    """System state snapshot"""
    id: str
    timestamp: float
    state: Dict[str, Any]
    metadata: Dict[str, Any] = None
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self._compute_hash()
        if self.metadata is None:
            self.metadata = {}
    
    def _compute_hash(self) -> str:
        """Compute hash of state"""
        data = json_dumps({"state": self.state, "timestamp": self.timestamp})
        return hashlib.sha256(data).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def verify(self) -> bool:
        """Verify snapshot integrity"""
        return self.hash == self._compute_hash()


def save_snapshot(state: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
    """
    Save a state snapshot.
    
    Args:
        state: State dictionary to save
        metadata: Optional metadata
    
    Returns:
        Snapshot ID (filename)
    """
    timestamp = time.time()
    snap_id = f"snap_{int(timestamp)}"
    
    snapshot = Snapshot(
        id=snap_id,
        timestamp=timestamp,
        state=state,
        metadata=metadata or {}
    )
    
    # Save to file
    filename = SNAP / f"{snap_id}.json"
    filename.write_bytes(json_dumps(snapshot.to_dict()))
    
    # Also save a lightweight index entry
    index_file = SNAP / "index.jsonl"
    index_entry = {
        "id": snap_id,
        "timestamp": timestamp,
        "hash": snapshot.hash,
        "metadata": metadata or {}
    }
    with index_file.open("ab") as f:
        f.write(json_dumps(index_entry) + b"\n")
    
    return snap_id


def load_snapshot(snap_id: str) -> Optional[Snapshot]:
    """
    Load a specific snapshot.
    
    Args:
        snap_id: Snapshot ID
    
    Returns:
        Snapshot object or None if not found
    """
    filename = SNAP / f"{snap_id}.json"
    
    if not filename.exists():
        return None
    
    try:
        data = json_loads(filename.read_bytes())
        snapshot = Snapshot(**data)
        
        # Verify integrity
        if not snapshot.verify():
            print(f"Warning: Snapshot {snap_id} failed integrity check")
        
        return snapshot
    except Exception as e:
        print(f"Failed to load snapshot {snap_id}: {e}")
        return None


def restore_last() -> Optional[Dict[str, Any]]:
    """
    Restore the most recent snapshot.
    
    Returns:
        State dict or None if no snapshots
    """
    snapshots = sorted(SNAP.glob("snap_*.json"))
    
    if not snapshots:
        return None
    
    # Try snapshots from newest to oldest
    for snap_file in reversed(snapshots):
        snap_id = snap_file.stem
        snapshot = load_snapshot(snap_id)
        
        if snapshot and snapshot.verify():
            return snapshot.state
    
    return None


def list_snapshots(limit: int = 10) -> List[Dict[str, Any]]:
    """
    List available snapshots.
    
    Args:
        limit: Maximum number to return
    
    Returns:
        List of snapshot metadata
    """
    # Try to use index first
    index_file = SNAP / "index.jsonl"
    
    if index_file.exists():
        entries = []
        with index_file.open("rb") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json_loads(line))
                    except:
                        continue
        
        # Sort by timestamp descending
        entries.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return entries[:limit]
    
    # Fallback to scanning files
    snapshots = []
    for snap_file in sorted(SNAP.glob("snap_*.json"), reverse=True)[:limit]:
        try:
            data = json_loads(snap_file.read_bytes())
            snapshots.append({
                "id": data.get("id"),
                "timestamp": data.get("timestamp"),
                "hash": data.get("hash"),
                "metadata": data.get("metadata", {})
            })
        except:
            continue
    
    return snapshots


def find_snapshot_by_metadata(key: str, value: Any) -> Optional[str]:
    """
    Find a snapshot by metadata value.
    
    Args:
        key: Metadata key
        value: Metadata value to match
    
    Returns:
        Snapshot ID or None
    """
    for snap_info in list_snapshots(limit=1000):
        if snap_info.get("metadata", {}).get(key) == value:
            return snap_info["id"]
    
    return None


def cleanup_old_snapshots(days: int = 7, keep_min: int = 10) -> int:
    """
    Clean up old snapshots.
    
    Args:
        days: Delete snapshots older than this many days
        keep_min: Always keep at least this many snapshots
    
    Returns:
        Number of deleted snapshots
    """
    cutoff = time.time() - (days * 24 * 3600)
    snapshots = sorted(SNAP.glob("snap_*.json"))
    
    # Always keep minimum number
    if len(snapshots) <= keep_min:
        return 0
    
    deleted = 0
    for snap_file in snapshots[:-keep_min]:  # Keep the newest keep_min
        try:
            # Check age
            data = json_loads(snap_file.read_bytes())
            if data.get("timestamp", 0) < cutoff:
                snap_file.unlink()
                deleted += 1
        except:
            continue
    
    return deleted


class CheckpointManager:
    """High-level checkpoint management"""
    
    def __init__(self, auto_snapshot_interval: int = 300):
        self.auto_snapshot_interval = auto_snapshot_interval
        self.last_snapshot_time = 0
        self.snapshot_history = []
        
    def checkpoint(self, state: Dict[str, Any], force: bool = False, **metadata) -> Optional[str]:
        """
        Create a checkpoint if needed.
        
        Args:
            state: Current state
            force: Force snapshot even if interval not reached
            **metadata: Additional metadata
        
        Returns:
            Snapshot ID or None if skipped
        """
        current_time = time.time()
        
        # Check if we should snapshot
        if not force:
            if current_time - self.last_snapshot_time < self.auto_snapshot_interval:
                return None
        
        # Create snapshot
        snap_id = save_snapshot(state, metadata)
        
        # Update tracking
        self.last_snapshot_time = current_time
        self.snapshot_history.append({
            "id": snap_id,
            "timestamp": current_time,
            "metadata": metadata
        })
        
        # Keep history bounded
        if len(self.snapshot_history) > 100:
            self.snapshot_history = self.snapshot_history[-50:]
        
        return snap_id
    
    def restore(self, snap_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Restore from checkpoint.
        
        Args:
            snap_id: Specific snapshot ID or None for latest
        
        Returns:
            Restored state or None
        """
        if snap_id:
            snapshot = load_snapshot(snap_id)
            if snapshot:
                return snapshot.state
        else:
            return restore_last()
        
        return None
    
    def rollback_to_safe_state(self, validator_fn=None) -> Optional[Dict[str, Any]]:
        """
        Rollback to the most recent safe state.
        
        Args:
            validator_fn: Optional function to validate state safety
        
        Returns:
            Safe state or None
        """
        for snap_info in list_snapshots(limit=20):
            snapshot = load_snapshot(snap_info["id"])
            
            if not snapshot:
                continue
            
            # Verify integrity
            if not snapshot.verify():
                continue
            
            # Apply custom validation if provided
            if validator_fn:
                if validator_fn(snapshot.state):
                    return snapshot.state
            else:
                # Basic validation: check for required keys
                required = ["metrics", "config"]
                if all(k in snapshot.state for k in required):
                    return snapshot.state
        
        return None
    
    def diff_snapshots(self, snap_id1: str, snap_id2: str) -> Dict[str, Any]:
        """
        Compare two snapshots.
        
        Args:
            snap_id1: First snapshot ID
            snap_id2: Second snapshot ID
        
        Returns:
            Difference summary
        """
        snap1 = load_snapshot(snap_id1)
        snap2 = load_snapshot(snap_id2)
        
        if not snap1 or not snap2:
            return {"error": "One or both snapshots not found"}
        
        def dict_diff(d1: dict, d2: dict, path: str = "") -> dict:
            diff = {
                "added": {},
                "removed": {},
                "changed": {}
            }
            
            # Find added/changed
            for key in d2:
                full_path = f"{path}.{key}" if path else key
                if key not in d1:
                    diff["added"][full_path] = d2[key]
                elif d1[key] != d2[key]:
                    if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                        sub_diff = dict_diff(d1[key], d2[key], full_path)
                        diff["added"].update(sub_diff["added"])
                        diff["removed"].update(sub_diff["removed"])
                        diff["changed"].update(sub_diff["changed"])
                    else:
                        diff["changed"][full_path] = {
                            "old": d1[key],
                            "new": d2[key]
                        }
            
            # Find removed
            for key in d1:
                if key not in d2:
                    full_path = f"{path}.{key}" if path else key
                    diff["removed"][full_path] = d1[key]
            
            return diff
        
        return {
            "snap1": snap_id1,
            "snap2": snap_id2,
            "time_diff": snap2.timestamp - snap1.timestamp,
            "diff": dict_diff(snap1.state, snap2.state)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get checkpoint statistics"""
        snapshots = list_snapshots(limit=100)
        
        total_size = sum(
            (SNAP / f"{s['id']}.json").stat().st_size
            for s in snapshots
            if (SNAP / f"{s['id']}.json").exists()
        )
        
        return {
            "total_snapshots": len(snapshots),
            "total_size_mb": total_size / (1024 * 1024),
            "oldest": snapshots[-1]["timestamp"] if snapshots else None,
            "newest": snapshots[0]["timestamp"] if snapshots else None,
            "auto_interval": self.auto_snapshot_interval,
            "last_checkpoint": self.last_snapshot_time
        }