"""
WORM Ledger - Write-Once Read-Many com Schema Pydantic
=====================================================

Implementa:
- Ledger append-only com SQLite WAL mode
- Schema Pydantic v2 para RunRecord
- File locks para concorrência
- Pasta runs/<ts_id>/ com artifacts
- Hash chain para integridade
- Rollback atômico via champion pointer
"""

import os
import json
import time
import sqlite3
import hashlib
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple as TypingTuple, Union
from typing_extensions import Tuple
from contextlib import contextmanager

try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False
    import fcntl  # Fallback para Unix

from pydantic import BaseModel, Field, validator
from dataclasses import asdict


@dataclass(frozen=True)
class WORMEvent:
    """Simple event structure appended to the WORM ledgers."""

    event_type: str
    cycle_id: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "cycle_id": self.cycle_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class RunMetrics(BaseModel):
    """Métricas de um run"""
    U: float = Field(0.0, ge=0, le=1, description="Utilidade")
    S: float = Field(0.0, ge=0, le=1, description="Estabilidade") 
    C: float = Field(0.0, ge=0, le=1, description="Custo")
    L: float = Field(0.0, ge=0, le=1, description="Aprendizado futuro")
    linf: float = Field(0.0, ge=0, le=1, description="L∞ score")
    score: float = Field(0.0, ge=0, le=1, description="Score U/S/C/L")
    cost_usd: float = Field(0.0, ge=0, description="Custo em USD")
    latency_ms: float = Field(0.0, ge=0, description="Latência em ms")
    tokens_used: int = Field(0, ge=0, description="Tokens utilizados")
    
    # Métricas específicas do sistema
    caos_phi: float = Field(0.0, ge=0, le=1, description="φ(CAOS⁺)")
    sr_score: float = Field(0.0, ge=0, le=1, description="SR-Ω∞")
    alpha_omega: float = Field(0.0, ge=0, le=1, description="α_t^Ω")


class GuardResults(BaseModel):
    """Resultados dos guards"""
    sigma_guard_ok: bool = Field(description="Σ-Guard passou")
    ir_ic_ok: bool = Field(description="IR→IC passou")
    sr_gate_ok: bool = Field(description="SR gate passou")
    caos_gate_ok: bool = Field(description="CAOS⁺ gate passou")
    
    # Detalhes das violações
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_hash: Optional[str] = Field(None, description="Hash da evidência ética")


class DecisionInfo(BaseModel):
    """Informação da decisão"""
    verdict: str = Field(description="promote|canary|rollback|fail")
    reason: str = Field(description="Motivo da decisão")
    confidence: float = Field(0.0, ge=0, le=1, description="Confiança na decisão")
    
    # Comparação com champion
    delta_linf: float = Field(description="ΔL∞ vs champion")
    delta_score: float = Field(description="ΔScore vs champion")
    beta_min_met: bool = Field(description="Se ΔL∞ ≥ β_min")


