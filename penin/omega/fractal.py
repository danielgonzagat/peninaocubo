"""
Fractal DSL - Auto-similar Structure
=====================================

Estrutura fractal onde o núcleo propaga parâmetros/gates para submódulos.
Profundidade e branching configuráveis, propagação não-compensatória.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
import json
import os
from pathlib import Path


@dataclass
class OmegaNode:
    """Nó da estrutura fractal Ω"""
    id: str
    depth: int
    config: Dict[str, Any]
    children: List["OmegaNode"] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "depth": self.depth,
            "config": self.config,
            "children": [c.to_dict() for c in self.children]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OmegaNode":
        node = cls(
            id=data["id"],
            depth=data["depth"],
            config=data["config"]
        )
        node.children = [cls.from_dict(c) for c in data.get("children", [])]
        return node


def build_fractal(root_cfg: Dict[str, Any], depth: int, branching: int, prefix: str = "Ω") -> OmegaNode:
    """
    Constrói árvore fractal com profundidade e branching configuráveis.
    
    Args:
        root_cfg: Configuração do nó raiz
        depth: Profundidade máxima
        branching: Número de filhos por nó
        prefix: Prefixo para IDs dos nós
        
    Returns:
        OmegaNode raiz com toda a árvore
    """
    root = OmegaNode(id=f"{prefix}-0", depth=0, config=root_cfg.copy())
    frontier = [root]
    
    for d in range(1, depth + 1):
        new_frontier = []
        for node in frontier:
            for i in range(branching):
                child = OmegaNode(
                    id=f"{prefix}-{d}-{i}-{node.id}",
                    depth=d,
                    config=root_cfg.copy()
                )
                node.children.append(child)
                new_frontier.append(child)
        frontier = new_frontier
    
    return root


def propagate_update(root: OmegaNode, patch: Dict[str, Any]) -> int:
    """
    Propaga patch do núcleo para todos os nós (não-compensatório).
    
    Args:
        root: Nó raiz
        patch: Dicionário com atualizações de configuração
        
    Returns:
        Número de nós atualizados
    """
    count = 0
    stack = [root]
    
    while stack:
        node = stack.pop()
        node.config.update(patch)
        count += 1
        stack.extend(node.children)
    
    return count


def validate_fractal_consistency(root: OmegaNode, key: str) -> bool:
    """
    Valida que todos os nós têm o mesmo valor para uma chave crítica.
    
    Args:
        root: Nó raiz
        key: Chave para verificar consistência
        
    Returns:
        True se todos os nós têm o mesmo valor
    """
    if key not in root.config:
        return False
    
    expected_value = root.config[key]
    stack = [root]
    
    while stack:
        node = stack.pop()
        if node.config.get(key) != expected_value:
            return False
        stack.extend(node.children)
    
    return True


def count_nodes(root: OmegaNode) -> int:
    """Conta número total de nós na árvore"""
    count = 1
    for child in root.children:
        count += count_nodes(child)
    return count


def save_fractal(root: OmegaNode, filepath: str | Path) -> None:
    """Salva estrutura fractal em JSON"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(root.to_dict(), f, indent=2, ensure_ascii=False)


def load_fractal(filepath: str | Path) -> OmegaNode:
    """Carrega estrutura fractal de JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return OmegaNode.from_dict(data)


class FractalManager:
    """Gerencia estruturas fractais Ω"""
    
    def __init__(self, root_cfg: Dict[str, Any] = None):
        self.root_cfg = root_cfg or {}
        self.root = None
    
    def build(self, depth: int = 2, branching: int = 3) -> OmegaNode:
        """Constrói estrutura fractal"""
        self.root = build_fractal(self.root_cfg, depth, branching)
        return self.root
    
    def update_all(self, patch: Dict[str, Any]) -> int:
        """Atualiza todos os nós com patch"""
        if self.root is None:
            return 0
        return propagate_update(self.root, patch)
    
    def validate(self, key: str) -> bool:
        """Valida consistência de chave em todos os nós"""
        if self.root is None:
            return False
        return validate_fractal_consistency(self.root, key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da estrutura"""
        if self.root is None:
            return {"nodes": 0, "depth": 0}
        
        return {
            "nodes": count_nodes(self.root),
            "depth": self.root.depth,
            "config_keys": list(self.root.config.keys())
        }
    
    def save(self, filepath: str | Path) -> None:
        """Salva estrutura"""
        if self.root is not None:
            save_fractal(self.root, filepath)
    
    def load(self, filepath: str | Path) -> None:
        """Carrega estrutura"""
        self.root = load_fractal(filepath)
        if self.root:
            self.root_cfg = self.root.config.copy()