"""
Self-RAG Recursive - Lightweight Knowledge Query
================================================

Implements a simple self-referential RAG system:
- Ingest text into knowledge base
- Query via token-based similarity
- Self-cycle: generate new questions from answers

This is a CPU-friendly PoC without heavy embeddings.
"""

from collections import Counter
import re
from pathlib import Path
from typing import Dict, Any, List, Optional


KB = Path.home() / ".penin_omega" / "knowledge"
KB.mkdir(parents=True, exist_ok=True)


def _tokenize(text: str) -> List[str]:
    """Tokenize text for similarity"""
    return [t for t in re.findall(r"[A-Za-z0-9_]+", text.lower()) if t]


def _score(query_tokens: Counter, doc_tokens: Counter) -> float:
    """Compute similarity score"""
    all_keys = set(query_tokens.keys()) | set(doc_tokens.keys())
    
    if not all_keys:
        return 0.0
    
    intersection = sum(min(query_tokens[k], doc_tokens[k]) for k in all_keys)
    union = sum(max(query_tokens[k], doc_tokens[k]) for k in all_keys)
    
    return intersection / max(1, union)


def ingest_text(name: str, text: str) -> None:
    """
    Ingest text into knowledge base.
    
    Args:
        name: Document name
        text: Document content
    """
    path = KB / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    print(f"📥 Ingested: {name} ({len(text)} chars)")


def query(q: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Query knowledge base.
    
    Args:
        q: Query string
        top_k: Number of results to return
        
    Returns:
        List of {doc, score, preview} dicts
    """
    query_tokens = Counter(_tokenize(q))
    
    results = []
    
    for doc_path in KB.glob("*.txt"):
        doc_text = doc_path.read_text(encoding="utf-8")
        doc_tokens = Counter(_tokenize(doc_text))
        
        score = _score(query_tokens, doc_tokens)
        
        if score > 0:
            results.append({
                "doc": doc_path.name,
                "score": score,
                "preview": doc_text[:200]
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:top_k]


def self_cycle() -> Dict[str, Any]:
    """
    Execute one self-RAG cycle.
    
    Generates a question, queries KB, and generates follow-up.
    
    Returns:
        Dict with cycle results
    """
    # Initial question
    q1 = "What is missing for safe evolution of PENIN-Ω?"
    
    # Query
    results = query(q1, top_k=1)
    
    if not results:
        return {"q1": q1, "a1": None, "q2": None}
    
    best = results[0]
    
    # Generate follow-up question
    q2 = f"Detail implementation gaps in {best['doc']}"
    
    return {
        "q1": q1,
        "a1": best,
        "q2": q2
    }


class SelfRAG:
    """
    Self-referential RAG system.
    
    Manages knowledge ingestion, querying, and recursive self-inquiry.
    """
    
    def __init__(self):
        self.cycle_history: List[Dict[str, Any]] = []
        print("🔄 Self-RAG initialized")
    
    def ingest(self, name: str, text: str) -> None:
        """Ingest document"""
        ingest_text(name, text)
    
    def query(self, q: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query knowledge base"""
        return query(q, top_k)
    
    def cycle(self) -> Dict[str, Any]:
        """Execute self-RAG cycle"""
        result = self_cycle()
        self.cycle_history.append(result)
        
        print(f"🔄 Cycle {len(self.cycle_history)}:")
        print(f"   Q1: {result['q1']}")
        if result['a1']:
            print(f"   A1: {result['a1']['doc']} (score={result['a1']['score']:.3f})")
        print(f"   Q2: {result['q2']}")
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        docs = list(KB.glob("*.txt"))
        
        return {
            "documents": len(docs),
            "cycles": len(self.cycle_history),
            "kb_path": str(KB)
        }


# Quick test
def quick_self_rag_test():
    """Quick test of self-RAG"""
    rag = SelfRAG()
    
    # Ingest some docs
    rag.ingest("penin_overview", """
        PENIN-Ω is an auto-evolutionary AI system.
        Key components: Sigma-Guard, CAOS+, SR-Omega, L-infinity, WORM ledger.
        Missing: Life Equation integration, fractal DSL, swarm consensus.
    """)
    
    rag.ingest("todo_list", """
        TODO for PENIN evolution:
        - Integrate Life Equation as positive gate
        - Implement fractal DSL for module replication
        - Add swarm cognitive gossip protocol
        - Enable API metabolization
    """)
    
    # Run query
    results = rag.query("What components are missing?")
    print(f"\n🔍 Query results:")
    for r in results:
        print(f"   {r['doc']}: {r['score']:.3f}")
    
    # Run cycle
    print(f"\n🔄 Running self-cycle...")
    rag.cycle()
    
    stats = rag.get_stats()
    print(f"\n📊 Stats: {stats}")
    
    return rag