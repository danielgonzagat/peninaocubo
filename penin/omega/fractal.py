"""
DSL Fractal / Auto-similaridade
===============================

Implementa estrutura fractal auto-similar para propagação de parâmetros
críticos do núcleo para submódulos de forma não-compensatória.

Características:
- Árvore hierárquica de nós Omega
- Propagação automática de updates do núcleo
- Comportamento não-compensatório (falha em um nó afeta toda a subárvore)
- Configuração via YAML
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import os
import time
from pathlib import Path
import orjson


@dataclass
class OmegaNode:
    """
    Nó da estrutura fractal Omega
    
    Cada nó representa um submódulo com configuração própria
    que herda e propaga parâmetros do núcleo.
    """
    id: str
    depth: int
    config: Dict[str, Any]
    children: List["OmegaNode"] = field(default_factory=list)
    parent: Optional["OmegaNode"] = None
    last_update: float = field(default_factory=time.time)
    health: float = 1.0  # Saúde do nó [0,1]
    
    def add_child(self, child: "OmegaNode") -> None:
        """Adiciona filho e define parent"""
        child.parent = self
        self.children.append(child)
    
    def get_path(self) -> str:
        """Retorna caminho hierárquico do nó"""
        if self.parent is None:
            return self.id
        return f"{self.parent.get_path()}/{self.id}"
    
    def is_healthy(self, threshold: float = 0.5) -> bool:
        """Verifica se o nó está saudável"""
        return self.health >= threshold
    
    def propagate_health_up(self) -> None:
        """Propaga saúde para cima (bottleneck)"""
        if self.children:
            # Saúde é o mínimo dos filhos (não-compensatório)
            self.health = min(child.health for child in self.children)
        
        if self.parent:
            self.parent.propagate_health_up()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa nó para dict"""
        return {
            "id": self.id,
            "depth": self.depth,
            "config": self.config,
            "children": [child.to_dict() for child in self.children],
            "last_update": self.last_update,
            "health": self.health,
            "path": self.get_path()
        }


def build_fractal(root_cfg: Dict[str, Any], depth: int, branching: int, prefix: str = "Ω") -> OmegaNode:
    """
    Constrói árvore fractal com configuração auto-similar
    
    Args:
        root_cfg: Configuração do nó raiz
        depth: Profundidade máxima da árvore
        branching: Número de filhos por nó
        prefix: Prefixo para IDs dos nós
        
    Returns:
        Nó raiz da árvore fractal
    """
    root = OmegaNode(id=f"{prefix}-0", depth=0, config=root_cfg.copy())
    
    # Construir árvore nível por nível
    current_level = [root]
    
    for d in range(1, depth + 1):
        next_level = []
        
        for parent_node in current_level:
            for i in range(branching):
                child_id = f"{prefix}-{d}-{i}-{parent_node.id.split('-')[-1]}"
                
                # Configuração herdada com pequenas variações
                child_config = parent_node.config.copy()
                
                # Adicionar variação fractal (auto-similaridade)
                if "fractal_scale" not in child_config:
                    child_config["fractal_scale"] = 1.0
                
                child_config["fractal_scale"] *= 0.8  # Redução fractal
                child_config["depth"] = d
                child_config["parent_id"] = parent_node.id
                
                child = OmegaNode(
                    id=child_id,
                    depth=d,
                    config=child_config
                )
                
                parent_node.add_child(child)
                next_level.append(child)
        
        current_level = next_level
    
    return root


def propagate_update(root: OmegaNode, patch: Dict[str, Any], 
                    non_compensatory: bool = True) -> Dict[str, Any]:
    """
    Propaga atualização do núcleo para toda a árvore
    
    Args:
        root: Nó raiz da árvore
        patch: Dicionário com atualizações
        non_compensatory: Se True, falha em um nó bloqueia propagação
        
    Returns:
        Relatório da propagação
    """
    report = {
        "timestamp": time.time(),
        "patch": patch,
        "nodes_updated": 0,
        "nodes_failed": 0,
        "failed_nodes": [],
        "success": True
    }
    
    # Propagação em largura (BFS)
    queue = [root]
    
    while queue:
        node = queue.pop(0)
        
        try:
            # Aplicar patch
            old_config = node.config.copy()
            node.config.update(patch)
            node.last_update = time.time()
            
            # Verificar se update foi bem-sucedido
            if _validate_node_config(node.config):
                report["nodes_updated"] += 1
                
                # Adicionar filhos à fila
                queue.extend(node.children)
            else:
                # Falha na validação
                node.config = old_config  # Rollback
                node.health = 0.1  # Marcar como não saudável
                report["nodes_failed"] += 1
                report["failed_nodes"].append(node.get_path())
                
                if non_compensatory:
                    # Parar propagação em caso de falha
                    report["success"] = False
                    break
                    
        except Exception as e:
            # Erro durante update
            report["nodes_failed"] += 1
            report["failed_nodes"].append(f"{node.get_path()}: {str(e)}")
            node.health = 0.1
            
            if non_compensatory:
                report["success"] = False
                break
    
    # Propagar saúde para cima
    root.propagate_health_up()
    
    return report


