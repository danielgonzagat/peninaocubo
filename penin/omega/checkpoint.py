"""
Checkpoint & Repair - State snapshots and recovery system
Saves and restores system state for rollback capability
"""

from pathlib import Path
import time
import orjson
import hashlib
import shutil
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


# Snapshot directory
SNAP = Path.home() / ".penin_omega" / "snapshots"
SNAP.mkdir(parents=True, exist_ok=True)


@dataclass
class Checkpoint:
    """Checkpoint metadata"""
    id: str
    timestamp: float
    state_hash: str
    metrics: Dict[str, float]
    reason: str
    parent_id: Optional[str] = None


def save_snapshot(
    state: dict,
    reason: str = "manual",
    metrics: Optional[dict] = None
) -> str:
    """
    Save a state snapshot
    
    Parameters:
    -----------
    state: State dictionary to save
    reason: Reason for checkpoint (e.g., "pre-evolution", "anomaly", "manual")
    metrics: Optional metrics at checkpoint time
    
    Returns:
    --------
    Checkpoint ID (filename)
    """
    # Generate checkpoint ID
    timestamp = time.time()
    checkpoint_id = f"snap_{int(timestamp)}"
    
    # Compute state hash
    state_bytes = orjson.dumps(state, option=orjson.OPT_SORT_KEYS)
    state_hash = hashlib.sha256(state_bytes).hexdigest()
    
    # Create checkpoint metadata
    checkpoint = Checkpoint(
        id=checkpoint_id,
        timestamp=timestamp,
        state_hash=state_hash,
        metrics=metrics or {},
        reason=reason,
        parent_id=get_latest_checkpoint_id()
    )
    
    # Save state
    state_file = SNAP / f"{checkpoint_id}.json"
    state_file.write_bytes(state_bytes)
    
    # Save metadata
    meta_file = SNAP / f"{checkpoint_id}.meta.json"
    meta_file.write_bytes(orjson.dumps(asdict(checkpoint)))
    
    return checkpoint_id


def restore_snapshot(checkpoint_id: Optional[str] = None) -> Optional[dict]:
    """
    Restore a state snapshot
    
    Parameters:
    -----------
    checkpoint_id: Checkpoint to restore (None for latest)
    
    Returns:
    --------
    Restored state dictionary or None if not found
    """
    if checkpoint_id is None:
        checkpoint_id = get_latest_checkpoint_id()
        if checkpoint_id is None:
            return None
    
    state_file = SNAP / f"{checkpoint_id}.json"
    
    if not state_file.exists():
        return None
    
    try:
        return orjson.loads(state_file.read_bytes())
    except Exception:
        return None


def get_latest_checkpoint_id() -> Optional[str]:
    """
    Get the ID of the most recent checkpoint
    
    Returns:
    --------
    Checkpoint ID or None if no checkpoints exist
    """
    snapshots = sorted(SNAP.glob("snap_*.json"))
    
    if not snapshots:
        return None
    
    return snapshots[-1].stem


def list_checkpoints(limit: int = 10) -> List[Dict[str, Any]]:
    """
    List available checkpoints
    
    Parameters:
    -----------
    limit: Maximum number of checkpoints to return
    
    Returns:
    --------
    List of checkpoint metadata dictionaries
    """
    checkpoints = []
    
    meta_files = sorted(SNAP.glob("*.meta.json"), reverse=True)
    
    for meta_file in meta_files[:limit]:
        try:
            metadata = orjson.loads(meta_file.read_bytes())
            checkpoints.append(metadata)
        except Exception:
            continue
    
    return checkpoints


def verify_checkpoint(checkpoint_id: str) -> bool:
    """
    Verify integrity of a checkpoint
    
    Parameters:
    -----------
    checkpoint_id: Checkpoint to verify
    
    Returns:
    --------
    True if checkpoint is valid, False otherwise
    """
    state_file = SNAP / f"{checkpoint_id}.json"
    meta_file = SNAP / f"{checkpoint_id}.meta.json"
    
    if not state_file.exists() or not meta_file.exists():
        return False
    
    try:
        # Load metadata
        metadata = orjson.loads(meta_file.read_bytes())
        expected_hash = metadata.get("state_hash")
        
        if not expected_hash:
            return False
        
        # Compute actual hash
        state_bytes = state_file.read_bytes()
        actual_hash = hashlib.sha256(state_bytes).hexdigest()
        
        return expected_hash == actual_hash
        
    except Exception:
        return False


def auto_cleanup(days_to_keep: int = 7, keep_min: int = 5) -> int:
    """
    Automatically clean up old checkpoints
    
    Parameters:
    -----------
    days_to_keep: Keep checkpoints from last N days
    keep_min: Minimum number of checkpoints to keep regardless of age
    
    Returns:
    --------
    Number of checkpoints deleted
    """
    cutoff_time = time.time() - (days_to_keep * 24 * 3600)
    
    # Get all checkpoints sorted by age
    checkpoints = []
    for meta_file in SNAP.glob("*.meta.json"):
        try:
            metadata = orjson.loads(meta_file.read_bytes())
            checkpoints.append((metadata["timestamp"], metadata["id"]))
        except Exception:
            continue
    
    checkpoints.sort(reverse=True)  # Newest first
    
    # Keep minimum number
    if len(checkpoints) <= keep_min:
        return 0
    
    # Delete old checkpoints
    deleted = 0
    for timestamp, checkpoint_id in checkpoints[keep_min:]:
        if timestamp < cutoff_time:
            # Delete checkpoint files
            state_file = SNAP / f"{checkpoint_id}.json"
            meta_file = SNAP / f"{checkpoint_id}.meta.json"
            
            try:
                if state_file.exists():
                    state_file.unlink()
                if meta_file.exists():
                    meta_file.unlink()
                deleted += 1
            except Exception:
                continue
    
    return deleted


