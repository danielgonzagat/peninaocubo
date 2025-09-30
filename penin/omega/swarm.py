"""
Swarm Cognitivo - Gossip e Agregação Global
============================================

Sistema de heartbeat e gossip entre nós cognitivos.
Persistência em SQLite, agregação de métricas globais (G).
"""

import os
import sqlite3
import time
import json
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass


ROOT = Path(os.getenv("PENIN_ROOT", Path.home() / ".penin_omega"))
DB = ROOT / "state" / "heartbeats.db"
DB.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class HeartbeatMessage:
    """Mensagem de heartbeat de um nó"""
    node: str
    timestamp: float
    payload: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node": self.node,
            "timestamp": self.timestamp,
            "payload": self.payload
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HeartbeatMessage":
        return cls(
            node=data["node"],
            timestamp=data["timestamp"],
            payload=data["payload"]
        )


def _init_db():
    """Inicializa banco de dados de heartbeats"""
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS hb (
                node TEXT,
                ts REAL,
                payload TEXT
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_hb_ts ON hb(ts)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_hb_node ON hb(node)")
        con.commit()


def heartbeat(node: str, payload: Dict[str, Any]) -> None:
    """
    Envia heartbeat de um nó.
    
    Args:
        node: Identificador do nó
        payload: Dicionário com métricas/estado
    """
    _init_db()
    ts = time.time()
    
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO hb(node, ts, payload) VALUES(?, ?, ?)",
            (node, ts, json.dumps(payload))
        )
        con.commit()


def sample_global_state(window_s: float = 60.0) -> Dict[str, float]:
    """
    Agrega estado global de todos os nós na janela temporal.
    
    Args:
        window_s: Janela de tempo em segundos
        
    Returns:
        Dict com médias das métricas dos nós
    """
    _init_db()
    t0 = time.time() - window_s
    
    with sqlite3.connect(DB) as con:
        cur = con.execute("SELECT payload FROM hb WHERE ts >= ?", (t0,))
        data = [json.loads(r[0]) for r in cur.fetchall()]
    
    if not data:
        return {}
    
    # Agregação simples (média de métricas)
    agg = {}
    for p in data:
        for k, v in p.items():
            try:
                agg[k] = agg.get(k, 0.0) + float(v)
            except (TypeError, ValueError):
                pass
    
    n = max(1, len(data))
    return {k: (v / n) for k, v in agg.items()}


def get_nodes(window_s: float = 60.0) -> List[str]:
    """
    Retorna lista de nós ativos na janela temporal.
    
    Args:
        window_s: Janela de tempo em segundos
        
    Returns:
        Lista de identificadores de nós
    """
    _init_db()
    t0 = time.time() - window_s
    
    with sqlite3.connect(DB) as con:
        cur = con.execute("SELECT DISTINCT node FROM hb WHERE ts >= ?", (t0,))
        return [r[0] for r in cur.fetchall()]


def get_node_history(node: str, window_s: float = 60.0) -> List[HeartbeatMessage]:
    """
    Retorna histórico de heartbeats de um nó.
    
    Args:
        node: Identificador do nó
        window_s: Janela de tempo em segundos
        
    Returns:
        Lista de HeartbeatMessage
    """
    _init_db()
    t0 = time.time() - window_s
    
    with sqlite3.connect(DB) as con:
        cur = con.execute(
            "SELECT node, ts, payload FROM hb WHERE node = ? AND ts >= ? ORDER BY ts DESC",
            (node, t0)
        )
        
        messages = []
        for row in cur.fetchall():
            msg = HeartbeatMessage(
                node=row[0],
                timestamp=row[1],
                payload=json.loads(row[2])
            )
            messages.append(msg)
        
        return messages


def cleanup_old_heartbeats(max_age_s: float = 3600.0) -> int:
    """
    Remove heartbeats antigos.
    
    Args:
        max_age_s: Idade máxima em segundos
        
    Returns:
        Número de registros removidos
    """
    _init_db()
    t0 = time.time() - max_age_s
    
    with sqlite3.connect(DB) as con:
        cur = con.execute("DELETE FROM hb WHERE ts < ?", (t0,))
        con.commit()
        return cur.rowcount


class SwarmCoordinator:
    """Coordenador do swarm cognitivo"""
    
    def __init__(self, node_id: str, heartbeat_interval: float = 5.0):
        self.node_id = node_id
        self.heartbeat_interval = heartbeat_interval
        self.last_heartbeat = 0.0
    
    def send_heartbeat(self, metrics: Dict[str, Any]) -> None:
        """Envia heartbeat com métricas atuais"""
        heartbeat(self.node_id, metrics)
        self.last_heartbeat = time.time()
    
    def should_send_heartbeat(self) -> bool:
        """Verifica se deve enviar heartbeat"""
        return (time.time() - self.last_heartbeat) >= self.heartbeat_interval
    
    def get_global_metrics(self, window_s: float = 60.0) -> Dict[str, float]:
        """Obtém métricas globais agregadas"""
        return sample_global_state(window_s)
    
    def get_active_nodes(self, window_s: float = 60.0) -> List[str]:
        """Obtém lista de nós ativos"""
        return get_nodes(window_s)
    
    def get_swarm_size(self, window_s: float = 60.0) -> int:
        """Retorna tamanho do swarm"""
        return len(self.get_active_nodes(window_s))
    
    def get_consensus_estimate(self, key: str, window_s: float = 60.0) -> float:
        """
        Estima consenso para uma métrica específica.
        
        Args:
            key: Chave da métrica
            window_s: Janela de tempo
            
        Returns:
            Valor médio da métrica no swarm
        """
        global_state = self.get_global_metrics(window_s)
        return global_state.get(key, 0.0)


def compute_global_coherence(window_s: float = 60.0) -> float:
    """
    Computa coerência global G do swarm.
    
    G é a média harmônica das métricas chave dos nós.
    
    Args:
        window_s: Janela de tempo
        
    Returns:
        Coerência global [0, 1]
    """
    global_state = sample_global_state(window_s)
    
    if not global_state:
        return 0.5  # Neutral quando não há dados
    
    # Métricas chave para coerência
    key_metrics = ["phi", "sr", "accuracy", "stability"]
    
    values = []
    for key in key_metrics:
        if key in global_state:
            values.append(max(0.01, global_state[key]))
    
    if not values:
        return 0.5
    
    # Média harmônica
    harmonic = len(values) / sum(1.0 / v for v in values)
    return max(0.0, min(1.0, harmonic))