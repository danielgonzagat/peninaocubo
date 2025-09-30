"""
Fractal DSL and Propagation Engine
==================================

Implements auto-similarity and fractal propagation for PENIN-Ω modules.
Non-compensatory propagation: core updates spread to all children.
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
    """Fractal node in the omega tree"""
    id: str
    depth: int
    config: Dict[str, Any]
    children: List["OmegaNode"] = field(default_factory=list)
    parent: Optional["OmegaNode"] = None
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "depth": self.depth,
            "config": self.config,
            "children_ids": [c.id for c in self.children],
            "parent_id": self.parent.id if self.parent else None,
            "created_at": self.created_at
        }


class FractalConfig:
    """Configuration for fractal tree"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                self.data = yaml.safe_load(f)
        else:
            # Default configuration
            self.data = {
                "version": 1,
                "depth": 2,
                "branching": 3,
                "weights": {
                    "caos": 1.0,
                    "sr": 1.0,
                    "g": 1.0
                },
                "sync": {
                    "propagate_core_updates": True,
                    "non_compensatory": True
                }
            }
    
    @property
    def depth(self) -> int:
        return self.data.get("depth", 2)
    
    @property
    def branching(self) -> int:
        return self.data.get("branching", 3)
    
    @property
    def weights(self) -> Dict[str, float]:
        return self.data.get("weights", {"caos": 1.0, "sr": 1.0, "g": 1.0})
    
    @property
    def propagate_core_updates(self) -> bool:
        return self.data.get("sync", {}).get("propagate_core_updates", True)
    
    @property
    def non_compensatory(self) -> bool:
        return self.data.get("sync", {}).get("non_compensatory", True)


def build_fractal(
    root_cfg: Dict[str, Any], 
    depth: int, 
    branching: int, 
    prefix: str = "Ω"
) -> OmegaNode:
    """
    Build fractal tree structure
    
    Args:
        root_cfg: Root configuration
        depth: Tree depth
        branching: Children per node
        prefix: Node ID prefix
        
    Returns:
        Root node of the fractal tree
    """
    root = OmegaNode(id=f"{prefix}-0", depth=0, config=root_cfg.copy())
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


