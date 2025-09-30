"""
Imunidade Digital - Detecção de Anomalias
==========================================

Detecção simples de anomalias + fail-closed.
"""

from typing import Dict, Any


def anomaly_score(metrics: Dict[str, Any]) -> float:
    """
    Calcula score de anomalia nas métricas.
    
    Args:
        metrics: Dicionário com métricas do sistema
        
    Returns:
        Score de anomalia (0 = normal, >1 = anômalo)
    """
    score = 0.0
    
    for k, v in metrics.items():
        try:
            val = float(v)
            
            # Valores fora de range razoável
            if not (0.0 <= val <= 1e6):
                score += 1.0
            
            # NaN ou Infinity
            if val != val or abs(val) == float('inf'):
                score += 2.0
            
            # Valores negativos onde não deveriam estar
            if val < 0 and k in ["accuracy", "phi", "sr", "G"]:
                score += 1.0
            
        except (TypeError, ValueError):
            # Valor não numérico onde deveria ser
            if k in ["accuracy", "phi", "sr", "G", "cost"]:
                score += 1.0
    
    return score


def guard(metrics: Dict[str, Any], trigger: float = 1.0) -> bool:
    """
    Gate de imunidade: True = OK, False = anomalia detectada.
    
    Args:
        metrics: Métricas do sistema
        trigger: Limiar para trigger (score >= trigger → bloqueio)
        
    Returns:
        True se sistema está normal (anomaly_score < trigger)
    """
    return anomaly_score(metrics) < trigger


def diagnose(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Diagnóstico detalhado de anomalias.
    
    Args:
        metrics: Métricas do sistema
        
    Returns:
        Dict com diagnóstico
    """
    issues = []
    
    for k, v in metrics.items():
        try:
            val = float(v)
            
            if not (0.0 <= val <= 1e6):
                issues.append(f"{k}={val} fora de range [0, 1e6]")
            
            if val != val:
                issues.append(f"{k} é NaN")
            
            if abs(val) == float('inf'):
                issues.append(f"{k} é Infinity")
            
            if val < 0 and k in ["accuracy", "phi", "sr", "G"]:
                issues.append(f"{k}={val} negativo (esperado >= 0)")
                
        except (TypeError, ValueError):
            issues.append(f"{k}={v} não é numérico")
    
    score = anomaly_score(metrics)
    
    return {
        "anomaly_score": score,
        "issues": issues,
        "healthy": score < 1.0,
        "num_issues": len(issues)
    }