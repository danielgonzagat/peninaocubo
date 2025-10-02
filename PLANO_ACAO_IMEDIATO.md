# 🎯 PLANO DE AÇÃO IMEDIATO — PENIN-Ω

**Data**: 2025-10-02  
**Objetivo**: Transformar PENIN-Ω de Alpha Técnico para v1.0 Production Beta  
**Prazo**: 2-3 semanas  
**Abordagem**: Pragmática, incremental, focada em VALUE

---

## 🚀 MISSÃO SIMPLIFICADA

**De**: Protótipo conceitual com 355 testes coletados (25+ validados)  
**Para**: Sistema estável com 90%+ testes passando + demos reais + ética operacional

---

## ✅ JÁ CONCLUÍDO NESTA SESSÃO

1. ✅ Fix crítico: `_clamp` import em `penin/omega/caos.py`
2. ✅ Instalação de dependências base (pydantic, pytest, hypothesis, numpy)
3. ✅ Validação de 25 testes core (CAOS⁺ + integrações SOTA P1)
4. ✅ Auditoria completa documentada (`AUDITORIA_PENIN_OMEGA_COMPLETA.md`)

---

## 📋 PRÓXIMOS PASSOS (Executáveis Hoje/Amanhã)

### **PASSO 1: Estabilizar Ambiente de Testes** (⏱️ 30 min)

```bash
#!/bin/bash
# Script: scripts/setup_dev_env.sh

set -e

echo "🔧 Installing all dependencies..."
pip install -e ".[dev,full]" --quiet

echo "📦 Installed packages:"
pip list | grep -E "(pytest|ruff|black|mypy|hypothesis|numpy|pydantic)"

echo "✅ Environment ready!"
```

**Executar**:
```bash
chmod +x scripts/setup_dev_env.sh
./scripts/setup_dev_env.sh
```

**Critério de Aceite**: Comando completa sem erros.

---

### **PASSO 2: Rodar Suite Completa de Testes** (⏱️ 15 min)

```bash
#!/bin/bash
# Script: scripts/run_all_tests.sh

set -e

echo "🧪 Running full test suite..."
pytest tests/ -v --tb=short --maxfail=10 > test_results_full.log 2>&1

echo "📊 Test Summary:"
tail -50 test_results_full.log

echo "💾 Full results saved to: test_results_full.log"
```

**Executar**:
```bash
chmod +x scripts/run_all_tests.sh
./scripts/run_all_tests.sh
```

**Critério de Aceite**: Identificar **todos** os testes que falham e por quê.

---

### **PASSO 3: Corrigir Erros de Importação Restantes** (⏱️ 1-2h)

**Com base em `test_results_full.log`**, criar PRs para:

1. **Imports faltantes**:
   ```python
   # Se faltam dependências opcionais, adicionar try/except
   try:
       import numpy as np
   except ImportError:
       np = None  # Fallback gracioso
   ```

2. **Módulos mal referenciados**:
   - Verificar todos os `from penin.X import Y`
   - Garantir que Y existe em X/__init__.py ou X.py

**Critério de Aceite**: `pytest tests/ --collect-only` sem erros.

---

### **PASSO 4: Criar Suite de Smoke Tests** (⏱️ 1h)

Criar `tests/test_smoke_critical.py`:

```python
"""
Smoke tests - Validação rápida de componentes críticos (< 5s total)
"""
import pytest

def test_import_core_modules():
    """Verifica que módulos essenciais importam sem erros."""
    from penin.core import caos
    from penin.math import linf
    from penin.engine import master_equation
    from penin.guard import sigma_guard_complete
    assert caos is not None
    assert linf is not None
    assert master_equation is not None
    assert sigma_guard_complete is not None

def test_caos_plus_basic():
    """Valida CAOS⁺ com inputs mínimos."""
    from penin.core.caos import compute_caos_plus
    result = compute_caos_plus(C=0.5, A=0.5, O=0.5, S=0.5, kappa=20.0)
    assert result > 0, "CAOS⁺ deve retornar valor positivo"
    assert result < 100, "CAOS⁺ não deve explodir"

def test_linf_basic():
    """Valida L∞ com inputs mínimos."""
    from penin.math.linf import linf_score
    metrics = {"acc": 0.8, "robust": 0.7}
    weights = {"acc": 2.0, "robust": 1.0}
    cost = 0.1
    result = linf_score(metrics, weights, cost)
    assert 0 <= result <= 1, "L∞ deve estar em [0,1]"

def test_cli_import():
    """Verifica que CLI pode ser importado."""
    from penin import cli
    assert cli is not None

@pytest.mark.asyncio
async def test_sr_service_import():
    """Verifica que SR-Ω∞ service pode ser importado."""
    from penin.sr import sr_service
    assert sr_service is not None
```

