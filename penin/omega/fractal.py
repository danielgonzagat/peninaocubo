from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class OmegaNode:
    id: str
    depth: int
    config: Dict[str, Any]
    children: List["OmegaNode"] = field(default_factory=list)


def build_fractal(root_cfg: Dict[str, Any], depth: int, branching: int, prefix: str = "Ω") -> OmegaNode:
    root = OmegaNode(id=f"{prefix}-0", depth=0, config=dict(root_cfg))
    frontier = [root]
    for d in range(1, depth + 1):
        new: List[OmegaNode] = []
        for node in frontier:
            for i in range(branching):
                child = OmegaNode(id=f"{prefix}-{d}-{i}", depth=d, config=dict(root_cfg))
                node.children.append(child)
                new.append(child)
        frontier = new
    return root


def propagate_update(root: OmegaNode, patch: Dict[str, Any]) -> None:
    stack = [root]
    while stack:
        node = stack.pop()
        node.config.update(patch)
        stack.extend(node.children)

