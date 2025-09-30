"""
Testes para DSL Fractal / Auto-similaridade
===========================================

Testa estrutura fractal, propagação de parâmetros e comportamento não-compensatório.
"""

import pytest
import tempfile
import os
from pathlib import Path

from penin.omega.fractal import (
    OmegaNode,
    build_fractal,
    propagate_update,
    FractalManager,
    quick_fractal_test,
    validate_fractal_propagation
)


class TestOmegaNode:
    """Testes da classe OmegaNode"""
    
    def test_node_creation(self):
        """Testa criação de nó"""
        config = {"param1": 1.0, "param2": "test"}
        node = OmegaNode(id="test-node", depth=0, config=config)
        
        assert node.id == "test-node"
        assert node.depth == 0
        assert node.config == config
        assert len(node.children) == 0
        assert node.parent is None
        assert node.health == 1.0
    
    def test_add_child(self):
        """Testa adição de filho"""
        parent = OmegaNode(id="parent", depth=0, config={})
        child = OmegaNode(id="child", depth=1, config={})
        
        parent.add_child(child)
        
        assert len(parent.children) == 1
        assert parent.children[0] == child
        assert child.parent == parent
    
    def test_get_path(self):
        """Testa geração de caminho hierárquico"""
        root = OmegaNode(id="root", depth=0, config={})
        child1 = OmegaNode(id="child1", depth=1, config={})
        child2 = OmegaNode(id="child2", depth=2, config={})
        
        root.add_child(child1)
        child1.add_child(child2)
        
        assert root.get_path() == "root"
        assert child1.get_path() == "root/child1"
        assert child2.get_path() == "root/child1/child2"
    
    def test_health_propagation(self):
        """Testa propagação de saúde (não-compensatório)"""
        root = OmegaNode(id="root", depth=0, config={})
        child1 = OmegaNode(id="child1", depth=1, config={})
        child2 = OmegaNode(id="child2", depth=1, config={})
        
        root.add_child(child1)
        root.add_child(child2)
        
        # Inicialmente todos saudáveis
        assert root.health == 1.0
        assert child1.health == 1.0
        assert child2.health == 1.0
        
        # Marcar um filho como não saudável
        child1.health = 0.3
        
        # Propagar saúde para cima
        root.propagate_health_up()
        
        # Root deve ter saúde mínima dos filhos (não-compensatório)
        assert root.health == 0.3
    
    def test_to_dict(self):
        """Testa serialização para dict"""
        config = {"param1": 1.0}
        node = OmegaNode(id="test", depth=0, config=config)
        child = OmegaNode(id="child", depth=1, config={})
        node.add_child(child)
        
        node_dict = node.to_dict()
        
        assert node_dict["id"] == "test"
        assert node_dict["depth"] == 0
        assert node_dict["config"] == config
        assert len(node_dict["children"]) == 1
        assert node_dict["children"][0]["id"] == "child"
        assert "path" in node_dict
        assert "health" in node_dict


class TestBuildFractal:
    """Testes da função build_fractal"""
    
    def test_build_simple_fractal(self):
        """Testa construção de fractal simples"""
        root_config = {"param1": 1.0, "fractal_scale": 1.0}
        
        root = build_fractal(root_config, depth=2, branching=2)
        
        assert root.id == "Ω-0"
        assert root.depth == 0
        assert len(root.children) == 2
        
        # Verificar primeiro nível
        for i, child in enumerate(root.children):
            assert child.depth == 1
            assert child.parent == root
            assert "fractal_scale" in child.config
            assert child.config["fractal_scale"] == 0.8  # Redução fractal
        
        # Verificar segundo nível
        for child in root.children:
            assert len(child.children) == 2
            for grandchild in child.children:
                assert grandchild.depth == 2
                assert grandchild.parent == child
                assert abs(grandchild.config["fractal_scale"] - 0.64) < 1e-10  # 0.8 * 0.8
    
    def test_build_fractal_depth_zero(self):
        """Testa construção com profundidade zero"""
        root_config = {"param1": 1.0}
        
        root = build_fractal(root_config, depth=0, branching=3)
        
        assert root.depth == 0
        assert len(root.children) == 0
    
    def test_build_fractal_custom_prefix(self):
        """Testa construção com prefixo customizado"""
        root_config = {"param1": 1.0}
        
        root = build_fractal(root_config, depth=1, branching=2, prefix="TEST")
        
        assert root.id == "TEST-0"
        assert root.children[0].id.startswith("TEST-1")


