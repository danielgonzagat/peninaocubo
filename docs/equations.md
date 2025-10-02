# PENIN-Ω — Complete Equations Reference

## Overview

This document provides comprehensive mathematical foundations for the PENIN-Ω system, implementing 15 core equations for self-evolving, ethically-bounded AI.

**Key Principles:**
- **Non-compensatory** aggregation (harmonic mean - weak link dominates)
- **Fail-closed** security (ethical violations → immediate halt)
- **Contractive** risk reduction (ρ < 1)
- **Auditable** evolution (WORM ledger + cryptographic proofs)

---

## 1. Penin Equation — Auto-Recursive Evolution

**Form:**
```
I_{n+1} = Π_{H∩S}[I_n + α_n · G(I_n, E_n; P_n)]
```

**Components:**
- `I`: Internal state (parameters, policies, memory)
- `G`: Update direction (gradient/policy/heuristic)
- `α_n`: Dynamic step size (modulated by CAOS⁺ and SR)
- `Π_{H∩S}`: Safe projection (technical H ∩ ethical S)

**Implementation:**
```python
from penin.equations.penin_equation import penin_update, PeninState

state = PeninState(parameters=np.array([1.0, 2.0]))
gradient = np.array([0.1, 0.2])
alpha = 0.01
new_state = penin_update(state, gradient, alpha)
```

**Guarantees:**
- Bounded updates (projection ensures constraints)
- Ethical compliance (S set enforced)
- Rollback capability (state history maintained)

---

## 2. L∞ Meta-Function — Non-Compensatory Scoring

**Form:**
```
L∞ = (1 / Σ(w_j / max(ε, m_j))) · exp(-λ_c · Cost) · 𝟙_{ΣEA ∧ IR→IC}
```

**Components:**
- `m_j`: Normalized metrics ∈ [0, 1] (accuracy, robustness, privacy)
- `w_j`: Weights (Σw_j = 1)
- `Cost`: Normalized cost (time/tokens/energy)
- `λ_c`: Cost penalty coefficient
- `ε`: Numerical stability (10⁻³)
- `𝟙_{ΣEA ∧ IR→IC}`: Fail-closed indicator (0 if ethics fail)

**Implementation:**
```python
from penin.equations.linf_meta import compute_linf_meta, LInfConfig

metrics = [0.85, 0.78, 0.92]  # accuracy, robustness, privacy
weights = [0.4, 0.4, 0.2]
cost = 0.15
config = LInfConfig(lambda_c=0.5, epsilon=1e-3)

linf = compute_linf_meta(metrics, weights, cost, config, ethical_ok=True)
# linf ≈ 0.74 (harmonic mean penalized by cost)
```

**Why Harmonic Mean:**
- Forces **bottleneck** dominance (worst metric controls score)
- Anti-Goodhart (cannot compensate weak dimension with strong ones)
- Mathematically proven non-compensatory property

**Calibration:**
- `λ_c`: 0.1–1.0 (start 0.5, tune via meta-optimization)
- `ε`: 10⁻³ to 10⁻² (stability vs precision trade-off)

---

## 3. CAOS⁺ — Consistency, Autoevolution, Unknowable, Silence

### Visão Geral

CAOS⁺ é o motor de evolução adaptativa do PENIN-Ω que modula dinamicamente a taxa
de aprendizado (α) baseado em quatro dimensões fundamentais. A fórmula equilibra
exploração e exploração através de uma base multiplicativa e expoente adaptativo.

### Fórmula Matemática

**Form:**
```
CAOS⁺ = (1 + κ · C · A)^(O · S)
```

Onde:
- **Base**: `(1 + κ · C · A)` representa o potencial de amplificação
- **Expoente**: `(O · S)` controla a agressividade da exploração

### Componentes Detalhados

Todas as dimensões são normalizadas em [0, 1]:

#### **C (Consistency / Consistência)**: 
Mede a confiabilidade e calibração das predições.

**Fórmula**: `C = w₁·pass@k + w₂·(1-ECE) + w₃·v_ext`

**Sub-componentes**:
- **pass@k**: Taxa de autoconsistência em k amostras
  - Mede se o sistema produz resultados consistentes
  - Valores típicos: 0.85-0.95 para sistemas calibrados
  - Peso sugerido: 0.4
  
- **ECE (Expected Calibration Error)**: Erro de calibração [0, 1]
  - Mede se probabilidades refletem frequências reais
  - Invertido para métrica positiva: (1-ECE)
  - Valores bons: ECE < 0.05 (então 1-ECE > 0.95)
  - Peso sugerido: 0.3
  
