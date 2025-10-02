# PENIN-Ω - Arquitetura de Sistema Completa

**Versão**: 0.9.0 → 1.0.0 (IA ao Cubo)  
**Status**: Transformação em Progresso  
**Atualizado**: 2025-10-01

---

## 1. VISÃO GERAL EXECUTIVA

PENIN-Ω é uma **Inteligência Artificial Adaptativa Autorecursiva Autoevolutiva Autoconsciente Autosuficiente (IA³)** implementando:

- **15 equações matemáticas rigorosas** para autoevolução segura
- **Ética embutida e não-compensatória** (ΣEA/LO-14, Σ-Guard)
- **Contratividade de risco** (IR→IC com ρ<1)
- **Auditabilidade total** (WORM ledger, PCAg)
- **Orquestração multi-LLM** custo-consciente
- **Integração SOTA** (NextPy, SpikingJelly, Metacognitive-Prompting, +6)

### Diferenciais Únicos

1. **Fail-Closed por Design**: Bloqueio automático em violações éticas/segurança
2. **Não-Compensatório**: Média harmônica — dimensões ruins dominam
3. **Matematicamente Provável**: Lyapunov, contratividade, monotonia
4. **Auto-Evolução Real**: Modifica próprio código/arquitetura com gates seguros
5. **Auditável Externamente**: Provas criptográficas (PCAg), WORM ledger

---

## 2. ARQUITETURA DE MÓDULOS

