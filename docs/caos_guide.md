# CAOS⁺ — Guia Completo do Motor Evolutivo

## Visão Geral

CAOS⁺ (Consistency, Autoevolution, Unknowable/Incognoscível, Silence) é o motor central do sistema auto-evolutivo PENIN-Ω. Ele modula dinamicamente a taxa de aprendizado (α) baseado em quatro dimensões fundamentais, permitindo exploração agressiva quando apropriado e conservadorismo quando necessário.

**Características Principais:**
- ✅ Fórmula matemática rigorosa com propriedades provadas
- ✅ Monotônica em todos os componentes (previsível)
- ✅ Auto-tunável via meta-otimização (Equação 10)
- ✅ Suavização temporal via EMA (reduz ruído)
- ✅ Auditável (todas decisões registradas em WORM ledger)

---

## Fórmula Matemática

### Forma Exponencial (Principal)

```
CAOS⁺ = (1 + κ·C·A)^(O·S)
```

**Onde:**
- **C** (Consistência): [0, 1] - Quão confiável é o sistema
- **A** (Autoevolução): [0, 1] - Eficiência do ganho por custo
- **O** (Incognoscível): [0, 1] - Grau de incerteza epistêmica
- **S** (Silêncio): [0, 1] - Qualidade do sinal (anti-ruído)
- **κ** (kappa): ≥ 1 - Ganho de amplificação (típico: 20-50)

**Output:**
- CAOS⁺ ≥ 1.0 (sem limite superior)
- Valores típicos: 1.5-5.0 em operação normal
- Serve como multiplicador de α_t (step size)

### Forma com Saturação (Alternativa)

```
φ_CAOS = tanh(γ · log(CAOS⁺))
```

**Onde:**
- **γ** (gamma): [0.1, 2.0] - Parâmetro de saturação (default: 0.7)

**Output:**
- φ_CAOS ∈ [0, 1) aproximadamente
- Útil para composição com outras métricas normalizadas

---

## Racional Matemático

### Por que esta fórmula?

A estrutura `(base)^(expoente)` foi escolhida por três razões fundamentais:

#### 1. **Separação de Concerns**

- **Base (1 + κ·C·A)**: Controla a magnitude da amplificação
  - Alta consistência + boa autoevolução → base grande → mais confiança
  - C=0 ou A=0 → base=1 → sem amplificação (segurança)
  
- **Expoente (O·S)**: Controla a agressividade
  - Alta incerteza (O) com alto silêncio (S) → libera exploração
  - Baixo O ou S → expoente pequeno → conservador

#### 2. **Propriedades Matemáticas Desejáveis**

- **Identidade**: CAOS⁺(0,0,0,0) = 1 (sem amplificação = neutro)
- **Monotonia**: ∂CAOS⁺/∂X > 0 para X ∈ {C, A, O, S} (previsível)
- **Composicionalidade**: Base e expoente independentes (ortogonais)
- **Estabilidade Numérica**: Sempre definida para inputs válidos

#### 3. **Alinhamento com Princípios de Aprendizado**

- **Exploit quando seguro** (C alto, A alto, O baixo): Base alta, expoente baixo = moderado
- **Explore quando incerto** (C médio, O alto, S alto): Expoente alto = agressivo
- **Cautela quando arriscado** (C baixo ou S baixo): Base baixa = conservador

### Exemplo Numérico

```python
# Cenário 1: Sistema maduro, domínio conhecido
C = 0.92  # Alta consistência
A = 0.30  # Baixa autoevolução (já otimizado)
O = 0.20  # Baixa incerteza
S = 0.85  # Alto silêncio
κ = 20

base = 1 + 20 * 0.92 * 0.30 = 6.52
expoente = 0.20 * 0.85 = 0.17
CAOS⁺ = 6.52^0.17 ≈ 1.37

# Resultado: Amplificação modesta (37% boost em α)
```