**Executar**:
```bash
pytest tests/test_smoke_critical.py -v
```

**Critério de Aceite**: Todos os smoke tests passam em < 5 segundos.

---

### **PASSO 5: Consolidar Documentação** (⏱️ 2-3h)

#### **5.1 Criar Índice Mestre**

Atualizar `docs/INDEX.md`:

```markdown
# 📚 PENIN-Ω Documentation Index

**Last Updated**: 2025-10-02  
**Version**: 0.9.0

---

## 🚀 Quick Start

- [README](../README.md) — Overview & Installation
- [60s Demo](../examples/demo_60s_complete.py) — Run in terminal
- [Setup Guide](SETUP.md) — Development environment

---

## 📖 Core Documentation

### Architecture & Design
- [Architecture](architecture.md) ⭐ **1100+ lines, comprehensive**
- [Equations Guide](guides/PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md) ⭐ **All 15 equations**
- [CAOS+ Guide](guides/CAOS_PLUS_GUIDE.md)

### Operations
- [Operations Guide](operations/README.md) — Deployment, monitoring, troubleshooting
- [Persistence](persistence.md) — State management
- [HA Deployment](operations/ha_deployment.md)

### Ethics & Security
- [Ethics](ethics.md) — ΣEA/LO-14, fail-closed gates
- [Security](security.md) — SBOM, SCA, threat model

### Integrations
- [SOTA Integrations](../penin/integrations/README.md) — NextPy, Metacognitive, SpikingJelly
- [LLM Providers](guides/llm_providers.md)

---

## 🔬 For Developers

- [Contributing](../CONTRIBUTING.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md)
- [Testing Guide](tests/README.md)

---

## 📦 Reports & History

- [Session Reports](reports/) — Transformation progress
- [Archived Docs](archive/) — Historical documentation (reference only)

---

## 🆘 Support

- [Issues](https://github.com/danielgonzagat/peninaocubo/issues)
- [Discussions](https://github.com/danielgonzagat/peninaocubo/discussions)
```

#### **5.2 Criar Operations Guide**

Criar `docs/operations/README.md`:

```markdown
# 🛠️ PENIN-Ω Operations Guide

## Deployment

### Local Development
\`\`\`bash
pip install -e ".[dev,full]"
pytest tests/test_smoke_critical.py  # Validate
python examples/demo_60s_complete.py  # Run demo
\`\`\`

### Docker Compose (Observability Stack)
\`\`\`bash
cd deploy/
docker-compose -f docker-compose.observability.yml up -d
\`\`\`

**Services**:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Loki: http://localhost:3100

## Monitoring

### Key Metrics

| Metric | Description | Threshold |
|--------|-------------|-----------|
| `penin_alpha` | Current α_t^Ω value | Monitor trend |
| `penin_delta_linf` | Change in L∞ | Must be > β_min |
| `penin_caos_plus` | CAOS+ amplification | > 1.0 |
| `penin_sr_score` | Self-reflection score | ≥ 0.80 |
| `penin_gate_fail_total` | Gate failures | Monitor spikes |

### Dashboards

Import `deploy/grafana/dashboards/penin_overview.json` in Grafana.

## Troubleshooting

### Common Issues

**Issue**: Tests fail with `ModuleNotFoundError`  
**Solution**: `pip install -e ".[dev,full]"`

**Issue**: OPA policies not found  
**Solution**: Check `policies/` directory exists, install OPA

**Issue**: Metrics not appearing in Prometheus  
**Solution**: Verify service is running on port 8010, check `/metrics` endpoint

## Runbooks

### Rollback Procedure

If a promotion causes issues:

1. Stop service: `pkill -f penin`
2. Restore from WORM ledger: `penin restore --hash <last_good_hash>`
3. Restart: `penin meta`
4. Verify: `curl http://localhost:8010/health`

### Emergency Shutdown

\`\`\`bash
# Graceful shutdown
penin shutdown --graceful

# Force kill (if hung)
pkill -9 -f penin
\`\`\`
```

#### **5.3 Arquivar Documentação Antiga**

