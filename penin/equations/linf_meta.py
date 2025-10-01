"""
Equação 2: Meta-Função L∞ — Avaliação Global Não-Compensatória
===============================================================

Forma: L_∞ = (1 / Σ_j w_j / max(ε, m_j)) · e^(-λ_c · Cost) · 1_{ΣEA ∧ IR→IC}

Avalia performance de forma não-compensatória (média harmônica ponderada)
penalizada por custo e gates ético-seguros.

Propriedades:
------------
- Média harmônica força bottleneck (pior dimensão domina)
- Anti-Goodhart: não pode compensar uma métrica ruim com outra boa
- Penalização exponencial de custo
- Fail-closed: ΣEA ou IR→IC falham → L∞ = 0

Componentes:
-----------
- m_j: métricas normalizadas [0,1] (acurácia, robustez, privacidade, etc.)
- w_j: pesos por métrica (Σ w_j = 1)
- ε: estabilizador para evitar divisão por zero (10⁻³ a 10⁻²)
- Cost: custo normalizado (tempo, tokens, energia)
- λ_c: coeficiente de penalização de custo (meta-otimizado)
- ΣEA: gate ético (Índice Agápe)
- IR→IC: gate de contratividade de risco

Calibração:
----------
- λ_c: começar em 0.1-1.0; ajustar por grid search ou AdaGrad (Eq. 10)
- ε: 10⁻³ para estabilidade numérica
- w_j: iguais inicialmente (1/n); refinar por importância do domínio
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class MetricType(Enum):
    """Tipos de métricas suportadas"""

    ACCURACY = "accuracy"  # Acurácia (higher is better)
    ROBUSTNESS = "robustness"  # Robustez adversarial
    CALIBRATION = "calibration"  # Calibração (ECE inverso)
    PRIVACY = "privacy"  # Privacidade (1 - vazamento)
    FAIRNESS = "fairness"  # Justiça (1 - bias ratio)
    CONSISTENCY = "consistency"  # Consistência (pass@k)
    EFFICIENCY = "efficiency"  # Eficiência (1 / custo normalizado)
    SAFETY = "safety"  # Segurança (violation rate invertido)
    INTERPRETABILITY = "interpretability"  # Interpretabilidade
    COVERAGE = "coverage"  # Cobertura de casos


@dataclass
class Metric:
    """
    Métrica individual m_j
    
    Deve ser normalizada em [0, 1] onde 1 = melhor
    """

    name: str
    value: float  # Normalizado [0, 1]
    weight: float = 1.0  # Peso w_j
    metric_type: MetricType = MetricType.ACCURACY
    raw_value: Optional[float] = None  # Valor bruto antes de normalização
    normalization: str = "min_max"  # min_max, sigmoid, clip

    def normalize(self, raw_val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Normaliza valor bruto para [0, 1]"""
        if self.normalization == "min_max":
            if max_val == min_val:
                return 0.5
            return max(0.0, min(1.0, (raw_val - min_val) / (max_val - min_val)))
        
        elif self.normalization == "sigmoid":
            # Sigmoid centrado em 0.5
            return 1.0 / (1.0 + math.exp(-10 * (raw_val - 0.5)))
        
        elif self.normalization == "clip":
            return max(0.0, min(1.0, raw_val))
        
        else:
            return max(0.0, min(1.0, raw_val))

    def is_valid(self) -> bool:
        """Verifica se métrica está no range válido"""
        return 0.0 <= self.value <= 1.0


@dataclass
class CostComponents:
    """
    Componentes de custo
    
    Todos normalizados para [0, ∞)
    """

    time_seconds: float = 0.0  # Tempo de execução
    tokens_used: int = 0  # Tokens LLM
    energy_kwh: float = 0.0  # Energia consumida
    memory_gb: float = 0.0  # Memória peak
    api_calls: int = 0  # Chamadas API
    
    # Normalização (custo / budget)
    time_budget: float = 10.0
    token_budget: int = 100000
    energy_budget: float = 1.0
    memory_budget: float = 16.0
    api_budget: int = 1000

    def total_normalized_cost(self) -> float:
        """
        Custo total normalizado
        
        Soma ponderada de todos os custos normalizados
        """
        cost_time = self.time_seconds / self.time_budget
        cost_tokens = self.tokens_used / self.token_budget
        cost_energy = self.energy_kwh / self.energy_budget
        cost_memory = self.memory_gb / self.memory_budget
        cost_api = self.api_calls / self.api_budget
        
        # Média ponderada (pode ajustar pesos)
        weights = [0.3, 0.3, 0.2, 0.1, 0.1]
        costs = [cost_time, cost_tokens, cost_energy, cost_memory, cost_api]
        
        return sum(w * c for w, c in zip(weights, costs))


