# SymbolicAI Integration

## Overview

The SymbolicAI adapter integrates neurosymbolic reasoning capabilities into PENIN-Ω, enabling the system to validate logical consistency of decisions, verify ethical constraints, and provide interpretable explanations.

**Priority:** P2 - High (SOTA Self-Modifying Evolution)  
**Repository:** https://github.com/ExtensityAI/symbolicai

## Features

### Core Capabilities

1. **Decision Validation** - Validate logical consistency of SR-Ω∞ champion-challenger decisions
2. **Symbolic Reasoning** - Apply formal logic to AI decisions and reasoning chains
3. **Constraint Verification** - Check satisfaction of ethical and logical constraints
4. **Explainable AI** - Generate interpretable explanations for decisions

### Key Operations

- `validate` - Validate decision logic and consistency
- `reason` - Apply symbolic reasoning with configurable depth
- `verify` - Verify constraint satisfaction
- `explain` - Generate human-readable explanations

## Configuration

```python
from penin.integrations.symbolic import SymbolicAIAdapter, SymbolicAIConfig

config = SymbolicAIConfig(
    reasoning_depth=5,              # Depth of reasoning chain (1-10)
    enable_logic_validation=True,   # Enable formal logic validation
    enable_constraint_checking=True, # Enable constraint satisfaction
    min_confidence=0.85,            # Minimum confidence threshold
    symbolic_fusion=True,           # Enable neurosymbolic fusion
    require_proof=False,            # Require formal proofs
    explain_reasoning=True,         # Generate explanations
    fail_open=False,                # Fail-closed mode (production safe)
)

adapter = SymbolicAIAdapter(config=config)
```

## Usage

### Basic Validation

```python
import asyncio
from penin.integrations.symbolic import SymbolicAIAdapter

async def validate_decision():
    adapter = SymbolicAIAdapter()
    adapter.initialize()
    
    decision = {
        "type": "champion_challenger",
        "score": 0.89,
        "confidence": 0.91,
        "verdict": "pass"
    }
    
    result = await adapter.execute("validate", decision=decision)
    
    if result["valid"]:
        print("✅ Decision is logically valid")
    else:
        print("❌ Decision validation failed")

asyncio.run(validate_decision())
```

### SR-Ω∞ Integration

```python
async def validate_sr_omega():
    adapter = SymbolicAIAdapter()
    adapter.initialize()
    
    # Decision from SR-Ω∞ Service
    decision = {
        "type": "champion_challenger_transition",
        "champion_model": "model_v1",
        "challenger_model": "model_v2",
        "score": 0.89,
        "confidence": 0.91,
        "verdict": "pass"
    }
    
    # Ethical constraints from CAOS+
    ethical_constraints = [
        "LO-01_compliance",
        "fail_closed_principle",
        "auditability_requirement",
        "no_harm_principle"
    ]
    
    # Validate with SymbolicAI
    validation = await adapter.validate_sr_omega_decision(
        decision,
        ethical_constraints
    )
    
    # Check results
    if (validation["valid"] and 
        validation["constraint_verification"]["all_constraints_satisfied"]):
        # Safe to proceed with transition
        print("✅ Decision validated - proceeding with transition")
    else:
        # Fail-closed: revert to champion
        print("❌ Validation failed - reverting to champion")

asyncio.run(validate_sr_omega())
```

### Symbolic Reasoning

```python
async def symbolic_reasoning():
    adapter = SymbolicAIAdapter()
    adapter.initialize()
    
    decision = {
        "type": "architecture_modification",
        "proposed_change": "Add neural layer",
        "impact_score": 0.75
    }
    
    reasoning = await adapter.reason(decision)
    
    print("Conclusions:")
    for conclusion in reasoning["conclusions"]:
        print(f"  • {conclusion}")

asyncio.run(symbolic_reasoning())
```

## Integration with PENIN-Ω

### SR-Ω∞ Service

