# penin/omega/swarm.py
"""
Swarm Cognitivo - Gossip Local e Agregação Global
================================================

Implementa swarm cognitivo com gossip protocol local usando SQLite/WORM.
Permite que múltiplos nós lógicos (na mesma máquina ou distribuídos)
compartilhem métricas e computem estado global G.

Características:
- Heartbeat de nós com payload de métricas
- Agregação temporal com janela deslizante
- Persistência em SQLite (~/.penin_omega/state/heartbeats.db)
- Integração com WORM ledger
- Detecção de nós inativos
- Cálculo de coerência global G
"""

import os
import sqlite3
import time
import random
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class NodeStatus(Enum):
    """Status de um nó no swarm"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class SwarmNode:
    """Representação de um nó no swarm"""
    node_id: str
    last_seen: float
    status: NodeStatus
    payload: Dict[str, Any]
    heartbeat_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "last_seen": self.last_seen,
            "status": self.status.value,
            "payload": self.payload,
            "heartbeat_count": self.heartbeat_count
        }
    
    def is_alive(self, timeout: float = 120.0) -> bool:
        """Verifica se o nó está vivo baseado no último heartbeat"""
        return (time.time() - self.last_seen) < timeout


# Configuração global
ROOT = Path(os.getenv("PENIN_ROOT", Path.home() / ".penin_omega"))
DB_PATH = ROOT / "state" / "heartbeats.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _init_db():
    """Inicializa banco de dados SQLite"""
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS heartbeats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                payload TEXT NOT NULL,
                hash TEXT,
                created_at REAL DEFAULT (julianday('now'))
            )
        """)
        
        con.execute("""
            CREATE INDEX IF NOT EXISTS idx_heartbeats_node_time 
            ON heartbeats(node_id, timestamp DESC)
        """)
        
        con.execute("""
            CREATE INDEX IF NOT EXISTS idx_heartbeats_time 
            ON heartbeats(timestamp DESC)
        """)
        
        con.commit()


def _hash_payload(payload: Dict[str, Any]) -> str:
    """Gera hash do payload para integridade"""
    payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload_str.encode()).hexdigest()[:16]


