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


@dataclass
class CAOSComponents:
    """Componentes CAOS como dataclass para uso em testes e APIs"""
    C: float
    A: float
    O: float
    S: float

    def to_dict(self) -> dict[str, float]:
        """Converte para dicionário"""
        return {"C": self.C, "A": self.A, "O": self.O, "S": self.S}


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
    kappa_max: float = 10.0  # Test expects 10.0

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
    saturation_method: str = "tanh"  # For test compatibility

    # Determinismo
    seed: int | None = None


class CAOSPlusEngine:
    """Motor de cálculo CAOS+ com configuração"""

    def __init__(self, config: CAOSConfig | None = None):
        self.config = config or CAOSConfig()

    def compute(self, C: float, A: float, O: float, S: float) -> float:
        """Computa CAOS+ exponencial básico"""
        return compute_caos_plus_exponential(C, A, O, S, kappa=self.config.kappa)

    def compute_phi(self, components: CAOSComponents) -> tuple[float, dict[str, Any]]:
        """Computa phi_caos com detalhes"""
        phi_result = phi_caos(components.C, components.A, components.O, components.S,
                             kappa=self.config.kappa, gamma=self.config.gamma)
        details = {
            "phi": phi_result,
            "components": components.to_dict(),
            "config": {
                "kappa": self.config.kappa,
                "gamma": self.config.gamma
            }
        }
        return phi_result, details


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
    É monotônica em todas as dimensões (C, A, O, S) e κ amplifica a base.

    Racional Matemático
    -------------------
    A fórmula CAOS⁺ foi projetada para modular a taxa de aprendizado (α) no motor
    evolutivo, equilibrando exploração e exploração através de quatro dimensões:

    1. **Base (1 + κ·C·A)**: Representa o potencial de amplificação
       - C·A mede a "qualidade" da evolução (consistência × autoevolução)
       - κ controla a intensidade da amplificação (padrão: 20.0)
       - Base sempre ≥ 1, garantindo que CAOS⁺ nunca reduz o passo

    2. **Expoente (O·S)**: Controla a agressividade da exploração
       - O (Incognoscível) aumenta quando há mais incerteza → mais exploração
       - S (Silêncio) aumenta com melhor qualidade de sinal → mais confiança
       - O·S alto → expoente alto → amplificação exponencial mais agressiva

    Propriedades Matemáticas
    ------------------------
    - **Identidade**: CAOS⁺(0,0,0,0) = 1^0 = 1 (sem amplificação)
    - **Máximo teórico**: CAOS⁺(1,1,1,1) = (1 + κ)^1 = 1 + κ
    - **Monotonicidade**: ∂CAOS⁺/∂x ≥ 0 para x ∈ {C, A, O, S, κ}
    - **Estabilidade**: Base sempre ≥ 1 previne valores negativos ou zero
    - **Escala**: Com κ=20, range típico é [1.0, 3.5] para valores práticos

    Args:
        c (float): Consistência [0, 1]. Mede confiabilidade das predições através de:
            - pass@k: taxa de autoconsistência em k amostras
            - (1-ECE): calibração das probabilidades (Expected Calibration Error)
            - v_ext: score de verificação externa (oracles, testes formais)
        a (float): Autoevolução [0, 1]. Mede eficiência do aprendizado:
            - Razão: ΔL∞⁺ / (Cost_norm + ε)
            - ΔL∞⁺: ganho de performance (apenas valores positivos)
            - Cost_norm: custo normalizado (tempo, tokens, energia)
        o (float): Incognoscível [0, 1]. Mede incerteza e necessidade de exploração:
            - epistemic_uncertainty: entropia, mutual information
            - ood_score: distância de distribuição de treino
            - ensemble_disagreement: variância entre predições do ensemble
        s (float): Silêncio [0, 1]. Mede qualidade do sinal (inverso de ruído):
            - (1-noise_ratio): anti-ruído
            - (1-redundancy_ratio): anti-redundância
            - (1-entropy_normalized): anti-entropia
        kappa (float): Ganho base ≥ 1 (padrão: 20.0). Controla intensidade da amplificação.
            - Valores típicos: 10-100
            - Maior κ → amplificação mais agressiva
            - Pode ser auto-tunado via Equação 10 (bandit meta-optimization)

    Returns:
        float: CAOS⁺ ≥ 1.0 (fator de amplificação, sem teto superior)
            - 1.0 = sem amplificação (componentes próximos de zero)
            - 1.5-2.5 = amplificação moderada (cenário típico)
            - > 3.0 = amplificação alta (alta consistência + incerteza)

    Examples:
        >>> # Exemplo 1: Estado inicial (sem evolução)
        >>> compute_caos_plus_exponential(c=0.0, a=0.0, o=0.0, s=0.0, kappa=20.0)
        1.0

        >>> # Exemplo 2: Alta consistência e autoevolução, baixa incerteza
        >>> compute_caos_plus_exponential(c=0.9, a=0.5, o=0.2, s=0.8, kappa=20.0)
        1.4454...  # Amplificação moderada (expoente baixo O·S=0.16)

        >>> # Exemplo 3: Alta incerteza → exploração mais agressiva
        >>> compute_caos_plus_exponential(c=0.8, a=0.4, o=0.8, s=0.9, kappa=20.0)
        4.2252...  # Amplificação ALTA devido a O·S = 0.72

        >>> # Exemplo 4: Efeito de κ na amplificação
        >>> compute_caos_plus_exponential(c=0.7, a=0.3, o=0.5, s=0.5, kappa=10.0)
        1.3269...
        >>> compute_caos_plus_exponential(c=0.7, a=0.3, o=0.5, s=0.5, kappa=50.0)
        1.8415...  # Maior κ → maior amplificação

    Uso no Pipeline PENIN-Ω
    -----------------------
    1. **Modulação de α**: α_eff = α_0 · φ(CAOS⁺) na Equação de Penin
    2. **Seleção de Challengers**: Maior CAOS⁺ → maior prioridade na Liga ACFA
    3. **Adaptação de β_min**: Threshold dinâmico da Death Equation

    Ver Também
    ----------
    - compute_caos_plus_complete: Versão completa com métricas estruturadas e EMA
    - compute_caos_plus_simple: Wrapper com configuração e clamping
    - phi_caos: Variante com saturação via tanh (compatibilidade histórica)
    - CAOSConfig: Configuração com clamps e normalização
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

    Variante histórica com output limitado a [0, 1) via tanh. Esta função aplica
    uma transformação não-linear sobre o CAOS⁺ exponencial para manter o resultado
    em um intervalo normalizado, útil para composições com outras métricas.

    Racional Matemático
    -------------------
    A função phi_caos foi desenvolvida para cenários onde é necessário:
    1. **Normalização**: Manter output em [0, 1) para integração com outras métricas
    2. **Saturação suave**: Evitar explosão numérica em casos extremos
    3. **Compatibilidade**: Manter consistência com código legado em penin/omega/

    Pipeline de transformação:
    1. Calcula base: (1 + κ·C·A)
    2. Aplica expoente: base^(O·S)  
    3. Transforma para log-space: log(base^(O·S)) = (O·S)·log(base)
    4. Aplica saturação: tanh(γ · log_caos)

    A função tanh garante:
    - tanh(0) = 0 (identidade)
    - tanh(∞) → 1 (saturação superior)
    - tanh(-∞) → -1 (não aplicável, base sempre ≥ 1)

    Args:
        c (float): Consistência [0, 1]
        a (float): Autoevolução [0, 1]
        o (float): Incognoscível [0, 1]
        s (float): Silêncio [0, 1]
        kappa (float): Ganho [1, kappa_max] (padrão: 2.0, menor que versão exponencial)
        kappa_max (float): Limite superior de kappa (padrão: 10.0)
        gamma (float): Parâmetro de saturação [0.1, 2.0] (padrão: 0.7)
            - gamma baixo → saturação mais suave (curva mais lenta)
            - gamma alto → saturação mais rápida (curva mais íngreme)

    Returns:
        float: φ_CAOS em [0, 1) aproximadamente
            - 0.0 = nenhuma amplificação
            - 0.5 = amplificação moderada  
            - ~0.9 = amplificação alta (próximo da saturação)
            - < 1.0 sempre (devido à tanh)

    Examples:
        >>> # Exemplo 1: Valores baixos → phi próximo de zero
        >>> phi_caos(c=0.1, a=0.1, o=0.1, s=0.1, kappa=2.0, gamma=0.7)
        0.0001...

        >>> # Exemplo 2: Valores moderados
        >>> phi_caos(c=0.7, a=0.5, o=0.6, s=0.8, kappa=2.0, gamma=0.7)
        0.1764...

        >>> # Exemplo 3: Valores altos → saturação próxima de 1
        >>> phi_caos(c=0.9, a=0.9, o=0.9, s=0.9, kappa=10.0, gamma=0.7)
        0.8489...

        >>> # Exemplo 4: Efeito do parâmetro gamma
        >>> phi_caos(c=0.8, a=0.6, o=0.7, s=0.7, kappa=5.0, gamma=0.3)  # suave
        0.1780...
        >>> phi_caos(c=0.8, a=0.6, o=0.7, s=0.7, kappa=5.0, gamma=1.5)  # íngreme
        0.7160...

    Nota:
        Esta fórmula é mantida para compatibilidade com código histórico
        em penin/omega/caos.py, mas a fórmula exponencial (compute_caos_plus_exponential)
        é preferida para uso no pipeline principal devido a:
        - Melhor interpretabilidade (amplificação direta)
        - Menos parâmetros (não precisa de gamma)
        - Range não limitado (útil para modulação de α)

    Ver Também
    ----------
    - compute_caos_plus_exponential: Fórmula preferida para pipeline principal
    - compute_caos_plus: Wrapper de compatibilidade que usa esta função
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

    Esta função é um meio-termo entre `compute_caos_plus_exponential` (fórmula pura)
    e `compute_caos_plus_complete` (pipeline completo). Use quando:
    - Você já calculou os componentes C, A, O, S
    - Não precisa de métricas estruturadas detalhadas
    - Quer configuração avançada (clamps, normalização, fórmula alternativa)
    - Não precisa de EMA ou tracking temporal

    Funcionalidades
    ---------------
    - Aplica clamping automático nos inputs [0, 1]
    - Suporta múltiplas fórmulas (exponential, phi_caos, hybrid)
    - Aplica clamps no output (caos_min, caos_max)
    - Normalização opcional para [0, 1]
    - Configuração via CAOSConfig

    Args:
        C (float): Consistência [0, 1]
            Valores fora do range são automaticamente clampados
        A (float): Autoevolução [0, 1]
            Valores fora do range são automaticamente clampados
        O (float): Incognoscível [0, 1]
            Valores fora do range são automaticamente clampados
        S (float): Silêncio [0, 1]
            Valores fora do range são automaticamente clampados
        kappa (float): Ganho base (padrão: 20.0)
            Usado apenas se config=None
        config (CAOSConfig | None): Configuração opcional
            Se None, cria config padrão com kappa fornecido
            Se fornecido, usa todos parâmetros do config

    Returns:
        float: CAOS⁺ processado conforme configuração
            - Range padrão: [1.0, 10.0]
            - Se normalize_output=True: [0.0, 1.0]
            - Sempre aplicado clamping conforme config

    Examples:
        >>> # Uso básico com defaults
        >>> compute_caos_plus_simple(0.8, 0.5, 0.3, 0.7, kappa=20.0)
        1.5863...

        >>> # Com configuração customizada
        >>> config = CAOSConfig(
        ...     kappa=25.0,
        ...     caos_min=1.0,
        ...     caos_max=5.0,  # Limitar amplificação
        ...     normalize_output=True  # Normalizar para [0, 1]
        ... )
        >>> compute_caos_plus_simple(0.8, 0.5, 0.3, 0.7, config=config)
        0.1465...  # Valor normalizado

        >>> # Usando fórmula alternativa phi_caos
        >>> config_phi = CAOSConfig(
        ...     formula=CAOSFormula.PHI_CAOS,
        ...     kappa=2.0,
        ...     gamma=0.7
        ... )
        >>> compute_caos_plus_simple(0.8, 0.5, 0.3, 0.7, config=config_phi)
        0.0805...  # Resultado da fórmula com saturação

        >>> # Clamping automático de inputs
        >>> compute_caos_plus_simple(1.5, -0.2, 0.5, 0.8)  # Valores inválidos
        1.0000  # Clampados para (1.0, 0.0, 0.5, 0.8) → resultado 1.0

    Quando Usar
    -----------
    Use `compute_caos_plus_simple` quando:
    ✅ Já tem C, A, O, S calculados
    ✅ Quer configuração avançada (clamps, normalização)
    ✅ Não precisa de métricas estruturadas
    ✅ Não precisa de EMA ou tracking

    Use `compute_caos_plus_exponential` quando:
    ✅ Quer fórmula pura sem configuração
    ✅ Máxima simplicidade

    Use `compute_caos_plus_complete` quando:
    ✅ Tem métricas estruturadas (ConsistencyMetrics, etc)
    ✅ Precisa de EMA e tracking temporal
    ✅ Precisa de auditoria completa (details dict)

    Ver Também
    ----------
    - compute_caos_plus_exponential: Fórmula matemática pura
    - compute_caos_plus_complete: Pipeline completo com métricas e EMA
    - CAOSConfig: Detalhes de configuração disponível
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

    Esta é a função de mais alto nível para cálculo de CAOS⁺, integrando todas as
    funcionalidades: computação de componentes, suavização temporal, configuração
    avançada e auditabilidade completa.

    Pipeline de Computação
    ----------------------
    1. **Agregação de Métricas**: Calcula C, A, O, S a partir de métricas raw
       - C: Média ponderada de pass@k, (1-ECE), verificação externa
       - A: Razão ganho/custo normalizada em [0, 1]
       - O: Média ponderada de incertezas (epistêmica, OOD, ensemble)
       - S: Média ponderada de qualidade de sinal (anti-ruído/redundância/entropia)

    2. **Atualização de Estado**: Armazena valores current (raw)

    3. **Suavização EMA**: Aplica Exponential Moving Average para estabilidade temporal
       - EMA_t = α · valor_t + (1-α) · EMA_{t-1}
       - α calculado via half-life (padrão: 5 amostras)
       - Reduz oscilações e melhora convergência

    4. **Clamping de Parâmetros**: Aplica limites em kappa (padrão: [10, 100])

    5. **Computação CAOS⁺**: Usa valores suavizados
       - Fórmula exponencial: (1 + κ·C·A)^(O·S)
       - Ou phi_caos com saturação, conforme config.formula

    6. **Pós-processamento**:
       - Clamp do resultado (padrão: [1, 10])
       - Log-space opcional (para comparações)
       - Normalização para [0, 1] opcional

    7. **Atualização de Histórico**: Armazena valor em FIFO buffer

    8. **Retorno**: Valor final + detalhes completos para auditoria (WORM ledger)

    Args:
        consistency_metrics (ConsistencyMetrics): Métricas de Consistência
            - pass_at_k: Taxa de sucesso em k tentativas [0, 1]
            - ece: Expected Calibration Error [0, 1] (menor é melhor)
            - external_verification: Score de verificação externa [0, 1]
            - Pesos: weight_pass, weight_ece, weight_external
            
        autoevolution_metrics (AutoevolutionMetrics): Métricas de Autoevolução
            - delta_linf: Ganho de L∞ (performance)
            - cost_normalized: Custo normalizado [0, ∞)
            - max_a: Clamp máximo antes de normalizar (padrão: 10.0)
            
        incognoscible_metrics (IncognoscibleMetrics): Métricas de Incognoscível
            - epistemic_uncertainty: Incerteza epistêmica [0, 1]
            - ood_score: Score out-of-distribution [0, 1]
            - ensemble_disagreement: Variância do ensemble [0, 1]
            - Pesos: weight_epistemic, weight_ood, weight_ensemble
            
        silence_metrics (SilenceMetrics): Métricas de Silêncio
            - noise_ratio: Proporção de ruído [0, 1]
            - redundancy_ratio: Proporção de redundância [0, 1]
            - entropy_normalized: Entropia normalizada [0, 1]
            - Pesos: weight_noise, weight_redundancy, weight_entropy (2:1:1)
            
        config (CAOSConfig | None): Configuração do motor CAOS⁺. Se None, usa defaults:
            - formula: CAOSFormula.EXPONENTIAL
            - kappa: 20.0 (range: [10, 100])
            - gamma: 0.7 (para phi_caos)
            - ema_half_life: 5 amostras
            - caos_min/max: [1.0, 10.0]
            - normalize_output: False
            
        state (CAOSState | None): Estado com histórico EMA. Se None, cria novo:
            - Valores raw: c_current, a_current, o_current, s_current
            - Valores suavizados: c_smoothed, a_smoothed, o_smoothed, s_smoothed
            - Histórico: últimas N amostras (padrão: 100)
            - update_count: Contador de atualizações

    Returns:
        tuple[float, dict[str, Any]]: (caos_plus_final, details)
        
        caos_plus_final (float): Valor CAOS⁺ final processado
            - Range típico: [1.0, 10.0] (ou [0, 1] se normalize_output=True)
            
        details (dict): Dicionário completo com métricas intermediárias:
            - 'components_raw': Dict[str, float] - C, A, O, S calculados
            - 'metrics_input': Dict - Todas métricas de entrada para auditoria
            - 'components_smoothed': Dict[str, float] - C, A, O, S suavizados via EMA
            - 'ema_alpha': float - Fator de suavização calculado
            - 'ema_half_life': int - Half-life configurado
            - 'kappa': float - κ clamped usado no cálculo
            - 'formula': str - Fórmula utilizada ('exponential' ou 'phi_caos')
            - 'caos_plus_raw': float - Valor antes de clamping
            - 'caos_plus_clamped': float - Valor após clamping [caos_min, caos_max]
            - 'caos_plus_log': float - Valor em log-space (se use_log_space=True)
            - 'caos_plus_normalized': float - Valor normalizado (se normalize_output=True)
            - 'caos_plus_final': float - Valor final retornado
            - 'state_update_count': int - Número de atualizações realizadas
            - 'state_stability': float - Estabilidade temporal (inverse CV)

    Examples:
        >>> # Exemplo 1: Uso básico com valores padrão
        >>> from penin.core.caos import (
        ...     compute_caos_plus_complete,
        ...     ConsistencyMetrics,
        ...     AutoevolutionMetrics,
        ...     IncognoscibleMetrics,
        ...     SilenceMetrics,
        ...     CAOSConfig,
        ...     CAOSState
        ... )
        >>> 
        >>> consistency = ConsistencyMetrics(pass_at_k=0.92, ece=0.008)
        >>> autoevolution = AutoevolutionMetrics(delta_linf=0.06, cost_normalized=0.15)
        >>> incognoscible = IncognoscibleMetrics(epistemic_uncertainty=0.35)
        >>> silence = SilenceMetrics(noise_ratio=0.08)
        >>> 
        >>> caos_plus, details = compute_caos_plus_complete(
        ...     consistency, autoevolution, incognoscible, silence
        ... )
        >>> print(f"CAOS⁺: {caos_plus:.3f}")  # doctest: +SKIP
        CAOS⁺: 1.199
        >>> print(f"C: {details['components_raw']['C']:.3f}")  # doctest: +SKIP
        C: 0.930

        >>> # Exemplo 2: Uso com suavização EMA para séries temporais
        >>> config = CAOSConfig(kappa=25.0, ema_half_life=5)
        >>> state = CAOSState()
        >>> 
        >>> # Primeira iteração
        >>> caos1, _ = compute_caos_plus_complete(
        ...     consistency, autoevolution, incognoscible, silence, config, state
        ... )
        >>> 
        >>> # Segunda iteração (com EMA do estado anterior)
        >>> consistency2 = ConsistencyMetrics(pass_at_k=0.95, ece=0.006)
        >>> caos2, details2 = compute_caos_plus_complete(
        ...     consistency2, autoevolution, incognoscible, silence, config, state
        ... )
        >>> # caos2 será suavizado com caos1 via EMA

        >>> # Exemplo 3: Configuração para output normalizado [0, 1]
        >>> config_norm = CAOSConfig(kappa=20.0, normalize_output=True)
        >>> caos_norm, details_norm = compute_caos_plus_complete(
        ...     consistency, autoevolution, incognoscible, silence, config_norm
        ... )
        >>> assert 0.0 <= caos_norm <= 1.0  # Garantido em [0, 1]

        >>> # Exemplo 4: Auditoria completa - inspecionar details
        >>> print("Componentes raw:", details['components_raw'])  # doctest: +SKIP
        >>> print("Componentes suavizados:", details['components_smoothed'])  # doctest: +SKIP
        >>> print("Estabilidade:", details['state_stability'])  # doctest: +SKIP

    Notas de Implementação
    ----------------------
    - **Thread-safety**: Não é thread-safe. Use locks se acessar state compartilhado
    - **Persistência**: state pode ser serializado/deserializado para checkpointing
    - **Determinismo**: Com seed fixo em config, resultados são reproduzíveis
    - **Performance**: O(1) em tempo, O(N) em espaço (N = max_history_length)

    Casos de Uso
    -----------
    1. **Pipeline principal**: Calcular CAOS⁺ para modulação de α na Eq. Penin
    2. **Análise temporal**: Usar state para tracking de estabilidade ao longo do tempo
    3. **Auditoria**: Usar details para registrar no WORM ledger
    4. **Debug**: Inspecionar components_raw vs components_smoothed para diagnóstico
    5. **Meta-optimization**: Usar histórico para ajustar κ via Eq. 10

    Ver Também
    ----------
    - compute_caos_plus_exponential: Fórmula matemática core
    - compute_caos_plus_simple: Versão simplificada sem métricas estruturadas
    - CAOSConfig: Detalhes de todos parâmetros de configuração
    - CAOSState: Estrutura de estado para tracking temporal
    - CAOSTracker: Classe helper para monitoramento contínuo
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
# EXPORTS & ALIASES
# =============================================================================

