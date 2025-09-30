"""
Checkpoint & Repair - State Snapshotting
========================================

Enables system rollback by saving/restoring state snapshots.
"""

from pathlib import Path
import time
from typing import Dict, Any, Optional

try:
    import orjson as json_lib
except ImportError:
    import json as json_lib


SNAP = Path.home() / ".penin_omega" / "snapshots"
SNAP.mkdir(parents=True, exist_ok=True)


def save_snapshot(state: Dict[str, Any]) -> str:
    """
    Save a state snapshot.
    
    Args:
        state: State to save
        
    Returns:
        Path to snapshot file
    """
    filename = f"snap_{int(time.time())}.json"
    path = SNAP / filename
    
    if hasattr(json_lib, 'dumps'):
        data = json_lib.dumps(state)
    else:
        import json
        data = json.dumps(state).encode()
    
    path.write_bytes(data)
    
    print(f"💾 Saved snapshot: {filename}")
    return str(path)


def restore_last() -> Optional[Dict[str, Any]]:
    """
    Restore the most recent snapshot.
    
    Returns:
        State dict or None if no snapshots
    """
    snaps = sorted(SNAP.glob("snap_*.json"))
    
    if not snaps:
        return None
    
    latest = snaps[-1]
    
    if hasattr(json_lib, 'loads'):
        state = json_lib.loads(latest.read_bytes())
    else:
        import json
        state = json.loads(latest.read_text())
    
    print(f"📥 Restored snapshot: {latest.name}")
    return state


def list_snapshots() -> list:
    """List all available snapshots"""
    return sorted(SNAP.glob("snap_*.json"))


class CheckpointManager:
    """
    Manages system checkpoints.
    
    Automatically saves before risky operations.
    """
    
    def __init__(self):
        self.last_snapshot: Optional[str] = None
        print("💾 Checkpoint Manager initialized")
    
    def save(self, state: Dict[str, Any]) -> str:
        """Save checkpoint"""
        path = save_snapshot(state)
        self.last_snapshot = path
        return path
    
    def restore(self) -> Optional[Dict[str, Any]]:
        """Restore last checkpoint"""
        return restore_last()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get checkpoint statistics"""
        snaps = list_snapshots()
        return {
            "total_snapshots": len(snaps),
            "last_snapshot": self.last_snapshot,
            "oldest": snaps[0].name if snaps else None,
            "newest": snaps[-1].name if snaps else None
        }


# Quick test
def quick_checkpoint_test():
    """Quick test of checkpoint system"""
    mgr = CheckpointManager()
    
    # Save checkpoint
    state = {"phi": 0.7, "sr": 0.85, "cycle": 42}
    mgr.save(state)
    
    # Restore
    restored = mgr.restore()
    print(f"\n📥 Restored: {restored}")
    
    stats = mgr.get_stats()
    print(f"\n📊 Stats: {stats}")
    
    return mgr