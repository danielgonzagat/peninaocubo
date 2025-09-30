"""
Neural Blockchain - Lightweight Distributed Ledger
==================================================

Implements lightweight neural blockchain on top of WORM ledger.
Uses HMAC-SHA256 for block integrity with chained hashes.
"""

import hmac
import hashlib
import time
import orjson
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class BlockStatus(Enum):
    """Block status"""
    GENESIS = "genesis"
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"


@dataclass
class NeuralBlock:
    """Neural blockchain block"""
    block_id: str
    timestamp: float
    prev_hash: str
    state_snapshot: Dict[str, Any]
    block_hash: str = ""
    status: BlockStatus = BlockStatus.PENDING
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "state_snapshot": self.state_snapshot,
            "block_hash": self.block_hash,
            "status": self.status.value,
            "created_at": self.created_at
        }


class NeuralChain:
    """Neural blockchain implementation"""
    
    def __init__(self, chain_path: str, hmac_key: Optional[str] = None):
        self.chain_path = Path(chain_path)
        self.chain_path.parent.mkdir(parents=True, exist_ok=True)
        
        # HMAC key for block integrity
        self.hmac_key = (hmac_key or os.getenv("PENIN_CHAIN_KEY", "dev-key")).encode()
        
        # Block storage
        self.blocks: List[NeuralBlock] = []
        self.block_index: Dict[str, NeuralBlock] = {}
        
        # Load existing chain
        self._load_chain()
    
    def _load_chain(self) -> None:
        """Load existing blockchain from file"""
        if not self.chain_path.exists():
            return
        
        try:
            with open(self.chain_path, 'rb') as f:
                for line in f:
                    if line.strip():
                        block_data = orjson.loads(line)
                        block = NeuralBlock(
                            block_id=block_data["block_id"],
                            timestamp=block_data["timestamp"],
                            prev_hash=block_data["prev_hash"],
                            state_snapshot=block_data["state_snapshot"],
                            block_hash=block_data.get("block_hash", ""),
                            status=BlockStatus(block_data.get("status", "pending")),
                            created_at=block_data.get("created_at", time.time())
                        )
                        self.blocks.append(block)
                        self.block_index[block.block_id] = block
        except Exception as e:
            print(f"Warning: Failed to load chain: {e}")
    
    def _save_block(self, block: NeuralBlock) -> None:
        """Save block to file"""
        with open(self.chain_path, 'ab') as f:
            f.write(orjson.dumps(block.to_dict()) + b'\n')
    
    def _hash_block(self, block_data: Dict[str, Any]) -> str:
        """Compute HMAC hash for block"""
        # Sort keys for deterministic hashing
        sorted_data = orjson.dumps(block_data, option=orjson.OPT_SORT_KEYS)
        return hmac.new(self.hmac_key, sorted_data, hashlib.sha256).hexdigest()
    
    def _validate_block(self, block: NeuralBlock) -> bool:
        """Validate block integrity"""
        # Check hash
        block_data = {
            "block_id": block.block_id,
            "timestamp": block.timestamp,
            "prev_hash": block.prev_hash,
            "state_snapshot": block.state_snapshot
        }
        
        expected_hash = self._hash_block(block_data)
        if block.block_hash != expected_hash:
            return False
        
        # Check previous block hash (if not genesis)
        if block.prev_hash != "GENESIS":
            if block.prev_hash not in [b.block_hash for b in self.blocks]:
                return False
        
        return True
    
    def add_block(self, state_snapshot: Dict[str, Any], block_id: Optional[str] = None) -> NeuralBlock:
        """
        Add new block to chain
        
        Args:
            state_snapshot: State data to store
            block_id: Optional block ID (auto-generated if None)
            
        Returns:
            Created block
        """
        # Generate block ID
        if block_id is None:
            block_id = f"block_{int(time.time())}_{len(self.blocks)}"
        
        # Get previous hash
        prev_hash = "GENESIS" if not self.blocks else self.blocks[-1].block_hash
        
        # Create block
        block = NeuralBlock(
            block_id=block_id,
            timestamp=time.time(),
            prev_hash=prev_hash,
            state_snapshot=state_snapshot
        )
        
        # Compute hash
        block_data = {
            "block_id": block.block_id,
            "timestamp": block.timestamp,
            "prev_hash": block.prev_hash,
            "state_snapshot": block.state_snapshot
        }
        
        block.block_hash = self._hash_block(block_data)
        
        # Validate block
        if self._validate_block(block):
            block.status = BlockStatus.VALID
        else:
            block.status = BlockStatus.INVALID
        
        # Add to chain
        self.blocks.append(block)
        self.block_index[block.block_id] = block
        
        # Save to file
        self._save_block(block)
        
        return block
    
    def get_block(self, block_id: str) -> Optional[NeuralBlock]:
        """Get block by ID"""
        return self.block_index.get(block_id)
    
    def get_latest_block(self) -> Optional[NeuralBlock]:
        """Get latest block"""
        return self.blocks[-1] if self.blocks else None
    
    def get_chain_length(self) -> int:
        """Get chain length"""
        return len(self.blocks)
    
    def validate_chain(self) -> Tuple[bool, List[str]]:
        """Validate entire chain"""
        issues = []
        
        for i, block in enumerate(self.blocks):
            if not self._validate_block(block):
                issues.append(f"Block {block.block_id} failed validation")
            
            # Check previous hash
            if i > 0:
                if block.prev_hash != self.blocks[i-1].block_hash:
                    issues.append(f"Block {block.block_id} has incorrect prev_hash")
        
        return len(issues) == 0, issues
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get chain statistics"""
        if not self.blocks:
            return {"length": 0, "valid_blocks": 0, "invalid_blocks": 0}
        
        valid_count = sum(1 for b in self.blocks if b.status == BlockStatus.VALID)
        invalid_count = sum(1 for b in self.blocks if b.status == BlockStatus.INVALID)
        
        return {
            "length": len(self.blocks),
            "valid_blocks": valid_count,
            "invalid_blocks": invalid_count,
            "latest_block_id": self.blocks[-1].block_id if self.blocks else None,
            "latest_block_hash": self.blocks[-1].block_hash if self.blocks else None,
            "chain_valid": len(self.validate_chain()[1]) == 0
        }
    
    def export_chain(self, filepath: str) -> None:
        """Export chain to file"""
        chain_data = {
            "exported_at": time.time(),
            "chain_length": len(self.blocks),
            "blocks": [block.to_dict() for block in self.blocks],
            "stats": self.get_chain_stats()
        }
        
        with open(filepath, 'w') as f:
            orjson.dump(chain_data, f, option=orjson.OPT_INDENT_2)
    
    def search_blocks(self, query: Dict[str, Any]) -> List[NeuralBlock]:
        """Search blocks by state snapshot criteria"""
        matching_blocks = []
        
        for block in self.blocks:
            match = True
            for key, value in query.items():
                if key not in block.state_snapshot:
                    match = False
                    break
                if block.state_snapshot[key] != value:
                    match = False
                    break
            
            if match:
                matching_blocks.append(block)
        
        return matching_blocks


class NeuralChainManager:
    """Manages neural blockchain operations"""
    
    def __init__(self, chain_path: Optional[str] = None):
        if chain_path is None:
            root_path = Path.home() / ".penin_omega" / "worm_ledger"
            root_path.mkdir(parents=True, exist_ok=True)
            chain_path = str(root_path / "neural_chain.jsonl")
        
        self.chain = NeuralChain(chain_path)
        self.block_counter = 0
    
    def add_state_snapshot(self, state: Dict[str, Any]) -> NeuralBlock:
        """Add state snapshot to chain"""
        block_id = f"snapshot_{int(time.time())}_{self.block_counter}"
        self.block_counter += 1
        
        return self.chain.add_block(state, block_id)
    
    def add_cycle_result(self, cycle_data: Dict[str, Any]) -> NeuralBlock:
        """Add evolution cycle result to chain"""
        state_snapshot = {
            "type": "evolution_cycle",
            "cycle_id": cycle_data.get("cycle_id", "unknown"),
            "timestamp": time.time(),
            "decision": cycle_data.get("decision", "unknown"),
            "metrics": cycle_data.get("metrics", {}),
            "evidence_hash": cycle_data.get("evidence_hash", ""),
            **cycle_data
        }
        
        return self.add_state_snapshot(state_snapshot)
    
    def add_life_equation_result(self, verdict: Dict[str, Any]) -> NeuralBlock:
        """Add Life Equation verdict to chain"""
        state_snapshot = {
            "type": "life_equation",
            "timestamp": time.time(),
            "verdict": verdict,
            "alpha_eff": verdict.get("alpha_eff", 0.0),
            "ok": verdict.get("ok", False)
        }
        
        return self.add_state_snapshot(state_snapshot)
    
    def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """Get latest state snapshot"""
        latest_block = self.chain.get_latest_block()
        return latest_block.state_snapshot if latest_block else None
    
    def get_chain_integrity(self) -> Tuple[bool, List[str]]:
        """Check chain integrity"""
        return self.chain.validate_chain()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chain statistics"""
        return self.chain.get_chain_stats()
    
    def search_by_type(self, block_type: str) -> List[NeuralBlock]:
        """Search blocks by type"""
        return self.chain.search_blocks({"type": block_type})
    
    def export_chain(self, filepath: str) -> None:
        """Export chain"""
        self.chain.export_chain(filepath)