@dataclass
class LInfConfig:
    """Configuração da meta-função L∞"""

    # Estabilizador numérico
    epsilon: float = 1e-3
    
    # Coeficiente de penalização de custo
    lambda_cost: float = 0.5
    
    # Método de agregação (harmonic padrão)
    aggregation: str = "harmonic"  # harmonic, geometric, min_soft
    
    # Normalização de pesos (auto-normalizar para soma = 1)
    auto_normalize_weights: bool = True
    
    # Fail-closed em gates
    fail_closed: bool = True
    
    # Threshold mínimo para cada métrica (opcional)
    min_metric_threshold: float = 0.0


@dataclass
class EthicalGates:
    """
    Gates éticos (ΣEA ∧ IR→IC)
    
    Se qualquer gate falhar e fail_closed=True, L∞ = 0
    """

    # ΣEA/LO-14: Índice Agápe
    agape_index: float = 1.0
    agape_threshold: float = 0.7
    
    # IR→IC: Contratividade de risco (ρ < 1)
    rho_contractivity: float = 0.95
    
    # ECE: Expected Calibration Error
    ece: float = 0.005
    ece_threshold: float = 0.01
    
    # Bias ratio
    rho_bias: float = 1.02
    rho_bias_threshold: float = 1.05
    
    # Consent
    consent: bool = True
    
    # Ecological OK
    eco_ok: bool = True

    def all_gates_pass(self) -> bool:
        """Verifica se todos os gates passaram"""
        return (
            self.agape_index >= self.agape_threshold
            and self.rho_contractivity < 1.0
            and self.ece <= self.ece_threshold
            and self.rho_bias <= self.rho_bias_threshold
            and self.consent
            and self.eco_ok
        )

    def failed_gates(self) -> List[str]:
        """Retorna lista de gates que falharam"""
        failed = []
        
        if self.agape_index < self.agape_threshold:
            failed.append(f"agape_index={self.agape_index:.3f} < {self.agape_threshold}")
        
        if self.rho_contractivity >= 1.0:
            failed.append(f"rho_contractivity={self.rho_contractivity:.3f} >= 1.0")
        
        if self.ece > self.ece_threshold:
            failed.append(f"ece={self.ece:.4f} > {self.ece_threshold}")
        
        if self.rho_bias > self.rho_bias_threshold:
            failed.append(f"rho_bias={self.rho_bias:.3f} > {self.rho_bias_threshold}")
        
        if not self.consent:
            failed.append("consent=False")
        
        if not self.eco_ok:
            failed.append("eco_ok=False")
        
        return failed


def harmonic_mean_weighted(
    metrics: List[Metric],
    epsilon: float = 1e-3,
) -> float:
    """
    Média harmônica ponderada
    
    Formula: H = (Σ w_j) / (Σ w_j / max(ε, m_j))
    
    Propriedade não-compensatória: se qualquer m_j → 0, então H → 0
    """
    if not metrics:
        return 0.0
    
    total_weight = sum(m.weight for m in metrics)
    if total_weight <= 0:
        return 0.0
    
    # Soma ponderada de 1/m_j
    denominator = sum(
        m.weight / max(epsilon, m.value) for m in metrics
    )
    
    if denominator <= epsilon:
        return 0.0
    
    return total_weight / denominator


def geometric_mean_weighted(
    metrics: List[Metric],
    epsilon: float = 1e-3,
) -> float:
    """
    Média geométrica ponderada
    
    Formula: G = exp(Σ w_j · ln(max(ε, m_j)) / Σ w_j)
    
    Também não-compensatória (multiplicativa)
    """
    if not metrics:
        return 0.0
    
    total_weight = sum(m.weight for m in metrics)
    if total_weight <= 0:
        return 0.0
    
    log_sum = sum(
        m.weight * math.log(max(epsilon, m.value)) for m in metrics
    )
    
    return math.exp(log_sum / total_weight)


