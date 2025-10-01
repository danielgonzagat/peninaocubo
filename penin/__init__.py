"""PENIN multi-API orchestration package."""

from __future__ import annotations

from importlib import metadata

from .config import settings  # noqa: F401
from .router import MultiLLMRouter  # noqa: F401

try:  # pragma: no cover - resolved at runtime when package is installed
    __version__ = metadata.version("peninaocubo")
except metadata.PackageNotFoundError:  # pragma: no cover - local source tree
    __version__ = "0.8.0"

__all__ = ["MultiLLMRouter", "settings", "__version__"]