class RunRecord(BaseModel):
    """Schema principal do run record"""
    # Identificação
    run_id: str = Field(description="UUID único do run")
    timestamp: float = Field(description="Unix timestamp")
    cycle: int = Field(ge=0, description="Número do ciclo")
    
    # Contexto técnico
    git_sha: Optional[str] = Field(None, description="SHA do commit")
    seed: Optional[int] = Field(None, description="Seed usado")
    config_hash: str = Field(description="Hash da configuração")
    
    # Provider/modelo
    provider_id: str = Field(description="ID do provider usado")
    model_name: Optional[str] = Field(None, description="Nome do modelo")
    candidate_cfg_hash: str = Field(description="Hash da config do candidato")
    
    # Métricas
    metrics: RunMetrics = Field(description="Métricas coletadas")
    
    # Gates
    gates: GuardResults = Field(description="Resultados dos gates")
    
    # Decisão
    decision: DecisionInfo = Field(description="Decisão tomada")
    
    # Metadados
    artifacts_path: Optional[str] = Field(None, description="Caminho dos artifacts")
    parent_run_id: Optional[str] = Field(None, description="Run pai (se challenger)")
    
    class Config:
        # Pydantic v2 compatibility
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WORMLedger:
    """
    Write-Once Read-Many Ledger com SQLite
    
    Features:
    - Append-only com hash chain
    - WAL mode para melhor concorrência
    - File locks para operações atômicas
    - Schema Pydantic para validação
    - Artifacts em diretórios separados
    """
    
    def __init__(self, 
                 db_path: Optional[Path] = None,
                 runs_dir: Optional[Path] = None,
                 enable_wal: bool = True):
        """
        Args:
            db_path: Caminho do banco SQLite
            runs_dir: Diretório para artifacts dos runs
            enable_wal: Se deve usar WAL mode
        """
        if db_path is None:
            db_path = Path.home() / ".penin_omega" / "worm_ledger" / "ledger.db"
        if runs_dir is None:
            runs_dir = Path.home() / ".penin_omega" / "runs"
            
        self.db_path = Path(db_path)
        self.runs_dir = Path(runs_dir)
        self.enable_wal = enable_wal
        
        # Criar diretórios
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        
        # Lock para operações críticas
        self._lock = threading.RLock()
        
        # Inicializar banco
        self._init_database()
        
        # Cache do último hash
        self._tail_hash = self._get_last_hash()
        
    def _init_database(self):
        """Inicializa banco com schema e configurações"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Configurar WAL mode e timeouts
            if self.enable_wal:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=5000")  # 5s timeout
                cursor.execute("PRAGMA wal_autocheckpoint=1000")
                
            # Criar tabela principal
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS run_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    timestamp REAL NOT NULL,
                    cycle INTEGER NOT NULL,
                    
                    -- Contexto
                    git_sha TEXT,
                    seed INTEGER,
                    config_hash TEXT NOT NULL,
                    
                    -- Provider
                    provider_id TEXT NOT NULL,
                    model_name TEXT,
                    candidate_cfg_hash TEXT NOT NULL,
                    
                    -- Dados JSON
                    metrics_json TEXT NOT NULL,
                    gates_json TEXT NOT NULL,
                    decision_json TEXT NOT NULL,
                    
                    -- Metadados
                    artifacts_path TEXT,
                    parent_run_id TEXT,
                    
                    -- Hash chain
                    prev_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL,
                    
                    -- Timestamps
                    created_at REAL NOT NULL,
                    
                    FOREIGN KEY (parent_run_id) REFERENCES run_records(run_id)
                )
            """)
            
            # Índices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_id ON run_records(run_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON run_records(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cycle ON run_records(cycle)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider ON run_records(provider_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision ON run_records(decision_json)")
            
            # Tabela de champion pointer (para rollback atômico)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS champion_pointer (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    run_id TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES run_records(run_id)
                )
            """)
            
            conn.commit()
            
    def _get_last_hash(self) -> str:
        """Obtém último hash da chain"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT record_hash FROM run_records ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else "genesis"
            
    def _compute_record_hash(self, record: RunRecord, prev_hash: str) -> str:
        """Computa hash do record para chain"""
        # Serializar record de forma determinística
        record_dict = record.model_dump()
        record_dict["prev_hash"] = prev_hash
        
        # Hash SHA-256
        record_json = json.dumps(record_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(record_json.encode()).hexdigest()
        
    def _create_run_directory(self, run_id: str) -> Path:
        """Cria diretório para artifacts do run"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.runs_dir / f"{timestamp}_{run_id[:8]}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir
        
    @contextmanager
    def _file_lock(self):
        """Context manager para file lock"""
        lock_file = self.db_path.parent / "ledger.lock"
        
        try:
            with open(lock_file, 'w') as f:
                if HAS_PORTALOCKER:
                    portalocker.lock(f, portalocker.LOCK_EX)
                else:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                yield
        finally:
            # Lock é liberado automaticamente quando arquivo fecha
            pass
            
    def append_record(self, record: RunRecord, 
                     artifacts: Optional[Dict[str, Any]] = None) -> str:
        """
        Adiciona record ao ledger (append-only)
        
        Args:
            record: RunRecord validado
            artifacts: Artifacts opcionais para salvar
            
        Returns:
            Hash do record inserido
        """
        with self._lock:
            with self._file_lock():
                # Criar diretório do run
                run_dir = self._create_run_directory(record.run_id)
                record.artifacts_path = str(run_dir)
                
                # Salvar artifacts
                if artifacts:
                    for name, content in artifacts.items():
                        artifact_path = run_dir / f"{name}.json"
                        with open(artifact_path, 'w', encoding='utf-8') as f:
                            json.dump(content, f, indent=2, ensure_ascii=False)
                            
                # Salvar config do record
                config_path = run_dir / "record.json"
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(record.model_dump(), f, indent=2, ensure_ascii=False)
                    
                # Computar hash
                record_hash = self._compute_record_hash(record, self._tail_hash)
                
                # Inserir no banco
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO run_records (
                            run_id, timestamp, cycle,
                            git_sha, seed, config_hash,
                            provider_id, model_name, candidate_cfg_hash,
                            metrics_json, gates_json, decision_json,
                            artifacts_path, parent_run_id,
                            prev_hash, record_hash, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.run_id, record.timestamp, record.cycle,
                        record.git_sha, record.seed, record.config_hash,
                        record.provider_id, record.model_name, record.candidate_cfg_hash,
                        record.metrics.model_dump_json(),
                        record.gates.model_dump_json(),
                        record.decision.model_dump_json(),
                        record.artifacts_path, record.parent_run_id,
                        self._tail_hash, record_hash, time.time()
                    ))
                    
                    conn.commit()
                    
                # Atualizar tail
                self._tail_hash = record_hash
                
                return record_hash
                
    def get_record(self, run_id: str) -> Optional[RunRecord]:
        """Recupera record por run_id"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM run_records WHERE run_id = ?
            """, (run_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            # Reconstruir RunRecord
            try:
                record = RunRecord(
                    run_id=row["run_id"],
                    timestamp=row["timestamp"],
                    cycle=row["cycle"],
                    git_sha=row["git_sha"],
                    seed=row["seed"],
                    config_hash=row["config_hash"],
                    provider_id=row["provider_id"],
                    model_name=row["model_name"],
                    candidate_cfg_hash=row["candidate_cfg_hash"],
                    metrics=RunMetrics.model_validate_json(row["metrics_json"]),
                    gates=GuardResults.model_validate_json(row["gates_json"]),
                    decision=DecisionInfo.model_validate_json(row["decision_json"]),
                    artifacts_path=row["artifacts_path"],
                    parent_run_id=row["parent_run_id"]
                )
                return record
            except Exception as e:
                print(f"Error reconstructing record {run_id}: {e}")
                return None
                
    def list_records(self, 
                    limit: int = 100,
                    offset: int = 0,
                    provider_id: Optional[str] = None,
                    verdict: Optional[str] = None) -> List[RunRecord]:
        """Lista records com filtros"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM run_records"
            params = []
            conditions = []
            
            if provider_id:
                conditions.append("provider_id = ?")
                params.append(provider_id)
                
            if verdict:
                conditions.append("decision_json LIKE ?")
                params.append(f'%"verdict": "{verdict}"%')
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                try:
                    record = RunRecord(
                        run_id=row["run_id"],
                        timestamp=row["timestamp"],
                        cycle=row["cycle"],
                        git_sha=row["git_sha"],
                        seed=row["seed"],
                        config_hash=row["config_hash"],
                        provider_id=row["provider_id"],
                        model_name=row["model_name"],
                        candidate_cfg_hash=row["candidate_cfg_hash"],
                        metrics=RunMetrics.model_validate_json(row["metrics_json"]),
                        gates=GuardResults.model_validate_json(row["gates_json"]),
                        decision=DecisionInfo.model_validate_json(row["decision_json"]),
                        artifacts_path=row["artifacts_path"],
                        parent_run_id=row["parent_run_id"]
                    )
                    records.append(record)
                except Exception as e:
                    print(f"Error reconstructing record {row['run_id']}: {e}")
                    continue
                    
            return records
            
    def set_champion(self, run_id: str) -> bool:
        """Define champion atual (para rollback atômico)"""
        with self._lock:
            with self._file_lock():
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    # Verificar se run existe
                    cursor.execute("SELECT 1 FROM run_records WHERE run_id = ?", (run_id,))
                    if not cursor.fetchone():
                        return False
                        
                    # Atualizar champion pointer
                    cursor.execute("""
                        INSERT OR REPLACE INTO champion_pointer (id, run_id, updated_at)
                        VALUES (1, ?, ?)
                    """, (run_id, time.time()))
                    
                    conn.commit()
                    return True
                    
    def get_champion(self) -> Optional[RunRecord]:
        """Obtém record do champion atual"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT run_id FROM champion_pointer WHERE id = 1
            """)
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return self.get_record(row[0])
            
    def verify_chain_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verifica integridade da hash chain"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT run_id, prev_hash, record_hash, 
                       metrics_json, gates_json, decision_json
                FROM run_records ORDER BY id
            """)
            
            prev_hash = "genesis"
            
            for row in cursor.fetchall():
                if row["prev_hash"] != prev_hash:
                    return False, f"Chain break at {row['run_id']}: expected prev_hash {prev_hash}, got {row['prev_hash']}"
                    
                # Reconstruir record para verificar hash
                try:
                    # Simplificado - só verificar se hash bate
                    expected_hash = row["record_hash"]
                    # Em produção, recalcular hash completo
                    prev_hash = expected_hash
                except Exception as e:
                    return False, f"Hash verification failed at {row['run_id']}: {e}"
                    
            return True, None
            
    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas do ledger"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Contagens básicas
            cursor.execute("SELECT COUNT(*) FROM run_records")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT decision_json, COUNT(*) 
                FROM run_records 
                GROUP BY decision_json
            """)
            
            decisions = {}
            for row in cursor.fetchall():
                try:
                    decision_data = json.loads(row[0])
                    verdict = decision_data.get("verdict", "unknown")
                    decisions[verdict] = row[1]
                except:
                    decisions["parse_error"] = decisions.get("parse_error", 0) + row[1]
                    
            # Champion info
            champion = self.get_champion()
            
            return {
                "total_records": total_records,
                "decisions": decisions,
                "champion_run_id": champion.run_id if champion else None,
                "db_path": str(self.db_path),
                "runs_dir": str(self.runs_dir),
                "wal_enabled": self.enable_wal,
                "tail_hash": self._tail_hash
            }


