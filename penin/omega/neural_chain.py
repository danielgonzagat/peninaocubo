"""
Blockchain Neural Leve - Sobre WORM
===================================

Encadeamento de blocos cognitivos com HMAC local.
"""

import hmac
import hashlib
import time
import orjson
import os
from pathlib import Path


KEY = (os.getenv("PENIN_CHAIN_KEY") or "dev-key").encode()
ROOT = Path.home() / ".penin_omega" / "worm_ledger"
ROOT.mkdir(parents=True, exist_ok=True)
CHAIN = ROOT / "neural_chain.jsonl"


def _hash_block(block: dict) -> str:
    """Gera hash HMAC do bloco"""
    raw = orjson.dumps(block, option=orjson.OPT_SORT_KEYS)
    return hmac.new(KEY, raw, hashlib.sha256).hexdigest()


def add_block(state_snapshot: dict, prev_hash: str = None) -> str:
    """
    Adiciona bloco à cadeia neural
    
    Args:
        state_snapshot: Snapshot do estado cognitivo
        prev_hash: Hash do bloco anterior
        
    Returns:
        Hash do novo bloco
    """
    block = {
        "ts": time.time(),
        "prev": prev_hash or "GENESIS",
        "state": state_snapshot,
    }
    block["hash"] = _hash_block(block)
    
    # Append ao arquivo
    with CHAIN.open("ab") as f:
        f.write(orjson.dumps(block) + b"\n")
    
    return block["hash"]


def get_chain_head() -> dict:
    """Retorna último bloco da cadeia"""
    if not CHAIN.exists():
        return None
    
    with CHAIN.open("rb") as f:
        lines = f.readlines()
        if lines:
            return orjson.loads(lines[-1])
    
    return None


def verify_chain() -> bool:
    """Verifica integridade da cadeia"""
    if not CHAIN.exists():
        return True
    
    try:
        with CHAIN.open("rb") as f:
            prev_hash = "GENESIS"
            
            for line in f:
                if not line.strip():
                    continue
                    
                block = orjson.loads(line)
                
                # Verificar hash
                expected_hash = _hash_block({
                    "ts": block["ts"],
                    "prev": block["prev"],
                    "state": block["state"]
                })
                
                if block["hash"] != expected_hash:
                    return False
                
                # Verificar encadeamento
                if block["prev"] != prev_hash:
                    return False
                
                prev_hash = block["hash"]
        
        return True
    except Exception:
        # Em caso de erro, assumir cadeia inválida
        return False