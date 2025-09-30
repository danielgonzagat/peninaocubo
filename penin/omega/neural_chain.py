"""
Neural Blockchain - Lightweight Chain on WORM
==============================================

Implements lightweight blockchain for cognitive states using HMAC.
Single-node PoC with future multi-node consensus support.
"""

import hmac
import hashlib
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    import orjson
    def dumps(obj): return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)
    def loads(data): return orjson.loads(data)
except ImportError:
    import json
    def dumps(obj): return json.dumps(obj, sort_keys=True).encode()
    def loads(data): return json.loads(data)


KEY = (os.getenv("PENIN_CHAIN_KEY") or "dev-key").encode()
ROOT = Path.home() / ".penin_omega" / "worm_ledger"
ROOT.mkdir(parents=True, exist_ok=True)
CHAIN = ROOT / "neural_chain.jsonl"


@dataclass
class Block:
    """Neural blockchain block"""
    index: int
    timestamp: float
    prev_hash: str
    state_snapshot: Dict[str, Any]
    nonce: int = 0
    hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def compute_hash(self) -> str:
        """Compute HMAC hash of block"""
        block_dict = self.to_dict()
        block_dict.pop("hash", None)  # Remove hash field for computation
        raw = dumps(block_dict)
        return hmac.new(KEY, raw, hashlib.sha256).hexdigest()


def _hash_block(b: Dict[str, Any]) -> str:
    """Hash a block dictionary"""
    # Remove hash field if present
    b_copy = b.copy()
    b_copy.pop("hash", None)
    raw = dumps(b_copy)
    return hmac.new(KEY, raw, hashlib.sha256).hexdigest()


def add_block(state_snapshot: Dict[str, Any], prev_hash: Optional[str] = None) -> str:
    """
    Add a new block to the chain.
    
    Args:
        state_snapshot: Current state to record
        prev_hash: Hash of previous block (or None for genesis)
    
    Returns:
        Hash of the new block
    """
    # Get last block if prev_hash not provided
    if prev_hash is None:
        prev_hash = get_last_hash() or "GENESIS"
    
    # Get next index
    chain = load_chain()
    next_index = len(chain)
    
    # Create block
    block = Block(
        index=next_index,
        timestamp=time.time(),
        prev_hash=prev_hash,
        state_snapshot=state_snapshot
    )
    
    # Compute hash
    block.hash = block.compute_hash()
    
    # Append to chain file
    with CHAIN.open("ab") as f:
        f.write(dumps(block.to_dict()) + b"\n")
    
    return block.hash


def load_chain() -> List[Block]:
    """Load the entire chain from file"""
    if not CHAIN.exists():
        return []
    
    blocks = []
    with CHAIN.open("rb") as f:
        for line in f:
            if line.strip():
                block_dict = loads(line)
                blocks.append(Block(**block_dict))
    
    return blocks


def get_last_hash() -> Optional[str]:
    """Get hash of the last block"""
    chain = load_chain()
    if not chain:
        return None
    return chain[-1].hash


def verify_chain() -> Tuple[bool, Optional[str]]:
    """
    Verify the integrity of the entire chain.
    
    Returns:
        (is_valid, error_message)
    """
    chain = load_chain()
    
    if not chain:
        return True, None
    
    # Verify genesis block
    if chain[0].prev_hash not in ["GENESIS", ""]:
        return False, "Invalid genesis block"
    
    # Verify each block
    for i, block in enumerate(chain):
        # Verify hash
        computed_hash = block.compute_hash()
        if block.hash != computed_hash:
            return False, f"Invalid hash at block {i}"
        
        # Verify link to previous block
        if i > 0:
            if block.prev_hash != chain[i-1].hash:
                return False, f"Invalid chain link at block {i}"
    
    return True, None


def get_block_by_hash(block_hash: str) -> Optional[Block]:
    """Find a block by its hash"""
    chain = load_chain()
    for block in chain:
        if block.hash == block_hash:
            return block
    return None


def get_blocks_since(timestamp: float) -> List[Block]:
    """Get all blocks since a given timestamp"""
    chain = load_chain()
    return [b for b in chain if b.timestamp >= timestamp]


