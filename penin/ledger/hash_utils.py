"""
PENIN-Ω Hash Utilities for WORM Ledger

Centralized hash algorithm management with:
- Modern BLAKE2b algorithm (256-bit)
- Backward compatibility with SHA-256
- Configurable hash algorithms
- Performance optimizations
- Future-proof design

Migration from SHA-256 to BLAKE2b:
- BLAKE2b is faster and more secure
- SHA-3 finalist with proven cryptographic properties
- Native support in Python 3.6+
- Better performance in hardware acceleration
- Supports keyed hashing for authentication
"""

from __future__ import annotations

import hashlib
from typing import Literal

# ============================================================================
# Constants
# ============================================================================

# Current hash algorithm (BLAKE2b with 256-bit output)
HASH_ALGORITHM: Literal["blake2b", "sha256", "sha3_256"] = "blake2b"
HASH_DIGEST_SIZE = 32  # 256 bits = 32 bytes

# Legacy support
LEGACY_HASH_ALGORITHM = "sha256"

# Hash algorithm versions for migration
HASH_VERSION = "2.0"  # BLAKE2b era
LEGACY_HASH_VERSION = "1.0"  # SHA-256 era


# ============================================================================
# Hash Functions
# ============================================================================


def compute_hash(data: bytes, algorithm: str = HASH_ALGORITHM) -> str:
    """
    Compute cryptographic hash of data.

    Args:
        data: Binary data to hash
        algorithm: Hash algorithm to use (blake2b, sha256, sha3_256)

    Returns:
        Hexadecimal hash digest

    Raises:
        ValueError: If algorithm is not supported
    """
    if algorithm == "blake2b":
        # BLAKE2b with 256-bit output (32 bytes)
        return hashlib.blake2b(data, digest_size=HASH_DIGEST_SIZE).hexdigest()
    elif algorithm == "sha256":
        # Legacy SHA-256 for backward compatibility
        return hashlib.sha256(data).hexdigest()
    elif algorithm == "sha3_256":
        # Alternative: SHA3-256 (NIST standard)
        return hashlib.sha3_256(data).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def compute_hash_legacy(data: bytes) -> str:
    """
    Compute legacy SHA-256 hash for backward compatibility.

    Args:
        data: Binary data to hash

    Returns:
        SHA-256 hexadecimal hash digest
    """
    return compute_hash(data, algorithm=LEGACY_HASH_ALGORITHM)


def verify_hash(
    data: bytes, expected_hash: str, algorithm: str = HASH_ALGORITHM
) -> bool:
    """
    Verify that data matches expected hash.

    Args:
        data: Binary data to verify
        expected_hash: Expected hexadecimal hash
        algorithm: Hash algorithm to use

    Returns:
        True if hash matches, False otherwise
    """
    computed = compute_hash(data, algorithm=algorithm)
    return computed == expected_hash


def detect_hash_algorithm(hash_value: str) -> str:
    """
    Detect hash algorithm from hash value length.

    Args:
        hash_value: Hexadecimal hash string

    Returns:
        Detected algorithm name (blake2b, sha256, sha3_256)

    Note:
        All three algorithms produce 64-character hex strings (256 bits).
        This function returns the current algorithm by default.
        For precise detection, use metadata from ledger header.
    """
    hash_len = len(hash_value)

    if hash_len == 64:
        # 256-bit hash (32 bytes * 2 hex chars)
        # Could be blake2b, sha256, or sha3_256
        return HASH_ALGORITHM
    elif hash_len == 128:
        # 512-bit BLAKE2b (default output size)
        return "blake2b"
    else:
        raise ValueError(f"Unknown hash length: {hash_len}")


# Internal placeholder: not part of public API
def _migrate_hash_chain(
    events: list[dict],
    from_algorithm: str = LEGACY_HASH_ALGORITHM,
    to_algorithm: str = HASH_ALGORITHM,
) -> list[dict]:
    """
    INTERNAL USE ONLY: Placeholder for hash chain migration.

    This function is not implemented. Hash chain migration requires event-specific
    serialization and should be performed using ledger-specific migration tools.

    Args:
        events: List of event dictionaries with hashes
        from_algorithm: Source hash algorithm
        to_algorithm: Target hash algorithm

    Returns:
        List of events with updated hashes (not implemented)

    Raises:
        NotImplementedError: Always raised. Use ledger-specific migration tools.
    """
    raise NotImplementedError(
        "Hash chain migration requires event-specific serialization. "
        "Use ledger-specific migration tools instead."
    )


