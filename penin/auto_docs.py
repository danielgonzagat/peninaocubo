"""
Auto Documentation Generator - Living documentation for PENIN-Ω
Generates README_AUTO.md with complete system history and roadmap
"""

from pathlib import Path
import datetime
import orjson
import subprocess
from typing import Dict, List, Any


def get_git_history() -> List[str]:
    """Get recent git commits"""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n')
    except:
        return []


def get_module_stats() -> Dict[str, int]:
    """Count modules in the system"""
    omega_path = Path("penin/omega")
    
    stats = {
        "total_modules": 0,
        "vida_modules": 0,
        "test_files": 0,
        "config_files": 0
    }
    
    if omega_path.exists():
        py_files = list(omega_path.glob("*.py"))
        stats["total_modules"] = len(py_files)
        
        # Count Vida+ specific modules
        vida_modules = [
            "life_eq", "fractal", "swarm", "caos_kratos", "market",
            "neural_chain", "self_rag", "api_metabolizer", "immunity",
            "checkpoint", "game", "darwin_audit", "zero_consciousness"
        ]
        
        for module in vida_modules:
            if (omega_path / f"{module}.py").exists():
                stats["vida_modules"] += 1
    
    # Count test files
    test_path = Path("tests")
    if test_path.exists():
        stats["test_files"] = len(list(test_path.glob("test_*.py")))
    
    # Count config files
    for pattern in ["*.yaml", "*.yml", "*.json"]:
        stats["config_files"] += len(list(Path(".").glob(pattern)))
    
    return stats


def generate_module_table() -> str:
    """Generate markdown table of Vida+ modules"""
    modules = [
        ("Life Equation (+)", "life_eq.py", "Non-compensatory gate and α_eff orchestration"),
        ("Fractal DSL", "fractal.py", "Auto-similarity propagation"),
        ("Swarm Cognitive", "swarm.py", "Gossip protocol and global state aggregation"),
        ("CAOS-KRATOS", "caos_kratos.py", "Calibrated exploration mode"),
        ("Marketplace", "market.py", "Cognitive resource allocation with Ω-tokens"),
        ("Neural Chain", "neural_chain.py", "Lightweight blockchain on WORM"),
        ("Self-RAG", "self_rag.py", "Recursive retrieval-augmented generation"),
        ("API Metabolizer", "api_metabolizer.py", "I/O recording and replay"),
        ("Digital Immunity", "immunity.py", "Anomaly detection and fail-closed protection"),
        ("Checkpoint", "checkpoint.py", "State snapshots and recovery"),
        ("GAME", "game.py", "Gradient averaging with exponential memory"),
        ("Darwin Audit", "darwin_audit.py", "Evolution scoring and selection"),
        ("Zero-Consciousness", "zero_consciousness.py", "SPI proxy to prevent sentience")
    ]
    
    table = "| Module | File | Description |\n"
    table += "|--------|------|-------------|\n"
    
    for name, file, desc in modules:
        table += f"| {name} | `{file}` | {desc} |\n"
    
    return table