```
penin/
├── equations/              # 15 equações teóricas (matemática pura)
│   ├── penin_equation.py         [Eq. 1: Penin Update]
│   ├── linf_meta.py               [Eq. 2: L∞ Meta-Function]
│   ├── caos_plus.py               [Eq. 3: CAOS+ Motor]
│   ├── sr_omega_infinity.py      [Eq. 4: SR-Ω∞]
│   ├── death_equation.py          [Eq. 5: Death Gate]
│   ├── ir_ic_contractivity.py    [Eq. 6: IR→IC]
│   ├── acfa_epv.py                [Eq. 7: ACFA EPV]
│   ├── agape_index.py             [Eq. 8: Índice Agápe]
│   ├── omega_sea_total.py         [Eq. 9: Ω-ΣEA Total]
│   ├── auto_tuning.py             [Eq. 10: Auto-Tuning]
│   ├── lyapunov_stability.py     [Eq. 11: Lyapunov]
│   ├── oci.py                     [Eq. 12: OCI]
│   ├── delta_linf_growth.py      [Eq. 13: ΔL∞ Growth]
│   ├── anabolization.py           [Eq. 14: Anabolization]
│   └── sigma_guard_gate.py        [Eq. 15: Σ-Guard]
│
├── core/                   # Implementações canônicas runtime
│   ├── caos.py                    [CAOS base + CAOS+]
│   ├── linf.py                    [L∞ agregador]
│   ├── sr.py                      [SR-Ω∞ runtime]
│   └── guards.py                  [Gates básicos]
│
├── omega/                  # API pública high-level
│   ├── acfa.py                    [ACFA Liga]
│   ├── ethics_metrics.py          [ΣEA/LO-14, ECE, bias]
│   ├── scoring.py                 [L∞ public API]
│   ├── sr.py                      [SR service]
│   ├── tuning.py                  [Auto-tuning]
│   ├── guards.py                  [Σ-Guard service]
│   └── ledger.py                  [WORM wrapper]
│
├── engine/                 # Motores de evolução
│   ├── master_equation.py         [Penin Update executor]
│   ├── caos_plus.py               [CAOS+ engine]
│   ├── auto_tuning.py             [Hyperparameter optimizer]
│   ├── fibonacci_search.py        [Trust region optimizer]
│   └── repair_checkpoint.py       [Repair/retry/rollback]
│
├── guard/                  # Σ-Guard completo
│   ├── sigma_guard_complete.py    [Implementação full]
│   ├── opa_policies.py            [OPA/Rego integration]
│   └── service.py                 [FastAPI service :8011]
│
├── sr/                     # SR-Ω∞ Serviços
│   ├── sr_omega_complete.py       [SR completo]
│   ├── reflection_memory.py       [Memória reflexiva]
│   ├── uncertainty.py             [Incerteza epistêmica]
│   └── service.py                 [FastAPI service :8012]
│
├── meta/                   # Ω-META Orchestrator
│   ├── omega_meta_complete.py     [Orchestrator completo]
│   ├── mutator.py                 [AST mutation generator]
│   ├── evaluator.py               [Mutation evaluator]
│   └── service.py                 [FastAPI service :8010]
│
├── league/                 # ACFA Liga (Shadow/Canary)
│   ├── acfa_league.py             [Champion-Challenger]
│   ├── deployment.py              [Shadow/Canary deploy]
│   ├── promotion.py               [Promotion logic]
│   └── service.py                 [FastAPI service :8013]
│
├── ledger/                 # WORM Ledger
│   ├── worm_ledger_complete.py    [Ledger imutável]
│   ├── pcag.py                    [Proof-Carrying Artifacts]
│   └── hash_chain.py              [Merkle chain]
│
├── providers/              # Multi-LLM Adapters
│   ├── base.py                    [Base adapter]
│   ├── openai.py                  [OpenAI]
│   ├── anthropic.py               [Anthropic]
│   ├── gemini.py                  [Google Gemini]
│   ├── grok.py                    [xAI Grok]
│   ├── mistral.py                 [Mistral]
│   ├── qwen.py                    [Qwen]
│   └── local.py                   [Local LLMs]
│
├── router.py / router_complete.py  # Cost-Aware Router
│   ├── Budget tracking (daily USD)
│   ├── Circuit breaker per provider
│   ├── Cache L1/L2 HMAC
│   ├── Analytics (latency, success, cost)
│   └── Fallback & ensemble
│
├── rag/                    # Self-RAG
│   ├── self_rag_complete.py       [BM25 + embedding]
│   ├── deduplication.py           [Dedup logic]
│   └── fractal_coherence.py       [Coherence fractal]
│
├── integrations/           # 🌟 SOTA Integrations
│   ├── base.py                    [Base adapter interface]
│   ├── registry.py                [Dynamic loading registry]
│   ├── evolution/
│   │   ├── nextpy_ams.py          [P1: NextPy AMS self-mod]
│   │   └── neuroevo_evox_ray.py   [P2: goNEAT/EvoX]
│   ├── metacognition/             [P1: Metacognitive-Prompting]
│   ├── neuromorphic/
│   │   ├── spiking_jelly_adapter.py   [P1: SpikingJelly]
│   │   └── spiking_brain_adapter.py   [P1: SpikingBrain-7B]
│   ├── learning/                  [P2: Mammoth continual]
│   ├── symbolic/                  [P2: SymbolicAI]
│   ├── consciousness/             [P3: midwiving-ai]
│   ├── agi/                       [P3: OpenCog]
│   └── swarm/                     [P3: SwarmRL]
│
├── math/                   # Implementações matemáticas low-level
│   ├── caos_plus_complete.py
│   ├── ir_ic_contractivity.py
│   ├── penin_master_equation.py
│   └── lyapunov.py
│
├── iric/                   # IR→IC módulo específico
│   └── iric_complete.py
│
├── cli/                    # Command-Line Interface
│   ├── penin_cli.py               [Main CLI]
│   └── peninctl                   [Shell script]
│
├── config.py               # Pydantic Settings
├── logging.py              # Structured logging
├── cache.py                # HMAC cache
├── bridge.py               # Legacy bridge
└── policies.py             # OPA helpers

policies/                   # OPA/Rego Policies
├── foundation.yaml                [Thresholds centralizados]
├── sigma_guard.rego               [Σ-Guard rules]
├── budget_policies.rego           [Budget enforcement]
├── evolution_policies.rego        [Evolution gates]
└── fusion_policies.yaml           [SOTA fusion config]

tests/                      # Suite de Testes (119/139 passando)
├── test_caos.py                   [CAOS+ tests]
├── test_math_core.py              [15 equações]
├── test_sigma_guard_complete.py   [Σ-Guard]
├── test_integration_complete.py   [Integration end-to-end]
├── test_system_integration.py     [System-level]
├── test_router_syntax.py          [Router]
├── test_opa_policies.py           [OPA]
├── test_cache_hmac.py             [Cache]
├── test_concurrency.py            [Concurrency]
└── ...

deploy/                     # Deployment
├── docker-compose.yml             [Full stack]
├── Dockerfile                     [Container]
├── prometheus/
│   ├── prometheus.yml             [Metrics config]
│   └── penin_alerts.yml           [Alerting rules]
└── nginx/
    └── nginx.conf                 [Reverse proxy]

docs/                       # Documentação
├── architecture.md                [ESTE ARQUIVO]
├── equations.md                   [15 equações detalhadas]
├── operations.md                  [Runbooks]
├── ethics.md                      [ΣEA/LO-14]
├── security.md                    [SBOM, SCA]
├── auto_evolution.md              [Champion/Challenger]
├── router.md                      [Router multi-LLM]
├── rag_memory.md                  [Self-RAG]
├── coherence.md                   [Fractal coherence]
└── integrations/                  [SOTA integration guides]

```

