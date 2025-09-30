# penin/omega/darwin_audit.py
"""
Darwiniano-Auditável
====================

Score darwiniano para seleção de variantes com auditoria completa.
"""

from typing import Dict, Any


def darwinian_score(life_ok: bool, caos_phi: float, sr: float, G: float, L_inf: float) -> float:
    """
    Calcula score darwiniano para seleção
    
    Usa comportamento não-compensatório leve: dominância pelo pior componente
    """
    if not life_ok:
        return 0.0
    
    # Não-compensatório: dominância pelo mínimo
    base_score = min(caos_phi, sr, G)
    
    # Modulado por L∞
    return base_score * L_inf


def selection_audit(candidates: list, scores: list) -> Dict[str, Any]:
    """
    Auditoria completa do processo de seleção
    
    Args:
        candidates: Lista de candidatos
        scores: Lista de scores correspondentes
        
    Returns:
        Relatório de auditoria
    """
    if not candidates or not scores or len(candidates) != len(scores):
        return {"error": "Invalid input", "selected": None}
    
    # Encontrar melhor candidato
    best_idx = max(range(len(scores)), key=lambda i: scores[i])
    selected = candidates[best_idx]
    best_score = scores[best_idx]
    
    # Estatísticas
    avg_score = sum(scores) / len(scores)
    score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
    
    return {
        "selected": selected,
        "selected_score": best_score,
        "total_candidates": len(candidates),
        "avg_score": avg_score,
        "score_variance": score_variance,
        "selection_advantage": best_score - avg_score,
        "audit_timestamp": __import__("time").time()
    }