"""
PENIN-Ω State Serialization
============================

JSON encoder/decoder for state persistence supporting custom types.
"""

from __future__ import annotations

import json
from collections import deque
from typing import Any

from penin.core.artifacts import NumericVectorArtifact


class StateEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for PENIN-Ω state objects.

    Handles:
    - NumericVectorArtifact
    - deque (collections)
    """

    def default(self, obj: Any) -> Any:
        """Convert custom objects to JSON-serializable format."""
        if isinstance(obj, NumericVectorArtifact):
            return obj.to_dict()

        if isinstance(obj, deque):
            return {
                "__type__": "deque",
                "items": list(obj),
                "maxlen": obj.maxlen,
            }

        return super().default(obj)


def state_decoder(dct: dict) -> Any:
    """
    Custom JSON decoder for PENIN-Ω state objects.

    Args:
        dct: Dictionary from JSON

    Returns:
        Decoded object (NumericVectorArtifact, deque, or original dict)
    """
    if "__type__" not in dct:
        return dct

    obj_type = dct["__type__"]

    if obj_type == "NumericVectorArtifact":
        return NumericVectorArtifact.from_dict(dct)

    if obj_type == "deque":
        items = dct["items"]
        maxlen = dct.get("maxlen")
        return deque(items, maxlen=maxlen)

    return dct