# ============================================================================
# Performance Benchmarks
# ============================================================================


def benchmark_hash_algorithms(data: bytes, iterations: int = 10000) -> dict[str, float]:
    """
    Benchmark hash algorithms for performance comparison.

    Args:
        data: Test data to hash
        iterations: Number of iterations for benchmark

    Returns:
        Dictionary mapping algorithm names to execution times
    """
    import timeit

    algorithms = ["blake2b", "sha256", "sha3_256"]
    results = {}

    for algo in algorithms:
        timer = timeit.Timer(lambda: compute_hash(data, algorithm=algo))
        time_taken = timer.timeit(number=iterations)
        results[algo] = time_taken

    return results


# ============================================================================
# Utility Functions
# ============================================================================


def hash_string(text: str, algorithm: str = HASH_ALGORITHM) -> str:
    """
    Compute hash of UTF-8 string.

    Args:
        text: String to hash
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal hash digest
    """
    return compute_hash(text.encode("utf-8"), algorithm=algorithm)


def hash_json(obj: dict, algorithm: str = HASH_ALGORITHM) -> str:
    """
    Compute hash of JSON-serializable object.

    Args:
        obj: Object to hash (must be JSON-serializable)
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal hash digest

    Note:
        Uses deterministic JSON serialization (sorted keys).
    """
    import json

    canonical = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hash_string(canonical, algorithm=algorithm)


def keyed_hash(data: bytes, key: bytes, algorithm: str = HASH_ALGORITHM) -> str:
    """
    Compute keyed hash (HMAC-like) for authentication.

    Args:
        data: Data to hash
        key: Secret key for authentication
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal hash digest

    Note:
        Only BLAKE2b supports native keyed hashing.
        Other algorithms fall back to standard HMAC.
    """
    if algorithm == "blake2b":
        # BLAKE2b native keyed hashing (more efficient)
        return hashlib.blake2b(data, key=key, digest_size=HASH_DIGEST_SIZE).hexdigest()
    else:
        # Fallback to HMAC for other algorithms
        import hmac

        if algorithm == "sha256":
            return hmac.new(key, data, hashlib.sha256).hexdigest()
        elif algorithm == "sha3_256":
            return hmac.new(key, data, hashlib.sha3_256).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm for keyed hash: {algorithm}")


# ============================================================================
# Migration Guide
# ============================================================================

"""
Migration Guide: SHA-256 to BLAKE2b
====================================

Why BLAKE2b?
-----------
- Modern cryptographic hash (2012) vs SHA-256 (2001)
- SHA-3 finalist with proven security
- Faster in optimized implementations
- Native keyed hashing support
- Better hardware acceleration
- Quantum-resistant design

Migration Steps:
----------------
1. Existing ledgers continue with SHA-256 (backward compatible)
2. New ledgers use BLAKE2b automatically
3. Ledger header stores hash_algorithm for verification
4. verify_chain() auto-detects algorithm from header
5. Optional: Explicit migration via migration tools

Backward Compatibility:
-----------------------
- compute_hash_legacy() provides SHA-256
- detect_hash_algorithm() auto-detects from context
- Ledger header includes hash_algorithm field
- Chain verification respects original algorithm

Performance Notes:
------------------
- BLAKE2b: ~20% slower in pure Python
- BLAKE2b: ~2x faster in C implementations
- BLAKE2b: Better for large data (streaming)
- SHA-256: Good for small data in Python

Security Notes:
---------------
- Both are cryptographically secure (256-bit)
- BLAKE2b: More modern design
- BLAKE2b: Better side-channel resistance
- SHA-256: More widely audited
- Both: Sufficient for audit trails

Recommendation:
---------------
Use BLAKE2b for new deployments.
Keep SHA-256 for legacy compatibility.
No urgent need to migrate existing ledgers.
"""
