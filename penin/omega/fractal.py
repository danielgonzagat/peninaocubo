from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OmegaNode:
    id: str
    depth: int
    config: dict[str, Any]
    children: list[OmegaNode] = field(default_factory=list)


def build_fractal(
    root_cfg: dict[str, Any], depth: int, branching: int, prefix="Ω"
) -> OmegaNode:
    root = OmegaNode(id=f"{prefix}-0", depth=0, config=dict(root_cfg))
    frontier = [root]
    for d in range(1, depth + 1):
        nxt = []
        for node in frontier:
            for i in range(branching):
                child = OmegaNode(
                    id=f"{prefix}-{d}-{i}", depth=d, config=dict(root_cfg)
                )
                node.children.append(child)
                nxt.append(child)
        frontier = nxt
    return root


def propagate_update(root: OmegaNode, patch: dict[str, Any]):
    stack = [root]
    while stack:
        node = stack.pop()
        node.config.update(patch)
        stack.extend(node.children)


def fractal_coherence(root: OmegaNode) -> float:
    """
    Compute coherence score for a fractal structure.
    Measures how consistent configurations are across the fractal tree.
    Returns a value between 0.0 (no coherence) and 1.0 (perfect coherence).
    """
    if not root:
        return 0.0

    # Collect all nodes
    nodes: list[OmegaNode] = []
    stack = [root]
    while stack:
        node = stack.pop()
        nodes.append(node)
        stack.extend(node.children)

    if len(nodes) <= 1:
        return 1.0

    # Compare configurations for coherence
    # Use root config as reference
    reference_config = root.config
    if not reference_config:
        return 1.0

    total_similarity = 0.0
    comparisons = 0

    for node in nodes[1:]:  # Skip root
        # Count matching keys and values
        matching = 0
        total_keys = len(reference_config)

        for key, ref_value in reference_config.items():
            if key in node.config and node.config[key] == ref_value:
                matching += 1

        if total_keys > 0:
            similarity = matching / total_keys
            total_similarity += similarity
            comparisons += 1

    if comparisons == 0:
        return 1.0

    return total_similarity / comparisons
