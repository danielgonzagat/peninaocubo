"""
Neural Blockchain - Lightweight Distributed Ledger
==================================================

Implements lightweight neural blockchain on top of WORM ledger.
Provides cognitive block validation and consensus mechanisms.
"""

import hmac
import hashlib
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class BlockStatus(Enum):
    """Block validation status"""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"
    CONFLICT = "conflict"


@dataclass
class NeuralBlock:
    """Block in the neural blockchain"""
    block_id: str
    timestamp: float
    prev_hash: str
    state_snapshot: Dict[str, Any]
    cognitive_signature: str
    validator_nodes: List[str] = field(default_factory=list)
    consensus_score: float = 0.0
    status: BlockStatus = BlockStatus.PENDING
    block_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "state_snapshot": self.state_snapshot,
            "cognitive_signature": self.cognitive_signature,
            "validator_nodes": self.validator_nodes,
            "consensus_score": self.consensus_score,
            "status": self.status.value,
            "block_hash": self.block_hash
        }


class NeuralBlockchain:
    """Neural blockchain implementation"""
    
    def __init__(self, root_dir: str = None, chain_key: str = None):
        if root_dir is None:
            root_dir = os.getenv("PENIN_ROOT", str(Path.home() / ".penin_omega"))
        
        self.root_dir = Path(root_dir)
        self.ledger_dir = self.root_dir / "worm_ledger"
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        
        self.chain_file = self.ledger_dir / "neural_chain.jsonl"
        self.chain_key = chain_key or os.getenv("PENIN_CHAIN_KEY", "dev-key")
        self.chain_key_bytes = self.chain_key.encode()
        
        # Blockchain state
        self.blocks: List[NeuralBlock] = []
        self.validator_nodes: List[str] = []
        self.consensus_threshold = 0.67  # 67% consensus required
        
        # Load existing chain
        self._load_chain()
    
    def _load_chain(self):
        """Load existing blockchain from file"""
        if not self.chain_file.exists():
            return
        
        try:
            with open(self.chain_file, 'r') as f:
                for line in f:
                    if line.strip():
                        block_data = json.loads(line)
                        block = NeuralBlock(
                            block_id=block_data["block_id"],
                            timestamp=block_data["timestamp"],
                            prev_hash=block_data["prev_hash"],
                            state_snapshot=block_data["state_snapshot"],
                            cognitive_signature=block_data["cognitive_signature"],
                            validator_nodes=block_data.get("validator_nodes", []),
                            consensus_score=block_data.get("consensus_score", 0.0),
                            status=BlockStatus(block_data.get("status", "pending")),
                            block_hash=block_data.get("block_hash", "")
                        )
                        self.blocks.append(block)
        except Exception as e:
            print(f"Error loading neural chain: {e}")
    
    def _hash_block(self, block: NeuralBlock) -> str:
        """Compute HMAC-SHA256 hash for block"""
        # Create deterministic representation
        block_data = {
            "block_id": block.block_id,
            "timestamp": block.timestamp,
            "prev_hash": block.prev_hash,
            "state_snapshot": block.state_snapshot,
            "cognitive_signature": block.cognitive_signature,
            "validator_nodes": sorted(block.validator_nodes)
        }
        
        # Serialize with sorted keys for consistency
        raw_data = json.dumps(block_data, sort_keys=True, separators=(',', ':'))
        
        # Compute HMAC-SHA256
        mac = hmac.new(self.chain_key_bytes, raw_data.encode(), hashlib.sha256)
        return mac.hexdigest()
    
    def add_block(self, state_snapshot: Dict[str, Any], 
                  prev_hash: str = None,
                  cognitive_signature: str = None) -> Tuple[str, bool]:
        """
        Add new block to neural blockchain
        
        Args:
            state_snapshot: Current system state
            prev_hash: Hash of previous block (None for genesis)
            cognitive_signature: Cognitive validation signature
            
        Returns:
            (block_hash, success)
        """
        # Determine previous hash
        if prev_hash is None:
            prev_hash = self.get_latest_hash() or "GENESIS"
        
        # Generate cognitive signature if not provided
        if cognitive_signature is None:
            cognitive_signature = self._generate_cognitive_signature(state_snapshot)
        
        # Create block
        block_id = f"block_{int(time.time())}_{len(self.blocks)}"
        block = NeuralBlock(
            block_id=block_id,
            timestamp=time.time(),
            prev_hash=prev_hash,
            state_snapshot=state_snapshot,
            cognitive_signature=cognitive_signature
        )
        
        # Compute block hash
        block.block_hash = self._hash_block(block)
        
        # Validate block
        if self._validate_block(block):
            # Add to chain
            self.blocks.append(block)
            
            # Persist to file
            self._persist_block(block)
            
            return block.block_hash, True
        else:
            return "", False
    
    def _generate_cognitive_signature(self, state_snapshot: Dict[str, Any]) -> str:
        """Generate cognitive signature for state snapshot"""
        # Extract key cognitive metrics
        cognitive_metrics = {
            "phi": state_snapshot.get("phi", 0.0),
            "sr": state_snapshot.get("sr", 0.0),
            "G": state_snapshot.get("G", 0.0),
            "alpha_eff": state_snapshot.get("alpha_eff", 0.0),
            "life_ok": state_snapshot.get("life_ok", False)
        }
        
        # Create signature from cognitive state
        signature_data = json.dumps(cognitive_metrics, sort_keys=True)
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()
        
        return signature_hash[:16]  # Short signature
    
    def _validate_block(self, block: NeuralBlock) -> bool:
        """Validate block before adding to chain"""
        # Check hash integrity
        computed_hash = self._hash_block(block)
        if computed_hash != block.block_hash:
            return False
        
        # Check previous hash consistency
        if block.prev_hash != "GENESIS":
            latest_hash = self.get_latest_hash()
            if block.prev_hash != latest_hash:
                return False
        
        # Check cognitive signature validity
        expected_signature = self._generate_cognitive_signature(block.state_snapshot)
        if block.cognitive_signature != expected_signature:
            return False
        
        # Check timestamp (not too far in future)
        if block.timestamp > time.time() + 60:  # 1 minute tolerance
            return False
        
        return True
    
    def _persist_block(self, block: NeuralBlock):
        """Persist block to file"""
        try:
            with open(self.chain_file, 'a') as f:
                f.write(json.dumps(block.to_dict()) + '\n')
        except Exception as e:
            print(f"Error persisting block: {e}")
    
    def get_latest_hash(self) -> Optional[str]:
        """Get hash of latest block"""
        if not self.blocks:
            return None
        return self.blocks[-1].block_hash
    
    def get_latest_block(self) -> Optional[NeuralBlock]:
        """Get latest block"""
        if not self.blocks:
            return None
        return self.blocks[-1]
    
    def get_block_by_hash(self, block_hash: str) -> Optional[NeuralBlock]:
        """Get block by hash"""
        for block in self.blocks:
            if block.block_hash == block_hash:
                return block
        return None
    
    def validate_chain(self) -> Tuple[bool, List[str]]:
        """Validate entire blockchain"""
        issues = []
        
        for i, block in enumerate(self.blocks):
            # Check hash integrity
            computed_hash = self._hash_block(block)
            if computed_hash != block.block_hash:
                issues.append(f"Block {i} hash mismatch")
            
            # Check previous hash (except genesis)
            if i > 0:
                prev_block = self.blocks[i-1]
                if block.prev_hash != prev_block.block_hash:
                    issues.append(f"Block {i} prev_hash mismatch")
        
        return len(issues) == 0, issues
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        if not self.blocks:
            return {"blocks": 0, "valid": True, "length": 0}
        
        valid_blocks = sum(1 for b in self.blocks if b.status == BlockStatus.VALID)
        
        return {
            "blocks": len(self.blocks),
            "valid_blocks": valid_blocks,
            "invalid_blocks": len(self.blocks) - valid_blocks,
            "valid": valid_blocks == len(self.blocks),
            "length": len(self.blocks),
            "latest_hash": self.get_latest_hash(),
            "genesis_time": self.blocks[0].timestamp if self.blocks else None,
            "latest_time": self.blocks[-1].timestamp if self.blocks else None
        }
    
    def get_state_history(self, key: str, window_blocks: int = 10) -> List[Tuple[float, Any]]:
        """Get history of specific state key"""
        history = []
        
        recent_blocks = self.blocks[-window_blocks:] if window_blocks > 0 else self.blocks
        
        for block in recent_blocks:
            if key in block.state_snapshot:
                history.append((block.timestamp, block.state_snapshot[key]))
        
        return history
    
    def add_validator_node(self, node_id: str):
        """Add validator node to consensus"""
        if node_id not in self.validator_nodes:
            self.validator_nodes.append(node_id)
    
    def remove_validator_node(self, node_id: str):
        """Remove validator node from consensus"""
        if node_id in self.validator_nodes:
            self.validator_nodes.remove(node_id)
    
    def get_consensus_status(self) -> Dict[str, Any]:
        """Get consensus status"""
        return {
            "validator_nodes": self.validator_nodes,
            "consensus_threshold": self.consensus_threshold,
            "active_validators": len(self.validator_nodes)
        }


