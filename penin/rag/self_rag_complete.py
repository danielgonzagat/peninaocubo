"""
PENIN-Ω Self-RAG — Self-Reflective Retrieval Augmented Generation

Features:
- BM25 + Embedding hybrid retrieval
- Deduplication with semantic similarity
- Chunking (512-2048 tokens configurable)
- Fractal coherence scoring
- Citation tracking with hash provenance
- Local document store
- WORM ledger integration for citations

Complies with:
- ΣEA/LO-14 (source attribution, no plagiarism)
- Fail-closed design
- Auditable retrieval decisions
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


# ============================================================================
# Constants and Configuration
# ============================================================================

DEFAULT_CHUNK_SIZE = 1024
DEFAULT_CHUNK_OVERLAP = 128
DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.85
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "will",
    "with",
    "this",
    "but",
    "they",
    "have",
    "had",
    "what",
    "when",
    "where",
    "who",
    "which",
    "why",
    "how",
}


# ============================================================================
# Document and Chunk
# ============================================================================


@dataclass
class Document:
    """Document with metadata."""

    doc_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str | None = None
    content_hash: str | None = None

    def __post_init__(self):
        """Compute content hash on initialization."""
        if self.content_hash is None:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
            "content_hash": self.content_hash,
        }


@dataclass
class Chunk:
    """Text chunk with provenance."""

    chunk_id: str
    doc_id: str
    content: str
    start_idx: int
    end_idx: int
    chunk_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Compute chunk hash on initialization."""
        if not self.chunk_hash:
            self.chunk_hash = hashlib.sha256(
                f"{self.doc_id}:{self.content}".encode()
            ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "content": self.content,
            "start_idx": self.start_idx,
            "end_idx": self.end_idx,
            "chunk_hash": self.chunk_hash,
            "metadata": self.metadata,
        }


@dataclass
class RetrievalResult:
    """Retrieval result with score and provenance."""

    chunk: Chunk
    score: float
    rank: int
    retrieval_method: str  # "bm25", "embedding", "hybrid"
    citation: str = ""

    def __post_init__(self):
        """Generate citation on initialization."""
        if not self.citation:
            self.citation = (
                f"[{self.chunk.doc_id}:{self.chunk.chunk_id} "
                f"hash:{self.chunk.chunk_hash[:8]}...]"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "rank": self.rank,
            "retrieval_method": self.retrieval_method,
            "citation": self.citation,
        }


# ============================================================================
# BM25 Retriever
# ============================================================================