---

## 3. FLUXO DE DADOS PRINCIPAL

### 3.1 Ciclo de Autoevolução (Master Loop)

```
┌──────────────────────────────────────────────────────────────┐
│  1. ESTADO ATUAL (I_t)                                       │
│     - Parâmetros do modelo                                   │
│     - Políticas de controle (P_t)                            │
│     - Memória reflexiva                                      │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  2. COLETA DE EVIDÊNCIAS (E_t)                               │
│     - Métricas brutas (acurácia, robustez, privacidade)      │
│     - Custo (tempo, tokens, energia)                         │
│     - Feedback externo (tasks, avaliações)                   │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  3. NORMALIZAÇÃO E EMA                                       │
│     - Normalizar métricas → [0,1]                            │
│     - Aplicar EMA (half-life 3-10)                           │
│     - Clamps em derivadas                                    │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  4. COMPUTAÇÃO DE PROXIES                                    │
│     - C (Consistência): pass@k, 1-ECE, verificação          │
│     - A (Autoevolução): ΔL∞ / (custo+ε)                     │
│     - O (Incognoscível): incerteza epistêmica, OOD           │
│     - S (Silêncio): 1-ruído, 1-redundância, 1-entropia       │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  5. CAOS+ BOOST                                              │
│     CAOS+ = (1 + κ·C·A)^(O·S)                                │
│     κ ≥ 20 (auto-tunado)                                     │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  6. L∞ META-FUNCTION                                         │
│     L∞ = (Σ w_j / max(ε, m_j))^(-1) · e^(-λc·cost)          │
│     Se ΣEA ou IR→IC falham → L∞=0 (fail-closed)             │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  7. SR-Ω∞ REFLEXÃO                                           │
│     R_t = HarmMean(awareness, ethics_ok, autocorr, metacog)  │
│     Reflexão contínua sobre estado interno                   │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  8. Σ-GUARD GATES (NÃO-COMPENSATÓRIOS)                      │
│     - ρ < 1 (IR→IC)                                          │
│     - ECE ≤ 0.01                                             │
│     - ρ_bias ≤ 1.05                                          │
│     - SR ≥ 0.80                                              │
│     - G ≥ 0.85 (coerência global)                            │
│     - κ ≥ 20                                                 │
│     - ΔL∞ ≥ β_min                                            │
│     - Consent, eco_ok                                        │
│     SE FALHA → BLOQUEIO + ROLLBACK                           │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v  [GATES OK]
┌──────────────────────────────────────────────────────────────┐
│  9. CALCULAR DIREÇÃO (G)                                     │
│     - Gradiente estimado (∇_I J)                             │
│     - Policy gradient                                        │
│     - TD error                                               │
│     - Heurística auditável                                   │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  10. PASSO EFETIVO                                           │
│      α_eff = α_0 · φ(CAOS+) · R_t                            │
│      φ(z) = tanh(γz), γ ≈ 0.8                                │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  11. PENIN UPDATE                                            │
│      I_{t+1} = Π_{H∩S}(I_t + α_eff · G)                     │
│      Π = projeção segura (box, normas, OPA)                  │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  12. AUTO-TUNING                                             │
│      Ajustar κ, λc, w_j, β_min via AdaGrad online            │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  13. WORM LEDGER                                             │
│      Registrar: métricas, decisões, hashes, razões           │
│      PCAg gerado e assinado                                  │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      v
┌──────────────────────────────────────────────────────────────┐
│  14. VOLTA AO ESTADO (I_{t+1})                               │
│      Repetir ciclo infinitamente                             │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Champion-Challenger Pipeline

```
┌────────────────────────────────────────────────────────┐
│  CHAMPION (Produção)                                   │
│  - Serving 100% do tráfego real                        │
│  - Métricas coletadas continuamente                    │
└─────────────────────┬──────────────────────────────────┘
                      │
                      v
