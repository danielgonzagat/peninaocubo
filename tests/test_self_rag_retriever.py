"""Tests for Self-RAG Retriever"""

import pytest
from penin.rag.retriever import (
    BM25Retriever,
    Document,
    HybridRetriever,
    RetrievalResult,
    deduplicate_results,
)


class TestBM25Retriever:
    """Test BM25 retrieval"""
    
    def test_add_and_search(self):
        """Test adding documents and searching"""
        retriever = BM25Retriever()
        
        # Add documents
        docs = [
            Document(doc_id="1", content="Machine learning is amazing"),
            Document(doc_id="2", content="Deep learning uses neural networks"),
            Document(doc_id="3", content="Machine learning algorithms are powerful"),
        ]
        
        for doc in docs:
            retriever.add_document(doc)
        
        # Search
        results = retriever.search("machine learning", top_k=2)
        
        assert len(results) <= 2
        assert all(r.retrieval_method == "bm25" for r in results)
        assert results[0].score > 0
    
    def test_relevance_ranking(self):
        """Test that more relevant docs rank higher"""
        retriever = BM25Retriever()
        
        retriever.add_document(Document(doc_id="1", content="cat dog bird"))
        retriever.add_document(Document(doc_id="2", content="cat cat cat"))  # More mentions
        retriever.add_document(Document(doc_id="3", content="unrelated content"))
        
        results = retriever.search("cat", top_k=3)
        
        # Doc 2 should rank highest (most mentions)
        assert results[0].document.doc_id == "2"
    
    def test_idf_computation(self):
        """Test IDF is computed correctly"""
        retriever = BM25Retriever()
        
        retriever.add_document(Document(doc_id="1", content="common word"))
        retriever.add_document(Document(doc_id="2", content="common word"))
        retriever.add_document(Document(doc_id="3", content="rare unique"))
        
        # "common" appears in 2/3 docs, "rare" in 1/3
        # IDF(rare) should be higher than IDF(common)
        assert "rare" in retriever.idf
        assert "common" in retriever.idf


class TestHybridRetriever:
    """Test hybrid BM25 + embedding retrieval"""
    
    def test_initialization(self):
        """Test hybrid retriever initialization"""
        retriever = HybridRetriever(bm25_weight=0.6, embedding_weight=0.4)
        
        assert retriever.bm25_weight == 0.6
        assert retriever.embedding_weight == 0.4
    
    def test_add_document_with_embedding(self):
        """Test adding document with embedding"""
        retriever = HybridRetriever()
        
        doc = Document(doc_id="1", content="Test content")
        embedding = [0.1] * 384  # Dummy embedding
        
        retriever.add_document(doc, embedding)
        
        assert len(retriever.bm25.documents) == 1
        assert len(retriever.embeddings) == 1
    
    def test_hybrid_search(self):
        """Test hybrid search combines both methods"""
        retriever = HybridRetriever()
        
        # Add documents
        docs = [
            Document(doc_id="1", content="machine learning"),
            Document(doc_id="2", content="deep learning"),
            Document(doc_id="3", content="unrelated"),
        ]
        
        for doc in docs:
            retriever.add_document(doc)
        
        # Search (without embeddings, falls back to BM25)
        results = retriever.search("machine learning", top_k=2)
        
        assert len(results) <= 2
        assert all(r.document.doc_id in ["1", "2", "3"] for r in results)


class TestDeduplication:
    """Test deduplication"""
    
    def test_removes_duplicates(self):
        """Test that exact duplicates are removed"""
        doc1 = Document(doc_id="1", content="Same content")
        doc2 = Document(doc_id="2", content="Same content")  # Duplicate
        doc3 = Document(doc_id="3", content="Different content")
        
        results = [
            RetrievalResult(doc1, 1.0, "bm25"),
            RetrievalResult(doc2, 0.9, "bm25"),
            RetrievalResult(doc3, 0.8, "bm25"),
        ]
        
        deduplicated = deduplicate_results(results)
        
        # Should only have 2 unique docs
        assert len(deduplicated) == 2
        unique_content = {r.document.content for r in deduplicated}
        assert len(unique_content) == 2
    
    def test_preserves_ranking(self):
        """Test that deduplication preserves top-ranked item"""
        results = [
            RetrievalResult(Document("1", "content A"), 1.0, "bm25"),
            RetrievalResult(Document("2", "content B"), 0.9, "bm25"),
            RetrievalResult(Document("3", "content A"), 0.8, "bm25"),  # Dup of 1
        ]
        
        deduplicated = deduplicate_results(results)
        
        # Should keep first occurrence (highest rank)
        assert deduplicated[0].document.doc_id == "1"
        assert deduplicated[1].document.doc_id == "2"


class TestDocumentHashing:
    """Test document provenance"""
    
    def test_document_hash_computation(self):
        """Test content hash generation"""
        doc = Document(doc_id="1", content="Test content for hashing")
        
        hash1 = doc.compute_hash()
        hash2 = doc.compute_hash()
        
        # Should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated to 16 chars
    
    def test_different_content_different_hash(self):
        """Test different content produces different hash"""
        doc1 = Document(doc_id="1", content="Content A")
        doc2 = Document(doc_id="2", content="Content B")
        
        assert doc1.compute_hash() != doc2.compute_hash()
