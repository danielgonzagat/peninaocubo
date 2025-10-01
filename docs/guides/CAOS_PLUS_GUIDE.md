# CAOS⁺ Usage Guide - Motor Evolutivo PENIN-Ω

## Tabela de Conteúdos

1. [Introdução](#introdução)
2. [Visão Geral da Fórmula](#visão-geral-da-fórmula)
3. [Componentes Detalhados](#componentes-detalhados)
4. [Guia de Implementação](#guia-de-implementação)
5. [Exemplos Práticos](#exemplos-práticos)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## Introdução

CAOS⁺ (Consistency, Autoevolution, Unknowable, Silence) é o motor de evolução
adaptativa central do sistema PENIN-Ω. Ele modula dinamicamente a taxa de
aprendizado baseado em quatro dimensões fundamentais, equilibrando:

- **Exploração**: Buscar em território desconhecido (alta incerteza)
- **Exploração**: Refinar em território conhecido (baixa incerteza)

### Por Que CAOS⁺?

Sistemas de IA tradicionais usam taxas de aprendizado fixas ou schedules simples.
CAOS⁺ vai além ao adaptar a taxa baseado em:

1. **Qualidade** (C·A): Quão bem o sistema está performando
2. **Contexto** (O·S): Quanto precisa explorar vs explorar

Isso resulta em:
- ✅ Convergência mais rápida em territórios conhecidos
- ✅ Exploração mais agressiva em territórios desconhecidos
- ✅ Melhor trade-off entre performance e custo
- ✅ Adaptação automática a mudanças no ambiente

---

## Visão Geral da Fórmula

### Fórmula Matemática

```
CAOS⁺ = (1 + κ · C · A)^(O · S)
```

### Anatomia da Fórmula

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  CAOS⁺ = (1 + κ · C · A)^(O · S)               │
│          └─────┬─────┘  └───┬───┘              │
│                │            │                   │
│             BASE        EXPOENTE                │
│          (Potencial)  (Agressividade)           │
│                                                 │
└─────────────────────────────────────────────────┘

BASE: Quanto pode amplificar
  - C·A = Qualidade do aprendizado
  - κ = Intensidade da amplificação
  - Range: [1, 1+κ] para C·A ∈ [0,1]

EXPOENTE: Quão agressiva é a amplificação
  - O·S = Contexto de exploração
  - Range: [0, 1]
  - 0 → Sem amplificação (base^0 = 1)
  - 1 → Amplificação máxima (base^1 = base)
```

### Interpretação Intuitiva

Pense em CAOS⁺ como um **acelerador de aprendizado**:

- **Motor (Base)**: Potência disponível = qualidade do sistema (C·A) × ganho (κ)
- **Pedal (Expoente)**: Quanto apertar = contexto de exploração (O·S)

**Exemplos**:
- Motor fraco + pedal fundo = pouco efeito
- Motor forte + pedal suave = aceleração controlada
- Motor forte + pedal fundo = **aceleração máxima!**

---

## Componentes Detalhados

### C - Consistency (Consistência) [0, 1]

**O Que Mede**: Confiabilidade das predições do sistema.

**Como Calcular**:
```
C = w₁·pass@k + w₂·(1-ECE) + w₃·v_ext
```

**Sub-métricas**:

#### 1. pass@k (Taxa de Autoconsistência)
- **Definição**: Probabilidade de gerar pelo menos 1 resposta correta em k tentativas
- **Como medir**: Gerar k amostras e verificar se pelo menos 1 está correta
- **Valores típicos**: 0.85-0.95 para sistemas calibrados
- **Peso sugerido**: 0.4

```python
# Exemplo de cálculo
num_correct = 0
k = 10
for i in range(k):
    output = model.generate(prompt)
    if verify(output):
        num_correct += 1

pass_at_k = 1.0 - (1.0 - num_correct/k) ** k  # Estimativa não-enviesada
```

#### 2. ECE - Expected Calibration Error
- **Definição**: Diferença entre confiança e acurácia
- **Como medir**: Dividir predições em bins por confiança, calcular |conf - acc|
- **Valores bons**: ECE < 0.05 (< 5% de erro)
- **Peso sugerido**: 0.3
- **Nota**: Invertemos para métrica positiva: (1-ECE)

```python
# Exemplo simplificado
ece = expected_calibration_error(predictions, confidences, num_bins=10)
ece_normalized = min(1.0, ece)  # Clamp em [0, 1]
consistency_component = 1.0 - ece_normalized
```

#### 3. v_ext (Verificação Externa)
- **Definição**: Score de validação por oracles, testes formais, ou humanos
- **Como medir**: Taxa de aprovação em testes externos
- **Valores típicos**: 0.80-0.90
- **Peso sugerido**: 0.3

```python
# Exemplo
external_tests_passed = 88
external_tests_total = 100
v_ext = external_tests_passed / external_tests_total  # 0.88
```

**Implementação**:
```python
from penin.core.caos import ConsistencyMetrics

consistency = ConsistencyMetrics(
    pass_at_k=0.92,
    ece=0.008,                    # 0.8% error
    external_verification=0.88,
    weight_pass=0.4,
    weight_ece=0.3,
    weight_external=0.3
)

C = consistency.compute_c()
print(f"C = {C:.3f}")  # C ≈ 0.930
```

**Interpretação**:
- **C > 0.8**: Sistema confiável, pode explorar mais agressivamente
- **C = 0.5-0.8**: Sistema moderado, exploração equilibrada
- **C < 0.5**: Sistema inconsistente, precisa calibrar antes de explorar

---

### A - Autoevolution (Autoevolução) [0, 1]

**O Que Mede**: Eficiência do aprendizado (ganho por custo).

**Como Calcular**:
```
A_raw = ΔL∞⁺ / (Cost_norm + ε)
A = min(A_raw / max_a, 1.0)  # Normalizar para [0, 1]
```

**Sub-métricas**:

#### 1. ΔL∞⁺ (Ganho de Performance)
- **Definição**: Melhoria na métrica L∞ (meta-score agregada)
- **Como medir**: L∞_new - L∞_old
- **Valores típicos**: 0.01-0.10 (1%-10% de ganho)
- **Nota**: Só considera ganhos positivos: max(0, ΔL∞)

#### 2. Cost_norm (Custo Normalizado)
- **Definição**: Recursos gastos (tempo, tokens, energia)
- **Como medir**: Custo atual / Custo budget
- **Valores típicos**: 0.05-0.20 (5%-20% do budget)

**Implementação**:
```python
from penin.core.caos import AutoevolutionMetrics

autoevolution = AutoevolutionMetrics(
    delta_linf=0.06,        # 6% de ganho
    cost_normalized=0.15,   # 15% do budget
    max_a=10.0              # Clamp antes de normalizar
)

A = autoevolution.compute_a()
print(f"A = {A:.3f}")  # A ≈ 0.040 (normalizado)
```

**Interpretação**:
- **A > 0.6**: Aprendizado eficiente, bom ROI
- **A = 0.3-0.6**: Aprendizado moderado
- **A < 0.3**: Aprendizado ineficiente ou estagnado

---

### O - Unknowable (Incognoscível) [0, 1]

**O Que Mede**: Incerteza e necessidade de exploração.

**Como Calcular**:
```
O = w_epi·epistemic + w_ood·ood_score + w_ens·ensemble_disagreement
```

**Sub-métricas**:

#### 1. Epistemic Uncertainty (Incerteza Epistêmica)
- **Definição**: Incerteza do modelo sobre as predições
- **Como medir**: 
  - Entropia: H(p) = -Σ p_i log p_i
  - Mutual Information em Bayesian NNs
  - Variância em dropout variational
- **Valores típicos**: 0.2-0.5
- **Peso sugerido**: 0.4

```python
# Exemplo com entropia
probs = softmax(logits)
entropy = -np.sum(probs * np.log(probs + 1e-10))
entropy_normalized = entropy / np.log(num_classes)  # Normalizar
```

#### 2. OOD Score (Out-of-Distribution)
- **Definição**: Distância de distribuição de treino
- **Como medir**:
  - Mahalanobis distance
  - KL divergence
  - Reconstruction error (autoencoders)
- **Valores típicos**: 0.1-0.4
- **Peso sugerido**: 0.3

#### 3. Ensemble Disagreement
- **Definição**: Variância entre predições de múltiplos modelos
- **Como medir**: Std ou variance entre ensemble
- **Valores típicos**: 0.15-0.35
- **Peso sugerido**: 0.3

**Implementação**:
```python
from penin.core.caos import IncognoscibleMetrics

incognoscible = IncognoscibleMetrics(
    epistemic_uncertainty=0.35,
    ood_score=0.28,
    ensemble_disagreement=0.30,
    weight_epistemic=0.4,
    weight_ood=0.3,
    weight_ensemble=0.3
)

O = incognoscible.compute_o()
print(f"O = {O:.3f}")  # O ≈ 0.314
```

**Interpretação**:
- **O > 0.6**: Alta incerteza → precisa EXPLORAR mais
- **O = 0.3-0.6**: Incerteza moderada → balancear exploração/exploração
- **O < 0.3**: Baixa incerteza → pode EXPLOITAR (exploit)

---

### S - Silence (Silêncio) [0, 1]

**O Que Mede**: Qualidade do sinal (anti-ruído).

**Como Calcular**:
```
S = v₁·(1-noise) + v₂·(1-redund) + v₃·(1-entropy)
```

Ponderação sugerida: **v₁:v₂:v₃ = 2:1:1** (ruído é mais crítico)

**Sub-métricas**:

#### 1. Anti-Noise (Anti-Ruído)
- **Definição**: Inverso da proporção de ruído no sinal
- **Como medir**: 1 - (ruído / sinal_total)
- **Valores bons**: noise < 0.1 → anti-noise > 0.9
- **Peso sugerido**: 0.5 (2/4)

#### 2. Anti-Redundancy (Anti-Redundância)
- **Definição**: Inverso da proporção de informação duplicada
- **Como medir**: 1 - (redundância / informação_total)
- **Valores bons**: redundancy < 0.15 → anti-redundancy > 0.85
- **Peso sugerido**: 0.25 (1/4)

#### 3. Anti-Entropy (Anti-Entropia)
- **Definição**: Inverso da desordem/imprevisibilidade
- **Como medir**: 1 - (entropia / entropia_max)
- **Valores bons**: entropy < 0.2 → anti-entropy > 0.8
- **Peso sugerido**: 0.25 (1/4)

**Implementação**:
```python
from penin.core.caos import SilenceMetrics

silence = SilenceMetrics(
    noise_ratio=0.08,         # 8% ruído
    redundancy_ratio=0.12,    # 12% redundância
    entropy_normalized=0.18,  # 18% entropia
    weight_noise=0.5,         # 2:1:1
    weight_redundancy=0.25,
    weight_entropy=0.25
)

S = silence.compute_s()
print(f"S = {S:.3f}")  # S ≈ 0.885
```

**Interpretação**:
- **S > 0.8**: Sinal limpo, alta confiança
- **S = 0.5-0.8**: Sinal moderado
- **S < 0.5**: Sinal ruidoso, baixa confiança

---

### κ - Kappa (Ganho Base)

**O Que Controla**: Intensidade da amplificação.

**Range**: κ ≥ 20 (padrão), típico: [10, 100]

**Efeito na Amplificação**:

| κ    | Tipo         | Range típico CAOS⁺ | Uso                    |
|------|--------------|-------------------|------------------------|
| 10   | Conservador  | 1.0 - 2.5×        | Ambientes estáveis     |
| 20   | **Padrão**   | 1.0 - 3.5×        | **Recomendado**        |
| 50   | Agressivo    | 1.0 - 5.0×        | Evolução rápida        |
| 100  | Extremo      | 1.0 - 7.0×        | Exploração máxima      |

**Auto-tuning**: κ pode ser otimizado via **Equação 10** (bandit meta-optimization).

```python
from penin.core.caos import CAOSConfig

# Configuração conservadora
config_conservative = CAOSConfig(kappa=10.0)

# Configuração padrão (recomendada)
config_default = CAOSConfig(kappa=20.0)

# Configuração agressiva
config_aggressive = CAOSConfig(kappa=50.0)
```

---

## Guia de Implementação

### Quick Start (5 minutos)

```python
from penin.core.caos import compute_caos_plus_exponential

# 1. Definir componentes (valores já calculados)
C = 0.88  # Alta consistência
A = 0.40  # Autoevolução moderada
O = 0.35  # Incerteza moderada
S = 0.82  # Alto silêncio
kappa = 20.0

# 2. Calcular CAOS⁺
caos_plus = compute_caos_plus_exponential(C, A, O, S, kappa)

# 3. Usar para modular taxa de aprendizado
alpha_base = 0.01
alpha_effective = alpha_base * caos_plus

print(f"CAOS⁺: {caos_plus:.4f}")
print(f"α_eff: {alpha_effective:.6f}")
```

### Implementação Completa (Produção)

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

# 1. Definir métricas estruturadas
consistency = ConsistencyMetrics(
    pass_at_k=0.92,
    ece=0.008,
    external_verification=0.88
)

autoevolution = AutoevolutionMetrics(
    delta_linf=0.06,
    cost_normalized=0.15
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

# 2. Configurar com EMA para estabilidade temporal
config = CAOSConfig(
    kappa=25.0,
    ema_half_life=5,
    caos_min=1.0,
    caos_max=10.0
)

# 3. Criar estado para tracking
state = CAOSState()

# 4. Computar CAOS⁺
caos_plus, details = compute_caos_plus_complete(
    consistency, autoevolution, incognoscible, silence,
    config, state
)

# 5. Usar resultados
print(f"CAOS⁺: {caos_plus:.4f}")
print(f"Componentes: {details['components_raw']}")
print(f"Estabilidade: {details['state_stability']:.3f}")

# 6. Registrar para auditoria (WORM ledger)
worm_entry = {
    "timestamp": time.time(),
    "caos_plus": caos_plus,
    **details
}
```

### Loop de Treinamento

```python
# Setup inicial
config = CAOSConfig(kappa=20.0, ema_half_life=5)
state = CAOSState()
alpha_base = 0.01

for epoch in range(num_epochs):
    # 1. Coletar métricas da época
    consistency = get_consistency_metrics(epoch)
    autoevolution = get_autoevolution_metrics(epoch)
    incognoscible = get_incognoscible_metrics(epoch)
    silence = get_silence_metrics(epoch)
    
    # 2. Calcular CAOS⁺ (com EMA automático)
    caos_plus, details = compute_caos_plus_complete(
        consistency, autoevolution, incognoscible, silence,
        config, state
    )
    
    # 3. Modular taxa de aprendizado
    alpha_effective = alpha_base * caos_plus
    
    # 4. Treinar com α_eff
    train_step(model, alpha_effective)
    
    # 5. Log para monitoramento
    logger.log({
        "epoch": epoch,
        "caos_plus": caos_plus,
        "alpha_effective": alpha_effective,
        "stability": details['state_stability']
    })
```

---

## Exemplos Práticos

### Exemplo 1: Exploração em Território Desconhecido

**Cenário**: Sistema entrando em novo domínio, precisa explorar.

```python
# Métricas típicas de exploração
consistency = ConsistencyMetrics(
    pass_at_k=0.55,         # Baixa (incerto)
    ece=0.08,               # Alta (mal calibrado)
    external_verification=0.60
)

autoevolution = AutoevolutionMetrics(
    delta_linf=0.03,        # Ganho baixo
    cost_normalized=0.20    # Custo alto (explorando)
)

incognoscible = IncognoscibleMetrics(
    epistemic_uncertainty=0.75,  # ALTA incerteza
    ood_score=0.65,             # ALTA OOD
    ensemble_disagreement=0.70   # ALTA disagreement
)

silence = SilenceMetrics(
    noise_ratio=0.15,       # Mais ruído
    redundancy_ratio=0.18,
    entropy_normalized=0.25
)

caos, details = compute_caos_plus_complete(
    consistency, autoevolution, incognoscible, silence
)

# Resultado esperado:
# C baixo × A baixo = base baixa (~2-3)
# O alto × S moderado = expoente moderado-alto (~0.4-0.5)
# CAOS⁺ ≈ 1.5-2.0 (amplificação moderada para exploração)
```

### Exemplo 2: Exploração em Território Conhecido

**Cenário**: Sistema refinando performance em domínio familiar.

```python
# Métricas típicas de exploração
consistency = ConsistencyMetrics(
    pass_at_k=0.92,         # ALTA (confiante)
    ece=0.008,              # Baixa (bem calibrado)
    external_verification=0.88
)

autoevolution = AutoevolutionMetrics(
    delta_linf=0.08,        # Ganho moderado-alto
    cost_normalized=0.12    # Custo baixo (eficiente)
)

incognoscible = IncognoscibleMetrics(
    epistemic_uncertainty=0.20,  # BAIXA incerteza
    ood_score=0.15,             # BAIXA OOD
    ensemble_disagreement=0.18   # BAIXA disagreement
)

silence = SilenceMetrics(
    noise_ratio=0.05,       # Baixo ruído
    redundancy_ratio=0.08,
    entropy_normalized=0.12
)

caos, details = compute_caos_plus_complete(
    consistency, autoevolution, incognoscible, silence
)

# Resultado esperado:
# C alto × A alto = base alta (~6-8)
# O baixo × S alto = expoente baixo (~0.15-0.25)
# CAOS⁺ ≈ 1.3-1.7 (amplificação moderada para exploração)
```

### Exemplo 3: Sweet Spot (Máxima Amplificação)

**Cenário**: Sistema aprendendo rapidamente em território parcialmente conhecido.

```python
# Métricas do sweet spot
consistency = ConsistencyMetrics(
    pass_at_k=0.88,
    ece=0.012,
    external_verification=0.85
)

autoevolution = AutoevolutionMetrics(
    delta_linf=0.10,        # ALTO ganho
    cost_normalized=0.10    # Custo moderado
)

incognoscible = IncognoscibleMetrics(
    epistemic_uncertainty=0.55,  # Incerteza moderada-alta
    ood_score=0.45,
    ensemble_disagreement=0.50
)

silence = SilenceMetrics(
    noise_ratio=0.08,
    redundancy_ratio=0.10,
    entropy_normalized=0.15
)

caos, details = compute_caos_plus_complete(
    consistency, autoevolution, incognoscible, silence
)

# Resultado esperado:
# C alto × A alto = base MUITO alta (~10-15)
# O moderado-alto × S alto = expoente moderado-alto (~0.4-0.6)
# CAOS⁺ ≈ 3.0-4.5 (MÁXIMA amplificação! 🚀)
```

---

## Best Practices

### 1. Use Suavização Temporal (EMA)

**Problema**: Métricas oscilam entre iterações.

**Solução**: Configure `ema_half_life`.

```python
config = CAOSConfig(
    kappa=20.0,
    ema_half_life=5  # Suavizar em 5 iterações
)
state = CAOSState()

# EMA é aplicado automaticamente
for epoch in range(num_epochs):
    caos, _ = compute_caos_plus_complete(..., config, state)
    # state é atualizado in-place com EMA
```

**Guidelines**:
- `ema_half_life = 3`: Resposta rápida (ambientes dinâmicos)
- `ema_half_life = 5`: **Balanceado (recomendado)**
- `ema_half_life = 10`: Resposta lenta (ambientes estáveis)

### 2. Configure Clamps Apropriados

```python
config = CAOSConfig(
    kappa=20.0,
    kappa_min=10.0,    # Nunca menos que 10
    kappa_max=100.0,   # Nunca mais que 100
    caos_min=1.0,      # CAOS⁺ sempre ≥ 1
    caos_max=10.0,     # Limitar explosão
)
```

### 3. Use Log-space para Comparações

```python
config = CAOSConfig(use_log_space=True)
caos, details = compute_caos_plus_complete(..., config)

log_caos = details['caos_plus_log']
# Útil para:
# - Plotting
# - Ranking de challengers
# - Análise estatística
```

### 4. Registre Tudo para Auditoria

```python
caos, details = compute_caos_plus_complete(...)

# Details contém TODAS métricas intermediárias
worm_entry = {
    "timestamp": time.time(),
    "caos_plus": caos,
    "components_raw": details['components_raw'],
    "components_smoothed": details['components_smoothed'],
    "kappa": details['kappa'],
    "state_stability": details['state_stability'],
    # ... etc
}

# Registrar no WORM ledger (write-once-read-many)
worm_ledger.append(worm_entry)
```

### 5. Monitore Estabilidade

```python
_, details = compute_caos_plus_complete(...)

stability = details['state_stability']

if stability < 0.95:
    print("⚠️  CAOS⁺ instável, considere aumentar ema_half_life")
elif stability > 0.99:
    print("✅ CAOS⁺ muito estável")
```

---

## Troubleshooting

### Problema 1: CAOS⁺ sempre próximo de 1.0

**Sintoma**: `caos_plus ≈ 1.0` (sem amplificação)

**Causas possíveis**:

1. **C·A muito baixo** (base ≈ 1):
   ```python
   # Debug
   C = details['components_smoothed']['C']
   A = details['components_smoothed']['A']
   print(f"C={C:.3f}, A={A:.3f}, C·A={C*A:.3f}")
   
   # Se C·A < 0.1:
   # → Sistema tem baixa qualidade
   # → Verificar métricas de consistência e autoevolução
   ```

2. **O·S muito baixo** (expoente ≈ 0):
   ```python
   # Debug
   O = details['components_smoothed']['O']
   S = details['components_smoothed']['S']
   print(f"O={O:.3f}, S={S:.3f}, O·S={O*S:.3f}")
   
   # Se O·S < 0.1:
   # → Sistema tem baixa incerteza E baixo silêncio
   # → Verificar métricas de incognoscível
   ```

**Soluções**:
- Verificar qualidade das métricas de entrada
- Ajustar pesos nas métricas
- Considerar usar κ maior (se apropriado)

### Problema 2: CAOS⁺ oscila muito

**Sintoma**: `caos_plus` varia muito entre iterações

**Causa**: Métricas de entrada oscilando, sem suavização

**Soluções**:

1. **Aumentar EMA half-life**:
   ```python
   config = CAOSConfig(ema_half_life=10)  # Mais suavização
   ```

2. **Verificar qualidade das métricas**:
   ```python
   # Plotar métricas raw vs smoothed
   raw = details['components_raw']
   smoothed = details['components_smoothed']
   
   # Se raw oscila muito:
   # → Problema nas métricas de entrada
   # → Melhorar coleta de métricas
   ```

### Problema 3: CAOS⁺ sempre no máximo (caos_max)

**Sintoma**: `caos_plus == caos_max` (saturando)

**Causas**:

1. **κ muito alto**:
   ```python
   kappa = details['kappa']
   if kappa > 50:
       print("κ muito alto, considere reduzir")
   ```

2. **caos_max muito baixo**:
   ```python
   config = CAOSConfig(caos_max=20.0)  # Aumentar teto
   ```

3. **C·A E O·S ambos muito altos**:
   ```python
   # Isso é na verdade DESEJÁVEL em cenários de sweet spot!
   # Mas se acontece sempre:
   # → Verificar se métricas estão super-otimistas
   ```

### Problema 4: Componentes calculados parecem errados

**Debug Completo**:

```python
def debug_caos(details):
    """Função helper para debug completo"""
    print("=== CAOS⁺ DEBUG ===")
    
    # 1. Métricas de entrada
    print("\n1. Métricas de Entrada:")
    for component, metrics in details['metrics_input'].items():
        print(f"  {component}:")
        for k, v in metrics.items():
            print(f"    {k}: {v:.4f}")
    
    # 2. Componentes calculados
    print("\n2. Componentes CAOS:")
    raw = details['components_raw']
    smoothed = details['components_smoothed']
    print(f"  Raw:      C={raw['C']:.3f}, A={raw['A']:.3f}, "
          f"O={raw['O']:.3f}, S={raw['S']:.3f}")
    print(f"  Smoothed: C={smoothed['C']:.3f}, A={smoothed['A']:.3f}, "
          f"O={smoothed['O']:.3f}, S={smoothed['S']:.3f}")
    
    # 3. Cálculo CAOS⁺
    print("\n3. Cálculo CAOS⁺:")
    C, A = smoothed['C'], smoothed['A']
    O, S = smoothed['O'], smoothed['S']
    kappa = details['kappa']
    base = 1 + kappa * C * A
    exponent = O * S
    print(f"  Base = 1 + {kappa}×{C:.3f}×{A:.3f} = {base:.4f}")
    print(f"  Exponent = {O:.3f}×{S:.3f} = {exponent:.4f}")
    print(f"  CAOS⁺_raw = {base:.4f}^{exponent:.4f} = {details['caos_plus_raw']:.4f}")
    print(f"  CAOS⁺_clamped = {details['caos_plus_clamped']:.4f}")
    print(f"  CAOS⁺_final = {details['caos_plus_final']:.4f}")
    
    # 4. Estado
    print("\n4. Estado:")
    print(f"  Updates: {details['state_update_count']}")
    print(f"  Stability: {details['state_stability']:.4f}")

# Uso
caos, details = compute_caos_plus_complete(...)
debug_caos(details)
```

---

## FAQ

### Q1: Quando usar `compute_caos_plus_exponential` vs `compute_caos_plus_complete`?

**A**: 
- Use `compute_caos_plus_exponential` quando já tem C, A, O, S calculados
- Use `compute_caos_plus_complete` para pipeline completo com métricas estruturadas

### Q2: Como escolher κ (kappa)?

**A**: 
- Padrão: κ = 20 (recomendado para a maioria dos casos)
- Conservador: κ = 10-15 (ambientes sensíveis)
- Agressivo: κ = 30-50 (evolução rápida)
- Extremo: κ = 50-100 (exploração máxima, use com cuidado)

### Q3: O que fazer se CAOS⁺ é sempre 1.0?

**A**: Veja [Problema 1 em Troubleshooting](#problema-1-caos-sempre-próximo-de-10)

### Q4: Posso usar CAOS⁺ sem EMA?

**A**: Sim, mas não recomendado:
```python
config = CAOSConfig(ema_half_life=0)  # Desabilita EMA
```
Isso remove suavização temporal, causando mais oscilações.

### Q5: Como interpretar `state_stability`?

**A**:
- `> 0.99`: Muito estável (bom)
- `0.95-0.99`: Estável (ok)
- `< 0.95`: Instável (considere mais suavização)

### Q6: CAOS⁺ pode ser > 10.0?

**A**: Por padrão não (clamped em `caos_max=10.0`), mas você pode configurar:
```python
config = CAOSConfig(caos_max=20.0)  # Permitir até 20×
```

### Q7: Qual é a diferença entre `compute_caos_plus` e `phi_caos`?

**A**:
- `compute_caos_plus`: Wrapper de compatibilidade, retorna tupla `(phi, details)`
- `phi_caos`: Fórmula com saturação tanh, output em [0, 1)
- **Recomendado**: Use `compute_caos_plus_exponential` para casos novos

### Q8: Como fazer auto-tuning de κ?

**A**: Use a Equação 10 (bandit meta-optimization). Exemplo simplificado:
```python
# Testar diferentes κ
kappas = [10, 20, 30, 50]
performances = []

for kappa in kappas:
    config = CAOSConfig(kappa=kappa)
    perf = train_and_evaluate(config)
    performances.append(perf)

# Escolher melhor κ
best_kappa = kappas[np.argmax(performances)]
```

### Q9: CAOS⁺ funciona para reinforcement learning?

**A**: Sim! Use:
- C: Taxa de sucesso, consistência de política
- A: Melhoria de reward / custo
- O: Incerteza sobre transições
- S: Qualidade de observações

### Q10: Posso usar CAOS⁺ para seleção de modelos?

**A**: Sim! Calcule CAOS⁺ para cada modelo e ranqueie:
```python
models_caos = []
for model in candidate_models:
    caos = compute_caos_for_model(model)
    models_caos.append((model, caos))

# Ordenar por CAOS⁺ (maior = melhor)
models_caos.sort(key=lambda x: x[1], reverse=True)
best_model = models_caos[0][0]
```

---

## Recursos Adicionais

### Código Fonte
- **Implementação canônica**: `penin/core/caos.py`
- **Exemplos executáveis**: `python penin/core/caos.py`
- **Testes**: `tests/test_caos.py`

### Documentação
- **Equações**: `docs/equations.md` (Seção 3)
- **Arquitetura**: `docs/architecture.md`
- **Guia completo**: Este arquivo

### Papers e Referências
- PENIN-Ω Master Equation (Seção 1 de equations.md)
- SR-Ω∞ Reflexive Score (Seção 4 de equations.md)
- ACFA League (docs/architecture.md)

---

## Conclusão

CAOS⁺ é um componente central do sistema PENIN-Ω que permite evolução adaptativa
inteligente. Ao balancear qualidade (C·A) e contexto (O·S), o sistema pode:

✅ Explorar eficientemente em territórios desconhecidos  
✅ Explorar eficientemente em territórios conhecidos  
✅ Adaptar-se automaticamente a mudanças  
✅ Manter auditabilidade completa  

Para começar rapidamente, veja a seção [Guia de Implementação](#guia-de-implementação).

Para casos de uso avançados, veja [Exemplos Práticos](#exemplos-práticos).

Para problemas, veja [Troubleshooting](#troubleshooting).

---

**Versão**: 1.0  
**Última atualização**: 2024  
**Autor**: PENIN-Ω Team  
**Licença**: Apache 2.0