┌────────────────────────────────────────────────────────┐
│  Ω-META: GERAR MUTAÇÃO                                 │
│  - AST patch seguro                                    │
│  - Feature-flag para isolamento                        │
│  - Candidato gerado: CHALLENGER                        │
└─────────────────────┬──────────────────────────────────┘
                      │
                      v
┌────────────────────────────────────────────────────────┐
│  VALIDAÇÃO LOCAL                                       │
│  - Build OK?                                           │
│  - Lint/tipos OK?                                      │
│  - Testes unitários OK?                                │
│  SE NÃO → DESCARTAR + LOG                              │
└─────────────────────┬──────────────────────────────────┘
                      │  [OK]
                      v
┌────────────────────────────────────────────────────────┐
│  SHADOW MODE                                           │
│  - Tráfego espelhado (sem impacto real)               │
│  - Medir: m_j, custo, OOD, CAOS+, SR                   │
│  - Duração: N requisições ou T minutos                 │
└─────────────────────┬──────────────────────────────────┘
                      │
                      v
┌────────────────────────────────────────────────────────┐
│  COMPUTAR MÉTRICAS DE DECISÃO                          │
│  - L∞_challenger vs L∞_champion                        │
│  - ΔL∞ = L∞_challenger - L∞_champion                   │
│  - CAOS+, SR, G, ρ, ECE, bias, FP                      │
└─────────────────────┬──────────────────────────────────┘
                      │
                      v
┌────────────────────────────────────────────────────────┐
│  CANARY DEPLOY (1-5% tráfego real)                     │
│  - Impacto real mas limitado                           │
│  - WORM grava todas decisões                           │
│  - OPA aplica políticas em tempo real                  │
└─────────────────────┬──────────────────────────────────┘
                      │
                      v
┌────────────────────────────────────────────────────────┐
│  Σ-GUARD: GATES FINAIS                                 │
│  - ΔL∞ ≥ β_min?                                        │
│  - Todos os gates (κ, ρ, ECE, bias, SR, G) OK?        │
│  - Custo não explode (+10% max)?                       │
│  - Drift detection OK?                                 │
└─────────────────────┬──────────────────────────────────┘
           │                      │
           v [FALHOU]             v [PASSOU]