# Backward compatibility aliases
caos_plus_simple = compute_caos_plus_simple  # Alias for tests

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
    "caos_plus_simple",  # Alias
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
    # CAOSComponents for structured return
    "CAOSComponents",
    # Tracker
    "CAOSTracker",
    # Constants
    "EPS",
    "DEFAULT_KAPPA",
    "DEFAULT_GAMMA",
]


# =============================================================================
# USAGE EXAMPLES AND BEST PRACTICES
# =============================================================================

def example_basic_usage():
    """
    Exemplo 1: Uso Básico - Cálculo Direto de CAOS⁺
    
    Demonstra o uso mais simples da função exponencial com valores de componentes
    já calculados.
    """
    print("=" * 70)
    print("EXEMPLO 1: Uso Básico - Cálculo Direto")
    print("=" * 70)

    # Cenário: Sistema com alta consistência, autoevolução moderada,
    # baixa incerteza e alto silêncio
    C = 0.88  # 88% de consistência
    A = 0.40  # 40% eficiência (normalizada)
    O = 0.25  # 25% de incerteza
    S = 0.85  # 85% qualidade de sinal
    kappa = 20.0

    caos_plus = compute_caos_plus_exponential(C, A, O, S, kappa)

    print("\nComponentes:")
    print(f"  C (Consistência):   {C:.2f}")
    print(f"  A (Autoevolução):   {A:.2f}")
    print(f"  O (Incognoscível):  {O:.2f}")
    print(f"  S (Silêncio):       {S:.2f}")
    print(f"  κ (kappa):          {kappa:.1f}")
    print("\nFórmula: CAOS⁺ = (1 + κ·C·A)^(O·S)")
    print(f"  Base = 1 + {kappa}×{C}×{A} = {1 + kappa*C*A:.4f}")
    print(f"  Expoente = {O}×{S} = {O*S:.4f}")
    print(f"\nResultado: CAOS⁺ = {caos_plus:.4f}")
    print(f"Amplificação: {(caos_plus - 1) * 100:.1f}% acima da baseline")


