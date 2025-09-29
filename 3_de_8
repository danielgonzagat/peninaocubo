#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENIN-Ω v7.0 FUSION SUPREMA - CÓDIGO 3/8: Aquisição de Conhecimento & Contexto
================================================================================
Subsistema de Aquisição com RAG + TTD-DR + Debate Multi-IA
Integração Simbiótica com 1/8 (Núcleo) e 2/8 (Estratégia)

MISSÃO COMPLETA:
- Transforma PlanΩ (2/8) em conhecimento novo e contextualizado
- Gera perguntas acionáveis via TTD-DR (Task-To-Data Retrieval)
- Seleciona fontes por UCB (ganho/custo/risco) com quotas e budgets
- Executa aquisição, chunking (900/140), dedupe (simhash), indexação RAG
- Realiza debate multi-IA e produz síntese auditável
- Atualiza Xt: novelty_sim (↓ melhor), RAG_recall (↓ melhor)
- Registra provas WORM completas com fail-closed

Versão: 7.0.0 - Fusão Definitiva
Data: 2025.09.16
"""

from __future__ import annotations
import os
import sys
import re
import json
import time
import uuid
import math
import glob
import hashlib
import sqlite3
import random
import threading
import asyncio
import traceback
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from datetime import datetime, timezone
from collections import defaultdict, Counter, deque
from abc import ABC, abstractmethod
from enum import Enum
from functools import lru_cache
import warnings

warnings.filterwarnings('ignore')

# =============================================================================
# IMPORTS OPCIONAIS COM FALLBACKS
# =============================================================================

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    SentenceTransformer = None
    HAS_ST = False

# =============================================================================
# INTEGRAÇÃO COM 1/8 E 2/8
# =============================================================================

try:
    # Importa do código 1/8
    from penin_omega_1_core import (
        OmegaState, WORMLedger, LLMBridge, MultiLevelCache,
        log, save_json, load_json, _ts, _hash_data,
        GOVERNANCE, DIRS as CORE_DIRS
    )
    # Importa do código 2/8
    from penin_omega_2_strategy import (
        PlanOmega, Goal, Constraints, Budgets
    )
    CORE_INTEGRATION = True
except ImportError:
    CORE_INTEGRATION = False
    
    # Fallbacks completos para operação standalone
    @dataclass
    class OmegaState:
        novelty_sim: float = 1.0
        rag_recall: float = 1.0
        hashes: List[str] = field(default_factory=list)
        proof_ids: List[str] = field(default_factory=list)
        U: float = 0.0
        cost: float = 0.0
        ece: float = 0.0
        rho: float = 0.5
        consent: bool = True
        eco_ok: bool = True
        cycle_count: int = 0
        timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
        version: str = "3.8.fusion"
        
        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)
        
        def validate_gates(self) -> bool:
            return self.ece <= 0.01 and self.rho <= 0.95 and self.consent and self.eco_ok

    class WORMLedger:
        def __init__(self, path: Optional[Path] = None):
            self.path = path or Path("ledger_f3.jsonl")
            self.lock = threading.RLock()
            
        def record_event(self, event_type: str, data: Dict[str, Any]) -> str:
            with self.lock:
                event_id = str(uuid.uuid4())
                payload = {
                    "event_id": event_id,
                    "type": event_type,
                    "data": data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                payload["hash"] = hashlib.sha256(
                    json.dumps(payload, sort_keys=True).encode()
                ).hexdigest()
                
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(payload, ensure_ascii=False) + "\n")
                
                return event_id

    class LLMBridge:
        async def call_best(self, prompt: str, system_prompt: str = "", **kwargs):
            class MockResponse:
                status = "COMPLETED"
                content = f"Resposta simulada para: {prompt[:100]}..."
                latency = 0.1
            return MockResponse(), "local"
        
        async def call_many(self, prompt: str, providers: List[str], **kwargs):
            responses = {}
            for p in providers[:2]:
                resp, _ = await self.call_best(prompt, **kwargs)
                responses[p] = resp
            return responses
        
        async def ensemble(self, responses: Dict[str, Any], **kwargs) -> str:
            contents = [r.content for r in responses.values() if hasattr(r, 'content')]
            return "\n".join(contents[:3]) if contents else "Fusão falhou."

    class MultiLevelCache:
        def __init__(self, **kwargs):
            self.cache = {}
        def get(self, key, default=None):
            return self.cache.get(key, default)
        def set(self, key, value, ttl=None):
            self.cache[key] = value

    @dataclass
    class Goal:
        name: str = ""
        metric: str = ""
        target: float = 0.0
        tolerance: float = 0.05
        deadline: int = 10
        description: str = ""
        
    @dataclass
    class Constraints:
        ece_max: float = 0.01
        rho_bias_max: float = 1.05
        rho_max: float = 0.95
        delta_linf_min: float = 0.01
        trust_region_radius_proposed: float = 0.1
        
    @dataclass
    class Budgets:
        max_cost: float = 10.0
        max_tokens: int = 100000
        max_llm_calls: int = 12
        max_latency_ms: int = 5000
        quota_local: float = 0.8
        used_llm_calls: int = 0
        used_tokens: int = 0
        
        def can_afford(self, required: Dict) -> bool:
            return (self.used_llm_calls + required.get("llm_calls", 0) <= self.max_llm_calls and
                    self.used_tokens + required.get("tokens", 0) <= self.max_tokens)
        
        def allocate(self, amount: Dict, purpose: str = "") -> bool:
            if not self.can_afford(amount):
                return False
            self.used_llm_calls += amount.get("llm_calls", 0)
            self.used_tokens += amount.get("tokens", 0)
            return True

    @dataclass
    class PlanOmega:
        id: str = ""
        goals: List[Goal] = field(default_factory=list)
        constraints: Constraints = field(default_factory=Constraints)
        budgets: Budgets = field(default_factory=Budgets)
        U_signal: float = 0.0
        priority_map: Dict[str, float] = field(default_factory=dict)
        
        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

    GOVERNANCE = {}
    
    def log(msg: str, level: str = "INFO"):
        print(f"[{level}] {msg}")
    
    def _ts():
        return datetime.now(timezone.utc).isoformat()
    
    def _hash_data(data: Any) -> str:
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(str(data).encode()).hexdigest()
    
    def save_json(path: Path, data: Any):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_json(path: Path, default=None):
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default

# =============================================================================
# CONFIGURAÇÃO E PATHS
# =============================================================================

if CORE_INTEGRATION:
    DIRS = CORE_DIRS
else:
    ROOT = Path("/opt/penin_omega") if os.path.exists("/opt/penin_omega") else Path.home() / ".penin_omega"
    DIRS = {
        "LOG": ROOT / "logs",
        "STATE": ROOT / "state",
        "CACHE": ROOT / "cache",
        "KNOWLEDGE": ROOT / "knowledge",
        "INDEX": ROOT / "index",
        "SYNTHESIS": ROOT / "synthesis",
        "WORM": ROOT / "worm"
    }
    for d in DIRS.values():
        d.mkdir(parents=True, exist_ok=True)

# Arquivos principais
LOG_FILE = DIRS["LOG"] / "acquisition_3_8.log"
INDEX_DB = DIRS["INDEX"] / "rag_index.sqlite3"
SYNTHESIS_DIR = DIRS["SYNTHESIS"]

# Configuração padrão
ACQ_CONFIG = {
    "version": "3.8.0",
    "chunk_size": 900,
    "overlap": 140,
    "simhash_bits": 64,
    "hamming_threshold": 3,
    "embedding_model": "all-MiniLM-L6-v2",
    "ucb_c": 0.3,
    "novelty_sample_k": 64,
    "recall_thr": 0.60,
    "max_questions": 8,
    "debate_providers": ["local", "openai", "anthropic"],
    "pii_regex": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b|\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    "max_docs_per_cycle": 50,
    "max_chars_per_doc": 100000,
    "max_total_chars": 500000
}

# =============================================================================
# ENUMS E ESTRUTURAS
# =============================================================================

class AcquisitionEventType(Enum):
    ACQ_START = "ACQ_START"
    ACQ_SOURCE_SELECT = "ACQ_SOURCE_SELECT"
    ACQ_ITEM = "ACQ_ITEM"
    ACQ_INDEXED = "ACQ_INDEXED"
    ACQ_SYNTHESIS = "ACQ_SYNTHESIS"
    ACQ_DONE = "ACQ_DONE"
    ACQ_ABORT = "ACQ_ABORT"

@dataclass
class AcquisitionReport:
    plan_hash: str
    questions: List[str]
    n_docs: int
    n_chunks: int
    novelty_sim: float
    rag_recall: float
    synthesis_path: Optional[str]
    sources_stats: Dict[str, Dict[str, Any]]
    proof_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Document:
    id: str
    title: str
    text: str
    source: str
    metadata: Dict[str, Any]
    simhash: int
    timestamp: str

@dataclass
class Chunk:
    id: str
    doc_id: str
    text: str
    simhash: int
    embedding: Optional[List[float]]
    order: int

# =============================================================================
# UTILITÁRIOS
# =============================================================================

def sanitize_pii(text: str) -> str:
    """Remove PII básica via regex."""
    return re.sub(ACQ_CONFIG["pii_regex"], "[REDACTED]", text)

def _tokenize(text: str) -> List[str]:
    """Tokenização simples para processamento."""
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_]+", sanitize_pii(text).lower())

# =============================================================================
# SIMHASH PARA DEDUPLICAÇÃO
# =============================================================================

class SimHashProcessor:
    """Processador para deduplicação baseada em SimHash."""
    
    def __init__(self, bits: int = 64, hamming_threshold: int = 3):
        self.bits = bits
        self.hamming_threshold = hamming_threshold
        self.seen_hashes = set()
    
    def compute(self, text: str) -> int:
        """Calcula o hash SimHash para um texto."""
        tokens = _tokenize(text)
        if not tokens:
            return 0
        
        vector = [0] * self.bits
        for token in tokens:
            token_hash = int(hashlib.md5(token.encode()).hexdigest(), 16)
            for i in range(self.bits):
                if (token_hash >> i) & 1:
                    vector[i] += 1
                else:
                    vector[i] -= 1
        
        simhash = 0
        for i, value in enumerate(vector):
            if value > 0:
                simhash |= 1 << i
        
        return simhash
    
    def is_duplicate(self, text: str) -> bool:
        """Verifica se um texto é duplicado baseado em SimHash."""
        if not text:
            return False
        
        new_hash = self.compute(text)
        
        for existing_hash in self.seen_hashes:
            if self.hamming_distance(new_hash, existing_hash) <= self.hamming_threshold:
                return True
        
        self.seen_hashes.add(new_hash)
        return False
    
    def hamming_distance(self, hash1: int, hash2: int) -> int:
        """Calcula a distância de Hamming entre dois hashes."""
        return bin(hash1 ^ hash2).count("1")

# =============================================================================
# EMBEDDER (CPU-FIRST)
# =============================================================================

class Embedder:
    """Gerenciador de embeddings com fallbacks."""
    
    def __init__(self, model_name: str = None, seed: int = 42):
        self.model_name = model_name or ACQ_CONFIG["embedding_model"]
        self.seed = seed
        self.model = None
        self.mode = "unknown"
        self.dimension = 384
        self._initialize()
    
    def _initialize(self):
        """Inicializa o embedder com base na disponibilidade."""
        if HAS_ST:
            try:
                self.model = SentenceTransformer(self.model_name, device='cpu')
                self.mode = "st"
                log(f"Embedder inicializado com sentence-transformers: {self.model_name}")
            except Exception as e:
                log(f"Falha ao carregar sentence-transformers: {e}", level="WARNING")
                self.mode = "lite"
        else:
            self.mode = "lite"
            self.dimension = 256
            log("Embedder usando modo lite (hash-based)")
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para uma lista de textos."""
        if not texts:
            return []
        
        if self.mode == "st" and self.model:
            embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            return [embedding.tolist() for embedding in embeddings]
        
        # Modo lite: bag-of-words com hashing
        results = []
        for text in texts:
            vector = [0.0] * self.dimension
            tokens = _tokenize(text)
            
            for token in tokens:
                hash_val = hash(token + str(self.seed)) % self.dimension
                vector[hash_val] += 1.0
            
            # Normalização L2
            norm = math.sqrt(sum(x * x for x in vector))
            if norm > 0:
                vector = [x / norm for x in vector]
            
            results.append(vector)
        
        return results

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calcula similaridade cosseno entre dois vetores."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(x * y for x, y in zip(vec1, vec2))
    norm1 = math.sqrt(sum(x * x for x in vec1))
    norm2 = math.sqrt(sum(y * y for y in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

# =============================================================================
# RAG INDEX
# =============================================================================

class RAGIndex:
    """Índice RAG com persistência em SQLite."""
    
    def __init__(self, db_path: Path = INDEX_DB, embedder: Optional[Embedder] = None):
        self.db_path = db_path
        self.embedder = embedder or Embedder()
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.simhash_processor = SimHashProcessor()
        self._init_db()
    
    def _init_db(self):
        """Inicializa o banco de dados SQLite."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT,
                source TEXT,
                metadata TEXT,
                simhash INTEGER,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                doc_id TEXT,
                text TEXT,
                simhash INTEGER,
                embedding TEXT,
                order_index INTEGER,
                FOREIGN KEY (doc_id) REFERENCES documents (id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks (doc_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunks_simhash ON chunks (simhash)')
        
        self.conn.commit()
    
    def add_document(self, document: Document) -> Dict[str, Any]:
        """Adiciona um documento ao índice."""
        # Verifica duplicatas
        if self.simhash_processor.is_duplicate(document.text):
            return {"doc_id": None, "n_chunks": 0, "duplicate": True}
        
        try:
            cursor = self.conn.cursor()
            
            # Insere documento
            cursor.execute(
                'INSERT INTO documents (id, title, source, metadata, simhash, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                (document.id, document.title, document.source,
                 json.dumps(document.metadata), document.simhash,
                 document.timestamp)
            )
            
            # Chunking do documento
            chunks = self._chunk_document(document)
            
            # Adiciona chunks
            for chunk in chunks:
                embedding_json = json.dumps(chunk.embedding) if chunk.embedding else None
                cursor.execute(
                    'INSERT INTO chunks (id, doc_id, text, simhash, embedding, order_index) VALUES (?, ?, ?, ?, ?, ?)',
                    (chunk.id, chunk.doc_id, chunk.text, chunk.simhash, embedding_json, chunk.order)
                )
            
            self.conn.commit()
            
            return {"doc_id": document.id, "n_chunks": len(chunks), "duplicate": False}
            
        except Exception as e:
            log(f"Erro ao adicionar documento ao índice: {e}", level="ERROR")
            self.conn.rollback()
            return {"doc_id": None, "n_chunks": 0, "error": str(e)}
    
    def _chunk_document(self, document: Document) -> List[Chunk]:
        """Divide um documento em chunks."""
        text = sanitize_pii(document.text)
        chunk_size = ACQ_CONFIG["chunk_size"]
        overlap = ACQ_CONFIG["overlap"]
        
        chunks = []
        start = 0
        order = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Ajusta para quebrar em limites de palavras
            if end < len(text) and text[end] not in ' \t\n\r':
                for i in range(min(50, end - start)):
                    if text[end - i] in ' \t\n\r':
                        end = end - i
                        break
            
            chunk_text = text[start:end].strip()
            
            # Ignora chunks muito pequenos
            if len(chunk_text) >= 50:
                chunk_id = f"{document.id}_chunk_{order}"
                chunk_simhash = self.simhash_processor.compute(chunk_text)
                
                # Gera embedding para o chunk
                embedding = self.embedder.encode([chunk_text])[0]
                
                chunks.append(Chunk(
                    id=chunk_id,
                    doc_id=document.id,
                    text=chunk_text,
                    simhash=chunk_simhash,
                    embedding=embedding,
                    order=order
                ))
                order += 1
            
            start = end - overlap if overlap > 0 else end
        
        return chunks
    
    def search(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        """Busca chunks relevantes para uma query."""
        if not query:
            return []
        
        # Embedding da query
        query_embedding = self.embedder.encode([query])[0]
        
        # Busca todos os chunks com embeddings
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, doc_id, text, embedding FROM chunks WHERE embedding IS NOT NULL LIMIT 1000')
        chunks = cursor.fetchall()
        
        # Calcula similaridade
        results = []
        for chunk_id, doc_id, text, embedding_json in chunks:
            try:
                chunk_embedding = json.loads(embedding_json)
                similarity = cosine_similarity(query_embedding, chunk_embedding)
                
                if similarity >= ACQ_CONFIG["recall_thr"]:
                    results.append({
                        "chunk_id": chunk_id,
                        "doc_id": doc_id,
                        "text": text,
                        "similarity": similarity
                    })
            except:
                continue
        
        # Ordena por similaridade e retorna os top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def compute_novelty(self, texts: List[str], sample_size: int = None) -> float:
        """Calcula métrica de novidade para textos em relação ao índice."""
        if sample_size is None:
            sample_size = ACQ_CONFIG["novelty_sample_k"]
        
        if not texts:
            return 0.0
        
        # Amostra chunks do índice para comparação
        cursor = self.conn.cursor()
        cursor.execute('SELECT text FROM chunks ORDER BY RANDOM() LIMIT ?', (sample_size,))
        sample_texts = [row[0] for row in cursor.fetchall()]
        
        if not sample_texts:
            return 0.0  # Índice vazio, baixa similaridade = alta novidade
        
        # Gera embeddings
        sample_embeddings = self.embedder.encode(sample_texts)
        text_embeddings = self.embedder.encode(texts)
        
        # Calcula similaridade máxima para cada texto
        max_similarities = []
        for text_embedding in text_embeddings:
            max_sim = 0.0
            for sample_embedding in sample_embeddings:
                similarity = cosine_similarity(text_embedding, sample_embedding)
                max_sim = max(max_sim, similarity)
            max_similarities.append(max_sim)
        
        # Retorna média das similaridades máximas (↓ é melhor)
        return sum(max_similarities) / len(max_similarities) if max_similarities else 0.0
    
    def compute_recall(self, queries: List[str]) -> float:
        """Calcula pseudo-recall para queries."""
        if not queries:
            return 0.0
        
        hits = 0
        for query in queries:
            results = self.search(query, top_k=1)
            if results and results[0]["similarity"] > ACQ_CONFIG["recall_thr"]:
                hits += 1
        
        # Retorna fração de hits (↓ é melhor segundo especificação)
        return hits / len(queries)

# =============================================================================
# UCB SOURCE SELECTOR
# =============================================================================

class UCBSourceSelector:
    """Seletor de fontes usando algoritmo UCB."""
    
    def __init__(self, exploration_factor: float = None):
        self.exploration_factor = exploration_factor or ACQ_CONFIG["ucb_c"]
        self.stats = defaultdict(lambda: {
            "selections": 0,
            "total_gain": 0.0,
            "total_cost": 0.0,
            "total_latency": 0.0
        })
        self.total_selections = 0
    
    def select_source(self, available_sources: List[str], u_signal: float = 0.0) -> str:
        """Seleciona uma fonte usando UCB."""
        if not available_sources:
            raise ValueError("Nenhuma fonte disponível")
        
        # Ajusta exploração com U_signal
        c = self.exploration_factor + u_signal * 0.1
        
        best_source = None
        best_score = -float('inf')
        
        for source in available_sources:
            stats = self.stats[source]
            
            if stats["selections"] == 0:
                # Fonte não explorada - prioridade máxima
                return source
            
            # Média de ganho ajustada por custo
            avg_gain = stats["total_gain"] / stats["selections"]
            avg_cost = max(0.01, stats["total_cost"] / stats["selections"])
            avg_latency = max(1, stats["total_latency"] / stats["selections"])
            
            # Ganho ajustado
            adjusted_gain = avg_gain / (avg_cost * (avg_latency / 1000))
            
            # Termo de exploração
            exploration = c * math.sqrt(
                math.log(self.total_selections + 1) / stats["selections"]
            )
            
            # Score UCB
            score = adjusted_gain + exploration
            
            if score > best_score:
                best_score = score
                best_source = source
        
        return best_source or available_sources[0]
    
    def update_stats(self, source: str, gain: float, cost: float = 0.0, latency_ms: float = 0.0):
        """Atualiza estatísticas para uma fonte."""
        self.stats[source]["selections"] += 1
        self.stats[source]["total_gain"] += max(0.0, gain)
        self.stats[source]["total_cost"] += cost
        self.stats[source]["total_latency"] += latency_ms
        self.total_selections += 1

# =============================================================================
# KNOWLEDGE SOURCES
# =============================================================================

class KnowledgeSource(ABC):
    """Classe base para fontes de conhecimento."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def fetch(self, query: str, max_chars: int) -> List[Document]:
        """Busca documentos relevantes para uma query."""
        pass
    
    def estimate_gain(self, documents: List[Document]) -> float:
        """Estima o ganho informacional dos documentos."""
        if not documents:
            return 0.0
        
        total_text = " ".join(doc.text for doc in documents)
        unique_words = set(total_text.split())
        total_words = len(total_text.split())
        
        if total_words == 0:
            return 0.0
        
        uniqueness_ratio = len(unique_words) / total_words
        return min(1.0, uniqueness_ratio)

class LocalFilesSource(KnowledgeSource):
    """Fonte de conhecimento: arquivos locais."""
    
    def __init__(self, root_dirs: List[Path]):
        super().__init__("local_files")
        self.root_dirs = root_dirs
        self.supported_extensions = {'.txt', '.md', '.json', '.py', '.yaml', '.yml'}
    
    async def fetch(self, query: str, max_chars: int) -> List[Document]:
        """Busca em arquivos locais por conteúdo relevante."""
        documents = []
        total_chars = 0
        
        # Palavras-chave da query
        keywords = set(re.findall(r'\b\w+\b', query.lower()))
        
        for root_dir in self.root_dirs:
            if not root_dir.exists():
                continue
            
            for ext in self.supported_extensions:
                for file_path in root_dir.rglob(f"*{ext}"):
                    if total_chars >= max_chars:
                        return documents
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Verifica relevância
                        content_lower = content.lower()
                        if not any(keyword in content_lower for keyword in keywords):
                            continue
                        
                        # Cria documento
                        doc_id = str(uuid.uuid4())
                        simhash = SimHashProcessor().compute(content)
                        
                        document = Document(
                            id=doc_id,
                            title=file_path.name,
                            text=content[:min(len(content), max_chars - total_chars)],
                            source=self.name,
                            metadata={"path": str(file_path)},
                            simhash=simhash,
                            timestamp=_ts()
                        )
                        
                        documents.append(document)
                        total_chars += len(document.text)
                        
                    except Exception as e:
                        log(f"Erro ao processar arquivo {file_path}: {e}", level="WARNING")
                        continue
        
        return documents

class LLMSource(KnowledgeSource):
    """Fonte de conhecimento: LLM."""
    
    def __init__(self, llm_bridge: LLMBridge):
        super().__init__("llm_qa")
        self.llm_bridge = llm_bridge
    
    async def fetch(self, query: str, max_chars: int) -> List[Document]:
        """Gera conhecimento novo usando LLM."""
        try:
            system_prompt = (
                "Você é um assistente especializado em gerar conhecimento técnico "
                "preciso e útil. Responda com conteúdo estruturado: "
                "1) Parágrafo técnico explicativo "
                "2) 3 bullets práticos e acionáveis "
                "3) 1 exemplo de código Python demonstrativo"
            )
            
            response, provider = await self.llm_bridge.call_best(
                query, 
                system_prompt=system_prompt,
                max_tokens=min(2000, max_chars // 4)
            )
            
            if response.status == "COMPLETED" and response.content:
                doc_id = str(uuid.uuid4())
                simhash = SimHashProcessor().compute(response.content)
                
                document = Document(
                    id=doc_id,
                    title=f"LLM Response: {query[:50]}...",
                    text=response.content[:max_chars],
                    source=f"{self.name}_{provider}",
                    metadata={"provider": provider, "query": query},
                    simhash=simhash,
                    timestamp=_ts()
                )
                
                return [document]
                
        except Exception as e:
            log(f"Erro na fonte LLM: {e}", level="ERROR")
        
        return []

class WebStubSource(KnowledgeSource):
    """Fonte de conhecimento: Web (stub para implementação futura)."""
    
    def __init__(self):
        super().__init__("web_stub")
    
    async def fetch(self, query: str, max_chars: int) -> List[Document]:
        """Stub para busca web."""
        doc_id = str(uuid.uuid4())
        content = (
            f"Resultados simulados para: {query}\n\n"
            "Técnicas de RAG avançadas:\n"
            "- Chunking semântico com overlap de 140 caracteres\n"
            "- SimHash para deduplicação (Hamming ≤ 3)\n"
            "- Embeddings MiniLM para CPU-first\n"
            "- UCB para seleção de fontes\n\n"
            "def chunk_text(text, size=900, overlap=140):\n"
            "    chunks = []\n"
            "    start = 0\n"
            "    while start < len(text):\n"
            "        end = min(start + size, len(text))\n"
            "        chunks.append(text[start:end])\n"
            "        start = end - overlap\n"
            "    return chunks"
        )
        
        document = Document(
            id=doc_id,
            title=f"Web Stub: {query[:30]}...",
            text=content[:max_chars],
            source=self.name,
            metadata={"query": query, "stub": True},
            simhash=SimHashProcessor().compute(content),
            timestamp=_ts()
        )
        
        return [document]

# =============================================================================
# TTD-DR QUESTION GENERATOR
# =============================================================================

class TTDDRQuestionGenerator:
    """Gerador de perguntas usando Task-To-Data Decomposition Retrieval."""
    
    def __init__(self, llm_bridge: Optional[LLMBridge] = None):
        self.llm_bridge = llm_bridge
    
    async def generate_questions(self, plan: PlanOmega, max_questions: int = 8) -> List[str]:
        """Gera perguntas acionáveis a partir do plano."""
        if not plan.goals:
            return self._fallback_questions()
        
        # Tentar via LLM se disponível
        if self.llm_bridge:
            try:
                return await self._generate_with_llm(plan, max_questions)
            except Exception as e:
                log(f"TTD-DR via LLM falhou: {e}, usando fallback", level="WARNING")
        
        # Fallback determinístico
        return self._generate_deterministic(plan, max_questions)
    
    async def _generate_with_llm(self, plan: PlanOmega, max_questions: int) -> List[str]:
        """Gera perguntas usando LLM."""
        goals_desc = "\n".join([
            f"- {g.name}: {g.metric} → {g.target} (±{g.tolerance})"
            for g in plan.goals[:5]
        ])
        
        constraints_desc = (
            f"ECE≤{plan.constraints.ece_max}, "
            f"ρ≤{plan.constraints.rho_max}, "
            f"ΔL∞≥{plan.constraints.delta_linf_min}"
        )
        
        prompt = (
            f"Desenvolva {max_questions} perguntas técnicas acionáveis (TTD-DR) "
            f"para alcançar os seguintes objetivos com as restrições indicadas.\n\n"
            f"Objetivos:\n{goals_desc}\n\n"
            f"Restrições: {constraints_desc}\n\n"
            "Formato: Lista numerada de perguntas específicas e práticas."
        )
        
        response, _ = await self.llm_bridge.call_best(
            prompt,
            system_prompt="Você é um especialista em decomposição de tarefas técnicas."
        )
        
        if response.status == "COMPLETED" and response.content:
            lines = response.content.split("\n")
            questions = [
                line.strip() for line in lines
                if line.strip() and (line[0].isdigit() or line.startswith("-"))
            ]
            return questions[:max_questions]
        
        return self._generate_deterministic(plan, max_questions)
    
    def _generate_deterministic(self, plan: PlanOmega, max_questions: int) -> List[str]:
        """Gera perguntas de forma determinística."""
        questions = []
        
        for goal in plan.goals[:max_questions]:
            if goal.metric == "ppl_ood":
                q = f"Como reduzir perplexidade OOD para {goal.target} mantendo ρ≤{plan.constraints.rho_max}?"
            elif goal.metric == "delta_linf":
                q = f"Quais técnicas maximizam ΔL∞ acima de {goal.target} com segurança?"
            elif goal.metric == "novelty_sim":
                q = f"Como descobrir conhecimento novo com novelty_sim≤{goal.target}?"
            elif goal.metric == "rag_recall":
                q = f"Como otimizar RAG para recall≤{goal.target} (menor redundância)?"
            else:
                q = f"Como alcançar '{goal.name}' ({goal.metric}={goal.target}) respeitando constraints?"
            
            questions.append(q)
        
        # Adicionar perguntas genéricas se necessário
        while len(questions) < min(3, max_questions):
            questions.extend(self._fallback_questions())
        
        return questions[:max_questions]
    
    def _fallback_questions(self) -> List[str]:
        """Perguntas padrão de fallback."""
        return [
            "Quais técnicas de RAG otimizam novelty e recall com baixo custo?",
            "Como implementar deduplicação eficiente com SimHash (Hamming≤3)?",
            "Quais embeddings CPU-first são mais eficazes para indexação?",
        ]

# =============================================================================
# MULTI-IA DEBATE & SYNTHESIS
# =============================================================================

class MultiAgentDebate:
    """Sistema de debate multi-IA com síntese auditável."""
    
    def __init__(self, llm_bridge: LLMBridge):
        self.llm_bridge = llm_bridge
    
    async def synthesize(
        self,
        questions: List[str],
        documents: List[Document],
        max_tokens: int = 2000
    ) -> Tuple[str, List[str]]:
        """Executa debate e produz síntese."""
        # Prepara corpus
        corpus = self._prepare_corpus(documents[:10])
        
        # Prompt para síntese
        prompt = self._build_synthesis_prompt(questions, corpus)
        
        # Tenta debate multi-provider
        providers = ACQ_CONFIG["debate_providers"]
        
        try:
            # Chama múltiplos providers
            responses = await self.llm_bridge.call_many(
                prompt,
                providers[:3],
                system_prompt="Você é um sintetizador técnico especializado em RAG e IA."
            )
            
            # Fusão via ensemble
            synthesis = await self.llm_bridge.ensemble(
                responses,
                arbiter="local"
            )
            
            providers_used = list(responses.keys())
            
        except Exception as e:
            log(f"Debate multi-IA falhou: {e}, usando single provider", level="WARNING")
            
            # Fallback para single provider
            response, provider = await self.llm_bridge.call_best(
                prompt,
                system_prompt="Sintetize o conhecimento de forma técnica e acionável."
            )
            
            synthesis = response.content if response.status == "COMPLETED" else corpus[:2000]
            providers_used = [provider]
        
        return synthesis, providers_used
    
    def _prepare_corpus(self, documents: List[Document]) -> str:
        """Prepara corpus para síntese."""
        sections = []
        for doc in documents:
            section = f"### {doc.title}\n"
            section += f"Fonte: {doc.source}\n"
            section += f"{doc.text[:1000]}..."
            sections.append(section)
        
        return "\n\n".join(sections)
    
    def _build_synthesis_prompt(self, questions: List[str], corpus: str) -> str:
        """Constrói prompt para síntese."""
        questions_str = "\n".join(f"- {q}" for q in questions[:5])
        
        return (
            "Sintetize o corpus abaixo em resposta às perguntas, "
            "organizando em:\n"
            "1. Seções temáticas claras\n"
            "2. Bullets práticos e acionáveis\n"
            "3. Código Python demonstrativo\n\n"
            f"PERGUNTAS:\n{questions_str}\n\n"
            f"CORPUS:\n{corpus[:8000]}\n\n"
            "SÍNTESE:"
        )

# =============================================================================
# KNOWLEDGE ACQUISITION ENGINE
# =============================================================================

class KnowledgeAcquisitionEngine:
    """Motor principal de aquisição de conhecimento (Fase 3)."""
    
    def __init__(
        self,
        omega_state: OmegaState,
        plan: PlanOmega,
        worm_ledger: Optional[WORMLedger] = None,
        llm_bridge: Optional[LLMBridge] = None,
        cache: Optional[MultiLevelCache] = None,
        roots: Optional[List[Path]] = None,
        seed: int = 42
    ):
        self.X = omega_state
        self.plan = plan
        self.worm = worm_ledger or WORMLedger()
        self.llm_bridge = llm_bridge or LLMBridge()
        self.cache = cache or MultiLevelCache()
        self.roots = roots or [DIRS.get("KNOWLEDGE", Path.cwd())]
        
        # Componentes
        self.index = RAGIndex()
        self.ucb_selector = UCBSourceSelector()
        self.question_generator = TTDDRQuestionGenerator(self.llm_bridge)
        self.debate_system = MultiAgentDebate(self.llm_bridge)
        
        # Fontes de conhecimento
        self.sources: Dict[str, KnowledgeSource] = {
            "local_files": LocalFilesSource(self.roots),
            "llm_qa": LLMSource(self.llm_bridge),
            "web_stub": WebStubSource()
        }
        
        # Estatísticas
        self.sources_stats = defaultdict(lambda: {
            "n": 0, "gain": 0.0, "lat_avg": 0.0, "cost": 0.0
        })
        
        # Configuração
        self.seed = seed
        random.seed(seed)
    
    async def execute(self) -> AcquisitionReport:
        """Executa ciclo completo de aquisição."""
        start_time = time.time()
        plan_hash = _hash_data(self.plan.to_dict())
        
        # Registra início
        proof_id = self.worm.record_event(
            AcquisitionEventType.ACQ_START.value,
            {
                "plan_hash": plan_hash,
                "timestamp": _ts(),
                "budgets": asdict(self.plan.budgets)
            }
        )
        
        # Verifica constraints (fail-closed)
        if not self._check_constraints():
            return self._abort_acquisition(plan_hash, "Constraints violadas", proof_id)
        
        # Gera perguntas via TTD-DR
        questions = await self.question_generator.generate_questions(
            self.plan,
            ACQ_CONFIG["max_questions"]
        )
        
        # Aquisição por UCB
        all_documents = await self._acquire_knowledge(questions)
        
        if not all_documents:
            return self._abort_acquisition(plan_hash, "Nenhum documento adquirido", proof_id)
        
        # Ingestão no índice
        n_docs, n_chunks = self._ingest_documents(all_documents)
        
        # Síntese via debate multi-IA
        synthesis, providers = await self.debate_system.synthesize(
            questions,
            all_documents
        )
        
        # Salva síntese
        synthesis_path = self._save_synthesis(synthesis, questions, all_documents)
        
        # Registra síntese
        self.worm.record_event(
            AcquisitionEventType.ACQ_SYNTHESIS.value,
            {
                "path": str(synthesis_path),
                "hash": _hash_data(synthesis),
                "providers": providers,
                "plan_hash": plan_hash
            }
        )
        
        # Atualiza métricas do Xt
        document_texts = [doc.text for doc in all_documents]
        novelty_sim = self.index.compute_novelty(document_texts)
        rag_recall = self.index.compute_recall(questions)
        
        # Atualiza estado (↓ é melhor para ambas as métricas)
        self.X.novelty_sim = novelty_sim
        self.X.rag_recall = rag_recall
        self.X.hashes.append(_hash_data(synthesis))
        self.X.proof_ids.append(proof_id)
        
        # Atualiza sinais
        if hasattr(self.plan, 'U_signal'):
            self.X.U += self.plan.U_signal * 0.1
        
        # Registra conclusão
        self.worm.record_event(
            AcquisitionEventType.ACQ_DONE.value,
            {
                "plan_hash": plan_hash,
                "n_docs": n_docs,
                "n_chunks": n_chunks,
                "novelty_sim": novelty_sim,
                "rag_recall": rag_recall,
                "sources_stats": dict(self.sources_stats),
                "processing_time": time.time() - start_time
            }
        )
        
        return AcquisitionReport(
            plan_hash=plan_hash,
            questions=questions,
            n_docs=n_docs,
            n_chunks=n_chunks,
            novelty_sim=novelty_sim,
            rag_recall=rag_recall,
            synthesis_path=str(synthesis_path),
            sources_stats=dict(self.sources_stats),
            proof_id=proof_id
        )
    
    def _check_constraints(self) -> bool:
        """Verifica se constraints são respeitadas."""
        # Verifica gates éticos (Σ-Guard)
        if hasattr(self.X, 'validate_gates'):
            if not self.X.validate_gates():
                log("Gates éticos/risco violados", level="ERROR")
                return False
        
        # Verifica budgets
        if self.plan.budgets.used_llm_calls >= self.plan.budgets.max_llm_calls:
            log("Budget de LLM calls excedido", level="ERROR")
            return False
        
        return True
    
    async def _acquire_knowledge(self, questions: List[str]) -> List[Document]:
        """Adquire conhecimento usando UCB para seleção de fontes."""
        all_documents = []
        
        for question in questions:
            # Verifica budget
            if not self.plan.budgets.can_afford({"llm_calls": 1, "tokens": 1000}):
                break
            
            # Seleciona fonte via UCB
            available_sources = list(self.sources.keys())
            
            # Filtra por quota_local se necessário
            if hasattr(self.plan.budgets, 'quota_local'):
                local_ratio = self.sources_stats["local_files"]["n"] / max(1, self.total_docs())
                if local_ratio < self.plan.budgets.quota_local:
                    available_sources = ["local_files"] + available_sources
            
            selected_source = self.ucb_selector.select_source(
                available_sources,
                getattr(self.plan, 'U_signal', 0.0)
            )
            
            # Registra seleção
            self.worm.record_event(
                AcquisitionEventType.ACQ_SOURCE_SELECT.value,
                {
                    "source": selected_source,
                    "question": question[:100],
                    "ucb_score": 0.0  # Simplificado
                }
            )
            
            # Busca documentos
            start_time = time.time()
            documents = await self.sources[selected_source].fetch(
                question,
                ACQ_CONFIG["max_chars_per_doc"]
            )
            latency_ms = (time.time() - start_time) * 1000
            
            # Calcula ganho
            gain = self.sources[selected_source].estimate_gain(documents)
            
            # Estima custo
            cost = len(documents) * 0.001 if selected_source == "llm_qa" else 0.0
            
            # Atualiza UCB
            self.ucb_selector.update_stats(selected_source, gain, cost, latency_ms)
            
            # Atualiza estatísticas
            self.sources_stats[selected_source]["n"] += len(documents)
            self.sources_stats[selected_source]["gain"] += gain
            self.sources_stats[selected_source]["cost"] += cost
            
            if self.sources_stats[selected_source]["n"] > 0:
                self.sources_stats[selected_source]["lat_avg"] = (
                    self.sources_stats[selected_source]["lat_avg"] * 
                    (self.sources_stats[selected_source]["n"] - len(documents)) +
                    latency_ms * len(documents)
                ) / self.sources_stats[selected_source]["n"]
            
            # Adiciona documentos
            all_documents.extend(documents)
            
            # Atualiza budget
            if selected_source == "llm_qa":
                self.plan.budgets.allocate(
                    {"llm_calls": 1, "tokens": sum(len(d.text) for d in documents) // 4},
                    purpose=f"acquire_{selected_source}"
                )
        
        return all_documents
    
    def _ingest_documents(self, documents: List[Document]) -> Tuple[int, int]:
        """Ingere documentos no índice."""
        n_docs = 0
        n_chunks = 0
        
        for doc in documents[:ACQ_CONFIG["max_docs_per_cycle"]]:
            result = self.index.add_document(doc)
            
            if not result.get("duplicate", False) and result.get("doc_id"):
                n_docs += 1
                n_chunks += result.get("n_chunks", 0)
                
                # Registra item
                self.worm.record_event(
                    AcquisitionEventType.ACQ_ITEM.value,
                    {
                        "doc_id": result["doc_id"],
                        "title": doc.title,
                        "source": doc.source,
                        "simhash": doc.simhash
                    }
                )
                
                # Registra indexação
                self.worm.record_event(
                    AcquisitionEventType.ACQ_INDEXED.value,
                    {
                        "doc_id": result["doc_id"],
                        "n_chunks": result.get("n_chunks", 0),
                        "vec_mode": self.index.embedder.mode
                    }
                )
        
        return n_docs, n_chunks
    
    def _save_synthesis(
        self,
        synthesis: str,
        questions: List[str],
        documents: List[Document]
    ) -> Path:
        """Salva síntese auditável."""
        synthesis_id = str(uuid.uuid4())[:8]
        synthesis_path = SYNTHESIS_DIR / f"synthesis_{synthesis_id}.json"
        
        synthesis_data = {
            "id": synthesis_id,
            "timestamp": _ts(),
            "content": synthesis,
            "questions": questions,
            "sources": [
                {
                    "title": doc.title,
                    "source": doc.source,
                    "metadata": doc.metadata
                }
                for doc in documents[:10]
            ],
            "hash": _hash_data(synthesis)
        }
        
        save_json(synthesis_path, synthesis_data)
        
        return synthesis_path
    
    def _abort_acquisition(
        self,
        plan_hash: str,
        reason: str,
        proof_id: str
    ) -> AcquisitionReport:
        """Aborta aquisição de forma segura."""
        self.worm.record_event(
            AcquisitionEventType.ACQ_ABORT.value,
            {
                "plan_hash": plan_hash,
                "reason": reason,
                "budget_state": asdict(self.plan.budgets)
            }
        )
        
        log(f"Aquisição abortada: {reason}", level="ERROR")
        
        # Retorna relatório conservador
        return AcquisitionReport(
            plan_hash=plan_hash,
            questions=[],
            n_docs=0,
            n_chunks=0,
            novelty_sim=self.X.novelty_sim,  # Mantém valores atuais
            rag_recall=self.X.rag_recall,
            synthesis_path=None,
            sources_stats={},
            proof_id=proof_id
        )
    
    def total_docs(self) -> int:
        """Retorna total de documentos processados."""
        return sum(stats["n"] for stats in self.sources_stats.values())

# =============================================================================
# API PÚBLICA
# =============================================================================

async def acquire_ucb(
    xt: OmegaState,
    plan: PlanOmega,
    budgets: Optional[Budgets] = None,
    roots: Optional[List[Path]] = None,
    bridge: Optional[LLMBridge] = None,
    worm: Optional[WORMLedger] = None,
    cache: Optional[MultiLevelCache] = None,
    seed: int = 42
) -> AcquisitionReport:
    """
    Função principal para aquisição de conhecimento (Fase 3).
    
    Args:
        xt: Estado Omega atual
        plan: Plano Ω-META do módulo 2/8
        budgets: Orçamentos (opcional, usa do plano se não fornecido)
        roots: Diretórios raiz para busca local
        bridge: Bridge LLM para acesso a modelos
        worm: Ledger WORM para registro de eventos
        cache: Cache multi-nível para otimização
        seed: Seed para determinismo
    
    Returns:
        Relatório completo de aquisição
    """
    # Usa budgets do plano se não fornecido
    if budgets:
        plan.budgets = budgets
    
    # Cria e executa engine
    engine = KnowledgeAcquisitionEngine(
        omega_state=xt,
        plan=plan,
        worm_ledger=worm,
        llm_bridge=bridge,
        cache=cache,
        roots=roots,
        seed=seed
    )
    
    return await engine.execute()

# Versão síncrona para compatibilidade
def acquire_ucb_sync(
    xt: OmegaState,
    plan: PlanOmega,
    **kwargs
) -> AcquisitionReport:
    """Versão síncrona da função de aquisição."""
    import asyncio
    return asyncio.run(acquire_ucb(xt, plan, **kwargs))

# =============================================================================
# CLI PARA TESTES
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PENIN-Ω 3/8 - Aquisição de Conhecimento & Contexto"
    )
    parser.add_argument("--plan", type=str, help="Path para JSON do PlanΩ")
    parser.add_argument("--roots", type=str, help="Diretórios separados por ';'")
    parser.add_argument("--seed", type=int, default=42)
    
    args = parser.parse_args()
    
    # Estado de teste
    test_state = OmegaState()
    
    # Plano de teste
    test_plan = PlanOmega(
        id="test_plan",
        goals=[
            Goal(
                name="improve_rag",
                description="Melhorar sistema RAG",
                metric="rag_recall",
                target=0.5
            )
        ],
        U_signal=0.5
    )
    
    # Carrega plano se fornecido
    if args.plan:
        try:
            with open(args.plan, "r") as f:
                plan_data = json.load(f)
                # Converteria para PlanOmega aqui
        except Exception as e:
            log(f"Erro ao carregar plano: {e}")
    
    # Diretórios
    roots = None
    if args.roots:
        roots = [Path(p.strip()) for p in args.roots.split(";")]
    
    # Executa
    async def run_test():
        report = await acquire_ucb(
            test_state,
            test_plan,
            roots=roots,
            seed=args.seed
        )
        
        print("\n" + "="*60)
        print("RELATÓRIO DE AQUISIÇÃO - FASE 3")
        print("="*60)
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        
        print("\n" + "="*60)
        print("ESTADO OMEGA ATUALIZADO")
        print("="*60)
        print(f"novelty_sim: {test_state.novelty_sim:.3f} (↓ é melhor)")
        print(f"rag_recall: {test_state.rag_recall:.3f} (↓ é melhor)")
        print(f"hashes: {len(test_state.hashes)} registrados")
        print(f"proof_ids: {len(test_state.proof_ids)} provas")
    
    import asyncio
    asyncio.run(run_test())
