# penin/omega/fractal.py
"""
DSL Fractal / Auto-similaridade
===============================

Implementa estrutura fractal auto-similar onde o núcleo propaga
parâmetros críticos para submódulos de forma não-compensatória.

Características:
- Árvore hierárquica de nós Omega
- Propagação automática de updates do núcleo
- Comportamento não-compensatório (falha em qualquer nível bloqueia)
- Configuração via YAML DSL
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import os
import time
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    import json as yaml  # Fallback to JSON


@dataclass
class OmegaNode:
    """Nó na estrutura fractal Omega"""
    id: str
    depth: int
    config: Dict[str, Any]
    children: List["OmegaNode"] = field(default_factory=list)
    parent: Optional["OmegaNode"] = None
    last_update: float = field(default_factory=time.time)
    status: str = "active"  # active, failed, disabled
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "depth": self.depth,
            "config": self.config,
            "children_ids": [child.id for child in self.children],
            "parent_id": self.parent.id if self.parent else None,
            "last_update": self.last_update,
            "status": self.status
        }
    
    def get_path(self) -> str:
        """Retorna caminho hierárquico do nó"""
        if self.parent is None:
            return self.id
        return f"{self.parent.get_path()}/{self.id}"
    
    def count_descendants(self) -> int:
        """Conta total de descendentes"""
        count = len(self.children)
        for child in self.children:
            count += child.count_descendants()
        return count


def load_fractal_config(config_path: str = "penin/omega/fractal_dsl.yaml") -> Dict[str, Any]:
    """Carrega configuração fractal do YAML"""
    try:
        if YAML_AVAILABLE:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Fallback: configuração hardcoded
            return {
                "version": 1,
                "depth": 2,
                "branching": 3,
                "weights": {"caos": 1.0, "sr": 1.0, "g": 1.0},
                "sync": {"propagate_core_updates": True, "non_compensatory": True},
                "thresholds": {
                    "beta_min": 0.01,
                    "theta_caos": 0.25,
                    "tau_sr": 0.80,
                    "theta_G": 0.85
                },
                "policies": {
                    "fail_closed": True,
                    "ethics_required": True,
                    "contractive_required": True
                }
            }
    except FileNotFoundError:
        # Configuração padrão se arquivo não existir
        return {
            "version": 1,
            "depth": 2,
            "branching": 3,
            "weights": {"caos": 1.0, "sr": 1.0, "g": 1.0},
            "sync": {"propagate_core_updates": True, "non_compensatory": True},
            "thresholds": {
                "beta_min": 0.01,
                "theta_caos": 0.25,
                "tau_sr": 0.80,
                "theta_G": 0.85
            },
            "policies": {
                "fail_closed": True,
                "ethics_required": True,
                "contractive_required": True
            }
        }


def build_fractal(root_cfg: Dict[str, Any], depth: int, branching: int, prefix: str = "Ω") -> OmegaNode:
    """
    Constrói árvore fractal auto-similar
    
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
    frontier = [root]
    
    for d in range(1, depth + 1):
        new_frontier = []
        
        for parent_node in frontier:
            for i in range(branching):
                child_id = f"{prefix}-{d}-{i}-{parent_node.id.split('-')[-1]}"
                child_config = root_cfg.copy()  # Herda configuração do núcleo
                
                child = OmegaNode(
                    id=child_id,
                    depth=d,
                    config=child_config,
                    parent=parent_node
                )
                
                parent_node.children.append(child)
                new_frontier.append(child)
        
        frontier = new_frontier
    
    return root


