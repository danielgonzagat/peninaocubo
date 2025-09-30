"""
Checkpoint & Repair System
==========================

Implements system snapshots and rollback mechanisms.
Provides save/restore functionality for system state.
"""

import os
import time
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import orjson


class CheckpointStatus(Enum):
    """Checkpoint status"""
    CREATED = "created"
    VERIFIED = "verified"
    CORRUPTED = "corrupted"
    RESTORED = "restored"
    FAILED = "failed"


@dataclass
class Checkpoint:
    """System checkpoint"""
    id: str
    timestamp: float
    version: str
    description: str
    status: CheckpointStatus
    file_path: Path
    checksum: str
    size_bytes: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "version": self.version,
            "description": self.description,
            "status": self.status.value,
            "file_path": str(self.file_path),
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata
        }


class CheckpointManager:
    """Manages system checkpoints"""
    
    def __init__(self, checkpoint_dir: Optional[Path] = None):
        if checkpoint_dir is None:
            checkpoint_dir = Path.home() / ".penin_omega" / "checkpoints"
        
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Load checkpoint registry
        self.registry_file = self.checkpoint_dir / "registry.json"
        self.checkpoints: Dict[str, Checkpoint] = {}
        self._load_registry()
        
        # Maximum number of checkpoints to keep
        self.max_checkpoints = 10
    
    def _load_registry(self) -> None:
        """Load checkpoint registry from disk"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                
                for checkpoint_data in data.get("checkpoints", []):
                    checkpoint = Checkpoint(
                        id=checkpoint_data["id"],
                        timestamp=checkpoint_data["timestamp"],
                        version=checkpoint_data["version"],
                        description=checkpoint_data["description"],
                        status=CheckpointStatus(checkpoint_data["status"]),
                        file_path=Path(checkpoint_data["file_path"]),
                        checksum=checkpoint_data["checksum"],
                        size_bytes=checkpoint_data["size_bytes"],
                        metadata=checkpoint_data.get("metadata", {})
                    )
                    self.checkpoints[checkpoint.id] = checkpoint
                    
            except Exception as e:
                print(f"Warning: Failed to load checkpoint registry: {e}")
                self.checkpoints = {}
    
    def _save_registry(self) -> None:
        """Save checkpoint registry to disk"""
        try:
            data = {
                "checkpoints": [cp.to_dict() for cp in self.checkpoints.values()],
                "last_updated": time.time()
            }
            
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error: Failed to save checkpoint registry: {e}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ""
    
    def _cleanup_old_checkpoints(self) -> None:
        """Remove old checkpoints to maintain max_checkpoints limit"""
        if len(self.checkpoints) <= self.max_checkpoints:
            return
        
        # Sort by timestamp (oldest first)
        sorted_checkpoints = sorted(
            self.checkpoints.values(),
            key=lambda cp: cp.timestamp
        )
        
        # Remove oldest checkpoints
        to_remove = sorted_checkpoints[:-self.max_checkpoints]
        for checkpoint in to_remove:
            self._remove_checkpoint(checkpoint.id)
    
    def _remove_checkpoint(self, checkpoint_id: str) -> None:
        """Remove checkpoint from registry and disk"""
        if checkpoint_id in self.checkpoints:
            checkpoint = self.checkpoints[checkpoint_id]
            
            # Remove file if it exists
            if checkpoint.file_path.exists():
                try:
                    checkpoint.file_path.unlink()
                except Exception as e:
                    print(f"Warning: Failed to remove checkpoint file {checkpoint.file_path}: {e}")
            
            # Remove from registry
            del self.checkpoints[checkpoint_id]
    
    def create_checkpoint(self, state: Dict[str, Any], description: str = "", 
                         version: str = "1.0") -> Optional[str]:
        """
        Create a new checkpoint
        
        Args:
            state: System state to save
            description: Description of checkpoint
            version: Version identifier
            
        Returns:
            Checkpoint ID if successful, None otherwise
        """
        try:
            # Generate checkpoint ID
            checkpoint_id = f"cp_{int(time.time())}_{hash(str(state)) % 10000:04d}"
            
            # Create checkpoint file
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
            
            # Save state to file
            with open(checkpoint_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            # Calculate checksum
            checksum = self._calculate_checksum(checkpoint_file)
            size_bytes = checkpoint_file.stat().st_size
            
            # Create checkpoint object
            checkpoint = Checkpoint(
                id=checkpoint_id,
                timestamp=time.time(),
                version=version,
                description=description,
                status=CheckpointStatus.CREATED,
                file_path=checkpoint_file,
                checksum=checksum,
                size_bytes=size_bytes,
                metadata={
                    "created_by": "checkpoint_manager",
                    "state_keys": list(state.keys()) if isinstance(state, dict) else []
                }
            )
            
            # Add to registry
            self.checkpoints[checkpoint_id] = checkpoint
            
            # Save registry
            self._save_registry()
            
            # Cleanup old checkpoints
            self._cleanup_old_checkpoints()
            
            return checkpoint_id
            
        except Exception as e:
            print(f"Error: Failed to create checkpoint: {e}")
            return None
    
    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore system state from checkpoint
        
        Args:
            checkpoint_id: ID of checkpoint to restore
            
        Returns:
            Restored state if successful, None otherwise
        """
        if checkpoint_id not in self.checkpoints:
            print(f"Error: Checkpoint {checkpoint_id} not found")
            return None
        
        checkpoint = self.checkpoints[checkpoint_id]
        
        try:
            # Verify file exists
            if not checkpoint.file_path.exists():
                print(f"Error: Checkpoint file {checkpoint.file_path} not found")
                checkpoint.status = CheckpointStatus.CORRUPTED
                self._save_registry()
                return None
            
            # Verify checksum
            current_checksum = self._calculate_checksum(checkpoint.file_path)
            if current_checksum != checkpoint.checksum:
                print(f"Error: Checkpoint {checkpoint_id} checksum mismatch")
                checkpoint.status = CheckpointStatus.CORRUPTED
                self._save_registry()
                return None
            
            # Load state
            with open(checkpoint.file_path, 'r') as f:
                state = json.load(f)
            
            # Update status
            checkpoint.status = CheckpointStatus.RESTORED
            self._save_registry()
            
            return state
            
        except Exception as e:
            print(f"Error: Failed to restore checkpoint {checkpoint_id}: {e}")
            checkpoint.status = CheckpointStatus.FAILED
            self._save_registry()
            return None
    
    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """Get the most recent checkpoint"""
        if not self.checkpoints:
            return None
        
        return max(self.checkpoints.values(), key=lambda cp: cp.timestamp)
    
    def get_checkpoint_list(self) -> List[Checkpoint]:
        """Get list of all checkpoints sorted by timestamp (newest first)"""
        return sorted(
            self.checkpoints.values(),
            key=lambda cp: cp.timestamp,
            reverse=True
        )
    
    def verify_checkpoint(self, checkpoint_id: str) -> bool:
        """Verify checkpoint integrity"""
        if checkpoint_id not in self.checkpoints:
            return False
        
        checkpoint = self.checkpoints[checkpoint_id]
        
        try:
            # Check file exists
            if not checkpoint.file_path.exists():
                checkpoint.status = CheckpointStatus.CORRUPTED
                self._save_registry()
                return False
            
            # Verify checksum
            current_checksum = self._calculate_checksum(checkpoint.file_path)
            if current_checksum != checkpoint.checksum:
                checkpoint.status = CheckpointStatus.CORRUPTED
                self._save_registry()
                return False
            
            # Try to load JSON
            with open(checkpoint.file_path, 'r') as f:
                json.load(f)
            
            checkpoint.status = CheckpointStatus.VERIFIED
            self._save_registry()
            return True
            
        except Exception:
            checkpoint.status = CheckpointStatus.CORRUPTED
            self._save_registry()
            return False
    
    def repair_checkpoint(self, checkpoint_id: str) -> bool:
        """Attempt to repair corrupted checkpoint"""
        if checkpoint_id not in self.checkpoints:
            return False
        
        checkpoint = self.checkpoints[checkpoint_id]
        
        try:
            # Try to restore from backup if available
            backup_file = checkpoint.file_path.with_suffix('.json.bak')
            if backup_file.exists():
                shutil.copy2(backup_file, checkpoint.file_path)
                
                # Verify repair
                if self.verify_checkpoint(checkpoint_id):
                    return True
            
            # If no backup, try to recreate from registry metadata
            # This is a last resort and may not work for all cases
            print(f"Warning: Cannot repair checkpoint {checkpoint_id} - no backup available")
            return False
            
        except Exception as e:
            print(f"Error: Failed to repair checkpoint {checkpoint_id}: {e}")
            return False
    
    def get_checkpoint_stats(self) -> Dict[str, Any]:
        """Get checkpoint system statistics"""
        total_checkpoints = len(self.checkpoints)
        status_counts = {}
        
        for checkpoint in self.checkpoints.values():
            status = checkpoint.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total_size = sum(cp.size_bytes for cp in self.checkpoints.values())
        
        return {
            "total_checkpoints": total_checkpoints,
            "status_distribution": status_counts,
            "total_size_bytes": total_size,
            "checkpoint_dir": str(self.checkpoint_dir),
            "max_checkpoints": self.max_checkpoints,
            "latest_checkpoint": self.get_latest_checkpoint().id if self.get_latest_checkpoint() else None
        }


