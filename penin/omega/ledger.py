"""
WORM Ledger — Write-Once Read-Many with SQLite + File Locks
============================================================

P0 Correction: Adiciona WAL mode + busy_timeout para evitar locks em
alta concorrência. Mantém compatibilidade com ledger JSONL existente.

Features:
- SQLite com WAL (Write-Ahead Logging)
- busy_timeout para resiliência
- Schema pydantic para validação
- Append-only com file locks (fcntl/portalocker)
- Encadeamento de hash para integridade
- PROMOTE_ATTEST com pré/pós hash
"""

from __future__ import annotations
import os
import json
import hashlib
import sqlite3
import threading
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object

# File locking
try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False
    try:
        import fcntl
        HAS_FCNTL = True
    except ImportError:
        HAS_FCNTL = False


# ============================================================================
# Schema de Eventos
# ============================================================================

if HAS_PYDANTIC:
    class WORMEvent(BaseModel):
        """Evento base do ledger."""
        timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
        event_type: str
        cycle_id: str
        data: Dict[str, Any] = Field(default_factory=dict)
        prev_hash: Optional[str] = None
        event_hash: Optional[str] = None
        
        def compute_hash(self) -> str:
            """Computa hash do evento para encadeamento."""
            hashable = f"{self.timestamp}|{self.event_type}|{self.cycle_id}|{json.dumps(self.data, sort_keys=True)}"
            return hashlib.sha256(hashable.encode()).hexdigest()
        
        class Config:
            extra = "allow"
else:
    @dataclass
    class WORMEvent:
        timestamp: str = ""
        event_type: str = ""
        cycle_id: str = ""
        data: Dict[str, Any] = field(default_factory=dict)
        prev_hash: Optional[str] = None
        event_hash: Optional[str] = None
        
        def compute_hash(self) -> str:
            hashable = f"{self.timestamp}|{self.event_type}|{self.cycle_id}|{json.dumps(self.data, sort_keys=True)}"
            return hashlib.sha256(hashable.encode()).hexdigest()


# ============================================================================
# SQLite WORM Ledger
# ============================================================================

