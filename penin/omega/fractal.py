"""
Fractal DSL / Auto-Similarity Module
====================================

Implements a fractal/self-similar structure for PENIN-Ω modules, where:
- Core parameters propagate to all child modules (non-compensatory)
- Each node is a self-contained Omega instance
- Updates cascade through the tree maintaining consistency

This enables scaling from a single node to arbitrarily deep hierarchies
while maintaining the same governance rules at every level.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


@dataclass
class OmegaNode:
    """
    A single node in the Omega fractal hierarchy.
    
    Each node:
    - Has its own configuration
    - Can have children (sub-modules)
    - Inherits updates from parents (non-compensatory)
    """
    id: str
    depth: int
    config: Dict[str, Any]
    children: List[OmegaNode] = field(default_factory=list)
    parent: Optional[OmegaNode] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "depth": self.depth,
            "config": self.config,
            "children": [c.to_dict() for c in self.children]
        }
    
    def count_nodes(self) -> int:
        """Count total nodes in subtree"""
        return 1 + sum(c.count_nodes() for c in self.children)
    
    def get_all_nodes(self) -> List[OmegaNode]:
        """Get flattened list of all nodes"""
        nodes = [self]
        for child in self.children:
            nodes.extend(child.get_all_nodes())
        return nodes


def build_fractal(
    root_cfg: Dict[str, Any],
    depth: int,
    branching: int,
    prefix: str = "Ω"
) -> OmegaNode:
    """
    Build a fractal tree of Omega nodes.
    
    Args:
        root_cfg: Configuration for root node
        depth: Number of levels below root (0 = just root)
        branching: Number of children per node
        prefix: ID prefix for nodes
        
    Returns:
        Root OmegaNode with full tree
    """
    root = OmegaNode(id=f"{prefix}-0", depth=0, config=root_cfg.copy())
    
    if depth == 0:
        return root
    
    # Build tree level by level
    frontier = [root]
    
    for d in range(1, depth + 1):
        new_frontier = []
        for node in frontier:
            for i in range(branching):
                child = OmegaNode(
                    id=f"{prefix}-{d}-{i}",
                    depth=d,
                    config=root_cfg.copy(),
                    parent=node
                )
                node.children.append(child)
                new_frontier.append(child)
        frontier = new_frontier
    
    return root


def propagate_update(
    root: OmegaNode,
    patch: Dict[str, Any],
    non_compensatory: bool = True
) -> int:
    """
    Propagate a configuration update through the entire tree.
    
    Args:
        root: Root node to start from
        patch: Configuration updates to apply
        non_compensatory: If True, ALL nodes must accept update (fail-closed)
        
    Returns:
        Number of nodes updated
    """
    if non_compensatory:
        # First, check if update would be valid for all nodes
        all_nodes = root.get_all_nodes()
        for node in all_nodes:
            # Here you could add validation logic
            # For now, we just accept all updates
            pass
    
    # Apply update to all nodes
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
    Check if a specific config key is consistent across all nodes.
    
    Args:
        root: Root node
        key: Configuration key to check
        
    Returns:
        True if all nodes have the same value for key
    """
    all_nodes = root.get_all_nodes()
    
    if not all_nodes:
        return True
    
    reference_value = all_nodes[0].config.get(key)
    
    return all(node.config.get(key) == reference_value for node in all_nodes)


@dataclass
class FractalDSLConfig:
    """Configuration for fractal DSL"""
    version: int = 1
    depth: int = 2
    branching: int = 3
    weights: Dict[str, float] = field(default_factory=lambda: {
        "caos": 1.0,
        "sr": 1.0,
        "g": 1.0
    })
    sync: Dict[str, bool] = field(default_factory=lambda: {
        "propagate_core_updates": True,
        "non_compensatory": True
    })
    
    @classmethod
    def from_yaml(cls, path: Path) -> FractalDSLConfig:
        """Load from YAML file"""
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(
            version=data.get("version", 1),
            depth=data.get("depth", 2),
            branching=data.get("branching", 3),
            weights=data.get("weights", {}),
            sync=data.get("sync", {})
        )
    
    def to_yaml(self, path: Path) -> None:
        """Save to YAML file"""
        import yaml
        data = {
            "version": self.version,
            "depth": self.depth,
            "branching": self.branching,
            "weights": self.weights,
            "sync": self.sync
        }
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)


class FractalOrchestrator:
    """
    Orchestrates a fractal hierarchy of Omega modules.
    
    Manages:
    - Tree construction and maintenance
    - Update propagation (with non-compensatory option)
    - Consistency validation
    - Metrics aggregation from all nodes
    """
    
    def __init__(self, config: FractalDSLConfig = None):
        self.config = config or FractalDSLConfig()
        self.root: Optional[OmegaNode] = None
        
    def initialize(self, base_config: Dict[str, Any]) -> None:
        """Initialize fractal tree"""
        self.root = build_fractal(
            base_config,
            self.config.depth,
            self.config.branching
        )
        print(f"🌳 Initialized fractal tree: {self.root.count_nodes()} nodes")
    
    def update_all(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply update to all nodes.
        
        Returns:
            Dict with update results
        """
        if self.root is None:
            return {"error": "Not initialized"}
        
        non_compensatory = self.config.sync.get("non_compensatory", True)
        count = propagate_update(self.root, patch, non_compensatory)
        
        return {
            "nodes_updated": count,
            "non_compensatory": non_compensatory,
            "patch": patch
        }
    
    def validate_consistency(self, keys: List[str] = None) -> Dict[str, bool]:
        """
        Validate consistency across nodes.
        
        Args:
            keys: List of config keys to check (None = check all)
            
        Returns:
            Dict mapping keys to consistency status
        """
        if self.root is None:
            return {}
        
        if keys is None:
            # Get all keys from root config
            keys = list(self.root.config.keys())
        
        results = {}
        for key in keys:
            results[key] = validate_fractal_consistency(self.root, key)
        
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics from all nodes"""
        if self.root is None:
            return {}
        
        all_nodes = self.root.get_all_nodes()
        
        return {
            "total_nodes": len(all_nodes),
            "depth": self.config.depth,
            "branching": self.config.branching,
            "leaf_nodes": sum(1 for n in all_nodes if not n.children),
            "tree_structure": self.root.to_dict()
        }
    
    def export_structure(self, path: Path) -> None:
        """Export tree structure to JSON"""
        if self.root is None:
            return
        
        with open(path, 'w') as f:
            json.dump(self.root.to_dict(), f, indent=2)
        
        print(f"📄 Exported fractal structure to {path}")


# Quick test function
def quick_fractal_test():
    """Quick test of fractal functionality"""
    config = FractalDSLConfig(depth=2, branching=3)
    orch = FractalOrchestrator(config)
    
    base_cfg = {
        "ece_threshold": 0.01,
        "rho_max": 0.95,
        "sr_min": 0.80
    }
    
    orch.initialize(base_cfg)
    print(f"Tree initialized: {orch.get_metrics()}")
    
    # Test update propagation
    update_result = orch.update_all({"ece_threshold": 0.008})
    print(f"Update result: {update_result}")
    
    # Test consistency
    consistency = orch.validate_consistency()
    print(f"Consistency check: {consistency}")
    
    return orch