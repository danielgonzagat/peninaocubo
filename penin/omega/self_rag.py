"""
Self-RAG Recursivo - PoC Leve
==============================

RAG simples sobre knowledge/ com queries recursivas.
Usa token overlap para similaridade (sem embeddings pesados).
"""

from collections import Counter
import re
from pathlib import Path
from typing import Dict, Any, Optional


KB = Path.home() / ".penin_omega" / "knowledge"
KB.mkdir(parents=True, exist_ok=True)


def _tok(s: str) -> list:
    """Tokeniza string em palavras"""
    return [t for t in re.findall(r"[A-Za-z0-9_]+", s.lower()) if t]


def _score(qt: Counter, dt: Counter) -> float:
    """Score de similaridade entre query e documento"""
    keys = set(qt) | set(dt)
    num = sum(min(qt[k], dt[k]) for k in keys)
    den = sum(max(qt[k], dt[k]) for k in keys) or 1
    return num / den


def ingest_text(name: str, text: str) -> None:
    """
    Ingere texto na knowledge base.
    
    Args:
        name: Nome do documento
        text: Conteúdo do texto
    """
    (KB / f"{name}.txt").write_text(text, encoding="utf-8")


def query(q: str) -> Dict[str, Any]:
    """
    Query na knowledge base.
    
    Args:
        q: Query string
        
    Returns:
        Dict com doc mais relevante e score
    """
    qt = Counter(_tok(q))
    best = None
    best_score = 0.0
    
    for p in KB.glob("*.txt"):
        text = p.read_text(encoding="utf-8")
        dt = Counter(_tok(text))
        s = _score(qt, dt)
        
        if s > best_score:
            best = p
            best_score = s
    
    return {
        "doc": best.name if best else None,
        "score": best_score,
        "content": best.read_text(encoding="utf-8") if best and best_score > 0.1 else None
    }


def self_cycle() -> Dict[str, Any]:
    """
    Executa um ciclo de auto-reflexão.
    
    Query inicial sobre evolução, depois gera nova query baseada no resultado.
    
    Returns:
        Dict com queries e respostas
    """
    q1 = "o que está faltando para evolução segura do penin?"
    ans1 = query(q1)
    
    if ans1["doc"]:
        # Gerar nova pergunta a partir do melhor doc
        q2 = f"Detalhar implementações pendentes em {ans1['doc']}"
        ans2 = query(q2)
        
        return {
            "q1": q1,
            "a1": ans1,
            "q2": q2,
            "a2": ans2
        }
    
    return {
        "q1": q1,
        "a1": ans1,
        "q2": None,
        "a2": None
    }


def get_knowledge_stats() -> Dict[str, Any]:
    """Estatísticas da knowledge base"""
    docs = list(KB.glob("*.txt"))
    
    total_chars = 0
    for doc in docs:
        total_chars += len(doc.read_text(encoding="utf-8"))
    
    return {
        "num_docs": len(docs),
        "total_chars": total_chars,
        "avg_chars_per_doc": total_chars // max(1, len(docs))
    }