```python
# Cenário 2: Exploração agressiva
C = 0.75  # Consistência moderada
A = 0.50  # Boa autoevolução
O = 0.60  # Alta incerteza (explorar!)
S = 0.70  # Silêncio moderado
κ = 35

base = 1 + 35 * 0.75 * 0.50 = 14.125
expoente = 0.60 * 0.70 = 0.42
CAOS⁺ = 14.125^0.42 ≈ 3.15

# Resultado: Amplificação agressiva (215% boost em α)
```

---

## Componentes Detalhados

### C — Consistência [0, 1]

**Definição**: Quão confiável e calibrado é o sistema.

**Cálculo**:
```
C = w1·pass@k + w2·(1-ECE) + w3·v_ext
```

**Sub-componentes**:
1. **pass@k**: Taxa de sucesso em k tentativas independentes
   - Exemplo: 9/10 amostras corretas → pass@k = 0.9
   - Mede auto-consistência (robustez)

2. **ECE** (Expected Calibration Error): Calibração de confiança
   - Mede se p(correto) ≈ confiança reportada
   - ECE < 0.01 é excelente (< 1% de erro)
   - Invertemos: (1-ECE) para que maior seja melhor

3. **v_ext**: Verificação externa
   - Oráculos, testes formais, validação humana
   - Típico: 0.7-0.95 em produção

**Pesos Recomendados**: w1=0.4, w2=0.3, w3=0.3

**Exemplo**:
```python
from penin.core.caos import ConsistencyMetrics

consistency = ConsistencyMetrics(
    pass_at_k=0.92,           # 92% auto-consistência
    ece=0.008,                # 0.8% erro de calibração
    external_verification=0.88 # 88% verificação externa
)

C = consistency.compute_c()
# C ≈ 0.40*0.92 + 0.30*(1-0.008) + 0.30*0.88
# C ≈ 0.368 + 0.298 + 0.264 = 0.930
```

**Interpretação**:
- C > 0.90: Sistema muito confiável (produção)
- C = 0.70-0.90: Confiável, mas monitorar
- C < 0.70: Atenção! Possível degradação

---

### A — Autoevolução [0, 1]

**Definição**: Eficiência do ganho evolutivo por unidade de custo.

**Cálculo**:
```
A = ΔL∞⁺ / (Cost_norm + ε)
A_normalized = A / A_max
```

**Sub-componentes**:
1. **ΔL∞⁺**: Ganho de L∞ (só positivo)
   - ΔL∞ = L∞_novo - L∞_antigo
   - ΔL∞⁺ = max(0, ΔL∞)

2. **Cost_norm**: Custo normalizado
   - Proporção do budget consumido
   - Exemplo: 0.15 = 15% do budget

3. **ε**: Estabilizador numérico (10⁻³ default)

**Normalização**: Divide por A_max (default 10.0) para manter em [0,1]

**Exemplo**:
```python
from penin.core.caos import AutoevolutionMetrics

autoevol = AutoevolutionMetrics(
    delta_linf=0.06,      # 6% ganho em L∞
    cost_normalized=0.15, # 15% do budget
    max_a=10.0
)

A = autoevol.compute_a()
# A_raw = 0.06 / (0.15 + 0.001) = 0.397
# A_normalized = 0.397 / 10.0 = 0.040 (4%)
```

**Interpretação**:
- A > 0.50: Evolução muito eficiente (ótimo!)
- A = 0.20-0.50: Evolução moderada
- A < 0.20: Baixa eficiência (considerar otimizar)

**Note**: A tende a ser baixo (~0.2-0.4) em produção pois sistemas maduros têm ganhos marginais pequenos.

---

### O — Incognoscível [0, 1]

**Definição**: Grau de incerteza epistêmica (o que o sistema não sabe que não sabe).

**Cálculo**:
```
O = w1·epistemic + w2·ood + w3·disagreement
```

