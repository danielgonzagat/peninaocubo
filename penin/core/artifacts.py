"""
PENIN-Ω Core Artifacts
=======================

Data structures for knowledge representation and state management.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NumericVectorArtifact:
    """
    Numeric vector artifact for knowledge representation.

    Attributes:
        vector: List of numeric values representing the artifact
        metadata: Optional metadata dictionary
    """

    vector: list[float]
    metadata: dict[str, any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "__type__": "NumericVectorArtifact",
            "vector": self.vector,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> NumericVectorArtifact:
        """Create from dictionary."""
        return cls(
            vector=data["vector"],
            metadata=data.get("metadata", {}),
        )