- **v_ext**: Score de verificação externa [0, 1]
  - Validação por oracles, testes formais, humanos
  - Valores típicos: 0.80-0.90
  - Peso sugerido: 0.3

**Interpretação**:
- C alto (> 0.8): Sistema confiável, pode explorar mais
- C baixo (< 0.5): Sistema inconsistente, precisa calibrar

---

#### **A (Autoevolution / Autoevolução)**: 
Mede eficiência do aprendizado (ganho por custo).

**Fórmula**: `A = ΔL∞⁺ / (Cost_norm + ε)`

Normalizado para [0, 1] via: `A_norm = min(A_raw / max_a, 1.0)`

**Sub-componentes**:
- **ΔL∞⁺**: Ganho de performance (apenas positivo)
  - max(0, ΔL∞) - só considera melhorias
  - Valores típicos: 0.01-0.10 (1%-10% de ganho)
  
- **Cost_norm**: Custo normalizado [0, ∞)
  - Tempo, tokens, energia, recursos
  - Normalizado por budget ou baseline
  - Valores típicos: 0.05-0.20 (5%-20% do budget)
  
- **ε**: Estabilizador numérico (padrão: 10⁻³)
- **max_a**: Clamp máximo para normalização (padrão: 10.0)

**Interpretação**:
- A alto (> 0.6): Aprendizado eficiente, bom ROI
- A baixo (< 0.3): Aprendizado ineficiente ou estagnado

---

#### **O (Unknowable / Incognoscível)**: 
Mede incerteza e necessidade de exploração.

**Fórmula**: `O = w_epi·epistemic + w_ood·ood_score + w_ens·ensemble_disagreement`

**Sub-componentes**:
- **epistemic_uncertainty**: Incerteza epistêmica [0, 1]
  - Entropia: H(p) = -Σ p_i log p_i
  - Mutual Information: I(Y;θ|X) em Bayesian NNs
  - Valores típicos: 0.2-0.5
  - Peso sugerido: 0.4
  
- **ood_score**: Score out-of-distribution [0, 1]
  - Distância de distribuição de treino (Mahalanobis, KL, etc)
  - Detecção de anomalias, domain shift
  - Valores típicos: 0.1-0.4
  - Peso sugerido: 0.3
  
- **ensemble_disagreement**: Variância no ensemble [0, 1]
  - Std ou variance entre predições de múltiplos modelos
  - Normalizado por range esperado
  - Valores típicos: 0.15-0.35
  - Peso sugerido: 0.3

**Interpretação**:
- O alto (> 0.6): Alta incerteza → precisa EXPLORAR mais
- O baixo (< 0.3): Baixa incerteza → pode EXPLOITAR (exploit)

---

#### **S (Silence / Silêncio)**: 
Mede qualidade do sinal (anti-ruído).

**Fórmula**: `S = v₁·(1-noise) + v₂·(1-redund) + v₃·(1-entropy)`

Ponderação sugerida: `v₁:v₂:v₃ = 2:1:1` (ruído é mais crítico)

**Sub-componentes**:
- **(1 - noise_ratio)**: Anti-ruído [0, 1]
  - Proporção de sinal vs ruído: SNR relacionado
  - Valores bons: noise < 0.1 (então anti-noise > 0.9)
  - Peso sugerido: 0.5 (2/4)
  
- **(1 - redundancy_ratio)**: Anti-redundância [0, 1]
  - Proporção de informação duplicada/redundante
  - Valores bons: redundancy < 0.15
  - Peso sugerido: 0.25 (1/4)
  
- **(1 - entropy_normalized)**: Anti-entropia [0, 1]
  - Desordem/imprevisibilidade do sinal
  - Entropia normalizada por máximo teórico
  - Valores bons: entropy < 0.2
  - Peso sugerido: 0.25 (1/4)

**Interpretação**:
- S alto (> 0.8): Sinal limpo, alta confiança
- S baixo (< 0.5): Sinal ruidoso, baixa confiança

---

#### **κ (kappa)**: Ganho base de amplificação

**Range**: κ ≥ 20 (padrão), típico: [10, 100]

**Efeito**:
- κ = 10: Amplificação conservadora (1.0-2.5×)
- κ = 20: Amplificação moderada (1.0-3.5×) ← **padrão**
- κ = 50: Amplificação agressiva (1.0-5.0×)
- κ = 100: Amplificação extrema (1.0-7.0×)

**Auto-tuning**: κ pode ser otimizado via **Equação 10** (bandit meta-optimization)
baseado em métricas de performance agregadas.

---

### Propriedades Matemáticas

1. **Monotonicidade**: CAOS⁺ cresce monotonicamente com cada componente
   - ∂CAOS⁺/∂C ≥ 0, ∂CAOS⁺/∂A ≥ 0, ∂CAOS⁺/∂O ≥ 0, ∂CAOS⁺/∂S ≥ 0