class TestPropagateUpdate:
    """Testes da função propagate_update"""
    
    def test_successful_propagation(self):
        """Testa propagação bem-sucedida"""
        root_config = {"param1": 1.0, "fractal_scale": 1.0, "depth": 0}
        root = build_fractal(root_config, depth=2, branching=2)
        
        patch = {"param1": 2.0, "new_param": "test"}
        
        report = propagate_update(root, patch, non_compensatory=True)
        
        assert report["success"] is True
        assert report["nodes_updated"] > 0
        assert report["nodes_failed"] == 0
        assert len(report["failed_nodes"]) == 0
        
        # Verificar se patch foi aplicado
        assert root.config["param1"] == 2.0
        assert root.config["new_param"] == "test"
        
        # Verificar propagação para filhos
        for child in root.children:
            assert child.config["param1"] == 2.0
            assert child.config["new_param"] == "test"
    
    def test_failed_propagation_non_compensatory(self):
        """Testa propagação com falha em modo não-compensatório"""
        root_config = {"param1": 1.0, "fractal_scale": 1.0, "depth": 0}
        root = build_fractal(root_config, depth=2, branching=2)
        
        # Patch que causará falha na validação
        patch = {"fractal_scale": -1.0}  # Valor inválido
        
        report = propagate_update(root, patch, non_compensatory=True)
        
        assert report["success"] is False
        assert report["nodes_failed"] > 0
        assert len(report["failed_nodes"]) > 0
    
    def test_propagation_compensatory_mode(self):
        """Testa propagação em modo compensatório (continua mesmo com falhas)"""
        root_config = {"param1": 1.0, "fractal_scale": 1.0, "depth": 0}
        root = build_fractal(root_config, depth=1, branching=2)
        
        # Patch que causará falha na validação
        patch = {"fractal_scale": -1.0}
        
        report = propagate_update(root, patch, non_compensatory=False)
        
        # Em modo compensatório, pode continuar mesmo com falhas
        # (depende da implementação específica)
        assert "success" in report
        assert "nodes_failed" in report


class TestFractalManager:
    """Testes da classe FractalManager"""
    
    def test_manager_initialization(self):
        """Testa inicialização do gerenciador"""
        manager = FractalManager()
        
        assert manager.config is not None
        assert "depth" in manager.config
        assert "branching" in manager.config
        assert manager.root is None
    
    def test_initialize_fractal(self):
        """Testa inicialização da estrutura fractal"""
        manager = FractalManager()
        root_config = {"param1": 1.0, "fractal_scale": 1.0}
        
        root = manager.initialize_fractal(root_config)
        
        assert manager.root is not None
        assert manager.root == root
        assert root.depth == 0
        assert len(root.children) > 0
    
    def test_update_core_parameters(self):
        """Testa atualização de parâmetros do núcleo"""
        manager = FractalManager()
        root_config = {"param1": 1.0, "fractal_scale": 1.0, "depth": 0}
        
        manager.initialize_fractal(root_config)
        
        updates = {"param1": 2.0, "new_param": "updated"}
        report = manager.update_core_parameters(updates)
        
        assert "success" in report
        assert "nodes_updated" in report
        assert manager.root.config["param1"] == 2.0
        assert manager.root.config["new_param"] == "updated"
    
    def test_get_health_report(self):
        """Testa geração de relatório de saúde"""
        manager = FractalManager()
        root_config = {"param1": 1.0, "fractal_scale": 1.0, "depth": 0}
        
        manager.initialize_fractal(root_config)
        
        report = manager.get_health_report()
        
        assert "root_health" in report
        assert "total_nodes" in report
        assert "healthy_nodes" in report
        assert "health_percentage" in report
        assert "depth_health" in report
        
        # Inicialmente todos devem estar saudáveis
        assert report["root_health"] == 1.0
        assert report["health_percentage"] == 1.0
    
    def test_save_and_load_state(self):
        """Testa salvamento e carregamento de estado"""
        manager = FractalManager()
        root_config = {"param1": 1.0, "fractal_scale": 1.0, "depth": 0}
        
        manager.initialize_fractal(root_config)
        
        # Salvar estado
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            manager.save_state(temp_path)
            
            # Verificar que arquivo foi criado
            assert os.path.exists(temp_path)
            
            # Carregar estado em novo manager
            manager2 = FractalManager()
            manager2.load_state(temp_path)
            
            # Verificar que estado foi carregado
            assert manager2.root is not None
            assert manager2.root.id == manager.root.id
            
        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestQuickFunctions:
    """Testes das funções de conveniência"""
    
    def test_quick_fractal_test(self):
        """Testa função de teste rápido"""
        report = quick_fractal_test(depth=2, branching=2)
        
        assert "success" in report
        assert "nodes_updated" in report
        assert "tree_stats" in report
        
        tree_stats = report["tree_stats"]
        assert "root_id" in tree_stats
        assert "root_health" in tree_stats
        assert "total_children" in tree_stats
        assert "max_depth" in tree_stats
    
    def test_validate_fractal_propagation(self):
        """Testa validação de propagação fractal"""
        results = validate_fractal_propagation()
        
        assert "successful_propagation" in results
        assert "failed_propagation" in results
        assert "non_compensatory_working" in results
        
        # Verificar que comportamento não-compensatório funciona
        assert results["successful_propagation"]["success"] is True
        assert results["failed_propagation"]["success"] is False
        assert results["non_compensatory_working"] is True


if __name__ == "__main__":
    pytest.main([__file__])