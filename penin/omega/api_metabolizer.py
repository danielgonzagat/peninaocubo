# penin/omega/api_metabolizer.py
"""
Metabolização de APIs - I/O Recorder + Replayer
===============================================

Grava chamadas de API para reduzir dependências externas através de replay
inteligente de respostas similares.
"""

import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
import re

try:
    import orjson as json
except ImportError:
    import json

LOG_PATH = Path.home() / ".penin_omega" / "knowledge" / "api_io.jsonl"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def record_call(provider: str, endpoint: str, req: Dict[str, Any], resp: Dict[str, Any]) -> str:
    """Grava chamada de API"""
    item = {
        "timestamp": time.time(),
        "provider": provider,
        "endpoint": endpoint,
        "request": req,
        "response": resp,
        "hash": hashlib.sha256(str(req).encode()).hexdigest()[:16]
    }
    
    with LOG_PATH.open("ab") as f:
        if hasattr(json, 'dumps'):
            content = json.dumps(item)
            if isinstance(content, bytes):
                f.write(content + b"\n")
            else:
                f.write(content.encode() + b"\n")
        else:
            f.write(str(item).encode() + b"\n")
    
    return item["hash"]


def suggest_replay(prompt: str, provider: str = "openai", similarity_threshold: float = 0.7) -> Optional[Dict[str, Any]]:
    """Sugere replay baseado em similaridade"""
    if not LOG_PATH.exists():
        return None
    
    prompt_tokens = _tokenize(prompt)
    best_match = None
    best_score = 0.0
    
    try:
        with LOG_PATH.open("rb") as f:
            for line in f:
                try:
                    item = json.loads(line.decode())
                    if item.get("provider") != provider:
                        continue
                    
                    req_prompt = item.get("request", {}).get("prompt", "")
                    if not req_prompt:
                        continue
                    
                    score = _similarity_score(prompt_tokens, _tokenize(req_prompt))
                    if score > best_score and score >= similarity_threshold:
                        best_score = score
                        best_match = item
                        
                except Exception:
                    continue
    except Exception:
        return None
    
    if best_match:
        return {
            "response": best_match["response"],
            "similarity": best_score,
            "original_prompt": best_match["request"].get("prompt", ""),
            "timestamp": best_match["timestamp"]
        }
    
    return None


def _tokenize(text: str) -> Counter:
    """Tokenização simples"""
    tokens = re.findall(r'\b\w+\b', text.lower())
    return Counter(tokens)


def _similarity_score(tokens1: Counter, tokens2: Counter) -> float:
    """Calcula similaridade entre tokens"""
    all_tokens = set(tokens1) | set(tokens2)
    if not all_tokens:
        return 0.0
    
    intersection = sum(min(tokens1[t], tokens2[t]) for t in all_tokens)
    union = sum(max(tokens1[t], tokens2[t]) for t in all_tokens)
    
    return intersection / union if union > 0 else 0.0


def get_metabolization_stats() -> Dict[str, Any]:
    """Estatísticas de metabolização"""
    if not LOG_PATH.exists():
        return {"total_calls": 0, "providers": {}}
    
    stats = {"total_calls": 0, "providers": {}}
    
    try:
        with LOG_PATH.open("rb") as f:
            for line in f:
                try:
                    item = json.loads(line.decode())
                    stats["total_calls"] += 1
                    provider = item.get("provider", "unknown")
                    if provider not in stats["providers"]:
                        stats["providers"][provider] = 0
                    stats["providers"][provider] += 1
                except Exception:
                    continue
    except Exception:
        pass
    
    return stats