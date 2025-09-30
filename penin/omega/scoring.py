"""
Scoring Module - L∞ Harmônica + Score U/S/C/L
==============================================

Implementa:
- Normalização de séries e EMA (Exponentially Weighted Moving Average)
- L∞ via média harmônica não-compensatória com penalização por custo
- Score U/S/C/L com gate de decisão ('pass'|'canary'|'fail')
- Estabilidade numérica com clamps e epsilon
"""

import math
from typing import List, Dict, Any, Optional
from typing_extensions import Tuple
from enum import Enum


class ScoreVerdict(Enum):
    """Veredito do Score Gate"""
    PASS = "pass"
    CANARY = "canary" 
    FAIL = "fail"


def normalize_series(values: List[float], 
                    method: str = "minmax",
                    target_range: Tuple[float, float] = (0.0, 1.0),
                    epsilon: float = 1e-9) -> List[float]:
    """
    Normaliza série de valores
    
    Args:
        values: Lista de valores para normalizar
        method: 'minmax', 'sigmoid', 'zscore'
        target_range: Range alvo (min, max)
        epsilon: Valor mínimo para evitar divisão por zero
        
    Returns:
        Lista de valores normalizados
    """
    if not values:
        return []
        
    if method == "minmax":
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val
        
        if range_val < epsilon:
            # Todos os valores são iguais
            return [target_range[0]] * len(values)
            
        normalized = [(v - min_val) / range_val for v in values]
        
    elif method == "sigmoid":
        # Sigmoid normalization: 1 / (1 + exp(-x))
        normalized = [1.0 / (1.0 + math.exp(-v)) for v in values]
        
    elif method == "zscore":
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_val = math.sqrt(variance + epsilon)
        
        # Z-score then sigmoid to [0,1]
        z_scores = [(v - mean_val) / std_val for v in values]
        normalized = [1.0 / (1.0 + math.exp(-z)) for z in z_scores]
        
    else:
        raise ValueError(f"Unknown normalization method: {method}")
        
    # Scale to target range
    if target_range != (0.0, 1.0):
        target_min, target_max = target_range
        target_span = target_max - target_min
        normalized = [target_min + v * target_span for v in normalized]
        
    return normalized


def ema_update(current_ema: Optional[float], 
               new_value: float, 
               alpha: float = 0.2) -> float:
    """
    Atualiza EMA (Exponentially Weighted Moving Average)
    
    Args:
        current_ema: Valor atual do EMA (None para primeiro valor)
        new_value: Novo valor a incorporar
        alpha: Fator de suavização [0,1] (maior = mais peso no novo valor)
        
    Returns:
        Novo valor do EMA
    """
    if current_ema is None:
        return new_value
        
    return alpha * new_value + (1 - alpha) * current_ema


class EMATracker:
    """Tracker de EMA com histórico"""
    
    def __init__(self, alpha: float = 0.2):
        self.alpha = alpha
        self.value: Optional[float] = None
        self.count = 0
        
    def update(self, new_value: float) -> float:
        """Atualiza e retorna novo EMA"""
        self.value = ema_update(self.value, new_value, self.alpha)
        self.count += 1
        return self.value
        
    def get_value(self) -> float:
        """Retorna valor atual (0 se não inicializado)"""
        return self.value if self.value is not None else 0.0


def harmonic_mean(values: List[float], 
                  weights: Optional[List[float]] = None,
                  epsilon: float = 1e-9) -> float:
    """
    Calcula média harmônica (não-compensatória)
    
    Args:
        values: Lista de valores > 0
        weights: Pesos opcionais (devem somar 1.0)
        epsilon: Valor mínimo para evitar divisão por zero
        
    Returns:
        Média harmônica
    """
    if not values:
        return 0.0
        
    # Garantir valores positivos
    safe_values = [max(epsilon, v) for v in values]
    
    if weights is None:
        weights = [1.0 / len(safe_values)] * len(safe_values)
    elif len(weights) != len(safe_values):
        raise ValueError("Weights and values must have same length")
        
    # Verificar se pesos somam ~1.0
    weight_sum = sum(weights)
    if abs(weight_sum - 1.0) > 1e-6:
        # Normalizar pesos
        weights = [w / weight_sum for w in weights]
        
    # Média harmônica ponderada: 1 / Σ(w_i / x_i)
    denominator = sum(w / v for w, v in zip(weights, safe_values))
    
    return 1.0 / max(epsilon, denominator)


