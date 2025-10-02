"""
PENIN-Ω Autoregeneração Module
===============================

Continuous self-improvement and auto-regeneration.

Implements F10: Autoregeneração e Autotreinamento
"""

from .continuous_learning import (
    ContinuousLearner,
    LearningMode,
    LearningSnapshot,
    RegenerationConfig,
    create_continuous_learner,
)
from .data_stream import (
    DataSample,
    DataStreamProcessor,
    create_data_stream,
)

__all__ = [
    "ContinuousLearner",
    "LearningMode",
    "LearningSnapshot",
    "RegenerationConfig",
    "create_continuous_learner",
    "DataSample",
    "DataStreamProcessor",
    "create_data_stream",
]
