"""
Testes para Swarm Cognitivo
===========================

Testa sistema de swarm com gossip local, agregação de métricas e consenso.
"""

import pytest
import tempfile
import os
import time
import sqlite3
from pathlib import Path

from penin.omega.swarm import (
    NodeMetrics,
    SwarmState,
    SwarmDatabase,
    SwarmAggregator,
    SwarmNode,
    SwarmOrchestrator,
    heartbeat,
    sample_global_state,
    quick_swarm_test
)


class TestNodeMetrics:
    """Testes da classe NodeMetrics"""
    
    def test_node_metrics_creation(self):
        """Testa criação de métricas de nó"""
        metrics = NodeMetrics(
            node_id="test-node",
            timestamp=time.time(),
            phi=0.7,
            sr=0.8,
            G=0.9,
            health=1.0,
            cpu_usage=0.2,
            memory_usage=0.3,
            latency=0.01
        )
        
        assert metrics.node_id == "test-node"
        assert metrics.phi == 0.7
        assert metrics.sr == 0.8
        assert metrics.G == 0.9
        assert metrics.health == 1.0
    
    def test_metrics_serialization(self):
        """Testa serialização/deserialização"""
        metrics = NodeMetrics(
            node_id="test",
            timestamp=123456.0,
            phi=0.5,
            sr=0.6,
            G=0.7,
            health=0.8,
            cpu_usage=0.1,
            memory_usage=0.2,
            latency=0.05
        )
        
        # Serializar
        data = metrics.to_dict()
        assert isinstance(data, dict)
        assert data["node_id"] == "test"
        assert data["phi"] == 0.5
        
        # Deserializar
        restored = NodeMetrics.from_dict(data)
        assert restored.node_id == metrics.node_id
        assert restored.phi == metrics.phi
        assert restored.sr == metrics.sr


class TestSwarmDatabase:
    """Testes da classe SwarmDatabase"""
    
    def test_database_initialization(self):
        """Testa inicialização do banco"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = SwarmDatabase(db_path)
            
            # Verificar que arquivo foi criado
            assert os.path.exists(db_path)
            
            # Verificar estrutura das tabelas
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                assert "heartbeats" in tables
    
    def test_insert_and_retrieve_heartbeat(self):
        """Testa inserção e recuperação de heartbeat"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = SwarmDatabase(db_path)
            
            # Inserir heartbeat
            metrics = NodeMetrics(
                node_id="test-node",
                timestamp=time.time(),
                phi=0.7,
                sr=0.8,
                G=0.9,
                health=1.0,
                cpu_usage=0.2,
                memory_usage=0.3,
                latency=0.01
            )
            
            db.insert_heartbeat(metrics)
            
            # Recuperar heartbeats
            heartbeats = db.get_recent_heartbeats(window_s=60.0)
            
            assert len(heartbeats) == 1
            assert heartbeats[0].node_id == "test-node"
            assert heartbeats[0].phi == 0.7
    
    def test_get_active_nodes(self):
        """Testa recuperação de nós ativos"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = SwarmDatabase(db_path)
            
            # Inserir heartbeats de múltiplos nós
            current_time = time.time()
            
            for i in range(3):
                metrics = NodeMetrics(
                    node_id=f"node-{i}",
                    timestamp=current_time - i,  # Nós com timestamps diferentes
                    phi=0.5,
                    sr=0.6,
                    G=0.7,
                    health=1.0,
                    cpu_usage=0.1,
                    memory_usage=0.1,
                    latency=0.01
                )
                db.insert_heartbeat(metrics)
            
            # Recuperar nós ativos (timeout generoso)
            active_nodes = db.get_active_nodes(timeout_s=60.0)
            
            assert len(active_nodes) == 3
            assert "node-0" in active_nodes
            assert "node-1" in active_nodes
            assert "node-2" in active_nodes
    
    def test_cleanup_old_data(self):
        """Testa limpeza de dados antigos"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = SwarmDatabase(db_path)
            
            # Inserir dados antigos e recentes
            old_time = time.time() - 48 * 3600  # 48 horas atrás
            recent_time = time.time()
            
            # Dado antigo
            old_metrics = NodeMetrics(
                node_id="old-node",
                timestamp=old_time,
                phi=0.5, sr=0.5, G=0.5, health=1.0,
                cpu_usage=0.1, memory_usage=0.1, latency=0.01
            )
            db.insert_heartbeat(old_metrics)
            
            # Dado recente
            recent_metrics = NodeMetrics(
                node_id="recent-node",
                timestamp=recent_time,
                phi=0.5, sr=0.5, G=0.5, health=1.0,
                cpu_usage=0.1, memory_usage=0.1, latency=0.01
            )
            db.insert_heartbeat(recent_metrics)
            
            # Verificar que ambos estão lá
            all_heartbeats = db.get_recent_heartbeats(window_s=72 * 3600)  # 72 horas
            assert len(all_heartbeats) == 2
            
            # Fazer cleanup (reter apenas 24 horas)
            deleted = db.cleanup_old_data(retention_hours=24)
            assert deleted == 1
            
            # Verificar que apenas o recente permanece
            remaining = db.get_recent_heartbeats(window_s=72 * 3600)
            assert len(remaining) == 1
            assert remaining[0].node_id == "recent-node"