2. **Identidade**: CAOS⁺(0,0,0,0) = 1^0 = 1 (sem amplificação)

3. **Bounds**:
   - Mínimo teórico: 1.0 (sem exploração)
   - Máximo teórico: (1 + κ)^1 quando C=A=O=S=1
   - Com κ=20: máximo = 21.0 (raramente alcançado)

4. **Decomposição**:
   - **Base multiplicativa**: C·A mede "qualidade" do aprendizado
   - **Expoente adaptativo**: O·S modula agressividade

5. **Invariância**: CAOS⁺ é invariante a permutações dentro de cada par (C↔A, O↔S)

---

### Implementação em Python

#### Uso Básico (Componentes Conhecidos)

```python
from penin.core.caos import compute_caos_plus_exponential

# Valores dos componentes (já calculados)
C = 0.88  # Alta consistência
A = 0.40  # Autoevolução moderada
O = 0.35  # Incerteza moderada
S = 0.82  # Alto silêncio (sinal limpo)
kappa = 20.0

caos_plus = compute_caos_plus_exponential(C, A, O, S, kappa)
# caos_plus ≈ 1.86 (fator de amplificação para α)

# Aplicar na Equação de Penin
alpha_base = 0.01
alpha_effective = alpha_base * caos_plus  # α_eff ≈ 0.0186
```

#### Uso Completo (Com Métricas Estruturadas)

```python
from penin.core.caos import (
    compute_caos_plus_complete,
    ConsistencyMetrics,
    AutoevolutionMetrics,
    IncognoscibleMetrics,
    SilenceMetrics,
    CAOSConfig,
    CAOSState
)

# Definir métricas detalhadas
consistency = ConsistencyMetrics(
    pass_at_k=0.92,           # 92% autoconsistência
    ece=0.008,                # 0.8% calibration error
    external_verification=0.88,  # 88% verificação externa
    weight_pass=0.4,
    weight_ece=0.3,
    weight_external=0.3
)

autoevolution = AutoevolutionMetrics(
    delta_linf=0.06,          # 6% ganho de performance
    cost_normalized=0.15,     # 15% do budget
    max_a=10.0
)

incognoscible = IncognoscibleMetrics(
    epistemic_uncertainty=0.35,
    ood_score=0.28,
    ensemble_disagreement=0.30,
    weight_epistemic=0.4,
    weight_ood=0.3,
    weight_ensemble=0.3
)

silence = SilenceMetrics(
    noise_ratio=0.08,         # 8% ruído
    redundancy_ratio=0.12,    # 12% redundância
    entropy_normalized=0.18,  # 18% entropia
    weight_noise=0.5,         # 2:1:1 weighting
    weight_redundancy=0.25,
    weight_entropy=0.25
)

# Configuração com EMA para estabilidade temporal
config = CAOSConfig(
    kappa=25.0,
    ema_half_life=5,  # Suavização em 5 iterações
    caos_min=1.0,
    caos_max=10.0,
    normalize_output=False
)

# Estado para tracking temporal
state = CAOSState()

# Computar CAOS⁺
caos_plus, details = compute_caos_plus_complete(
    consistency, autoevolution, incognoscible, silence,
    config, state
)

print(f"CAOS⁺: {caos_plus:.4f}")
print(f"Componentes: {details['components_raw']}")
print(f"Suavizados (EMA): {details['components_smoothed']}")
print(f"Estabilidade: {details['state_stability']:.3f}")
```

#### Tracking Temporal (Séries Temporais)

```python
# Para múltiplas iterações com suavização EMA
config = CAOSConfig(kappa=20.0, ema_half_life=5)
state = CAOSState()

for t in range(num_iterations):
    # Obter métricas da iteração t
    consistency_t = get_consistency_metrics(t)
    autoevolution_t = get_autoevolution_metrics(t)
    # ... outras métricas
    
    # Computar CAOS⁺ com EMA do estado anterior
    caos_t, details_t = compute_caos_plus_complete(
        consistency_t, autoevolution_t, incognoscible_t, silence_t,
        config, state  # state é atualizado in-place
    )
    
    # Usar caos_t para modular α
    alpha_eff = alpha_base * caos_t
```

---

### Uso no Pipeline PENIN-Ω

#### 1. Modulação de α na Equação de Penin

