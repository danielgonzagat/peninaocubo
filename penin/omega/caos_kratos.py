"""
CAOS-KRATOS - Exploração Calibrada
==================================

Extensão do CAOS⁺ para exploração mais agressiva mantendo estabilidade.
Reforça impacto de (O×S) de forma saturada e controlada.

Fórmula: φ_kratos = φ_caos(C, A, O^exploration_factor, S^exploration_factor)
"""

from .caos import phi_caos


def phi_kratos(C: float, A: float, O: float, S: float, 
               exploration_factor: float = 2.0, **kwargs) -> float:
    """
    CAOS-KRATOS: reforça impacto de (O×S) mantendo saturação
    
    Args:
        C, A, O, S: Componentes CAOS
        exploration_factor: Fator de exploração (default: 2.0)
        **kwargs: Argumentos adicionais para phi_caos
        
    Returns:
        Valor φ_kratos
    """
    # Reforçar O e S com saturação
    O_enhanced = min(1.0, O ** (1.0 / max(1.0, exploration_factor)))
    S_enhanced = min(1.0, S ** (1.0 / max(1.0, exploration_factor)))
    
    return phi_caos(C, A, O_enhanced, S_enhanced, **kwargs)


def adaptive_kratos(C: float, A: float, O: float, S: float,
                   current_performance: float, target_performance: float = 0.8) -> float:
    """
    CAOS-KRATOS adaptativo baseado na performance atual
    
    Args:
        C, A, O, S: Componentes CAOS
        current_performance: Performance atual [0,1]
        target_performance: Performance alvo [0,1]
        
    Returns:
        Valor φ_kratos adaptativo
    """
    # Calcular fator de exploração baseado na performance
    if current_performance < target_performance:
        # Performance baixa -> mais exploração
        exploration_factor = 2.0 + (target_performance - current_performance) * 3.0
    else:
        # Performance boa -> menos exploração
        exploration_factor = 1.0 + max(0.0, (target_performance - current_performance))
    
    return phi_kratos(C, A, O, S, exploration_factor)