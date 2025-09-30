# penin/omega/self_rag.py
"""
Self-RAG Recursivo
==================

Sistema de auto-questionamento e busca recursiva no knowledge base.
"""

from collections import Counter
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

KB_PATH = Path.home() / ".penin_omega" / "knowledge"
KB_PATH.mkdir(parents=True, exist_ok=True)


def _tokenize(text: str) -> List[str]:
    """Tokenização simples"""
    return [t for t in re.findall(r"[A-Za-z0-9_]+", text.lower()) if t]


def _similarity_score(query_tokens: Counter, doc_tokens: Counter) -> float:
    """Calcula similaridade entre query e documento"""
    all_tokens = set(query_tokens) | set(doc_tokens)
    if not all_tokens:
        return 0.0
    
    intersection = sum(min(query_tokens[t], doc_tokens[t]) for t in all_tokens)
    union = sum(max(query_tokens[t], doc_tokens[t]) for t in all_tokens)
    
    return intersection / union if union > 0 else 0.0


def ingest_text(name: str, text: str) -> str:
    """Ingere texto no knowledge base"""
    file_path = KB_PATH / f"{name}.txt"
    file_path.write_text(text, encoding="utf-8")
    return str(file_path)


def query(question: str, top_k: int = 3) -> Dict[str, Any]:
    """Busca no knowledge base"""
    query_tokens = Counter(_tokenize(question))
    results = []
    
    for txt_file in KB_PATH.glob("*.txt"):
        try:
            content = txt_file.read_text(encoding="utf-8")
            doc_tokens = Counter(_tokenize(content))
            score = _similarity_score(query_tokens, doc_tokens)
            
            if score > 0:
                results.append({
                    "document": txt_file.name,
                    "score": score,
                    "content_preview": content[:200] + "..." if len(content) > 200 else content
                })
        except Exception:
            continue
    
    # Ordenar por score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "query": question,
        "results": results[:top_k],
        "total_found": len(results)
    }


def self_cycle() -> Dict[str, Any]:
    """Executa ciclo de auto-questionamento"""
    base_question = "o que está faltando para evolução segura do penin?"
    
    # Primeira busca
    first_result = query(base_question)
    
    if not first_result["results"]:
        return {
            "cycle": 1,
            "question": base_question,
            "answer": None,
            "next_question": None
        }
    
    # Gerar próxima pergunta baseada no melhor resultado
    best_doc = first_result["results"][0]["document"]
    next_question = f"Detalhar implementações pendentes em {best_doc}"
    
    # Segunda busca
    second_result = query(next_question)
    
    return {
        "cycle": 2,
        "first_question": base_question,
        "first_answer": first_result,
        "second_question": next_question,
        "second_answer": second_result
    }


def get_knowledge_stats() -> Dict[str, Any]:
    """Estatísticas do knowledge base"""
    files = list(KB_PATH.glob("*.txt"))
    total_size = sum(f.stat().st_size for f in files if f.exists())
    
    return {
        "total_documents": len(files),
        "total_size_bytes": total_size,
        "documents": [f.name for f in files]
    }