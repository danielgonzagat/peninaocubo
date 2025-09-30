"""
API Metabolizer - I/O recorder and replayer for reducing API dependencies
Records API calls and can suggest cached responses for similar queries
"""

import orjson
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


# Log directory
LOG = Path.home() / ".penin_omega" / "knowledge" / "api_io.jsonl"
LOG.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class APICall:
    """Record of an API call"""
    timestamp: float
    provider: str
    endpoint: str
    request: dict
    response: dict
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    success: bool = True


def record_call(
    provider: str,
    endpoint: str,
    req: dict,
    resp: dict,
    latency_ms: float = 0.0,
    cost_usd: float = 0.0,
    success: bool = True
) -> None:
    """
    Record an API call for future replay
    
    Parameters:
    -----------
    provider: API provider name (e.g., "openai", "anthropic")
    endpoint: API endpoint (e.g., "chat/completions")
    req: Request payload
    resp: Response payload
    latency_ms: Call latency in milliseconds
    cost_usd: Call cost in USD
    success: Whether call succeeded
    """
    call = APICall(
        timestamp=time.time(),
        provider=provider,
        endpoint=endpoint,
        request=req,
        response=resp,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        success=success
    )
    
    with LOG.open("ab") as f:
        f.write(orjson.dumps(asdict(call)) + b"\n")


def suggest_replay(
    provider: str,
    endpoint: str,
    request: dict,
    similarity_threshold: float = 0.9
) -> Optional[dict]:
    """
    Suggest a cached response for a similar request
    
    Parameters:
    -----------
    provider: API provider name
    endpoint: API endpoint
    request: Current request to match
    similarity_threshold: Minimum similarity for replay
    
    Returns:
    --------
    Cached response if similar enough, None otherwise
    """
    if not LOG.exists():
        return None
    
    # Compute request signature
    current_sig = _compute_signature(request)
    
    best_match = None
    best_similarity = 0.0
    
    with LOG.open("rb") as f:
        for line in f:
            try:
                record = orjson.loads(line)
                
                # Check provider and endpoint match
                if record["provider"] != provider or record["endpoint"] != endpoint:
                    continue
                
                # Check if successful call
                if not record.get("success", True):
                    continue
                
                # Compute similarity
                similarity = _compute_similarity(request, record["request"])
                
                if similarity > best_similarity and similarity >= similarity_threshold:
                    best_similarity = similarity
                    best_match = record["response"]
                    
            except Exception:
                continue
    
    return best_match


def _compute_signature(obj: Any) -> str:
    """
    Compute a signature for an object
    
    Parameters:
    -----------
    obj: Object to compute signature for
    
    Returns:
    --------
    Hex string signature
    """
    # Serialize with sorted keys for consistency
    serialized = orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)
    return hashlib.sha256(serialized).hexdigest()


def _compute_similarity(req1: dict, req2: dict) -> float:
    """
    Compute similarity between two requests
    
    Parameters:
    -----------
    req1: First request
    req2: Second request
    
    Returns:
    --------
    Similarity score [0, 1]
    """
    # Simple approach: check key overlap and value similarity
    keys1 = set(req1.keys())
    keys2 = set(req2.keys())
    
    if not keys1 or not keys2:
        return 0.0
    
    # Key overlap
    key_overlap = len(keys1 & keys2) / len(keys1 | keys2)
    
    # Value similarity for common keys
    common_keys = keys1 & keys2
    if not common_keys:
        return key_overlap
    
    value_similarities = []
    for key in common_keys:
        v1 = req1[key]
        v2 = req2[key]
        
        if isinstance(v1, str) and isinstance(v2, str):
            # String similarity (simple length-based)
            if v1 == v2:
                value_similarities.append(1.0)
            else:
                max_len = max(len(v1), len(v2))
                if max_len > 0:
                    similarity = 1.0 - abs(len(v1) - len(v2)) / max_len
                    value_similarities.append(similarity)
                else:
                    value_similarities.append(0.0)
        elif v1 == v2:
            value_similarities.append(1.0)
        else:
            value_similarities.append(0.0)
    
    value_similarity = sum(value_similarities) / len(value_similarities) if value_similarities else 0.0
    
    # Weighted combination
    return 0.3 * key_overlap + 0.7 * value_similarity


