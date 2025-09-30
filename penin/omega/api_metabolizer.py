"""
API Metabolizer - I/O Recording & Replay
========================================

Records API calls and responses to enable:
- Replay of similar requests (reducing dependencies)
- Learning from I/O patterns
- Eventually replacing APIs with internal models

This is the first step toward "metabolizing" external dependencies.
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import Counter
import re

try:
    import orjson as json_lib
except ImportError:
    import json as json_lib


LOG = Path.home() / ".penin_omega" / "knowledge" / "api_io.jsonl"
LOG.parent.mkdir(parents=True, exist_ok=True)


def record_call(
    provider: str,
    endpoint: str,
    req: Dict[str, Any],
    resp: Dict[str, Any]
) -> None:
    """
    Record an API call.
    
    Args:
        provider: Provider name (e.g., "openai", "anthropic")
        endpoint: Endpoint name (e.g., "chat/completions")
        req: Request payload
        resp: Response payload
    """
    item = {
        "t": time.time(),
        "p": provider,
        "e": endpoint,
        "req": req,
        "resp": resp
    }
    
    if hasattr(json_lib, 'dumps'):
        data = json_lib.dumps(item) + b"\n" if 'orjson' in str(type(json_lib)) else (json_lib.dumps(item) + "\n").encode()
    else:
        import json
        data = (json.dumps(item) + "\n").encode()
    
    LOG.open("ab").write(data)


def _tokenize(text: str) -> List[str]:
    """Simple tokenization for similarity"""
    return [t for t in re.findall(r"[A-Za-z0-9_]+", text.lower()) if t]


def _similarity(text1: str, text2: str) -> float:
    """Compute similarity between two texts"""
    tokens1 = Counter(_tokenize(text1))
    tokens2 = Counter(_tokenize(text2))
    
    all_tokens = set(tokens1.keys()) | set(tokens2.keys())
    
    if not all_tokens:
        return 0.0
    
    intersection = sum(min(tokens1[t], tokens2[t]) for t in all_tokens)
    union = sum(max(tokens1[t], tokens2[t]) for t in all_tokens)
    
    return intersection / max(1, union)


def suggest_replay(
    provider: str,
    prompt: str,
    similarity_threshold: float = 0.7
) -> Optional[Dict[str, Any]]:
    """
    Suggest a replay from past calls.
    
    Args:
        provider: Provider name
        prompt: Current prompt
        similarity_threshold: Minimum similarity to consider
        
    Returns:
        Best matching response or None
    """
    if not LOG.exists():
        return None
    
    best_match = None
    best_score = 0.0
    
    with LOG.open("rb") as f:
        for line in f:
            if hasattr(json_lib, 'loads'):
                item = json_lib.loads(line)
            else:
                import json
                item = json.loads(line.decode())
            
            if item["p"] != provider:
                continue
            
            # Extract prompt from request
            req_prompt = str(item["req"].get("prompt", item["req"].get("messages", "")))
            
            # Compute similarity
            score = _similarity(prompt, req_prompt)
            
            if score > best_score:
                best_score = score
                best_match = item
    
    if best_match and best_score >= similarity_threshold:
        return {
            "response": best_match["resp"],
            "similarity": best_score,
            "timestamp": best_match["t"]
        }
    
    return None


def get_stats() -> Dict[str, Any]:
    """Get metabolizer statistics"""
    if not LOG.exists():
        return {"total_calls": 0}
    
    providers = Counter()
    endpoints = Counter()
    total = 0
    
    with LOG.open("rb") as f:
        for line in f:
            if hasattr(json_lib, 'loads'):
                item = json_lib.loads(line)
            else:
                import json
                item = json.loads(line.decode())
            
            providers[item["p"]] += 1
            endpoints[item["e"]] += 1
            total += 1
    
    return {
        "total_calls": total,
        "providers": dict(providers),
        "endpoints": dict(endpoints)
    }


class APIMetabolizer:
    """
    Manages API call recording and replay.
    
    Integration point for the router to gradually reduce
    external dependencies.
    """
    
    def __init__(self, replay_enabled: bool = True):
        self.replay_enabled = replay_enabled
        self.hits = 0
        self.misses = 0
        
        print(f"🧬 API Metabolizer initialized (replay={'ON' if replay_enabled else 'OFF'})")
    
    def record(
        self,
        provider: str,
        endpoint: str,
        req: Dict[str, Any],
        resp: Dict[str, Any]
    ) -> None:
        """Record an API call"""
        record_call(provider, endpoint, req, resp)
    
    def try_replay(
        self,
        provider: str,
        prompt: str,
        similarity_threshold: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """
        Try to replay from cache.
        
        Returns:
            Cached response or None
        """
        if not self.replay_enabled:
            return None
        
        result = suggest_replay(provider, prompt, similarity_threshold)
        
        if result:
            self.hits += 1
            print(f"🎯 Cache HIT (similarity={result['similarity']:.2f})")
        else:
            self.misses += 1
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        global_stats = get_stats()
        
        hit_rate = self.hits / max(1, self.hits + self.misses)
        
        return {
            **global_stats,
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "hit_rate": hit_rate
        }


# Quick test
def quick_metabolizer_test():
    """Quick test of metabolizer"""
    meta = APIMetabolizer(replay_enabled=True)
    
    # Record some calls
    for i in range(3):
        meta.record(
            "openai",
            "chat/completions",
            {"prompt": f"Test prompt {i}"},
            {"text": f"Response {i}", "cost": 0.01}
        )
    
    # Try replay
    result = meta.try_replay("openai", "Test prompt 0")
    print(f"\n🎯 Replay result: {result}")
    
    stats = meta.get_stats()
    print(f"\n📊 Stats: {stats}")
    
    return meta