# Global chain instance
_global_chain: Optional[NeuralChainManager] = None


def get_global_chain() -> NeuralChainManager:
    """Get global neural chain instance"""
    global _global_chain
    
    if _global_chain is None:
        _global_chain = NeuralChainManager()
    
    return _global_chain


def add_block(state_snapshot: Dict[str, Any], prev_hash: Optional[str] = None) -> str:
    """Convenience function to add block"""
    chain = get_global_chain()
    block = chain.add_state_snapshot(state_snapshot)
    return block.block_hash


def test_neural_chain() -> Dict[str, Any]:
    """Test neural chain functionality"""
    chain = get_global_chain()
    
    # Add some test blocks
    block1 = chain.add_state_snapshot({
        "type": "test",
        "data": "block1",
        "value": 42
    })
    
    block2 = chain.add_state_snapshot({
        "type": "test",
        "data": "block2",
        "value": 84
    })
    
    # Add cycle result
    cycle_result = chain.add_cycle_result({
        "cycle_id": "test_cycle_001",
        "decision": "promote",
        "metrics": {"score": 0.85, "cost": 0.02}
    })
    
    # Get stats
    stats = chain.get_stats()
    
    # Validate chain
    is_valid, issues = chain.get_chain_integrity()
    
    # Search blocks
    test_blocks = chain.search_by_type("test")
    
    return {
        "blocks_created": 3,
        "block_hashes": [block1.block_hash, block2.block_hash, cycle_result.block_hash],
        "chain_stats": stats,
        "chain_valid": is_valid,
        "validation_issues": issues,
        "test_blocks_found": len(test_blocks)
    }