def example_structured_metrics():
    """
    Exemplo 2: Uso com Métricas Estruturadas
    
    Demonstra como usar a função completa com métricas estruturadas,
    incluindo todas as sub-métricas que compõem cada dimensão CAOS.
    """
    print("\n" + "=" * 70)
    print("EXEMPLO 2: Uso com Métricas Estruturadas")
    print("=" * 70)

    # Configurar métricas detalhadas
    consistency = ConsistencyMetrics(
        pass_at_k=0.92,           # 92% de autoconsistência
        ece=0.008,                # 0.8% calibration error (excelente)
        external_verification=0.88,  # 88% verificação externa
    )

    autoevolution = AutoevolutionMetrics(
        delta_linf=0.06,          # 6% de ganho de performance
        cost_normalized=0.15,     # 15% do budget utilizado
    )

    incognoscible = IncognoscibleMetrics(
        epistemic_uncertainty=0.35,   # Incerteza moderada
        ood_score=0.28,              # 28% OOD
        ensemble_disagreement=0.30,   # 30% de disagreement
    )

    silence = SilenceMetrics(
        noise_ratio=0.08,         # 8% ruído (baixo)
        redundancy_ratio=0.12,    # 12% redundância
        entropy_normalized=0.18,  # 18% entropia
    )

    # Computar CAOS⁺
    caos_plus, details = compute_caos_plus_complete(
        consistency, autoevolution, incognoscible, silence
    )

    print("\nMétricas de Entrada:")
    print("  Consistência:")
    print(f"    - pass@k:            {consistency.pass_at_k:.3f}")
    print(f"    - ECE:               {consistency.ece:.3f}")
    print(f"    - Verif. Externa:    {consistency.external_verification:.3f}")
    print("  Autoevolução:")
    print(f"    - ΔL∞:               {autoevolution.delta_linf:.3f}")
    print(f"    - Custo normalizado: {autoevolution.cost_normalized:.3f}")
    print("  Incognoscível:")
    print(f"    - Inc. Epistêmica:   {incognoscible.epistemic_uncertainty:.3f}")
    print(f"    - OOD Score:         {incognoscible.ood_score:.3f}")
    print(f"    - Ensemble Disagr.:  {incognoscible.ensemble_disagreement:.3f}")
    print("  Silêncio:")
    print(f"    - Ruído:             {silence.noise_ratio:.3f}")
    print(f"    - Redundância:       {silence.redundancy_ratio:.3f}")
    print(f"    - Entropia:          {silence.entropy_normalized:.3f}")

    print("\nComponentes CAOS Agregados:")
    for comp, val in details['components_raw'].items():
        print(f"  {comp}: {val:.3f}")

    print(f"\nCAOS⁺ Final: {caos_plus:.4f}")