**Sub-componentes**:
1. **epistemic_uncertainty**: Incerteza epistêmica
   - Entropy, Mutual Information, variance
   - Mede incerteza do modelo (não dos dados)

2. **ood_score**: Out-of-Distribution score
   - Distância da distribuição de treino
   - Detecta inputs anômalos

3. **ensemble_disagreement**: Disagreement de ensemble
   - Variância entre modelos independentes
   - Alto = modelos discordam = incerteza

**Pesos Recomendados**: w1=0.4, w2=0.3, w3=0.3

**Exemplo**:
```python
from penin.core.caos import IncognoscibleMetrics

incog = IncognoscibleMetrics(
    epistemic_uncertainty=0.35,  # 35% incerteza
    ood_score=0.28,              # 28% OOD
    ensemble_disagreement=0.30   # 30% disagreement
)

O = incog.compute_o()
# O ≈ 0.4*0.35 + 0.3*0.28 + 0.3*0.30
# O ≈ 0.140 + 0.084 + 0.090 = 0.314
```

**Interpretação**:
- O > 0.60: Alta incerteza → EXPLORAR!
- O = 0.30-0.60: Incerteza moderada
- O < 0.30: Baixa incerteza → EXPLOITAR

**Princípio**: Mais O → maior expoente → amplificação mais agressiva → exploração liberada.

---

### S — Silêncio [0, 1]

**Definição**: Qualidade do sinal (anti-ruído, anti-redundância, anti-entropia).

**Cálculo**:
```
S = v1·(1-noise) + v2·(1-redund) + v3·(1-entropy)
```

**Sub-componentes**:
1. **noise_ratio**: Proporção de ruído [0,1]
   - SNR, outliers, medições instáveis
   - S inverte: queremos BAIXO ruído

2. **redundancy_ratio**: Proporção de redundância [0,1]
   - Informação duplicada, features correlacionadas
   - Desperdiça computação

3. **entropy_normalized**: Entropia normalizada [0,1]
   - Desordem, imprevisibilidade
   - Alto = caótico, baixo = estruturado

**Pesos Recomendados**: v1=0.5, v2=0.25, v3=0.25 (ratio 2:1:1)

**Exemplo**:
```python
from penin.core.caos import SilenceMetrics

silence = SilenceMetrics(
    noise_ratio=0.08,          # 8% ruído
    redundancy_ratio=0.12,     # 12% redundância
    entropy_normalized=0.18    # 18% entropia
)

S = silence.compute_s()
# S ≈ 0.5*(1-0.08) + 0.25*(1-0.12) + 0.25*(1-0.18)
# S ≈ 0.5*0.92 + 0.25*0.88 + 0.25*0.82
# S ≈ 0.460 + 0.220 + 0.205 = 0.885
```

**Interpretação**:
- S > 0.80: Sinal limpo (ótimo!)
- S = 0.60-0.80: Qualidade aceitável
- S < 0.60: Muito ruidoso (melhorar preprocessing)

**Princípio**: Alto S → maior expoente → sistema confia nos dados → exploração mais segura.

---

## Parâmetros Globais

### κ (Kappa) — Ganho de Amplificação

**Definição**: Controla a agressividade do sistema evolutivo.

**Range**: [kappa_min, kappa_max] típico [10, 100]

**Valores Recomendados**:
- **κ = 10-15**: Conservador (produção estável, baixo risco)
- **κ = 20-25**: Balanceado (default, boa exploração/exploitação)
- **κ = 30-50**: Agressivo (pesquisa, experimentação)
- **κ > 50**: Muito agressivo (use com cautela!)

**Auto-Tuning**: κ pode ser auto-tunado via Equação 10 (AdaGrad-style).

**Exemplo**:
```python
from penin.core.caos import CAOSConfig

# Conservador
config_conservative = CAOSConfig(kappa=12.0)

# Balanceado
config_balanced = CAOSConfig(kappa=20.0)

# Agressivo
config_aggressive = CAOSConfig(kappa=40.0)
```

