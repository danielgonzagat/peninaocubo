"""
PENIN-Ω Equation 12: OCI (Organizational Closure Index)
========================================================

Fórmula:
    OCI = (#dependências_fechadas) / (#dependências_possíveis)

Mede fechamento organizacional (feedback loops auditáveis).

Re-exports from penin.math.oci.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    from penin.math.oci import oci_score
except ImportError:
    oci_score = None


@dataclass
class OCIConfig:
    """Configuration for OCI."""

    min_closure_threshold: float = 0.80


@dataclass
class Dependency:
    """Represents a dependency edge."""

    from_node: str
    to_node: str
    is_closed: bool  # Has feedback loop


def organizational_closure_index(
    dependencies: list[Dependency], config: OCIConfig | None = None
) -> tuple[float, bool]:
    """
    Compute OCI from dependency graph.

    Returns:
        (OCI_score, gate_pass)
    """
    config = config or OCIConfig()

    if not dependencies:
        return 0.0, False

    closed_count = sum(1 for d in dependencies if d.is_closed)
    total_count = len(dependencies)

    oci = closed_count / total_count
    gate_pass = oci >= config.min_closure_threshold

    return oci, gate_pass


__all__ = ["OCIConfig", "Dependency", "organizational_closure_index", "oci_score"]