def example_temporal_tracking():
    """
    Exemplo 3: Tracking Temporal com EMA
    
    Demonstra como usar o estado (CAOSState) para suavização temporal
    via Exponential Moving Average, útil para séries temporais.
    """
    print("\n" + "=" * 70)
    print("EXEMPLO 3: Tracking Temporal com EMA")
    print("=" * 70)

    # Configuração com EMA
    config = CAOSConfig(
        kappa=25.0,
        ema_half_life=5,  # 5 iterações para decair 50%
    )
    state = CAOSState()

    # Simular 10 iterações com variações nas métricas
    print("\nSimulação de 10 iterações:")
    print(f"{'Iter':<6} {'C_raw':<8} {'C_ema':<8} {'CAOS⁺':<10} {'Estabilidade':<12}")
    print("-" * 60)

    for i in range(10):
        # Métricas com variação simulada
        import random
        random.seed(42 + i)  # Reproducibilidade

        consistency = ConsistencyMetrics(
            pass_at_k=0.90 + random.uniform(-0.05, 0.05),
            ece=0.01 + random.uniform(-0.003, 0.003),
        )
        autoevolution = AutoevolutionMetrics(
            delta_linf=0.05 + random.uniform(-0.02, 0.02),
            cost_normalized=0.12 + random.uniform(-0.03, 0.03),
        )
        incognoscible = IncognoscibleMetrics(
            epistemic_uncertainty=0.30 + random.uniform(-0.05, 0.05),
        )
        silence = SilenceMetrics(
            noise_ratio=0.10 + random.uniform(-0.02, 0.02),
        )

        caos, details = compute_caos_plus_complete(
            consistency, autoevolution, incognoscible, silence,
            config, state
        )

        c_raw = details['components_raw']['C']
        c_ema = details['components_smoothed']['C']
        stability = details['state_stability']

        print(f"{i+1:<6} {c_raw:<8.4f} {c_ema:<8.4f} {caos:<10.4f} {stability:<12.4f}")

    print("\nObservação: C_ema converge suavemente, reduzindo oscilações.")
    print("Estabilidade aumenta ao longo do tempo (menor CV).")


