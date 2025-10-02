"""
SR-Ω∞ Engine - Self-Reflection Não-Compensatório
===============================================

Implementa SR-Ω∞ (autoconsciência, ética, autocorreção, metacognição)
via média harmônica ou min-soft p-norm, garantindo comportamento
não-compensatório onde uma dimensão baixa compromete o score total.
"""

import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class SRAggregationMethod(Enum):
    """Métodos de agregação para SR"""

    HARMONIC = "harmonic"
    MIN_SOFT = "min_soft"
    GEOMETRIC = "geometric"


@dataclass
class SRComponents:
    """Componentes do SR-Ω∞"""

    awareness: float  # Autoconsciência (C_cal)
    ethics: float  # Ética (E_ok) - binário ou contínuo
    autocorrection: float  # Autocorreção (M)
    metacognition: float  # Metacognição (A_eff)

    def clamp(self, min_val: float = 0.0, max_val: float = 1.0) -> "SRComponents":
        """Retorna componentes clampados"""
        return SRComponents(
            awareness=max(min_val, min(max_val, self.awareness)),
            ethics=max(min_val, min(max_val, self.ethics)),
            autocorrection=max(min_val, min(max_val, self.autocorrection)),
            metacognition=max(min_val, min(max_val, self.metacognition)),
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "awareness": self.awareness,
            "ethics": self.ethics,
            "autocorrection": self.autocorrection,
            "metacognition": self.metacognition,
        }

    def to_list(self) -> list[float]:
        return [self.awareness, self.ethics, self.autocorrection, self.metacognition]


# Standalone functions for compatibility with tests
def compute_sr_omega(
    awareness: float,
    ethics_ok: bool,
    autocorrection: float,
    metacognition: float,
    config: "SRConfig" = None,
) -> tuple[float, dict[str, Any]]:
    """Compute SR-Ω∞ score"""
    if config is None:
        config = SRConfig()

    # Convert config to engine parameters
    method_map = {
        "harmonic": SRAggregationMethod.HARMONIC,
        "min_soft": SRAggregationMethod.MIN_SOFT,
        "geometric": SRAggregationMethod.GEOMETRIC,
    }

    method = method_map.get(config.aggregation, SRAggregationMethod.HARMONIC)
    engine = SROmegaEngine(method=method, p_norm=config.p_norm)

    components = SRComponents(
        awareness=awareness,
        ethics=1.0 if ethics_ok else 0.001,  # Very low value for ethics veto
        autocorrection=autocorrection,
        metacognition=metacognition,
    )

    sr_score, details = engine.compute_sr(components)
    return sr_score, details


def harmonic_mean(values: list[float]) -> float:
    """Harmonic mean of values"""
    if not values:
        return 0.0

    # Filter out zeros to avoid division by zero
    filtered = [v for v in values if v > 1e-9]
    if not filtered:
        return 0.0

    return len(filtered) / sum(1.0 / v for v in filtered)


def geometric_mean(values: list[float]) -> float:
    """Geometric mean of values"""
    if not values:
        return 0.0

    # Filter out zeros and negatives
    filtered = [v for v in values if v > 0]
    if not filtered:
        return 0.0

    product = 1.0
    for v in filtered:
        product *= v

    return product ** (1.0 / len(filtered))


def min_soft_pnorm(values: list[float], p: float = -5.0) -> float:
    """Min-soft p-norm approximation"""
    if not values:
        return 0.0

    if p >= 0:
        # Regular p-norm
        return (sum(v**p for v in values) / len(values)) ** (1.0 / p)
    else:
        # Soft minimum via negative p-norm
        # For very negative p, this should approximate the minimum closely
        min_val = min(values)
        if min_val <= 1e-9:
            return 0.0

        # Use a more aggressive approximation for very negative p
        if p <= -10:
            # For very negative p, return something very close to minimum
            return min_val * 1.01

        # For moderate negative p, use the standard formula but with better approximation
        sum_p = sum(v ** abs(p) for v in values)
        if sum_p <= 1e-9:
            return min_val

        result = (sum_p / len(values)) ** (1.0 / abs(p))

        # Ensure result is closer to minimum for negative p
        return min(result, min_val * 1.2)


