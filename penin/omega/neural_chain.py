"""
Neural Blockchain - Lightweight blockchain on top of WORM
Implements cognitive state chaining with HMAC-SHA256
"""

import hmac
import hashlib
import time
import orjson
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


# Chain key from environment or default
KEY = (os.getenv("PENIN_CHAIN_KEY") or "dev-key").encode()

# Root directory for chain storage
ROOT = Path(os.getenv("PENIN_ROOT", Path.home() / ".penin_omega")) / "worm_ledger"
ROOT.mkdir(parents=True, exist_ok=True)
CHAIN = ROOT / "neural_chain.jsonl"


def _hash_block(block: dict) -> str:
    """
    Compute HMAC-SHA256 hash of a block
    
    Parameters:
    -----------
    block: Block dictionary to hash
    
    Returns:
    --------
    Hex string of the hash
    """
    # Serialize with sorted keys for consistency
    raw = orjson.dumps(block, option=orjson.OPT_SORT_KEYS)
    return hmac.new(KEY, raw, hashlib.sha256).hexdigest()


def add_block(
    state_snapshot: dict,
    prev_hash: Optional[str] = None,
    metadata: Optional[dict] = None
) -> str:
    """
    Add a new block to the neural chain
    
    Parameters:
    -----------
    state_snapshot: Current state to record
    prev_hash: Hash of previous block (None for genesis)
    metadata: Additional metadata to include
    
    Returns:
    --------
    Hash of the newly added block
    """
    # Get previous hash if not provided
    if prev_hash is None:
        prev_hash = get_latest_hash() or "GENESIS"
    
    # Construct block
    block = {
        "index": get_chain_length(),
        "ts": time.time(),
        "prev": prev_hash,
        "state": state_snapshot,
    }
    
    if metadata:
        block["metadata"] = metadata
    
    # Compute hash
    block["hash"] = _hash_block(block)
    
    # Append to chain
    with CHAIN.open("ab") as f:
        f.write(orjson.dumps(block) + b"\n")
    
    return block["hash"]


def get_latest_hash() -> Optional[str]:
    """
    Get hash of the latest block in the chain
    
    Returns:
    --------
    Hash string or None if chain is empty
    """
    if not CHAIN.exists():
        return None
    
    try:
        # Read last line
        with CHAIN.open("rb") as f:
            # Seek to end and read backwards to find last line
            f.seek(0, 2)  # End of file
            file_size = f.tell()
            
            if file_size == 0:
                return None
            
            # Read last 1KB (should contain last line)
            read_size = min(1024, file_size)
            f.seek(file_size - read_size)
            data = f.read(read_size)
            
            # Find last newline
            lines = data.split(b"\n")
            last_line = lines[-2] if len(lines) > 1 and lines[-1] == b"" else lines[-1]
            
            if last_line:
                block = orjson.loads(last_line)
                return block.get("hash")
    except Exception:
        pass
    
    return None


def get_chain_length() -> int:
    """
    Get the current length of the chain
    
    Returns:
    --------
    Number of blocks in the chain
    """
    if not CHAIN.exists():
        return 0
    
    count = 0
    with CHAIN.open("rb") as f:
        for _ in f:
            count += 1
    
    return count


def verify_chain(verbose: bool = False) -> bool:
    """
    Verify the integrity of the entire chain
    
    Parameters:
    -----------
    verbose: If True, print verification details
    
    Returns:
    --------
    True if chain is valid, False otherwise
    """
    if not CHAIN.exists():
        if verbose:
            print("Chain does not exist")
        return True  # Empty chain is valid
    
    prev_hash = "GENESIS"
    
    with CHAIN.open("rb") as f:
        for i, line in enumerate(f):
            try:
                block = orjson.loads(line)
                
                # Check previous hash linkage
                if block.get("prev") != prev_hash:
                    if verbose:
                        print(f"Block {i}: Previous hash mismatch")
                        print(f"  Expected: {prev_hash}")
                        print(f"  Got: {block.get('prev')}")
                    return False
                
                # Verify block hash
                stored_hash = block.get("hash")
                block_copy = dict(block)
                del block_copy["hash"]
                computed_hash = _hash_block(block_copy)
                
                if stored_hash != computed_hash:
                    if verbose:
                        print(f"Block {i}: Hash mismatch")
                        print(f"  Stored: {stored_hash}")
                        print(f"  Computed: {computed_hash}")
                    return False
                
                prev_hash = stored_hash
                
            except Exception as e:
                if verbose:
                    print(f"Block {i}: Error - {e}")
                return False
    
    if verbose:
        print(f"Chain verified: {i + 1} blocks OK")
    
    return True