def propagate_update(root: OmegaNode, patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Propagate core updates to all children (non-compensatory)
    
    Args:
        root: Root node of the tree
        patch: Configuration patch to apply
        
    Returns:
        Dict with propagation statistics
    """
    stats = {
        "nodes_updated": 0,
        "depth_reached": 0,
        "propagation_time": 0
    }
    
    start_time = time.time()
    
    # Non-compensatory: every child receives the core patch
    stack = [root]
    while stack:
        node = stack.pop()
        
        # Apply patch
        node.config.update(patch)
        stats["nodes_updated"] += 1
        stats["depth_reached"] = max(stats["depth_reached"], node.depth)
        
        # Add children to stack
        stack.extend(node.children)
    
    stats["propagation_time"] = time.time() - start_time
    return stats


def collect_tree_state(root: OmegaNode) -> Dict[str, Any]:
    """
    Collect state from entire tree
    
    Args:
        root: Root node
        
    Returns:
        Dict with tree state
    """
    nodes = []
    stack = [root]
    
    while stack:
        node = stack.pop()
        nodes.append(node.to_dict())
        stack.extend(node.children)
    
    return {
        "total_nodes": len(nodes),
        "max_depth": max(n["depth"] for n in nodes),
        "nodes": nodes
    }


def validate_fractal_integrity(root: OmegaNode) -> Dict[str, Any]:
    """
    Validate fractal tree integrity
    
    Args:
        root: Root node
        
    Returns:
        Validation results
    """
    issues = []
    
    # Check parent-child relationships
    stack = [root]
    while stack:
        node = stack.pop()
        
        # Check children have correct parent reference
        for child in node.children:
            if child.parent != node:
                issues.append(f"Child {child.id} has incorrect parent reference")
        
        # Check parent has child in children list
        if node.parent:
            if node not in node.parent.children:
                issues.append(f"Node {node.id} not in parent's children list")
        
        stack.extend(node.children)
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "total_nodes": len(collect_tree_state(root)["nodes"])
    }


class FractalManager:
    """Manager for fractal tree operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = FractalConfig(config_path)
        self.root: Optional[OmegaNode] = None
        self.update_history: List[Dict[str, Any]] = []
    
    def initialize_tree(self, root_config: Dict[str, Any]) -> OmegaNode:
        """Initialize fractal tree"""
        self.root = build_fractal(
            root_config,
            self.config.depth,
            self.config.branching
        )
        return self.root
    
    def update_core(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        """Update core configuration and propagate"""
        if not self.root:
            raise ValueError("Tree not initialized")
        
        # Record update
        update_record = {
            "timestamp": time.time(),
            "patch": patch,
            "before_state": collect_tree_state(self.root)
        }
        
        # Propagate update
        stats = propagate_update(self.root, patch)
        
        # Record after state
        update_record["after_state"] = collect_tree_state(self.root)
        update_record["stats"] = stats
        
        self.update_history.append(update_record)
        
        return stats
    
    def get_node_by_id(self, node_id: str) -> Optional[OmegaNode]:
        """Find node by ID"""
        if not self.root:
            return None
        
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.id == node_id:
                return node
            stack.extend(node.children)
        
        return None
    
    def get_nodes_at_depth(self, depth: int) -> List[OmegaNode]:
        """Get all nodes at specific depth"""
        if not self.root:
            return []
        
        nodes = []
        stack = [self.root]
        
        while stack:
            node = stack.pop()
            if node.depth == depth:
                nodes.append(node)
            elif node.depth < depth:
                stack.extend(node.children)
        
        return nodes
    
    def validate_tree(self) -> Dict[str, Any]:
        """Validate entire tree"""
        if not self.root:
            return {"valid": False, "error": "Tree not initialized"}
        
        return validate_fractal_integrity(self.root)
    
    def export_tree(self, filepath: str) -> None:
        """Export tree to JSON file"""
        if not self.root:
            raise ValueError("Tree not initialized")
        
        tree_data = {
            "config": self.config.data,
            "tree_state": collect_tree_state(self.root),
            "update_history": self.update_history,
            "exported_at": time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(tree_data, f, indent=2)
    
    def import_tree(self, filepath: str) -> None:
        """Import tree from JSON file"""
        with open(filepath, 'r') as f:
            tree_data = json.load(f)
        
        # Restore config
        self.config.data = tree_data["config"]
        
        # Note: Tree reconstruction from state would require more complex logic
        # For now, just restore the update history
        self.update_history = tree_data.get("update_history", [])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fractal manager statistics"""
        if not self.root:
            return {"status": "not_initialized"}
        
        tree_state = collect_tree_state(self.root)
        validation = self.validate_tree()
        
        return {
            "status": "initialized",
            "total_nodes": tree_state["total_nodes"],
            "max_depth": tree_state["max_depth"],
            "valid": validation["valid"],
            "update_count": len(self.update_history),
            "config": self.config.data
        }


# Convenience functions
def create_default_fractal() -> FractalManager:
    """Create default fractal manager"""
    manager = FractalManager()
    default_config = {
        "base_alpha": 1e-3,
        "caos_kappa": 20.0,
        "sr_threshold": 0.8,
        "global_coherence_threshold": 0.85
    }
    manager.initialize_tree(default_config)
    return manager


def quick_fractal_update(
    manager: FractalManager, 
    param_name: str, 
    param_value: Any
) -> Dict[str, Any]:
    """Quick fractal update"""
    patch = {param_name: param_value}
    return manager.update_core(patch)


def test_fractal_propagation() -> Dict[str, Any]:
    """Test fractal propagation"""
    manager = create_default_fractal()
    
    # Test update
    stats1 = quick_fractal_update(manager, "test_param", 42)
    
    # Test another update
    stats2 = quick_fractal_update(manager, "another_param", "test_value")
    
    # Get final stats
    final_stats = manager.get_stats()
    
    return {
        "update1_stats": stats1,
        "update2_stats": stats2,
        "final_stats": final_stats,
        "validation": manager.validate_tree()
    }