class TestSwarmAggregator:
    """Testes da classe SwarmAggregator"""
    
    def test_harmonic_mean(self):
        """Testa média harmônica"""
        aggregator = SwarmAggregator()
        
        # Caso normal
        values = [0.5, 0.6, 0.7]
        result = aggregator.harmonic_mean(values)
        expected = 3 / (1/0.5 + 1/0.6 + 1/0.7)
        assert abs(result - expected) < 1e-10
        
        # Lista vazia
        assert aggregator.harmonic_mean([]) == 0.0
        
        # Valores com zeros (devem ser filtrados)
        values_with_zero = [0.5, 0.0, 0.6]
        result = aggregator.harmonic_mean(values_with_zero)
        expected = 2 / (1/0.5 + 1/0.6)
        assert abs(result - expected) < 1e-10
    
    def test_weighted_harmonic_mean(self):
        """Testa média harmônica ponderada"""
        aggregator = SwarmAggregator()
        
        values = [0.5, 0.6]
        weights = [1.0, 2.0]
        
        result = aggregator.weighted_harmonic_mean(values, weights)
        expected = (1.0 + 2.0) / (1.0/0.5 + 2.0/0.6)
        assert abs(result - expected) < 1e-10
        
        # Listas de tamanhos diferentes
        assert aggregator.weighted_harmonic_mean([0.5], [1.0, 2.0]) == 0.0
    
    def test_aggregate_metrics(self):
        """Testa agregação de métricas"""
        aggregator = SwarmAggregator()
        
        # Criar heartbeats de múltiplos nós
        heartbeats = []
        for i in range(3):
            metrics = NodeMetrics(
                node_id=f"node-{i}",
                timestamp=time.time(),
                phi=0.5 + i * 0.1,
                sr=0.6 + i * 0.1,
                G=0.7 + i * 0.1,
                health=0.9,
                cpu_usage=0.1,
                memory_usage=0.1,
                latency=0.01
            )
            heartbeats.append(metrics)
        
        # Agregar
        state = aggregator.aggregate_metrics(heartbeats)
        
        assert isinstance(state, SwarmState)
        assert state.active_nodes == 3
        assert state.global_phi > 0.0
        assert state.global_sr > 0.0
        assert state.global_G > 0.0
        assert state.global_health > 0.0
        assert len(state.consensus_hash) > 0
    
    def test_aggregate_empty_metrics(self):
        """Testa agregação com lista vazia"""
        aggregator = SwarmAggregator()
        
        state = aggregator.aggregate_metrics([])
        
        assert state.active_nodes == 0
        assert state.global_phi == 0.0
        assert state.global_sr == 0.0
        assert state.global_G == 0.0
        assert state.global_health == 0.0
    
    def test_aggregate_unhealthy_nodes(self):
        """Testa agregação com nós não saudáveis"""
        aggregator = SwarmAggregator()
        
        # Criar nós com saúde baixa
        heartbeats = []
        for i in range(3):
            metrics = NodeMetrics(
                node_id=f"node-{i}",
                timestamp=time.time(),
                phi=0.5,
                sr=0.6,
                G=0.7,
                health=0.05,  # Saúde muito baixa (< 0.1)
                cpu_usage=0.1,
                memory_usage=0.1,
                latency=0.01
            )
            heartbeats.append(metrics)
        
        # Agregar
        state = aggregator.aggregate_metrics(heartbeats)
        
        # Nós não saudáveis devem ser filtrados
        assert state.active_nodes == 3  # Contados, mas não usados na agregação
        assert state.global_phi == 0.0  # Sem nós saudáveis
        assert state.global_sr == 0.0
        assert state.global_G == 0.0
        assert state.global_health == 0.0


class TestSwarmNode:
    """Testes da classe SwarmNode"""
    
    def test_node_creation(self):
        """Testa criação de nó"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = SwarmDatabase(db_path)
            
            node = SwarmNode("test-node", db)
            
            assert node.node_id == "test-node"
            assert node.db == db
            assert not node.running
            assert node.local_metrics.node_id == "test-node"
    
    def test_update_metrics(self):
        """Testa atualização de métricas"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = SwarmDatabase(db_path)
            
            node = SwarmNode("test-node", db)
            
            # Atualizar métricas
            node.update_metrics(phi=0.8, sr=0.9, health=0.95)
            
            assert node.local_metrics.phi == 0.8
            assert node.local_metrics.sr == 0.9
            assert node.local_metrics.health == 0.95
    
    def test_heartbeat(self):
        """Testa envio de heartbeat"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = SwarmDatabase(db_path)
            
            node = SwarmNode("test-node", db)
            node.update_metrics(phi=0.7)
            
            # Enviar heartbeat
            node.heartbeat()
            
            # Verificar que foi armazenado
            heartbeats = db.get_recent_heartbeats()
            assert len(heartbeats) == 1
            assert heartbeats[0].node_id == "test-node"
            assert heartbeats[0].phi == 0.7
    
    def test_get_swarm_state(self):
        """Testa obtenção de estado do swarm"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = SwarmDatabase(db_path)
            
            node = SwarmNode("test-node", db)
            
            # Adicionar alguns heartbeats
            node.heartbeat()
            
            # Obter estado
            state = node.get_swarm_state()
            
            assert isinstance(state, SwarmState)
            assert state.active_nodes >= 0


