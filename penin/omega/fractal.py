"""
Fractal DSL - Self-Similar Architecture
========================================

Implements fractal/self-similar architecture for PENIN-Ω.
Each node inherits configuration from parent with non-compensatory propagation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import os
import yaml
from pathlib import Path


@dataclass
class OmegaNode:
    """Fractal node in the Omega architecture"""
    id: str
    depth: int
    config: Dict[str, Any]
    children: List["OmegaNode"] = field(default_factory=list)
    health_score: float = 1.0
    resource_allocation: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation"""
        return {
            "id": self.id,
            "depth": self.depth,
            "config": self.config,
            "health_score": self.health_score,
            "resource_allocation": self.resource_allocation,
            "children": [c.id for c in self.children]
        }
    
    def propagate_health(self) -> float:
        """Calculate propagated health from children (non-compensatory)"""
        if not self.children:
            return self.health_score
        
        # Non-compensatory: worst child affects parent
        child_healths = [c.propagate_health() for c in self.children]
        min_child = min(child_healths) if child_healths else 1.0
        
        # Parent health is weighted combination (70% self, 30% worst child)
        return 0.7 * self.health_score + 0.3 * min_child


def load_fractal_config(config_path: str = "penin/omega/fractal_dsl.yaml") -> Dict[str, Any]:
    """Load fractal configuration from YAML"""
    if not os.path.exists(config_path):
        # Return default config if file doesn't exist
        return {
            "version": 1,
            "depth": 2,
            "branching": 3,
            "weights": {"caos": 1.0, "sr": 1.0, "g": 1.0},
            "sync": {"propagate_core_updates": True, "non_compensatory": True},
            "replication": {
                "inherit_thresholds": True,
                "scale_factor": 0.9,
                "min_resources": 0.1
            }
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def build_fractal(
    root_cfg: Dict[str, Any], 
    depth: int, 
    branching: int, 
    prefix: str = "Ω",
    scale_factor: float = 0.9
) -> OmegaNode:
    """
    Build fractal tree structure.
    
    Args:
        root_cfg: Root configuration dict
        depth: Tree depth
        branching: Number of children per node
        prefix: Node ID prefix
        scale_factor: Resource scaling per level
    
    Returns:
        Root OmegaNode with full tree
    """
    root = OmegaNode(
        id=f"{prefix}-0", 
        depth=0, 
        config=root_cfg.copy(),
        resource_allocation=1.0
    )
    
    # Build tree level by level
    frontier = [root]
    for d in range(1, depth + 1):
        new_frontier = []
        child_resources = scale_factor ** d
        
        for node in frontier:
            for i in range(branching):
                # Each child inherits parent config with scaled resources
                child_cfg = node.config.copy()
                child_cfg["resource_scale"] = child_resources
                
                child = OmegaNode(
                    id=f"{prefix}-{d}-{i}",
                    depth=d,
                    config=child_cfg,
                    resource_allocation=child_resources
                )
                node.children.append(child)
                new_frontier.append(child)
        
        frontier = new_frontier
    
    return root


def propagate_update(root: OmegaNode, patch: Dict[str, Any], non_compensatory: bool = True):
    """
    Propagate configuration update through tree.
    
    Args:
        root: Root node
        patch: Configuration patch to apply
        non_compensatory: If True, all nodes must accept update
    """
    # Use DFS to propagate updates
    stack = [root]
    updated = []
    
    while stack:
        node = stack.pop()
        
        # Apply patch to node
        old_config = node.config.copy()
        node.config.update(patch)
        updated.append((node, old_config))
        
        # Add children to stack
        stack.extend(node.children)
    
    # If non-compensatory, validate all updates succeeded
    if non_compensatory:
        for node, old_config in updated:
            # Simple validation: check required keys exist
            required = ["weights", "sync"]
            if not all(k in node.config for k in required):
                # Rollback on failure
                for n, old in updated:
                    n.config = old
                raise ValueError(f"Non-compensatory update failed at node {node.id}")


def find_node(root: OmegaNode, node_id: str) -> Optional[OmegaNode]:
    """Find node by ID in tree"""
    if root.id == node_id:
        return root
    
    for child in root.children:
        result = find_node(child, node_id)
        if result:
            return result
    
    return None


def calculate_tree_health(root: OmegaNode) -> Dict[str, float]:
    """
    Calculate health metrics for entire tree.
    
    Returns:
        Dict with health metrics
    """
    def traverse(node: OmegaNode) -> List[float]:
        healths = [node.health_score]
        for child in node.children:
            healths.extend(traverse(child))
        return healths
    
    all_healths = traverse(root)
    
    if not all_healths:
        return {"avg": 0.0, "min": 0.0, "max": 0.0}
    
    return {
        "avg": sum(all_healths) / len(all_healths),
        "min": min(all_healths),
        "max": max(all_healths),
        "propagated": root.propagate_health()
    }


class FractalOrchestrator:
    """Orchestrates fractal architecture operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_fractal_config(config_path) if config_path else load_fractal_config()
        self.root = self._build_tree()
        
    def _build_tree(self) -> OmegaNode:
        """Build tree from configuration"""
        return build_fractal(
            root_cfg=self.config,
            depth=self.config.get("depth", 2),
            branching=self.config.get("branching", 3),
            scale_factor=self.config.get("replication", {}).get("scale_factor", 0.9)
        )
    
    def update_all(self, patch: Dict[str, Any]) -> bool:
        """Update all nodes with patch"""
        try:
            propagate_update(
                self.root, 
                patch, 
                non_compensatory=self.config.get("sync", {}).get("non_compensatory", True)
            )
            return True
        except Exception as e:
            print(f"Update failed: {e}")
            return False
    
    def get_health(self) -> Dict[str, float]:
        """Get tree health metrics"""
        return calculate_tree_health(self.root)
    
    def find(self, node_id: str) -> Optional[OmegaNode]:
        """Find node by ID"""
        return find_node(self.root, node_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export tree structure as dict"""
        def node_to_full_dict(node: OmegaNode) -> Dict[str, Any]:
            d = node.to_dict()
            d["children"] = [node_to_full_dict(c) for c in node.children]
            return d
        
        return {
            "config": self.config,
            "tree": node_to_full_dict(self.root),
            "health": self.get_health()
        }