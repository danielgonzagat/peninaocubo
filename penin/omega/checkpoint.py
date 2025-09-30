"""
Checkpoint & Repair System
==========================

Implements checkpoint and repair mechanisms for saving and restoring
system snapshots with fail-closed protection.
"""

import os
import time
import json
import shutil
import hashlib
import orjson
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CheckpointType(Enum):
    """Types of checkpoints"""
    PRE_MUTATION = "pre_mutation"
    POST_MUTATION = "post_mutation"
    ROLLBACK_POINT = "rollback_point"
    SYSTEM_SNAPSHOT = "system_snapshot"
    EMERGENCY = "emergency"


@dataclass
class CheckpointMetadata:
    """Checkpoint metadata"""
    checkpoint_id: str
    timestamp: float
    checkpoint_type: CheckpointType
    description: str
    state_hash: str
    size_bytes: int
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RepairAction:
    """Repair action"""
    action_type: str
    target: str
    parameters: Dict[str, Any]
    timestamp: float
    success: bool
    error_message: Optional[str] = None


class CheckpointManager:
    """Checkpoint and repair manager"""
    
    def __init__(self, checkpoint_dir: Path = None):
        if checkpoint_dir is None:
            checkpoint_dir = Path.home() / ".penin_omega" / "snapshots"
        
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.metadata_dir = self.checkpoint_dir / "metadata"
        self.state_dir = self.checkpoint_dir / "state"
        self.repair_log = self.checkpoint_dir / "repair_log.jsonl"
        
        self.metadata_dir.mkdir(exist_ok=True)
        self.state_dir.mkdir(exist_ok=True)
        
        # In-memory cache
        self.checkpoint_cache: Dict[str, CheckpointMetadata] = {}
        self.repair_history: List[RepairAction] = []
        
        # Load existing checkpoints
        self._load_checkpoint_metadata()
    
    def _generate_checkpoint_id(self, checkpoint_type: CheckpointType) -> str:
        """Generate unique checkpoint ID"""
        timestamp = int(time.time() * 1000)  # milliseconds
        return f"{checkpoint_type.value}_{timestamp}"
    
    def _calculate_state_hash(self, state: Dict[str, Any]) -> str:
        """Calculate hash of state"""
        # Sort keys for consistent hashing
        state_str = orjson.dumps(state, option=orjson.OPT_SORT_KEYS)
        return hashlib.sha256(state_str).hexdigest()
    
    def _save_state_to_file(self, checkpoint_id: str, state: Dict[str, Any]) -> Path:
        """Save state to file"""
        state_file = self.state_dir / f"{checkpoint_id}.json"
        
        # Write with atomic operation
        temp_file = state_file.with_suffix('.tmp')
        temp_file.write_bytes(orjson.dumps(state, option=orjson.OPT_SORT_KEYS))
        temp_file.rename(state_file)
        
        return state_file
    
    def _load_state_from_file(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load state from file"""
        state_file = self.state_dir / f"{checkpoint_id}.json"
        
        if not state_file.exists():
            return None
        
        try:
            return orjson.loads(state_file.read_bytes())
        except (orjson.JSONDecodeError, FileNotFoundError):
            return None
    
    def _load_checkpoint_metadata(self):
        """Load checkpoint metadata from disk"""
        self.checkpoint_cache.clear()
        
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                metadata_data = orjson.loads(metadata_file.read_bytes())
                metadata = CheckpointMetadata(**metadata_data)
                self.checkpoint_cache[metadata.checkpoint_id] = metadata
            except (orjson.JSONDecodeError, TypeError):
                # Skip corrupted metadata files
                continue
    
    def _save_checkpoint_metadata(self, metadata: CheckpointMetadata):
        """Save checkpoint metadata to disk"""
        metadata_file = self.metadata_dir / f"{metadata.checkpoint_id}.json"
        
        # Write with atomic operation
        temp_file = metadata_file.with_suffix('.tmp')
        temp_file.write_bytes(orjson.dumps(metadata.__dict__, option=orjson.OPT_SORT_KEYS))
        temp_file.rename(metadata_file)
        
        # Update cache
        self.checkpoint_cache[metadata.checkpoint_id] = metadata
    
    def create_checkpoint(self, state: Dict[str, Any], 
                         checkpoint_type: CheckpointType,
                         description: str = "",
                         dependencies: List[str] = None,
                         tags: List[str] = None) -> str:
        """
        Create a checkpoint
        
        Args:
            state: System state to checkpoint
            checkpoint_type: Type of checkpoint
            description: Human-readable description
            dependencies: List of dependent checkpoint IDs
            tags: List of tags for organization
            
        Returns:
            Checkpoint ID
        """
        checkpoint_id = self._generate_checkpoint_id(checkpoint_type)
        
        # Calculate state hash
        state_hash = self._calculate_state_hash(state)
        
        # Save state to file
        state_file = self._save_state_to_file(checkpoint_id, state)
        size_bytes = state_file.stat().st_size
        
        # Create metadata
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            timestamp=time.time(),
            checkpoint_type=checkpoint_type,
            description=description,
            state_hash=state_hash,
            size_bytes=size_bytes,
            dependencies=dependencies or [],
            tags=tags or []
        )
        
        # Save metadata
        self._save_checkpoint_metadata(metadata)
        
        return checkpoint_id
    
    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore a checkpoint
        
        Args:
            checkpoint_id: ID of checkpoint to restore
            
        Returns:
            Restored state or None if failed
        """
        if checkpoint_id not in self.checkpoint_cache:
            return None
        
        metadata = self.checkpoint_cache[checkpoint_id]
        
        # Load state from file
        state = self._load_state_from_file(checkpoint_id)
        if state is None:
            return None
        
        # Verify state hash
        current_hash = self._calculate_state_hash(state)
        if current_hash != metadata.state_hash:
            # State corruption detected
            self._log_repair_action("hash_verification_failed", checkpoint_id, {
                "expected_hash": metadata.state_hash,
                "actual_hash": current_hash
            }, success=False, error_message="State hash mismatch")
            return None
        
        return state
    
    def list_checkpoints(self, checkpoint_type: CheckpointType = None,
                        tags: List[str] = None) -> List[CheckpointMetadata]:
        """
        List checkpoints
        
        Args:
            checkpoint_type: Filter by checkpoint type
            tags: Filter by tags
            
        Returns:
            List of checkpoint metadata
        """
        checkpoints = list(self.checkpoint_cache.values())
        
        if checkpoint_type:
            checkpoints = [c for c in checkpoints if c.checkpoint_type == checkpoint_type]
        
        if tags:
            checkpoints = [c for c in checkpoints if any(tag in c.tags for tag in tags)]
        
        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x.timestamp, reverse=True)
        
        return checkpoints
    
    def get_latest_checkpoint(self, checkpoint_type: CheckpointType = None) -> Optional[CheckpointMetadata]:
        """Get latest checkpoint of given type"""
        checkpoints = self.list_checkpoints(checkpoint_type)
        return checkpoints[0] if checkpoints else None
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint
        
        Args:
            checkpoint_id: ID of checkpoint to delete
            
        Returns:
            True if successful
        """
        if checkpoint_id not in self.checkpoint_cache:
            return False
        
        try:
            # Delete state file
            state_file = self.state_dir / f"{checkpoint_id}.json"
            if state_file.exists():
                state_file.unlink()
            
            # Delete metadata file
            metadata_file = self.metadata_dir / f"{checkpoint_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            # Remove from cache
            del self.checkpoint_cache[checkpoint_id]
            
            return True
        except OSError:
            return False
    
    def cleanup_old_checkpoints(self, max_age_hours: float = 24.0, 
                               max_count: int = 100) -> int:
        """
        Clean up old checkpoints
        
        Args:
            max_age_hours: Maximum age in hours
            max_count: Maximum number of checkpoints to keep
            
        Returns:
            Number of checkpoints deleted
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # Get all checkpoints sorted by timestamp
        all_checkpoints = self.list_checkpoints()
        
        # Keep only recent checkpoints
        recent_checkpoints = [c for c in all_checkpoints if c.timestamp >= cutoff_time]
        
        # If still too many, keep only the most recent
        if len(recent_checkpoints) > max_count:
            recent_checkpoints = recent_checkpoints[:max_count]
        
        # Delete old checkpoints
        deleted_count = 0
        for checkpoint in all_checkpoints:
            if checkpoint not in recent_checkpoints:
                if self.delete_checkpoint(checkpoint.checkpoint_id):
                    deleted_count += 1
        
        return deleted_count
    
    def _log_repair_action(self, action_type: str, target: str, 
                          parameters: Dict[str, Any], success: bool,
                          error_message: str = None):
        """Log repair action"""
        action = RepairAction(
            action_type=action_type,
            target=target,
            parameters=parameters,
            timestamp=time.time(),
            success=success,
            error_message=error_message
        )
        
        self.repair_history.append(action)
        
        # Write to log file
        log_entry = {
            "timestamp": action.timestamp,
            "action_type": action.action_type,
            "target": action.target,
            "parameters": action.parameters,
            "success": action.success,
            "error_message": action.error_message
        }
        
        with open(self.repair_log, "a") as f:
            f.write(orjson.dumps(log_entry).decode() + "\n")
    
    def repair_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Attempt to repair a corrupted checkpoint
        
        Args:
            checkpoint_id: ID of checkpoint to repair
            
        Returns:
            True if repair successful
        """
        if checkpoint_id not in self.checkpoint_cache:
            return False
        
        metadata = self.checkpoint_cache[checkpoint_id]
        
        # Try to restore state
        state = self._load_state_from_file(checkpoint_id)
        if state is None:
            # State file missing - try to find backup
            backup_files = list(self.state_dir.glob(f"{checkpoint_id}.*"))
            if backup_files:
                # Try to restore from backup
                for backup_file in backup_files:
                    try:
                        state = orjson.loads(backup_file.read_bytes())
                        # Restore original file
                        state_file = self.state_dir / f"{checkpoint_id}.json"
                        backup_file.rename(state_file)
                        
                        self._log_repair_action("restore_from_backup", checkpoint_id, {
                            "backup_file": str(backup_file)
                        }, success=True)
                        return True
                    except (orjson.JSONDecodeError, OSError):
                        continue
            
            self._log_repair_action("repair_failed", checkpoint_id, {}, 
                                   success=False, error_message="No valid backup found")
            return False
        
        # Verify and fix state hash if needed
        current_hash = self._calculate_state_hash(state)
        if current_hash != metadata.state_hash:
            # Update metadata with correct hash
            metadata.state_hash = current_hash
            self._save_checkpoint_metadata(metadata)
            
            self._log_repair_action("fix_hash", checkpoint_id, {
                "old_hash": metadata.state_hash,
                "new_hash": current_hash
            }, success=True)
        
        return True
    
    def get_repair_history(self) -> List[RepairAction]:
        """Get repair action history"""
        return self.repair_history.copy()
    
    def get_checkpoint_stats(self) -> Dict[str, Any]:
        """Get checkpoint statistics"""
        all_checkpoints = list(self.checkpoint_cache.values())
        
        if not all_checkpoints:
            return {
                "total_checkpoints": 0,
                "total_size_bytes": 0,
                "checkpoint_types": {},
                "oldest_checkpoint": None,
                "newest_checkpoint": None
            }
        
        # Count by type
        type_counts = {}
        for checkpoint in all_checkpoints:
            type_name = checkpoint.checkpoint_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Calculate total size
        total_size = sum(c.size_bytes for c in all_checkpoints)
        
        # Find oldest and newest
        timestamps = [c.timestamp for c in all_checkpoints]
        oldest_time = min(timestamps)
        newest_time = max(timestamps)
        
        oldest_checkpoint = next(c for c in all_checkpoints if c.timestamp == oldest_time)
        newest_checkpoint = next(c for c in all_checkpoints if c.timestamp == newest_time)
        
        return {
            "total_checkpoints": len(all_checkpoints),
            "total_size_bytes": total_size,
            "checkpoint_types": type_counts,
            "oldest_checkpoint": {
                "id": oldest_checkpoint.checkpoint_id,
                "timestamp": oldest_checkpoint.timestamp,
                "type": oldest_checkpoint.checkpoint_type.value
            },
            "newest_checkpoint": {
                "id": newest_checkpoint.checkpoint_id,
                "timestamp": newest_checkpoint.timestamp,
                "type": newest_checkpoint.checkpoint_type.value
            }
        }


# Integration functions
def create_pre_mutation_checkpoint(manager: CheckpointManager, 
                                 state: Dict[str, Any]) -> str:
    """Create pre-mutation checkpoint"""
    return manager.create_checkpoint(
        state=state,
        checkpoint_type=CheckpointType.PRE_MUTATION,
        description="State before mutation",
        tags=["mutation", "pre"]
    )


def create_post_mutation_checkpoint(manager: CheckpointManager, 
                                   state: Dict[str, Any]) -> str:
    """Create post-mutation checkpoint"""
    return manager.create_checkpoint(
        state=state,
        checkpoint_type=CheckpointType.POST_MUTATION,
        description="State after mutation",
        tags=["mutation", "post"]
    )


def create_rollback_point(manager: CheckpointManager, 
                         state: Dict[str, Any]) -> str:
    """Create rollback point"""
    return manager.create_checkpoint(
        state=state,
        checkpoint_type=CheckpointType.ROLLBACK_POINT,
        description="Rollback point",
        tags=["rollback", "safe"]
    )


def restore_last_safe_state(manager: CheckpointManager) -> Optional[Dict[str, Any]]:
    """Restore last safe state"""
    # Look for rollback points first
    rollback_checkpoint = manager.get_latest_checkpoint(CheckpointType.ROLLBACK_POINT)
    if rollback_checkpoint:
        return manager.restore_checkpoint(rollback_checkpoint.checkpoint_id)
    
    # Fall back to pre-mutation checkpoint
    pre_mutation_checkpoint = manager.get_latest_checkpoint(CheckpointType.PRE_MUTATION)
    if pre_mutation_checkpoint:
        return manager.restore_checkpoint(pre_mutation_checkpoint.checkpoint_id)
    
    return None


# Example usage
if __name__ == "__main__":
    # Create checkpoint manager
    manager = CheckpointManager()
    
    # Create test state
    test_state = {
        "alpha_eff": 0.5,
        "phi": 0.7,
        "sr": 0.8,
        "G": 0.9,
        "timestamp": time.time()
    }
    
    # Create checkpoint
    checkpoint_id = manager.create_checkpoint(
        state=test_state,
        checkpoint_type=CheckpointType.SYSTEM_SNAPSHOT,
        description="Test checkpoint",
        tags=["test", "example"]
    )
    
    print(f"Created checkpoint: {checkpoint_id}")
    
    # List checkpoints
    checkpoints = manager.list_checkpoints()
    print(f"Total checkpoints: {len(checkpoints)}")
    
    # Restore checkpoint
    restored_state = manager.restore_checkpoint(checkpoint_id)
    if restored_state:
        print(f"Restored state: {restored_state}")
    else:
        print("Failed to restore checkpoint")
    
    # Get stats
    stats = manager.get_checkpoint_stats()
    print(f"Checkpoint stats: {stats}")
    
    # Cleanup
    manager.delete_checkpoint(checkpoint_id)
    print("Checkpoint deleted")