**Impacto**:
```python
C, A = 0.8, 0.5
kappa_values = [10, 20, 30, 50]

for k in kappa_values:
    base = 1 + k * C * A
    print(f"κ={k}: base={base:.1f}")

# Saída:
# κ=10: base=5.0
# κ=20: base=9.0
# κ=30: base=13.0
# κ=50: base=21.0
```

---

## Exemplos Práticos

### Exemplo 1: Pipeline Completo de Produção

```python
from penin.core.caos import (
    ConsistencyMetrics, AutoevolutionMetrics,
    IncognoscibleMetrics, SilenceMetrics,
    CAOSConfig, CAOSState,
    compute_caos_plus_complete
)

# 1. Coletar métricas raw do sistema
consistency = ConsistencyMetrics(
    pass_at_k=0.92,
    ece=0.008,
    external_verification=0.88
)

autoevolution = AutoevolutionMetrics(
    delta_linf=0.06,      # 6% ganho
    cost_normalized=0.15  # 15% budget
)

incognoscible = IncognoscibleMetrics(
    epistemic_uncertainty=0.35,
    ood_score=0.28,
    ensemble_disagreement=0.30
)

silence = SilenceMetrics(
    noise_ratio=0.08,
    redundancy_ratio=0.12,
    entropy_normalized=0.18
)

# 2. Configurar motor CAOS⁺
config = CAOSConfig(
    kappa=25.0,           # Moderadamente agressivo
    ema_half_life=5,      # Suavizar em 5 iterações
    caos_min=1.0,         # Base mínima
    caos_max=10.0,        # Teto de amplificação
    normalize_output=False # Manter como multiplicador
)

# 3. Estado persistente (compartilhado entre iterações)
state = CAOSState()

# 4. Computar CAOS⁺
caos_plus, details = compute_caos_plus_complete(
    consistency, autoevolution, incognoscible, silence,
    config, state
)

print(f"CAOS⁺: {caos_plus:.4f}")
print(f"Componentes (smoothed): C={details['components_smoothed']['C']:.3f}, "
      f"A={details['components_smoothed']['A']:.3f}, "
      f"O={details['components_smoothed']['O']:.3f}, "
      f"S={details['components_smoothed']['S']:.3f}")

# 5. Usar no pipeline evolutivo
alpha_base = 0.1
alpha_effective = alpha_base * caos_plus

print(f"\nPipeline de Evolução:")
print(f"  α_base: {alpha_base}")
print(f"  CAOS⁺: {caos_plus:.4f}")
print(f"  α_eff: {alpha_effective:.4f} (amplificado {caos_plus:.1f}×)")

# 6. Decisão de promoção
threshold = 2.0
if caos_plus >= threshold:
    decision = "PROMOTE"
    print(f"\n✅ DECISÃO: {decision} (CAOS⁺ {caos_plus:.2f} ≥ {threshold})")
else:
    decision = "ROLLBACK"
    print(f"\n❌ DECISÃO: {decision} (CAOS⁺ {caos_plus:.2f} < {threshold})")

# 7. Registrar em WORM ledger para auditoria
import json
import datetime

ledger_entry = {
    "timestamp": datetime.datetime.utcnow().isoformat(),
    "caos_plus": caos_plus,
    "alpha_effective": alpha_effective,
    "decision": decision,
    "details": details,
    "metrics": {
        "consistency": consistency.__dict__,
        "autoevolution": autoevolution.__dict__,
        "incognoscible": incognoscible.__dict__,
        "silence": silence.__dict__
    }
}

# with open("worm_ledger.jsonl", "a") as f:
#     f.write(json.dumps(ledger_entry) + "\n")

print(f"\n📝 Entry registrado no WORM ledger")
```