def _validate_node_config(config: Dict[str, Any]) -> bool:
    """
    Valida configuração do nó
    
    Args:
        config: Configuração a validar
        
    Returns:
        True se válida, False caso contrário
    """
    # Validações básicas
    required_keys = ["fractal_scale", "depth"]
    
    for key in required_keys:
        if key not in config:
            return False
    
    # Validar tipos e ranges
    if not isinstance(config["fractal_scale"], (int, float)):
        return False
    
    if config["fractal_scale"] <= 0 or config["fractal_scale"] > 2.0:
        return False
    
    if not isinstance(config["depth"], int) or config["depth"] < 0:
        return False
    
    return True


class FractalManager:
    """
    Gerenciador da estrutura fractal
    
    Coordena criação, atualização e monitoramento da árvore fractal.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: Caminho para arquivo de configuração YAML
        """
        self.config_path = config_path or "penin/omega/fractal_dsl.yaml"
        self.root: Optional[OmegaNode] = None
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração do DSL"""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except ImportError:
            # Fallback sem yaml
            return {
                "version": 1,
                "depth": 2,
                "branching": 3,
                "weights": {"caos": 1.0, "sr": 1.0, "g": 1.0},
                "sync": {"propagate_core_updates": True, "non_compensatory": True}
            }
        except Exception:
            # Configuração padrão
            return {
                "version": 1,
                "depth": 2,
                "branching": 3,
                "weights": {"caos": 1.0, "sr": 1.0, "g": 1.0},
                "sync": {"propagate_core_updates": True, "non_compensatory": True}
            }
    
    def initialize_fractal(self, root_config: Dict[str, Any]) -> OmegaNode:
        """
        Inicializa estrutura fractal
        
        Args:
            root_config: Configuração do nó raiz
            
        Returns:
            Nó raiz da árvore
        """
        self.root = build_fractal(
            root_cfg=root_config,
            depth=self.config["depth"],
            branching=self.config["branching"],
            prefix="Ω"
        )
        
        return self.root
    
    def update_core_parameters(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza parâmetros do núcleo e propaga para toda a árvore
        
        Args:
            updates: Dicionário com atualizações
            
        Returns:
            Relatório da propagação
        """
        if self.root is None:
            raise ValueError("Fractal not initialized. Call initialize_fractal() first.")
        
        non_compensatory = self.config["sync"]["non_compensatory"]
        
        return propagate_update(self.root, updates, non_compensatory)
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Gera relatório de saúde da árvore fractal
        
        Returns:
            Relatório com métricas de saúde
        """
        if self.root is None:
            return {"error": "Fractal not initialized"}
        
        report = {
            "timestamp": time.time(),
            "root_health": self.root.health,
            "total_nodes": 0,
            "healthy_nodes": 0,
            "unhealthy_nodes": [],
            "depth_health": {}
        }
        
        # Percorrer árvore e coletar métricas
        queue = [self.root]
        
        while queue:
            node = queue.pop(0)
            report["total_nodes"] += 1
            
            if node.is_healthy():
                report["healthy_nodes"] += 1
            else:
                report["unhealthy_nodes"].append({
                    "path": node.get_path(),
                    "health": node.health,
                    "depth": node.depth
                })
            
            # Saúde por profundidade
            depth_key = f"depth_{node.depth}"
            if depth_key not in report["depth_health"]:
                report["depth_health"][depth_key] = {"total": 0, "healthy": 0}
            
            report["depth_health"][depth_key]["total"] += 1
            if node.is_healthy():
                report["depth_health"][depth_key]["healthy"] += 1
            
            queue.extend(node.children)
        
        # Calcular percentuais
        if report["total_nodes"] > 0:
            report["health_percentage"] = report["healthy_nodes"] / report["total_nodes"]
        else:
            report["health_percentage"] = 0.0
        
        return report
    
    def save_state(self, filepath: str) -> None:
        """
        Salva estado da árvore fractal
        
        Args:
            filepath: Caminho para salvar o estado
        """
        if self.root is None:
            raise ValueError("Fractal not initialized")
        
        state = {
            "config": self.config,
            "tree": self.root.to_dict(),
            "timestamp": time.time()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(orjson.dumps(state, option=orjson.OPT_INDENT_2))
    
    def load_state(self, filepath: str) -> None:
        """
        Carrega estado da árvore fractal
        
        Args:
            filepath: Caminho do arquivo de estado
        """
        with open(filepath, 'rb') as f:
            state = orjson.loads(f.read())
        
        self.config = state["config"]
        # TODO: Reconstruir árvore a partir do dict
        # Por simplicidade, apenas recriar com config
        if "tree" in state and "config" in state["tree"]:
            self.root = self._dict_to_node(state["tree"])
    
    def _dict_to_node(self, node_dict: Dict[str, Any]) -> OmegaNode:
        """
        Reconstrói nó a partir de dict
        
        Args:
            node_dict: Dicionário com dados do nó
            
        Returns:
            Nó reconstruído
        """
        node = OmegaNode(
            id=node_dict["id"],
            depth=node_dict["depth"],
            config=node_dict["config"],
            last_update=node_dict.get("last_update", time.time()),
            health=node_dict.get("health", 1.0)
        )
        
        # Reconstruir filhos recursivamente
        for child_dict in node_dict.get("children", []):
            child = self._dict_to_node(child_dict)
            node.add_child(child)
        
        return node


# Funções de conveniência
def quick_fractal_test(depth: int = 2, branching: int = 3) -> Dict[str, Any]:
    """
    Teste rápido da estrutura fractal
    
    Args:
        depth: Profundidade da árvore
        branching: Número de filhos por nó
        
    Returns:
        Relatório do teste
    """
    # Configuração inicial
    root_config = {
        "temperature": 0.7,
        "learning_rate": 0.01,
        "fractal_scale": 1.0,
        "depth": 0
    }
    
    # Criar árvore
    root = build_fractal(root_config, depth, branching)
    
    # Testar propagação
    update_patch = {
        "temperature": 0.8,
        "new_param": "fractal_test"
    }
    
    report = propagate_update(root, update_patch)
    
    # Adicionar métricas da árvore
    report["tree_stats"] = {
        "root_id": root.id,
        "root_health": root.health,
        "total_children": len(root.children),
        "max_depth": depth
    }
    
    return report


def validate_fractal_propagation() -> Dict[str, Any]:
    """
    Valida comportamento não-compensatório da propagação
    
    Returns:
        Relatório de validação
    """
    results = {}
    
    # Teste 1: Propagação bem-sucedida
    root_config = {"param1": 1.0, "fractal_scale": 1.0, "depth": 0}
    root = build_fractal(root_config, depth=2, branching=2)
    
    good_patch = {"param1": 2.0, "param2": "test"}
    report1 = propagate_update(root, good_patch, non_compensatory=True)
    
    results["successful_propagation"] = {
        "success": report1["success"],
        "nodes_updated": report1["nodes_updated"],
        "nodes_failed": report1["nodes_failed"]
    }
    
    # Teste 2: Propagação com falha (simulada)
    root2 = build_fractal(root_config, depth=2, branching=2)
    
    # Patch que causará falha na validação
    bad_patch = {"fractal_scale": -1.0}  # Valor inválido
    report2 = propagate_update(root2, bad_patch, non_compensatory=True)
    
    results["failed_propagation"] = {
        "success": report2["success"],
        "nodes_updated": report2["nodes_updated"],
        "nodes_failed": report2["nodes_failed"],
        "failed_nodes": report2["failed_nodes"]
    }
    
    # Teste 3: Comportamento não-compensatório
    results["non_compensatory_working"] = (
        results["successful_propagation"]["success"] and
        not results["failed_propagation"]["success"]
    )
    
    return results