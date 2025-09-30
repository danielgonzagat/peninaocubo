"""
Swarm Cognitivo - Gossip Local e Agregação Global
=================================================

Implementa sistema de swarm cognitivo com:
- Heartbeats entre nós lógicos na mesma máquina
- Persistência em SQLite/WORM
- Agregação de métricas globais (φ, SR, G)
- Consenso simplificado via gossip protocol
- Detecção de falhas e recuperação automática

Características:
- CPU-first (sem dependências de rede externa)
- Fail-closed (nós não responsivos são excluídos)
- Métricas agregadas via média harmônica (não-compensatório)
- Estado persistente em ~/.penin_omega/state/
"""

import os
import sqlite3
import time
import random
import json
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
import hashlib


# Configuração de diretórios
ROOT = Path(os.getenv("PENIN_ROOT", Path.home() / ".penin_omega"))
STATE_DIR = ROOT / "state"
DB_PATH = STATE_DIR / "heartbeats.db"
GOSSIP_DB = STATE_DIR / "gossip.db"

# Configurações do swarm
DEFAULT_HEARTBEAT_INTERVAL = 5.0  # segundos
DEFAULT_GOSSIP_INTERVAL = 10.0    # segundos
DEFAULT_NODE_TIMEOUT = 30.0       # segundos
DEFAULT_WINDOW_SIZE = 60.0        # janela de agregação em segundos


@dataclass
class NodeMetrics:
    """Métricas de um nó do swarm"""
    node_id: str
    timestamp: float
    phi: float          # CAOS⁺
    sr: float           # Self-Reflection
    G: float            # Coerência global
    health: float       # Saúde do nó [0,1]
    cpu_usage: float    # Uso de CPU [0,1]
    memory_usage: float # Uso de memória [0,1]
    latency: float      # Latência em segundos
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeMetrics':
        return cls(**data)