def min_soft_pnorm(
    metrics: List[Metric],
    p: float = -10.0,
    epsilon: float = 1e-3,
) -> float:
    """
    Aproximação soft do mínimo via p-norm negativo
    
    Formula: (Σ w_j · m_j^p)^(1/p)
    
    Para p << 0, aproxima min(m_j)
    """
    if not metrics:
        return 0.0
    
    total_weight = sum(m.weight for m in metrics)
    if total_weight <= 0:
        return 0.0
    
    # Para p muito negativo, usa aproximação soft min
    if p <= -50:
        # Retorna valor muito próximo do mínimo
        min_val = min(m.value for m in metrics)
        return max(epsilon, min_val)
    
    # p-norm
    powered_sum = sum(
        m.weight * (max(epsilon, m.value) ** p) for m in metrics
    )
    
    if powered_sum <= 0:
        return epsilon
    
    result = (powered_sum / total_weight) ** (1.0 / p)
    return max(0.0, min(1.0, result))


def compute_linf_meta(
    metrics: List[Metric],
    cost: CostComponents,
    ethical_gates: EthicalGates,
    config: Optional[LInfConfig] = None,
) -> Tuple[float, Dict[str, Any]]:
    """
    Calcula L∞ = (média_não_compensatória) · e^(-λ_c · Cost) · 1_{ΣEA ∧ IR→IC}
    
    Args:
        metrics: Lista de métricas normalizadas m_j com pesos w_j
        cost: Componentes de custo
        ethical_gates: Gates éticos (ΣEA, IR→IC)
        config: Configuração da L∞
    
    Returns:
        (linf_score, details_dict)
        - linf_score: Valor L∞ em [0, 1]
        - details_dict: Detalhes da computação
    """
    if config is None:
        config = LInfConfig()
    
    details: Dict[str, Any] = {
        "config": {
            "epsilon": config.epsilon,
            "lambda_cost": config.lambda_cost,
            "aggregation": config.aggregation,
        },
        "metrics_count": len(metrics),
        "ethical_gates_pass": ethical_gates.all_gates_pass(),
    }
    
    # 1. Validar métricas
    valid_metrics = [m for m in metrics if m.is_valid()]
    if not valid_metrics:
        details["error"] = "no_valid_metrics"
        return 0.0, details
    
    details["valid_metrics_count"] = len(valid_metrics)
    
    # 2. Auto-normalizar pesos se configurado
    if config.auto_normalize_weights:
        total_weight = sum(m.weight for m in valid_metrics)
        if total_weight > 0:
            for m in valid_metrics:
                m.weight = m.weight / total_weight
    
    # 3. Verificar thresholds mínimos (opcional)
    if config.min_metric_threshold > 0:
        below_threshold = [
            m.name for m in valid_metrics if m.value < config.min_metric_threshold
        ]
        if below_threshold and config.fail_closed:
            details["error"] = "metrics_below_threshold"
            details["below_threshold"] = below_threshold
            return 0.0, details
    
    # 4. Calcular agregação não-compensatória
    if config.aggregation == "harmonic":
        base_score = harmonic_mean_weighted(valid_metrics, config.epsilon)
        details["aggregation_method"] = "harmonic_mean"
    
    elif config.aggregation == "geometric":
        base_score = geometric_mean_weighted(valid_metrics, config.epsilon)
        details["aggregation_method"] = "geometric_mean"
    
    elif config.aggregation == "min_soft":
        base_score = min_soft_pnorm(valid_metrics, p=-10.0, epsilon=config.epsilon)
        details["aggregation_method"] = "min_soft_pnorm"
    
    else:
        # Default: harmonic
        base_score = harmonic_mean_weighted(valid_metrics, config.epsilon)
        details["aggregation_method"] = "harmonic_mean_default"
    
    details["base_score"] = base_score
    
    # 5. Calcular custo normalizado
    total_cost = cost.total_normalized_cost()
    details["total_cost_normalized"] = total_cost
    
    # 6. Aplicar penalização de custo: e^(-λ_c · Cost)
    cost_penalty = math.exp(-config.lambda_cost * max(0.0, total_cost))
    details["cost_penalty"] = cost_penalty
    
    # 7. Aplicar base_score * cost_penalty
    linf_before_gates = base_score * cost_penalty
    details["linf_before_gates"] = linf_before_gates
    
    # 8. Verificar gates éticos: ΣEA ∧ IR→IC
    gates_pass = ethical_gates.all_gates_pass()
    details["ethical_gates_pass"] = gates_pass
    
    if not gates_pass:
        failed = ethical_gates.failed_gates()
        details["failed_gates"] = failed
        
        if config.fail_closed:
            # Fail-closed: L∞ = 0
            details["linf_final"] = 0.0
            details["action"] = "rejected_ethical_gates"
            return 0.0, details
        else:
            # Soft penalty: multiplicar por 0.1
            linf_final = linf_before_gates * 0.1
            details["linf_final"] = linf_final
            details["action"] = "penalized_ethical_gates"
            return linf_final, details
    
    # 9. L∞ final
    linf_final = max(0.0, min(1.0, linf_before_gates))
    details["linf_final"] = linf_final
    details["action"] = "accepted"
    
    # 10. Adicionar breakdown de métricas
    details["metrics_breakdown"] = [
        {
            "name": m.name,
            "value": m.value,
            "weight": m.weight,
            "type": m.metric_type.value,
            "raw_value": m.raw_value,
        }
        for m in valid_metrics
    ]
    
    return linf_final, details