```bash
#!/bin/bash
# Script: scripts/cleanup_docs.sh

echo "📁 Archiving old status reports..."

# Move todos os arquivos de status antigos
find docs/archive/sessions/2025-10-01/ -name "*STATUS*.md" -o -name "*RESUMO*.md" | while read f; do
  mkdir -p docs/archive/deprecated/sessions/2025-10-01/
  mv "$f" docs/archive/deprecated/sessions/2025-10-01/
done

echo "✅ Cleanup complete. Archived to docs/archive/deprecated/"
```

**Critério de Aceite**: Menos de 30 arquivos .md em `docs/` (excluindo archive).

---

### **PASSO 6: Implementar OPA/Rego Básico** (⏱️ 3-4h)

#### **6.1 Instalar OPA**

```bash
# Download OPA binary
wget https://openpolicyagent.org/downloads/latest/opa_linux_amd64 -O /usr/local/bin/opa
chmod +x /usr/local/bin/opa

# Verify
opa version
```

#### **6.2 Criar Política Básica**

Atualizar `policies/sigma_guard.rego`:

```rego
package penin.guard

# Default: deny all unless explicitly allowed
default allow = false

# Allow if all ethical gates pass
allow {
    ethical_gates_pass
    risk_contractivity_ok
    budget_ok
}

# Ethical gates
ethical_gates_pass {
    input.ethics.consent == true
    input.ethics.ece <= 0.01
    input.ethics.bias_rho <= 1.05
    input.ethics.no_harm == true
}

# Risk contractividade
risk_contractivity_ok {
    input.risk.contractivity_rho < 1.0
}

# Budget check
budget_ok {
    input.budget.used_pct < 0.95
}

# Reason for denial (for logging)
deny_reason = reason {
    not ethical_gates_pass
    reason := "Ethical gates failed"
}

deny_reason = reason {
    not risk_contractivity_ok
    reason := "Risk not contractive (ρ ≥ 1.0)"
}

deny_reason = reason {
    not budget_ok
    reason := "Budget exceeded 95%"
}
```

#### **6.3 Integrar OPA em Σ-Guard**

Atualizar `penin/guard/sigma_guard_complete.py`:

```python
import subprocess
import json
from typing import Dict, Any

def check_opa_policy(input_data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Checa política OPA/Rego.
    
    Returns:
        (allowed, reason)
    """
    input_json = json.dumps(input_data)
    
    try:
        result = subprocess.run(
            ["opa", "eval", "-d", "policies/", "-i", "-", "--format", "json", "data.penin.guard.allow"],
            input=input_json.encode(),
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False, "OPA evaluation failed"
        
        response = json.loads(result.stdout)
        allowed = response.get("result", [{}])[0].get("expressions", [{}])[0].get("value", False)
        
        if not allowed:
            # Get deny reason
            reason_result = subprocess.run(
                ["opa", "eval", "-d", "policies/", "-i", "-", "--format", "json", "data.penin.guard.deny_reason"],
                input=input_json.encode(),
                capture_output=True,
                text=True,
                timeout=5
            )
            reason_data = json.loads(reason_result.stdout)
            reason = reason_data.get("result", [{}])[0].get("expressions", [{}])[0].get("value", "Unknown reason")
        else:
            reason = "All gates passed"
        
        return allowed, reason
    
    except Exception as e:
        # Fail-closed: se OPA falha, bloqueia
        return False, f"OPA check failed: {str(e)}"
```

#### **6.4 Criar Teste de OPA**

Criar `tests/test_opa_integration.py`:

```python
import pytest
import json
from penin.guard.sigma_guard_complete import check_opa_policy

def test_opa_allows_valid_input():
    """OPA deve permitir input que passa em todos os gates."""
    input_data = {
        "ethics": {
            "consent": True,
            "ece": 0.005,
            "bias_rho": 1.02,
            "no_harm": True
        },
        "risk": {
            "contractivity_rho": 0.95
        },
        "budget": {
            "used_pct": 0.75
        }
    }
    
    allowed, reason = check_opa_policy(input_data)
    assert allowed, f"Deveria permitir, mas bloqueou: {reason}"
    assert reason == "All gates passed"

def test_opa_blocks_high_ece():
    """OPA deve bloquear se ECE > 0.01."""
    input_data = {
        "ethics": {
            "consent": True,
            "ece": 0.02,  # Muito alto!
            "bias_rho": 1.02,
            "no_harm": True
        },
        "risk": {
            "contractivity_rho": 0.95
        },
        "budget": {
            "used_pct": 0.75
        }
    }
    
    allowed, reason = check_opa_policy(input_data)
    assert not allowed, "Deveria bloquear ECE alto"
    assert "Ethical gates failed" in reason

def test_opa_blocks_non_contractive():
    """OPA deve bloquear se ρ ≥ 1.0."""
    input_data = {
        "ethics": {
            "consent": True,
            "ece": 0.005,
            "bias_rho": 1.02,
            "no_harm": True
        },
        "risk": {
            "contractivity_rho": 1.05  # Não contrativo!
        },
        "budget": {
            "used_pct": 0.75
        }
    }
    
    allowed, reason = check_opa_policy(input_data)
    assert not allowed, "Deveria bloquear risco não-contrativo"
    assert "Risk not contractive" in reason
```