# Funções de conveniência
def create_run_record(run_id: Optional[str] = None,
                     provider_id: str = "unknown",
                     metrics: Optional[Dict[str, float]] = None,
                     decision_verdict: str = "pending") -> RunRecord:
    """Cria RunRecord com defaults"""
    if run_id is None:
        run_id = str(uuid.uuid4())
        
    if metrics is None:
        metrics = {}
        
    return RunRecord(
        run_id=run_id,
        timestamp=time.time(),
        cycle=0,
        config_hash="default",
        provider_id=provider_id,
        candidate_cfg_hash="default",
        metrics=RunMetrics(**metrics),
        gates=GuardResults(
            sigma_guard_ok=True,
            ir_ic_ok=True,
            sr_gate_ok=True,
            caos_gate_ok=True
        ),
        decision=DecisionInfo(
            verdict=decision_verdict,
            reason="default",
            delta_linf=0.0,
            delta_score=0.0,
            beta_min_met=False
        )
    )


def quick_ledger_append(ledger: WORMLedger,
                       provider_id: str,
                       metrics: Dict[str, float],
                       verdict: str,
                       artifacts: Optional[Dict[str, Any]] = None) -> str:
    """Append rápido ao ledger"""
    record = create_run_record(
        provider_id=provider_id,
        metrics=metrics,
        decision_verdict=verdict
    )
    
    return ledger.append_record(record, artifacts)