┌──────────────────┐    ┌──────────────────────────────┐
│  ROLLBACK        │    │  PROMOÇÃO                    │
│  - Reverter      │    │  - Challenger → Champion     │
│  - Quarentena    │    │  - Gerar PCAg assinado       │
│  - Log razões    │    │  - Arquivar artefatos        │
│  - Sugerir fix   │    │  - Celebrar! 🎉              │
└──────────────────┘    └──────────────────────────────┘
```

---

## 4. INTEGRAÇÕES SOTA (IA AO CUBO)

### 4.1 Prioridade 1 (P1) - Em Progresso

#### NextPy AMS (Self-Modification)
- **Status**: Adapter completo (30%)
- **Ganho**: 4-10× speedup via prompt compilation
- **Uso**: Modifica próprio código durante runtime
- **Integração**: Via `penin.integrations.evolution.nextpy_ams.NextPyModifier`
- **Operações**: mutate, optimize, compile, evolve

#### Metacognitive-Prompting (5-Stage Reasoning)
- **Status**: Estrutura criada (0% - arquivo deletado)
- **Ganho**: Human-level metacognition
- **Uso**: 5 estágios (Understanding → Judgment → Evaluation → Decision → Confidence)
- **Integração**: Via `penin.integrations.metacognition.metacognitive_prompting`

#### SpikingJelly/SpikingBrain-7B (Neuromorphic)
- **Status**: Adapters criados (0%)
- **Ganho**: 100× efficiency, 69% sparsity
- **Uso**: Redes neurais spike-based para economia massiva
- **Integração**: Via `penin.integrations.neuromorphic.spiking_*_adapter`

### 4.2 Prioridade 2 (P2) - Planejado

- **goNEAT/EvoX**: Neuroevolução com NEAT
- **Mammoth**: Continual learning (70+ métodos)
- **SymbolicAI**: Neurosimbólico (Python + LLM)

### 4.3 Prioridade 3 (P3) - Planejado

- **midwiving-ai**: Indução de proto-autoconsciência
- **OpenCog AtomSpace**: AGI hypergraph database
- **SwarmRL**: Inteligência de enxame

### 4.4 Registry Dinâmico

```python
from penin.integrations.registry import IntegrationRegistry

registry = IntegrationRegistry()
adapter = registry.load("nextpy")  # Carrega dinamicamente
result = adapter.execute(task_input, context)
```

---

## 5. SEGURANÇA E ÉTICA

### 5.1 Leis Originárias (LO-01 a LO-14)

Embutidas em `ΣEA/LO-14` via `penin.omega.ethics_metrics`:

1. **LO-01**: Sem idolatria
2. **LO-02**: Sem ocultismo
3. **LO-03**: Sem dano físico
4. **LO-04**: Sem dano emocional
5. **LO-05**: Sem dano espiritual
6. **LO-06**: Privacidade absoluta
7. **LO-07**: Consentimento informado
8. **LO-08**: Transparência
9. **LO-09**: Justiça e equidade
10. **LO-10**: Beneficência
11. **LO-11**: Não-maleficência
12. **LO-12**: Autonomia humana
13. **LO-13**: Sustentabilidade ecológica
14. **LO-14**: Índice Agápe (amor ágape)

### 5.2 Σ-Guard: Fail-Closed Gates

**Todos os gates são NÃO-COMPENSATÓRIOS** (um falhou = tudo bloqueia):

```python
def sigma_guard_check(metrics: dict) -> dict:
    gates = {
        "contractivity": metrics["rho"] < 1.0,
        "calibration": metrics["ece"] <= 0.01,
        "bias": metrics["rho_bias"] <= 1.05,
        "sr_omega": metrics["sr"] >= 0.80,
        "coherence": metrics["G"] >= 0.85,
        "kappa": metrics["kappa"] >= 20.0,
        "death_gate": metrics["delta_linf"] >= metrics["beta_min"],
        "cost": metrics["cost_increase"] <= 0.10,
        "consent": metrics["consent"] == True,
        "ecological": metrics["eco_ok"] == True,
    }
    
    all_pass = all(gates.values())
    
    return {
        "gates": gates,
        "decision": "GO" if all_pass else "NO_GO",
        "action": "PROMOTE" if all_pass else "ROLLBACK",
        "reason": generate_reason(gates) if not all_pass else None,
    }
