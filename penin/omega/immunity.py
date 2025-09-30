# penin/omega/immunity.py
"""
Imunidade Digital
=================

Detecção de anomalias e ativação de fail-closed.
"""

import math
from typing import Dict, Any, List


def anomaly_score(metrics: Dict[str, Any]) -> float:
    """Calcula score de anomalia"""
    score = 0.0
    
    for key, value in metrics.items():
        try:
            float_val = float(value)
            
            # Detectar valores inválidos
            if math.isnan(float_val) or math.isinf(float_val):
                score += 2.0
            elif float_val < 0 and key in ["phi", "sr", "G", "alpha_eff"]:
                score += 1.5  # Métricas não devem ser negativas
            elif float_val > 1.0 and key in ["phi", "sr", "G"]:
                score += 1.0  # Métricas normalizadas
            elif abs(float_val) > 1e6:
                score += 1.0  # Valores muito grandes
                
        except (ValueError, TypeError):
            score += 1.0  # Valores não numéricos
    
    return score


def guard(metrics: Dict[str, Any], trigger: float = 1.0) -> bool:
    """Guard de imunidade - True = OK, False = ativar fail-closed"""
    return anomaly_score(metrics) < trigger


def immune_response(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Resposta imune completa"""
    score = anomaly_score(metrics)
    triggered = score >= 1.0
    
    return {
        "anomaly_score": score,
        "immune_triggered": triggered,
        "action": "fail_closed" if triggered else "continue",
        "timestamp": __import__("time").time()
    }