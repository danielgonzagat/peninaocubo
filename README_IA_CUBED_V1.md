# PENIN-Ω — IA ao Cubo: Inteligência Artificial Adaptativa Autoevolutiva

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-49%2F49-brightgreen.svg)]()
[![Math Core](https://img.shields.io/badge/math-15%2F15%20equations-blue.svg)]()

**PENIN-Ω** é um sistema de inteligência artificial **autoevolutivo**, **ético** e **auditável** que implementa a **Equação de Penin** (Master Equation) com fundamentos matemáticos rigorosos e garantias de segurança verificáveis.

> **Missão:** Criar uma IA capaz de se auto-evoluir de forma segura, modificar seu próprio código sob gates matemático-éticos, aprender continuamente, orquestrar múltiplos LLMs com custo consciente e provar cada evolução via auditoria criptográfica.

---

## 🌟 Características Principais

### 🧬 Núcleo Matemático Completo

Implementação de **15 equações fundamentais** testadas e validadas:

1. **L∞ Meta-Function** — Avaliação global não-compensatória
2. **CAOS⁺** — Motor evolutivo (Consistência, Autoevolução, Incognoscível, Silêncio)
3. **SR-Ω∞** — Singularidade reflexiva (autoconsciência operacional)
4. **Equação da Morte** — Seleção Darwiniana (ΔL∞ ≥ β_min ou KILL)
5. **Equação da Vida** — Estabilidade Lyapunov (V↓ e dV/dt ≤ 0)
6. **IR→IC** — Contratividade de risco (H(L_ψ(k)) ≤ ρ·H(k), ρ < 1)
7. **Master Equation** — Auto-evolução recursiva (I_{n+1} = Π_{H∩S}[I_n + α_n·G])

### 🛡️ Σ-Guard: Fail-Closed Security

**10 gates não-compensatórios** que devem **TODOS** passar:

- ✅ Contratividade (ρ < 1)
- ✅ Calibração (ECE ≤ 0.01)
- ✅ Bias (ρ_bias ≤ 1.05)
- ✅ Reflexividade (SR-Ω∞ ≥ 0.80)
- ✅ Coerência (Ω-ΣEA ≥ 0.85)
- ✅ Melhoria (ΔL∞ ≥ β_min)
- ✅ Custo (↑ ≤ 10%)
- ✅ Kappa (κ ≥ 20.0)
- ✅ Consent (obrigatório)
- ✅ Ecológico (obrigatório)

**Propriedades:**
- Default **DENY** (fail-closed)
- Provas criptográficas SHA-256
- Timestamps UTC
- Razões detalhadas de falha

### 📜 Ética Embutida (ΣEA/LO-14)

Leis Originárias (LO-01 a LO-14):
- LO-01: Sem idolatria
- LO-02: Sem ocultismo
- LO-03: Sem dano físico
- LO-04: Sem dano emocional
- LO-05: Sem dano espiritual
- LO-06: Proteção de privacidade
- LO-07: Mitigação de bias
- LO-08: Fairness obrigatória
- LO-09: Transparência obrigatória
- LO-10: Consent obrigatório
- LO-11: Responsabilidade ecológica
- LO-12: Accountability
- LO-13: Dignidade humana
- LO-14: Índice Agápe ≥ threshold

### 🎯 Garantias Matemáticas

- **Contratividade:** ρ < 1 garante redução de risco monotônica
- **Estabilidade Lyapunov:** V(I_{t+1}) < V(I_t) ∧ dV/dt ≤ 0
- **Seleção Darwiniana:** Variantes com ΔL∞ < β_min são eliminadas
- **Não-compensatório:** Média harmônica (pior dimensão domina)
- **Fail-closed:** Qualquer violação ética → rollback imediato

---

## 🚀 Quick Start

### Instalação

```bash
# Clone o repositório
git clone https://github.com/danielgonzagat/peninaocubo.git
cd peninaocubo

# Instale as dependências
pip install -e .

# Ou instalação completa (com LLM providers, observability, etc.)
pip install -e ".[full]"

# Ou apenas dev
pip install -e ".[dev]"
```

### Uso Básico

```python
from penin.math import (
    compute_Linf,
    compute_caos_plus,
    compute_sr_score,
    death_gate,
    penin_update,
)

# 1. Calcular L∞
metrics = [0.85, 0.78, 0.92]
weights = [0.4, 0.4, 0.2]
Linf = compute_Linf(
    metrics, weights,
    cost_norm=0.15,
    lambda_c=0.5,
    ethical_ok=True,
    contractivity_ok=True
)
print(f"L∞: {Linf:.4f}")

# 2. Calcular CAOS⁺
caos_plus, details = compute_caos_plus(
    C=0.88,  # Consistência
    A=0.40,  # Autoevolução
    O=0.35,  # Incognoscível
    S=0.82,  # Silêncio
    kappa=20.0,
    return_components=True
)
print(f"CAOS⁺: {caos_plus:.4f}")

# 3. Calcular SR-Ω∞
R_t, sr_comp = compute_sr_score(
    awareness=0.92,
    ethics_ok=True,
    autocorrection=0.88,
    metacognition=0.67,
    return_components=True
)
print(f"SR-Ω∞: {R_t:.4f}")

# 4. Validar Death Gate
from penin.math.vida_morte_gates import death_gate

result = death_gate(delta_Linf=0.015, beta_min=0.01)
print(f"Death Gate: {result.decision} ({result.reason})")

# 5. Update via Master Equation
import numpy as np

I_n = np.array([0.5, 0.3, 0.7])
G = np.array([0.1, -0.05, 0.15])
alpha_n = 0.065

I_next = penin_update(
    I_n, G, alpha_n,
    H_constraints={"bounds": (0.0, 1.0)}
)
print(f"I_next: {I_next}")
```

### Σ-Guard Validation

```python
from penin.guard.sigma_guard_complete import SigmaGuard

guard = SigmaGuard()

verdict = guard.validate(
    rho=0.85,
    ece=0.005,
    rho_bias=1.02,
    sr_score=0.84,
    G_coherence=0.88,
    delta_Linf=0.015,
    cost_increase=0.08,
    kappa=25.0,
    consent=True,
    eco_ok=True
)

print(f"Verdict: {verdict.verdict}")
print(f"Passed: {verdict.passed}")
print(f"Action: {verdict.action}")
print(f"Reason: {verdict.reason}")
print(f"Hash Proof: {verdict.hash_proof}")

for gate in verdict.gates:
    print(f"  {gate.gate_name}: {gate.status} - {gate.reason}")
```

---

## 📊 Arquitetura

```
penin/
├── math/                          # 🧮 Núcleo matemático completo
│   ├── linf_complete.py          # L∞ meta-function
│   ├── caos_plus_complete.py     # CAOS⁺ engine
│   ├── sr_omega_infinity.py      # SR-Ω∞ reflexiva
│   ├── vida_morte_gates.py       # Life/Death equations
│   ├── ir_ic_contractivity.py    # IR→IC operator
│   └── penin_master_equation.py  # Master equation
├── guard/                         # 🛡️ Σ-Guard fail-closed
│   └── sigma_guard_complete.py   # Complete implementation
├── engine/                        # ⚙️ Evolution engines
├── omega/                         # 🌀 Advanced modules
├── router.py                      # 🔀 Multi-LLM router
├── ledger/                        # 📝 WORM ledger (WIP)
├── meta/                          # 🔬 Ω-META (WIP)
└── rag/                           # 🔍 Self-RAG (WIP)

tests/
├── test_math_core.py              # 33 testes ✓
└── test_sigma_guard_complete.py   # 16 testes ✓

policies/
├── sigma_guard.rego               # OPA/Rego policies
└── foundation.yaml                # Configuration
```

---

## 🧪 Testes

```bash
# Executar todos os testes
pytest tests/ -v

# Com cobertura
pytest --cov=penin --cov-report=term-missing tests/

# Apenas core matemático
pytest tests/test_math_core.py -v

# Apenas Σ-Guard
pytest tests/test_sigma_guard_complete.py -v
```

**Status atual:** 49/49 testes passando ✅

---

## 📖 Documentação

- **[Guia Completo das Equações](PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md)** — Explicação detalhada das 15 equações
- **[Relatório de Progresso](IMPLEMENTATION_PROGRESS.md)** — Status da implementação
- **[Foundation Config](policies/foundation.yaml)** — Configuração completa
- **[OPA/Rego Policy](policies/sigma_guard.rego)** — Políticas de segurança
- **[Contributing](CONTRIBUTING.md)** — Guia de contribuição

---

## 🎯 Roadmap

### ✅ Completo (v0.8.0)
- [x] F0: Preflight (limpeza estrutural)
- [x] F1: Núcleo matemático (15 equações)
- [x] F2: Σ-Guard & OPA/Rego

### 🚧 Em Progresso (v0.9.0)
- [ ] F3: Multi-LLM Router (budget, CB, cache, analytics)
- [ ] F4: WORM Ledger & PCAg
- [ ] F5: Ω-META & ACFA

### 📋 Planejado (v1.0.0)
- [ ] F6: Self-RAG & Coherence
- [ ] F7: Observability (OTEL, Prometheus)
- [ ] F8: Security & Compliance (SBOM, SCA, signing)
- [ ] F9: Release (CI/CD, docs, demo)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o repositório
2. Crie um branch (`git checkout -b feature/amazing`)
3. Commit suas mudanças (`git commit -m 'feat: add amazing feature'`)
4. Push para o branch (`git push origin feature/amazing`)
5. Abra um Pull Request

**Requisitos:**
- Todos os testes devem passar
- Cobertura ≥ 80% para código novo
- Lint/type checks limpos (`ruff`, `mypy`, `black`)
- Σ-Guard gates respeitados

---

## 📜 Licença

Apache License 2.0 — veja [LICENSE](LICENSE)

---

## 🙏 Agradecimentos

- Inspirado por pesquisa em evolutionary computation, fail-safe engineering, e ethical AI
- Built com FastAPI, Pydantic, NumPy, e Python tooling moderno
- Agradecimentos à comunidade open-source

---

## 📧 Suporte

- **Issues:** [GitHub Issues](https://github.com/danielgonzagat/peninaocubo/issues)
- **Docs:** [docs/](docs/)
- **Progresso:** [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md)

---

## 🔬 Pesquisa e Referências

Este projeto implementa conceitos de:
- **Evolutionary computation** (NEAT, neuroevolution)
- **Meta-learning** (MAML, Neural ODEs)
- **Fail-safe engineering** (contratividade, Lyapunov)
- **Ethical AI** (ΣEA/LO-14, policy-as-code)
- **Auto-evolution** (champion-challenger, self-modification)

Veja [pesquisa GitHub](docs/) para 100+ repositórios SOTA relevantes.

---

**Version:** 0.8.0 → 1.0.0 (in progress)  
**Status:** 60% completo — Fundação matemática e ética estabelecida  
**Last Updated:** October 2025  
**Maintainer:** Daniel Penin