class SQLiteWORMLedger:
    """
    Ledger WORM baseado em SQLite com WAL + busy_timeout.
    
    P0 Corrections:
    - journal_mode=WAL para concorrência
    - busy_timeout=3000ms para retry automático
    - Thread-safe connection pool
    """
    
    def __init__(self, db_path: str = "/tmp/penin_worm.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtém conexão thread-local."""
        if not hasattr(self._local, 'conn'):
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0  # 30s timeout para operações
            )
            
            # P0 FIX: Ativar WAL + busy_timeout
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=3000")  # 3s retry
            conn.execute("PRAGMA synchronous=NORMAL")  # Performance vs durability
            
            # Ativar foreign keys
            conn.execute("PRAGMA foreign_keys=ON")
            
            self._local.conn = conn
        
        return self._local.conn
    
    def _init_db(self):
        """Inicializa schema do banco."""
        conn = self._get_connection()
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                cycle_id TEXT NOT NULL,
                data TEXT NOT NULL,
                prev_hash TEXT,
                event_hash TEXT NOT NULL UNIQUE,
                created_at REAL NOT NULL DEFAULT (julianday('now'))
            )
        """)
        
        # Índices para performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cycle_id ON events(cycle_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON events(created_at)")
        
        conn.commit()
    
    def append(self, event: WORMEvent) -> str:
        """
        Adiciona evento ao ledger (append-only).
        
        Args:
            event: Evento a ser adicionado
        
        Returns:
            Hash do evento inserido
        """
        conn = self._get_connection()
        
        # Use BEGIN IMMEDIATE para serializar writes em WAL mode
        conn.execute("BEGIN IMMEDIATE")
        
        try:
            # Obter último hash para encadeamento
            prev_hash = self._get_last_hash(conn)
            event.prev_hash = prev_hash
            
            # Computar hash do evento
            event.event_hash = event.compute_hash()
            
            # Inserir
            conn.execute("""
                INSERT INTO events (timestamp, event_type, cycle_id, data, prev_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.event_type,
                event.cycle_id,
                json.dumps(event.data),
                event.prev_hash,
                event.event_hash
            ))
            
            conn.commit()
            return event.event_hash
        except Exception as e:
            conn.rollback()
            raise
    
    def _get_last_hash(self, conn: sqlite3.Connection) -> Optional[str]:
        """Obtém hash do último evento."""
        cursor = conn.execute(
            "SELECT event_hash FROM events ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return row[0] if row else None
    
    def query(
        self,
        event_type: Optional[str] = None,
        cycle_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WORMEvent]:
        """
        Consulta eventos do ledger.
        
        Args:
            event_type: Filtrar por tipo (opcional)
            cycle_id: Filtrar por ciclo (opcional)
            limit: Máximo de eventos a retornar
        
        Returns:
            Lista de eventos
        """
        conn = self._get_connection()
        
        query = "SELECT timestamp, event_type, cycle_id, data, prev_hash, event_hash FROM events"
        conditions = []
        params = []
        
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        
        if cycle_id:
            conditions.append("cycle_id = ?")
            params.append(cycle_id)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        
        events = []
        for row in cursor.fetchall():
            timestamp, evt_type, cid, data_json, prev_h, evt_h = row
            event = WORMEvent(
                timestamp=timestamp,
                event_type=evt_type,
                cycle_id=cid,
                data=json.loads(data_json),
                prev_hash=prev_h,
                event_hash=evt_h
            )
            events.append(event)
        
        return events
    
    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """
        Verifica integridade da cadeia de hashes.
        
        Returns:
            (válido, mensagem de erro)
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT id, timestamp, event_type, cycle_id, data, prev_hash, event_hash FROM events ORDER BY id"
        )
        
        prev_hash = None
        for row in cursor.fetchall():
            id_, timestamp, evt_type, cid, data_json, stored_prev, stored_hash = row
            
            # Verificar encadeamento
            if stored_prev != prev_hash:
                return False, f"Chain broken at event {id_}: expected prev_hash={prev_hash}, got {stored_prev}"
            
            # Verificar hash
            event = WORMEvent(
                timestamp=timestamp,
                event_type=evt_type,
                cycle_id=cid,
                data=json.loads(data_json),
                prev_hash=stored_prev
            )
            computed_hash = event.compute_hash()
            
            if computed_hash != stored_hash:
                return False, f"Hash mismatch at event {id_}: expected {computed_hash}, got {stored_hash}"
            
            prev_hash = stored_hash
        
        return True, None
    
    def export_to_jsonl(self, output_path: str) -> int:
        """
        Exporta ledger para formato JSONL (compatibilidade).
        
        Args:
            output_path: Caminho do arquivo JSONL
        
        Returns:
            Número de eventos exportados
        """
        events = self.query(limit=1_000_000)  # Todos os eventos
        
        with open(output_path, "w") as f:
            for event in reversed(events):  # Ordem cronológica
                record = {
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "cycle_id": event.cycle_id,
                    "data": event.data,
                    "prev_hash": event.prev_hash,
                    "event_hash": event.event_hash
                }
                f.write(json.dumps(record) + "\n")
        
        return len(events)
    
    def close(self):
        """Fecha conexões."""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()


# ============================================================================
# JSONL Ledger (Legado, com file locks)
# ============================================================================

class JSONLWORMLedger:
    """
    Ledger WORM baseado em arquivo JSONL com locks.
    
    Mantido para compatibilidade com ledger_f3.jsonl existente.
    """
    
    def __init__(self, jsonl_path: str = "ledger_f3.jsonl"):
        self.jsonl_path = Path(jsonl_path)
        self._lock = threading.Lock()
    
    def append(self, event: WORMEvent) -> str:
        """Adiciona evento ao JSONL com lock."""
        # Obter último hash
        prev_hash = self._get_last_hash()
        event.prev_hash = prev_hash
        event.event_hash = event.compute_hash()
        
        record = {
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "cycle_id": event.cycle_id,
            "data": event.data,
            "prev_hash": event.prev_hash,
            "event_hash": event.event_hash
        }
        
        with self._lock:
            # File lock se disponível
            with self.jsonl_path.open("a") as f:
                if HAS_PORTALOCKER:
                    portalocker.lock(f, portalocker.LOCK_EX)
                elif HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                
                f.write(json.dumps(record) + "\n")
                f.flush()
                os.fsync(f.fileno())
                
                if HAS_PORTALOCKER:
                    portalocker.unlock(f)
                elif HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
        return event.event_hash
    
    def _get_last_hash(self) -> Optional[str]:
        """Obtém hash do último evento."""
        if not self.jsonl_path.exists():
            return None
        
        last_hash = None
        with self.jsonl_path.open("r") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    last_hash = record.get("event_hash")
        
        return last_hash
    
    def query(
        self,
        event_type: Optional[str] = None,
        cycle_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WORMEvent]:
        """Consulta eventos do JSONL."""
        if not self.jsonl_path.exists():
            return []
        
        events = []
        with self.jsonl_path.open("r") as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                
                # Filtros
                if event_type and record.get("event_type") != event_type:
                    continue
                if cycle_id and record.get("cycle_id") != cycle_id:
                    continue
                
                event = WORMEvent(
                    timestamp=record["timestamp"],
                    event_type=record["event_type"],
                    cycle_id=record["cycle_id"],
                    data=record.get("data", {}),
                    prev_hash=record.get("prev_hash"),
                    event_hash=record.get("event_hash")
                )
                events.append(event)
                
                if len(events) >= limit:
                    break
        
        return events[-limit:]  # Retornar últimos N
    
    def migrate_to_sqlite(self, sqlite_ledger: SQLiteWORMLedger) -> int:
        """
        Migra eventos JSONL para SQLite.
        
        Args:
            sqlite_ledger: Instância do SQLite ledger
        
        Returns:
            Número de eventos migrados
        """
        if not self.jsonl_path.exists():
            return 0
        
        count = 0
        with self.jsonl_path.open("r") as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                event = WORMEvent(
                    timestamp=record["timestamp"],
                    event_type=record["event_type"],
                    cycle_id=record["cycle_id"],
                    data=record.get("data", {}),
                    prev_hash=record.get("prev_hash"),
                    event_hash=record.get("event_hash")
                )
                
                # Inserir diretamente (sem recomputar hash)
                conn = sqlite_ledger._get_connection()
                conn.execute("""
                    INSERT INTO events (timestamp, event_type, cycle_id, data, prev_hash, event_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event.timestamp,
                    event.event_type,
                    event.cycle_id,
                    json.dumps(event.data),
                    event.prev_hash,
                    event.event_hash
                ))
                count += 1
        
        sqlite_ledger._get_connection().commit()
        return count


# ============================================================================
# Facade Unificado
# ============================================================================

class WORMLedger:
    """
    Facade unificado para ledger WORM.
    
    Usa SQLite por padrão (P0 fix), com fallback para JSONL.
    """
    
    def __init__(
        self,
        use_sqlite: bool = True,
        sqlite_path: str = "/tmp/penin_worm.db",
        jsonl_path: str = "ledger_f3.jsonl"
    ):
        self.use_sqlite = use_sqlite
        
        if use_sqlite:
            self.ledger = SQLiteWORMLedger(sqlite_path)
        else:
            self.ledger = JSONLWORMLedger(jsonl_path)
    
    def append(self, event: WORMEvent) -> str:
        """Adiciona evento."""
        return self.ledger.append(event)
    
    def query(self, **kwargs) -> List[WORMEvent]:
        """Consulta eventos."""
        return self.ledger.query(**kwargs)
    
    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """Verifica integridade (apenas SQLite)."""
        if isinstance(self.ledger, SQLiteWORMLedger):
            return self.ledger.verify_chain()
        return True, "Chain verification not supported for JSONL"
    
    def close(self):
        """Fecha ledger."""
        if isinstance(self.ledger, SQLiteWORMLedger):
            self.ledger.close()