# Global checkpoint manager instance
_global_checkpoint_manager: Optional[CheckpointManager] = None


def get_global_checkpoint_manager() -> CheckpointManager:
    """Get global checkpoint manager instance"""
    global _global_checkpoint_manager
    
    if _global_checkpoint_manager is None:
        _global_checkpoint_manager = CheckpointManager()
    
    return _global_checkpoint_manager


def save_snapshot(state: Dict[str, Any], description: str = "") -> Optional[str]:
    """Convenience function to save system snapshot"""
    manager = get_global_checkpoint_manager()
    return manager.create_checkpoint(state, description)


def restore_last() -> Optional[Dict[str, Any]]:
    """Convenience function to restore last checkpoint"""
    manager = get_global_checkpoint_manager()
    latest = manager.get_latest_checkpoint()
    
    if latest is None:
        return None
    
    return manager.restore_checkpoint(latest.id)


def test_checkpoint_system() -> Dict[str, Any]:
    """Test checkpoint system functionality"""
    manager = get_global_checkpoint_manager()
    
    # Test state
    test_state = {
        "alpha_eff": 0.02,
        "phi": 0.7,
        "sr": 0.85,
        "G": 0.9,
        "metrics": {
            "latency": 0.1,
            "memory": 0.5,
            "cpu": 0.3
        },
        "timestamp": time.time()
    }
    
    # Create checkpoint
    checkpoint_id = manager.create_checkpoint(test_state, "Test checkpoint")
    
    if checkpoint_id is None:
        return {"error": "Failed to create checkpoint"}
    
    # Verify checkpoint
    verify_result = manager.verify_checkpoint(checkpoint_id)
    
    # Restore checkpoint
    restored_state = manager.restore_checkpoint(checkpoint_id)
    
    # Get stats
    stats = manager.get_checkpoint_stats()
    
    return {
        "checkpoint_id": checkpoint_id,
        "verify_result": verify_result,
        "restore_success": restored_state is not None,
        "state_match": restored_state == test_state if restored_state else False,
        "stats": stats
    }