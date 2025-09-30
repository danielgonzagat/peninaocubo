"""
CAOS-KRATOS - Exploração Calibrada
===================================

Variante de CAOS⁺ que reforça exploração (O×S) mantendo saturação.
Usado apenas em modo "explore", com Σ-Guard fail-closed.
"""

from .caos import phi_caos


def phi_kratos(
    C: float,
    A: float,
    O: float,
    S: float,
    exploration_factor: float = 2.0,
    kappa: float = 2.0,
    gamma: float = 0.7,
    kappa_max: float = 10.0
) -> float:
    """
    CAOS-KRATOS: reforça impacto de (O×S) para exploração.
    
    Args:
        C, A, O, S: Componentes CAOS
        exploration_factor: Fator de exploração (recomendado: 1.5 a 2.5)
        kappa: Parâmetro de caos
        gamma: Parâmetro de saturação
        kappa_max: Máximo kappa
        
    Returns:
        φ_kratos ∈ [0, 1)
    """
    # Reforça O e S para exploração, mas mantém saturação
    O_exp = min(1.0, O ** (1.0 / max(1.0, exploration_factor)))
    S_exp = min(1.0, S ** (1.0 / max(1.0, exploration_factor)))
    
    return phi_caos(C, A, O_exp, S_exp, kappa, kappa_max, gamma)


def compute_exploration_boost(phi_caos_base: float, phi_kratos: float) -> float:
    """
    Calcula boost de exploração.
    
    Args:
        phi_caos_base: φ do CAOS⁺ normal
        phi_kratos: φ do CAOS-KRATOS
        
    Returns:
        Razão de boost (phi_kratos / phi_caos_base)
    """
    if phi_caos_base <= 1e-9:
        return 1.0
    return phi_kratos / phi_caos_base


def should_explore(
    phi_kratos: float,
    threshold: float = 0.5,
    sigma_guard_ok: bool = True
) -> bool:
    """
    Decide se deve entrar em modo exploração.
    
    Args:
        phi_kratos: Valor do φ_kratos
        threshold: Limiar para exploração
        sigma_guard_ok: Gate Σ-Guard passou
        
    Returns:
        True se deve explorar (com guards OK)
    """
    return phi_kratos >= threshold and sigma_guard_ok