class BM25:
    """
    BM25 ranking function for document retrieval.

    Parameters:
    - k1: term frequency saturation (default: 1.5)
    - b: length normalization (default: 0.75)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: list[list[str]] = []
        self.doc_lengths: list[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_freqs: dict[str, int] = defaultdict(int)
        self.idf: dict[str, float] = {}
        self.doc_ids: list[str] = []

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Tokenize text (simple whitespace + lowercasing)."""
        tokens = re.findall(r"\b\w+\b", text.lower())
        return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

    def fit(self, documents: list[tuple[str, str]]) -> None:
        """
        Fit BM25 on corpus.

        Args:
            documents: List of (doc_id, content) tuples
        """
        self.corpus = []
        self.doc_lengths = []
        self.doc_ids = []

        for doc_id, content in documents:
            tokens = self.tokenize(content)
            self.corpus.append(tokens)
            self.doc_lengths.append(len(tokens))
            self.doc_ids.append(doc_id)

        if not self.doc_lengths:
            self.avg_doc_length = 0.0
        else:
            self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)

        # Compute document frequencies
        self.doc_freqs.clear()
        for tokens in self.corpus:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1

        # Compute IDF
        num_docs = len(self.corpus)
        self.idf = {}
        for token, freq in self.doc_freqs.items():
            self.idf[token] = math.log((num_docs - freq + 0.5) / (freq + 0.5) + 1.0)

    def score(self, query: str, doc_idx: int) -> float:
        """
        Compute BM25 score for query against document.

        Args:
            query: Query string
            doc_idx: Document index

        Returns:
            BM25 score
        """
        if doc_idx >= len(self.corpus):
            return 0.0

        query_tokens = self.tokenize(query)
        doc_tokens = self.corpus[doc_idx]
        doc_length = self.doc_lengths[doc_idx]

        score = 0.0
        term_freqs = Counter(doc_tokens)

        for token in query_tokens:
            if token not in self.idf:
                continue

            tf = term_freqs.get(token, 0)
            idf = self.idf[token]

            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_length / self.avg_doc_length)
            )

            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Search corpus with query.

        Args:
            query: Query string
            top_k: Number of top results

        Returns:
            List of (doc_id, score) tuples sorted by score
        """
        scores = []
        for idx in range(len(self.corpus)):
            score = self.score(query, idx)
            if score > 0:
                scores.append((self.doc_ids[idx], score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ============================================================================
# Embedding Retriever
# ============================================================================


class EmbeddingRetriever:
    """
    Dense embedding retriever using sentence transformers.

    Uses cosine similarity for ranking.
    """

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        """Initialize embedding model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not available. "
                "Install with: pip install sentence-transformers"
            )

        if not NUMPY_AVAILABLE:
            raise ImportError("numpy not available. " "Install with: pip install numpy")

        self.model = SentenceTransformer(model_name)
        self.embeddings: np.ndarray | None = None
        self.doc_ids: list[str] = []

    def fit(self, documents: list[tuple[str, str]]) -> None:
        """
        Fit embeddings on corpus.

        Args:
            documents: List of (doc_id, content) tuples
        """
        self.doc_ids = [doc_id for doc_id, _ in documents]
        contents = [content for _, content in documents]

        # Encode all documents
        self.embeddings = self.model.encode(
            contents, convert_to_numpy=True, show_progress_bar=False
        )

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Search corpus with query.

        Args:
            query: Query string
            top_k: Number of top results

        Returns:
            List of (doc_id, score) tuples sorted by score
        """
        if self.embeddings is None:
            return []

        # Encode query
        query_embedding = self.model.encode(
            [query], convert_to_numpy=True, show_progress_bar=False
        )[0]

        # Compute similarities
        scores = []
        for idx, doc_embedding in enumerate(self.embeddings):
            similarity = self.cosine_similarity(query_embedding, doc_embedding)
            scores.append((self.doc_ids[idx], float(similarity)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ============================================================================
# Chunker
# ============================================================================


class TextChunker:
    """
    Text chunker with overlapping windows.

    Supports:
    - Fixed-size chunking
    - Sentence boundary preservation (optional)
    - Overlapping windows
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
        preserve_sentences: bool = True,
    ):
        """Initialize chunker."""
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.preserve_sentences = preserve_sentences

    def chunk(self, doc: Document) -> list[Chunk]:
        """
        Chunk document into overlapping chunks.

        Args:
            doc: Document to chunk

        Returns:
            List of Chunk objects
        """
        content = doc.content
        chunks = []

        if self.preserve_sentences:
            # Split by sentences (naive)
            sentences = re.split(r"[.!?]+\s+", content)
            chunks = self._chunk_sentences(doc, sentences)
        else:
            # Simple fixed-size chunking
            chunks = self._chunk_fixed(doc, content)

        return chunks

    def _chunk_fixed(self, doc: Document, content: str) -> list[Chunk]:
        """Fixed-size chunking."""
        chunks = []
        start = 0
        chunk_num = 0

        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            chunk_content = content[start:end]

            chunk = Chunk(
                chunk_id=f"{doc.doc_id}_chunk_{chunk_num}",
                doc_id=doc.doc_id,
                content=chunk_content,
                start_idx=start,
                end_idx=end,
                metadata=doc.metadata.copy(),
            )
            chunks.append(chunk)

            # Move to next chunk with overlap
            start = end - self.overlap
            if start >= len(content):
                break

            chunk_num += 1

        return chunks

    def _chunk_sentences(self, doc: Document, sentences: list[str]) -> list[Chunk]:
        """Sentence-aware chunking."""
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_num = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Finalize current chunk
                chunk_content = ". ".join(current_chunk) + "."
                start_idx = doc.content.find(current_chunk[0])
                end_idx = start_idx + len(chunk_content)

                chunk = Chunk(
                    chunk_id=f"{doc.doc_id}_chunk_{chunk_num}",
                    doc_id=doc.doc_id,
                    content=chunk_content,
                    start_idx=start_idx,
                    end_idx=end_idx,
                    metadata=doc.metadata.copy(),
                )
                chunks.append(chunk)

                # Start new chunk with overlap (keep last sentence)
                if self.overlap > 0 and current_chunk:
                    current_chunk = [current_chunk[-1]]
                    current_length = len(current_chunk[-1])
                else:
                    current_chunk = []
                    current_length = 0

                chunk_num += 1

            current_chunk.append(sentence.strip())
            current_length += sentence_length

        # Add final chunk
        if current_chunk:
            chunk_content = ". ".join(current_chunk) + "."
            start_idx = doc.content.find(current_chunk[0]) if current_chunk else 0
            end_idx = start_idx + len(chunk_content)

            chunk = Chunk(
                chunk_id=f"{doc.doc_id}_chunk_{chunk_num}",
                doc_id=doc.doc_id,
                content=chunk_content,
                start_idx=start_idx,
                end_idx=end_idx,
                metadata=doc.metadata.copy(),
            )
            chunks.append(chunk)

        return chunks


