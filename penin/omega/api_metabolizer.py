"""
API Metabolizer - I/O Recording and Replay
===========================================

Records API calls for future replay and dependency reduction.
Learns patterns to suggest cached responses.
"""

import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import re

try:
    import orjson
    json_dumps = lambda x: orjson.dumps(x)
    json_loads = lambda x: orjson.loads(x)
except ImportError:
    import json
    json_dumps = lambda x: json.dumps(x).encode()
    json_loads = lambda x: json.loads(x)


LOG = Path.home() / ".penin_omega" / "knowledge" / "api_io.jsonl"
LOG.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class APICall:
    """Recorded API call"""
    timestamp: float
    provider: str
    endpoint: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def signature(self) -> str:
        """Generate signature for matching similar calls"""
        # Create a signature from provider, endpoint, and key request params
        sig_parts = [
            self.provider,
            self.endpoint,
            str(self.request.get("model", "")),
            str(len(self.request.get("prompt", ""))),
            str(self.request.get("max_tokens", 0))
        ]
        sig_str = "|".join(sig_parts)
        return hashlib.md5(sig_str.encode()).hexdigest()[:16]


def record_call(
    provider: str,
    endpoint: str,
    req: Dict[str, Any],
    resp: Dict[str, Any],
    latency_ms: float = 0.0,
    cost_usd: float = 0.0,
    success: bool = True
) -> bool:
    """
    Record an API call for future analysis.
    
    Args:
        provider: API provider name
        endpoint: API endpoint
        req: Request payload
        resp: Response payload
        latency_ms: Call latency in milliseconds
        cost_usd: Call cost in USD
        success: Whether call succeeded
    
    Returns:
        True if successfully recorded
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
    
    try:
        with LOG.open("ab") as f:
            f.write(json_dumps(call.to_dict()) + b"\n")
        return True
    except Exception as e:
        print(f"Failed to record API call: {e}")
        return False


def load_history(limit: int = 1000) -> List[APICall]:
    """Load API call history"""
    if not LOG.exists():
        return []
    
    calls = []
    with LOG.open("rb") as f:
        for line in f:
            if line.strip():
                try:
                    data = json_loads(line)
                    calls.append(APICall(**data))
                except:
                    continue
    
    # Return most recent calls
    return calls[-limit:] if len(calls) > limit else calls


def suggest_replay(prompt: str, provider: str = None) -> Optional[Dict[str, Any]]:
    """
    Suggest a cached response for a similar prompt.
    
    Args:
        prompt: Current prompt
        provider: Optional provider filter
    
    Returns:
        Suggested response or None
    """
    history = load_history()
    
    if not history:
        return None
    
    # Filter by provider if specified
    if provider:
        history = [h for h in history if h.provider == provider]
    
    # Simple similarity: find calls with similar prompt length
    prompt_len = len(prompt)
    best_match = None
    best_score = float('inf')
    
    for call in history:
        if not call.success:
            continue
            
        req_prompt = call.request.get("prompt", "")
        if not req_prompt:
            continue
        
        # Calculate similarity score (simple length difference)
        len_diff = abs(len(req_prompt) - prompt_len)
        
        # Bonus for exact matches in first N characters
        prefix_match = 0
        if req_prompt[:50] == prompt[:50]:
            prefix_match = 100
        
        score = len_diff - prefix_match
        
        if score < best_score:
            best_score = score
            best_match = call
    
    if best_match and best_score < 100:  # Threshold for similarity
        return {
            "response": best_match.response,
            "cached": True,
            "original_timestamp": best_match.timestamp,
            "similarity_score": 1.0 / (1.0 + best_score),
            "provider": best_match.provider
        }
    
    return None


def analyze_patterns() -> Dict[str, Any]:
    """Analyze API usage patterns"""
    history = load_history()
    
    if not history:
        return {"message": "No history available"}
    
    # Group by provider
    by_provider = {}
    for call in history:
        if call.provider not in by_provider:
            by_provider[call.provider] = {
                "count": 0,
                "total_cost": 0.0,
                "total_latency": 0.0,
                "success_rate": 0.0,
                "endpoints": set()
            }
        
        stats = by_provider[call.provider]
        stats["count"] += 1
        stats["total_cost"] += call.cost_usd
        stats["total_latency"] += call.latency_ms
        stats["endpoints"].add(call.endpoint)
        if call.success:
            stats["success_rate"] += 1
    
    # Calculate averages
    for provider, stats in by_provider.items():
        count = stats["count"]
        if count > 0:
            stats["avg_cost"] = stats["total_cost"] / count
            stats["avg_latency"] = stats["total_latency"] / count
            stats["success_rate"] = stats["success_rate"] / count
            stats["endpoints"] = list(stats["endpoints"])
    
    # Find most similar calls (potential duplicates)
    signatures = {}
    for call in history:
        sig = call.signature()
        if sig not in signatures:
            signatures[sig] = []
        signatures[sig].append(call)
    
    duplicates = {
        sig: len(calls) 
        for sig, calls in signatures.items() 
        if len(calls) > 1
    }
    
    return {
        "total_calls": len(history),
        "by_provider": by_provider,
        "duplicate_patterns": duplicates,
        "potential_savings": sum(
            (len(calls) - 1) * calls[0].cost_usd
            for calls in signatures.values()
            if len(calls) > 1
        )
    }


class APIMetabolizer:
    """
    High-level API metabolizer that learns and replaces API calls.
    """
    
    def __init__(self, cache_threshold: float = 0.8):
        self.cache_threshold = cache_threshold  # Similarity threshold for caching
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_saved": 0.0
        }
    
    def metabolize(
        self,
        provider: str,
        endpoint: str,
        request: Dict[str, Any],
        fallback_fn = None
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Try to metabolize (cache) an API call.
        
        Args:
            provider: API provider
            endpoint: API endpoint
            request: Request payload
            fallback_fn: Function to call if cache miss
        
        Returns:
            (response, was_cached)
        """
        # Try to find cached response
        prompt = request.get("prompt", "")
        cached = suggest_replay(prompt, provider)
        
        if cached and cached.get("similarity_score", 0) >= self.cache_threshold:
            # Use cached response
            self.stats["cache_hits"] += 1
            self.stats["total_saved"] += request.get("estimated_cost", 0.001)
            
            return cached["response"], True
        
        # Cache miss - make real call if fallback provided
        self.stats["cache_misses"] += 1
        
        if fallback_fn:
            start_time = time.time()
            response = fallback_fn(request)
            latency_ms = (time.time() - start_time) * 1000
            
            # Record for future use
            record_call(
                provider=provider,
                endpoint=endpoint,
                req=request,
                resp=response,
                latency_ms=latency_ms,
                cost_usd=request.get("estimated_cost", 0.001)
            )
            
            return response, False
        
        return {"error": "No cached response and no fallback"}, False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get metabolizer statistics"""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = self.stats["cache_hits"] / max(total, 1)
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "total_calls": total,
            "patterns": analyze_patterns()
        }
    
    def learn_pattern(self, pattern_type: str, examples: List[Dict[str, Any]]):
        """
        Learn a pattern from examples (future: train small model).
        
        Args:
            pattern_type: Type of pattern (completion, classification, etc)
            examples: List of input/output examples
        """
        # Placeholder for future ML-based pattern learning
        # Could train a small model to replicate API behavior
        pass
    
    def suggest_replacement(self, provider: str) -> Optional[str]:
        """
        Suggest a replacement strategy for a provider.
        
        Args:
            provider: Provider to analyze
        
        Returns:
            Suggestion string or None
        """
        patterns = analyze_patterns()
        
        if provider not in patterns.get("by_provider", {}):
            return None
        
        stats = patterns["by_provider"][provider]
        
        suggestions = []
        
        # High cost suggestion
        if stats.get("avg_cost", 0) > 0.01:
            suggestions.append(
                f"High average cost (${stats['avg_cost']:.4f}). "
                "Consider caching or using cheaper provider."
            )
        
        # High latency suggestion
        if stats.get("avg_latency", 0) > 1000:
            suggestions.append(
                f"High latency ({stats['avg_latency']:.0f}ms). "
                "Consider async batching or local model."
            )
        
        # Duplicate pattern suggestion
        duplicate_count = sum(
            1 for v in patterns.get("duplicate_patterns", {}).values()
            if v > 5
        )
        if duplicate_count > 0:
            suggestions.append(
                f"Found {duplicate_count} duplicate patterns. "
                f"Potential savings: ${patterns.get('potential_savings', 0):.2f}"
            )
        
        return " ".join(suggestions) if suggestions else None


def cleanup_old_logs(days: int = 30) -> int:
    """Clean up old API logs"""
    if not LOG.exists():
        return 0
    
    cutoff = time.time() - (days * 24 * 3600)
    kept_calls = []
    removed = 0
    
    with LOG.open("rb") as f:
        for line in f:
            if line.strip():
                try:
                    data = json_loads(line)
                    if data.get("timestamp", 0) >= cutoff:
                        kept_calls.append(line)
                    else:
                        removed += 1
                except:
                    continue
    
    # Rewrite file with kept calls
    if removed > 0:
        with LOG.open("wb") as f:
            for line in kept_calls:
                f.write(line)
    
    return removed