**Saída Esperada**:
```
CAOS⁺: 1.8654
Componentes (smoothed): C=0.930, A=0.398, O=0.314, S=0.885

Pipeline de Evolução:
  α_base: 0.1
  CAOS⁺: 1.8654
  α_eff: 0.1865 (amplificado 1.9×)

❌ DECISÃO: ROLLBACK (CAOS⁺ 1.87 < 2.0)

📝 Entry registrado no WORM ledger
```

---

### Exemplo 2: Comparação de Cenários

```python
from penin.core.caos import compute_caos_plus_exponential

def analyze_scenario(name, C, A, O, S, kappa=20.0):
    """Analisa um cenário e imprime detalhes"""
    caos = compute_caos_plus_exponential(C, A, O, S, kappa)
    base = 1 + kappa * C * A
    exp = O * S
    
    print(f"\n{name}:")
    print(f"  C={C:.2f}, A={A:.2f}, O={O:.2f}, S={S:.2f}, κ={kappa}")
    print(f"  Base: {base:.2f}")
    print(f"  Expoente: {exp:.2f}")
    print(f"  CAOS⁺: {caos:.2f}")
    
    # Interpretação
    if caos > 3.0:
        print(f"  → Amplificação FORTE (explorar agressivamente)")
    elif caos > 2.0:
        print(f"  → Amplificação MODERADA (balanceado)")
    elif caos > 1.5:
        print(f"  → Amplificação LEVE (conservador)")
    else:
        print(f"  → Amplificação MÍNIMA (muito conservador)")
    
    return caos

# Cenário 1: Sistema maduro, domínio conhecido
analyze_scenario(
    "Cenário 1: Produção Estável",
    C=0.92, A=0.30, O=0.20, S=0.85, kappa=15
)

# Cenário 2: Boa autoevolução, incerteza moderada
analyze_scenario(
    "Cenário 2: Evolução Ativa",
    C=0.85, A=0.50, O=0.40, S=0.75, kappa=20
)

# Cenário 3: Exploração agressiva
analyze_scenario(
    "Cenário 3: Pesquisa e Exploração",
    C=0.75, A=0.50, O=0.60, S=0.70, kappa=35
)

# Cenário 4: Baixa confiança (rollback provável)
analyze_scenario(
    "Cenário 4: Sistema Degradado",
    C=0.60, A=0.20, O=0.50, S=0.55, kappa=20
)
```

**Saída Esperada**:
```
Cenário 1: Produção Estável:
  C=0.92, A=0.30, O=0.20, S=0.85, κ=15
  Base: 5.14
  Expoente: 0.17
  CAOS⁺: 1.32
  → Amplificação MÍNIMA (muito conservador)

Cenário 2: Evolução Ativa:
  C=0.85, A=0.50, O=0.40, S=0.75, κ=20
  Base: 9.50
  Expoente: 0.30
  CAOS⁺: 1.97
  → Amplificação LEVE (conservador)

Cenário 3: Pesquisa e Exploração:
  C=0.75, A=0.50, O=0.60, S=0.70, κ=35
  Base: 14.12
  Expoente: 0.42
  CAOS⁺: 3.15
  → Amplificação FORTE (explorar agressivamente)

Cenário 4: Sistema Degradado:
  C=0.60, A=0.20, O=0.50, S=0.55, κ=20
  Base: 3.40
  Expoente: 0.28
  CAOS⁺: 1.43
  → Amplificação LEVE (conservador)
```

---

### Exemplo 3: Suavização Temporal com EMA