**Executar**:
```bash
pytest tests/test_opa_integration.py -v
```

**Critério de Aceite**: Todos os 3 testes de OPA passam.

---

### **PASSO 7: Criar Demo Real (Não Simulada)** (⏱️ 2-3h)

Criar `examples/demo_real_evaluation.py`:

```python
"""
Demo Real: PENIN-Ω com Avaliação Objetiva
Usa função de Ackley para otimização matemática real.
"""
import numpy as np
from rich.console import Console
from rich.table import Table
from penin.core.caos import compute_caos_plus
from penin.math.linf import linf_score
from penin.sr.sr_service import compute_sr_score

console = Console()

def ackley_function(x: np.ndarray) -> float:
    """Função de Ackley (otimização benchmark)."""
    n = len(x)
    sum1 = np.sum(x ** 2)
    sum2 = np.sum(np.cos(2 * np.pi * x))
    return -20 * np.exp(-0.2 * np.sqrt(sum1 / n)) - np.exp(sum2 / n) + 20 + np.e

def evaluate_artifact(artifact: np.ndarray) -> dict:
    """Avalia artefato em ambiente real."""
    fitness = ackley_function(artifact)
    
    # Normalizar para [0,1] (menor é melhor)
    # Ackley mínimo global = 0 em x=(0,0,...,0)
    # Típico range: [0, 20]
    normalized_fitness = max(0, 1 - (fitness / 20.0))
    
    # Métricas derivadas
    consistency = normalized_fitness  # Proxy
    robustness = 1.0 - abs(np.std(artifact))  # Menos variância = mais robusto
    
    return {
        "fitness": normalized_fitness,
        "consistency": consistency,
        "robustness": robustness,
        "raw_ackley": fitness
    }

def main():
    console.print("[bold cyan]PENIN-Ω — Demo Real com Avaliação Objetiva[/bold cyan]\n")
    
    # Gerar artefato inicial (random)
    np.random.seed(42)
    current_artifact = np.random.uniform(-5, 5, size=5)
    
    console.print(f"[yellow]Artefato Inicial:[/yellow] {current_artifact}")
    
    # Evolução com 5 ciclos
    for cycle in range(1, 6):
        console.print(f"\n[bold green]═══ Ciclo {cycle}/5 ═══[/bold green]")
        
        # Avaliar artefato atual
        metrics = evaluate_artifact(current_artifact)
        console.print(f"  Fitness: {metrics['fitness']:.4f} (Ackley: {metrics['raw_ackley']:.4f})")
        
        # Computar CAOS⁺
        caos = compute_caos_plus(
            C=metrics['consistency'],
            A=metrics['fitness'],  # Autoevolução = fitness
            O=0.5,  # Incerteza média
            S=metrics['robustness'],
            kappa=20.0
        )
        
        # Computar L∞
        linf = linf_score(
            metrics={"fitness": metrics['fitness'], "robustness": metrics['robustness']},
            weights={"fitness": 2.0, "robustness": 1.0},
            cost=0.1
        )
        
        # Computar SR
        sr = compute_sr_score(
            awareness=metrics['consistency'],
            ethics_ok=True,
            autocorr=0.8,
            metacog=linf
        )
        
        console.print(f"  CAOS⁺: {caos:.4f}")
        console.print(f"  L∞: {linf:.4f}")
        console.print(f"  SR-Ω∞: {sr:.4f}")
        
        # Mutação proporcional a CAOS⁺
        mutation = np.random.normal(0, 0.1 * caos, size=5)
        new_artifact = current_artifact + mutation
        new_artifact = np.clip(new_artifact, -5, 5)  # Projeção segura
        
        # Avaliar novo artefato
        new_metrics = evaluate_artifact(new_artifact)
        delta_linf = new_metrics['fitness'] - metrics['fitness']
        
        # Decisão: promover ou rejeitar
        if delta_linf > 0.01:  # β_min
            decision = "[bold green]PROMOTED[/bold green]"
            current_artifact = new_artifact
        else:
            decision = "[bold red]REJECTED (rollback)[/bold red]"
        
        console.print(f"  ΔL∞: {delta_linf:+.4f}")
        console.print(f"  Decisão: {decision}")
    
    # Resultado final
    final_metrics = evaluate_artifact(current_artifact)
    console.print(f"\n[bold cyan]Resultado Final:[/bold cyan]")
    console.print(f"  Artefato: {current_artifact}")
    console.print(f"  Fitness Final: {final_metrics['fitness']:.4f}")
    console.print(f"  Ackley Final: {final_metrics['raw_ackley']:.4f} (ideal: 0.0)")

if __name__ == "__main__":
    main()
```