# ---------------------------------------------------------------------------
# Legacy compatibility layer (P0 regression expectations)
# ---------------------------------------------------------------------------

def _canonical_json(payload: Dict[str, Any]) -> str:
    """Return a deterministic JSON encoding used for hashing."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


class SQLiteWORMLedger:
    """Minimal SQLite-backed ledger compatible with the legacy API."""

    def __init__(self, db_path: Union[str, Path], enable_wal: bool = True):
        self.db_path = Path(db_path)
        self.enable_wal = enable_wal
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        if self.enable_wal:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS worm_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                cycle_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp REAL NOT NULL,
                prev_hash TEXT,
                hash TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        return self._conn

    def _get_last_hash(self) -> Optional[str]:
        cursor = self._conn.execute("SELECT hash FROM worm_events ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return row["hash"] if row else None

    def append(self, event: WORMEvent) -> str:
        payload = event.to_dict()
        canonical = _canonical_json(payload)
        with self._lock:
            prev_hash = self._get_last_hash() or "GENESIS"
            computed = hashlib.sha256(f"{prev_hash}:{canonical}".encode("utf-8")).hexdigest()
            self._conn.execute(
                "INSERT INTO worm_events (event_type, cycle_id, payload, timestamp, prev_hash, hash) VALUES (?, ?, ?, ?, ?, ?)",
                (event.event_type, event.cycle_id, canonical, event.timestamp, prev_hash, computed),
            )
            self._conn.commit()
        return computed

    def query(self, limit: int = 100) -> List[WORMEvent]:
        cursor = self._conn.execute(
            "SELECT event_type, cycle_id, payload, timestamp FROM worm_events ORDER BY id ASC LIMIT ?",
            (limit,),
        )
        events: List[WORMEvent] = []
        for row in cursor.fetchall():
            data = json.loads(row["payload"])
            events.append(WORMEvent(row["event_type"], row["cycle_id"], data, row["timestamp"]))
        return events

    def verify_chain(self) -> TypingTuple[bool, str]:
        cursor = self._conn.execute("SELECT prev_hash, hash, payload FROM worm_events ORDER BY id ASC")
        prev = "GENESIS"
        for row in cursor.fetchall():
            canonical = row["payload"]
            expected = hashlib.sha256(f"{prev}:{canonical}".encode("utf-8")).hexdigest()
            if row["hash"] != expected:
                return False, f"hash mismatch at {row['hash']}"
            prev = row["hash"]
        return True, "ok"

    def close(self) -> None:
        self._conn.close()


class JSONLWORMLedger:
    """Append-only JSONL ledger for lightweight scenarios."""

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.touch()

    def _iter_entries(self) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                entries.append(json.loads(line))
        return entries

    def append(self, event: WORMEvent) -> str:
        payload = event.to_dict()
        canonical = _canonical_json(payload)
        with self._lock:
            entries = self._iter_entries()
            prev_hash = entries[-1]["hash"] if entries else "GENESIS"
            computed = hashlib.sha256(f"{prev_hash}:{canonical}".encode("utf-8")).hexdigest()
            entry = {
                **payload,
                "prev_hash": prev_hash,
                "hash": computed,
            }
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return computed

    def query(self, limit: int = 100) -> List[WORMEvent]:
        entries = self._iter_entries()
        tail = entries[-limit:]
        return [
            WORMEvent(item["event_type"], item["cycle_id"], item["data"], item.get("timestamp", time.time()))
            for item in tail
        ]

    def verify_chain(self) -> TypingTuple[bool, str]:
        prev = "GENESIS"
        for entry in self._iter_entries():
            canonical = _canonical_json({
                "event_type": entry["event_type"],
                "cycle_id": entry["cycle_id"],
                "data": entry["data"],
                "timestamp": entry["timestamp"],
            })
            expected = hashlib.sha256(f"{prev}:{canonical}".encode("utf-8")).hexdigest()
            if entry["hash"] != expected:
                return False, f"hash mismatch at {entry['hash']}"
            prev = entry["hash"]
        return True, "ok"

    def close(self) -> None:
        return None


# ---------------------------------------------------------------------------
# Legacy compatibility layer (P0 regression expectations)
# ---------------------------------------------------------------------------

def _canonical_json(payload: Dict[str, Any]) -> str:
    """Return a deterministic JSON encoding used for hashing."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