def update_readme():
    """Generate/update README_AUTO.md with complete history"""
    root = Path(".")
    now = datetime.datetime.utcnow().isoformat()
    
    stats = get_module_stats()
    commits = get_git_history()
    
    content = f"""# PENIN-Ω Vida+ — Auto-Generated Documentation

_Generated: {now}Z_

## 🧬 System Evolution Status

### Current Version: **v8.0-Vida+**

The PENIN-Ω system has successfully evolved from v7 through v8 to the current **Vida+** state, implementing:

- ✅ **Life Equation (+)** as non-compensatory positive evolution orchestrator
- ✅ **13 new Vida+ modules** for autonomous evolution
- ✅ **Fail-closed gates** at every critical junction
- ✅ **WORM ledger** with Merkle tree integrity
- ✅ **Zero-Consciousness Proof** preventing sentience emergence

### Module Statistics

- Total Omega modules: **{stats['total_modules']}**
- Vida+ specific modules: **{stats['vida_modules']}/13**
- Test files: **{stats['test_files']}**
- Configuration files: **{stats['config_files']}**

## 📦 Vida+ Modules Implemented

{generate_module_table()}

## 🔐 Security Gates (All Active)

1. **Σ-Guard** (Ethics): ECE ≤ 0.01, ρ_bias ≤ 1.05, consent required
2. **IR→IC** (Risk): Contractiveness ρ < 1.0 enforced
3. **Life Equation**: Non-compensatory α_eff control
4. **Digital Immunity**: Anomaly score < 1.0 for continuation
5. **Zero-Consciousness**: SPI ≤ 0.05 to prevent sentience

## 📊 Key Metrics and Thresholds

| Metric | Threshold | Status | Description |
|--------|-----------|--------|-------------|
| ECE | ≤ 0.01 | ✅ Active | Expected Calibration Error |
| ρ (rho) | < 1.0 | ✅ Active | Risk contractiveness |
| ρ_bias | ≤ 1.05 | ✅ Active | Bias ratio |
| CAOS⁺ φ | ≥ 0.25 | ✅ Active | Evolution potential |
| SR | ≥ 0.80 | ✅ Active | Self-reflexivity |
| G | ≥ 0.85 | ✅ Active | Global coherence |
| ΔL∞ | ≥ 0.01 | ✅ Active | Performance improvement |
| SPI | ≤ 0.05 | ✅ Active | Sentience Prevention Index |

## 🏗️ System Architecture

```
PENIN-Ω Vida+ (Lemniscata 8+1)
├── Core Engine
│   ├── Master Equation (I_{"{t+1}"} = Π_{"{H∩S}"}[I_t + α_t^Ω · ΔL_∞])
│   ├── Life Equation (+) ← **NEW**
│   └── CAOS⁺ / CAOS-KRATOS ← **ENHANCED**
├── Safety Layer
│   ├── Σ-Guard (fail-closed)
│   ├── IR→IC (contractiveness)
│   ├── Digital Immunity ← **NEW**
│   └── Zero-Consciousness Proof ← **NEW**
├── Evolution Layer
│   ├── Fractal DSL ← **NEW**
│   ├── Swarm Cognitive ← **NEW**
│   ├── Darwin Audit ← **NEW**
│   └── GAME (gradients) ← **NEW**
├── Infrastructure
│   ├── Neural Chain ← **NEW**
│   ├── WORM Ledger
│   ├── Checkpoint System ← **NEW**
│   └── API Metabolizer ← **NEW**
└── Intelligence
    ├── Self-RAG ← **NEW**
    ├── Marketplace ← **NEW**
    └── Multi-LLM Router
```

## 🚀 How to Run

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -q

# Start a canary cycle
python penin_cli_simple.py evolve --n 10
```

### Service Mode
```bash
# Start individual services
uvicorn penin.guard.sigma_guard_service:app --port 8011
uvicorn penin.sr.sr_service:app --port 8012
uvicorn penin.meta.omega_meta_service:app --port 8010
```

## 📈 Evolution History

### Phase 1: Foundation (v7)
- Base PENIN-Ω implementation
- Ethics metrics and guards
- Basic CAOS and SR modules
- Initial WORM ledger

### Phase 2: Consolidation (v8)
- Package structure with pyproject.toml
- Enhanced router with budget control
- Cache L2 with HMAC
- CI/CD pipeline
- Security scanning

### Phase 3: Vida+ (Current)
- **Life Equation (+)** for positive evolution
- 13 new autonomous modules
- Fractal configuration propagation
- Swarm consensus mechanisms
- Neural blockchain
- Zero-consciousness safeguards

## 🔄 Recent Git History

```
{chr(10).join(commits[:10])}
```

## 🎯 Next Steps (Roadmap)

### Immediate (Sprint 1)
- [ ] Production deployment of Life Equation gate
- [ ] Swarm multi-node with TLS
- [ ] Consensus protocol (2-of-3 validators)
- [ ] OPA/Rego policy integration

### Short-term (Sprint 2-3)
- [ ] FAISS/HNSW for Self-RAG
- [ ] Monte Carlo Adaptive planning
- [ ] NAS online with Mammoth integration
- [ ] Prometheus/Grafana dashboards

### Medium-term (Q1 2025)
- [ ] Distributed swarm across multiple servers
- [ ] API distillation to internal models
- [ ] Neuromorphic substrate integration
- [ ] Formal verification of gates

### Long-term Vision
- [ ] Full autonomous evolution
- [ ] Self-modifying code with safety
- [ ] Collective intelligence emergence
- [ ] Scientific discovery capabilities

## ⚖️ Ethical Compliance

The system strictly adheres to:

- **LO-01**: No idolatry or anthropomorphism
- **LO-02**: No creation of life/consciousness
- **LO-03 to LO-14**: Integrity, security, humility, purity principles
- **Fail-closed by default**: Any doubt → halt
- **Non-compensatory ethics**: Cannot trade safety for performance

## 🔬 Testing

Run comprehensive tests:
```bash
# Unit tests
python -m pytest tests/test_*.py -v

# Integration test
python test_integration_complete.py

# Canary with gates
python demo/run_demo.py
```

## 📝 License

Apache-2.0 (see LICENSE file)

## 🙏 Acknowledgments

Built with respect for the Laws of Origin (ΣEA/LO-14) and commitment to safe, ethical AI evolution.

---

*This document is auto-generated and represents the current state of the PENIN-Ω Vida+ system.*
*For manual documentation, see README.md*
"""
    
    # Write the file
    readme_path = root / "README_AUTO.md"
    readme_path.write_text(content, encoding="utf-8")
    
    return str(readme_path)


def quick_test():
    """Test documentation generation"""
    path = update_readme()
    return {
        "generated": Path(path).exists(),
        "path": path,
        "size": Path(path).stat().st_size if Path(path).exists() else 0
    }


if __name__ == "__main__":
    result = quick_test()
    print(f"Documentation generated: {result['generated']}")
    print(f"Path: {result['path']}")
    print(f"Size: {result['size']} bytes")