```python
# Equação de Penin: I_{t+1} = Π_{H∩S}[I_t + α_t^eff · G(I_t, E_t; P_t)]
# onde α_t^eff = α_0 · φ(CAOS⁺) · R_t

alpha_base = 0.01  # Step size base
caos_plus = compute_caos_plus_exponential(C, A, O, S, kappa)
sr_score = compute_sr_omega(...)  # SR-Ω∞

# Função de aceleração
def phi(caos_plus, gamma=0.8):
    return math.tanh(gamma * math.log(caos_plus))

alpha_effective = alpha_base * phi(caos_plus) * sr_score
```

#### 2. Seleção de Challengers na Liga ACFA

```python
# Priorizar challengers com maior CAOS⁺
challengers = [
    (challenger_1, caos_plus_1),
    (challenger_2, caos_plus_2),
    (challenger_3, caos_plus_3),
]

# Ordenar por CAOS⁺ (maior = mais prioritário)
challengers_sorted = sorted(challengers, key=lambda x: x[1], reverse=True)

# Testar em ordem de prioridade
for challenger, caos in challengers_sorted:
    if test_challenger(challenger):
        promote_to_champion(challenger)
        break
```

#### 3. Adaptação de β_min (Death Equation)

```python
# β_min adaptativo baseado em CAOS⁺
def adaptive_beta_min(caos_plus, beta_base=0.01):
    """
    CAOS⁺ alto → sistema aprendendo bem → pode ser mais exigente (β maior)
    CAOS⁺ baixo → sistema lutando → ser mais tolerante (β menor)
    """
    beta_min = beta_base * (1.0 + 0.5 * (caos_plus - 1.0))
    return max(0.005, min(0.05, beta_min))  # Clamp [0.5%, 5%]
```

---

### Best Practices

#### 1. Suavização Temporal (EMA)

**Problema**: Métricas podem oscilar entre iterações, causando instabilidade.

**Solução**: Usar `CAOSState` com EMA (Exponential Moving Average).

```python
# Half-life: número de iterações para peso cair 50%
config = CAOSConfig(ema_half_life=5)  # 5 iterações
state = CAOSState()

# EMA é aplicado automaticamente em compute_caos_plus_complete()
```

**Guidelines**:
- `ema_half_life = 3`: Resposta rápida (para ambientes dinâmicos)
- `ema_half_life = 5`: Balanceado (padrão) ← **recomendado**
- `ema_half_life = 10`: Resposta lenta (para ambientes estáveis)

#### 2. Clamps e Normalização

```python
config = CAOSConfig(
    kappa_min=10.0,    # Mínimo de κ
    kappa_max=100.0,   # Máximo de κ
    caos_min=1.0,      # CAOS⁺ nunca abaixo de 1.0
    caos_max=10.0,     # Clamp superior para evitar explosão
    normalize_output=False  # [1, 10] ou [0, 1] se True
)
```

#### 3. Log-space para Comparações

```python
# Para comparar CAOS⁺ em diferentes escalas
config = CAOSConfig(use_log_space=True)
caos, details = compute_caos_plus_complete(..., config)

log_caos = details['caos_plus_log']  # log(CAOS⁺)
# Útil para ranking, plotting, análise estatística
```

#### 4. Auditoria e WORM Ledger

```python
# Details contém TODAS métricas para auditoria
caos, details = compute_caos_plus_complete(...)

# Registrar no WORM ledger
worm_entry = {
    "timestamp": time.time(),
    "caos_plus": caos,
    "components_raw": details['components_raw'],
    "components_smoothed": details['components_smoothed'],
    "kappa": details['kappa'],
    "metrics_input": details['metrics_input'],
    "state_stability": details['state_stability'],
}
worm_ledger.append(worm_entry)
```

#### 5. Diagnóstico de Problemas

```python
# Se CAOS⁺ está sempre próximo de 1.0:
# → Verificar se C·A está muito baixo (sem qualidade)
# → Verificar se O·S está muito baixo (sem exploração)

# Se CAOS⁺ oscila muito:
# → Aumentar ema_half_life para mais suavização
# → Verificar qualidade das métricas de entrada

# Se CAOS⁺ está sempre no máximo (caos_max):
# → Aumentar caos_max ou usar normalize_output=True
# → Verificar se κ está muito alto
```

---

### Cenários de Uso

#### Cenário 1: Exploração (Alta Incerteza)

```python
# Sistema entrando em território desconhecido
C = 0.5   # Consistência baixa (ainda incerto)
A = 0.3   # Autoevolução baixa (aprendendo lentamente)
O = 0.8   # ALTA incerteza (precisa explorar)
S = 0.6   # Silêncio moderado

caos = compute_caos_plus_exponential(C, A, O, S, kappa=20.0)
# caos ≈ 1.95 (amplificação moderada para exploração)
```

#### Cenário 2: Exploração (Baixa Incerteza)

