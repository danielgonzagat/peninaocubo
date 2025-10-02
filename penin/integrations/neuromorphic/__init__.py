"""
Neuromorphic Computing Integrations
====================================

Integrates state-of-the-art spiking neural network frameworks for
massive efficiency gains (100× speedup, 69% sparsity).

Technologies:
-------------
1. **SpikingJelly** (5.2k⭐) - PyTorch framework for SNNs
   - 11× training acceleration
   - CUDA-enhanced neurons
   - Major neuromorphic hardware support
   - Science Advances published

2. **SpikingBrain-7B** (2025 breakthrough) - 7B parameter SNN LLM
   - 100× speedup in time-to-first-token for 4M-token sequences
   - 69% sparsity
   - Matches mainstream model performance with 2% training data

Key Features:
-------------
- Event-driven computation (only fire on spikes)
- Temporal encoding (information in spike timing)
- Energy efficiency (neuromorphic hardware compatible)
- Biological plausibility
- Gradient descent via surrogate gradients

Ethical Considerations:
-----------------------
- **LO-01 Compliance**: SNNs are computational models, not biological consciousness
- **IR→IC**: Spiking behavior increases uncertainty initially, must demonstrate ρ<1
- **Fail-Closed**: Revert to traditional ANN if SNN validation fails
- **Auditability**: Log all spike patterns and membrane potentials

Performance Targets:
--------------------
- Inference: 100× faster than dense ANNs
- Training: 11× faster with specialized acceleration
- Memory: 69% reduction via sparsity
- Energy: 1000× lower for neuromorphic hardware
"""

from penin.integrations.neuromorphic.spikingjelly_adapter import (
    SpikingJellyConfig,
    SpikingNetworkAdapter,
)

try:
    from penin.integrations.neuromorphic.spiking_brain_adapter import (
        SpikingBrainAdapter,
    )

    __all__ = ["SpikingNetworkAdapter", "SpikingJellyConfig", "SpikingBrainAdapter"]
except ImportError:
    __all__ = ["SpikingNetworkAdapter", "SpikingJellyConfig"]