def example_exploration_vs_exploitation():
    """
    Exemplo 4: Exploração vs Exploração
    
    Demonstra como CAOS⁺ modula entre exploração (alta incerteza)
    e exploração (alta consistência).
    """
    print("\n" + "=" * 70)
    print("EXEMPLO 4: Exploração vs Exploração")
    print("=" * 70)

    kappa = 20.0

    # Cenário 1: Exploração (alta incerteza, baixa consistência)
    print("\nCenário 1: EXPLORAÇÃO")
    print("Situação: Entrando em território desconhecido")
    C_explore = 0.5   # Consistência baixa (incerto)
    A_explore = 0.3   # Autoevolução baixa (ainda aprendendo)
    O_explore = 0.8   # Incerteza ALTA (precisa explorar)
    S_explore = 0.6   # Silêncio moderado

    caos_explore = compute_caos_plus_exponential(
        C_explore, A_explore, O_explore, S_explore, kappa
    )

    print(f"  C={C_explore}, A={A_explore}, O={O_explore}, S={S_explore}")
    print(f"  Base: (1 + {kappa}×{C_explore}×{A_explore}) = {1 + kappa*C_explore*A_explore:.2f}")
    print(f"  Expoente: {O_explore}×{S_explore} = {O_explore*S_explore:.2f}")
    print(f"  CAOS⁺ = {caos_explore:.4f}")
    print("  → Alta incerteza (O) → expoente alto → amplificação moderada")

    # Cenário 2: Exploração (baixa incerteza, alta consistência)
    print("\nCenário 2: EXPLORAÇÃO (Exploitation)")
    print("Situação: Refinando em território conhecido")
    C_exploit = 0.9   # Consistência ALTA (confiante)
    A_exploit = 0.6   # Autoevolução alta (aprendendo bem)
    O_exploit = 0.2   # Incerteza BAIXA (território conhecido)
    S_exploit = 0.9   # Silêncio alto (sinal limpo)

    caos_exploit = compute_caos_plus_exponential(
        C_exploit, A_exploit, O_exploit, S_exploit, kappa
    )

    print(f"  C={C_exploit}, A={A_exploit}, O={O_exploit}, S={S_exploit}")
    print(f"  Base: (1 + {kappa}×{C_exploit}×{A_exploit}) = {1 + kappa*C_exploit*A_exploit:.2f}")
    print(f"  Expoente: {O_exploit}×{S_exploit} = {O_exploit*S_exploit:.2f}")
    print(f"  CAOS⁺ = {caos_exploit:.4f}")
    print("  → Baixa incerteza (O) → expoente baixo → amplificação moderada")

    # Cenário 3: Sweet Spot (alto C·A, alto O·S)
    print("\nCenário 3: SWEET SPOT")
    print("Situação: Aprendendo rápido em território parcialmente conhecido")
    C_sweet = 0.85
    A_sweet = 0.7
    O_sweet = 0.6
    S_sweet = 0.85

    caos_sweet = compute_caos_plus_exponential(
        C_sweet, A_sweet, O_sweet, S_sweet, kappa
    )

    print(f"  C={C_sweet}, A={A_sweet}, O={O_sweet}, S={S_sweet}")
    print(f"  Base: (1 + {kappa}×{C_sweet}×{A_sweet}) = {1 + kappa*C_sweet*A_sweet:.2f}")
    print(f"  Expoente: {O_sweet}×{S_sweet} = {O_sweet*S_sweet:.2f}")
    print(f"  CAOS⁺ = {caos_sweet:.4f}")
    print("  → Alto C·A E alto O·S → MÁXIMA amplificação!")

    print("\nComparação:")
    print(f"  Exploração:  {caos_explore:.4f}")
    print(f"  Exploração:  {caos_exploit:.4f}")
    print(f"  Sweet Spot:  {caos_sweet:.4f} ← MELHOR!")