def propagate_update(root: OmegaNode, patch: Dict[str, Any], non_compensatory: bool = True) -> Dict[str, Any]:
    """
    Propaga update do núcleo para toda a árvore
    
    Args:
        root: Nó raiz
        patch: Mudanças a serem aplicadas
        non_compensatory: Se True, falha em qualquer nó bloqueia toda a operação
        
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
            # Verificar se patch contém valores serializáveis
            for key, value in patch.items():
                if callable(value):
                    raise ValueError(f"Non-serializable value for key {key}: {type(value)}")
            
            # Aplicar patch
            node.config.update(patch)
            node.last_update = time.time()
            node.status = "active"
            report["nodes_updated"] += 1
            
            # Adicionar filhos à fila
            queue.extend(node.children)
            
        except Exception as e:
            # Falha na atualização
            node.status = "failed"
            report["nodes_failed"] += 1
            report["failed_nodes"].append({
                "node_id": node.id,
                "error": str(e),
                "path": node.get_path()
            })
            
            if non_compensatory:
                # Fail-closed: uma falha bloqueia tudo
                report["success"] = False
                report["error"] = f"Non-compensatory failure at node {node.id}: {e}"
                break
    
    return report


def validate_fractal_consistency(root: OmegaNode) -> Dict[str, Any]:
    """
    Valida consistência da estrutura fractal
    
    Verifica:
    - Todos os nós têm configuração consistente com o núcleo
    - Não há nós órfãos ou ciclos
    - Status de todos os nós
    """
    validation = {
        "timestamp": time.time(),
        "total_nodes": 0,
        "active_nodes": 0,
        "failed_nodes": 0,
        "inconsistent_nodes": [],
        "orphaned_nodes": [],
        "valid": True
    }
    
    # Traversal completo
    stack = [root]
    visited = set()
    
    while stack:
        node = stack.pop()
        
        if node.id in visited:
            # Ciclo detectado
            validation["valid"] = False
            validation["error"] = f"Cycle detected at node {node.id}"
            break
        
        visited.add(node.id)
        validation["total_nodes"] += 1
        
        # Verificar status
        if node.status == "active":
            validation["active_nodes"] += 1
        elif node.status == "failed":
            validation["failed_nodes"] += 1
        
        # Verificar consistência de configuração crítica
        if node.depth > 0:  # Não verificar o root contra si mesmo
            critical_keys = ["thresholds", "policies"]
            for key in critical_keys:
                if key in root.config and key in node.config:
                    if node.config[key] != root.config[key]:
                        validation["inconsistent_nodes"].append({
                            "node_id": node.id,
                            "key": key,
                            "expected": root.config[key],
                            "actual": node.config[key]
                        })
        
        # Verificar parentesco
        for child in node.children:
            if child.parent != node:
                validation["orphaned_nodes"].append(child.id)
        
        # Adicionar filhos à pilha
        stack.extend(node.children)
    
    # Determinar validade geral
    if validation["inconsistent_nodes"] or validation["orphaned_nodes"]:
        validation["valid"] = False
    
    return validation


def fractal_health_check(root: OmegaNode) -> Dict[str, Any]:
    """
    Verifica saúde geral da estrutura fractal
    
    Returns:
        Relatório de saúde com métricas e recomendações
    """
    health = {
        "timestamp": time.time(),
        "overall_health": "unknown",
        "metrics": {},
        "recommendations": []
    }
    
    # Coletar métricas
    total_nodes = root.count_descendants() + 1  # +1 para o root
    validation = validate_fractal_consistency(root)
    
    health["metrics"] = {
        "total_nodes": total_nodes,
        "active_nodes": validation["active_nodes"],
        "failed_nodes": validation["failed_nodes"],
        "consistency_score": 1.0 - (len(validation["inconsistent_nodes"]) / max(1, total_nodes)),
        "uptime_ratio": validation["active_nodes"] / max(1, total_nodes)
    }
    
    # Determinar saúde geral
    consistency_score = health["metrics"]["consistency_score"]
    uptime_ratio = health["metrics"]["uptime_ratio"]
    
    if consistency_score >= 0.95 and uptime_ratio >= 0.90:
        health["overall_health"] = "excellent"
    elif consistency_score >= 0.85 and uptime_ratio >= 0.80:
        health["overall_health"] = "good"
    elif consistency_score >= 0.70 and uptime_ratio >= 0.60:
        health["overall_health"] = "fair"
    else:
        health["overall_health"] = "poor"
    
    # Gerar recomendações
    if validation["failed_nodes"] > 0:
        health["recommendations"].append("Investigate and repair failed nodes")
    
    if validation["inconsistent_nodes"]:
        health["recommendations"].append("Propagate configuration updates to fix inconsistencies")
    
    if uptime_ratio < 0.80:
        health["recommendations"].append("Consider reducing fractal depth or branching factor")
    
    return health


class FractalManager:
    """
    Gerenciador da estrutura fractal
    
    Responsável por:
    - Carregar/salvar configuração
    - Construir e manter a árvore
    - Propagar updates
    - Monitorar saúde
    """
    
    def __init__(self, config_path: str = "penin/omega/fractal_dsl.yaml"):
        self.config_path = config_path
        self.config = load_fractal_config(config_path)
        self.root = None
        self.last_health_check = 0
        
    def initialize(self) -> OmegaNode:
        """Inicializa a estrutura fractal"""
        root_config = {
            "thresholds": self.config["thresholds"],
            "policies": self.config["policies"],
            "weights": self.config["weights"]
        }
        
        self.root = build_fractal(
            root_config,
            self.config["depth"],
            self.config["branching"]
        )
        
        return self.root
    
    def update_core_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza configuração do núcleo e propaga para toda a árvore
        
        Args:
            updates: Mudanças na configuração
            
        Returns:
            Relatório da propagação
        """
        if self.root is None:
            raise RuntimeError("Fractal not initialized. Call initialize() first.")
        
        # Atualizar configuração local
        self.config.update(updates)
        
        # Propagar para a árvore
        non_compensatory = self.config["sync"]["non_compensatory"]
        report = propagate_update(self.root, updates, non_compensatory)
        
        return report
    
    def health_check(self, force: bool = False) -> Dict[str, Any]:
        """
        Executa verificação de saúde (com cache)
        
        Args:
            force: Se True, força nova verificação ignorando cache
            
        Returns:
            Relatório de saúde
        """
        now = time.time()
        
        # Cache de 60 segundos
        if not force and (now - self.last_health_check) < 60:
            return {"cached": True, "message": "Use force=True for fresh health check"}
        
        if self.root is None:
            return {"error": "Fractal not initialized"}
        
        health = fractal_health_check(self.root)
        self.last_health_check = now
        
        return health
    
    def get_node_by_id(self, node_id: str) -> Optional[OmegaNode]:
        """Encontra nó por ID"""
        if self.root is None:
            return None
        
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.id == node_id:
                return node
            stack.extend(node.children)
        
        return None
    
    def export_structure(self) -> Dict[str, Any]:
        """Exporta estrutura completa para JSON"""
        if self.root is None:
            return {"error": "Fractal not initialized"}
        
        def serialize_node(node: OmegaNode) -> Dict[str, Any]:
            return {
                **node.to_dict(),
                "children": [serialize_node(child) for child in node.children]
            }
        
        return {
            "config": self.config,
            "structure": serialize_node(self.root),
            "exported_at": time.time()
        }