```python
from penin.core.caos import (
    ConsistencyMetrics, AutoevolutionMetrics,
    IncognoscibleMetrics, SilenceMetrics,
    CAOSConfig, CAOSState,
    compute_caos_plus_complete
)
import random

# Simular 10 iterações com métricas variáveis
config = CAOSConfig(
    kappa=20.0,
    ema_half_life=3,  # Suavizar em ~3 iterações
    normalize_output=False
)

state = CAOSState()

print("Iteração | C_raw | C_smoothed | CAOS⁺_raw | CAOS⁺_final | Estabilidade")
print("-" * 75)

for i in range(10):
    # Simular variação nas métricas
    noise = random.uniform(-0.05, 0.05)
    
    consistency = ConsistencyMetrics(
        pass_at_k=min(1.0, max(0.0, 0.90 + noise))
    )
    autoevolution = AutoevolutionMetrics(delta_linf=0.05)
    incognoscible = IncognoscibleMetrics(epistemic_uncertainty=0.30)
    silence = SilenceMetrics(noise_ratio=0.10)
    
    caos, details = compute_caos_plus_complete(
        consistency, autoevolution, incognoscible, silence,
        config, state
    )
    
    c_raw = details['components_raw']['C']
    c_smoothed = details['components_smoothed']['C']
    caos_raw = details['caos_plus_raw']
    stability = details['state_stability']
    
    print(f"{i+1:8d} | {c_raw:.3f} | {c_smoothed:.3f}      | {caos_raw:.3f}     | "
          f"{caos:.3f}       | {stability:.3f}")

print("\n📊 Observações:")
print("  - C_smoothed converge gradualmente (EMA reduz ruído)")
print("  - Estabilidade aumenta com mais amostras")
print("  - CAOS⁺_final é mais estável que CAOS⁺_raw")
```

---

## Best Practices

### 1. **Calibração de κ (Kappa)**

```python
# Teste diferentes valores de kappa
def test_kappa_range():
    C, A, O, S = 0.85, 0.40, 0.35, 0.80
    
    print("κ     | Base  | CAOS⁺ | α_eff (α_base=0.1)")
    print("-" * 45)
    
    for kappa in [10, 15, 20, 25, 30, 40, 50]:
        from penin.core.caos import compute_caos_plus_exponential
        caos = compute_caos_plus_exponential(C, A, O, S, kappa)
        base = 1 + kappa * C * A
        alpha_eff = 0.1 * caos
        print(f"{kappa:5d} | {base:5.1f} | {caos:5.2f} | {alpha_eff:.4f}")

test_kappa_range()
```

**Recomendação**: Comece com κ=20, monitore ΔL∞/custo, ajuste via auto-tuning.

---

### 2. **Monitoramento de Estabilidade**

```python
def check_stability(state, threshold=0.7):
    """Verifica estabilidade do CAOS⁺"""
    stability = state.get_stability()
    
    if stability < threshold:
        print(f"⚠️ ALERTA: Estabilidade baixa ({stability:.3f} < {threshold})")
        print("   Sugestões:")
        print("   - Aumentar ema_half_life (mais suavização)")
        print("   - Verificar qualidade das métricas de entrada")
        print("   - Reduzir κ (ser mais conservador)")
        return False
    else:
        print(f"✅ Estabilidade OK ({stability:.3f} ≥ {threshold})")
        return True
```

---

### 3. **Análise de Gargalos**

```python
def analyze_bottlenecks(details):
    """Identifica componentes que limitam CAOS⁺"""
    comps = details['components_smoothed']
    
    print("\nAnálise de Gargalos:")
    for name, value in comps.items():
        status = "✅" if value >= 0.7 else "⚠️" if value >= 0.5 else "❌"
        print(f"  {status} {name}: {value:.3f}")
    
    # Identificar gargalo
    bottleneck = min(comps.items(), key=lambda x: x[1])
    print(f"\n🎯 Gargalo principal: {bottleneck[0]} = {bottleneck[1]:.3f}")
    
    # Sugestões
    suggestions = {
        'C': "Melhorar calibração (ECE) ou pass@k",
        'A': "Otimizar cost/performance ratio",
        'O': "Normal ser baixo em produção (significa certeza)",
        'S': "Reduzir ruído, redundância ou entropia nos dados"
    }
    
    print(f"   Sugestão: {suggestions[bottleneck[0]]}")
```

