"""
Fractal DSL and auto-similarity propagation for PENIN-Ω
Implements hierarchical node structure with non-compensatory update propagation
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
import json
import os
import yaml
from pathlib import Path


@dataclass
class OmegaNode:
    """Fractal node in the Omega hierarchy"""
    id: str
    depth: int
    config: Dict[str, Any]
    children: List["OmegaNode"] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node and children to dict representation"""
        return {
            "id": self.id,
            "depth": self.depth,
            "config": self.config,
            "children": [child.to_dict() for child in self.children]
        }


def build_fractal(root_cfg: Dict[str, Any], depth: int, branching: int, prefix: str = "Ω") -> OmegaNode:
    """
    Build fractal tree structure
    
    Parameters:
    -----------
    root_cfg: Root configuration to propagate
    depth: Number of levels below root
    branching: Number of children per node
    prefix: Node ID prefix
    
    Returns:
    --------
    OmegaNode root with full tree structure
    """
    root = OmegaNode(id=f"{prefix}-0", depth=0, config=root_cfg.copy())
    frontier = [root]
    
    for d in range(1, depth + 1):
        new_frontier = []
        for node in frontier:
            for i in range(branching):
                child_id = f"{prefix}-{d}-{node.id.split('-')[-1]}-{i}"
                child = OmegaNode(id=child_id, depth=d, config=root_cfg.copy())
                node.children.append(child)
                new_frontier.append(child)
        frontier = new_frontier
    
    return root


def propagate_update(root: OmegaNode, patch: Dict[str, Any], non_compensatory: bool = True):
    """
    Propagate configuration updates through the fractal tree
    
    Parameters:
    -----------
    root: Root node of the tree
    patch: Configuration updates to apply
    non_compensatory: If True, all nodes receive the same update (fail-closed)
    """
    stack = [root]
    while stack:
        node = stack.pop()
        if non_compensatory:
            # Non-compensatory: exact same update for all
            node.config.update(patch)
        else:
            # Compensatory: could apply weighted/modified updates
            # For now, same as non-compensatory
            node.config.update(patch)
        stack.extend(node.children)


def load_fractal_config(config_path: str = None) -> Dict[str, Any]:
    """Load fractal configuration from YAML file"""
    if config_path is None:
        config_path = Path(__file__).parent / "fractal_dsl.yaml"
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def apply_fractal_weights(node: OmegaNode, weights: Dict[str, float]) -> float:
    """
    Apply fractal weights to compute node score
    
    Parameters:
    -----------
    node: Node to evaluate
    weights: Weight dictionary for metrics
    
    Returns:
    --------
    Weighted score for the node
    """
    score = 0.0
    for key, weight in weights.items():
        if key in node.config:
            score += weight * float(node.config.get(key, 0.0))
    return score


def collect_metrics(root: OmegaNode) -> Dict[str, List[float]]:
    """
    Collect all metrics from the fractal tree
    
    Returns:
    --------
    Dictionary mapping metric names to list of values across all nodes
    """
    metrics = {}
    stack = [root]
    
    while stack:
        node = stack.pop()
        for key, value in node.config.items():
            if isinstance(value, (int, float)):
                if key not in metrics:
                    metrics[key] = []
                metrics[key].append(float(value))
        stack.extend(node.children)
    
    return metrics


def fractal_coherence(root: OmegaNode, threshold: float = 0.1) -> float:
    """
    Compute fractal coherence (how similar nodes are to root)
    
    Parameters:
    -----------
    root: Root node
    threshold: Maximum deviation allowed for coherence
    
    Returns:
    --------
    Coherence score [0, 1] where 1 is perfect coherence
    """
    if not root.children:
        return 1.0
    
    root_values = {k: v for k, v in root.config.items() if isinstance(v, (int, float))}
    deviations = []
    
    stack = list(root.children)
    while stack:
        node = stack.pop()
        for key, root_val in root_values.items():
            if key in node.config:
                node_val = node.config[key]
                if isinstance(node_val, (int, float)):
                    deviation = abs(float(node_val) - float(root_val))
                    deviations.append(min(deviation / threshold, 1.0))
        stack.extend(node.children)
    
    if not deviations:
        return 1.0
    
    # Return inverse of mean deviation
    return 1.0 - (sum(deviations) / len(deviations))


def quick_test():
    """Quick test of fractal system"""
    # Load config
    config = load_fractal_config()
    
    # Build fractal tree
    root_cfg = {
        "caos": 0.8,
        "sr": 0.75,
        "g": 0.9,
        "alpha": 0.001
    }
    
    tree = build_fractal(
        root_cfg=root_cfg,
        depth=config["depth"],
        branching=config["branching"]
    )
    
    # Test propagation
    update = {"alpha": 0.002, "caos": 0.85}
    propagate_update(tree, update, non_compensatory=config["sync"]["non_compensatory"])
    
    # Check coherence
    coherence = fractal_coherence(tree)
    
    # Collect metrics
    metrics = collect_metrics(tree)
    
    return {
        "tree": tree,
        "coherence": coherence,
        "metrics": metrics,
        "node_count": 1 + config["branching"] + config["branching"]**2
    }


if __name__ == "__main__":
    result = quick_test()
    print(f"Fractal tree built with {result['node_count']} nodes")
    print(f"Coherence: {result['coherence']:.3f}")
    print(f"Metrics collected: {list(result['metrics'].keys())}")
    print(f"Root config: {result['tree'].config}")