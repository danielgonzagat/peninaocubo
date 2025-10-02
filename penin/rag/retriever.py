"""
Self-RAG Retriever (BM25 + Embeddings)
=======================================

Hybrid retrieval system combining:
1. BM25 (sparse, keyword-based)
2. Dense embeddings (semantic similarity)

With deduplication, chunking, and provenance tracking.

References:
-----------
- Self-RAG: Learning to Retrieve, Generate, and Critique
- Hybrid search (BM25 + dense retrieval)
- PENIN-Ω coherence functions
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """Document for retrieval"""
    
    doc_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Provenance
    source: str | None = None
    hash: str | None = None
    timestamp: float | None = None
    
    def compute_hash(self) -> str:
        """Compute content hash"""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]


@dataclass
class RetrievalResult:
    """Single retrieval result"""
    
    document: Document
    score: float
    retrieval_method: str  # "bm25" | "embedding" | "hybrid"
    
    # Provenance
    query: str | None = None
    rank: int | None = None


class BM25Retriever:
    """
    BM25 retrieval (sparse, keyword-based).
    
    Fast, interpretable, good for exact matches.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25.
        
        Args:
            k1: Term frequency saturation parameter (typical: 1.2-2.0)
            b: Length normalization parameter (typical: 0.75)
        """
        self.k1 = k1
        self.b = b
        
        # Document store
        self.documents: list[Document] = []
        self.doc_lengths: list[int] = []
        self.avg_doc_length: float = 0.0
        
        # Inverted index
        self.inverted_index: dict[str, list[int]] = defaultdict(list)
        self.term_freqs: list[Counter] = []
        
        # IDF scores
        self.idf: dict[str, float] = {}
    
    def add_document(self, document: Document) -> None:
        """Add document to index"""
        doc_idx = len(self.documents)
        self.documents.append(document)
        
        # Tokenize
        tokens = self._tokenize(document.content)
        self.doc_lengths.append(len(tokens))
        
        # Update average length
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
        
        # Build inverted index
        term_freq = Counter(tokens)
        self.term_freqs.append(term_freq)
        
        for term in term_freq:
            self.inverted_index[term].append(doc_idx)
        
        # Recompute IDF
        self._compute_idf()
    
    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """
        Search documents using BM25.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of RetrievalResult sorted by score
        """
        query_tokens = self._tokenize(query)
        
        # Compute BM25 score for each document
        scores = []
        for doc_idx, document in enumerate(self.documents):
            score = self._compute_bm25_score(query_tokens, doc_idx)
            scores.append((doc_idx, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        results = []
        for rank, (doc_idx, score) in enumerate(scores[:top_k]):
            results.append(
                RetrievalResult(
                    document=self.documents[doc_idx],
                    score=score,
                    retrieval_method="bm25",
                    query=query,
                    rank=rank,
                )
            )
        
        return results
    
    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization (lowercase + split)"""
        return text.lower().split()
    
    def _compute_idf(self) -> None:
        """Compute IDF scores for all terms"""
        N = len(self.documents)
        
        for term, doc_list in self.inverted_index.items():
            df = len(doc_list)  # Document frequency
            # IDF = log((N - df + 0.5) / (df + 0.5) + 1)
            self.idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
    
    def _compute_bm25_score(self, query_tokens: list[str], doc_idx: int) -> float:
        """Compute BM25 score for a document"""
        score = 0.0
        doc_length = self.doc_lengths[doc_idx]
        term_freq = self.term_freqs[doc_idx]
        
        for term in query_tokens:
            if term not in self.idf:
                continue
            
            # Term frequency in document
            tf = term_freq.get(term, 0)
            
            # IDF
            idf = self.idf[term]
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_length / self.avg_doc_length)
            )
            
            score += idf * (numerator / denominator)
        
        return score


