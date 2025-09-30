"""
Metabolização de APIs - I/O Recorder → Replayer
================================================

Grava chamadas de APIs e sugere respostas cacheadas para reduzir dependências.
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    import json
    HAS_ORJSON = False


LOG = Path.home() / ".penin_omega" / "knowledge" / "api_io.jsonl"
LOG.parent.mkdir(parents=True, exist_ok=True)


def record_call(provider: str, endpoint: str, req: Dict[str, Any], resp: Dict[str, Any]) -> None:
    """
    Grava chamada de API.
    
    Args:
        provider: Nome do provider (e.g., "openai", "anthropic")
        endpoint: Endpoint chamado
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
    
    if HAS_ORJSON:
        line = orjson.dumps(item) + b"\n"
    else:
        line = (json.dumps(item) + "\n").encode()
    
    LOG.open("ab").write(line)


def suggest_replay(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Procura resposta similar para replay.
    
    Args:
        prompt: Prompt da query atual
        
    Returns:
        Response dict ou None se não encontrar similar
    """
    if not LOG.exists():
        return None
    
    best = None
    best_diff = 10**9
    
    for line in LOG.open("rb"):
        if HAS_ORJSON:
            it = orjson.loads(line)
        else:
            it = json.loads(line.decode())
        
        # Verificar se tem prompt similar
        req_prompt = it.get("req", {})
        if isinstance(req_prompt, dict):
            req_prompt = req_prompt.get("prompt", "") or req_prompt.get("messages", "")
        if isinstance(req_prompt, list):
            req_prompt = str(req_prompt)
        
        if isinstance(req_prompt, str):
            diff = abs(len(req_prompt) - len(prompt))
            if diff < best_diff:
                best_diff = diff
                best = it
    
    if best and best_diff < 100:  # Similar enough
        return best.get("resp", {"note": "cached-response"})
    
    return None


def get_provider_stats(provider: str) -> Dict[str, Any]:
    """
    Estatísticas de uso de um provider.
    
    Args:
        provider: Nome do provider
        
    Returns:
        Dict com estatísticas
    """
    if not LOG.exists():
        return {"count": 0, "first": None, "last": None}
    
    count = 0
    first_ts = None
    last_ts = None
    
    for line in LOG.open("rb"):
        if HAS_ORJSON:
            it = orjson.loads(line)
        else:
            it = json.loads(line.decode())
        
        if it.get("p") == provider:
            count += 1
            ts = it.get("t", 0)
            if first_ts is None or ts < first_ts:
                first_ts = ts
            if last_ts is None or ts > last_ts:
                last_ts = ts
    
    return {
        "count": count,
        "first": first_ts,
        "last": last_ts
    }