def create_backup(checkpoint_id: str, backup_path: Optional[Path] = None) -> bool:
    """
    Create a backup copy of a checkpoint
    
    Parameters:
    -----------
    checkpoint_id: Checkpoint to backup
    backup_path: Optional backup directory (default: snapshots/backups)
    
    Returns:
    --------
    True if backup successful, False otherwise
    """
    if backup_path is None:
        backup_path = SNAP / "backups"
    
    backup_path.mkdir(parents=True, exist_ok=True)
    
    state_file = SNAP / f"{checkpoint_id}.json"
    meta_file = SNAP / f"{checkpoint_id}.meta.json"
    
    if not state_file.exists() or not meta_file.exists():
        return False
    
    try:
        # Copy files to backup
        shutil.copy2(state_file, backup_path / state_file.name)
        shutil.copy2(meta_file, backup_path / meta_file.name)
        return True
    except Exception:
        return False


def diff_checkpoints(checkpoint_id1: str, checkpoint_id2: str) -> Dict[str, Any]:
    """
    Compare two checkpoints and return differences
    
    Parameters:
    -----------
    checkpoint_id1: First checkpoint
    checkpoint_id2: Second checkpoint
    
    Returns:
    --------
    Dictionary describing differences
    """
    state1 = restore_snapshot(checkpoint_id1)
    state2 = restore_snapshot(checkpoint_id2)
    
    if state1 is None or state2 is None:
        return {"error": "Could not load one or both checkpoints"}
    
    # Find differences
    keys1 = set(state1.keys())
    keys2 = set(state2.keys())
    
    added_keys = keys2 - keys1
    removed_keys = keys1 - keys2
    common_keys = keys1 & keys2
    
    changed_keys = []
    for key in common_keys:
        if state1[key] != state2[key]:
            changed_keys.append(key)
    
    return {
        "checkpoint1": checkpoint_id1,
        "checkpoint2": checkpoint_id2,
        "added_keys": list(added_keys),
        "removed_keys": list(removed_keys),
        "changed_keys": changed_keys,
        "total_changes": len(added_keys) + len(removed_keys) + len(changed_keys)
    }


def rollback_chain(target_checkpoint_id: str) -> List[str]:
    """
    Get the chain of checkpoints to rollback through
    
    Parameters:
    -----------
    target_checkpoint_id: Target checkpoint to rollback to
    
    Returns:
    --------
    List of checkpoint IDs from current to target
    """
    chain = []
    current_id = get_latest_checkpoint_id()
    
    if current_id is None or current_id == target_checkpoint_id:
        return []
    
    # Build parent chain
    visited = set()
    
    while current_id and current_id != target_checkpoint_id:
        if current_id in visited:
            break  # Avoid cycles
        
        chain.append(current_id)
        visited.add(current_id)
        
        # Get parent
        meta_file = SNAP / f"{current_id}.meta.json"
        if meta_file.exists():
            try:
                metadata = orjson.loads(meta_file.read_bytes())
                current_id = metadata.get("parent_id")
            except Exception:
                break
        else:
            break
    
    if current_id == target_checkpoint_id:
        chain.append(target_checkpoint_id)
        return chain
    
    return []  # Target not in chain


def quick_test():
    """Quick test of checkpoint system"""
    # Save some checkpoints
    state1 = {"epoch": 0, "loss": 1.0, "model": "v1"}
    cp1 = save_snapshot(state1, reason="initial", metrics={"accuracy": 0.1})
    
    time.sleep(0.1)  # Ensure different timestamp
    
    state2 = {"epoch": 1, "loss": 0.8, "model": "v1.1"}
    cp2 = save_snapshot(state2, reason="after_training", metrics={"accuracy": 0.3})
    
    time.sleep(0.1)
    
    state3 = {"epoch": 2, "loss": 0.6, "model": "v1.2"}
    cp3 = save_snapshot(state3, reason="improvement", metrics={"accuracy": 0.5})
    
    # Verify checkpoints
    valid1 = verify_checkpoint(cp1)
    valid3 = verify_checkpoint(cp3)
    
    # Restore latest
    restored = restore_snapshot()
    
    # List checkpoints
    checkpoint_list = list_checkpoints(limit=5)
    
    # Diff checkpoints
    diff = diff_checkpoints(cp1, cp3)
    
    # Rollback chain
    chain = rollback_chain(cp1)
    
    return {
        "checkpoints_saved": 3,
        "latest_id": cp3,
        "valid1": valid1,
        "valid3": valid3,
        "restored_epoch": restored.get("epoch") if restored else None,
        "checkpoints_listed": len(checkpoint_list),
        "total_changes": diff.get("total_changes", 0),
        "rollback_chain_length": len(chain)
    }


if __name__ == "__main__":
    result = quick_test()
    print("Checkpoint & Repair Test:")
    print(f"  Checkpoints saved: {result['checkpoints_saved']}")
    print(f"  Latest ID: {result['latest_id']}")
    print(f"  Validation: cp1={result['valid1']}, cp3={result['valid3']}")
    print(f"  Restored epoch: {result['restored_epoch']}")
    print(f"  Checkpoints listed: {result['checkpoints_listed']}")
    print(f"  Changes cp1→cp3: {result['total_changes']}")
    print(f"  Rollback chain length: {result['rollback_chain_length']}")