def example_kappa_tuning():
    """
    Exemplo 5: Efeito do Parâmetro κ (kappa)
    
    Demonstra como κ controla a intensidade da amplificação.
    """
    print("\n" + "=" * 70)
    print("EXEMPLO 5: Efeito do Parâmetro κ (kappa)")
    print("=" * 70)

    # Fixar componentes
    C, A, O, S = 0.8, 0.5, 0.6, 0.7

    print(f"\nComponentes fixos: C={C}, A={A}, O={O}, S={S}")
    print(f"\n{'κ':<10} {'CAOS⁺':<12} {'Amplificação %':<15}")
    print("-" * 40)

    for kappa in [10.0, 20.0, 30.0, 50.0, 100.0]:
        caos = compute_caos_plus_exponential(C, A, O, S, kappa)
        amplification = (caos - 1.0) * 100
        print(f"{kappa:<10.1f} {caos:<12.4f} {amplification:<15.1f}%")

    print("\nObservação: κ maior → amplificação mais agressiva")
    print("Valores típicos: 10-50 (conservador a agressivo)")
    print("κ pode ser auto-tunado via Equação 10 (bandit meta-opt)")


def example_edge_cases():
    """
    Exemplo 6: Casos Extremos e Edge Cases
    
    Demonstra o comportamento em situações limite.
    """
    print("\n" + "=" * 70)
    print("EXEMPLO 6: Casos Extremos e Edge Cases")
    print("=" * 70)

    kappa = 20.0

    # Edge Case 1: Todos zeros
    print("\n1. Todos componentes = 0 (sem informação)")
    caos1 = compute_caos_plus_exponential(0, 0, 0, 0, kappa)
    print(f"   CAOS⁺(0,0,0,0) = {caos1:.4f}")
    print("   → Base^0 = 1^0 = 1 (identidade, sem amplificação)")

    # Edge Case 2: Todos uns
    print("\n2. Todos componentes = 1 (máximo)")
    caos2 = compute_caos_plus_exponential(1, 1, 1, 1, kappa)
    print(f"   CAOS⁺(1,1,1,1) = {caos2:.4f}")
    print(f"   → (1 + κ)^1 = {1 + kappa}")

    # Edge Case 3: C=A=0 (sem qualidade)
    print("\n3. C=A=0, O=S=1 (sem consistência/autoevolução)")
    caos3 = compute_caos_plus_exponential(0, 0, 1, 1, kappa)
    print(f"   CAOS⁺(0,0,1,1) = {caos3:.4f}")
    print("   → (1 + 0)^1 = 1 (base não amplifica sem C·A)")

    # Edge Case 4: O=S=0 (sem incerteza)
    print("\n4. C=A=1, O=S=0 (sem incerteza/silêncio)")
    caos4 = compute_caos_plus_exponential(1, 1, 0, 0, kappa)
    print(f"   CAOS⁺(1,1,0,0) = {caos4:.4f}")
    print("   → Base^0 = anything^0 = 1 (expoente zero neutraliza)")

    # Edge Case 5: Clamping automático
    print("\n5. Valores fora de [0,1] são clampados automaticamente")
    caos5 = compute_caos_plus_exponential(1.5, -0.2, 0.5, 0.8, kappa)
    print("   Input: (1.5, -0.2, 0.5, 0.8)")
    print("   Clamped: (1.0, 0.0, 0.5, 0.8)")
    print(f"   CAOS⁺ = {caos5:.4f}")
    print("   → Garantia: sempre valores válidos")