class TestSwarmOrchestrator:
    """Testes da classe SwarmOrchestrator"""
    
    def test_orchestrator_creation(self):
        """Testa criação do orquestrador"""
        orchestrator = SwarmOrchestrator()
        
        assert isinstance(orchestrator.db, SwarmDatabase)
        assert isinstance(orchestrator.aggregator, SwarmAggregator)
        assert len(orchestrator.nodes) == 0
    
    def test_create_node(self):
        """Testa criação de nó"""
        orchestrator = SwarmOrchestrator()
        
        node = orchestrator.create_node("test-node")
        
        assert node.node_id == "test-node"
        assert "test-node" in orchestrator.nodes
        
        # Criar mesmo nó novamente deve retornar o existente
        node2 = orchestrator.create_node("test-node")
        assert node2 == node
    
    def test_start_and_stop_node(self):
        """Testa iniciar e parar nó"""
        orchestrator = SwarmOrchestrator()
        
        # Iniciar nó
        node = orchestrator.start_node("test-node", phi=0.8, sr=0.9)
        
        assert node.running
        assert node.local_metrics.phi == 0.8
        assert node.local_metrics.sr == 0.9
        
        # Parar nó
        orchestrator.stop_node("test-node")
        
        assert "test-node" not in orchestrator.nodes
    
    def test_get_node_status(self):
        """Testa obtenção de status dos nós"""
        orchestrator = SwarmOrchestrator()
        
        # Criar alguns nós
        orchestrator.create_node("node-1")
        orchestrator.create_node("node-2")
        
        status = orchestrator.get_node_status()
        
        assert status["total_nodes"] == 2
        assert "running_nodes" in status
        assert "inactive_nodes" in status
    
    def test_simulate_swarm(self):
        """Testa simulação de swarm"""
        orchestrator = SwarmOrchestrator()
        
        # Simular swarm pequeno e rápido
        report = orchestrator.simulate_swarm(num_nodes=2, duration_s=0.5)
        
        assert "simulation_duration" in report
        assert "num_nodes" in report
        assert "final_state" in report
        assert "node_status" in report
        assert "success" in report
        
        assert report["num_nodes"] == 2
        assert report["simulation_duration"] == 0.5


class TestConvenienceFunctions:
    """Testes das funções de conveniência"""
    
    def test_heartbeat_function(self):
        """Testa função heartbeat"""
        # Usar banco temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configurar caminho temporário
            import penin.omega.swarm as swarm_module
            original_db_path = swarm_module.DB_PATH
            swarm_module.DB_PATH = Path(temp_dir) / "test.db"
            
            try:
                # Enviar heartbeat
                payload = {"phi": 0.7, "sr": 0.8, "G": 0.9}
                heartbeat("test-node", payload)
                
                # Verificar que foi armazenado
                db = SwarmDatabase(str(swarm_module.DB_PATH))
                heartbeats = db.get_recent_heartbeats()
                
                assert len(heartbeats) >= 1
                # Encontrar o heartbeat do test-node
                test_heartbeat = next((hb for hb in heartbeats if hb.node_id == "test-node"), None)
                assert test_heartbeat is not None
                assert test_heartbeat.phi == 0.7
                
            finally:
                # Restaurar caminho original
                swarm_module.DB_PATH = original_db_path
    
    def test_sample_global_state_function(self):
        """Testa função sample_global_state"""
        # Usar banco temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            import penin.omega.swarm as swarm_module
            original_db_path = swarm_module.DB_PATH
            swarm_module.DB_PATH = Path(temp_dir) / "test.db"
            
            try:
                # Adicionar alguns heartbeats
                heartbeat("node-1", {"phi": 0.6, "sr": 0.7, "G": 0.8})
                heartbeat("node-2", {"phi": 0.7, "sr": 0.8, "G": 0.9})
                
                # Obter estado global
                state = sample_global_state()
                
                assert isinstance(state, dict)
                assert "active_nodes" in state
                assert "global_phi" in state
                assert "global_sr" in state
                assert "global_G" in state
                
            finally:
                swarm_module.DB_PATH = original_db_path
    
    def test_quick_swarm_test(self):
        """Testa função quick_swarm_test"""
        report = quick_swarm_test()
        
        assert isinstance(report, dict)
        assert "simulation_duration" in report
        assert "num_nodes" in report
        assert "final_state" in report
        assert "success" in report


if __name__ == "__main__":
    pytest.main([__file__])