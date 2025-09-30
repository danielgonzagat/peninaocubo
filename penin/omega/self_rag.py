"""
Self-RAG Recursive System
=========================

Implements recursive self-RAG for knowledge ingestion and querying.
Uses simple token-based similarity for document retrieval.
"""

import re
import json
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class DocumentType(Enum):
    """Document types"""
    TEXT = "text"
    CODE = "code"
    CONFIG = "config"
    LOG = "log"
    METRIC = "metric"


@dataclass
class Document:
    """Document structure"""
    name: str
    content: str
    doc_type: DocumentType
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "content": self.content,
            "doc_type": self.doc_type.value,
            "created_at": self.created_at,
            "metadata": self.metadata
        }


class SelfRAG:
    """Self-RAG implementation"""
    
    def __init__(self, knowledge_path: Optional[str] = None):
        if knowledge_path is None:
            root_path = Path.home() / ".penin_omega" / "knowledge"
            root_path.mkdir(parents=True, exist_ok=True)
            self.knowledge_path = root_path
        else:
            self.knowledge_path = Path(knowledge_path)
            self.knowledge_path.mkdir(parents=True, exist_ok=True)
        
        self.documents: Dict[str, Document] = {}
        self.token_index: Dict[str, List[str]] = {}  # token -> document names
        self.query_history: List[Dict[str, Any]] = []
        
        # Load existing documents
        self._load_documents()
    
    def _load_documents(self) -> None:
        """Load existing documents from knowledge path"""
        for file_path in self.knowledge_path.glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                doc_name = file_path.stem
                doc = Document(
                    name=doc_name,
                    content=content,
                    doc_type=DocumentType.TEXT
                )
                
                self.documents[doc_name] = doc
                self._index_document(doc)
                
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # Extract words and numbers
        tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
        return [t for t in tokens if len(t) > 1]  # Filter single characters
    
    def _index_document(self, doc: Document) -> None:
        """Index document tokens"""
        tokens = self._tokenize(doc.content)
        
        for token in tokens:
            if token not in self.token_index:
                self.token_index[token] = []
            if doc.name not in self.token_index[token]:
                self.token_index[token].append(doc.name)
    
    def ingest_text(self, name: str, text: str, doc_type: DocumentType = DocumentType.TEXT, 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Ingest text document
        
        Args:
            name: Document name
            text: Document content
            doc_type: Type of document
            metadata: Optional metadata
            
        Returns:
            Success status
        """
        try:
            # Create document
            doc = Document(
                name=name,
                content=text,
                doc_type=doc_type,
                metadata=metadata or {}
            )
            
            # Store document
            self.documents[name] = doc
            
            # Index tokens
            self._index_document(doc)
            
            # Save to file
            file_path = self.knowledge_path / f"{name}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return True
            
        except Exception as e:
            print(f"Error ingesting {name}: {e}")
            return False
    
    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Query documents using token similarity
        
        Args:
            query_text: Query text
            top_k: Number of top results to return
            
        Returns:
            List of matching documents with scores
        """
        query_tokens = self._tokenize(query_text)
        query_counter = Counter(query_tokens)
        
        # Score documents
        doc_scores = {}
        
        for doc_name, doc in self.documents.items():
            doc_tokens = self._tokenize(doc.content)
            doc_counter = Counter(doc_tokens)
            
            # Calculate similarity score
            score = self._calculate_similarity(query_counter, doc_counter)
            doc_scores[doc_name] = {
                "score": score,
                "document": doc.to_dict(),
                "matched_tokens": list(set(query_tokens) & set(doc_tokens))
            }
        
        # Sort by score and return top_k
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        results = []
        for doc_name, doc_data in sorted_docs[:top_k]:
            if doc_data["score"] > 0:
                results.append({
                    "doc_name": doc_name,
                    "score": doc_data["score"],
                    "content_preview": doc_data["document"]["content"][:200] + "...",
                    "matched_tokens": doc_data["matched_tokens"],
                    "doc_type": doc_data["document"]["doc_type"]
                })
        
        # Record query
        self.query_history.append({
            "query": query_text,
            "timestamp": time.time(),
            "results_count": len(results),
            "top_score": results[0]["score"] if results else 0.0
        })
        
        return results
    
    def _calculate_similarity(self, query_tokens: Counter, doc_tokens: Counter) -> float:
        """Calculate similarity between query and document tokens"""
        if not query_tokens or not doc_tokens:
            return 0.0
        
        # Jaccard similarity
        intersection = sum(min(query_tokens[token], doc_tokens[token]) for token in query_tokens)
        union = sum(max(query_tokens[token], doc_tokens[token]) for token in query_tokens)
        
        # Add tokens from doc that aren't in query
        for token in doc_tokens:
            if token not in query_tokens:
                union += doc_tokens[token]
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def self_cycle(self, base_question: str = "What is missing for safe evolution?") -> Dict[str, Any]:
        """
        Perform self-RAG cycle
        
        Args:
            base_question: Initial question
            
        Returns:
            Cycle results
        """
        # Step 1: Query for base question
        initial_results = self.query(base_question, top_k=2)
        
        if not initial_results:
            return {
                "q1": base_question,
                "a1": None,
                "q2": None,
                "cycle_complete": False,
                "reason": "no_documents_found"
            }
        
        # Step 2: Generate follow-up question based on best result
        best_doc = initial_results[0]
        follow_up_question = f"Detail the implementation requirements mentioned in {best_doc['doc_name']}"
        
        # Step 3: Query for follow-up
        follow_up_results = self.query(follow_up_question, top_k=2)
        
        # Step 4: Generate insights
        insights = self._generate_insights(initial_results, follow_up_results)
        
        return {
            "q1": base_question,
            "a1": initial_results,
            "q2": follow_up_question,
            "a2": follow_up_results,
            "insights": insights,
            "cycle_complete": True
        }
    
    def _generate_insights(self, results1: List[Dict[str, Any]], 
                          results2: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from query results"""
        insights = []
        
        # Analyze common themes
        all_tokens = set()
        for result in results1 + results2:
            all_tokens.update(result.get("matched_tokens", []))
        
        if all_tokens:
            insights.append(f"Common themes: {', '.join(sorted(all_tokens)[:5])}")
        
        # Analyze document types
        doc_types = [r.get("doc_type", "unknown") for r in results1 + results2]
        type_counts = Counter(doc_types)
        if type_counts:
            insights.append(f"Document types found: {dict(type_counts)}")
        
        # Analyze scores
        scores = [r.get("score", 0) for r in results1 + results2]
        if scores:
            avg_score = sum(scores) / len(scores)
            insights.append(f"Average relevance score: {avg_score:.3f}")
        
        return insights
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            "total_documents": len(self.documents),
            "total_tokens": len(self.token_index),
            "total_queries": len(self.query_history),
            "document_types": dict(Counter(doc.doc_type.value for doc in self.documents.values())),
            "recent_queries": self.query_history[-5:] if self.query_history else []
        }
    
    def search_documents(self, keyword: str) -> List[str]:
        """Search documents by keyword"""
        keyword_lower = keyword.lower()
        matching_docs = []
        
        for token, doc_names in self.token_index.items():
            if keyword_lower in token:
                matching_docs.extend(doc_names)
        
        return list(set(matching_docs))
    
    def export_knowledge(self, filepath: str) -> None:
        """Export knowledge base"""
        export_data = {
            "exported_at": time.time(),
            "documents": {name: doc.to_dict() for name, doc in self.documents.items()},
            "query_history": self.query_history,
            "stats": self.get_knowledge_stats()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
    
    def clear_knowledge(self) -> None:
        """Clear knowledge base"""
        self.documents.clear()
        self.token_index.clear()
        self.query_history.clear()
        
        # Remove files
        for file_path in self.knowledge_path.glob("*.txt"):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Warning: Failed to remove {file_path}: {e}")


# Global self-RAG instance
_global_rag: Optional[SelfRAG] = None


def get_global_rag() -> SelfRAG:
    """Get global self-RAG instance"""
    global _global_rag
    
    if _global_rag is None:
        _global_rag = SelfRAG()
    
    return _global_rag


def ingest_text(name: str, text: str, doc_type: DocumentType = DocumentType.TEXT) -> bool:
    """Convenience function to ingest text"""
    rag = get_global_rag()
    return rag.ingest_text(name, text, doc_type)


def query(q: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Convenience function to query"""
    rag = get_global_rag()
    return rag.query(q, top_k)


def self_cycle() -> Dict[str, Any]:
    """Convenience function for self-cycle"""
    rag = get_global_rag()
    return rag.self_cycle()


def test_self_rag() -> Dict[str, Any]:
    """Test self-RAG functionality"""
    rag = get_global_rag()
    
    # Clear existing knowledge
    rag.clear_knowledge()
    
    # Ingest test documents
    doc1_content = """
    PENIN-Ω evolution requires careful monitoring of CAOS+ metrics.
    The Life Equation (+) provides non-compensatory gates for safe evolution.
    Sigma Guard ensures ethical compliance with ECE <= 0.01.
    """
    
    doc2_content = """
    Implementation checklist:
    1. Life Equation (+) integration
    2. Fractal DSL propagation
    3. Swarm cognitive gossip
    4. Neural blockchain integrity
    5. Self-RAG knowledge base
    """
    
    doc3_content = """
    Safety requirements:
    - Fail-closed behavior
    - Non-compensatory gates
    - WORM ledger integrity
    - Merkle hash validation
    - Zero-consciousness proof
    """
    
    rag.ingest_text("evolution_guide", doc1_content)
    rag.ingest_text("implementation_checklist", doc2_content)
    rag.ingest_text("safety_requirements", doc3_content)
    
    # Test queries
    q1_results = rag.query("What is needed for safe evolution?", top_k=2)
    q2_results = rag.query("implementation requirements", top_k=2)
    
    # Test self-cycle
    cycle_result = rag.self_cycle("What are the key safety requirements?")
    
    # Get stats
    stats = rag.get_knowledge_stats()
    
    return {
        "documents_ingested": 3,
        "query1_results": q1_results,
        "query2_results": q2_results,
        "self_cycle_result": cycle_result,
        "knowledge_stats": stats
    }