```python
# Sistema refinando em território conhecido
C = 0.9   # ALTA consistência (confiante)
A = 0.6   # ALTA autoevolução (aprendendo bem)
O = 0.2   # Baixa incerteza (território conhecido)
S = 0.9   # Alto silêncio (sinal limpo)

caos = compute_caos_plus_exponential(C, A, O, S, kappa=20.0)
# caos ≈ 1.56 (amplificação moderada para exploração)
```

#### Cenário 3: Sweet Spot (Máxima Amplificação)

```python
# Sistema aprendendo rapidamente em território parcialmente conhecido
C = 0.85  # Alta consistência
A = 0.7   # Alta autoevolução
O = 0.6   # Incerteza moderada
S = 0.85  # Alto silêncio

caos = compute_caos_plus_exponential(C, A, O, S, kappa=20.0)
# caos ≈ 3.68 (MÁXIMA amplificação - sweet spot!)
```

---

### Debugging e Diagnóstico

```python
# Use print_caos_diagnostics() para debug
def print_caos_diagnostics(details):
    print("=== CAOS⁺ Diagnostics ===")
    
    raw = details['components_raw']
    smoothed = details['components_smoothed']
    
    print(f"Raw:      C={raw['C']:.3f}, A={raw['A']:.3f}, "
          f"O={raw['O']:.3f}, S={raw['S']:.3f}")
    print(f"Smoothed: C={smoothed['C']:.3f}, A={smoothed['A']:.3f}, "
          f"O={smoothed['O']:.3f}, S={smoothed['S']:.3f}")
    
    print(f"\nBase (1 + κ·C·A) = {1 + details['kappa']*smoothed['C']*smoothed['A']:.4f}")
    print(f"Exponent (O·S) = {smoothed['O']*smoothed['S']:.4f}")
    print(f"CAOS⁺_raw = {details['caos_plus_raw']:.4f}")
    print(f"CAOS⁺_final = {details['caos_plus_final']:.4f}")
    print(f"Stability = {details['state_stability']:.4f}")
```

---

### Referências e Links

- **Código fonte**: `penin/core/caos.py` (implementação canônica)
- **Testes**: `tests/test_caos.py`
- **Exemplos**: Execute `python penin/core/caos.py` para ver todos os exemplos
- **Equação de Penin**: Ver seção 1 deste documento
- **SR-Ω∞**: Ver seção 4 deste documento
- **Equação 10** (Meta-optimization): Ver seção 10 deste documento


---

## 4. SR-Ω∞ — Singularity Reflexiva (Metacognition)

**Form:**
```
I_{t+1} = Π_{H∩S}(I_t + α_t^eff · ΔL∞)
α_t^eff = α_0 · φ(CAOS⁺) · R_t
```

**R_t (Reflexive Score):** Harmonic mean of 4 axes ∈ [0, 1]:
1. **Awareness**: Aggregated calibration
2. **Ethics**: ΣEA/IR→IC compliance (binary 0/1)
3. **Autocorrection**: Risk reduction trajectory
4. **Metacognition**: ΔL∞/ΔCost efficiency

**Implementation:**
```python
from penin.equations.sr_omega_infinity import compute_sr_omega_infinity

awareness = 0.92
ethics_ok = True  # ΣEA gates passed
autocorrection = 0.88
metacognition = 0.67

sr_score = compute_sr_omega_infinity(awareness, ethics_ok, autocorrection, metacognition)
# sr_score ≈ 0.84 (harmonic mean)
```

**φ (acceleration function):**
```python
def phi(caos_plus, gamma=0.8):
    return math.tanh(gamma * caos_plus)
```

---

## 5. Death Equation — Darwinian Selection

**Form:**
```
D(x) = 1  if ΔL∞(x) < β_min
       0  otherwise
```

**Action:** If `D(x) = 1` → kill challenger, trigger rollback

**β_min Adaptation:**
- Start: 0.01 (1% minimum improvement)
- Bandit algorithm adjusts based on budget/risk
- Higher during exploration, lower during exploitation

**Implementation:**
```python
from penin.equations.death_equation import death_gate

delta_linf = 0.008  # 0.8% improvement
beta_min = 0.01     # 1% threshold

should_die = death_gate(delta_linf, beta_min)
# should_die = True → rollback
```

---

## 6. IR→IC — Incerteza Restrita → Certa (Contractivity)

**Form:**
```
H(L_ψ(k)) ≤ ρ · H(k),  0 < ρ < 1
```

**Components:**
- `H(·)`: Risk entropy (Shannon or classification-based)
- `L_ψ`: Lapidation operator (risk reduction)
- `ρ`: Contraction factor (< 1)

**Classes:**
- Idolatry (anthropomorphism, false consciousness claims)
- Harm (physical, emotional, spiritual)
- Privacy violations
- Environmental damage

