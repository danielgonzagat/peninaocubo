"""
Fractal DSL and Auto-Similarity Engine
======================================

Implements fractal/auto-similar architecture where core parameters
are propagated to submódulos maintaining non-compensatory behavior.
"""

from __future__ import annotations
import yaml
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class OmegaNode:
    """Node in the fractal tree"""
    id: str
    depth: int
    config: Dict[str, Any]
    children: List["OmegaNode"] = field(default_factory=list)
    parent: Optional["OmegaNode"] = None
    last_update: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "depth": self.depth,
            "config": self.config,
            "children_ids": [c.id for c in self.children],
            "parent_id": self.parent.id if self.parent else None,
            "last_update": self.last_update
        }


@dataclass
class FractalConfig:
    """Configuration for fractal tree"""
    version: int = 1
    depth: int = 2
    branching: int = 3
    weights: Dict[str, float] = field(default_factory=lambda: {
        "caos": 1.0,
        "sr": 1.0,
        "g": 1.0
    })
    sync: Dict[str, Any] = field(default_factory=lambda: {
        "propagate_core_updates": True,
        "non_compensatory": True
    })


class FractalTree:
    """Fractal tree builder and manager"""
    
    def __init__(self, config: FractalConfig = None):
        self.config = config or FractalConfig()
        self.root: Optional[OmegaNode] = None
        self.nodes: Dict[str, OmegaNode] = {}
        self.update_history: List[Dict[str, Any]] = []
    
    def build_fractal(self, root_cfg: Dict[str, Any], prefix: str = "Ω") -> OmegaNode:
        """Build fractal tree from root configuration"""
        self.root = OmegaNode(
            id=f"{prefix}-0",
            depth=0,
            config=root_cfg.copy(),
            last_update=time.time()
        )
        self.nodes[self.root.id] = self.root
        
        frontier = [self.root]
        
        for d in range(1, self.config.depth + 1):
            new_frontier = []
            for node in frontier:
                for i in range(self.config.branching):
                    child_id = f"{prefix}-{d}-{i}"
                    child_config = root_cfg.copy()
                    
                    # Add fractal-specific parameters
                    child_config.update({
                        "fractal_depth": d,
                        "fractal_branch": i,
                        "parent_id": node.id,
                        "fractal_weights": self.config.weights.copy()
                    })
                    
                    child = OmegaNode(
                        id=child_id,
                        depth=d,
                        config=child_config,
                        parent=node,
                        last_update=time.time()
                    )
                    
                    node.children.append(child)
                    self.nodes[child_id] = child
                    new_frontier.append(child)
            
            frontier = new_frontier
        
        return self.root
    
    def propagate_update(self, patch: Dict[str, Any], 
                        non_compensatory: bool = True) -> Dict[str, Any]:
        """
        Propagate update from root to all children
        
        Args:
            patch: Configuration patch to apply
            non_compensatory: If True, all children get exact same patch
            
        Returns:
            Update summary with affected nodes
        """
        if not self.root:
            raise ValueError("No fractal tree built yet")
        
        update_start = time.time()
        affected_nodes = []
        
        # Apply patch to root
        self.root.config.update(patch)
        self.root.last_update = update_start
        affected_nodes.append(self.root.id)
        
        # Propagate to all children
        stack = list(self.root.children)
        while stack:
            node = stack.pop()
            
            if non_compensatory:
                # Non-compensatory: exact same patch
                node.config.update(patch)
            else:
                # Compensatory: allow some variation based on depth/position
                modified_patch = self._modify_patch_for_node(patch, node)
                node.config.update(modified_patch)
            
            node.last_update = update_start
            affected_nodes.append(node.id)
            
            # Add children to stack
            stack.extend(node.children)
        
        # Record update
        update_record = {
            "timestamp": update_start,
            "patch": patch,
            "affected_nodes": affected_nodes,
            "non_compensatory": non_compensatory,
            "total_nodes": len(affected_nodes)
        }
        self.update_history.append(update_record)
        
        return update_record
    
    def _modify_patch_for_node(self, patch: Dict[str, Any], 
                              node: OmegaNode) -> Dict[str, Any]:
        """Modify patch for specific node (compensatory mode)"""
        modified = patch.copy()
        
        # Add depth-based scaling
        depth_factor = 1.0 - (node.depth * 0.1)  # Slight reduction with depth
        
        for key, value in modified.items():
            if isinstance(value, (int, float)):
                modified[key] = value * depth_factor
        
        return modified
    
    def get_node_config(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific node"""
        node = self.nodes.get(node_id)
        return node.config if node else None
    
    def get_subtree_configs(self, root_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all configurations in subtree"""
        root = self.nodes.get(root_id)
        if not root:
            return {}
        
        configs = {}
        stack = [root]
        
        while stack:
            node = stack.pop()
            configs[node.id] = node.config.copy()
            stack.extend(node.children)
        
        return configs
    
    def validate_consistency(self) -> Dict[str, Any]:
        """Validate consistency across fractal tree"""
        if not self.root:
            return {"valid": False, "error": "No tree built"}
        
        issues = []
        core_params = set(self.root.config.keys())
        
        # Check all nodes have core parameters
        for node_id, node in self.nodes.items():
            node_params = set(node.config.keys())
            missing_params = core_params - node_params
            if missing_params:
                issues.append(f"Node {node_id} missing params: {missing_params}")
        
        # Check non-compensatory consistency
        if self.config.sync.get("non_compensatory", True):
            core_values = {}
            for param in core_params:
                if isinstance(self.root.config[param], (int, float, str, bool)):
                    core_values[param] = self.root.config[param]
            
            for node_id, node in self.nodes.items():
                for param, expected_value in core_values.items():
                    if node.config.get(param) != expected_value:
                        issues.append(f"Node {node_id} param {param} inconsistent")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "total_nodes": len(self.nodes),
            "core_params": len(core_params)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fractal tree statistics"""
        if not self.root:
            return {"nodes": 0, "depth": 0, "updates": 0}
        
        depths = [node.depth for node in self.nodes.values()]
        update_times = [node.last_update for node in self.nodes.values()]
        
        return {
            "nodes": len(self.nodes),
            "depth": max(depths) if depths else 0,
            "avg_depth": sum(depths) / len(depths) if depths else 0,
            "updates": len(self.update_history),
            "last_update": max(update_times) if update_times else 0,
            "config_version": self.config.version
        }
    
    def export_tree(self) -> Dict[str, Any]:
        """Export entire tree structure"""
        return {
            "config": {
                "version": self.config.version,
                "depth": self.config.depth,
                "branching": self.config.branching,
                "weights": self.config.weights,
                "sync": self.config.sync
            },
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "update_history": self.update_history[-10:],  # Last 10 updates
            "stats": self.get_stats()
        }
    
    def load_from_yaml(self, yaml_path: str) -> FractalConfig:
        """Load fractal configuration from YAML"""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        self.config = FractalConfig(
            version=data.get("version", 1),
            depth=data.get("depth", 2),
            branching=data.get("branching", 3),
            weights=data.get("weights", {"caos": 1.0, "sr": 1.0, "g": 1.0}),
            sync=data.get("sync", {"propagate_core_updates": True, "non_compensatory": True})
        )
        
        return self.config


# Utility functions
def create_fractal_tree(config_path: str = None, 
                       root_config: Dict[str, Any] = None) -> FractalTree:
    """Create fractal tree from config"""
    tree = FractalTree()
    
    if config_path and Path(config_path).exists():
        tree.load_from_yaml(config_path)
    
    if root_config is None:
        root_config = {
            "base_alpha": 1e-3,
            "caos_kappa": 20.0,
            "sr_threshold": 0.80,
            "life_thresholds": {
                "beta_min": 0.01,
                "theta_caos": 0.25,
                "tau_sr": 0.80,
                "theta_G": 0.85
            }
        }
    
    tree.build_fractal(root_config)
    return tree


def propagate_life_equation_params(tree: FractalTree, 
                                  life_params: Dict[str, Any]) -> Dict[str, Any]:
    """Propagate Life Equation parameters through fractal tree"""
    return tree.propagate_update(life_params, non_compensatory=True)


def validate_fractal_consistency(tree: FractalTree) -> bool:
    """Validate fractal tree consistency"""
    result = tree.validate_consistency()
    return result["valid"]


# Example usage
if __name__ == "__main__":
    # Create fractal tree
    tree = create_fractal_tree()
    
    # Propagate update
    update_result = tree.propagate_update({
        "base_alpha": 2e-3,
        "caos_kappa": 25.0
    })
    
    print(f"Updated {update_result['total_nodes']} nodes")
    print(f"Tree stats: {tree.get_stats()}")
    
    # Validate consistency
    consistency = tree.validate_consistency()
    print(f"Consistency: {consistency['valid']}")