# Integration with WORM ledger
def integrate_neural_chain_with_worm(
    worm_ledger_path: str,
    state_snapshot: Dict[str, Any]
) -> Tuple[str, bool]:
    """
    Integrate neural chain with existing WORM ledger
    
    Args:
        worm_ledger_path: Path to WORM ledger
        state_snapshot: Current system state
        
    Returns:
        (block_hash, success)
    """
    # Create neural blockchain
    chain = NeuralBlockchain()
    
    # Add current state as block
    block_hash, success = chain.add_block(state_snapshot)
    
    if success:
        # Log integration in WORM
        worm_entry = {
            "timestamp": time.time(),
            "event_type": "NEURAL_CHAIN_BLOCK",
            "block_hash": block_hash,
            "state_keys": list(state_snapshot.keys()),
            "chain_length": len(chain.blocks)
        }
        
        try:
            with open(worm_ledger_path, 'a') as f:
                f.write(json.dumps(worm_entry) + '\n')
        except Exception as e:
            print(f"Error logging to WORM: {e}")
    
    return block_hash, success


# Integration with Life Equation
def integrate_neural_chain_in_life_equation(
    life_verdict: Dict[str, Any],
    chain: NeuralBlockchain = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Integrate neural chain into Life Equation evaluation
    
    Args:
        life_verdict: Result from life_equation()
        chain: Neural blockchain instance
        
    Returns:
        (block_hash, chain_details)
    """
    if chain is None:
        chain = NeuralBlockchain()
    
    # Create state snapshot from life verdict
    state_snapshot = {
        "life_ok": life_verdict.get("ok", False),
        "alpha_eff": life_verdict.get("alpha_eff", 0.0),
        "phi": life_verdict.get("metrics", {}).get("phi", 0.0),
        "sr": life_verdict.get("metrics", {}).get("sr", 0.0),
        "G": life_verdict.get("metrics", {}).get("G", 0.0),
        "timestamp": life_verdict.get("timestamp", time.time())
    }
    
    # Add block to chain
    block_hash, success = chain.add_block(state_snapshot)
    
    chain_details = {
        "block_hash": block_hash,
        "success": success,
        "chain_stats": chain.get_chain_stats(),
        "consensus_status": chain.get_consensus_status()
    }
    
    return block_hash, chain_details


# Example usage
if __name__ == "__main__":
    # Create neural blockchain
    chain = NeuralBlockchain()
    
    # Add some blocks
    state1 = {"phi": 0.7, "sr": 0.8, "G": 0.9, "life_ok": True}
    hash1, success1 = chain.add_block(state1)
    print(f"Block 1: {hash1[:16]}... (success: {success1})")
    
    state2 = {"phi": 0.8, "sr": 0.85, "G": 0.92, "life_ok": True}
    hash2, success2 = chain.add_block(state2)
    print(f"Block 2: {hash2[:16]}... (success: {success2})")
    
    # Validate chain
    valid, issues = chain.validate_chain()
    print(f"Chain valid: {valid}")
    if issues:
        print(f"Issues: {issues}")
    
    # Get stats
    stats = chain.get_chain_stats()
    print(f"Chain stats: {stats}")
    
    # Get state history
    phi_history = chain.get_state_history("phi", 5)
    print(f"Phi history: {phi_history}")