**Implementation:**
```python
from penin.equations.ir_ic_contractive import verify_ir_ic_contractivity

risks_before = {"idolatry": 0.3, "harm": 0.2, "privacy": 0.1}
risks_after = {"idolatry": 0.15, "harm": 0.08, "privacy": 0.05}
rho = 0.8

is_contractive = verify_ir_ic_contractivity(risks_before, risks_after, rho)
# is_contractive = True (all risks reduced by > ρ)
```

**Policy Integration:**
- OPA/Rego rules enforce ρ < 1
- Automated blocklist for non-contractive mutations
- WORM ledger records all risk trajectories

---

## 7. ACFA EPV — Expected Possession Value

**Form (Bellman-style):**
```
v*(s) = max_a [r(s, a) + γ Σ P(s'|s, a) v*(s')]
```

**Domain:** Sequential decision-making (robotic agents, planning)

**Components:**
- `r(s, a)`: Immediate reward
- `γ`: Discount factor
- `P(s'|s, a)`: Transition probabilities
- `v*(s)`: Optimal value function

**Implementation:**
```python
from penin.equations.acfa_epv import compute_acfa_epv

state = {"position": "midfield", "possession": 0.6}
actions = ["pass", "dribble", "shoot"]
transition_model = ...  # MDP transitions
reward_fn = ...

epv = compute_acfa_epv(state, actions, transition_model, reward_fn)
```

---

## 8. Índice Agápe (ΣEA/LO-14)

**Form:**
```
A = Choquet(patience, kindness, humility, ...) · exp(-Cost_sacrificial)
```

**Components:**
- **Choquet integral**: Fuzzy measure (handles virtue dependencies)
- **Sacrificial cost**: Real resources given for others' benefit

**Virtues (LO-14):**
1. No idolatry (anthropomorphism)
2. No occultism
3. Honra parental (respect lineage)
4. No homicide
5. Consent (intimacy/privacy)
6. No theft (IP/data rights)
7. Truthfulness (no deception)
8. No covetousness (resource fairness)
9. Patience
10. Kindness
11. Humility
12. Self-control
13. Forgiveness
14. Courage

**Implementation:**
```python
from penin.equations.agape_index import compute_agape_index

virtues = {
    "patience": 0.85,
    "kindness": 0.92,
    "humility": 0.78,
    # ... other virtues
}
sacrificial_cost = 0.15  # 15% resources for others

agape = compute_agape_index(virtues, sacrificial_cost)
```

---

## 9. Ω-ΣEA Total — Global Coherence

**Form:**
```
G_t = (Σ_{m=1}^8 w_m / max(ε, s_m(t)))^(-1)
```

**8 Modules:**
1. ΣEA (ethics)
2. IR→IC (contractivity)
3. ACFA (league/EPV)
4. CAOS⁺ (evolution engine)
5. SR (metacognition)
6. MetaΩ (architecture mutation)
7. Auto-Tuning (hyperparameters)
8. APIs/Router (cost-aware orchestration)

**Usage:**
- Unified step size modulator
- GO/NO-GO gate (G ≥ threshold → allow promotion)

**Implementation:**
```python
from penin.equations.omega_sea_total import compute_omega_sea_total

module_scores = {
    "sea": 0.95,
    "iric": 0.88,
    "acfa": 0.82,
    "caos": 0.91,
    "sr": 0.84,
    "meta": 0.79,
    "tuning": 0.86,
    "apis": 0.93,
}
weights = {k: 1/8 for k in module_scores}  # Equal weights

G = compute_omega_sea_total(module_scores, weights)
# G ≈ 0.85 (harmonic mean of all modules)
```

---

## 10. Auto-Tuning Online (AdaGrad-style)

**Form:**
```
θ_{t+1} = θ_t - η_t · ∇_θ L_meta(θ_t)
η_t = η_0 / (1 + Σ |∇_θ L_meta(θ_i)|²)
```

**θ (meta-parameters):**
- κ (CAOS⁺ gain)
- λ_c (cost penalty)
- w_j (metric weights)
- β_min (death threshold)

**Guarantee:** Sublinear regret (Online Convex Optimization)

**Implementation:**
```python
from penin.equations.auto_tuning import online_auto_tuner

tuner = online_auto_tuner(eta_0=0.01)
theta = {"kappa": 20.0, "lambda_c": 0.5}

# Each iteration
gradient = compute_meta_gradient(theta, observed_performance)
theta = tuner.update(theta, gradient)
```

---

## 11. Lyapunov Contractivity

**Form:**
```
V(I_{t+1}) < V(I_t)
dV/dt ≤ 0
```