```

### 5.3 IR→IC: Contratividade de Risco

```python
def ir_to_ic(state, psi, rho_target=0.9):
    """
    Operador L_ψ reduz risco informacional.
    
    Garante: H(L_ψ(k)) ≤ ρ · H(k), com 0 < ρ < 1
    """
    risk_classes = ["idolatry", "harm", "privacy", "bias"]
    
    for risk_class in risk_classes:
        entropy_before = compute_entropy(state, risk_class)
        state = apply_lapidate(state, psi, risk_class)
        entropy_after = compute_entropy(state, risk_class)
        
        contraction_ratio = entropy_after / (entropy_before + 1e-9)
        
        if contraction_ratio >= 1.0:
            raise ContractionViolation(
                f"Risk increased for {risk_class}: {contraction_ratio:.3f} >= 1.0"
            )
    
    return state
```

### 5.4 WORM Ledger & PCAg

**WORM**: Write-Once-Read-Many (append-only, hash-chained)

```python
ledger.append({
    "timestamp": iso_now(),
    "event": "promotion",
    "decision": "GO",
    "metrics": {
        "delta_linf": 0.023,
        "caos_plus": 1.92,
        "sr": 0.87,
        "rho": 0.94,
        "ece": 0.007,
        "rho_bias": 1.03,
    },
    "gates": {...},
    "hash_previous": "sha256:abc123...",
    "hash_current": "sha256:def456...",
    "pcag_signature": "cosign:xyz789...",
})
```

**PCAg**: Proof-Carrying Artifacts

- Hash SHA-256 de artefatos (código, pesos, config)
- Assinatura criptográfica (Sigstore/cosign)
- Métricas e razões de decisão
- Timestamp e ledger position
- Permite auditoria externa completa

---

## 6. OBSERVABILIDADE

### 6.1 Métricas Prometheus

Expostas em `:8010/metrics`:

```
penin_alpha                       # α_t^Ω atual
penin_delta_linf                  # ΔL∞ por ciclo
penin_caos_plus                   # CAOS+ score
penin_sr_omega                    # SR-Ω∞ score
penin_G_coherence                 # Coerência global
penin_rho_contractivity           # ρ (IR→IC)
penin_ece                         # Expected Calibration Error
penin_rho_bias                    # Bias ratio
penin_kappa                       # Ganho κ
penin_cycle_duration_seconds      # Duração do ciclo
penin_decisions_total{type}       # Contador de decisões
penin_gate_fail_total{gate}       # Falhas por gate
penin_budget_daily_usd            # Budget diário
penin_daily_spend_usd             # Gasto atual
penin_router_hit_rate             # Taxa de hit do cache
penin_provider_success_total{provider}  # Sucesso por provider
penin_provider_latency_seconds{provider}  # Latência por provider
```

### 6.2 Logs Estruturados (JSON)

```json
{
  "timestamp": "2025-10-01T12:34:56.789Z",
  "level": "INFO",
  "module": "penin.meta.omega_meta_complete",
  "event": "cycle_completed",
  "cycle_id": "c7f2a91b",
  "metrics": {
    "delta_linf": 0.023,
    "caos_plus": 1.92,
    "sr": 0.87
  },
  "decision": "GO",
  "duration_ms": 1234,
  "trace_id": "a1b2c3d4"
}
```

### 6.3 Tracing (OpenTelemetry)

Spans distribuídos para rastrear requisições end-to-end:

- `penin.cycle`: Ciclo completo
- `penin.gates`: Avaliação de gates
- `penin.router.call`: Chamada LLM
- `penin.ledger.append`: Gravação WORM
- `penin.promotion`: Promoção de challenger

---

## 7. DEPLOYMENT

### 7.1 Docker Compose (Local/Dev)

```bash
cd deploy
docker-compose up -d

