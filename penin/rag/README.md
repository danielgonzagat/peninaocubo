# RAG - Self-RAG Retrieval

**Layer**: 2 (Implementations)  
**Purpose**: Hybrid knowledge retrieval  

## Modules

### `retriever.py`
BM25 + embedding hybrid retrieval.
```python
from penin.rag.retriever import HybridRetriever, Document
retriever = HybridRetriever()
retriever.add_documents([doc1, doc2])
results = retriever.search("query", top_k=5)
```

### `self_rag_complete.py` (899 lines)
Complete Self-RAG system.

**See**: [ARCHITECTURE.md](../ARCHITECTURE.md)