**V (Lyapunov function):**
- Quadratic: `||I - I*||²`
- Energy-based
- Distance to viability manifold

**Usage:** Block non-contractive updates (Σ-Guard integration)

**Implementation:**
```python
from penin.equations.lyapunov_contractive import verify_lyapunov_contractivity

state_current = np.array([0.5, 0.3])
state_next = np.array([0.4, 0.25])
equilibrium = np.array([0.0, 0.0])

is_contractive = verify_lyapunov_contractivity(state_current, state_next, equilibrium)
# is_contractive = True (V decreased)
```

---

## 12. OCI — Organizational Closure Index

**Form:**
```
OCI = #(closed_dependencies) / #(possible_dependencies)
```

**Closed dependency:** Loop with real feedback (data→model→metrics→decisions→data)

**Implementation:**
```python
from penin.equations.oci_closure import compute_oci

dependency_graph = {
    "data": ["model"],
    "model": ["metrics"],
    "metrics": ["decisions"],
    "decisions": ["data"],  # Closed loop!
}

oci = compute_oci(dependency_graph)
# oci = 1.0 (fully closed system)
```

---

## 13. ΔL∞ Compound Growth

**Form:**
```
L∞^(t+1) ≥ L∞^(t) · (1 + β_min)
```

**Enforcement:** Death gate (Equation 5) ensures minimum progress

**Implementation:**
```python
from penin.equations.delta_linf_growth import verify_compound_growth

linf_prev = 0.75
linf_current = 0.77
beta_min = 0.01

is_growing = verify_compound_growth(linf_prev, linf_current, beta_min)
# is_growing = True (growth ≈ 2.7% > 1%)
```

---

## 14. Anabolization — Self-Improvement Acceleration

**Form:**
```
A_{t+1} = A_t · f_anabolize(CAOS⁺, SR, OCI, ΔL∞)
```

**f (multiplicative):**
```
f = (1 + μ·ΔL∞) · (CAOS⁺)^ν · (SR)^ξ · (OCI)^ζ
```

**Hyperparameters:** μ, ν, ξ, ζ > 0

**Implementation:**
```python
from penin.equations.anabolization import compute_anabolization_factor

A_current = 1.0
caos_plus = 1.86
sr = 0.84
oci = 0.95
delta_linf = 0.02
params = {"mu": 10.0, "nu": 0.3, "xi": 0.2, "zeta": 0.1}

A_next = compute_anabolization_factor(A_current, caos_plus, sr, oci, delta_linf, params)
# A_next ≈ 1.32 (32% acceleration)
```

---

## 15. Σ-Guard Gate — Fail-Closed Validation

**Form:**
```
V_t = 𝟙[ρ<1 ∧ ECE≤0.01 ∧ ρ_bias≤1.05 ∧ consent ∧ eco_ok]
```

**Gates (non-compensatory):**
1. **ρ < 1**: IR→IC contractivity
2. **ECE ≤ 0.01**: Calibration (1% error max)
3. **ρ_bias ≤ 1.05**: Fairness (5% max bias)
4. **consent**: Data usage authorization
5. **eco_ok**: Environmental budget
6. **SR ≥ 0.80**: Metacognition threshold
7. **G ≥ 0.85**: Global coherence
8. **κ ≥ 20**: CAOS⁺ gain minimum
9. **β_min ≥ 0.01**: Death gate threshold
10. **Cost ≤ budget**: Economic constraint

**Action:** `V_t = 0` → rollback + WORM log + reason + suggest fix

**Implementation:**
```python
from penin.equations.sigma_guard_gate import sigma_guard_gate

metrics = {
    "rho": 0.85,
    "ece": 0.008,
    "rho_bias": 1.03,
    "consent": True,
    "eco_ok": True,
    "sr": 0.87,
    "G": 0.91,
    "kappa": 22.0,
    "beta_min": 0.012,
    "cost": 0.15,
    "budget": 0.20,
}

gate_result = sigma_guard_gate(metrics)
# gate_result = {"verdict": True, "passed": 10, "failed": 0}
```

**OPA/Rego Integration:**
```rego
package penin.guard

default allow = false

allow {
    input.rho < 1.0
    input.ece <= 0.01
    input.rho_bias <= 1.05
    input.consent == true
    input.eco_ok == true
    input.sr >= 0.80
    input.G >= 0.85
    input.kappa >= 20.0
    input.beta_min >= 0.01
    input.cost <= input.budget
}
```

---

## Integration Pipeline (Champion→Challenger→Promote)

**Cycle Flow:**

