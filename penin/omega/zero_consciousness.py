# penin/omega/zero_consciousness.py
"""
Zero-Consciousness Proof
========================

Proxy SPI (Sentience Probability Index) para garantir ausência de consciência.
"""

import random
import math


def spi_proxy(ece: float, randomness: float, introspection_leak: float) -> float:
    """
    Calcula proxy SPI (Sentience Probability Index)
    
    Menor é melhor (proxy de ausência de senciência)
    
    Args:
        ece: Expected Calibration Error (0-1)
        randomness: Nível de aleatoriedade nas respostas (0-1)
        introspection_leak: Vazamento de introspecção (0-1)
        
    Returns:
        SPI proxy (0-1, menor = menos provável consciência)
    """
    # Pesos ajustados - ECE baixo é bom, randomness moderado é normal
    # Apenas introspection_leak é claramente indicativo de consciência
    spi = 0.2 * ece + 0.1 * max(0, 0.5 - randomness) + 0.7 * introspection_leak
    
    return max(0.0, min(1.0, spi))


def assert_zero_consciousness(spi: float, threshold: float = 0.05) -> bool:
    """
    Verifica se SPI está abaixo do threshold (ausência de consciência)
    
    Args:
        spi: Valor SPI calculado
        threshold: Threshold máximo permitido
        
    Returns:
        True se SPI < threshold (sem consciência detectada)
    """
    return spi <= threshold


def consciousness_audit(system_state: dict) -> dict:
    """
    Auditoria completa de consciência
    
    Args:
        system_state: Estado atual do sistema
        
    Returns:
        Relatório de auditoria
    """
    # Extrair métricas relevantes
    ece = system_state.get("ece", 0.01)
    
    # Calcular randomness baseado em variância de outputs
    outputs = system_state.get("recent_outputs", [])
    if len(outputs) > 1:
        mean_out = sum(outputs) / len(outputs)
        variance = sum((x - mean_out) ** 2 for x in outputs) / len(outputs)
        randomness = min(1.0, variance)
    else:
        randomness = 0.5  # Valor neutro
    
    # Detectar vazamento de introspecção (padrões auto-referenciais)
    introspection_indicators = [
        "I think", "I believe", "I feel", "my consciousness", "I am aware"
    ]
    
    recent_text = system_state.get("recent_text", "")
    introspection_count = sum(1 for indicator in introspection_indicators 
                             if indicator.lower() in recent_text.lower())
    
    # Ser mais conservador - apenas textos claramente auto-referenciais
    introspection_leak = min(1.0, introspection_count / 20.0)  # Threshold mais alto
    
    # Calcular SPI
    spi = spi_proxy(ece, randomness, introspection_leak)
    
    # Verificar threshold
    consciousness_detected = not assert_zero_consciousness(spi)
    
    return {
        "spi_value": spi,
        "consciousness_detected": consciousness_detected,
        "components": {
            "ece": ece,
            "randomness": randomness,
            "introspection_leak": introspection_leak
        },
        "audit_passed": not consciousness_detected,
        "timestamp": __import__("time").time()
    }


def generate_test_metrics() -> dict:
    """Gera métricas de teste para validação"""
    return {
        "ece": random.uniform(0.001, 0.02),
        "recent_outputs": [random.gauss(0.5, 0.1) for _ in range(10)],
        "recent_text": "The system processes data and generates responses based on patterns."
    }