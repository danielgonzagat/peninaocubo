"""
Neurosymbolic AI Integrations
==============================

Integrates neurosymbolic reasoning frameworks that combine neural learning
with symbolic logic for interpretable, verifiable AI decisions.

Technologies:
-------------
1. **SymbolicAI** (ExtensityAI) - Neurosymbolic reasoning framework
   - Combines neural networks with symbolic reasoning
   - Logical consistency validation
   - Constraint satisfaction checking
   - Interpretable decision explanations

Key Features:
-------------
- Logic validation for SR-Ω∞ decisions
- Symbolic reasoning for ethical constraints
- Neurosymbolic fusion for interpretability
- Formal verification capabilities
- Explainable AI (XAI) support

Ethical Considerations:
-----------------------
- **LO-01 Compliance**: Symbolic reasoning enhances interpretability
- **IR→IC**: Formal verification reduces uncertainty in critical decisions
- **Fail-Closed**: Invalid symbolic proofs block risky transitions
- **Auditability**: All logical reasoning chains logged to WORM ledger

Integration with PENIN-Ω:
--------------------------
- Validates champion-challenger transitions in SR-Ω∞
- Ensures ethical constraint satisfaction in CAOS+
- Provides interpretable explanations for Ω-META decisions
- Formal verification for critical system state changes
"""

from penin.integrations.symbolic.symbolicai_adapter import (
    SymbolicAIAdapter,
    SymbolicAIConfig,
)

__all__ = ["SymbolicAIAdapter", "SymbolicAIConfig"]