def get_provider_stats(provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics for API calls
    
    Parameters:
    -----------
    provider: Optional provider to filter by
    
    Returns:
    --------
    Statistics dictionary
    """
    if not LOG.exists():
        return {
            "total_calls": 0,
            "total_cost": 0.0,
            "avg_latency": 0.0,
            "success_rate": 0.0,
            "providers": {}
        }
    
    stats = {
        "total_calls": 0,
        "total_cost": 0.0,
        "total_latency": 0.0,
        "success_count": 0,
        "providers": {}
    }
    
    with LOG.open("rb") as f:
        for line in f:
            try:
                record = orjson.loads(line)
                
                # Filter by provider if specified
                if provider and record["provider"] != provider:
                    continue
                
                p = record["provider"]
                if p not in stats["providers"]:
                    stats["providers"][p] = {
                        "calls": 0,
                        "cost": 0.0,
                        "latency": 0.0,
                        "success": 0
                    }
                
                stats["total_calls"] += 1
                stats["providers"][p]["calls"] += 1
                
                cost = record.get("cost_usd", 0.0)
                stats["total_cost"] += cost
                stats["providers"][p]["cost"] += cost
                
                latency = record.get("latency_ms", 0.0)
                stats["total_latency"] += latency
                stats["providers"][p]["latency"] += latency
                
                if record.get("success", True):
                    stats["success_count"] += 1
                    stats["providers"][p]["success"] += 1
                    
            except Exception:
                continue
    
    # Compute averages
    if stats["total_calls"] > 0:
        stats["avg_latency"] = stats["total_latency"] / stats["total_calls"]
        stats["success_rate"] = stats["success_count"] / stats["total_calls"]
    else:
        stats["avg_latency"] = 0.0
        stats["success_rate"] = 0.0
    
    # Remove intermediate counters
    del stats["total_latency"]
    del stats["success_count"]
    
    return stats


def find_replaceable_calls(min_frequency: int = 3) -> List[Dict[str, Any]]:
    """
    Find API calls that could be replaced with cached responses
    
    Parameters:
    -----------
    min_frequency: Minimum number of similar calls to consider replaceable
    
    Returns:
    --------
    List of replaceable call patterns
    """
    if not LOG.exists():
        return []
    
    # Group calls by signature
    call_groups = {}
    
    with LOG.open("rb") as f:
        for line in f:
            try:
                record = orjson.loads(line)
                
                # Create pattern key
                pattern_key = f"{record['provider']}:{record['endpoint']}"
                
                # Compute request signature
                req_sig = _compute_signature(record["request"])
                
                if pattern_key not in call_groups:
                    call_groups[pattern_key] = {}
                
                if req_sig not in call_groups[pattern_key]:
                    call_groups[pattern_key][req_sig] = {
                        "count": 0,
                        "total_cost": 0.0,
                        "sample_request": record["request"],
                        "sample_response": record["response"]
                    }
                
                call_groups[pattern_key][req_sig]["count"] += 1
                call_groups[pattern_key][req_sig]["total_cost"] += record.get("cost_usd", 0.0)
                
            except Exception:
                continue
    
    # Find patterns with high frequency
    replaceable = []
    
    for pattern_key, signatures in call_groups.items():
        for req_sig, data in signatures.items():
            if data["count"] >= min_frequency:
                provider, endpoint = pattern_key.split(":", 1)
                replaceable.append({
                    "provider": provider,
                    "endpoint": endpoint,
                    "frequency": data["count"],
                    "total_cost": data["total_cost"],
                    "potential_savings": data["total_cost"] * 0.9,  # Assume 90% savings
                    "sample_request": data["sample_request"]
                })
    
    # Sort by potential savings
    replaceable.sort(key=lambda x: x["potential_savings"], reverse=True)
    
    return replaceable


def create_replay_cache(max_size: int = 1000) -> Dict[str, dict]:
    """
    Create an in-memory replay cache from recorded calls
    
    Parameters:
    -----------
    max_size: Maximum cache size
    
    Returns:
    --------
    Cache dictionary mapping signatures to responses
    """
    if not LOG.exists():
        return {}
    
    cache = {}
    entries = []
    
    # Collect all successful calls
    with LOG.open("rb") as f:
        for line in f:
            try:
                record = orjson.loads(line)
                
                if record.get("success", True):
                    sig = f"{record['provider']}:{record['endpoint']}:{_compute_signature(record['request'])}"
                    entries.append((
                        sig,
                        record["response"],
                        record["timestamp"]
                    ))
            except Exception:
                continue
    
    # Keep most recent entries up to max_size
    entries.sort(key=lambda x: x[2], reverse=True)
    
    for sig, response, _ in entries[:max_size]:
        cache[sig] = response
    
    return cache


def quick_test():
    """Quick test of API metabolizer"""
    # Record some test calls
    record_call(
        provider="openai",
        endpoint="chat/completions",
        req={"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]},
        resp={"choices": [{"message": {"content": "Hi there!"}}]},
        latency_ms=523.4,
        cost_usd=0.002
    )
    
    record_call(
        provider="openai",
        endpoint="chat/completions",
        req={"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]},
        resp={"choices": [{"message": {"content": "Hello!"}}]},
        latency_ms=412.1,
        cost_usd=0.002
    )
    
    record_call(
        provider="anthropic",
        endpoint="messages",
        req={"model": "claude-3", "messages": [{"role": "user", "content": "Test"}]},
        resp={"content": "Test response"},
        latency_ms=234.5,
        cost_usd=0.001
    )
    
    # Test replay suggestion
    replay = suggest_replay(
        provider="openai",
        endpoint="chat/completions",
        request={"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]},
        similarity_threshold=0.9
    )
    
    # Get stats
    stats = get_provider_stats()
    
    # Find replaceable calls
    replaceable = find_replaceable_calls(min_frequency=2)
    
    return {
        "calls_recorded": stats["total_calls"],
        "total_cost": stats["total_cost"],
        "replay_found": replay is not None,
        "replaceable_patterns": len(replaceable),
        "potential_savings": sum(r["potential_savings"] for r in replaceable)
    }


if __name__ == "__main__":
    result = quick_test()
    print("API Metabolizer Test:")
    print(f"  Calls recorded: {result['calls_recorded']}")
    print(f"  Total cost: ${result['total_cost']:.3f}")
    print(f"  Replay found: {result['replay_found']}")
    print(f"  Replaceable patterns: {result['replaceable_patterns']}")
    print(f"  Potential savings: ${result['potential_savings']:.3f}")