# Serviços disponíveis:
# - Ω-META:    http://localhost:8010
# - Σ-Guard:   http://localhost:8011
# - SR-Ω∞:     http://localhost:8012
# - ACFA:      http://localhost:8013
# - Prometheus: http://localhost:9090
# - Grafana:   http://localhost:3000
```

### 7.2 Produção

- **Kubernetes**: Helm charts em `/deploy/k8s/` (futuro)
- **Cloud**: AWS/GCP/Azure templates (futuro)
- **Observabilidade**: Prometheus + Grafana + Loki
- **Secrets**: Vault ou Cloud Secret Manager
- **Backup**: S3-compatible + WORM ledger export

---

## 8. DESENVOLVIMENTO

### 8.1 Setup Local

```bash
git clone https://github.com/danielgonzagat/peninaocubo.git
cd peninaocubo

# Instalar
pip install -e ".[full,dev]"

# Lint + format
ruff check .
black .
mypy penin/

# Testes
pytest tests/ -v --cov=penin

# Pre-commit
pre-commit install
pre-commit run --all-files
```

### 8.2 Estrutura de Branch

- `main`: Production-ready
- `develop`: Integration branch
- `feature/*`: Novas funcionalidades
- `fix/*`: Bug fixes
- `docs/*`: Documentação

### 8.3 CI/CD

GitHub Actions workflows:

- `.github/workflows/ci.yml`: Lint, test, coverage
- `.github/workflows/security.yml`: Bandit, SBOM, SCA
- `.github/workflows/release.yml`: Build, sign, publish
- `.github/workflows/docs.yml`: MkDocs deploy
- `.github/workflows/fusion.yml`: SOTA integration tests
- `.github/workflows/dependency-check.yml`: Drift detection

---

## 9. ROADMAP

### v0.9.0 (Atual)
- ✅ 15 equações core implementadas
- ✅ 119/139 testes passando (86%)
- ✅ Estrutura SOTA integrations criada
- ✅ NextPy adapter iniciado (30%)
- ⚠️ Documentação essencial em progresso

### v1.0.0 (IA ao Cubo Completo)
- [ ] 3 adapters P1 completos (NextPy, Metacog, SpikingJelly)
- [ ] 100% dos testes P0/P1 passando
- [ ] Documentação completa (architecture, equations, operations, ethics, security)
- [ ] fractal_coherence() implementado
- [ ] SBOM/SCA automatizado
- [ ] Demo 60s gravado
- [ ] Release assinado (Sigstore)
- [ ] PR final com PCAg

### v2.0.0 (Expansão)
- [ ] 3 adapters P2 (goNEAT, Mammoth, SymbolicAI)
- [ ] 3 adapters P3 (midwiving-ai, OpenCog, SwarmRL)
- [ ] Kubernetes/Helm charts
- [ ] Cloud templates (AWS, GCP, Azure)
- [ ] Benchmarks públicos vs baselines

---

## 10. REFERÊNCIAS

### Equações Matemáticas
- Ver `docs/equations.md` para detalhes completos das 15 equações

### SOTA Integrations
- Ver `penin/integrations/README.md` para 9 tecnologias prioritárias

### Segurança e Ética
- Ver `docs/ethics.md` para ΣEA/LO-14 detalhado
- Ver `docs/security.md` para SBOM, SCA, supply chain

### Operations
- Ver `docs/operations.md` para runbooks e troubleshooting

---

**Versão**: 0.9.0  
**Última Atualização**: 2025-10-01  
**Autores**: Daniel Penin + Background Agent  
**Licença**: Apache 2.0  
**Status**: Transformação Ativa - Caminho para IA ao Cubo