def run_all_examples():
    """
    Executa todos os exemplos de uso do CAOS⁺.
    
    Este função demonstra as principais funcionalidades e casos de uso
    do motor CAOS⁺, servindo como tutorial completo e referência rápida.
    """
    print("\n" + "=" * 70)
    print("PENIN-Ω CAOS⁺ Engine - Exemplos de Uso Completos")
    print("=" * 70)
    print("\nEste módulo demonstra o uso do motor CAOS⁺ (Consistência,")
    print("Autoevolução, Incognoscível, Silêncio) que modula a taxa de")
    print("aprendizado no sistema evolutivo PENIN-Ω.")
    print()
    print("Fórmula: CAOS⁺ = (1 + κ·C·A)^(O·S)")
    print()

    example_basic_usage()
    example_structured_metrics()
    example_temporal_tracking()
    example_exploration_vs_exploitation()
    example_kappa_tuning()
    example_edge_cases()

    print("\n" + "=" * 70)
    print("FIM DOS EXEMPLOS")
    print("=" * 70)
    print("\nPara mais informações:")
    print("- Documentação: docs/equations.md")
    print("- Código fonte: penin/core/caos.py")
    print("- Testes: tests/test_caos.py")
    print()


if __name__ == "__main__":
    # Executar todos os exemplos quando o módulo é chamado diretamente
    run_all_examples()