**Executar**:
```bash
python examples/demo_real_evaluation.py
```

**Critério de Aceite**: Demo roda sem erros e mostra evolução de fitness real (não simulada).

---

## 📅 CRONOGRAMA EXECUTIVO

| Dia | Ações | Horas | Entregas |
|-----|-------|-------|----------|
| **Dia 1** | Passos 1-3: Ambiente + Testes + Fixes | 4h | Ambiente estável, testes coletam |
| **Dia 2** | Passo 4-5: Smoke tests + Docs | 4h | Smoke tests, INDEX.md |
| **Dia 3** | Passo 6: OPA/Rego básico | 4h | Políticas OPA funcionais |
| **Dia 4** | Passo 7: Demo real | 3h | Demo com avaliação objetiva |
| **Dia 5** | Review + ajustes | 2h | PR para v0.9.5 |

**Total**: ~17h (2-3 dias de trabalho focado)

---

## ✅ CRITÉRIOS DE SUCESSO (v0.9.5)

1. ✅ **Testes**: 90%+ dos testes passam (320+/355)
2. ✅ **Smoke Tests**: Suite de 5-8 smoke tests em < 5s
3. ✅ **OPA/Rego**: Políticas éticas funcionais, 3+ testes passando
4. ✅ **Demo Real**: 1 demo com avaliação objetiva (Ackley ou similar)
5. ✅ **Docs**: INDEX.md + operations.md + cleanup de 80% dos status reports
6. ✅ **Linting**: ruff, black, mypy passam sem erros críticos

---

## 🚧 DEPOIS DE v0.9.5 (Roadmap v1.0)

- 🔴 **Segurança**: SBOM, SCA, artifact signing
- 🟡 **Observabilidade**: Grafana dashboards funcionais
- 🟡 **Router**: Budget tracker + circuit breaker validados
- 🟢 **Benchmarks**: Comparativos com baselines (random, greedy)
- 🟢 **SOTA P2**: goNEAT, Mammoth, SymbolicAI

---

## 💬 COMUNICAÇÃO

Criar PR com checklist:

```markdown
## Título PR: v0.9.5 — Estabilização e Demos Reais

### Checklist de Qualidade

- [ ] Todos os smoke tests passam (< 5s)
- [ ] 90%+ dos testes passam
- [ ] OPA/Rego políticas funcionais (3+ testes)
- [ ] Demo real executável (`examples/demo_real_evaluation.py`)
- [ ] Docs consolidadas (INDEX.md, operations.md)
- [ ] Linting limpo (ruff, black, mypy)

### Métricas

- **Testes Passando**: XXX/355 (YY%)
- **Cobertura**: XX%
- **Smoke Tests**: X/X (100%)
- **OPA Tests**: 3/3 (100%)

### Demos Funcionando

- `examples/demo_60s_complete.py` ✅
- `examples/demo_real_evaluation.py` ✅ NEW

### Impacto

Este PR transforma PENIN-Ω de Alpha para v0.9.5 Beta-Ready:
- Testes estáveis e confiáveis
- Ética operacional (OPA/Rego)
- Avaliação real (não simulada)
- Documentação consolidada

### Próximos Passos (v1.0)

- SBOM + SCA
- Observabilidade completa
- Router validado
- Benchmarks
```

---

**Assinatura Digital**:  
🤖 Background Agent  
📅 2025-10-02  
🎯 Missão: PENIN-Ω v0.9.0 → v1.0.0

---