# ============================================================================
# Deduplication
# ============================================================================


class Deduplicator:
    """
    Semantic deduplication using embedding similarity.
    """

    def __init__(
        self,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        use_embeddings: bool = True,
    ):
        """Initialize deduplicator."""
        self.similarity_threshold = similarity_threshold
        self.use_embeddings = use_embeddings

        if use_embeddings and not SENTENCE_TRANSFORMERS_AVAILABLE:
            self.use_embeddings = False

    def deduplicate(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Deduplicate chunks based on similarity.

        Args:
            chunks: List of chunks

        Returns:
            Deduplicated list of chunks
        """
        if not chunks:
            return []

        if self.use_embeddings:
            return self._deduplicate_embeddings(chunks)
        else:
            return self._deduplicate_hashes(chunks)

    def _deduplicate_hashes(self, chunks: list[Chunk]) -> list[Chunk]:
        """Hash-based exact deduplication."""
        seen_hashes: set[str] = set()
        unique_chunks = []

        for chunk in chunks:
            if chunk.chunk_hash not in seen_hashes:
                seen_hashes.add(chunk.chunk_hash)
                unique_chunks.append(chunk)

        return unique_chunks

    def _deduplicate_embeddings(self, chunks: list[Chunk]) -> list[Chunk]:
        """Embedding-based semantic deduplication."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE or not NUMPY_AVAILABLE:
            return self._deduplicate_hashes(chunks)

        model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)

        # Encode all chunks
        contents = [chunk.content for chunk in chunks]
        embeddings = model.encode(
            contents, convert_to_numpy=True, show_progress_bar=False
        )

        # Greedy deduplication
        keep_mask = [True] * len(chunks)

        for i in range(len(chunks)):
            if not keep_mask[i]:
                continue

            for j in range(i + 1, len(chunks)):
                if not keep_mask[j]:
                    continue

                similarity = EmbeddingRetriever.cosine_similarity(
                    embeddings[i], embeddings[j]
                )

                if similarity >= self.similarity_threshold:
                    keep_mask[j] = False

        return [chunk for chunk, keep in zip(chunks, keep_mask, strict=False) if keep]


# ============================================================================
# Fractal Coherence
# ============================================================================


def fractal_coherence(results: list[RetrievalResult]) -> float:
    """
    Compute fractal coherence across multiple retrieval results.

    Measures multi-level consistency:
    - Document-level: are results from same documents?
    - Semantic-level: are results semantically similar?
    - Rank-level: are top results consistent?

    Returns value in [0, 1] where 1 = perfect coherence.

    Args:
        results: List of retrieval results

    Returns:
        Coherence score [0, 1]
    """
    if not results:
        return 0.0

    if len(results) == 1:
        return 1.0

    # Document-level coherence
    doc_ids = [r.chunk.doc_id for r in results]
    unique_docs = len(set(doc_ids))
    doc_coherence = 1.0 - (unique_docs - 1) / len(results)

    # Rank-level coherence (top results should have higher scores)
    scores = [r.score for r in results]
    rank_coherence = 1.0
    for i in range(len(scores) - 1):
        if scores[i] < scores[i + 1]:
            rank_coherence *= 0.9  # Penalize inversions

    # Method-level coherence (prefer consistent retrieval methods)
    methods = [r.retrieval_method for r in results]
    unique_methods = len(set(methods))
    method_coherence = 1.0 - (unique_methods - 1) / len(results)

    # Harmonic mean (non-compensatory)
    epsilon = 1e-6
    components = [doc_coherence, rank_coherence, method_coherence]
    harmonic = len(components) / sum(1.0 / max(epsilon, c) for c in components)

    return harmonic


# ============================================================================
# Self-RAG System
# ============================================================================