def linf_harmonic(weights: List[float], 
                  metrics: List[float],
                  cost: float,
                  lambda_c: float = 0.1,
                  ethical_ok: bool = True,
                  epsilon: float = 1e-9) -> float:
    """
    Calcula L∞ via média harmônica com penalização por custo
    
    Args:
        weights: Pesos das métricas (devem somar 1.0)
        metrics: Valores das métricas [0,1]
        cost: Custo normalizado [0,1] (0=barato, 1=caro)
        lambda_c: Fator de penalização por custo
        ethical_ok: Se gates éticos passaram
        epsilon: Valor mínimo
        
    Returns:
        Score L∞
    """
    if len(weights) != len(metrics):
        raise ValueError("Weights and metrics must have same length")
        
    # Média harmônica das métricas
    base_score = harmonic_mean(metrics, weights, epsilon)
    
    # Penalização exponencial por custo
    cost_penalty = math.exp(-lambda_c * cost)
    
    # Gate ético (multiplicativo, não-compensatório)
    ethical_gate = 1.0 if ethical_ok else 0.0
    
    # Score final
    linf_score = base_score * cost_penalty * ethical_gate
    
    return max(0.0, min(1.0, linf_score))  # Clamp [0,1]


def score_gate(U: float, S: float, C: float, L: float,
               wU: float, wS: float, wC: float, wL: float,
               tau: float = 0.7,
               canary_margin: float = 0.1) -> Tuple[ScoreVerdict, float]:
    """
    Calcula Score U/S/C/L e retorna veredito
    
    Args:
        U: Utilidade [0,1]
        S: Estabilidade [0,1] 
        C: Custo [0,1] (0=barato, 1=caro)
        L: Aprendizado futuro [0,1]
        wU, wS, wC, wL: Pesos (devem somar 1.0)
        tau: Threshold para PASS
        canary_margin: Margem para CANARY vs FAIL
        
    Returns:
        (verdict, score)
    """
    # Verificar pesos
    weight_sum = wU + wS + wC + wL
    if abs(weight_sum - 1.0) > 1e-6:
        # Normalizar
        wU, wS, wC, wL = wU/weight_sum, wS/weight_sum, wC/weight_sum, wL/weight_sum
        
    # Score: U/S/L são positivos, C é negativo (custo é ruim)
    score = wU * U + wS * S - wC * C + wL * L
    
    # Clamp score [0,1] (pode ser negativo se C muito alto)
    score = max(0.0, min(1.0, score))
    
    # Decisão
    if score >= tau:
        verdict = ScoreVerdict.PASS
    elif score >= (tau - canary_margin):
        verdict = ScoreVerdict.CANARY
    else:
        verdict = ScoreVerdict.FAIL
        
    return verdict, score


class USCLScorer:
    """Scorer U/S/C/L com EMA e normalização"""
    
    def __init__(self, 
                 weights: Optional[Dict[str, float]] = None,
                 tau: float = 0.7,
                 canary_margin: float = 0.1,
                 ema_alpha: float = 0.2):
        """
        Args:
            weights: Dict com wU, wS, wC, wL (default: iguais)
            tau: Threshold para PASS
            canary_margin: Margem para CANARY
            ema_alpha: Fator EMA
        """
        if weights is None:
            weights = {"wU": 0.25, "wS": 0.25, "wC": 0.25, "wL": 0.25}
            
        self.weights = weights
        self.tau = tau
        self.canary_margin = canary_margin
        
        # EMA trackers
        self.ema_U = EMATracker(ema_alpha)
        self.ema_S = EMATracker(ema_alpha)
        self.ema_C = EMATracker(ema_alpha)
        self.ema_L = EMATracker(ema_alpha)
        
    def update_and_score(self, U: float, S: float, C: float, L: float) -> Dict[str, Any]:
        """
        Atualiza EMAs e calcula score
        
        Returns:
            Dict com score, verdict, EMAs, etc.
        """
        # Atualizar EMAs
        ema_U = self.ema_U.update(U)
        ema_S = self.ema_S.update(S)
        ema_C = self.ema_C.update(C)
        ema_L = self.ema_L.update(L)
        
        # Calcular score com valores EMA
        verdict, score = score_gate(
            ema_U, ema_S, ema_C, ema_L,
            self.weights["wU"], self.weights["wS"], 
            self.weights["wC"], self.weights["wL"],
            self.tau, self.canary_margin
        )
        
        return {
            "score": score,
            "verdict": verdict.value,
            "raw_values": {"U": U, "S": S, "C": C, "L": L},
            "ema_values": {"U": ema_U, "S": ema_S, "C": ema_C, "L": ema_L},
            "weights": self.weights,
            "tau": self.tau,
            "passed": verdict == ScoreVerdict.PASS,
            "canary": verdict == ScoreVerdict.CANARY
        }


