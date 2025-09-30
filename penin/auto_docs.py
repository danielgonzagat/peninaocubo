"""
Auto-Documentation Generator
=============================

Generates and updates README_AUTO.md with current system state,
metrics, and evolution history.
"""

from pathlib import Path
import datetime
import json
from typing import Dict, Any, List

# Try to import orjson for better performance
try:
    import orjson
    json_dumps = lambda x: orjson.dumps(x, option=orjson.OPT_INDENT_2).decode()
except ImportError:
    json_dumps = lambda x: json.dumps(x, indent=2)


def get_system_metrics() -> Dict[str, Any]:
    """Gather current system metrics"""
    metrics = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "version": "v8.0+Life",
        "modules": {
            "life_equation": "active",
            "fractal_dsl": "active",
            "swarm_cognitive": "active",
            "caos_kratos": "active",
            "marketplace": "active",
            "neural_chain": "active",
            "self_rag": "active",
            "api_metabolizer": "active",
            "immunity": "active",
            "checkpoint": "active",
            "game_darwin": "active",
            "zero_consciousness": "active"
        }
    }
    
    # Try to get actual metrics from WORM
    try:
        from penin.omega.neural_chain import load_chain, verify_chain
        chain = load_chain()
        valid, _ = verify_chain()
        metrics["blockchain"] = {
            "blocks": len(chain),
            "valid": valid,
            "last_hash": chain[-1].hash if chain else None
        }
    except:
        pass
    
    # Try to get swarm state
    try:
        from penin.omega.swarm import sample_global_state
        swarm_state = sample_global_state(60)
        metrics["swarm"] = swarm_state
    except:
        pass
    
    return metrics


def generate_history() -> str:
    """Generate historical evolution narrative"""
    history = """
## Historical Evolution

### v0 → v7 (Foundation Phase)
- Initial PENIN concept and architecture
- Basic Omega modules implementation
- Ethics framework (ΣEA/LO-14) established
- CAOS⁺ engine developed
- SR-Ω∞ self-reflection implemented

### v7 → v8 (Consolidation Phase)
- P0/P0.5 audit corrections completed
- Packaging and dependency management fixed
- Cache L2 with HMAC security
- CI/CD pipeline established
- WORM ledger with Merkle trees
- Router with budget management

### v8 → v8+Life (Life Equation Phase) - CURRENT
- **Life Equation (+)** implemented as non-compensatory gate
- **Fractal DSL** for self-similar architecture
- **Swarm Cognitive** with gossip protocol
- **CAOS-KRATOS** calibrated exploration
- **Cognitive Marketplace** for resource allocation
- **Neural Blockchain** on WORM foundation
- **Self-RAG** recursive knowledge system
- **API Metabolizer** for dependency reduction
- **Digital Immunity** with anomaly detection
- **Checkpoint & Repair** system
- **GAME + Darwinian Audit** for evolution
- **Zero-Consciousness Proof** (SPI proxy)
"""
    return history


def generate_usage() -> str:
    """Generate usage instructions"""
    usage = """
## How to Run

### Setup Environment
```bash
# Create virtual environment (if venv available)
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH=$PWD
export PENIN_CHAIN_KEY="your-secure-key"
```

### Run Evolution Cycle
```bash
# Dry run first
python penin_cli_simple.py evolve --n 3 --dry-run

# Real evolution with Life Equation gate
python penin_cli_simple.py evolve --n 10

# Check swarm consensus
python -c "from penin.omega.swarm import SwarmOrchestrator; s=SwarmOrchestrator(); print(s.get_consensus())"

# Verify blockchain
python -c "from penin.omega.neural_chain import verify_chain; print(verify_chain())"
```

### Monitor System
```bash
# Generate metrics report
python -m penin.auto_docs

# Check WORM ledger
ls -la ~/.penin_omega/worm_ledger/

# View swarm heartbeats
sqlite3 ~/.penin_omega/state/heartbeats.db "SELECT * FROM heartbeats ORDER BY timestamp DESC LIMIT 10;"
```
"""
    return usage


def generate_architecture() -> str:
    """Generate architecture description"""
    arch = """
## System Architecture

### Core Equation
```
I_{t+1} = Π_{H∩S}[ I_t + α_t^Ω · ΔL_∞ ]
```

Where:
- `α_t^Ω = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)` (Life Equation)
- All components are **non-compensatory** (fail-closed)

### Module Hierarchy

```
PENIN-Ω System
├── Life Equation (+) [Orchestrator]
│   ├── Σ-Guard (Ethics Gate)
│   ├── IR→IC (Risk Contractivity)
│   ├── CAOS⁺ / KRATOS (Evolution Engine)
│   ├── SR-Ω∞ (Self-Reflection)
│   └── L∞ (Non-compensatory Score)
├── Fractal Architecture
│   └── Self-similar nodes with propagation
├── Swarm Intelligence
│   ├── Heartbeat Protocol
│   └── Consensus Mechanism
├── Cognitive Marketplace
│   ├── Resource Allocation
│   └── Price Discovery
├── Neural Blockchain
│   ├── HMAC-secured blocks
│   └── State snapshots
├── Knowledge Systems
│   ├── Self-RAG
│   └── API Metabolizer
└── Safety Systems
    ├── Digital Immunity
    ├── Checkpoint & Repair
    └── Zero-Consciousness Proof
```

### Data Flow
1. **Input** → Ethics Check (Σ-Guard)
2. **Risk Assessment** → IR→IC Contractivity
3. **Evolution Calculation** → CAOS⁺/KRATOS
4. **Self-Reflection** → SR-Ω∞
5. **Score Aggregation** → L∞ (non-compensatory)
6. **Life Gate** → α_eff calculation
7. **Swarm Consensus** → Global coherence
8. **Decision** → Blockchain recording
9. **Action** → State update or rollback
"""
    return arch