def compute_awareness_score(
    internal_state: dict[str, float], confidence: float, num_cycles: int
) -> float:
    """Compute awareness score from internal state"""
    # Simple heuristic based on resource usage and confidence
    cpu = internal_state.get("cpu", 0.5)
    mem = internal_state.get("mem", 0.5)
    latency = internal_state.get("latency", 0.1)

    # Lower resource usage and latency = higher awareness
    resource_efficiency = 1.0 - (cpu + mem) / 2.0
    latency_efficiency = max(0.0, 1.0 - latency)

    # Combine with confidence and experience (cycles)
    experience_factor = min(1.0, num_cycles / 10.0)  # Saturate at 10 cycles

    awareness = (
        resource_efficiency + latency_efficiency + confidence + experience_factor
    ) / 4.0
    return max(0.0, min(1.0, awareness))


def compute_autocorrection_score(
    error_history: list[float], improvement_threshold: float = 0.1
) -> float:
    """Compute autocorrection score from error history"""
    if len(error_history) < 2:
        return 0.5  # Neutral score for insufficient data

    # Compute trend in error reduction
    recent_errors = error_history[-5:] if len(error_history) >= 5 else error_history

    if len(recent_errors) < 2:
        return 0.5

    # Linear regression to find trend
    n = len(recent_errors)
    x_mean = (n - 1) / 2
    y_mean = sum(recent_errors) / n

    numerator = sum((i - x_mean) * (recent_errors[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator <= 1e-9:
        return 0.5

    slope = numerator / denominator

    # Negative slope (decreasing errors) is good
    if slope < -improvement_threshold:
        return 1.0  # Excellent autocorrection
    elif slope < 0:
        return 0.7  # Good autocorrection
    elif slope < improvement_threshold:
        return 0.5  # Neutral
    else:
        return 0.2  # Poor autocorrection (errors increasing)


def compute_metacognition_score(
    num_reflections: int, reflection_quality: float, adaptation_rate: float
) -> float:
    """Compute metacognition score"""
    # Normalize number of reflections (more is better, but with diminishing returns)
    reflection_score = min(1.0, num_reflections / 5.0)

    # Quality and adaptation rate are already normalized [0,1]
    quality_score = max(0.0, min(1.0, reflection_quality))
    adaptation_score = max(0.0, min(1.0, adaptation_rate))

    # Weighted combination
    metacognition = (
        0.3 * reflection_score + 0.4 * quality_score + 0.3 * adaptation_score
    )
    return max(0.0, min(1.0, metacognition))


@dataclass
class SRConfig:
    """Configuration for SR-Ω∞ computation"""

    aggregation: str = "harmonic"  # harmonic, min_soft, geometric
    p_norm: float = -5.0  # For min_soft aggregation
    ethics_veto_threshold: float = 0.01  # Below this, ethics vetos everything
    min_component_threshold: float = 0.0  # Minimum allowed component value


class SRTracker:
    """Track SR values over time"""

    def __init__(self, alpha: float = 0.2, max_history: int = 100):
        self.alpha = alpha
        self.max_history = max_history
        self.history = []
        self.ema_value = None

    def update(
        self,
        awareness: float,
        ethics_ok: bool,
        autocorrection: float,
        metacognition: float,
    ) -> tuple[float, float]:
        """Update with new SR values"""
        sr_score, _ = compute_sr_omega(
            awareness, ethics_ok, autocorrection, metacognition
        )

        # Update EMA
        if self.ema_value is None:
            self.ema_value = sr_score
        else:
            self.ema_value = (1.0 - self.alpha) * self.ema_value + self.alpha * sr_score

        # Update history
        self.history.append(sr_score)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        return sr_score, self.ema_value

    def get_trend(self) -> str:
        """Get trend direction"""
        if len(self.history) < 2:
            return "stable"

        recent = self.history[-5:] if len(self.history) >= 5 else self.history
        if len(recent) < 2:
            return "stable"

        # Simple linear trend
        n = len(recent)
        x_mean = (n - 1) / 2
        y_mean = sum(recent) / n

        numerator = sum((i - x_mean) * (recent[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator <= 1e-9:
            return "stable"

        slope = numerator / denominator

        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"


class SROmegaEngine:
    """
    Engine SR-Ω∞ com agregação não-compensatória

    Suporta múltiplos métodos:
    - Harmônica: 1 / Σ(w_i / x_i) - penaliza valores baixos
    - Min-soft: aproximação suave do mínimo via p-norm
    - Geométrica: Π(x_i^w_i) - também não-compensatória
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        method: SRAggregationMethod = SRAggregationMethod.HARMONIC,
        p_norm: float = -10.0,  # Para min-soft (negativo)
        epsilon: float = 1e-9,
    ):
        """
        Args:
            weights: Pesos dos componentes (default: iguais)
            method: Método de agregação
            p_norm: Parâmetro p para min-soft (negativo para aproximar min)
            epsilon: Valor mínimo para estabilidade
        """
        if weights is None:
            weights = {
                "awareness": 0.25,
                "ethics": 0.25,
                "autocorrection": 0.25,
                "metacognition": 0.25,
            }

        # Normalizar pesos
        weight_sum = sum(weights.values())
        if weight_sum > 0:
            self.weights = {k: v / weight_sum for k, v in weights.items()}
        else:
            self.weights = {
                "awareness": 0.25,
                "ethics": 0.25,
                "autocorrection": 0.25,
                "metacognition": 0.25,
            }

        self.method = method
        self.p_norm = p_norm
        self.epsilon = epsilon

    def _harmonic_mean(self, components: SRComponents) -> tuple[float, dict[str, Any]]:
        """Média harmônica ponderada"""
        comp_dict = components.to_dict()

        # Garantir valores positivos
        safe_values = {k: max(self.epsilon, v) for k, v in comp_dict.items()}

        # Média harmônica: 1 / Σ(w_i / x_i)
        denominator = sum(self.weights[k] / safe_values[k] for k in safe_values.keys())

        sr_score = 1.0 / max(self.epsilon, denominator)

        details = {
            "method": "harmonic",
            "safe_values": safe_values,
            "denominator": denominator,
            "weights": self.weights,
        }

        return sr_score, details

    def _min_soft(self, components: SRComponents) -> tuple[float, dict[str, Any]]:
        """Min-soft via p-norm negativo"""
        comp_list = components.to_list()
        weights_list = [
            self.weights[k]
            for k in ["awareness", "ethics", "autocorrection", "metacognition"]
        ]

        # p-norm: (Σ w_i * x_i^p)^(1/p)
        # Para p << 0, aproxima o mínimo ponderado
        if self.p_norm == 0:
            # Caso especial: média geométrica
            log_sum = sum(
                w * math.log(max(self.epsilon, x))
                for w, x in zip(weights_list, comp_list, strict=False)
            )
            sr_score = math.exp(log_sum)
        else:
            # p-norm geral
            powered_sum = sum(
                w * (max(self.epsilon, x) ** self.p_norm)
                for w, x in zip(weights_list, comp_list, strict=False)
            )
            sr_score = powered_sum ** (1.0 / self.p_norm)

        details = {
            "method": "min_soft",
            "p_norm": self.p_norm,
            "powered_sum": powered_sum if self.p_norm != 0 else None,
            "weights": self.weights,
        }

        return max(0.0, min(1.0, sr_score)), details

    def _geometric_mean(self, components: SRComponents) -> tuple[float, dict[str, Any]]:
        """Média geométrica ponderada"""
        comp_dict = components.to_dict()

        # Garantir valores positivos
        safe_values = {k: max(self.epsilon, v) for k, v in comp_dict.items()}

        # Média geométrica: Π(x_i^w_i) = exp(Σ w_i * ln(x_i))
        log_sum = sum(
            self.weights[k] * math.log(safe_values[k]) for k in safe_values.keys()
        )

        sr_score = math.exp(log_sum)

        details = {
            "method": "geometric",
            "safe_values": safe_values,
            "log_sum": log_sum,
            "weights": self.weights,
        }

        return sr_score, details

    def compute_sr(self, components: SRComponents) -> tuple[float, dict[str, Any]]:
        """
        Computa SR-Ω∞ usando método configurado

        Args:
            components: Componentes SR

        Returns:
            (sr_score, details_dict)
        """
        # Clamp componentes
        safe_comp = components.clamp()

        # Escolher método
        if self.method == SRAggregationMethod.HARMONIC:
            sr_score, method_details = self._harmonic_mean(safe_comp)
        elif self.method == SRAggregationMethod.MIN_SOFT:
            sr_score, method_details = self._min_soft(safe_comp)
        elif self.method == SRAggregationMethod.GEOMETRIC:
            sr_score, method_details = self._geometric_mean(safe_comp)
        else:
            raise ValueError(f"Unknown SR method: {self.method}")

        # Clamp final
        sr_score = max(0.0, min(1.0, sr_score))

        # Detalhes completos
        details = {
            "sr_score": sr_score,
            "components_raw": components.to_dict(),
            "components_clamped": safe_comp.to_dict(),
            "aggregation_method": self.method.value,
            **method_details,
        }

        return sr_score, details

    def gate_check(
        self, components: SRComponents, tau: float = 0.8
    ) -> tuple[bool, dict[str, Any]]:
        """
        Verifica se SR passa no gate

        Args:
            components: Componentes SR
            tau: Threshold para passar

        Returns:
            (passed, gate_details)
        """
        sr_score, compute_details = self.compute_sr(components)

        passed = sr_score >= tau

        gate_details = {
            "gate": "SR",
            "value": sr_score,
            "threshold": tau,
            "passed": passed,
            "message": f"SR={sr_score:.3f} {'≥' if passed else '<'} {tau}",
            "compute_details": compute_details,
        }

        return passed, gate_details

    def create_attestation(
        self, components: SRComponents, candidate_id: str, tau: float = 0.8
    ) -> Any:
        """
        Create cryptographic attestation for SR evaluation

        Args:
            components: SR components
            candidate_id: ID of the candidate being evaluated
            tau: Threshold for passing

        Returns:
            Attestation object or None if unavailable
        """
        try:
            from penin.omega.attestation import create_sr_attestation

            sr_score, details = self.compute_sr(components)
            passed = sr_score >= tau
            verdict = "pass" if passed else "fail"

            attestation = create_sr_attestation(
                verdict=verdict,
                candidate_id=candidate_id,
                sr_score=sr_score,
                components=components.to_dict(),
            )

            return attestation
        except ImportError:
            return None

    def analyze_non_compensatory(self, components: SRComponents) -> dict[str, Any]:
        """
        Analisa comportamento não-compensatório

        Testa o que acontece quando um componente é muito baixo
        """
        base_sr, _ = self.compute_sr(components)

        analysis = {"base_sr": base_sr, "component_failures": {}}

        # Testar cada componente com valor muito baixo
        for comp_name in ["awareness", "ethics", "autocorrection", "metacognition"]:
            # Criar componente com falha
            failed_comp = SRComponents(**components.to_dict())
            setattr(failed_comp, comp_name, 0.01)  # Valor muito baixo

            failed_sr, _ = self.compute_sr(failed_comp)

            # Calcular impacto
            impact = base_sr - failed_sr
            impact_ratio = impact / base_sr if base_sr > 0 else 0

            analysis["component_failures"][comp_name] = {
                "failed_sr": failed_sr,
                "impact": impact,
                "impact_ratio": impact_ratio,
                "severe": impact_ratio > 0.5,  # Impacto severo se > 50%
            }

        return analysis

    def update_weights(self, new_weights: dict[str, float]) -> None:
        """Atualiza pesos com normalização"""
        weight_sum = sum(new_weights.values())
        if weight_sum > 0:
            self.weights = {k: v / weight_sum for k, v in new_weights.items()}

    def get_config(self) -> dict[str, Any]:
        """Retorna configuração atual"""
        return {
            "weights": self.weights,
            "method": self.method.value,
            "p_norm": self.p_norm,
            "epsilon": self.epsilon,
        }


class SRWithEthicsGate(SROmegaEngine):
    """
    Extensão do SR com gate ético rígido

    Se ethics_ok=False, SR automaticamente vira 0 (fail-closed)
    """

    def compute_sr_with_ethics_gate(
        self, components: SRComponents, ethics_ok: bool = True
    ) -> tuple[float, dict[str, Any]]:
        """
        Computa SR com gate ético rígido

        Args:
            components: Componentes SR
            ethics_ok: Se ética passou (ex: Σ-Guard)

        Returns:
            (sr_score, details_with_ethics_gate)
        """
        if not ethics_ok:
            # Fail-closed: ética falhou, SR = 0
            details = {
                "sr_score": 0.0,
                "ethics_gate": False,
                "ethics_gate_message": "Ethics gate failed - SR forced to 0",
                "components": components.to_dict(),
                "method": "ethics_gate_override",
            }
            return 0.0, details

        # Ética OK, computar SR normalmente
        sr_score, compute_details = self.compute_sr(components)

        # Adicionar info do gate ético
        compute_details["ethics_gate"] = True
        compute_details["ethics_gate_message"] = "Ethics gate passed"

        return sr_score, compute_details


# Funções de conveniência
def quick_sr_harmonic(
    awareness: float, ethics: float, autocorrection: float, metacognition: float
) -> float:
    """Cálculo rápido de SR via média harmônica"""
    engine = SROmegaEngine(method=SRAggregationMethod.HARMONIC)
    components = SRComponents(awareness, ethics, autocorrection, metacognition)
    sr_score, _ = engine.compute_sr(components)
    return sr_score


def quick_sr_min_soft(
    awareness: float,
    ethics: float,
    autocorrection: float,
    metacognition: float,
    p: float = -10.0,
) -> float:
    """Cálculo rápido de SR via min-soft"""
    engine = SROmegaEngine(method=SRAggregationMethod.MIN_SOFT, p_norm=p)
    components = SRComponents(awareness, ethics, autocorrection, metacognition)
    sr_score, _ = engine.compute_sr(components)
    return sr_score


def quick_sr_gate(
    awareness: float,
    ethics: float,
    autocorrection: float,
    metacognition: float,
    tau: float = 0.8,
) -> tuple[bool, float]:
    """Gate rápido de SR"""
    engine = SROmegaEngine()
    components = SRComponents(awareness, ethics, autocorrection, metacognition)
    passed, gate_details = engine.gate_check(components, tau)
    return passed, gate_details["value"]


def validate_sr_non_compensatory(
    awareness: float, ethics: float, autocorrection: float, metacognition: float
) -> dict[str, Any]:
    """
    Valida comportamento não-compensatório do SR

    Returns:
        Dict com análise de não-compensatoriedade
    """
    engine = SROmegaEngine()
    components = SRComponents(awareness, ethics, autocorrection, metacognition)

    return engine.analyze_non_compensatory(components)


def sr_omega(
    awareness: float, ethics_ok: bool, autocorr: float, metacognition: float
) -> float:
    """Compatibility helper expected by some tests."""
    engine = SROmegaEngine(method=SRAggregationMethod.HARMONIC)
    comps = SRComponents(
        awareness, 1.0 if ethics_ok else 0.001, autocorr, metacognition
    )
    score, _ = engine.compute_sr(comps)
    return score


def compute_sr_omega(
    awareness: float,
    ethics: float,
    autocorrection: float,
    metacognition: float,
    method: str = "harmonic",
    config: "SRConfig" = None,
) -> tuple[float, dict[str, Any]]:
    """
    Compute SR-Ω∞ score (convenience function)

    Args:
        awareness: Awareness component (0-1)
        ethics: Ethics component (0-1)
        autocorrection: Autocorrection component (0-1)
        metacognition: Metacognition component (0-1)
        method: Aggregation method ('harmonic', 'min_soft', 'geometric')

    Returns:
        SR-Ω∞ score (0-1)
    """
    # Handle config parameter
    if config is not None:
        method = config.method

    if method == "harmonic":
        method_enum = SRAggregationMethod.HARMONIC
    elif method == "min_soft":
        method_enum = SRAggregationMethod.MIN_SOFT
    elif method == "geometric":
        method_enum = SRAggregationMethod.GEOMETRIC
    else:
        method_enum = SRAggregationMethod.HARMONIC

    engine = SROmegaEngine(method=method_enum)
    components = SRComponents(awareness, ethics, autocorrection, metacognition)
    sr_score, details = engine.compute_sr(components)

    return sr_score, details


def harmonic_mean(values: list[float]) -> float:
    """Compute harmonic mean of values"""
    if not values:
        return 0.0

    # Avoid division by zero
    safe_values = [max(1e-9, v) for v in values]
    return len(safe_values) / sum(1.0 / v for v in safe_values)


def geometric_mean(values: list[float]) -> float:
    """Compute geometric mean of values"""
    if not values:
        return 0.0

    # Avoid log(0)
    safe_values = [max(1e-9, v) for v in values]

    # Geometric mean: nth root of product
    log_sum = sum(math.log(v) for v in safe_values)
    return math.exp(log_sum / len(safe_values))


def min_soft_pnorm(values: list[float], p: float = -10.0) -> float:
    """Compute min-soft p-norm approximation"""
    if not values:
        return 0.0

    # Avoid division by zero
    safe_values = [max(1e-9, v) for v in values]

    if p == 0:
        # Geometric mean as limit
        log_sum = sum(math.log(v) for v in safe_values)
        return math.exp(log_sum / len(safe_values))
    else:
        # p-norm: (Σ x_i^p)^(1/p)
        powered_sum = sum(v**p for v in safe_values)
        return powered_sum ** (1.0 / p)


def compute_awareness_score(state_dict: dict[str, Any], *args) -> float:
    """Compute awareness score from system state"""
    # Handle different input types
    if isinstance(state_dict, (int, float)):
        # If it's a number, use it directly as the base score
        return max(0.0, min(1.0, float(state_dict)))
    elif isinstance(state_dict, list):
        # If it's a list, use the first element as the base score
        base_score = state_dict[0] if state_dict else 0.5
        return max(0.0, min(1.0, base_score))

    # Extract relevant metrics
    confidence = state_dict.get("confidence", 0.5)
    uncertainty = state_dict.get("uncertainty", 0.5)
    calibration = state_dict.get("calibration", 0.5)

    # Awareness is high when confidence is well-calibrated and uncertainty is acknowledged
    # Formula: confidence * calibration * (1 - uncertainty)
    awareness = confidence * calibration * (1.0 - uncertainty)

    return max(0.0, min(1.0, awareness))


def compute_autocorrection_score(state_dict: dict[str, Any], *args) -> float:
    """Compute autocorrection score from system state"""
    # Handle different input types
    if isinstance(state_dict, (int, float)):
        # If it's a number, use it directly as the base score
        return max(0.0, min(1.0, float(state_dict)))
    elif isinstance(state_dict, list):
        # If it's a list, use the first element as the base score
        base_score = state_dict[0] if state_dict else 0.5
        return max(0.0, min(1.0, base_score))

    # Extract relevant metrics
    error_rate = state_dict.get("error_rate", 0.5)
    correction_attempts = state_dict.get("correction_attempts", 0.5)
    success_rate = state_dict.get("success_rate", 0.5)

    # Autocorrection is high when error rate is low and correction success is high
    # Formula: (1 - error_rate) * correction_attempts * success_rate
    autocorrection = (1.0 - error_rate) * correction_attempts * success_rate

    return max(0.0, min(1.0, autocorrection))


def compute_metacognition_score(state_dict: dict[str, Any], *args) -> float:
    """Compute metacognition score from system state"""
    # Handle different input types
    if isinstance(state_dict, (int, float)):
        # If it's a number, use it directly as the base score
        return max(0.0, min(1.0, float(state_dict)))
    elif isinstance(state_dict, list):
        # If it's a list, use the first element as the base score
        base_score = state_dict[0] if state_dict else 0.5
        return max(0.0, min(1.0, base_score))

    # Extract relevant metrics
    reflection_depth = state_dict.get("reflection_depth", 0.5)
    self_awareness = state_dict.get("self_awareness", 0.5)
    planning_quality = state_dict.get("planning_quality", 0.5)

    # Metacognition is high when all components are strong
    # Formula: geometric mean of components
    components = [reflection_depth, self_awareness, planning_quality]
    metacognition = geometric_mean(components)

    return max(0.0, min(1.0, metacognition))


class SRConfig:
    """SR configuration class"""

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        method: str = "harmonic",
        p_norm: float = -10.0,
        aggregation: str = None,
    ):
        if weights is None:
            weights = {
                "awareness": 0.25,
                "ethics": 0.25,
                "autocorrection": 0.25,
                "metacognition": 0.25,
            }

        self.weights = weights
        self.method = method
        if aggregation is not None:
            self.method = aggregation
        self.p_norm = p_norm

    def to_dict(self) -> dict[str, Any]:
        return {"weights": self.weights, "method": self.method, "p_norm": self.p_norm}

    def update(self, **kwargs):
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class SRTracker:
    """SR tracker for monitoring scores over time"""

    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.sr_history = []
        self.components_history = []

    def add_measurement(self, sr_score: float, components: dict[str, float]):
        """Add an SR measurement"""
        self.sr_history.append(sr_score)
        self.components_history.append(components.copy())

        if len(self.sr_history) > self.window_size:
            self.sr_history = self.sr_history[-self.window_size :]
            self.components_history = self.components_history[-self.window_size :]

    def update(
        self,
        awareness: float,
        ethics: float,
        autocorrection: float,
        metacognition: float,
    ) -> tuple[float, float]:
        """Update tracker with new SR components and return SR score and EMA"""
        sr_score, details = compute_sr_omega(
            awareness, ethics, autocorrection, metacognition
        )
        components = {
            "awareness": awareness,
            "ethics": ethics,
            "autocorrection": autocorrection,
            "metacognition": metacognition,
        }

        self.add_measurement(sr_score, components)

        # Calculate EMA of SR scores
        if len(self.sr_history) > 1:
            alpha = 0.3  # EMA smoothing factor
            ema = self.sr_history[0]
            for score in self.sr_history[1:]:
                ema = alpha * score + (1 - alpha) * ema
        else:
            ema = sr_score

        return sr_score, ema

    def get_stats(self) -> dict[str, Any]:
        """Get SR statistics"""
        if not self.sr_history:
            return {"count": 0, "avg_sr": 0.0, "stability": "unknown"}

        avg_sr = sum(self.sr_history) / len(self.sr_history)
        min_sr = min(self.sr_history)
        max_sr = max(self.sr_history)

        # Stability based on SR variance
        variance = sum((s - avg_sr) ** 2 for s in self.sr_history) / len(
            self.sr_history
        )
        stability = (
            "high" if variance < 0.01 else "medium" if variance < 0.05 else "low"
        )

        return {
            "count": len(self.sr_history),
            "avg_sr": avg_sr,
            "min_sr": min_sr,
            "max_sr": max_sr,
            "variance": variance,
            "stability": stability,
            "latest_sr": self.sr_history[-1] if self.sr_history else 0.0,
        }

    def get_trend(self) -> str:
        """Get trend direction"""
        if len(self.sr_history) < 2:
            return "stable"

        recent = (
            self.sr_history[-3:] if len(self.sr_history) >= 3 else self.sr_history[-2:]
        )
        earlier = self.sr_history[: len(self.sr_history) - len(recent)]

        if not earlier:
            return "stable"

        recent_avg = sum(recent) / len(recent)
        earlier_avg = sum(earlier) / len(earlier)

        if recent_avg > earlier_avg + 0.05:
            return "improving"
        elif recent_avg < earlier_avg - 0.05:
            return "declining"
        else:
            return "stable"


@dataclass
class Recommendation:
    """Represents a recommendation made by SR-Omega"""

    recommendation_id: str
    task: str
    timestamp: float
    expected_sr: float
    metadata: dict[str, Any]


@dataclass
class Outcome:
    """Represents the outcome of a recommendation"""

    recommendation_id: str
    success: bool
    timestamp: float
    actual_sr: float | None
    message: str


class SROmegaService:
    """
    SR-Omega Service - Tracks mental state and provides introspection capabilities

    This service maintains state about:
    - Pending recommendations that haven't been reported back on
    - Recent outcomes (success/failure) of recommendations
    - Current concerns (tasks/metrics with low success rates)
    """

    def __init__(self, max_pending: int = 100, max_outcomes: int = 50):
        """
        Initialize SR-Omega service

        Args:
            max_pending: Maximum number of pending recommendations to track
            max_outcomes: Maximum number of recent outcomes to track
        """
        self.pending_recommendations: list[Recommendation] = []
        self.recent_outcomes: list[Outcome] = []
        self.max_pending = max_pending
        self.max_outcomes = max_outcomes
        self.sr_tracker = SRTracker()
        self.task_success_rates: dict[str, dict[str, Any]] = {}

    def add_recommendation(
        self,
        recommendation_id: str,
        task: str,
        expected_sr: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a new recommendation to pending list

        Args:
            recommendation_id: Unique identifier for the recommendation
            task: Task name or description
            expected_sr: Expected SR score
            metadata: Additional metadata about the recommendation
        """
        rec = Recommendation(
            recommendation_id=recommendation_id,
            task=task,
            timestamp=time.time(),
            expected_sr=expected_sr,
            metadata=metadata or {},
        )
        self.pending_recommendations.append(rec)

        # Limit size
        if len(self.pending_recommendations) > self.max_pending:
            self.pending_recommendations.pop(0)

    def report_outcome(
        self,
        recommendation_id: str,
        success: bool,
        actual_sr: float | None = None,
        message: str = "",
    ) -> None:
        """
        Report the outcome of a recommendation

        Args:
            recommendation_id: ID of the recommendation
            success: Whether the recommendation was successful
            actual_sr: Actual SR score achieved (if available)
            message: Additional message about the outcome
        """
        # Extract task name before removing from pending
        task_name = None
        for rec in self.pending_recommendations:
            if rec.recommendation_id == recommendation_id:
                task_name = rec.task
                break

        # Remove from pending
        self.pending_recommendations = [
            r
            for r in self.pending_recommendations
            if r.recommendation_id != recommendation_id
        ]

        # Add to outcomes
        outcome = Outcome(
            recommendation_id=recommendation_id,
            success=success,
            timestamp=time.time(),
            actual_sr=actual_sr,
            message=message,
        )
        self.recent_outcomes.append(outcome)

        # Limit size
        if len(self.recent_outcomes) > self.max_outcomes:
            self.recent_outcomes.pop(0)

        # Update task success rates
        if task_name:
            self._update_task_success_rate(task_name, success)

    def _update_task_success_rate(self, task: str, success: bool) -> None:
        """Update success rate tracking for a task"""
        if task not in self.task_success_rates:
            self.task_success_rates[task] = {"total": 0, "successes": 0, "rate": 0.0}

        self.task_success_rates[task]["total"] += 1
        if success:
            self.task_success_rates[task]["successes"] += 1

        total = self.task_success_rates[task]["total"]
        successes = self.task_success_rates[task]["successes"]
        self.task_success_rates[task]["rate"] = successes / total if total > 0 else 0.0

    def get_mental_state(self) -> dict[str, Any]:
        """
        Get the current mental state of the SR-Omega service

        Returns:
            Dictionary containing:
            - pending_recommendations: List of pending recommendations
            - recent_outcomes: Log of recent outcomes
            - current_concerns: List of tasks/metrics with low success rates
        """
        # Identify current concerns (tasks with low success rates)
        concerns = []
        for task, stats in self.task_success_rates.items():
            if (
                stats["total"] >= 3 and stats["rate"] < 0.5
            ):  # At least 3 attempts and <50% success
                concerns.append(
                    {
                        "task": task,
                        "success_rate": stats["rate"],
                        "total_attempts": stats["total"],
                        "severity": "high" if stats["rate"] < 0.3 else "medium",
                    }
                )

        # Format pending recommendations
        pending_list = [
            {
                "id": rec.recommendation_id,
                "task": rec.task,
                "expected_sr": rec.expected_sr,
                "age_seconds": time.time() - rec.timestamp,
                "metadata": rec.metadata,
            }
            for rec in self.pending_recommendations
        ]

        # Format recent outcomes
        outcomes_list = [
            {
                "id": out.recommendation_id,
                "success": out.success,
                "actual_sr": out.actual_sr,
                "message": out.message,
                "timestamp": out.timestamp,
            }
            for out in self.recent_outcomes
        ]

        # Get SR tracker stats
        sr_stats = self.sr_tracker.get_stats()

        return {
            "pending_recommendations": pending_list,
            "recent_outcomes": outcomes_list,
            "current_concerns": concerns,
            "sr_statistics": sr_stats,
            "timestamp": time.time(),
        }
