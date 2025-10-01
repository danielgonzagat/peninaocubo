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

**Form:**
```
CAOS⁺ = (1 + κ · C · A)^(O · S)
```

**Components (all ∈ [0, 1]):**
- **C (Consistency)**: `(pass@k + (1-ECE) + v_ext) / 3`
  - pass@k: Self-consistency across samples
  - ECE: Expected Calibration Error
  - v_ext: External verification score
  
- **A (Autoevolution)**: `ΔL∞ / (Cost_norm + ε)`
  - Improvement per unit cost
  
- **O (Unknowable)**: `w_epi · epistemic + w_ood · ood_score`
  - Epistemic uncertainty (model confidence)
  - OOD: Out-of-distribution detection
  
- **S (Silence)**: `2(1-noise) + 1(1-redund) + 1(1-entropy)` / 4
  - Weighted anti-noise/redundancy/entropy

- **κ (kappa)**: Amplification gain (≥ 20, auto-tuned)

**Implementation:**
```python
from penin.equations.caos_plus import compute_caos_plus_exponential, CAOSConfig

C = 0.88  # high consistency
A = 0.40  # moderate improvement/cost
O = 0.35  # some uncertainty
S = 0.82  # high signal quality
kappa = 20.0

config = CAOSConfig(kappa=kappa)
caos_plus = compute_caos_plus_exponential(C, A, O, S, config)
# caos_plus ≈ 1.86 (boost factor for step size)
```

**Usage:**
- Modulates α (step size) in Penin Equation
- Challenger selection (higher CAOS⁺ → prioritize)
- Adaptive β_min (death gate threshold)

**Best Practices:**
- EMA smoothing (half-life 3-10 iterations)
- Clamp derivatives (avoid numerical instability)
- Log-space comparison for large ranges

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
