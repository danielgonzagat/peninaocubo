"""
Self-RAG - Recursive Retrieval-Augmented Generation
====================================================

Lightweight self-referential RAG system for knowledge management.
Uses simple text matching without heavy dependencies.
"""

from collections import Counter
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import time


KB = Path.home() / ".penin_omega" / "knowledge"
KB.mkdir(parents=True, exist_ok=True)


@dataclass
class Document:
    """Knowledge document"""
    name: str
    content: str
    metadata: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


def _tokenize(text: str) -> List[str]:
    """Simple tokenization"""
    return [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", text) if t]


def _score(query_tokens: Counter, doc_tokens: Counter) -> float:
    """Calculate similarity score between query and document"""
    keys = set(query_tokens) | set(doc_tokens)
    if not keys:
        return 0.0
    
    # Jaccard similarity with frequency weighting
    numerator = sum(min(query_tokens[k], doc_tokens[k]) for k in keys)
    denominator = sum(max(query_tokens[k], doc_tokens[k]) for k in keys)
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator


def ingest_text(name: str, text: str, metadata: Dict[str, Any] = None) -> bool:
    """
    Ingest a text document into the knowledge base.
    
    Args:
        name: Document name (used as filename)
        text: Document content
        metadata: Optional metadata
    
    Returns:
        True if successfully ingested
    """
    try:
        doc = Document(name=name, content=text, metadata=metadata or {})
        
        # Save document
        doc_path = KB / f"{name}.txt"
        doc_path.write_text(text, encoding="utf-8")
        
        # Save metadata
        meta_path = KB / f"{name}.meta.json"
        meta_data = {
            "name": name,
            "timestamp": doc.timestamp,
            "metadata": doc.metadata,
            "token_count": len(_tokenize(text)),
            "char_count": len(text)
        }
        meta_path.write_text(json.dumps(meta_data, indent=2), encoding="utf-8")
        
        return True
    except Exception as e:
        print(f"Failed to ingest document: {e}")
        return False


def query(q: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Query the knowledge base.
    
    Args:
        q: Query string
        top_k: Number of top results to return
    
    Returns:
        List of matching documents with scores
    """
    query_tokens = Counter(_tokenize(q))
    results = []
    
    for doc_path in KB.glob("*.txt"):
        # Skip metadata files
        if ".meta." in doc_path.name:
            continue
        
        try:
            content = doc_path.read_text(encoding="utf-8")
            doc_tokens = Counter(_tokenize(content))
            score = _score(query_tokens, doc_tokens)
            
            # Load metadata if available
            meta_path = doc_path.with_suffix(".meta.json")
            metadata = {}
            if meta_path.exists():
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            
            results.append({
                "name": doc_path.stem,
                "score": score,
                "preview": content[:200] + "..." if len(content) > 200 else content,
                "metadata": metadata
            })
        except Exception as e:
            print(f"Error reading {doc_path}: {e}")
            continue
    
    # Sort by score and return top k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def self_cycle(initial_query: str = None, max_depth: int = 3) -> List[Dict[str, Any]]:
    """
    Perform recursive self-questioning cycle.
    
    Args:
        initial_query: Starting query (or use default)
        max_depth: Maximum recursion depth
    
    Returns:
        List of query-answer pairs from the cycle
    """
    if initial_query is None:
        initial_query = "What is missing for safe evolution of PENIN?"
    
    cycle_results = []
    current_query = initial_query
    
    for depth in range(max_depth):
        # Query knowledge base
        results = query(current_query, top_k=1)
        
        if not results or results[0]["score"] < 0.1:
            # No good match - record and stop
            cycle_results.append({
                "depth": depth,
                "query": current_query,
                "answer": None,
                "score": 0.0,
                "next_query": None
            })
            break
        
        best_result = results[0]
        
        # Generate next query based on result
        # Simple heuristic: ask for details about the first noun phrase
        doc_tokens = _tokenize(best_result.get("preview", ""))
        
        # Find potential topics (consecutive capitalized words or technical terms)
        next_topics = []
        for i, token in enumerate(doc_tokens):
            if len(token) > 4 and token not in ["what", "where", "when", "how", "why"]:
                next_topics.append(token)
                if len(next_topics) >= 3:
                    break
        
        if next_topics:
            next_query = f"Explain implementation details for {' '.join(next_topics[:2])}"
        else:
            next_query = f"What are the next steps after {best_result['name']}?"
        
        cycle_results.append({
            "depth": depth,
            "query": current_query,
            "answer": best_result,
            "score": best_result["score"],
            "next_query": next_query
        })
        
        current_query = next_query
    
    return cycle_results


def extract_concepts(text: str) -> List[str]:
    """Extract key concepts from text"""
    tokens = _tokenize(text)
    
    # Simple concept extraction: find technical terms
    concepts = []
    
    # Look for acronyms (all caps, 2-5 chars)
    acronyms = [t for t in tokens if t.isupper() and 2 <= len(t) <= 5]
    concepts.extend(acronyms)
    
    # Look for compound terms (containing underscore or numbers)
    technical = [t for t in tokens if "_" in t or any(c.isdigit() for c in t)]
    concepts.extend(technical)
    
    # Look for long words (likely technical terms)
    long_terms = [t for t in tokens if len(t) > 10]
    concepts.extend(long_terms[:5])  # Limit to avoid noise
    
    # Deduplicate while preserving order
    seen = set()
    unique_concepts = []
    for c in concepts:
        if c not in seen:
            seen.add(c)
            unique_concepts.append(c)
    
    return unique_concepts


def build_graph() -> Dict[str, List[str]]:
    """
    Build a concept graph from the knowledge base.
    
    Returns:
        Dict mapping concepts to related concepts
    """
    graph = {}
    
    for doc_path in KB.glob("*.txt"):
        if ".meta." in doc_path.name:
            continue
        
        try:
            content = doc_path.read_text(encoding="utf-8")
            concepts = extract_concepts(content)
            
            # Create edges between co-occurring concepts
            for i, c1 in enumerate(concepts):
                if c1 not in graph:
                    graph[c1] = []
                
                for c2 in concepts[i+1:i+5]:  # Window of 5
                    if c2 != c1:
                        graph[c1].append(c2)
                        if c2 not in graph:
                            graph[c2] = []
                        graph[c2].append(c1)
        except:
            continue
    
    # Deduplicate edges
    for concept in graph:
        graph[concept] = list(set(graph[concept]))
    
    return graph


class SelfRAG:
    """High-level Self-RAG orchestrator"""
    
    def __init__(self):
        self.history = []
        self.concept_graph = None
        
    def ingest(self, name: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Ingest new knowledge"""
        success = ingest_text(name, content, metadata)
        if success:
            # Invalidate concept graph cache
            self.concept_graph = None
        return success
    
    def ask(self, question: str) -> Dict[str, Any]:
        """Ask a question and get answer with context"""
        results = query(question, top_k=3)
        
        if not results:
            return {
                "question": question,
                "answer": "No relevant knowledge found",
                "confidence": 0.0,
                "sources": []
            }
        
        # Combine top results
        best = results[0]
        
        # Extract answer (simple: use preview)
        answer = best["preview"]
        
        # Calculate confidence
        confidence = best["score"]
        
        # Get related concepts
        concepts = extract_concepts(question + " " + answer)
        
        # Find related documents
        related = []
        for concept in concepts[:3]:  # Check top 3 concepts
            concept_results = query(concept, top_k=2)
            for r in concept_results:
                if r["name"] not in [res["name"] for res in results]:
                    related.append(r["name"])
        
        response = {
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "sources": [r["name"] for r in results],
            "related": related[:3],
            "concepts": concepts[:5]
        }
        
        # Record in history
        self.history.append({
            "timestamp": time.time(),
            "question": question,
            "answer": answer,
            "confidence": confidence
        })
        
        return response
    
    def explore(self, topic: str = None, depth: int = 3) -> List[Dict[str, Any]]:
        """Explore a topic recursively"""
        if topic is None:
            # Pick a random concept from the graph
            if self.concept_graph is None:
                self.concept_graph = build_graph()
            
            if self.concept_graph:
                import random
                topic = random.choice(list(self.concept_graph.keys()))
            else:
                topic = "PENIN evolution"
        
        return self_cycle(f"Explain {topic} in detail", max_depth=depth)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG statistics"""
        doc_count = len(list(KB.glob("*.txt")))
        
        if self.concept_graph is None:
            self.concept_graph = build_graph()
        
        return {
            "documents": doc_count,
            "concepts": len(self.concept_graph),
            "edges": sum(len(v) for v in self.concept_graph.values()),
            "queries": len(self.history),
            "avg_confidence": (
                sum(h["confidence"] for h in self.history) / len(self.history)
                if self.history else 0.0
            )
        }
    
    def suggest_ingestion(self) -> List[str]:
        """Suggest what knowledge to ingest next"""
        suggestions = []
        
        # Analyze query failures
        failed_queries = [
            h["question"] for h in self.history
            if h.get("confidence", 0) < 0.3
        ]
        
        if failed_queries:
            suggestions.append(f"Add documentation about: {', '.join(failed_queries[:3])}")
        
        # Find isolated concepts
        if self.concept_graph is None:
            self.concept_graph = build_graph()
        
        isolated = [
            c for c, edges in self.concept_graph.items()
            if len(edges) < 2
        ]
        
        if isolated:
            suggestions.append(f"Expand knowledge on: {', '.join(isolated[:3])}")
        
        # Suggest based on age
        old_docs = []
        for meta_path in KB.glob("*.meta.json"):
            try:
                meta = json.loads(meta_path.read_text())
                age_days = (time.time() - meta.get("timestamp", 0)) / 86400
                if age_days > 30:
                    old_docs.append(meta_path.stem.replace(".meta", ""))
            except:
                continue
        
        if old_docs:
            suggestions.append(f"Update old documents: {', '.join(old_docs[:3])}")
        
        return suggestions