def get_block(index: int) -> Optional[dict]:
    """
    Get a specific block by index
    
    Parameters:
    -----------
    index: Block index (0-based)
    
    Returns:
    --------
    Block dictionary or None if not found
    """
    if not CHAIN.exists():
        return None
    
    with CHAIN.open("rb") as f:
        for i, line in enumerate(f):
            if i == index:
                return orjson.loads(line)
    
    return None


def get_blocks_since(timestamp: float) -> List[dict]:
    """
    Get all blocks since a given timestamp
    
    Parameters:
    -----------
    timestamp: Unix timestamp
    
    Returns:
    --------
    List of blocks added after the timestamp
    """
    if not CHAIN.exists():
        return []
    
    blocks = []
    with CHAIN.open("rb") as f:
        for line in f:
            block = orjson.loads(line)
            if block.get("ts", 0) > timestamp:
                blocks.append(block)
    
    return blocks


def compute_chain_merkle_root() -> Optional[str]:
    """
    Compute Merkle root of all block hashes
    
    Returns:
    --------
    Merkle root hash or None if chain is empty
    """
    if not CHAIN.exists():
        return None
    
    # Collect all block hashes
    hashes = []
    with CHAIN.open("rb") as f:
        for line in f:
            block = orjson.loads(line)
            hashes.append(block.get("hash", ""))
    
    if not hashes:
        return None
    
    # Build Merkle tree
    while len(hashes) > 1:
        next_level = []
        for i in range(0, len(hashes), 2):
            left = hashes[i]
            right = hashes[i + 1] if i + 1 < len(hashes) else left
            combined = (left + right).encode()
            parent = hashlib.sha256(combined).hexdigest()
            next_level.append(parent)
        hashes = next_level
    
    return hashes[0]


def fork_detection() -> List[int]:
    """
    Detect potential forks in the chain
    
    Returns:
    --------
    List of block indices where forks might exist
    """
    if not CHAIN.exists():
        return []
    
    forks = []
    seen_hashes = set()
    
    with CHAIN.open("rb") as f:
        for i, line in enumerate(f):
            block = orjson.loads(line)
            block_hash = block.get("hash")
            
            if block_hash in seen_hashes:
                forks.append(i)
            else:
                seen_hashes.add(block_hash)
    
    return forks


def quick_test():
    """Quick test of neural blockchain"""
    # Add some blocks
    blocks_added = []
    
    # Genesis block
    h1 = add_block(
        {"epoch": 0, "loss": 1.0, "accuracy": 0.1},
        metadata={"type": "genesis"}
    )
    blocks_added.append(h1)
    
    # Evolution blocks
    h2 = add_block(
        {"epoch": 1, "loss": 0.8, "accuracy": 0.3},
        prev_hash=h1,
        metadata={"type": "training"}
    )
    blocks_added.append(h2)
    
    h3 = add_block(
        {"epoch": 2, "loss": 0.6, "accuracy": 0.5},
        prev_hash=h2,
        metadata={"type": "training"}
    )
    blocks_added.append(h3)
    
    # Verify chain
    valid = verify_chain(verbose=False)
    
    # Get chain info
    length = get_chain_length()
    latest = get_latest_hash()
    merkle = compute_chain_merkle_root()
    
    return {
        "blocks_added": len(blocks_added),
        "chain_length": length,
        "chain_valid": valid,
        "latest_hash": latest[:8] + "..." if latest else None,
        "merkle_root": merkle[:8] + "..." if merkle else None
    }


if __name__ == "__main__":
    result = quick_test()
    print("Neural Blockchain Test:")
    print(f"  Blocks added: {result['blocks_added']}")
    print(f"  Chain length: {result['chain_length']}")
    print(f"  Chain valid: {result['chain_valid']}")
    print(f"  Latest hash: {result['latest_hash']}")
    print(f"  Merkle root: {result['merkle_root']}")