class LInfinityScorer:
    """Scorer L∞ com múltiplas métricas e penalização por custo"""
    
    def __init__(self,
                 metric_weights: Optional[Dict[str, float]] = None,
                 lambda_c: float = 0.1,
                 ema_alpha: float = 0.2):
        """
        Args:
            metric_weights: Pesos das métricas (default: iguais)
            lambda_c: Fator de penalização por custo
            ema_alpha: Fator EMA
        """
        if metric_weights is None:
            metric_weights = {
                "rsi": 0.2,
                "synergy": 0.2, 
                "novelty": 0.2,
                "stability": 0.2,
                "viability": 0.15,
                "cost": 0.05
            }
            
        self.weights = metric_weights
        self.lambda_c = lambda_c
        
        # EMA trackers para cada métrica
        self.ema_trackers = {
            name: EMATracker(ema_alpha) 
            for name in metric_weights.keys()
        }
        
    def update_and_score(self, metrics: Dict[str, float], 
                        ethical_ok: bool = True) -> Dict[str, Any]:
        """
        Atualiza EMAs e calcula L∞
        
        Args:
            metrics: Dict com valores das métricas
            ethical_ok: Se gates éticos passaram
            
        Returns:
            Dict com L∞, EMAs, etc.
        """
        # Atualizar EMAs
        ema_values = {}
        for name, tracker in self.ema_trackers.items():
            if name in metrics:
                ema_values[name] = tracker.update(metrics[name])
            else:
                ema_values[name] = tracker.get_value()
                
        # Preparar para L∞ (excluir custo das métricas principais)
        metric_names = [name for name in self.weights.keys() if name != "cost"]
        metric_values = [ema_values[name] for name in metric_names]
        metric_weights = [self.weights[name] for name in metric_names]
        
        # Normalizar pesos (excluindo custo)
        weight_sum = sum(metric_weights)
        if weight_sum > 0:
            metric_weights = [w / weight_sum for w in metric_weights]
        else:
            metric_weights = [1.0 / len(metric_weights)] * len(metric_weights)
            
        # Custo separado
        cost = ema_values.get("cost", 0.0)
        
        # Calcular L∞
        linf_score = linf_harmonic(
            metric_weights, metric_values, cost, 
            self.lambda_c, ethical_ok
        )
        
        return {
            "linf": linf_score,
            "raw_metrics": metrics,
            "ema_metrics": ema_values,
            "weights": self.weights,
            "lambda_c": self.lambda_c,
            "ethical_ok": ethical_ok,
            "cost_penalty": math.exp(-self.lambda_c * cost)
        }


# Funções de conveniência
def quick_normalize(values: List[float]) -> List[float]:
    """Normalização rápida min-max para [0,1]"""
    return normalize_series(values, method="minmax")


def quick_harmonic(values: List[float]) -> float:
    """Média harmônica rápida (pesos iguais)"""
    return harmonic_mean(values)


def quick_score_gate(U: float, S: float, C: float, L: float, 
                    tau: float = 0.7) -> Tuple[str, float]:
    """Score gate rápido com pesos iguais"""
    verdict, score = score_gate(U, S, C, L, 0.25, 0.25, 0.25, 0.25, tau)
    return verdict.value, score