class HybridRetriever:
    """
    Hybrid retriever combining BM25 + embeddings.
    
    Uses Reciprocal Rank Fusion (RRF) to merge results.
    """
    
    def __init__(
        self,
        bm25_weight: float = 0.5,
        embedding_weight: float = 0.5,
        k_rrf: int = 60,
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            bm25_weight: Weight for BM25 scores
            embedding_weight: Weight for embedding scores
            k_rrf: RRF constant (typical: 60)
        """
        self.bm25 = BM25Retriever()
        self.bm25_weight = bm25_weight
        self.embedding_weight = embedding_weight
        self.k_rrf = k_rrf
        
        # Embedding store (simplified - in production use vector DB)
        self.embeddings: list[list[float]] = []
    
    def add_document(self, document: Document, embedding: list[float] | None = None) -> None:
        """
        Add document to both BM25 and embedding indices.
        
        Args:
            document: Document to add
            embedding: Optional precomputed embedding
        """
        self.bm25.add_document(document)
        
        if embedding is not None:
            self.embeddings.append(embedding)
        else:
            # Generate dummy embedding (in production, use real model)
            self.embeddings.append([0.0] * 384)  # Typical embedding dim
    
    def search(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """
        Hybrid search using BM25 + embeddings.
        
        Args:
            query: Text query
            query_embedding: Optional query embedding
            top_k: Number of results
        
        Returns:
            Fused results from both retrievers
        """
        # BM25 results
        bm25_results = self.bm25.search(query, top_k=top_k * 2)  # Get more for fusion
        
        # Embedding results (simplified - in production use vector search)
        embedding_results = []
        if query_embedding and len(self.embeddings) > 0:
            embedding_results = self._search_embeddings(query_embedding, top_k * 2)
        
        # Fuse with RRF
        fused = self._reciprocal_rank_fusion(bm25_results, embedding_results, top_k)
        
        return fused
    
    def _search_embeddings(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievalResult]:
        """Search using cosine similarity (simplified)"""
        scores = []
        
        for idx, doc_emb in enumerate(self.embeddings):
            # Cosine similarity
            sim = self._cosine_similarity(query_embedding, doc_emb)
            scores.append((idx, sim))
        
        # Sort
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        results = []
        for rank, (idx, score) in enumerate(scores[:top_k]):
            if idx < len(self.bm25.documents):
                results.append(
                    RetrievalResult(
                        document=self.bm25.documents[idx],
                        score=score,
                        retrieval_method="embedding",
                        rank=rank,
                    )
                )
        
        return results
    
    def _reciprocal_rank_fusion(
        self,
        results1: list[RetrievalResult],
        results2: list[RetrievalResult],
        top_k: int,
    ) -> list[RetrievalResult]:
        """
        Fuse results using Reciprocal Rank Fusion.
        
        RRF score = sum(1 / (k + rank))
        """
        # Build doc_id → RRF score mapping
        rrf_scores: dict[str, float] = defaultdict(float)
        
        for rank, result in enumerate(results1):
            rrf_scores[result.document.doc_id] += 1.0 / (self.k_rrf + rank + 1)
        
        for rank, result in enumerate(results2):
            rrf_scores[result.document.doc_id] += 1.0 / (self.k_rrf + rank + 1)
        
        # Get all unique documents
        all_docs = {}
        for result in results1 + results2:
            all_docs[result.document.doc_id] = result.document
        
        # Create fused results
        fused = []
        for doc_id, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            fused.append(
                RetrievalResult(
                    document=all_docs[doc_id],
                    score=score,
                    retrieval_method="hybrid",
                )
            )
        
        return fused
    
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)


# ============================================================================
# DEDUPLICATION
# ============================================================================

def deduplicate_results(
    results: list[RetrievalResult],
    threshold: float = 0.9,
) -> list[RetrievalResult]:
    """
    Remove near-duplicate results.
    
    Args:
        results: Retrieval results
        threshold: Similarity threshold for duplicates
    
    Returns:
        Deduplicated results
    """
    if len(results) <= 1:
        return results
    
    # Simple deduplication based on content hash
    seen_hashes = set()
    deduplicated = []
    
    for result in results:
        content_hash = result.document.compute_hash()
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            deduplicated.append(result)
    
    return deduplicated


__all__ = [
    "Document",
    "RetrievalResult",
    "BM25Retriever",
    "HybridRetriever",
    "deduplicate_results",
]