def compute_delta_linf(
    linf_current: float,
    linf_previous: float,
    beta_min: float = 0.01,
) -> Tuple[float, bool]:
    """
    Calcula ΔL∞ e verifica se atende crescimento mínimo
    
    Args:
        linf_current: L∞ atual
        linf_previous: L∞ anterior
        beta_min: Crescimento mínimo exigido (default 1%)
    
    Returns:
        (delta_linf, meets_threshold)
    """
    delta_linf = linf_current - linf_previous
    meets_threshold = delta_linf >= beta_min
    
    return delta_linf, meets_threshold


def linf_sensitivity_analysis(
    metrics: List[Metric],
    cost: CostComponents,
    ethical_gates: EthicalGates,
    config: Optional[LInfConfig] = None,
) -> Dict[str, Any]:
    """
    Análise de sensibilidade da L∞
    
    Testa o impacto de variações em cada métrica
    """
    if config is None:
        config = LInfConfig()
    
    # L∞ base
    linf_base, _ = compute_linf_meta(metrics, cost, ethical_gates, config)
    
    sensitivity: Dict[str, Any] = {
        "linf_base": linf_base,
        "metric_sensitivities": [],
    }
    
    # Testar cada métrica
    for i, metric in enumerate(metrics):
        original_value = metric.value
        
        # Teste: reduzir métrica em 10%
        metric.value = max(0.0, original_value * 0.9)
        linf_down, _ = compute_linf_meta(metrics, cost, ethical_gates, config)
        
        # Teste: aumentar métrica em 10%
        metric.value = min(1.0, original_value * 1.1)
        linf_up, _ = compute_linf_meta(metrics, cost, ethical_gates, config)
        
        # Restaurar valor original
        metric.value = original_value
        
        # Calcular elasticidade
        delta_down = linf_base - linf_down
        delta_up = linf_up - linf_base
        avg_delta = (delta_down + delta_up) / 2.0
        
        elasticity = (avg_delta / linf_base) / 0.1 if linf_base > 0 else 0.0
        
        sensitivity["metric_sensitivities"].append({
            "metric_name": metric.name,
            "elasticity": elasticity,
            "linf_down": linf_down,
            "linf_up": linf_up,
            "impact": "high" if abs(elasticity) > 0.5 else "medium" if abs(elasticity) > 0.2 else "low",
        })
    
    return sensitivity


# Exemplo de uso
def example_linf_computation():
    """Exemplo de computação de L∞"""
    
    # Métricas exemplo
    metrics = [
        Metric("accuracy", 0.85, weight=0.4, metric_type=MetricType.ACCURACY),
        Metric("robustness", 0.78, weight=0.3, metric_type=MetricType.ROBUSTNESS),
        Metric("privacy", 0.92, weight=0.2, metric_type=MetricType.PRIVACY),
        Metric("fairness", 0.88, weight=0.1, metric_type=MetricType.FAIRNESS),
    ]
    
    # Custo
    cost = CostComponents(
        time_seconds=5.0,
        tokens_used=10000,
        energy_kwh=0.1,
        memory_gb=4.0,
        api_calls=50,
    )
    
    # Gates éticos
    gates = EthicalGates(
        agape_index=0.85,
        rho_contractivity=0.95,
        ece=0.008,
        rho_bias=1.03,
        consent=True,
        eco_ok=True,
    )
    
    # Configuração
    config = LInfConfig(
        epsilon=1e-3,
        lambda_cost=0.5,
        aggregation="harmonic",
        fail_closed=True,
    )
    
    # Computar L∞
    linf, details = compute_linf_meta(metrics, cost, gates, config)
    
    print(f"L∞ = {linf:.4f}")
    print(f"Base score: {details['base_score']:.4f}")
    print(f"Cost penalty: {details['cost_penalty']:.4f}")
    print(f"Ethical gates: {details['ethical_gates_pass']}")
    
    return linf, details


if __name__ == "__main__":
    example_linf_computation()
