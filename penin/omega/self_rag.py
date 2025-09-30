"""
Self-RAG Recursive - Lightweight recursive retrieval-augmented generation
Uses simple token matching for knowledge base queries
"""

from collections import Counter
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Knowledge base directory
KB = Path.home() / ".penin_omega" / "knowledge"
KB.mkdir(parents=True, exist_ok=True)


def _tokenize(text: str) -> List[str]:
    """
    Simple tokenization: extract alphanumeric tokens
    
    Parameters:
    -----------
    text: Input text
    
    Returns:
    --------
    List of lowercase tokens
    """
    return [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", text) if t]


def _score(query_tokens: Counter, doc_tokens: Counter) -> float:
    """
    Compute similarity score between query and document
    
    Parameters:
    -----------
    query_tokens: Token counter for query
    doc_tokens: Token counter for document
    
    Returns:
    --------
    Similarity score [0, 1]
    """
    if not query_tokens or not doc_tokens:
        return 0.0
    
    # Compute intersection and union
    keys = set(query_tokens) | set(doc_tokens)
    
    if not keys:
        return 0.0
    
    # Jaccard-like similarity with frequency consideration
    numerator = sum(min(query_tokens[k], doc_tokens[k]) for k in keys)
    denominator = sum(max(query_tokens[k], doc_tokens[k]) for k in keys)
    
    return numerator / denominator if denominator > 0 else 0.0


def ingest_text(name: str, text: str, metadata: Optional[dict] = None) -> None:
    """
    Ingest a text document into the knowledge base
    
    Parameters:
    -----------
    name: Document name (without extension)
    text: Document content
    metadata: Optional metadata to store with document
    """
    # Save text
    doc_path = KB / f"{name}.txt"
    doc_path.write_text(text, encoding="utf-8")
    
    # Save metadata if provided
    if metadata:
        meta_path = KB / f"{name}.meta.json"
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def query(q: str, top_k: int = 3) -> List[Dict[str, any]]:
    """
    Query the knowledge base
    
    Parameters:
    -----------
    q: Query string
    top_k: Number of top results to return
    
    Returns:
    --------
    List of results with document name, score, and snippet
    """
    query_tokens = Counter(_tokenize(q))
    results = []
    
    for doc_path in KB.glob("*.txt"):
        # Skip metadata files
        if ".meta." in doc_path.name:
            continue
        
        # Read and tokenize document
        try:
            doc_text = doc_path.read_text(encoding="utf-8")
            doc_tokens = Counter(_tokenize(doc_text))
            
            # Compute score
            score = _score(query_tokens, doc_tokens)
            
            if score > 0:
                # Extract snippet around best matching position
                snippet = extract_snippet(doc_text, q, max_length=200)
                
                results.append({
                    "doc": doc_path.stem,
                    "score": score,
                    "snippet": snippet,
                    "path": str(doc_path)
                })
        except Exception:
            continue
    
    # Sort by score and return top k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def extract_snippet(text: str, query: str, max_length: int = 200) -> str:
    """
    Extract a relevant snippet from text based on query
    
    Parameters:
    -----------
    text: Full document text
    query: Query string
    max_length: Maximum snippet length
    
    Returns:
    --------
    Relevant text snippet
    """
    # Find first occurrence of any query word
    query_words = _tokenize(query)
    
    if not query_words:
        return text[:max_length] + "..." if len(text) > max_length else text
    
    best_pos = len(text)
    for word in query_words:
        pos = text.lower().find(word.lower())
        if pos != -1 and pos < best_pos:
            best_pos = pos
    
    if best_pos == len(text):
        # No match found, return beginning
        return text[:max_length] + "..." if len(text) > max_length else text
    
    # Extract window around match
    start = max(0, best_pos - max_length // 2)
    end = min(len(text), start + max_length)
    
    snippet = text[start:end]
    
    # Add ellipsis if truncated
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    
    return snippet


def self_cycle(initial_query: Optional[str] = None, max_depth: int = 3) -> List[Dict[str, any]]:
    """
    Recursive self-questioning cycle
    
    Parameters:
    -----------
    initial_query: Starting query (default: system introspection)
    max_depth: Maximum recursion depth
    
    Returns:
    --------
    List of query-answer pairs from the cycle
    """
    if initial_query is None:
        initial_query = "what is missing for safe evolution of the penin system?"
    
    cycle_results = []
    current_query = initial_query
    
    for depth in range(max_depth):
        # Query knowledge base
        results = query(current_query, top_k=1)
        
        if not results:
            # No results, end cycle
            cycle_results.append({
                "depth": depth,
                "query": current_query,
                "answer": None,
                "next_query": None
            })
            break
        
        best_result = results[0]
        
        # Generate next query based on result
        # Simple heuristic: ask for more details about the document
        next_query = generate_followup_query(best_result["doc"], best_result["snippet"])
        
        cycle_results.append({
            "depth": depth,
            "query": current_query,
            "answer": best_result,
            "next_query": next_query
        })
        
        current_query = next_query
    
    return cycle_results


def generate_followup_query(doc_name: str, snippet: str) -> str:
    """
    Generate a follow-up query based on previous result
    
    Parameters:
    -----------
    doc_name: Name of the document found
    snippet: Snippet from the document
    
    Returns:
    --------
    Follow-up query string
    """
    # Extract key terms from snippet
    tokens = _tokenize(snippet)
    
    if not tokens:
        return f"explain more about {doc_name}"
    
    # Find most common non-trivial tokens
    token_counts = Counter(tokens)
    
    # Filter out common words (simple stopword list)
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "and", "or", "but"}
    filtered = [(t, c) for t, c in token_counts.items() if t not in stopwords and len(t) > 2]
    
    if filtered:
        # Use most common meaningful term
        key_term = max(filtered, key=lambda x: x[1])[0]
        return f"explain implementation details for {key_term} in {doc_name}"
    else:
        return f"what are the key concepts in {doc_name}"


def build_index() -> Dict[str, List[str]]:
    """
    Build an inverted index for faster queries
    
    Returns:
    --------
    Dictionary mapping tokens to document names
    """
    index = {}
    
    for doc_path in KB.glob("*.txt"):
        if ".meta." in doc_path.name:
            continue
        
        try:
            doc_text = doc_path.read_text(encoding="utf-8")
            tokens = set(_tokenize(doc_text))
            
            for token in tokens:
                if token not in index:
                    index[token] = []
                index[token].append(doc_path.stem)
        except Exception:
            continue
    
    return index


def quick_test():
    """Quick test of Self-RAG system"""
    # Ingest some test documents
    ingest_text(
        "penin_overview",
        "PENIN-Ω is an auto-evolutionary system with fail-closed gates and "
        "non-compensatory evaluation. It uses CAOS+ for exploration and "
        "Life Equation for positive evolution orchestration.",
        metadata={"type": "overview", "version": "1.0"}
    )
    
    ingest_text(
        "safety_gates",
        "The system implements multiple safety gates including Sigma-Guard for ethics, "
        "IR-IC for risk contractiveness, and Zero-Consciousness Proof to prevent "
        "sentience emergence. All gates operate in fail-closed mode.",
        metadata={"type": "safety", "critical": True}
    )
    
    ingest_text(
        "evolution_mechanics",
        "Evolution is controlled by alpha_eff computed from the Life Equation. "
        "The system uses fractal propagation for configuration updates and "
        "swarm consensus for distributed decision making.",
        metadata={"type": "technical", "module": "evolution"}
    )
    
    # Test query
    results = query("safety gates for evolution", top_k=2)
    
    # Test self-cycle
    cycle = self_cycle("how does PENIN ensure safety?", max_depth=2)
    
    return {
        "docs_ingested": 3,
        "query_results": len(results),
        "top_result": results[0]["doc"] if results else None,
        "top_score": results[0]["score"] if results else 0,
        "cycle_depth": len(cycle),
        "final_query": cycle[-1]["next_query"] if cycle else None
    }


if __name__ == "__main__":
    result = quick_test()
    print("Self-RAG Recursive Test:")
    print(f"  Documents ingested: {result['docs_ingested']}")
    print(f"  Query results: {result['query_results']}")
    print(f"  Top result: {result['top_result']} (score: {result['top_score']:.3f})")
    print(f"  Self-cycle depth: {result['cycle_depth']}")
    print(f"  Final query: {result['final_query']}")