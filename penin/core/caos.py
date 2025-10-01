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

        c = (
            self.weight_pass * pass_norm
            + self.weight_ece * ece_norm
            + self.weight_external * ext_norm
        )

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

        o = (
            self.weight_epistemic * epist_norm
            + self.weight_ood * ood_norm
            + self.weight_ensemble * ens_norm
        )

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

    Esta é a fórmula matemática canônica original.
    Monotônica em C, A, O, S; κ amplifica a base.

    Args:
        c: Consistência [0, 1]
        a: Autoevolução [0, 1]
        o: Incognoscível [0, 1]
        s: Silêncio [0, 1]
        kappa: Ganho base ≥ 1

    Returns:
        CAOS⁺ ≥ 1 (sem teto, unbounded)

    Propriedades:
        - CAOS⁺(0,0,0,0) = 1
        - CAOS⁺(1,1,1,1) = (1 + κ)^1 = 1 + κ
        - Maior κ → maior amplificação
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

    Variante histórica com output limitado a [0, 1) via tanh.
    Útil para composições com outras métricas normalizadas.

    Args:
        c, a, o, s: Componentes [0, 1]
        kappa: Ganho [1, kappa_max]
        kappa_max: Limite superior de kappa
        gamma: Saturação [0.1, 2.0]

    Returns:
        φ_CAOS em [0, 1) aproximadamente

    Nota:
        Esta fórmula é mantida para compatibilidade com código histórico
        em penin/omega/caos.py, mas a fórmula exponencial é preferida
        para uso no pipeline principal.
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

    Pipeline:
    1. Calcula componentes C, A, O, S a partir de métricas raw
    2. Atualiza estado (valores current)
    3. Aplica suavização EMA
    4. Calcula CAOS⁺ com valores suavizados
    5. Aplica clamps e normalização
    6. Atualiza histórico
    7. Retorna score e details para auditoria

    Args:
        consistency_metrics: Métricas de C
        autoevolution_metrics: Métricas de A
        incognoscible_metrics: Métricas de O
        silence_metrics: Métricas de S
        config: Configuração (se None, usa defaults)
        state: Estado com histórico EMA (se None, cria novo)

    Returns:
        (caos_plus_final, details_dict)
        - caos_plus_final: Valor CAOS⁺ final
        - details_dict: Dicionário com todas métricas intermediárias para WORM ledger
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