The primary integration point is with the SR-Ω∞ Service for validating champion-challenger decisions:

```python
class SROmegaService:
    def __init__(self):
        self.symbolicai = SymbolicAIAdapter()
        self.symbolicai.initialize()
    
    async def evaluate_challenger(self, champion, challenger):
        # Generate decision
        decision = self.generate_decision(champion, challenger)
        
        # Validate with SymbolicAI
        validation = await self.symbolicai.validate_sr_omega_decision(
            decision,
            self.ethical_constraints
        )
        
        # Fail-closed: only proceed if valid
        if validation["valid"] and \
           validation["constraint_verification"]["all_constraints_satisfied"]:
            self.apply_transition(challenger)
            self.worm_ledger.log(validation)
        else:
            logger.warning("Decision failed validation")
            self.revert_to_champion()
```

### CAOS+ Integration

Validates ethical constraint satisfaction:

```python
# In CAOS+ system
validation = await symbolicai.verify(
    decision=caos_decision,
    context={"constraints": ethical_laws}
)

if not validation["all_constraints_satisfied"]:
    raise EthicalViolationError(validation["violated_constraints"])
```

## Testing

Run the test suite:

```bash
pytest tests/integrations/test_symbolicai.py -v
```

Run the demo:

```bash
python examples/demo_symbolicai.py
```

## Architecture

### Class Hierarchy

```
BaseIntegrationAdapter (base.py)
    ↓
SymbolicAIAdapter (symbolicai_adapter.py)
    • SymbolicAIConfig - Configuration
    • validate_sr_omega_decision() - High-level interface
    • execute() - Core operation dispatcher
    • _validate_decision() - Logic validation
    • _symbolic_reason() - Reasoning chains
    • _verify_constraints() - Constraint checking
    • _explain_decision() - Explanation generation
```

### Status Flow

```
NOT_INSTALLED → INSTALLED → INITIALIZED → ACTIVE
                                ↓
                            FAILED (with retry/fallback)
```

## Ethical Compliance

### LO-01 Compliance
Symbolic reasoning provides formal logic validation, avoiding anthropomorphism through mathematical foundations.

### IR→IC (Contractivity)
Formal verification reduces uncertainty (ρ < 1) in critical decisions through symbolic proof.

### Fail-Closed
Invalid symbolic proofs block risky transitions. Configure with `fail_open=False` (default).

### Auditability
All reasoning chains logged to WORM ledger with full transparency.

## Performance

### Metrics Tracked
- Invocations count
- Success rate
- Average latency (ms)
- Cost (USD)
- Quality scores

### Expected Performance
- Validation latency: <50ms (placeholder mode)
- Reasoning depth: 1-10 steps configurable
- Constraint checking: O(n) where n = number of constraints

## Installation

### Basic Installation
```bash
pip install symbolicai
```

### PENIN-Ω Installation
```bash
pip install peninaocubo[symbolicai]
# or for all P2 integrations:
pip install peninaocubo[sota-p2]
```

## Roadmap

### Current (v0.9.0)
- ✅ Base adapter implementation
- ✅ Configuration system
- ✅ SR-Ω∞ validation interface
- ✅ Comprehensive test suite
- ✅ Demo and documentation

### Future (v1.0+)
- 🔄 Full SymbolicAI library integration
- 🔄 Formal theorem proving
- 🔄 Advanced constraint solvers
- 🔄 Distributed reasoning across instances
- 🔄 Learning from validation history

## Examples

See `examples/demo_symbolicai.py` for a complete working example demonstrating:
- Configuration setup
- Decision validation
- Constraint verification
- Explanation generation
- SR-Ω∞ integration pattern

## References

- **GitHub:** https://github.com/ExtensityAI/symbolicai
- **Paper:** Neurosymbolic AI research papers
- **PENIN-Ω Docs:** Main repository documentation

## License

Apache 2.0 (same as PENIN-Ω)

## Contributing

See main repository CONTRIBUTING.md for contribution guidelines.