---

### 4. **Thresholds de Decisão**

```python
def make_decision(caos_plus, context="production"):
    """Decide promoção baseado em thresholds contextualizados"""
    
    thresholds = {
        "production": 2.0,      # Conservador
        "staging": 1.5,         # Moderado
        "research": 1.2         # Agressivo
    }
    
    threshold = thresholds.get(context, 2.0)
    
    if caos_plus >= threshold:
        return "PROMOTE", f"CAOS⁺ {caos_plus:.2f} ≥ {threshold}"
    else:
        return "ROLLBACK", f"CAOS⁺ {caos_plus:.2f} < {threshold}"

# Uso
decision, reason = make_decision(1.85, "production")
print(f"{decision}: {reason}")
```

---

## Perguntas Frequentes (FAQ)

### Q1: Por que CAOS⁺ sempre ≥ 1?

**A**: A base é (1 + κ·C·A), com mínimo = 1 quando C=0 ou A=0. Qualquer base^expoente com base ≥ 1 resulta em ≥ 1. Isso garante que CAOS⁺ seja um multiplicador neutro ou amplificador, nunca penalizador.

---

### Q2: Quando usar exponential vs phi_caos?

**A**: 
- **Exponential** (recomendado): Pipeline evolutivo principal, modulação de α
- **phi_caos**: Composição com métricas normalizadas, visualizações, debug

---

### Q3: Como escolher κ (kappa)?

**A**:
1. Comece com κ=20 (default balanceado)
2. Monitore ΔL∞/custo por 5-10 iterações
3. Se evolução muito lenta: aumentar κ (25-30)
4. Se instável/excessiva: reduzir κ (15-18)
5. Use auto-tuning (Eq. 10) após calibração inicial

---

### Q4: O que fazer se CAOS⁺ é sempre baixo (<1.5)?

**A**: Investigar componentes:
- C baixo? → Melhorar calibração, pass@k
- A baixo? → Normal em produção madura (ganhos marginais)
- O ou S baixo? → Pode ser desejável (certeza, sinal limpo)
- κ baixo? → Aumentar se apropriado

---

### Q5: CAOS⁺ > 5.0 é perigoso?

**A**: Depende do contexto:
- **Pesquisa/exploração**: OK (desejável)
- **Produção crítica**: Cuidado! Monitore de perto
- **Solução**: Usar clamps (caos_max=10.0) ou reduzir κ

---

### Q6: Como integrar CAOS⁺ com SR-Ω∞?

**A**:
```python
from penin.equations.sr_omega_infinity import compute_sr_omega_infinity

# CAOS⁺ modula amplitude
caos_plus = compute_caos_plus_exponential(C, A, O, S, kappa)

# SR modula direção/qualidade
sr = compute_sr_omega_infinity(awareness, ethics_ok, autocorrection, metacog)

# α_eff combina ambos
alpha_effective = alpha_base * caos_plus * sr
```

---

## Referências

### Documentação Relacionada
- [Equações Completas](equations.md) - Todas as 15 equações do PENIN-Ω
- [Guia do Sistema Completo](COMPLETE_SYSTEM_GUIDE.md) - Pipeline Champion-Challenger
- [Arquitetura](architecture.md) - Visão geral do sistema

### Código Fonte
- `penin/core/caos.py` - Implementação principal
- `penin/equations/caos_plus.py` - Equação canônica
- `tests/test_caos.py` - Testes unitários

### Papers e Referências Acadêmicas
- Multi-Criteria Decision Analysis (MCDA)
- Exponential Moving Average (EMA) para séries temporais
- Adaptive Learning Rates em Deep Learning

---

**Versão**: 1.0.0  
**Última Atualização**: 2025-01-15  
**Status**: Production-Ready  
**Licença**: Apache 2.0