def heartbeat(node_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envia heartbeat de um nó com payload de métricas
    
    Args:
        node_id: Identificador único do nó
        payload: Métricas e dados do nó (phi, sr, G, etc.)
        
    Returns:
        Confirmação do heartbeat
    """
    _init_db()
    
    timestamp = time.time()
    payload_json = json.dumps(payload, ensure_ascii=False)
    payload_hash = _hash_payload(payload)
    
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO heartbeats(node_id, timestamp, payload, hash) VALUES(?, ?, ?, ?)",
            (node_id, timestamp, payload_json, payload_hash)
        )
        con.commit()
        
        # Limpar heartbeats antigos (manter últimos 1000 por nó)
        con.execute("""
            DELETE FROM heartbeats 
            WHERE node_id = ? AND id NOT IN (
                SELECT id FROM heartbeats 
                WHERE node_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1000
            )
        """, (node_id, node_id))
        con.commit()
    
    return {
        "node_id": node_id,
        "timestamp": timestamp,
        "hash": payload_hash,
        "status": "recorded"
    }


def sample_global_state(window_s: float = 60.0, min_nodes: int = 1) -> Dict[str, Any]:
    """
    Agrega estado global do swarm em janela temporal
    
    Args:
        window_s: Janela temporal em segundos
        min_nodes: Mínimo de nós ativos para considerar válido
        
    Returns:
        Estado global agregado
    """
    _init_db()
    
    t0 = time.time() - window_s
    
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(
            "SELECT node_id, payload, timestamp FROM heartbeats WHERE timestamp >= ? ORDER BY timestamp DESC",
            (t0,)
        )
        rows = cur.fetchall()
    
    if not rows:
        return {
            "timestamp": time.time(),
            "window_s": window_s,
            "active_nodes": 0,
            "global_state": {},
            "status": "no_data"
        }
    
    # Agrupar por nó (pegar o mais recente de cada)
    nodes_data = {}
    for node_id, payload_json, timestamp in rows:
        if node_id not in nodes_data or timestamp > nodes_data[node_id]["timestamp"]:
            try:
                payload = json.loads(payload_json)
                nodes_data[node_id] = {
                    "payload": payload,
                    "timestamp": timestamp
                }
            except json.JSONDecodeError:
                continue
    
    active_nodes = len(nodes_data)
    
    if active_nodes < min_nodes:
        return {
            "timestamp": time.time(),
            "window_s": window_s,
            "active_nodes": active_nodes,
            "global_state": {},
            "status": "insufficient_nodes",
            "min_required": min_nodes
        }
    
    # Agregação das métricas
    aggregated = {}
    metric_counts = {}
    
    for node_id, data in nodes_data.items():
        payload = data["payload"]
        for key, value in payload.items():
            try:
                float_value = float(value)
                if key not in aggregated:
                    aggregated[key] = 0.0
                    metric_counts[key] = 0
                aggregated[key] += float_value
                metric_counts[key] += 1
            except (ValueError, TypeError):
                # Ignorar valores não numéricos
                continue
    
    # Calcular médias
    global_state = {}
    for key, total in aggregated.items():
        count = metric_counts[key]
        global_state[key] = total / count if count > 0 else 0.0
    
    # Calcular coerência global G (média harmônica das métricas principais)
    main_metrics = ["phi", "sr", "caos", "ethics"]
    main_values = []
    
    for metric in main_metrics:
        if metric in global_state and global_state[metric] > 0:
            main_values.append(global_state[metric])
    
    if main_values:
        # Média harmônica
        G = len(main_values) / sum(1.0 / max(1e-9, v) for v in main_values)
    else:
        G = 0.0
    
    global_state["G"] = G
    
    return {
        "timestamp": time.time(),
        "window_s": window_s,
        "active_nodes": active_nodes,
        "nodes": list(nodes_data.keys()),
        "global_state": global_state,
        "status": "aggregated"
    }


def get_swarm_nodes(timeout: float = 120.0) -> List[SwarmNode]:
    """
    Retorna lista de nós ativos no swarm
    
    Args:
        timeout: Timeout para considerar nó inativo (segundos)
        
    Returns:
        Lista de nós com status
    """
    _init_db()
    
    current_time = time.time()
    cutoff_time = current_time - timeout
    
    with sqlite3.connect(DB_PATH) as con:
        # Pegar último heartbeat de cada nó
        cur = con.execute("""
            SELECT node_id, MAX(timestamp) as last_seen, payload, COUNT(*) as heartbeat_count
            FROM heartbeats 
            GROUP BY node_id
            ORDER BY last_seen DESC
        """)
        rows = cur.fetchall()
    
    nodes = []
    for node_id, last_seen, payload_json, heartbeat_count in rows:
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            payload = {}
        
        # Determinar status
        if last_seen >= cutoff_time:
            status = NodeStatus.ACTIVE
        elif last_seen >= (cutoff_time - timeout):  # Grace period
            status = NodeStatus.INACTIVE
        else:
            status = NodeStatus.FAILED
        
        node = SwarmNode(
            node_id=node_id,
            last_seen=last_seen,
            status=status,
            payload=payload,
            heartbeat_count=heartbeat_count
        )
        
        nodes.append(node)
    
    return nodes


def swarm_health_check() -> Dict[str, Any]:
    """
    Verifica saúde geral do swarm
    
    Returns:
        Relatório de saúde do swarm
    """
    nodes = get_swarm_nodes()
    global_state = sample_global_state()
    
    active_count = sum(1 for n in nodes if n.status == NodeStatus.ACTIVE)
    inactive_count = sum(1 for n in nodes if n.status == NodeStatus.INACTIVE)
    failed_count = sum(1 for n in nodes if n.status == NodeStatus.FAILED)
    
    total_nodes = len(nodes)
    
    # Calcular métricas de saúde
    if total_nodes > 0:
        active_ratio = active_count / total_nodes
        health_score = active_ratio * global_state["global_state"].get("G", 0.0)
    else:
        active_ratio = 0.0
        health_score = 0.0
    
    # Determinar status geral
    if active_count >= 3 and active_ratio >= 0.8 and health_score >= 0.7:
        overall_status = "excellent"
    elif active_count >= 2 and active_ratio >= 0.6 and health_score >= 0.5:
        overall_status = "good"
    elif active_count >= 1 and active_ratio >= 0.4:
        overall_status = "fair"
    else:
        overall_status = "poor"
    
    return {
        "timestamp": time.time(),
        "overall_status": overall_status,
        "health_score": health_score,
        "nodes": {
            "total": total_nodes,
            "active": active_count,
            "inactive": inactive_count,
            "failed": failed_count,
            "active_ratio": active_ratio
        },
        "global_state": global_state["global_state"],
        "recommendations": _generate_swarm_recommendations(
            active_count, inactive_count, failed_count, health_score
        )
    }


def _generate_swarm_recommendations(active: int, inactive: int, failed: int, health_score: float) -> List[str]:
    """Gera recomendações baseadas no estado do swarm"""
    recommendations = []
    
    if active < 2:
        recommendations.append("Consider adding more active nodes for redundancy")
    
    if failed > 0:
        recommendations.append(f"Investigate {failed} failed nodes")
    
    if health_score < 0.5:
        recommendations.append("Global coherence is low - check individual node metrics")
    
    if inactive > active:
        recommendations.append("More nodes are inactive than active - check network connectivity")
    
    return recommendations


def cleanup_old_heartbeats(days_to_keep: int = 7) -> Dict[str, Any]:
    """
    Remove heartbeats antigos para manter banco limpo
    
    Args:
        days_to_keep: Dias de histórico para manter
        
    Returns:
        Relatório da limpeza
    """
    _init_db()
    
    cutoff_time = time.time() - (days_to_keep * 24 * 3600)
    
    with sqlite3.connect(DB_PATH) as con:
        # Contar registros antes
        cur = con.execute("SELECT COUNT(*) FROM heartbeats WHERE timestamp < ?", (cutoff_time,))
        old_count = cur.fetchone()[0]
        
        # Remover registros antigos
        con.execute("DELETE FROM heartbeats WHERE timestamp < ?", (cutoff_time,))
        deleted_count = con.total_changes
        con.commit()
        
        # Vacuum para recuperar espaço
        con.execute("VACUUM")
    
    return {
        "timestamp": time.time(),
        "days_kept": days_to_keep,
        "old_records_found": old_count,
        "records_deleted": deleted_count,
        "status": "cleaned"
    }


class SwarmManager:
    """
    Gerenciador do Swarm Cognitivo
    
    Facilita operações de alto nível no swarm
    """
    
    def __init__(self, node_id: str, heartbeat_interval: float = 30.0):
        self.node_id = node_id
        self.heartbeat_interval = heartbeat_interval
        self.last_heartbeat = 0
        self.metrics_cache = {}
        
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Atualiza cache de métricas locais"""
        self.metrics_cache.update(metrics)
        
    def send_heartbeat(self, additional_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Envia heartbeat com métricas atuais
        
        Args:
            additional_metrics: Métricas adicionais para este heartbeat
            
        Returns:
            Confirmação do heartbeat
        """
        payload = self.metrics_cache.copy()
        
        if additional_metrics:
            payload.update(additional_metrics)
        
        # Adicionar metadados do nó
        payload.update({
            "node_id": self.node_id,
            "heartbeat_interval": self.heartbeat_interval,
            "local_time": time.time()
        })
        
        result = heartbeat(self.node_id, payload)
        self.last_heartbeat = time.time()
        
        return result
    
    def should_send_heartbeat(self) -> bool:
        """Verifica se é hora de enviar heartbeat"""
        return (time.time() - self.last_heartbeat) >= self.heartbeat_interval
    
    def get_global_coherence(self, window_s: float = 60.0) -> float:
        """
        Obtém coerência global G do swarm
        
        Args:
            window_s: Janela temporal para agregação
            
        Returns:
            Valor de G (coerência global)
        """
        global_state = sample_global_state(window_s)
        return global_state["global_state"].get("G", 0.0)
    
    def auto_heartbeat_loop(self, duration: float = 300.0) -> Dict[str, Any]:
        """
        Loop automático de heartbeats por duração especificada
        
        Args:
            duration: Duração em segundos
            
        Returns:
            Relatório do loop
        """
        start_time = time.time()
        heartbeats_sent = 0
        
        while (time.time() - start_time) < duration:
            if self.should_send_heartbeat():
                self.send_heartbeat()
                heartbeats_sent += 1
            
            time.sleep(min(5.0, self.heartbeat_interval / 4))  # Sleep adaptativo
        
        return {
            "duration": duration,
            "heartbeats_sent": heartbeats_sent,
            "final_global_G": self.get_global_coherence()
        }


# Funções de conveniência
def quick_swarm_test() -> Dict[str, Any]:
    """Teste rápido da funcionalidade do swarm"""
    
    # Simular 3 nós enviando heartbeats
    nodes = ["node-A", "node-B", "node-C"]
    
    for i, node_id in enumerate(nodes):
        metrics = {
            "phi": 0.7 + i * 0.1,
            "sr": 0.8 + i * 0.05,
            "caos": 0.6 + i * 0.15,
            "ethics": 0.9 + i * 0.02
        }
        heartbeat(node_id, metrics)
        time.sleep(0.1)  # Pequeno delay
    
    # Aguardar e amostrar estado global
    time.sleep(0.5)
    global_state = sample_global_state(window_s=10.0)
    
    # Verificar saúde
    health = swarm_health_check()
    
    return {
        "nodes_simulated": len(nodes),
        "global_state": global_state,
        "health": health,
        "test_status": "completed"
    }


def validate_swarm_aggregation() -> Dict[str, Any]:
    """
    Valida que a agregação do swarm funciona corretamente
    
    Testa se métricas são agregadas corretamente e G é calculado
    """
    # Limpar dados antigos
    cleanup_old_heartbeats(0)  # Remove tudo
    
    # Enviar heartbeats com valores conhecidos
    test_data = [
        ("test-node-1", {"phi": 0.8, "sr": 0.9, "caos": 0.7, "ethics": 0.95}),
        ("test-node-2", {"phi": 0.6, "sr": 0.7, "caos": 0.8, "ethics": 0.85}),
        ("test-node-3", {"phi": 0.9, "sr": 0.8, "caos": 0.6, "ethics": 0.90})
    ]
    
    for node_id, metrics in test_data:
        heartbeat(node_id, metrics)
    
    # Amostrar estado global
    global_state = sample_global_state(window_s=10.0)
    
    # Verificar se agregação está correta
    expected_phi = (0.8 + 0.6 + 0.9) / 3  # 0.7667
    expected_sr = (0.9 + 0.7 + 0.8) / 3   # 0.8
    
    actual_phi = global_state["global_state"].get("phi", 0)
    actual_sr = global_state["global_state"].get("sr", 0)
    actual_G = global_state["global_state"].get("G", 0)
    
    phi_correct = abs(actual_phi - expected_phi) < 0.01
    sr_correct = abs(actual_sr - expected_sr) < 0.01
    G_reasonable = 0.5 < actual_G < 1.0  # G deve estar em range razoável
    
    return {
        "test": "swarm_aggregation",
        "expected": {"phi": expected_phi, "sr": expected_sr},
        "actual": {"phi": actual_phi, "sr": actual_sr, "G": actual_G},
        "validation": {
            "phi_correct": phi_correct,
            "sr_correct": sr_correct,
            "G_reasonable": G_reasonable,
            "all_passed": phi_correct and sr_correct and G_reasonable
        },
        "global_state_full": global_state
    }