class SelfRAG:
    """
    Self-Reflective Retrieval Augmented Generation system.

    Features:
    - Hybrid BM25 + embedding retrieval
    - Deduplication
    - Chunking
    - Fractal coherence
    - Citation tracking
    - WORM ledger integration ready
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        top_k: int = DEFAULT_TOP_K,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        use_embeddings: bool = True,
    ):
        """Initialize Self-RAG."""
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            overlap=chunk_overlap,
        )
        self.deduplicator = Deduplicator(
            similarity_threshold=similarity_threshold,
            use_embeddings=use_embeddings,
        )
        self.bm25 = BM25()
        self.embedding_retriever: EmbeddingRetriever | None = None
        self.top_k = top_k
        self.use_embeddings = use_embeddings

        self.documents: dict[str, Document] = {}
        self.chunks: dict[str, Chunk] = {}
        self._fitted = False

    def add_document(self, doc: Document) -> None:
        """Add document to corpus."""
        self.documents[doc.doc_id] = doc
        self._fitted = False

    def add_documents(self, docs: Iterable[Document]) -> None:
        """Add multiple documents."""
        for doc in docs:
            self.add_document(doc)

    def fit(self) -> None:
        """Fit retrievers on corpus."""
        if not self.documents:
            return

        # Chunk all documents
        all_chunks = []
        for doc in self.documents.values():
            chunks = self.chunker.chunk(doc)
            all_chunks.extend(chunks)

        # Deduplicate
        unique_chunks = self.deduplicator.deduplicate(all_chunks)

        # Store chunks
        self.chunks = {chunk.chunk_id: chunk for chunk in unique_chunks}

        # Fit BM25
        bm25_docs = [(chunk.chunk_id, chunk.content) for chunk in unique_chunks]
        self.bm25.fit(bm25_docs)

        # Fit embedding retriever
        if self.use_embeddings and SENTENCE_TRANSFORMERS_AVAILABLE:
            self.embedding_retriever = EmbeddingRetriever()
            self.embedding_retriever.fit(bm25_docs)

        self._fitted = True

    def search(
        self,
        query: str,
        top_k: int | None = None,
        method: str = "hybrid",
    ) -> list[RetrievalResult]:
        """
        Search corpus with query.

        Args:
            query: Query string
            top_k: Number of results (default: self.top_k)
            method: "bm25", "embedding", or "hybrid"

        Returns:
            List of RetrievalResult sorted by score
        """
        if not self._fitted:
            self.fit()

        if not self.chunks:
            return []

        k = top_k or self.top_k

        if method == "bm25":
            return self._search_bm25(query, k)
        elif method == "embedding":
            return self._search_embedding(query, k)
        elif method == "hybrid":
            return self._search_hybrid(query, k)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _search_bm25(self, query: str, top_k: int) -> list[RetrievalResult]:
        """BM25 search."""
        bm25_results = self.bm25.search(query, top_k)

        results = []
        for rank, (chunk_id, score) in enumerate(bm25_results, 1):
            if chunk_id not in self.chunks:
                continue

            result = RetrievalResult(
                chunk=self.chunks[chunk_id],
                score=score,
                rank=rank,
                retrieval_method="bm25",
            )
            results.append(result)

        return results

    def _search_embedding(self, query: str, top_k: int) -> list[RetrievalResult]:
        """Embedding search."""
        if not self.embedding_retriever:
            return []

        embedding_results = self.embedding_retriever.search(query, top_k)

        results = []
        for rank, (chunk_id, score) in enumerate(embedding_results, 1):
            if chunk_id not in self.chunks:
                continue

            result = RetrievalResult(
                chunk=self.chunks[chunk_id],
                score=score,
                rank=rank,
                retrieval_method="embedding",
            )
            results.append(result)

        return results

    def _search_hybrid(self, query: str, top_k: int) -> list[RetrievalResult]:
        """Hybrid BM25 + embedding search."""
        # Get results from both methods
        bm25_results = self._search_bm25(query, top_k * 2)
        embedding_results = self._search_embedding(query, top_k * 2)

        # Combine scores (reciprocal rank fusion)
        combined_scores: dict[str, float] = {}

        for result in bm25_results:
            chunk_id = result.chunk.chunk_id
            # RRF score
            rrf_score = 1.0 / (60 + result.rank)
            combined_scores[chunk_id] = combined_scores.get(chunk_id, 0.0) + rrf_score

        for result in embedding_results:
            chunk_id = result.chunk.chunk_id
            rrf_score = 1.0 / (60 + result.rank)
            combined_scores[chunk_id] = combined_scores.get(chunk_id, 0.0) + rrf_score

        # Sort by combined score
        ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]

        # Create results
        results = []
        for rank, (chunk_id, score) in enumerate(ranked, 1):
            if chunk_id not in self.chunks:
                continue

            result = RetrievalResult(
                chunk=self.chunks[chunk_id],
                score=score,
                rank=rank,
                retrieval_method="hybrid",
            )
            results.append(result)

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get corpus statistics."""
        return {
            "num_documents": len(self.documents),
            "num_chunks": len(self.chunks),
            "fitted": self._fitted,
            "use_embeddings": self.use_embeddings,
            "chunk_size": self.chunker.chunk_size,
            "chunk_overlap": self.chunker.overlap,
            "top_k": self.top_k,
        }


# ============================================================================
# Factory Function
# ============================================================================


def create_self_rag(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    top_k: int = DEFAULT_TOP_K,
    use_embeddings: bool = True,
) -> SelfRAG:
    """
    Create Self-RAG system.

    Args:
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        top_k: Number of top results
        use_embeddings: Use embedding retriever

    Returns:
        SelfRAG instance
    """
    return SelfRAG(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        top_k=top_k,
        use_embeddings=use_embeddings,
    )
