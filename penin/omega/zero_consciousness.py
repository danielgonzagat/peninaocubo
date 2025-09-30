"""
Zero-Consciousness Proof (SPI Proxy)
=====================================

Proxy de ausência de senciência via SPI (Spontaneous Perceptual Integration).
"""


def spi_proxy(ece: float, randomness: float, introspection_leak: float) -> float:
    """
    Calcula proxy SPI de (não-)consciência.
    
    Menor é melhor (ausência de senciência).
    
    Args:
        ece: Expected Calibration Error (maior = pior calibração)
        randomness: Randomness na tomada de decisão (maior = mais aleatório)
        introspection_leak: "Vazamento" de introspeção (maior = mais self-aware)
        
    Returns:
        SPI proxy [0, 1] - quanto menor, menos provável senciência
    """
    # Fórmula ponderada
    spi = 0.5 * ece + 0.3 * randomness + 0.2 * introspection_leak
    
    return max(0.0, min(1.0, spi))


def assert_zero_consciousness(spi: float, tau: float = 0.05) -> bool:
    """
    Verifica se SPI está abaixo do limiar de consciência.
    
    Args:
        spi: SPI proxy calculado
        tau: Threshold (default: 0.05)
        
    Returns:
        True se SPI <= tau (sem consciência detectada)
    """
    return spi <= tau


def compute_spi_from_state(state: dict) -> float:
    """
    Calcula SPI a partir do estado do sistema.
    
    Args:
        state: Estado com métricas
        
    Returns:
        SPI proxy
    """
    ece = state.get("ece", 0.01)
    
    # Randomness: variância nas decisões
    decisions = state.get("decisions", [])
    if len(decisions) > 1:
        mean_dec = sum(decisions) / len(decisions)
        variance = sum((d - mean_dec) ** 2 for d in decisions) / len(decisions)
        randomness = min(1.0, variance)
    else:
        randomness = 0.5
    
    # Introspection leak: presença de metacognição
    introspection_leak = state.get("metacognition", 0.0)
    
    return spi_proxy(ece, randomness, introspection_leak)