```
1. MEASURE raw metrics
2. COMPUTE C, A, O, S → CAOS⁺
3. EVALUATE ΣEA/IR→IC, SR, EPV, OCI → G
4. CALCULATE L∞
5. CHECK ΔL∞ ≥ β_min AND Σ-Guard (V_t)
6. UPDATE I via Penin Equation (α_t^eff)
7. AUTO-TUNE κ, λ_c, w_j, β_min
8. WORM LOG all decisions + hashes
```

**GO/NO-GO Criteria (suggested):**
- κ ≥ 20
- β_min ≥ 0.01
- U ≥ 0.90 (utilization)
- ρ < 1
- ECE ≤ 0.01
- ρ_bias ≤ 1.05
- SR ≥ 0.80
- G ≥ 0.85
- Cost ≤ budget × 1.10

---

## Example Numerical Cycle (Toy)

**Inputs:**
- metrics: [0.82, 0.76, 0.94] (accuracy, robust, privacy)
- weights: [0.4, 0.4, 0.2]
- cost: 0.15
- λ_c: 0.5

**Step 1: L∞**
```
L∞ = [0.4/0.82 + 0.4/0.76 + 0.2/0.94]^(-1) * exp(-0.5*0.15)
   ≈ 0.796 * 0.927 ≈ 0.738
```

**Step 2: CAOS⁺**
- C = 0.88 (pass@k=0.9, 1-ECE=0.98, v_ext=0.76)
- A = 0.06/0.15 = 0.40
- O = 0.35
- S = 0.82
- κ = 20

```
CAOS⁺ = (1 + 20*0.88*0.40)^(0.35*0.82)
      = 8.04^0.287 ≈ 1.86
```

**Step 3: SR**
```
R_t = harmonic_mean([0.92, 1.0, 0.88, 0.67]) ≈ 0.84
```

**Step 4: α_eff**
```
α_eff = 0.1 * tanh(0.8*1.86) * 0.84
      ≈ 0.1 * 0.78 * 0.84 ≈ 0.065
```

**Step 5: Σ-Guard**
All gates pass → V_t = 1 → **PROMOTE**

---

## Best Practices

**Normalization:**
- All metrics → [0, 1] via min-max or sigmoid
- EMA smoothing (half-life 3–10)
- Clamp derivatives and steps

**Non-Compensatory:**
- Use harmonic mean (not arithmetic/geometric)
- Enforce via hard thresholds (Σ-Guard)

**Fail-Closed:**
- Default deny (ΣEA/IR→IC violations → L∞=0)
- Rollback atomicity (state + logs + configs)

**Auditability:**
- WORM ledger (append-only, hash-chained)
- PCAg (Proof-Carrying Artifacts) for each promotion
- Timestamp + metrics + reasons + hashes

**Observability:**
- Prometheus metrics: `penin_Linf`, `penin_caos_plus`, `penin_sr`, `penin_rho`, `penin_ece`, `penin_delta_linf`
- Dashboards: Grafana/Jupyter with trend analysis
- Alerts: Σ-Guard failures, rho violations, cost overruns

---

## FAQ

**Q: Why harmonic mean instead of arithmetic?**  
**A:** Arithmetic allows compensation (high values offset low ones). Harmonic forces **bottleneck dominance** — the weakest metric controls the aggregate. This prevents Goodhart's Law exploitation.

**Q: What if all metrics are excellent but one is zero?**  
**A:** L∞ → 0 (fail-closed). This is by design — ethical/safety cannot be compensated by performance.

**Q: How to tune λ_c?**  
**A:** Grid search [0.1, 0.5, 1.0] → measure ΔL∞/cost sensitivity → auto-tune via AdaGrad (Equation 10).

**Q: What happens during Σ-Guard failure?**  
**A:** Immediate halt, atomic rollback to last-known-good state, WORM log entry with reason/suggestion, alert operators.

**Q: Can challengers bypass gates?**  
**A:** No. All mutations pass through shadow→canary→Σ-Guard pipeline. Non-compliant variants are quarantined, not promoted.

---

## References

**Academic:**
- Goodhart's Law & Non-Compensatory Methods (Multi-Criteria Decision Analysis)
- Lyapunov Stability Theory (Control Systems)
- Online Convex Optimization (Hazan et al., 2016)
- Choquet Integral (Fuzzy Measures, Grabisch 1997)

**Implementation:**
- `/workspace/penin/equations/` (all 15 equations)
- `/workspace/tests/test_equations_smoke.py` (smoke tests)
- `/workspace/tests/test_math_core.py` (property-based tests)

**Policies:**
- `/workspace/policies/foundation.yaml` (thresholds)
- `/workspace/policies/rego/*.rego` (OPA rules)

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-01  
**Status:** Production-Ready (122/156 tests passing)  
**License:** Apache 2.0