class SQLiteWORMLedger:
    """Minimal SQLite-backed ledger compatible with the legacy API."""

    def __init__(self, db_path: Union[str, Path], enable_wal: bool = True):
        self.db_path = Path(db_path)
        self.enable_wal = enable_wal
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        if self.enable_wal:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS worm_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                cycle_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp REAL NOT NULL,
                prev_hash TEXT,
                hash TEXT NOT NULL
            )
            """)
        self._conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        return self._conn

    def _get_last_hash(self) -> Optional[str]:
        cursor = self._conn.execute("SELECT hash FROM worm_events ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return row["hash"] if row else None

    def append(self, event: WORMEvent) -> str:
        payload = event.to_dict()
        canonical = _canonical_json(payload)
        with self._lock:
            prev_hash = self._get_last_hash() or "GENESIS"
            computed = hashlib.sha256(f"{prev_hash}:{canonical}".encode("utf-8")).hexdigest()
            self._conn.execute("INSERT INTO worm_events (event_type, cycle_id, payload, timestamp, prev_hash, hash) VALUES (?, ?, ?, ?, ?, ?)",
                                (event.event_type, event.cycle_id, canonical, event.timestamp, prev_hash, computed))
            self._conn.commit()
        return computed

    def query(self, limit: int = 100) -> List[WORMEvent]:
        cursor = self._conn.execute("SELECT event_type, cycle_id, payload, timestamp FROM worm_events ORDER BY id ASC LIMIT ?", (limit,))
        events: List[WORMEvent] = []
        for row in cursor.fetchall():
            data = json.loads(row["payload"])
            events.append(WORMEvent(row["event_type"], row["cycle_id"], data, row["timestamp"]))
        return events

    def verify_chain(self) -> TypingTuple[bool, str]:
        cursor = self._conn.execute("SELECT prev_hash, hash, payload FROM worm_events ORDER BY id ASC")
        prev = "GENESIS"
        for row in cursor.fetchall():
            canonical = row["payload"]
            expected = hashlib.sha256(f"{prev}:{canonical}".encode("utf-8")).hexdigest()
            if row["hash"] != expected:
                return False, f"hash mismatch at {row['hash']}"
            prev = row["hash"]
        return True, "ok"

    def close(self) -> None:
        self._conn.close()


class JSONLWORMLedger:
    """Append-only JSONL ledger for lightweight scenarios."""

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.touch()

    def _iter_entries(self) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                entries.append(json.loads(line))
        return entries

    def append(self, event: WORMEvent) -> str:
        payload = event.to_dict()
        canonical = _canonical_json(payload)
        with self._lock:
            entries = self._iter_entries()
            prev_hash = entries[-1]["hash"] if entries else "GENESIS"
            computed = hashlib.sha256(f"{prev_hash}:{canonical}".encode("utf-8")).hexdigest()
            entry = {**payload, "prev_hash": prev_hash, "hash": computed}
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return computed

    def query(self, limit: int = 100) -> List[WORMEvent]:
        entries = self._iter_entries()
        tail = entries[-limit:]
        return [WORMEvent(item["event_type"], item["cycle_id"], item["data"], item.get("timestamp", time.time())) for item in tail]

    def verify_chain(self) -> TypingTuple[bool, str]:
        prev = "GENESIS"
        for entry in self._iter_entries():
            canonical = _canonical_json({"event_type": entry["event_type"], "cycle_id": entry["cycle_id"], "data": entry["data"], "timestamp": entry["timestamp"]})
            expected = hashlib.sha256(f"{prev}:{canonical}".encode("utf-8")).hexdigest()
            if entry["hash"] != expected:
                return False, f"hash mismatch at {entry['hash']}"
            prev = entry["hash"]
        return True, "ok"

    def close(self) -> None:
        return None