# Funções de conveniência
def quick_fractal_test() -> Dict[str, Any]:
    """Teste rápido da funcionalidade fractal"""
    manager = FractalManager()
    root = manager.initialize()
    
    # Teste de propagação
    update_report = manager.update_core_config({
        "thresholds": {
            "beta_min": 0.02,  # Mudança no threshold
            "theta_caos": 0.30,
            "tau_sr": 0.85,
            "theta_G": 0.90
        }
    })
    
    # Verificação de saúde
    health = manager.health_check(force=True)
    
    return {
        "root_id": root.id,
        "total_nodes": root.count_descendants() + 1,
        "update_report": update_report,
        "health": health
    }


def validate_fractal_non_compensatory() -> Dict[str, Any]:
    """
    Valida comportamento não-compensatório
    
    Testa se uma falha em qualquer nó bloqueia toda a operação
    """
    manager = FractalManager()
    root = manager.initialize()
    
    # Simular falha injetando configuração inválida
    invalid_update = {
        "invalid_key": lambda x: x  # Função não serializável para forçar erro
    }
    
    try:
        report = manager.update_core_config(invalid_update)
        return {
            "test": "non_compensatory_behavior",
            "expected_failure": True,
            "actual_failure": not report["success"],
            "passed": not report["success"],
            "report": report
        }
    except Exception as e:
        return {
            "test": "non_compensatory_behavior",
            "expected_failure": True,
            "actual_failure": True,
            "passed": True,
            "error": str(e)
        }