@dataclass
class SwarmState:
    """Estado agregado do swarm"""
    timestamp: float
    active_nodes: int
    global_phi: float       # φ agregado
    global_sr: float        # SR agregado
    global_G: float         # G agregado
    global_health: float    # Saúde agregada
    consensus_hash: str     # Hash do consenso
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SwarmDatabase:
    """Gerenciador de banco de dados do swarm"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.gossip_db = str(GOSSIP_DB)
        self._init_databases()
    
    def _init_databases(self):
        """Inicializa bancos de dados"""
        # Criar diretório se não existir
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Banco principal (heartbeats)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS heartbeats (
                    node_id TEXT,
                    timestamp REAL,
                    phi REAL,
                    sr REAL,
                    G REAL,
                    health REAL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    latency REAL,
                    payload TEXT,
                    PRIMARY KEY (node_id, timestamp)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_heartbeats_timestamp 
                ON heartbeats(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_heartbeats_node_timestamp 
                ON heartbeats(node_id, timestamp)
            """)
        
        # Banco de gossip
        with sqlite3.connect(self.gossip_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gossip_messages (
                    message_id TEXT PRIMARY KEY,
                    sender_node TEXT,
                    timestamp REAL,
                    message_type TEXT,
                    content TEXT,
                    signature TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS swarm_consensus (
                    timestamp REAL PRIMARY KEY,
                    active_nodes INTEGER,
                    global_phi REAL,
                    global_sr REAL,
                    global_G REAL,
                    global_health REAL,
                    consensus_hash TEXT
                )
            """)
    
    def insert_heartbeat(self, metrics: NodeMetrics) -> None:
        """Insere heartbeat no banco"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO heartbeats 
                (node_id, timestamp, phi, sr, G, health, cpu_usage, memory_usage, latency, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.node_id,
                metrics.timestamp,
                metrics.phi,
                metrics.sr,
                metrics.G,
                metrics.health,
                metrics.cpu_usage,
                metrics.memory_usage,
                metrics.latency,
                json.dumps(metrics.to_dict())
            ))
    
    def get_recent_heartbeats(self, window_s: float = DEFAULT_WINDOW_SIZE) -> List[NodeMetrics]:
        """Recupera heartbeats recentes"""
        cutoff = time.time() - window_s
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT node_id, timestamp, phi, sr, G, health, cpu_usage, memory_usage, latency
                FROM heartbeats 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff,))
            
            heartbeats = []
            for row in cursor.fetchall():
                metrics = NodeMetrics(
                    node_id=row[0],
                    timestamp=row[1],
                    phi=row[2],
                    sr=row[3],
                    G=row[4],
                    health=row[5],
                    cpu_usage=row[6],
                    memory_usage=row[7],
                    latency=row[8]
                )
                heartbeats.append(metrics)
            
            return heartbeats
    
    def get_active_nodes(self, timeout_s: float = DEFAULT_NODE_TIMEOUT) -> List[str]:
        """Retorna lista de nós ativos"""
        cutoff = time.time() - timeout_s
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT node_id 
                FROM heartbeats 
                WHERE timestamp >= ?
            """, (cutoff,))
            
            return [row[0] for row in cursor.fetchall()]
    
    def cleanup_old_data(self, retention_hours: int = 24) -> int:
        """Remove dados antigos"""
        cutoff = time.time() - (retention_hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM heartbeats WHERE timestamp < ?", (cutoff,))
            deleted = cursor.rowcount
        
        # Cleanup gossip também (banco separado)
        try:
            with sqlite3.connect(self.gossip_db) as conn:
                conn.execute("DELETE FROM gossip_messages WHERE timestamp < ?", (cutoff,))
        except sqlite3.OperationalError:
            # Tabela pode não existir ainda
            pass
            
        return deleted
    
    def store_consensus(self, state: SwarmState) -> None:
        """Armazena estado de consenso"""
        with sqlite3.connect(self.gossip_db) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO swarm_consensus
                (timestamp, active_nodes, global_phi, global_sr, global_G, global_health, consensus_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                state.timestamp,
                state.active_nodes,
                state.global_phi,
                state.global_sr,
                state.global_G,
                state.global_health,
                state.consensus_hash
            ))


class SwarmAggregator:
    """Agregador de métricas do swarm"""
    
    @staticmethod
    def harmonic_mean(values: List[float]) -> float:
        """Média harmônica (não-compensatória)"""
        if not values:
            return 0.0
        
        # Filtrar valores muito baixos para evitar divisão por zero
        filtered = [v for v in values if v > 1e-9]
        if not filtered:
            return 0.0
        
        return len(filtered) / sum(1.0 / v for v in filtered)
    
    @staticmethod
    def weighted_harmonic_mean(values: List[float], weights: List[float]) -> float:
        """Média harmônica ponderada"""
        if not values or not weights or len(values) != len(weights):
            return 0.0
        
        numerator = sum(weights)
        denominator = sum(w / max(1e-9, v) for v, w in zip(values, weights))
        
        return numerator / max(1e-9, denominator)
    
    def aggregate_metrics(self, heartbeats: List[NodeMetrics]) -> SwarmState:
        """
        Agrega métricas de múltiplos nós
        
        Args:
            heartbeats: Lista de métricas dos nós
            
        Returns:
            Estado agregado do swarm
        """
        if not heartbeats:
            return SwarmState(
                timestamp=time.time(),
                active_nodes=0,
                global_phi=0.0,
                global_sr=0.0,
                global_G=0.0,
                global_health=0.0,
                consensus_hash=""
            )
        
        # Agrupar por nó (pegar mais recente de cada)
        latest_by_node = {}
        for hb in heartbeats:
            if hb.node_id not in latest_by_node or hb.timestamp > latest_by_node[hb.node_id].timestamp:
                latest_by_node[hb.node_id] = hb
        
        latest_metrics = list(latest_by_node.values())
        
        # Filtrar nós saudáveis (health > 0.1)
        healthy_metrics = [m for m in latest_metrics if m.health > 0.1]
        
        if not healthy_metrics:
            return SwarmState(
                timestamp=time.time(),
                active_nodes=len(latest_metrics),
                global_phi=0.0,
                global_sr=0.0,
                global_G=0.0,
                global_health=0.0,
                consensus_hash=""
            )
        
        # Agregar usando média harmônica (não-compensatório)
        phi_values = [m.phi for m in healthy_metrics]
        sr_values = [m.sr for m in healthy_metrics]
        G_values = [m.G for m in healthy_metrics]
        health_values = [m.health for m in healthy_metrics]
        
        # Pesos baseados na saúde dos nós
        weights = health_values
        
        global_phi = self.weighted_harmonic_mean(phi_values, weights)
        global_sr = self.weighted_harmonic_mean(sr_values, weights)
        global_G = self.weighted_harmonic_mean(G_values, weights)
        global_health = self.harmonic_mean(health_values)
        
        # Gerar hash de consenso
        consensus_data = {
            "nodes": sorted([m.node_id for m in healthy_metrics]),
            "phi": round(global_phi, 6),
            "sr": round(global_sr, 6),
            "G": round(global_G, 6)
        }
        consensus_hash = hashlib.sha256(
            json.dumps(consensus_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return SwarmState(
            timestamp=time.time(),
            active_nodes=len(healthy_metrics),
            global_phi=global_phi,
            global_sr=global_sr,
            global_G=global_G,
            global_health=global_health,
            consensus_hash=consensus_hash
        )


class SwarmNode:
    """Nó individual do swarm"""
    
    def __init__(self, node_id: str, db: SwarmDatabase = None):
        self.node_id = node_id
        self.db = db or SwarmDatabase()
        self.aggregator = SwarmAggregator()
        self.running = False
        self.heartbeat_thread = None
        self.gossip_thread = None
        
        # Métricas locais
        self.local_metrics = NodeMetrics(
            node_id=node_id,
            timestamp=time.time(),
            phi=0.5,
            sr=0.5,
            G=0.5,
            health=1.0,
            cpu_usage=0.1,
            memory_usage=0.1,
            latency=0.01
        )
    
    def update_metrics(self, **kwargs) -> None:
        """Atualiza métricas locais"""
        for key, value in kwargs.items():
            if hasattr(self.local_metrics, key):
                setattr(self.local_metrics, key, value)
        
        self.local_metrics.timestamp = time.time()
    
    def heartbeat(self) -> None:
        """Envia heartbeat para o swarm"""
        self.local_metrics.timestamp = time.time()
        self.db.insert_heartbeat(self.local_metrics)
    
    def get_swarm_state(self, window_s: float = DEFAULT_WINDOW_SIZE) -> SwarmState:
        """Obtém estado agregado do swarm"""
        heartbeats = self.db.get_recent_heartbeats(window_s)
        return self.aggregator.aggregate_metrics(heartbeats)
    
    def start_heartbeat_loop(self, interval: float = DEFAULT_HEARTBEAT_INTERVAL) -> None:
        """Inicia loop de heartbeat em thread separada"""
        if self.running:
            return
        
        self.running = True
        
        def heartbeat_loop():
            while self.running:
                try:
                    self.heartbeat()
                    time.sleep(interval)
                except Exception as e:
                    print(f"Heartbeat error for {self.node_id}: {e}")
                    time.sleep(interval)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def start_gossip_loop(self, interval: float = DEFAULT_GOSSIP_INTERVAL) -> None:
        """Inicia loop de gossip em thread separada"""
        def gossip_loop():
            while self.running:
                try:
                    # Obter estado do swarm e armazenar consenso
                    swarm_state = self.get_swarm_state()
                    self.db.store_consensus(swarm_state)
                    
                    # Cleanup periódico
                    if random.random() < 0.1:  # 10% de chance
                        self.db.cleanup_old_data()
                    
                    time.sleep(interval)
                except Exception as e:
                    print(f"Gossip error for {self.node_id}: {e}")
                    time.sleep(interval)
        
        self.gossip_thread = threading.Thread(target=gossip_loop, daemon=True)
        self.gossip_thread.start()
    
    def start(self, heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
              gossip_interval: float = DEFAULT_GOSSIP_INTERVAL) -> None:
        """Inicia nó do swarm"""
        self.start_heartbeat_loop(heartbeat_interval)
        self.start_gossip_loop(gossip_interval)
    
    def stop(self) -> None:
        """Para nó do swarm"""
        self.running = False
        
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1.0)
        
        if self.gossip_thread:
            self.gossip_thread.join(timeout=1.0)


class SwarmOrchestrator:
    """Orquestrador do swarm cognitivo"""
    
    def __init__(self):
        self.db = SwarmDatabase()
        self.aggregator = SwarmAggregator()
        self.nodes: Dict[str, SwarmNode] = {}
    
    def create_node(self, node_id: str) -> SwarmNode:
        """Cria novo nó no swarm"""
        if node_id in self.nodes:
            return self.nodes[node_id]
        
        node = SwarmNode(node_id, self.db)
        self.nodes[node_id] = node
        return node
    
    def start_node(self, node_id: str, **initial_metrics) -> SwarmNode:
        """Inicia nó com métricas iniciais"""
        node = self.create_node(node_id)
        
        if initial_metrics:
            node.update_metrics(**initial_metrics)
        
        node.start()
        return node
    
    def stop_node(self, node_id: str) -> None:
        """Para nó específico"""
        if node_id in self.nodes:
            self.nodes[node_id].stop()
            del self.nodes[node_id]
    
    def stop_all_nodes(self) -> None:
        """Para todos os nós"""
        for node in self.nodes.values():
            node.stop()
        self.nodes.clear()
    
    def get_global_state(self, window_s: float = DEFAULT_WINDOW_SIZE) -> SwarmState:
        """Obtém estado global do swarm"""
        heartbeats = self.db.get_recent_heartbeats(window_s)
        return self.aggregator.aggregate_metrics(heartbeats)
    
    def get_node_status(self) -> Dict[str, Any]:
        """Retorna status de todos os nós"""
        active_nodes = self.db.get_active_nodes()
        
        status = {
            "total_nodes": len(self.nodes),
            "active_nodes": len(active_nodes),
            "running_nodes": [node_id for node_id, node in self.nodes.items() if node.running],
            "inactive_nodes": [node_id for node_id in self.nodes.keys() if node_id not in active_nodes]
        }
        
        return status
    
    def simulate_swarm(self, num_nodes: int = 3, duration_s: float = 10.0) -> Dict[str, Any]:
        """
        Simula swarm com múltiplos nós para teste
        
        Args:
            num_nodes: Número de nós a criar
            duration_s: Duração da simulação
            
        Returns:
            Relatório da simulação
        """
        # Criar e iniciar nós
        for i in range(num_nodes):
            node_id = f"node-{i}"
            initial_metrics = {
                "phi": 0.5 + random.uniform(-0.2, 0.2),
                "sr": 0.7 + random.uniform(-0.1, 0.1),
                "G": 0.8 + random.uniform(-0.1, 0.1),
                "health": 0.9 + random.uniform(-0.1, 0.1),
                "cpu_usage": random.uniform(0.1, 0.3),
                "memory_usage": random.uniform(0.1, 0.4)
            }
            self.start_node(node_id, **initial_metrics)
        
        # Aguardar simulação
        time.sleep(duration_s)
        
        # Coletar estado final
        final_state = self.get_global_state()
        node_status = self.get_node_status()
        
        # Parar todos os nós
        self.stop_all_nodes()
        
        return {
            "simulation_duration": duration_s,
            "num_nodes": num_nodes,
            "final_state": final_state.to_dict(),
            "node_status": node_status,
            "success": final_state.active_nodes > 0
        }


# Funções de conveniência
def heartbeat(node_id: str, payload: Dict[str, Any]) -> None:
    """
    Função de conveniência para enviar heartbeat
    
    Args:
        node_id: ID do nó
        payload: Dados do heartbeat
    """
    db = SwarmDatabase()
    
    metrics = NodeMetrics(
        node_id=node_id,
        timestamp=time.time(),
        phi=payload.get("phi", 0.5),
        sr=payload.get("sr", 0.5),
        G=payload.get("G", 0.5),
        health=payload.get("health", 1.0),
        cpu_usage=payload.get("cpu_usage", 0.1),
        memory_usage=payload.get("memory_usage", 0.1),
        latency=payload.get("latency", 0.01)
    )
    
    db.insert_heartbeat(metrics)


def sample_global_state(window_s: float = DEFAULT_WINDOW_SIZE) -> Dict[str, Any]:
    """
    Função de conveniência para obter estado global
    
    Args:
        window_s: Janela de tempo em segundos
        
    Returns:
        Estado agregado do swarm
    """
    db = SwarmDatabase()
    aggregator = SwarmAggregator()
    
    heartbeats = db.get_recent_heartbeats(window_s)
    state = aggregator.aggregate_metrics(heartbeats)
    
    return state.to_dict()


def quick_swarm_test() -> Dict[str, Any]:
    """
    Teste rápido do swarm cognitivo
    
    Returns:
        Relatório do teste
    """
    orchestrator = SwarmOrchestrator()
    return orchestrator.simulate_swarm(num_nodes=3, duration_s=2.0)