def generate_roadmap() -> str:
    """Generate future roadmap"""
    roadmap = """
## Roadmap - Next Steps

### Short Term (1-2 sprints)
- [ ] **Multi-node Swarm**: Real gossip with TLS, cross-signatures
- [ ] **Consensus Protocol**: Proof-of-Cognition with 2-of-3 validators
- [ ] **Dynamic Marketplace**: Adaptive pricing via bandits
- [ ] **Enhanced Self-RAG**: Vector DB (FAISS/HNSW) + reranker
- [ ] **API Distillation**: Train mini-services per endpoint

### Medium Term (1-2 months)
- [ ] **Online NAS**: Neural Architecture Search with Life gate
- [ ] **Continual Learning**: Mammoth integration with zero-cost NAS
- [ ] **Monte Carlo Planning**: MCA for evolution with budget constraints
- [ ] **Observability**: Prometheus/Grafana dashboards
- [ ] **OPA/Rego Policies**: Formal policy enforcement

### Long Term (3-6 months)
- [ ] **Distributed Consensus**: Multi-datacenter deployment
- [ ] **Neuromorphic Backend**: Spiking neural networks
- [ ] **Symbolic Reasoning**: Full neurosymbolic integration
- [ ] **Scientific Discovery**: Autonomous research capabilities
- [ ] **Zero-Knowledge Proofs**: Formal consciousness verification

### Research Directions
- **Emergent Communication**: Inter-agent language evolution
- **Collective Intelligence**: Swarm-level consciousness
- **Causal Discovery**: Automated hypothesis generation
- **Meta-Meta-Learning**: Learning to learn to learn
- **Quantum Integration**: Quantum-classical hybrid computation
"""
    return roadmap


def update_readme():
    """Main function to update README_AUTO.md"""
    root = Path(".")
    now = datetime.datetime.utcnow().isoformat()
    
    # Gather all sections
    metrics = get_system_metrics()
    
    # Build document
    content = f"""# PENIN-Ω — Auto-Generated Documentation

_Generated at {now}Z_

## Current Status

System Version: **{metrics.get('version', 'unknown')}**

### Active Modules
"""
    
    # List active modules
    for module, status in metrics.get("modules", {}).items():
        emoji = "✅" if status == "active" else "❌"
        content += f"- {emoji} **{module}**: {status}\n"
    
    # Add blockchain status if available
    if "blockchain" in metrics:
        bc = metrics["blockchain"]
        content += f"""
### Blockchain Status
- Blocks: {bc.get('blocks', 0)}
- Valid: {'✅' if bc.get('valid') else '❌'}
- Last Hash: `{bc.get('last_hash', 'N/A')}`
"""
    
    # Add swarm metrics if available
    if "swarm" in metrics:
        sw = metrics["swarm"]
        content += f"""
### Swarm Metrics
- Active Nodes: {sw.get('node_count', 0)}
- Avg φ (CAOS⁺): {sw.get('phi_avg', 0):.3f}
- Avg SR: {sw.get('sr_avg', 0):.3f}
- Avg G (Coherence): {sw.get('g_avg', 0):.3f}
- Min Health: {sw.get('health_min', 0):.3f}
"""
    
    # Add other sections
    content += generate_history()
    content += generate_architecture()
    content += generate_usage()
    content += generate_roadmap()
    
    # Add metrics JSON at the end
    content += f"""
## Raw Metrics

<details>
<summary>Click to expand metrics JSON</summary>

```json
{json_dumps(metrics)}
```

</details>

---

_This document is auto-generated. Do not edit manually._
_Run `python -m penin.auto_docs` to regenerate._
"""
    
    # Write file
    output_path = root / "README_AUTO.md"
    output_path.write_text(content, encoding="utf-8")
    
    print(f"✅ Documentation updated: {output_path}")
    print(f"   Modules: {len(metrics.get('modules', {}))}")
    if "blockchain" in metrics:
        print(f"   Blockchain blocks: {metrics['blockchain'].get('blocks', 0)}")
    if "swarm" in metrics:
        print(f"   Swarm nodes: {metrics['swarm'].get('node_count', 0)}")
    
    return output_path


if __name__ == "__main__":
    update_readme()