__version__ = "0.1.0"

"""PENIN multi-API orchestration package.

Contains configuration, provider adapters, a multi-LLM router, tool schemas,
and ingestion helpers (Kaggle/HuggingFace/papers). All components are optional
and import lazily so existing modules can run without these dependencies.
"""

__all__ = [
    "config",
    "router",
]
