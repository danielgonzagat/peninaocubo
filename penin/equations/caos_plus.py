"""
Equação 3: Motor CAOS⁺ — Consistência, Autoevolução, Incognoscível, Silêncio
============================================================================

Forma: CAOS⁺ = (1 + κ · C · A)^(O · S)

Implementa motor de evolução que modula passo e exploração baseado em
quatro dimensões fundamentais:

Dimensões (todas em [0,1]):
---------------------------
- C (Consistência): média de pass@k, (1-ECE), verificação externa
- A (Autoevolução): ganho por custo (ΔL∞ / Cost)
- O (Incognoscível): incerteza epistêmica/OOD → mais O libera exploração
- S (Silêncio): anti-ruído/redundância/entropia

Parâmetros:
-----------
- κ (kappa): ganho base ≥ 20 (auto-tunável via Eq. 10)
- γ (gamma): parâmetro de saturação para φ(z) = tanh(γ·z)

Propriedades:
-------------
- CAOS⁺ ≥ 1 sempre (base multiplicativa)
- Alto C·A amplifica exploração
- Alto O·S aumenta expoente (mais agressivo)
- Suavização via EMA para estabilidade
- Clamps para evitar explosão

Uso:
----
Modula α_t^{eff} na Equação de Penin (Eq. 1) e desempata challengers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CAOSComponent(Enum):
    """Componentes do CAOS⁺"""

    CONSISTENCY = "C"  # Consistência
    AUTOEVOLUTION = "A"  # Autoevolução
    INCOGNOSCIBLE = "O"  # Incognoscível/OOD
    SILENCE = "S"  # Silêncio


@dataclass
class ConsistencyMetrics:
    """
    Métricas de Consistência (C)

    C = média(pass@k, 1-ECE, v_ext)
    """

    # Pass@k: taxa de sucessos em k tentativas
    pass_at_k: float = 0.9
    k_samples: int = 10

    # Expected Calibration Error (calibração de confiança)
    ece: float = 0.01  # Menor é melhor, típico < 0.05

    # Verificação externa (oracle, testes formais)
    external_verification: float = 0.85  # Score de verificação externa

    # Pesos para agregação
    weight_pass: float = 0.4
    weight_ece: float = 0.3
    weight_external: float = 0.3

    def compute_c(self) -> float:
        """Calcula C (Consistência) em [0, 1]"""
        # Normalizar componentes
        pass_norm = max(0.0, min(1.0, self.pass_at_k))
        ece_norm = max(0.0, min(1.0, 1.0 - self.ece))  # Inverter ECE
        ext_norm = max(0.0, min(1.0, self.external_verification))

        # Média ponderada
        c = self.weight_pass * pass_norm + self.weight_ece * ece_norm + self.weight_external * ext_norm

        return max(0.0, min(1.0, c))


@dataclass
class AutoevolutionMetrics:
    """
    Métricas de Autoevolução (A)

    A = ΔL∞⁺ / (Cost_norm + ε)

    Mede ganho de performance por unidade de custo
    """

    # Ganho de L∞ (só positivo)
    delta_linf: float = 0.05

    # Custo normalizado [0, ∞)
    cost_normalized: float = 0.1

    # Estabilizador
    epsilon: float = 1e-3

    # Clamp máximo para A (evitar explosão)
    max_a: float = 10.0

    def compute_a(self) -> float:
        """Calcula A (Autoevolução) em [0, max_a]"""
        # Só considera ganhos positivos
        delta_positive = max(0.0, self.delta_linf)

        # Ganho por custo
        cost_denom = max(self.epsilon, self.cost_normalized + self.epsilon)
        a = delta_positive / cost_denom

        # Clamp
        a = max(0.0, min(self.max_a, a))

        # Normalizar para [0, 1] opcional (ou manter como multiplicador)
        # Para manter amplificação, não normaliza aqui
        # Mas para CAOS⁺, vamos normalizar para [0, 1]
        a_normalized = a / self.max_a

        return max(0.0, min(1.0, a_normalized))


@dataclass
class IncognoscibleMetrics:
    """
    Métricas de Incognoscível (O)

    O = média(incerteza_epistêmica, OOD_score, ensemble_disagreement)

    Mede grau de desconhecimento → mais O libera exploração
    """

    # Incerteza epistêmica (ex: entropy, mutual information)
    epistemic_uncertainty: float = 0.3

    # Out-of-Distribution score
    ood_score: float = 0.25  # Distância de distribuição de treino

    # Disagreement em ensemble (variância de predições)
    ensemble_disagreement: float = 0.2

    # Pesos
    weight_epistemic: float = 0.4
    weight_ood: float = 0.3
    weight_ensemble: float = 0.3

    def compute_o(self) -> float:
        """Calcula O (Incognoscível) em [0, 1]"""
        # Normalizar componentes
        epist_norm = max(0.0, min(1.0, self.epistemic_uncertainty))
        ood_norm = max(0.0, min(1.0, self.ood_score))
        ens_norm = max(0.0, min(1.0, self.ensemble_disagreement))

        # Média ponderada
        o = self.weight_epistemic * epist_norm + self.weight_ood * ood_norm + self.weight_ensemble * ens_norm

        return max(0.0, min(1.0, o))


@dataclass
class SilenceMetrics:
    """
    Métricas de Silêncio (S)

    S = v1·(1-ruído) + v2·(1-redundância) + v3·(1-entropia)

    Mede qualidade de sinal (anti-ruído, anti-redundância, anti-entropia)
    Ponderação sugerida: v1:v2:v3 = 2:1:1
    """

    # Ruído: proporção de informação ruidosa
    noise_ratio: float = 0.1  # 10% ruído

    # Redundância: proporção de informação duplicada
    redundancy_ratio: float = 0.15  # 15% redundante

    # Entropia normalizada: desordem/imprevisibilidade
    entropy_normalized: float = 0.2  # 20% entropia

    # Pesos (v1:v2:v3 = 2:1:1)
    weight_noise: float = 0.5  # 2/4
    weight_redundancy: float = 0.25  # 1/4
    weight_entropy: float = 0.25  # 1/4

    def compute_s(self) -> float:
        """Calcula S (Silêncio) em [0, 1]"""
        # Inverter métricas (queremos BAIXO ruído/redundância/entropia)
        anti_noise = 1.0 - max(0.0, min(1.0, self.noise_ratio))
        anti_redundancy = 1.0 - max(0.0, min(1.0, self.redundancy_ratio))
        anti_entropy = 1.0 - max(0.0, min(1.0, self.entropy_normalized))

        # Média ponderada
        s = (
            self.weight_noise * anti_noise
            + self.weight_redundancy * anti_redundancy
            + self.weight_entropy * anti_entropy
        )

        return max(0.0, min(1.0, s))


@dataclass
class CAOSConfig:
    """Configuração do motor CAOS⁺"""

    # Ganho base κ ≥ 20 (auto-tunável)
    kappa: float = 20.0

    # Clamps para segurança
    kappa_min: float = 10.0
    kappa_max: float = 100.0

    # EMA half-life para suavização (em número de amostras)
    ema_half_life: int = 5

    # Clamp do resultado CAOS⁺
    caos_min: float = 1.0  # Base mínima
    caos_max: float = 10.0  # Teto de amplificação

    # Log-space para comparação (opcional)
    use_log_space: bool = False

    # Normalizar CAOS⁺ para [0, 1] após computação
    normalize_output: bool = False


@dataclass
class CAOSState:
    """
    Estado do CAOS⁺ com histórico EMA

    Mantém valores suavizados via Exponential Moving Average
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
        Atualiza EMA

        EMA_t = α · value_t + (1-α) · EMA_{t-1}

        Args:
            new_value: Novo valor observado
            current_ema: EMA atual
            alpha: Fator de suavização (0 = sem mudança, 1 = esquece passado)

        Returns:
            EMA atualizado
        """
        if self.update_count == 0:
            # Primeira atualização: inicializar EMA com valor observado
            return new_value

        return alpha * new_value + (1.0 - alpha) * current_ema

    def add_to_history(self, caos_value: float):
        """Adiciona valor ao histórico"""
        self.history.append(caos_value)
        if len(self.history) > self.max_history_length:
            self.history.pop(0)


def compute_ema_alpha(half_life: int) -> float:
    """
    Calcula α para EMA dado half-life

    Half-life: número de amostras para peso cair para 50%

    Args:
        half_life: Half-life em número de amostras

    Returns:
        α (fator de suavização)
    """
    if half_life <= 0:
        return 1.0  # Sem suavização

    # α = 1 - exp(-ln(2) / half_life)
    return 1.0 - math.exp(-math.log(2.0) / half_life)


def compute_caos_plus_raw(
    c: float,
    a: float,
    o: float,
    s: float,
    kappa: float,
) -> float:
    """
    Calcula CAOS⁺ = (1 + κ · C · A)^(O · S)

    Args:
        c: Consistência [0, 1]
        a: Autoevolução [0, 1]
        o: Incognoscível [0, 1]
        s: Silêncio [0, 1]
        kappa: Ganho base ≥ 20

    Returns:
        CAOS⁺ ≥ 1
    """
    # Clamp inputs para segurança
    c = max(0.0, min(1.0, c))
    a = max(0.0, min(1.0, a))
    o = max(0.0, min(1.0, o))
    s = max(0.0, min(1.0, s))
    kappa = max(1.0, kappa)  # Mínimo 1

    # Base: (1 + κ · C · A)
    base = 1.0 + kappa * c * a

    # Expoente: O · S
    exponent = o * s

    # CAOS⁺
    caos_plus = base**exponent

    return caos_plus


def compute_caos_plus_complete(
    consistency_metrics: ConsistencyMetrics,
    autoevolution_metrics: AutoevolutionMetrics,
    incognoscible_metrics: IncognoscibleMetrics,
    silence_metrics: SilenceMetrics,
    config: CAOSConfig | None = None,
    state: CAOSState | None = None,
) -> tuple[float, dict[str, Any]]:
    """
    Calcula CAOS⁺ completo com todas as métricas e suavização EMA

    Args:
        consistency_metrics: Métricas de C
        autoevolution_metrics: Métricas de A
        incognoscible_metrics: Métricas de O
        silence_metrics: Métricas de S
        config: Configuração do CAOS⁺
        state: Estado com histórico EMA

    Returns:
        (caos_plus, details_dict)
        - caos_plus: Valor CAOS⁺
        - details_dict: Detalhes da computação
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

    details["components_raw"] = {
        "C": c_raw,
        "A": a_raw,
        "O": o_raw,
        "S": s_raw,
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

    # 4. Aplicar clamps em kappa
    kappa_clamped = max(config.kappa_min, min(config.kappa_max, config.kappa))
    details["kappa"] = kappa_clamped

    # 5. Computar CAOS⁺ com valores suavizados
    caos_plus = compute_caos_plus_raw(
        c=state.c_smoothed,
        a=state.a_smoothed,
        o=state.o_smoothed,
        s=state.s_smoothed,
        kappa=kappa_clamped,
    )

    details["caos_plus_raw"] = caos_plus

    # 6. Aplicar clamps no resultado
    caos_plus_clamped = max(config.caos_min, min(config.caos_max, caos_plus))
    details["caos_plus_clamped"] = caos_plus_clamped

    # 7. Log-space (opcional, para comparação)
    if config.use_log_space:
        caos_log = math.log(caos_plus_clamped)
        details["caos_plus_log"] = caos_log

    # 8. Normalizar saída (opcional, para [0, 1])
    if config.normalize_output:
        # Normalizar CAOS⁺ de [caos_min, caos_max] para [0, 1]
        caos_normalized = (caos_plus_clamped - config.caos_min) / (config.caos_max - config.caos_min)
        caos_plus_final = max(0.0, min(1.0, caos_normalized))
        details["caos_plus_normalized"] = caos_plus_final
    else:
        caos_plus_final = caos_plus_clamped

    # 9. Atualizar estado
    state.caos_plus = caos_plus_final
    state.add_to_history(caos_plus_final)
    state.update_count += 1

    details["state_update_count"] = state.update_count
    details["caos_plus_final"] = caos_plus_final

    return caos_plus_final, details


# Overload simplificado (quando já se tem C, A, O, S)
def compute_caos_plus_simple(
    C: float,
    A: float,
    O: float,
    S: float,
    kappa: float = 20.0,
    config: CAOSConfig | None = None,
) -> float:
    """
    Versão simplificada quando já se tem C, A, O, S

    Args:
        C: Consistência [0, 1]
        A: Autoevolução [0, 1]
        O: Incognoscível [0, 1]
        S: Silêncio [0, 1]
        kappa: Ganho base
        config: Configuração opcional

    Returns:
        CAOS⁺
    """
    if config is None:
        config = CAOSConfig(kappa=kappa)

    # Clamp inputs
    C = max(0.0, min(1.0, C))
    A = max(0.0, min(1.0, A))
    O = max(0.0, min(1.0, O))
    S = max(0.0, min(1.0, S))

    # Computar
    caos_raw = compute_caos_plus_raw(C, A, O, S, config.kappa)

    # Clamp
    caos_plus = max(config.caos_min, min(config.caos_max, caos_raw))

    # Normalizar se configurado
    if config.normalize_output:
        caos_plus = (caos_plus - config.caos_min) / (config.caos_max - config.caos_min)

    return caos_plus


# Exemplo de uso
def example_caos_computation():
    """Exemplo de computação de CAOS⁺"""

    # Métricas de Consistência
    consistency = ConsistencyMetrics(
        pass_at_k=0.92,
        ece=0.008,
        external_verification=0.88,
    )

    # Métricas de Autoevolução
    autoevolution = AutoevolutionMetrics(
        delta_linf=0.06,  # 6% de ganho
        cost_normalized=0.15,  # 15% do budget
    )

    # Métricas de Incognoscível
    incognoscible = IncognoscibleMetrics(
        epistemic_uncertainty=0.35,
        ood_score=0.28,
        ensemble_disagreement=0.30,
    )

    # Métricas de Silêncio
    silence = SilenceMetrics(
        noise_ratio=0.08,
        redundancy_ratio=0.12,
        entropy_normalized=0.18,
    )

    # Configuração
    config = CAOSConfig(
        kappa=25.0,
        ema_half_life=5,
        normalize_output=False,
    )

    # Estado
    state = CAOSState()

    # Computar CAOS⁺
    caos_plus, details = compute_caos_plus_complete(consistency, autoevolution, incognoscible, silence, config, state)

    print(f"CAOS⁺ = {caos_plus:.4f}")
    print(
        f"Components (smoothed): C={details['components_smoothed']['C']:.3f}, "
        f"A={details['components_smoothed']['A']:.3f}, "
        f"O={details['components_smoothed']['O']:.3f}, "
        f"S={details['components_smoothed']['S']:.3f}"
    )
    print(f"κ = {details['kappa']:.1f}")

    return caos_plus, details


if __name__ == "__main__":
    example_caos_computation()