class NeuralLedger:
    """
    High-level interface for neural blockchain.
    Manages state snapshots and provides query capabilities.
    """
    
    def __init__(self):
        self.last_hash = get_last_hash()
        
    def record_state(self, state: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """
        Record a state snapshot in the chain.
        
        Args:
            state: State dictionary to record
            metadata: Optional metadata
        
        Returns:
            Block hash
        """
        snapshot = {
            "state": state,
            "metadata": metadata or {},
            "recorded_at": time.time()
        }
        
        self.last_hash = add_block(snapshot, self.last_hash)
        return self.last_hash
    
    def record_decision(
        self,
        decision_type: str,
        decision: Any,
        reasons: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> str:
        """
        Record a decision in the chain.
        
        Args:
            decision_type: Type of decision (promote/rollback/explore)
            decision: The decision value
            reasons: Reasoning behind decision
            metrics: Associated metrics
        
        Returns:
            Block hash
        """
        snapshot = {
            "type": "decision",
            "decision_type": decision_type,
            "decision": decision,
            "reasons": reasons,
            "metrics": metrics
        }
        
        return self.record_state(snapshot)
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent history"""
        chain = load_chain()
        recent = chain[-limit:] if len(chain) > limit else chain
        
        return [
            {
                "index": b.index,
                "timestamp": b.timestamp,
                "hash": b.hash,
                "snapshot": b.state_snapshot
            }
            for b in recent
        ]
    
    def verify(self) -> bool:
        """Verify chain integrity"""
        valid, error = verify_chain()
        if not valid:
            print(f"Chain verification failed: {error}")
        return valid
    
    def get_state_at(self, block_hash: str) -> Optional[Dict[str, Any]]:
        """Get state at a specific block"""
        block = get_block_by_hash(block_hash)
        if block:
            return block.state_snapshot
        return None
    
    def rollback_to(self, block_hash: str) -> bool:
        """
        Rollback to a specific block (by creating a new block with old state).
        
        Args:
            block_hash: Hash of block to rollback to
        
        Returns:
            True if successful
        """
        block = get_block_by_hash(block_hash)
        if not block:
            return False
        
        # Create rollback block
        rollback_snapshot = {
            "type": "rollback",
            "rollback_to": block_hash,
            "rollback_index": block.index,
            "restored_state": block.state_snapshot
        }
        
        self.record_state(rollback_snapshot, {"rollback": True})
        return True


def create_genesis_block() -> str:
    """Create the genesis block if chain is empty"""
    if not CHAIN.exists() or CHAIN.stat().st_size == 0:
        genesis_state = {
            "type": "genesis",
            "created_at": time.time(),
            "version": "1.0",
            "chain_id": hashlib.sha256(KEY).hexdigest()[:16]
        }
        return add_block(genesis_state, "GENESIS")
    return get_last_hash()


class ConsensusManager:
    """
    Future: Manages consensus among multiple nodes.
    Currently single-node placeholder.
    """
    
    def __init__(self, node_id: str = None):
        self.node_id = node_id or f"node-{os.getpid()}"
        self.validators: List[str] = [self.node_id]
        
    def propose_block(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a new block for consensus"""
        # Single node: auto-approve
        proposal = {
            "proposer": self.node_id,
            "state": state,
            "validators": self.validators,
            "signatures": {self.node_id: self._sign(state)}
        }
        return proposal
    
    def _sign(self, data: Dict[str, Any]) -> str:
        """Sign data with node key"""
        raw = dumps(data)
        node_key = (self.node_id + str(KEY)).encode()
        return hmac.new(node_key, raw, hashlib.sha256).hexdigest()
    
    def validate_proposal(self, proposal: Dict[str, Any]) -> bool:
        """Validate a block proposal"""
        # Single node: always valid if from self
        return proposal["proposer"] == self.node_id
    
    def finalize_block(self, proposal: Dict[str, Any]) -> str:
        """Finalize a validated proposal into a block"""
        if self.validate_proposal(proposal):
            return add_block(proposal["state"])
        raise ValueError("Invalid proposal")


# Initialize genesis block on module load
if not CHAIN.exists() or CHAIN.stat().st_size == 0:
    create_genesis_block()