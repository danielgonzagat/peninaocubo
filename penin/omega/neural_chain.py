"""
Neural Blockchain (Lightweight) - Cognitive State Chain
======================================================

Implements a lightweight blockchain over the existing WORM ledger:
- Each block contains a state snapshot
- Blocks are chained via HMAC-SHA256
- Single-node PoC (extensible to multi-node consensus)

This provides additional integrity guarantees beyond WORM append-only.
"""

import hmac
import hashlib
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import orjson as json_lib
except ImportError:
    import json as json_lib


# Configuration
KEY = (os.getenv("PENIN_CHAIN_KEY") or "dev-key").encode()
ROOT = Path.home() / ".penin_omega" / "worm_ledger"
ROOT.mkdir(parents=True, exist_ok=True)
CHAIN = ROOT / "neural_chain.jsonl"


def _hash_block(block: Dict[str, Any]) -> str:
    """
    Compute HMAC-SHA256 hash of a block.
    
    Args:
        block: Block dictionary
        
    Returns:
        Hex digest of hash
    """
    if hasattr(json_lib, 'dumps'):
        raw = json_lib.dumps(block, option=json_lib.OPT_SORT_KEYS) if 'orjson' in str(type(json_lib)) else json_lib.dumps(block, sort_keys=True).encode()
    else:
        import json
        raw = json.dumps(block, sort_keys=True).encode()
    
    return hmac.new(KEY, raw, hashlib.sha256).hexdigest()


def add_block(state_snapshot: Dict[str, Any], prev_hash: Optional[str] = None) -> str:
    """
    Add a new block to the chain.
    
    Args:
        state_snapshot: Current state to record
        prev_hash: Hash of previous block (None for genesis)
        
    Returns:
        Hash of new block
    """
    block = {
        "ts": time.time(),
        "prev": prev_hash or "GENESIS",
        "state": state_snapshot,
    }
    
    # Compute hash
    block["hash"] = _hash_block(block)
    
    # Append to chain
    if hasattr(json_lib, 'dumps'):
        block_bytes = json_lib.dumps(block) + b"\n" if 'orjson' in str(type(json_lib)) else (json_lib.dumps(block) + "\n").encode()
    else:
        import json
        block_bytes = (json.dumps(block) + "\n").encode()
    
    CHAIN.open("ab").write(block_bytes)
    
    return block["hash"]


def get_chain_head() -> Optional[Dict[str, Any]]:
    """
    Get the most recent block.
    
    Returns:
        Latest block or None if chain is empty
    """
    if not CHAIN.exists():
        return None
    
    last_line = None
    with CHAIN.open("rb") as f:
        for line in f:
            last_line = line
    
    if not last_line:
        return None
    
    if hasattr(json_lib, 'loads'):
        return json_lib.loads(last_line)
    else:
        import json
        return json.loads(last_line.decode())


def verify_chain() -> Dict[str, Any]:
    """
    Verify integrity of entire chain.
    
    Returns:
        Dict with verification results
    """
    if not CHAIN.exists():
        return {"valid": True, "blocks": 0, "reason": "Empty chain"}
    
    blocks = []
    with CHAIN.open("rb") as f:
        for line in f:
            if hasattr(json_lib, 'loads'):
                block = json_lib.loads(line)
            else:
                import json
                block = json.loads(line.decode())
            blocks.append(block)
    
    if not blocks:
        return {"valid": True, "blocks": 0, "reason": "Empty chain"}
    
    # Verify each block
    for i, block in enumerate(blocks):
        # Check prev hash linkage
        if i > 0:
            expected_prev = blocks[i-1]["hash"]
            if block["prev"] != expected_prev:
                return {
                    "valid": False,
                    "blocks": len(blocks),
                    "failed_at": i,
                    "reason": f"Broken chain at block {i}: prev={block['prev']} != expected={expected_prev}"
                }
        
        # Verify block hash
        recorded_hash = block["hash"]
        block_copy = dict(block)
        del block_copy["hash"]
        computed_hash = _hash_block(block_copy)
        
        if recorded_hash != computed_hash:
            return {
                "valid": False,
                "blocks": len(blocks),
                "failed_at": i,
                "reason": f"Invalid hash at block {i}"
            }
    
    return {
        "valid": True,
        "blocks": len(blocks),
        "head_hash": blocks[-1]["hash"] if blocks else None
    }


def get_chain_stats() -> Dict[str, Any]:
    """Get chain statistics"""
    verification = verify_chain()
    
    if not CHAIN.exists() or verification["blocks"] == 0:
        return {
            "blocks": 0,
            "valid": True,
            "size_bytes": 0
        }
    
    return {
        "blocks": verification["blocks"],
        "valid": verification["valid"],
        "head_hash": verification.get("head_hash"),
        "size_bytes": CHAIN.stat().st_size if CHAIN.exists() else 0
    }


class NeuralChainRecorder:
    """
    Records cognitive states to the neural blockchain.
    
    Integrates with evolution cycles to provide tamper-evident
    state history.
    """
    
    def __init__(self):
        self.last_hash: Optional[str] = None
        
        # Get current head
        head = get_chain_head()
        if head:
            self.last_hash = head["hash"]
            print(f"⛓️  Neural Chain initialized (head={self.last_hash[:16]}...)")
        else:
            print("⛓️  Neural Chain initialized (genesis)")
    
    def record_state(self, state: Dict[str, Any]) -> str:
        """
        Record a state snapshot.
        
        Args:
            state: State to record
            
        Returns:
            Hash of new block
        """
        block_hash = add_block(state, self.last_hash)
        self.last_hash = block_hash
        
        print(f"⛓️  Recorded block: {block_hash[:16]}...")
        
        return block_hash
    
    def verify(self) -> bool:
        """Verify chain integrity"""
        result = verify_chain()
        
        if result["valid"]:
            print(f"✅ Chain valid ({result['blocks']} blocks)")
        else:
            print(f"❌ Chain invalid: {result['reason']}")
        
        return result["valid"]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chain statistics"""
        return get_chain_stats()


# Quick test
def quick_chain_test():
    """Quick test of neural chain"""
    recorder = NeuralChainRecorder()
    
    # Record some blocks
    for i in range(5):
        state = {
            "cycle": i,
            "phi": 0.7 + i * 0.02,
            "sr": 0.85 + i * 0.01,
            "G": 0.90
        }
        recorder.record_state(state)
    
    # Verify
    recorder.verify()
    
    # Get stats
    stats = recorder.get_stats()
    print(f"\n📊 Chain stats: {stats}")
    
    return recorder