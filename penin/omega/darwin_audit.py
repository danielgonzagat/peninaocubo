"""
Darwiniano-Auditável
====================

Score darwiniano para seleção de variantes com auditoria.
"""


def darwinian_score(life_ok: bool, caos_phi: float, sr: float, G: float, L_inf: float) -> float:
    """
    Score darwiniano para seleção.
    
    Não-compensatório leve: dominância pelo pior componente.
    
    Args:
        life_ok: Equação de Vida passou
        caos_phi: φ do CAOS⁺
        sr: Score SR-Ω∞
        G: Coerência global
        L_inf: Score L∞
        
    Returns:
        Score darwiniano [0, 1]
    """
    if not life_ok:
        return 0.0
    
    # Não-compensatório: dominância do pior componente
    bottleneck = min(caos_phi, sr, G)
    
    # Modular por L_inf (qualidade geral)
    return bottleneck * L_inf


def select_variant(variants: list, key=None) -> dict:
    """
    Seleciona melhor variante por score darwiniano.
    
    Args:
        variants: Lista de variantes (dicts com scores)
        key: Função para extrair score (default: lambda x: x.get("darwin_score", 0))
        
    Returns:
        Variante com maior score
    """
    if not variants:
        return None
    
    if key is None:
        key = lambda x: x.get("darwin_score", 0.0)
    
    return max(variants, key=key)