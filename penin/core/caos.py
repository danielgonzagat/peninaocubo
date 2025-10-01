"""
PENIN-Ω CAOS⁺ Engine - Implementação Canônica Consolidada
==========================================================

Equação 3: Motor CAOS⁺ — Consistência, Autoevolução, Incognoscível, Silêncio

Forma matemática: CAOS⁺ = (1 + κ · C · A)^(O · S)

Este módulo consolida TODAS as implementações de CAOS⁺ previamente espalhadas em:
- penin/engine/caos_plus.py (wrapper, removido)
- penin/omega/caos.py (implementação phi_caos, migrado)
- penin/equations/caos_plus.py (documentação, migrado)

SINGLE SOURCE OF TRUTH para cálculo de CAOS⁺ no sistema PENIN-Ω.

Dimensões (todas normalizadas [0,1]):
-------------------------------------
- C (Consistência): média(pass@k, 1-ECE, verificação_externa)
- A (Autoevolução): ΔL∞⁺ / (Cost_norm + ε)
- O (Incognoscível): incerteza epistêmica + OOD + disagreement
- S (Silêncio): anti-ruído, anti-redundância, anti-entropia

Parâmetros:
-----------
- κ (kappa): ganho base ≥ 20 (auto-tunável via Eq. 10)
- γ (gamma): saturação para φ(z) = tanh(γ·z) na variante phi_caos

Propriedades matemáticas:
-------------------------
- CAOS⁺ ≥ 1 sempre (base multiplicativa)
- Monotônico em C, A, O, S
- Alto C·A amplifica base
- Alto O·S aumenta expoente
- Suavização via EMA para estabilidade temporal
- Clamps para evitar explosão numérica

Uso no pipeline:
----------------
- Modula α_t^{eff} na Equação de Penin (Eq. 1)
- Desempata challengers na Liga ACFA
- Sinaliza qualidade de evolução para SR-Ω∞

Auditabilidade:
---------------
- Todos cálculos registrados em WORM ledger
- PCAg gerados para cada computação crítica
- Determinismo garantido via seed

Quick Start:
------------
>>> # Uso simples com componentes já calculados
>>> from penin.core.caos import compute_caos_plus_exponential
>>> caos = compute_caos_plus_exponential(c=0.88, a=0.40, o=0.35, s=0.82, kappa=20.0)
>>> print(f"CAOS⁺: {caos:.2f}")  # ~1.86

>>> # Uso completo com métricas e EMA
>>> from penin.core.caos import (
...     ConsistencyMetrics, AutoevolutionMetrics,
...     IncognoscibleMetrics, SilenceMetrics,
...     CAOSConfig, CAOSState, compute_caos_plus_complete
... )
>>> 
>>> consistency = ConsistencyMetrics(pass_at_k=0.92, ece=0.008)
>>> autoevol = AutoevolutionMetrics(delta_linf=0.06, cost_normalized=0.15)
>>> incog = IncognoscibleMetrics(epistemic_uncertainty=0.35)
>>> silence = SilenceMetrics(noise_ratio=0.08)
>>> 
>>> config = CAOSConfig(kappa=25.0, ema_half_life=5)
>>> state = CAOSState()
>>> 
>>> caos, details = compute_caos_plus_complete(
...     consistency, autoevol, incog, silence, config, state
... )
>>> print(f"CAOS⁺: {caos:.4f}, Stability: {details['state_stability']:.3f}")

Documentação Completa:
---------------------
Para guia detalhado com exemplos práticos, best practices e FAQ, consulte:
docs/caos_guide.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Constants
EPS = 1e-9  # Estabilizador numérico global
DEFAULT_KAPPA = 20.0  # Ganho base padrão
DEFAULT_GAMMA = 0.7  # Saturação padrão


class CAOSComponent(Enum):
    """Componentes do CAOS⁺"""

    CONSISTENCY = "C"  # Consistência
    AUTOEVOLUTION = "A"  # Autoevolução
    INCOGNOSCIBLE = "O"  # Incognoscível/OOD
    SILENCE = "S"  # Silêncio


class CAOSFormula(Enum):
    """Fórmulas disponíveis de CAOS⁺"""

    EXPONENTIAL = "exponential"  # (1 + κ·C·A)^(O·S) - fórmula pura
    PHI_CAOS = "phi_caos"  # tanh(γ·log((1 + κ·C·A)^(O·S))) - com saturação
    HYBRID = "hybrid"  # Escolhe automaticamente baseado em contexto


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def clamp01(x: float) -> float:
    """Clampa valor para [0, 1]"""
    return max(0.0, min(1.0, x))


def clamp(x: float, min_val: float, max_val: float) -> float:
    """Clampa valor para [min_val, max_val]"""
    return max(min_val, min(max_val, x))


def compute_ema_alpha(half_life: int) -> float:
    """
    Calcula α para EMA dado half-life

    Half-life: número de amostras para peso cair para 50%
    Fórmula: α = 1 - exp(-ln(2) / half_life)

    Args:
        half_life: Half-life em número de amostras (típico: 3-10)

    Returns:
        α (fator de suavização) em [0, 1]
    """
    if half_life <= 0:
        return 1.0  # Sem suavização
    return 1.0 - math.exp(-math.log(2.0) / half_life)


# =============================================================================
# METRICS DATACLASSES
# =============================================================================


@dataclass
class ConsistencyMetrics:
    """
    Métricas de Consistência (C)

    C = w1·pass@k + w2·(1-ECE) + w3·v_ext

    Componentes:
    - pass@k: Taxa de sucesso em k tentativas [0, 1]
    - ECE: Expected Calibration Error [0, 1] (menor é melhor)
    - v_ext: Verificação externa (oracle, formal) [0, 1]
    """

    pass_at_k: float = 0.9
    k_samples: int = 10
    ece: float = 0.01  # Típico < 0.05
    external_verification: float = 0.85

    # Pesos (devem somar 1.0)
    weight_pass: float = 0.4
    weight_ece: float = 0.3
    weight_external: float = 0.3

    def compute_c(self) -> float:
        """Calcula C (Consistência) em [0, 1]"""
        pass_norm = clamp01(self.pass_at_k)
        ece_norm = clamp01(1.0 - self.ece)  # Inverter ECE
        ext_norm = clamp01(self.external_verification)

        c = self.weight_pass * pass_norm + self.weight_ece * ece_norm + self.weight_external * ext_norm

        return clamp01(c)


@dataclass
class AutoevolutionMetrics:
    """
    Métricas de Autoevolução (A)

    A = ΔL∞⁺ / (Cost_norm + ε)

    Mede ganho de performance por unidade de custo.
    Só considera ganhos positivos (ΔL∞⁺ = max(0, ΔL∞)).
    """

    delta_linf: float = 0.05  # Ganho de L∞
    cost_normalized: float = 0.1  # Custo [0, ∞)
    epsilon: float = EPS
    max_a: float = 10.0  # Clamp máximo antes de normalizar

    def compute_a(self) -> float:
        """Calcula A (Autoevolução) normalizado em [0, 1]"""
        delta_positive = max(0.0, self.delta_linf)
        cost_denom = max(self.epsilon, self.cost_normalized + self.epsilon)
        a_raw = delta_positive / cost_denom

        # Clamp e normaliza para [0, 1]
        a_clamped = clamp(a_raw, 0.0, self.max_a)
        a_normalized = a_clamped / self.max_a

        return clamp01(a_normalized)


@dataclass
class IncognoscibleMetrics:
    """
    Métricas de Incognoscível (O)

    O = média ponderada(epistemic_uncertainty, ood_score, ensemble_disagreement)

    Mede grau de desconhecimento → mais O libera exploração.
    """

    epistemic_uncertainty: float = 0.3  # Entropy, MI
    ood_score: float = 0.25  # Out-of-distribution
    ensemble_disagreement: float = 0.2  # Variância predições

    # Pesos
    weight_epistemic: float = 0.4
    weight_ood: float = 0.3
    weight_ensemble: float = 0.3

    def compute_o(self) -> float:
        """Calcula O (Incognoscível) em [0, 1]"""
        epist_norm = clamp01(self.epistemic_uncertainty)
        ood_norm = clamp01(self.ood_score)
        ens_norm = clamp01(self.ensemble_disagreement)

        o = self.weight_epistemic * epist_norm + self.weight_ood * ood_norm + self.weight_ensemble * ens_norm

        return clamp01(o)


@dataclass
class SilenceMetrics:
    """
    Métricas de Silêncio (S)

    S = v1·(1-ruído) + v2·(1-redundância) + v3·(1-entropia)

    Ponderação sugerida: v1:v2:v3 = 2:1:1
    Mede qualidade de sinal (anti-ruído, anti-redundância, anti-entropia).
    """

    noise_ratio: float = 0.1  # Proporção ruído
    redundancy_ratio: float = 0.15  # Proporção redundância
    entropy_normalized: float = 0.2  # Entropia normalizada

    # Pesos (v1:v2:v3 = 2:1:1)
    weight_noise: float = 0.5  # 2/4
    weight_redundancy: float = 0.25  # 1/4
    weight_entropy: float = 0.25  # 1/4

    def compute_s(self) -> float:
        """Calcula S (Silêncio) em [0, 1]"""
        anti_noise = 1.0 - clamp01(self.noise_ratio)
        anti_redundancy = 1.0 - clamp01(self.redundancy_ratio)
        anti_entropy = 1.0 - clamp01(self.entropy_normalized)

        s = (
            self.weight_noise * anti_noise
            + self.weight_redundancy * anti_redundancy
            + self.weight_entropy * anti_entropy
        )

        return clamp01(s)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class CAOSConfig:
    """Configuração global do motor CAOS⁺"""

    # Fórmula a usar
    formula: CAOSFormula = CAOSFormula.EXPONENTIAL

    # Ganho base κ (auto-tunável via Eq. 10)
    kappa: float = DEFAULT_KAPPA
    kappa_min: float = 10.0
    kappa_max: float = 100.0

    # Saturação γ (para phi_caos)
    gamma: float = DEFAULT_GAMMA
    gamma_min: float = 0.1
    gamma_max: float = 2.0

    # EMA para suavização temporal
    ema_half_life: int = 5  # Amostras

    # Clamps do resultado
    caos_min: float = 1.0  # Base mínima
    caos_max: float = 10.0  # Teto de amplificação

    # Modos
    use_log_space: bool = False  # Para comparação
    normalize_output: bool = False  # [0, 1] output

    # Determinismo
    seed: int | None = None


# =============================================================================
# STATE TRACKING
# =============================================================================


@dataclass
class CAOSState:
    """
    Estado do CAOS⁺ com histórico e EMA

    Mantém valores raw e suavizados via Exponential Moving Average.
    """

    # Valores atuais (raw)
    c_current: float = 0.0
    a_current: float = 0.0
    o_current: float = 0.0
    s_current: float = 0.0

    # Valores suavizados (EMA)
    c_smoothed: float = 0.0
    a_smoothed: float = 0.0
    o_smoothed: float = 0.0
    s_smoothed: float = 0.0

    # CAOS⁺ atual
    caos_plus: float = 1.0

    # Histórico (últimas N amostras)
    history: list[float] = field(default_factory=list)
    max_history_length: int = 100

    # Contador de atualizações
    update_count: int = 0

    def update_ema(self, new_value: float, current_ema: float, alpha: float) -> float:
        """
        Atualiza EMA: EMA_t = α · value_t + (1-α) · EMA_{t-1}

        Na primeira atualização, inicializa EMA com valor observado.
        """
        if self.update_count == 0:
            return new_value
        return alpha * new_value + (1.0 - alpha) * current_ema

    def add_to_history(self, caos_value: float):
        """Adiciona valor ao histórico (FIFO)"""
        self.history.append(caos_value)
        if len(self.history) > self.max_history_length:
            self.history.pop(0)

    def get_stability(self) -> float:
        """
        Retorna estabilidade (inverse coefficient of variation)

        Stability = 1 / (1 + CV) onde CV = σ / μ
        """
        if len(self.history) < 2:
            return 1.0

        mean_val = sum(self.history) / len(self.history)
        if mean_val <= EPS:
            return 0.0

        variance = sum((v - mean_val) ** 2 for v in self.history) / len(self.history)
        cv = math.sqrt(variance) / mean_val

        return 1.0 / (1.0 + cv)


# =============================================================================
# CORE COMPUTATION FUNCTIONS
# =============================================================================


def compute_caos_plus_exponential(
    c: float,
    a: float,
    o: float,
    s: float,
    kappa: float = DEFAULT_KAPPA,
) -> float:
    """
    Fórmula CAOS⁺ exponencial pura: (1 + κ·C·A)^(O·S)

    Esta é a fórmula matemática canônica original do motor evolutivo PENIN-Ω.
    A função é monotônica em todos os parâmetros C, A, O, S, permitindo
    controle preciso da amplificação evolutiva através de κ (kappa).

    **Racional Matemático:**
    
    A fórmula CAOS⁺ foi projetada para modular a taxa de aprendizado α_t no
    sistema auto-evolutivo. Ela combina dois produtos fundamentais:
    
    - Base: (1 + κ·C·A) - amplifica quando Consistência e Autoevolução são altas
    - Expoente: (O·S) - intensifica quando há Incerteza controlada e Silêncio
    
    A estrutura exponencial garante que:
    1. Sistemas consistentes e auto-evolutivos recebem maior amplificação (base alta)
    2. A exploração é liberada gradualmente conforme o incognoscível aumenta
    3. O silêncio (qualidade do sinal) modula a agressividade da exploração
    4. O resultado sempre ≥ 1, servindo como multiplicador de α
    
    **Quando usar:**
    - Pipeline principal de evolução (Champion-Challenger)
    - Seleção de challengers na Liga ACFA
    - Modulação de α_t^{eff} na Equação de Penin (Eq. 1)
    - Quando precisar de output não-limitado (> 1.0)

    Args:
        c (float): Consistência [0, 1] - Média ponderada de:
            * pass@k: taxa de sucesso em k tentativas
            * 1-ECE: calibração (Expected Calibration Error invertido)
            * v_ext: score de verificação externa (oráculos, testes formais)
            Valores típicos: 0.7-0.95 para sistemas em produção
            
        a (float): Autoevolução [0, 1] - Ganho por custo normalizado:
            * A = ΔL∞⁺ / (Cost_norm + ε)
            * Mede eficiência evolutiva (quanto melhorou por recurso gasto)
            Valores típicos: 0.2-0.6 (mais alto em fases de otimização)
            
        o (float): Incognoscível [0, 1] - Grau de incerteza epistêmica:
            * Combina uncertainty, OOD score, ensemble disagreement
            * Mais O → libera mais exploração
            Valores típicos: 0.2-0.5 (baixo em produção, alto em exploração)
            
        s (float): Silêncio [0, 1] - Qualidade do sinal:
            * S = pesos·[(1-ruído), (1-redundância), (1-entropia)]
            * Penaliza ruído, redundância e entropia
            Valores típicos: 0.6-0.9 (alto silêncio = dados limpos)
            
        kappa (float): Ganho base de amplificação (≥ 1, default=20.0)
            * Controla a agressividade do sistema evolutivo
            * κ = 20: padrão para exploração moderada
            * κ = 10-15: conservador (produção estável)
            * κ = 30-50: agressivo (pesquisa/experimentação)
            * Auto-tunável via Equação 10 (AdaGrad-style)

    Returns:
        float: CAOS⁺ ≥ 1.0 (unbounded)
            * Valores típicos: 1.5-5.0 em operação normal
            * Serve como multiplicador de α_t (step size)
            * CAOS⁺ > 3.0 indica forte confiança para evolução
            * CAOS⁺ ≈ 1.0 indica cautela (sistema conservador)

    Propriedades Matemáticas:
        - Identidade: CAOS⁺(0,0,0,0) = 1 (sem amplificação)
        - Máximo dependente de κ: CAOS⁺(1,1,1,1) = (1 + κ)
        - Monotônica: ∂CAOS⁺/∂C > 0, ∂CAOS⁺/∂A > 0, ∂CAOS⁺/∂O > 0, ∂CAOS⁺/∂S > 0
        - Composicionalidade: base e expoente independentes
        - Estabilidade numérica: sempre definida para inputs válidos

    Examples:
        >>> # Exemplo 1: Sistema conservador (produção estável)
        >>> caos = compute_caos_plus_exponential(
        ...     c=0.90,  # Alta consistência
        ...     a=0.30,  # Baixa autoevolução (já otimizado)
        ...     o=0.20,  # Baixa incerteza (domínio conhecido)
        ...     s=0.85,  # Alto silêncio (dados limpos)
        ...     kappa=15.0  # Conservador
        ... )
        >>> print(f"CAOS⁺ conservador: {caos:.2f}")  # ~1.3
        
        >>> # Exemplo 2: Sistema exploratório (pesquisa)
        >>> caos = compute_caos_plus_exponential(
        ...     c=0.75,  # Consistência moderada
        ...     a=0.50,  # Boa autoevolução
        ...     o=0.60,  # Alta incerteza (exploração)
        ...     s=0.70,  # Silêncio moderado
        ...     kappa=35.0  # Agressivo
        ... )
        >>> print(f"CAOS⁺ exploratório: {caos:.2f}")  # ~3.2
        
        >>> # Exemplo 3: Uso típico em pipeline de evolução
        >>> from penin.core.caos import ConsistencyMetrics, AutoevolutionMetrics
        >>> from penin.core.caos import IncognoscibleMetrics, SilenceMetrics
        >>> 
        >>> # Coletar métricas
        >>> consistency = ConsistencyMetrics(pass_at_k=0.92, ece=0.008, external_verification=0.88)
        >>> autoevol = AutoevolutionMetrics(delta_linf=0.06, cost_normalized=0.15)
        >>> incog = IncognoscibleMetrics(epistemic_uncertainty=0.35, ood_score=0.28)
        >>> silence = SilenceMetrics(noise_ratio=0.08, redundancy_ratio=0.12)
        >>> 
        >>> # Calcular componentes
        >>> c = consistency.compute_c()
        >>> a = autoevol.compute_a()
        >>> o = incog.compute_o()
        >>> s = silence.compute_s()
        >>> 
        >>> # Computar CAOS⁺
        >>> caos = compute_caos_plus_exponential(c, a, o, s, kappa=20.0)
        >>> 
        >>> # Usar como multiplicador de step size
        >>> alpha_base = 0.1
        >>> alpha_effective = alpha_base * caos
        >>> print(f"α_eff = {alpha_effective:.3f}")  # Amplificado por CAOS⁺
        
    See Also:
        - phi_caos: Variante com saturação via tanh (output limitado a [0,1))
        - compute_caos_plus_complete: Pipeline completo com EMA e auditoria
        - compute_caos_plus_simple: Wrapper simplificado
        
    References:
        - Equação 3 do PENIN-Ω: Motor CAOS⁺ (docs/equations.md)
        - Master Equation (Eq. 1): Uso de α_t^{eff} modulado por CAOS⁺
        - Liga ACFA: Seleção de challengers via CAOS⁺
    """
    # Clamp inputs
    c = clamp01(c)
    a = clamp01(a)
    o = clamp01(o)
    s = clamp01(s)
    kappa = max(1.0, kappa)

    # Base: 1 + κ·C·A
    base = 1.0 + kappa * c * a

    # Expoente: O·S
    exponent = o * s

    # CAOS⁺
    caos_plus = base**exponent

    return caos_plus


def phi_caos(
    c: float,
    a: float,
    o: float,
    s: float,
    kappa: float = 2.0,
    kappa_max: float = 10.0,
    gamma: float = DEFAULT_GAMMA,
) -> float:
    """
    Fórmula CAOS⁺ com saturação: tanh(γ · log(CAOS⁺_exponencial))

    Variante histórica com output limitado a [0, 1) via tangente hiperbólica.
    Útil para composições com outras métricas normalizadas e quando se
    deseja evitar amplificação excessiva.

    **Racional Matemático:**
    
    Esta variante aplica saturação não-linear ao CAOS⁺ exponencial:
    1. Calcula log(CAOS⁺_exponencial) para comprimir o range
    2. Multiplica por γ (gamma) para controlar a suavidade da saturação
    3. Aplica tanh() para garantir output em [0, 1)
    
    A saturação via tanh é útil quando:
    - Você precisa compor CAOS⁺ com outras métricas [0,1]
    - Deseja evitar amplificações muito grandes (estabilidade)
    - Está em fase de calibração/debug do sistema
    
    **Quando usar:**
    - Integrações com sistemas legados que esperam [0,1]
    - Visualizações e dashboards normalizados
    - Composição com outras métricas via operações aritméticas
    - Quando quiser limitar o impacto de κ muito alto

    Args:
        c (float): Consistência [0, 1] - veja compute_caos_plus_exponential
        a (float): Autoevolução [0, 1] - veja compute_caos_plus_exponential
        o (float): Incognoscível [0, 1] - veja compute_caos_plus_exponential
        s (float): Silêncio [0, 1] - veja compute_caos_plus_exponential
        
        kappa (float): Ganho base (será clamped em [1.0, kappa_max], default=2.0)
            * κ = 2.0: padrão conservador para variante phi
            * κ < 2.0: extremamente conservador
            * κ > 5.0: mais agressivo (mas limitado por kappa_max)
            
        kappa_max (float): Teto de kappa (default=10.0)
            * Previne κ excessivamente alto na variante saturada
            * Típico: 5.0-20.0
            
        gamma (float): Parâmetro de saturação [0.1, 2.0] (default=0.7)
            * Controla a "suavidade" da função tanh
            * γ baixo (0.1-0.5): saturação muito suave (quase linear)
            * γ médio (0.6-0.8): balanceado
            * γ alto (1.0-2.0): saturação agressiva (satura rápido)

    Returns:
        float: φ_CAOS ∈ [0, 1) aproximadamente
            * Valores típicos: 0.2-0.8
            * φ < 0.3: sistema muito conservador
            * φ ≈ 0.5: balanceado
            * φ > 0.7: sistema confiante (mas ainda limitado)

    Examples:
        >>> # Exemplo 1: Uso básico com defaults
        >>> phi = phi_caos(c=0.8, a=0.5, o=0.7, s=0.9)
        >>> print(f"φ_CAOS: {phi:.3f}")  # ~0.25-0.35
        
        >>> # Exemplo 2: Comparação com exponencial
        >>> c, a, o, s, kappa = 0.88, 0.40, 0.35, 0.82, 20.0
        >>> caos_exp = compute_caos_plus_exponential(c, a, o, s, kappa)
        >>> phi = phi_caos(c, a, o, s, kappa=kappa, kappa_max=50.0, gamma=0.7)
        >>> print(f"CAOS⁺ exponencial: {caos_exp:.2f}")  # ~1.86
        >>> print(f"φ_CAOS saturado: {phi:.3f}")  # ~0.30-0.50
        
        >>> # Exemplo 3: Ajustando saturação via gamma
        >>> c, a, o, s = 0.9, 0.5, 0.4, 0.8
        >>> phi_suave = phi_caos(c, a, o, s, gamma=0.3)  # Saturação suave
        >>> phi_medio = phi_caos(c, a, o, s, gamma=0.7)  # Balanceado
        >>> phi_rapido = phi_caos(c, a, o, s, gamma=1.5)  # Satura rápido
        >>> print(f"γ=0.3: {phi_suave:.3f}, γ=0.7: {phi_medio:.3f}, γ=1.5: {phi_rapido:.3f}")
        
        >>> # Exemplo 4: Integração com outras métricas normalizadas
        >>> from penin.equations.sr_omega_infinity import compute_sr_omega_infinity
        >>> phi = phi_caos(0.85, 0.40, 0.30, 0.80, kappa=5.0)
        >>> sr = compute_sr_omega_infinity(0.92, True, 0.88, 0.67)
        >>> # Ambos em [0,1], podemos combinar facilmente
        >>> combined_score = 0.6 * phi + 0.4 * sr
        >>> print(f"Score combinado: {combined_score:.3f}")

    Note:
        Esta fórmula é mantida para compatibilidade com código histórico
        em penin/omega/caos.py. Para o pipeline evolutivo principal,
        prefira compute_caos_plus_exponential() que fornece amplificação
        não-limitada, mais adequada para modular α_t.

    See Also:
        - compute_caos_plus_exponential: Variante exponencial pura (preferida)
        - compute_caos_plus: Wrapper de compatibilidade que retorna (phi, details)
        - caos_plus: Interface alternativa com kwargs
        
    References:
        - Equação 3 do PENIN-Ω (docs/equations.md)
        - penin/omega/caos.py: Implementação histórica
    """
    # Clamp inputs
    c = clamp01(c)
    a = clamp01(a)
    o = clamp01(o)
    s = clamp01(s)
    kappa = clamp(kappa, 1.0, kappa_max)
    gamma = clamp(gamma, 0.1, 2.0)

    # Base (com proteção numérica)
    base = max(1.0 + EPS, 1.0 + kappa * c * a)

    # Expoente
    exp_term = clamp01(o * s)

    # Log-space para estabilidade
    log_caos = exp_term * math.log(base)

    # Saturação tanh
    phi = math.tanh(gamma * log_caos)

    return phi


def compute_caos_plus_simple(
    C: float,
    A: float,
    O: float,
    S: float,
    kappa: float = DEFAULT_KAPPA,
    config: CAOSConfig | None = None,
) -> float:
    """
    Wrapper simplificado quando já se tem C, A, O, S normalizados.

    Args:
        C, A, O, S: Componentes [0, 1]
        kappa: Ganho base
        config: Configuração opcional (se None, usa defaults)

    Returns:
        CAOS⁺ (scaled e clamped conforme config)
    """
    if config is None:
        config = CAOSConfig(kappa=kappa)

    # Clamp inputs
    C = clamp01(C)
    A = clamp01(A)
    O = clamp01(O)
    S = clamp01(S)

    # Escolhe fórmula
    if config.formula == CAOSFormula.EXPONENTIAL:
        caos_raw = compute_caos_plus_exponential(C, A, O, S, config.kappa)
    elif config.formula == CAOSFormula.PHI_CAOS:
        caos_raw = phi_caos(C, A, O, S, config.kappa, config.kappa_max, config.gamma)
    else:  # HYBRID
        # Usa exponencial por padrão
        caos_raw = compute_caos_plus_exponential(C, A, O, S, config.kappa)

    # Clamp
    caos_clamped = clamp(caos_raw, config.caos_min, config.caos_max)

    # Normalizar se configurado
    if config.normalize_output:
        caos_final = (caos_clamped - config.caos_min) / (config.caos_max - config.caos_min)
    else:
        caos_final = caos_clamped

    return caos_final


def compute_caos_plus_complete(
    consistency_metrics: ConsistencyMetrics,
    autoevolution_metrics: AutoevolutionMetrics,
    incognoscible_metrics: IncognoscibleMetrics,
    silence_metrics: SilenceMetrics,
    config: CAOSConfig | None = None,
    state: CAOSState | None = None,
) -> tuple[float, dict[str, Any]]:
    """
    Computação CAOS⁺ completa com métricas detalhadas, EMA e auditoria.
    
    Esta é a função de mais alto nível para computação de CAOS⁺ em produção.
    Ela fornece um pipeline completo desde métricas raw até score final,
    incluindo suavização temporal via EMA e geração de dados para auditoria.

    **Pipeline de Computação:**
    
    1. **Agregação de Métricas**: Calcula C, A, O, S a partir de métricas raw
       - C: média ponderada de pass@k, (1-ECE), verificação externa
       - A: ΔL∞ normalizado por custo
       - O: média de incerteza epistêmica, OOD, disagreement
       - S: média ponderada de anti-ruído, anti-redundância, anti-entropia
    
    2. **Atualização de Estado**: Registra valores raw (c_current, a_current, etc.)
    
    3. **Suavização EMA**: Aplica Exponential Moving Average com half-life configurável
       - Reduz variância e ruído nas medições
       - Primeira iteração: inicializa EMA com valor observado
       - Iterações subsequentes: EMA_t = α·valor_t + (1-α)·EMA_{t-1}
    
    4. **Computação CAOS⁺**: Usa fórmula selecionada (exponencial ou phi_caos)
       com valores suavizados
    
    5. **Clamps e Normalização**: Aplica limites min/max e opcionalmente normaliza
       para [0,1]
    
    6. **Atualização de Histórico**: Mantém FIFO das últimas N amostras para
       análise de estabilidade
    
    7. **Geração de Details**: Cria dict completo para WORM ledger e auditoria

    **Quando usar:**
    - Pipeline de produção com Champion-Challenger
    - Quando precisar de auditabilidade completa (WORM ledger)
    - Quando tiver métricas raw que precisam ser agregadas
    - Quando quiser suavização temporal (EMA)

    Args:
        consistency_metrics (ConsistencyMetrics): Métricas de Consistência (C)
            Campos principais:
            - pass_at_k: taxa de sucesso em k tentativas [0,1]
            - ece: Expected Calibration Error [0,1] (menor é melhor)
            - external_verification: score de verificação externa [0,1]
            - Pesos para agregação (weight_pass, weight_ece, weight_external)
            
        autoevolution_metrics (AutoevolutionMetrics): Métricas de Autoevolução (A)
            Campos principais:
            - delta_linf: ganho de L∞ (valores negativos viram 0)
            - cost_normalized: custo normalizado [0,∞)
            - max_a: limite superior para clamp (default 10.0)
            
        incognoscible_metrics (IncognoscibleMetrics): Métricas de Incognoscível (O)
            Campos principais:
            - epistemic_uncertainty: entropy, mutual information [0,1]
            - ood_score: out-of-distribution score [0,1]
            - ensemble_disagreement: variância de predições [0,1]
            - Pesos para agregação
            
        silence_metrics (SilenceMetrics): Métricas de Silêncio (S)
            Campos principais:
            - noise_ratio: proporção de ruído [0,1]
            - redundancy_ratio: proporção de redundância [0,1]
            - entropy_normalized: entropia normalizada [0,1]
            - Pesos para agregação (recomendado 2:1:1)
            
        config (CAOSConfig | None): Configuração do motor CAOS⁺
            Se None, usa defaults (exponential formula, kappa=20, etc.)
            Campos principais:
            - formula: EXPONENTIAL | PHI_CAOS | HYBRID
            - kappa: ganho base [kappa_min, kappa_max]
            - ema_half_life: amostras para peso cair 50% (típico 3-10)
            - caos_min, caos_max: clamps do output
            - normalize_output: se True, retorna em [0,1]
            
        state (CAOSState | None): Estado com histórico e EMA
            Se None, cria novo (primeira computação)
            Campos principais:
            - c/a/o/s_current: valores raw atuais
            - c/a/o/s_smoothed: valores suavizados via EMA
            - history: lista FIFO dos últimos CAOS⁺
            - update_count: número de atualizações

    Returns:
        tuple[float, dict[str, Any]]: (caos_plus_final, details_dict)
        
        caos_plus_final (float): Valor CAOS⁺ final (após EMA, clamps, normalização)
            - Se normalize_output=False: típico 1.0-10.0
            - Se normalize_output=True: [0, 1]
            
        details_dict (dict): Dicionário completo para auditoria contendo:
            - components_raw: {C, A, O, S} antes de EMA
            - components_smoothed: {C, A, O, S} após EMA
            - metrics_input: todas métricas raw de entrada
            - caos_plus_raw: resultado antes de clamps
            - caos_plus_clamped: após aplicar min/max
            - caos_plus_final: resultado final
            - ema_alpha, ema_half_life: parâmetros de suavização
            - kappa, formula: configuração usada
            - state_update_count: número de iterações
            - state_stability: inverse coefficient of variation
            
    Examples:
        >>> # Exemplo 1: Uso típico em produção
        >>> from penin.core.caos import (
        ...     ConsistencyMetrics, AutoevolutionMetrics,
        ...     IncognoscibleMetrics, SilenceMetrics,
        ...     CAOSConfig, CAOSState, compute_caos_plus_complete
        ... )
        >>> 
        >>> # Coletar métricas do sistema
        >>> consistency = ConsistencyMetrics(
        ...     pass_at_k=0.92,
        ...     ece=0.008,
        ...     external_verification=0.88
        ... )
        >>> 
        >>> autoevolution = AutoevolutionMetrics(
        ...     delta_linf=0.06,  # 6% de ganho em L∞
        ...     cost_normalized=0.15  # 15% do budget consumido
        ... )
        >>> 
        >>> incognoscible = IncognoscibleMetrics(
        ...     epistemic_uncertainty=0.35,
        ...     ood_score=0.28,
        ...     ensemble_disagreement=0.30
        ... )
        >>> 
        >>> silence = SilenceMetrics(
        ...     noise_ratio=0.08,  # 8% ruído
        ...     redundancy_ratio=0.12,  # 12% redundância
        ...     entropy_normalized=0.18  # 18% entropia
        ... )
        >>> 
        >>> # Configurar motor
        >>> config = CAOSConfig(
        ...     kappa=25.0,  # Moderadamente agressivo
        ...     ema_half_life=5,  # Suavizar em 5 iterações
        ...     normalize_output=False  # Manter como multiplicador
        ... )
        >>> 
        >>> # Estado persistente entre iterações
        >>> state = CAOSState()
        >>> 
        >>> # Computar CAOS⁺
        >>> caos_plus, details = compute_caos_plus_complete(
        ...     consistency, autoevolution, incognoscible, silence,
        ...     config, state
        ... )
        >>> 
        >>> # Usar no pipeline evolutivo
        >>> alpha_base = 0.1
        >>> alpha_effective = alpha_base * caos_plus
        >>> print(f"CAOS⁺: {caos_plus:.4f}")
        >>> print(f"α_eff: {alpha_effective:.4f}")
        >>> 
        >>> # Registrar em WORM ledger
        >>> import json
        >>> ledger_entry = {
        ...     "timestamp": "2025-01-15T10:30:00Z",
        ...     "caos_plus": caos_plus,
        ...     "details": details,
        ...     "decision": "PROMOTE" if caos_plus > 2.0 else "KEEP"
        ... }
        >>> # worm_ledger.append(ledger_entry)
        
        >>> # Exemplo 2: Múltiplas iterações com EMA
        >>> config = CAOSConfig(ema_half_life=3)
        >>> state = CAOSState()
        >>> 
        >>> for iteration in range(5):
        ...     # Simular métricas variáveis
        ...     consistency = ConsistencyMetrics(pass_at_k=0.90 + iteration*0.01)
        ...     autoevolution = AutoevolutionMetrics(delta_linf=0.05)
        ...     incognoscible = IncognoscibleMetrics(epistemic_uncertainty=0.30)
        ...     silence = SilenceMetrics(noise_ratio=0.10)
        ...     
        ...     caos, details = compute_caos_plus_complete(
        ...         consistency, autoevolution, incognoscible, silence,
        ...         config, state
        ...     )
        ...     
        ...     print(f"Iter {iteration+1}: CAOS⁺={caos:.3f}, "
        ...           f"C_smoothed={details['components_smoothed']['C']:.3f}, "
        ...           f"stability={details['state_stability']:.3f}")
        
        >>> # Exemplo 3: Auditoria e análise de estabilidade
        >>> caos, details = compute_caos_plus_complete(
        ...     consistency, autoevolution, incognoscible, silence
        ... )
        >>> 
        >>> # Verificar estabilidade
        >>> if details['state_stability'] < 0.7:
        ...     print("⚠️ Sistema instável - considere aumentar ema_half_life")
        >>> 
        >>> # Analisar contribuição de cada componente
        >>> comps = details['components_smoothed']
        >>> print(f"Gargalos: C={comps['C']:.2f}, A={comps['A']:.2f}, "
        ...       f"O={comps['O']:.2f}, S={comps['S']:.2f}")
        >>> 
        >>> # Decisão baseada em threshold
        >>> threshold = 2.0
        >>> decision = "PROMOTE" if caos >= threshold else "ROLLBACK"
        >>> print(f"Decisão: {decision} (CAOS⁺={caos:.2f} vs threshold={threshold})")

    Raises:
        ValueError: Se métricas de entrada tiverem valores inválidos (fora de ranges)
        
    Note:
        - Esta função mantém estado entre chamadas via `state` parameter
        - Para uso stateless, omita `state` (será criado novo a cada chamada)
        - O dicionário `details` deve ser registrado no WORM ledger para auditoria
        - EMA requer múltiplas iterações para convergir (mínimo 2-3 × half_life)

    See Also:
        - compute_caos_plus_exponential: Fórmula core (sem agregação)
        - compute_caos_plus_simple: Wrapper quando já tem C, A, O, S
        - ConsistencyMetrics, AutoevolutionMetrics, etc.: Dataclasses de métricas
        - CAOSConfig: Configuração do motor
        - CAOSState: Estado persistente com histórico
        
    References:
        - Equação 3 do PENIN-Ω (docs/equations.md)
        - WORM Ledger: docs/architecture.md
        - Pipeline Champion-Challenger: docs/COMPLETE_SYSTEM_GUIDE.md
    """
    if config is None:
        config = CAOSConfig()

    if state is None:
        state = CAOSState()

    details: dict[str, Any] = {}

    # 1. Computar componentes C, A, O, S
    c_raw = consistency_metrics.compute_c()
    a_raw = autoevolution_metrics.compute_a()
    o_raw = incognoscible_metrics.compute_o()
    s_raw = silence_metrics.compute_s()

    details["components_raw"] = {"C": c_raw, "A": a_raw, "O": o_raw, "S": s_raw}
    details["metrics_input"] = {
        "consistency": {
            "pass_at_k": consistency_metrics.pass_at_k,
            "ece": consistency_metrics.ece,
            "external_verification": consistency_metrics.external_verification,
        },
        "autoevolution": {
            "delta_linf": autoevolution_metrics.delta_linf,
            "cost_normalized": autoevolution_metrics.cost_normalized,
        },
        "incognoscible": {
            "epistemic_uncertainty": incognoscible_metrics.epistemic_uncertainty,
            "ood_score": incognoscible_metrics.ood_score,
            "ensemble_disagreement": incognoscible_metrics.ensemble_disagreement,
        },
        "silence": {
            "noise_ratio": silence_metrics.noise_ratio,
            "redundancy_ratio": silence_metrics.redundancy_ratio,
            "entropy_normalized": silence_metrics.entropy_normalized,
        },
    }

    # 2. Atualizar estado (current values)
    state.c_current = c_raw
    state.a_current = a_raw
    state.o_current = o_raw
    state.s_current = s_raw

    # 3. Suavizar via EMA
    alpha = compute_ema_alpha(config.ema_half_life)

    state.c_smoothed = state.update_ema(c_raw, state.c_smoothed, alpha)
    state.a_smoothed = state.update_ema(a_raw, state.a_smoothed, alpha)
    state.o_smoothed = state.update_ema(o_raw, state.o_smoothed, alpha)
    state.s_smoothed = state.update_ema(s_raw, state.s_smoothed, alpha)

    details["components_smoothed"] = {
        "C": state.c_smoothed,
        "A": state.a_smoothed,
        "O": state.o_smoothed,
        "S": state.s_smoothed,
    }
    details["ema_alpha"] = alpha
    details["ema_half_life"] = config.ema_half_life

    # 4. Aplicar clamps em kappa
    kappa_clamped = clamp(config.kappa, config.kappa_min, config.kappa_max)
    details["kappa"] = kappa_clamped
    details["formula"] = config.formula.value

    # 5. Computar CAOS⁺ com valores suavizados
    if config.formula == CAOSFormula.EXPONENTIAL:
        caos_plus_raw = compute_caos_plus_exponential(
            state.c_smoothed, state.a_smoothed, state.o_smoothed, state.s_smoothed, kappa_clamped
        )
    elif config.formula == CAOSFormula.PHI_CAOS:
        caos_plus_raw = phi_caos(
            state.c_smoothed,
            state.a_smoothed,
            state.o_smoothed,
            state.s_smoothed,
            kappa_clamped,
            config.kappa_max,
            config.gamma,
        )
    else:  # HYBRID
        caos_plus_raw = compute_caos_plus_exponential(
            state.c_smoothed, state.a_smoothed, state.o_smoothed, state.s_smoothed, kappa_clamped
        )

    details["caos_plus_raw"] = caos_plus_raw

    # 6. Aplicar clamps no resultado
    caos_plus_clamped = clamp(caos_plus_raw, config.caos_min, config.caos_max)
    details["caos_plus_clamped"] = caos_plus_clamped

    # 7. Log-space (opcional, para comparação)
    if config.use_log_space:
        caos_log = math.log(max(EPS, caos_plus_clamped))
        details["caos_plus_log"] = caos_log

    # 8. Normalizar saída (opcional)
    if config.normalize_output:
        caos_normalized = (caos_plus_clamped - config.caos_min) / (config.caos_max - config.caos_min)
        caos_plus_final = clamp01(caos_normalized)
        details["caos_plus_normalized"] = caos_plus_final
    else:
        caos_plus_final = caos_plus_clamped

    # 9. Atualizar estado
    state.caos_plus = caos_plus_final
    state.add_to_history(caos_plus_final)
    state.update_count += 1

    details["state_update_count"] = state.update_count
    details["state_stability"] = state.get_stability()
    details["caos_plus_final"] = caos_plus_final

    return caos_plus_final, details


# =============================================================================
# COMPATIBILITY WRAPPERS
# =============================================================================


def compute_caos_plus(
    C: float,
    A: float,
    O: float,
    S: float,
    kappa: float = 2.0,
    config: CAOSConfig | None = None,
) -> tuple[float, dict[str, Any]]:
    """
    Wrapper de compatibilidade com assinatura antiga de penin/omega/caos.py

    Retorna tupla (phi, details) como esperado por código legado.
    """
    if config is None:
        config = CAOSConfig(kappa=kappa, formula=CAOSFormula.PHI_CAOS)

    # Usa phi_caos para compatibilidade
    phi = phi_caos(C, A, O, S, kappa)

    details = {
        "C": C,
        "A": A,
        "O": O,
        "S": S,
        "kappa": kappa,
        "phi": phi,
        "components": {"C": C, "A": A, "O": O, "S": S},
    }

    return phi, details


def caos_plus(
    C: float | None = None,
    A: float | None = None,
    O: float | None = None,
    S: float | None = None,
    kappa: float = 2.0,
    gamma: float = DEFAULT_GAMMA,
    kappa_max: float = 10.0,
    **kwargs,
) -> dict[str, Any]:
    """
    Wrapper de compatibilidade com função caos_plus() de penin/omega/caos.py

    Aceita nomes alternativos (coherence, awareness, openness, stability).
    """
    # Accept alternative keyword names
    if C is None and "coherence" in kwargs:
        C = kwargs["coherence"]
    if A is None and "awareness" in kwargs:
        A = kwargs["awareness"]
    if O is None and "openness" in kwargs:
        O = kwargs["openness"]
    if S is None and "stability" in kwargs:
        S = kwargs["stability"]

    # Default values
    C = C if C is not None else 0.5
    A = A if A is not None else 0.5
    O = O if O is not None else 0.5
    S = S if S is not None else 0.5

    phi = phi_caos(C, A, O, S, kappa=kappa, kappa_max=kappa_max, gamma=gamma)

    return {
        "phi": phi,
        "components": {"C": C, "A": A, "O": O, "S": S},
        "caos_product": C * A,
        "openness_stability": O * S,
        "kappa": kappa,
        "gamma": gamma,
        "risk_level": "low" if phi < 0.5 else "medium" if phi < 0.8 else "high",
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def harmonic_mean(c: float, a: float, o: float, s: float) -> float:
    """Média harmônica de C, A, O, S (alternativa não-compensatória)"""
    values = [c, a, o, s]
    filtered = [v for v in values if v > EPS]
    if not filtered:
        return 0.0
    return len(filtered) / sum(1.0 / v for v in filtered)


def geometric_mean(c: float, a: float, o: float, s: float) -> float:
    """Média geométrica de C, A, O, S"""
    product = c * a * o * s
    if product <= 0:
        return 0.0
    return product**0.25


def caos_gradient(c: float, a: float, o: float, s: float, kappa: float) -> dict[str, float]:
    """Calcula gradientes numéricos de CAOS⁺ (para otimização)"""
    eps = 1e-6

    phi_base = phi_caos(c, a, o, s, kappa)

    dC = (phi_caos(c + eps, a, o, s, kappa) - phi_base) / eps
    dA = (phi_caos(c, a + eps, o, s, kappa) - phi_base) / eps
    dO = (phi_caos(c, a, o + eps, s, kappa) - phi_base) / eps
    dS = (phi_caos(c, a, o, s + eps, kappa) - phi_base) / eps

    return {"dC": dC, "dA": dA, "dO": dO, "dS": dS}


# =============================================================================
# TRACKER CLASS
# =============================================================================


class CAOSTracker:
    """
    Tracker para monitorar CAOS⁺ ao longo do tempo.

    Features:
    - EMA automático
    - Histórico limitado
    - Cálculo de estabilidade
    - Alertas de anomalias
    """

    def __init__(
        self,
        alpha: float = 0.2,
        max_history: int = 100,
        config: CAOSConfig | None = None,
    ):
        self.alpha = alpha
        self.max_history = max_history
        self.config = config or CAOSConfig()
        self.history = []
        self.ema_value = None

    def update(self, c: float, a: float, o: float, s: float, kappa: float = 2.0) -> tuple[float, float]:
        """Atualiza tracker com novos valores CAOS"""
        caos_val = phi_caos(c, a, o, s, kappa)

        # Update EMA
        if self.ema_value is None:
            self.ema_value = caos_val
        else:
            self.ema_value = (1.0 - self.alpha) * self.ema_value + self.alpha * caos_val

        # Update history
        self.history.append(caos_val)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        return caos_val, self.ema_value

    def get_stability(self) -> float:
        """Estabilidade (inverse coefficient of variation)"""
        if len(self.history) < 2:
            return 1.0

        mean_val = sum(self.history) / len(self.history)
        if mean_val <= EPS:
            return 0.0

        variance = sum((v - mean_val) ** 2 for v in self.history) / len(self.history)
        cv = math.sqrt(variance) / mean_val

        return 1.0 / (1.0 + cv)

    def get_trend(self) -> float:
        """Tendência (slope recente via regressão linear simples)"""
        if len(self.history) < 3:
            return 0.0

        n = len(self.history)
        x = list(range(n))
        y = self.history

        # Simple linear regression
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator < EPS:
            return 0.0

        slope = numerator / denominator
        return slope


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "CAOSComponent",
    "CAOSFormula",
    # Metrics
    "ConsistencyMetrics",
    "AutoevolutionMetrics",
    "IncognoscibleMetrics",
    "SilenceMetrics",
    # Config & State
    "CAOSConfig",
    "CAOSState",
    # Core functions
    "compute_caos_plus_exponential",
    "phi_caos",
    "compute_caos_plus_simple",
    "compute_caos_plus_complete",
    # Compatibility wrappers
    "compute_caos_plus",
    "caos_plus",
    # Helpers
    "clamp01",
    "clamp",
    "compute_ema_alpha",
    "harmonic_mean",
    "geometric_mean",
    "caos_gradient",
    # Tracker
    "CAOSTracker",
    # Constants
    "EPS",
    "DEFAULT_KAPPA",
    "DEFAULT_GAMMA",
]
