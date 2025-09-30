"""
CAOS⁺ Engine - Estável com Log-Space + Tanh
===========================================

Implementa φ(CAOS⁺) com:
- Log-space para evitar overflow: log_caos = (O*S) * log(1 + κ*C*A)
- Saturação tanh: φ = tanh(γ * log_caos)
- Clamps para C,A,O,S ∈ [0,1] e κ ≤ κ_max
- Monotonicidade e estabilidade numérica
"""

import math
from typing import Dict, Any, Optional
from typing_extensions import Tuple
from dataclasses import dataclass


@dataclass
class CAOSComponents:
    """Componentes do CAOS⁺"""
    C: float  # Complexidade
    A: float  # Adaptabilidade  
    O: float  # Incognoscível (Unknowable)
    S: float  # Silêncio (Silence)
    
    def clamp(self, min_val: float = 0.0, max_val: float = 1.0) -> 'CAOSComponents':
        """Retorna componentes clampados"""
        return CAOSComponents(
            C=max(min_val, min(max_val, self.C)),
            A=max(min_val, min(max_val, self.A)),
            O=max(min_val, min(max_val, self.O)),
            S=max(min_val, min(max_val, self.S))
        )
        
    def to_dict(self) -> Dict[str, float]:
        return {"C": self.C, "A": self.A, "O": self.O, "S": self.S}


class CAOSPlusEngine:
    """
    Engine CAOS⁺ com estabilidade numérica
    
    Fórmula estável:
    log_caos = (O*S) * log(1 + κ*C*A)
    φ = tanh(γ * log_caos)
    """
    
    def __init__(self, 
                 kappa: float = 2.0,
                 kappa_max: float = 10.0,
                 gamma: float = 0.5,
                 epsilon: float = 1e-9):
        """
        Args:
            kappa: Fator de amplificação
            kappa_max: Valor máximo para κ (clamp)
            gamma: Fator de saturação tanh
            epsilon: Valor mínimo para estabilidade
        """
        self.kappa = max(1.0, min(kappa_max, kappa))  # Clamp κ
        self.kappa_max = kappa_max
        self.gamma = gamma
        self.epsilon = epsilon
        
    def compute_phi(self, components: CAOSComponents) -> Tuple[float, Dict[str, Any]]:
        """
        Computa φ(CAOS⁺) de forma estável
        
        Args:
            components: Componentes C,A,O,S
            
        Returns:
            (phi_value, details_dict)
        """
        # Clamp componentes
        safe_comp = components.clamp()
        C, A, O, S = safe_comp.C, safe_comp.A, safe_comp.O, safe_comp.S
        
        # Produto CA (núcleo da complexidade adaptativa)
        ca_product = C * A
        
        # Produto OS (expoente - representa incognoscível × silêncio)
        os_product = O * S
        
        # Log-space computation para evitar overflow
        # log_caos = (O*S) * log(1 + κ*C*A)
        inner_term = 1.0 + self.kappa * ca_product
        
        if inner_term <= self.epsilon:
            # Caso degenerado
            log_caos = 0.0
        else:
            log_caos = os_product * math.log(inner_term)
            
        # Saturação tanh para manter φ ∈ (-1, 1)
        phi_raw = math.tanh(self.gamma * log_caos)
        
        # Mapear para [0, 1] se necessário
        phi = (phi_raw + 1.0) / 2.0  # tanh ∈ [-1,1] → [0,1]
        
        # Detalhes para debug/auditoria
        details = {
            "components_raw": components.to_dict(),
            "components_clamped": safe_comp.to_dict(),
            "ca_product": ca_product,
            "os_product": os_product,
            "inner_term": inner_term,
            "log_caos": log_caos,
            "phi_raw": phi_raw,
            "phi": phi,
            "kappa": self.kappa,
            "gamma": self.gamma,
            "stable": True
        }
        
        return phi, details
        
    def compute_harmony(self, components: CAOSComponents) -> float:
        """
        Computa harmonia CAOS: (C+A) / (O+S)
        
        Representa balanceamento entre:
        - Numerador: Capacidades ativas (Complexidade + Adaptabilidade)
        - Denominador: Incertezas passivas (Incognoscível + Silêncio)
        """
        safe_comp = components.clamp()
        
        numerator = safe_comp.C + safe_comp.A
        denominator = safe_comp.O + safe_comp.S
        
        # Evitar divisão por zero
        if denominator < self.epsilon:
            return 1.0  # Default harmony
            
        harmony = numerator / denominator
        
        # Clamp para evitar valores extremos
        return max(0.0, min(10.0, harmony))
        
    def update_kappa(self, new_kappa: float) -> float:
        """
        Atualiza κ com clamp de segurança
        
        Returns:
            Valor efetivo de κ após clamp
        """
        self.kappa = max(1.0, min(self.kappa_max, new_kappa))
        return self.kappa
        
    def analyze_sensitivity(self, components: CAOSComponents, 
                          delta: float = 0.01) -> Dict[str, float]:
        """
        Análise de sensibilidade: ∂φ/∂component
        
        Args:
            components: Componentes base
            delta: Perturbação para diferença finita
            
        Returns:
            Dict com sensibilidades
        """
        phi_base, _ = self.compute_phi(components)
        
        sensitivities = {}
        
        for comp_name in ["C", "A", "O", "S"]:
            # Perturbar componente
            perturbed = CAOSComponents(**components.to_dict())
            current_val = getattr(perturbed, comp_name)
            setattr(perturbed, comp_name, current_val + delta)
            
            # Calcular φ perturbado
            phi_perturbed, _ = self.compute_phi(perturbed)
            
            # Sensibilidade (diferença finita)
            sensitivity = (phi_perturbed - phi_base) / delta
            sensitivities[f"d_phi_d_{comp_name}"] = sensitivity
            
        return sensitivities
        
    def check_monotonicity(self, components: CAOSComponents) -> Dict[str, bool]:
        """
        Verifica monotonicidade: φ deve crescer com C,A,O,S
        
        Returns:
            Dict indicando se cada componente é monotônico
        """
        phi_base, _ = self.compute_phi(components)
        
        monotonic = {}
        delta = 0.1
        
        for comp_name in ["C", "A", "O", "S"]:
            # Aumentar componente
            increased = CAOSComponents(**components.to_dict())
            current_val = getattr(increased, comp_name)
            new_val = min(1.0, current_val + delta)  # Clamp em 1.0
            setattr(increased, comp_name, new_val)
            
            phi_increased, _ = self.compute_phi(increased)
            
            # Deve ser monotônico crescente (ou pelo menos não decrescente)
            monotonic[comp_name] = phi_increased >= phi_base
            
        return monotonic
        
    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração atual"""
        return {
            "kappa": self.kappa,
            "kappa_max": self.kappa_max,
            "gamma": self.gamma,
            "epsilon": self.epsilon
        }


class CAOSPlusWithChaos(CAOSPlusEngine):
    """
    Extensão do CAOS⁺ com injeção de caos determinística
    """
    
    def __init__(self, 
                 kappa: float = 2.0,
                 kappa_max: float = 10.0,
                 gamma: float = 0.5,
                 chaos_probability: float = 0.01,
                 chaos_factor_range: Tuple[float, float] = (0.9, 1.1),
                 epsilon: float = 1e-9):
        """
        Args:
            chaos_probability: Probabilidade de injeção de caos
            chaos_factor_range: Range do fator de caos (multiplicativo)
        """
        super().__init__(kappa, kappa_max, gamma, epsilon)
        self.chaos_prob = chaos_probability
        self.chaos_range = chaos_factor_range
        
    def inject_chaos(self, components: CAOSComponents, 
                    rng_func: callable) -> CAOSComponents:
        """
        Injeta caos determinístico nos componentes
        
        Args:
            components: Componentes originais
            rng_func: Função RNG determinística (ex: lambda: random.random())
            
        Returns:
            Componentes com caos injetado
        """
        if rng_func() >= self.chaos_prob:
            return components  # Sem caos
            
        # Aplicar fator de caos
        chaos_factor = self.chaos_range[0] + rng_func() * (
            self.chaos_range[1] - self.chaos_range[0]
        )
        
        chaotic = CAOSComponents(
            C=components.C * chaos_factor,
            A=components.A * chaos_factor,
            O=components.O * chaos_factor,
            S=components.S * chaos_factor
        )
        
        return chaotic.clamp()  # Sempre clamp após caos
        
    def compute_phi_with_chaos(self, components: CAOSComponents,
                              rng_func: callable) -> Tuple[float, Dict[str, Any]]:
        """
        Computa φ com injeção de caos
        
        Args:
            components: Componentes base
            rng_func: Função RNG determinística
            
        Returns:
            (phi_value, details_with_chaos_info)
        """
        # Injetar caos
        chaotic_components = self.inject_chaos(components, rng_func)
        
        # Computar φ
        phi, details = self.compute_phi(chaotic_components)
        
        # Adicionar info de caos
        details["chaos_injected"] = not (chaotic_components.to_dict() == components.to_dict())
        details["original_components"] = components.to_dict()
        details["chaos_probability"] = self.chaos_prob
        
        return phi, details


# Funções de conveniência
def quick_caos_phi(C: float, A: float, O: float, S: float,
                   kappa: float = 2.0, gamma: float = 0.5) -> float:
    """Cálculo rápido de φ(CAOS⁺)"""
    engine = CAOSPlusEngine(kappa=kappa, gamma=gamma)
    components = CAOSComponents(C, A, O, S)
    phi, _ = engine.compute_phi(components)
    return phi


def quick_caos_harmony(C: float, A: float, O: float, S: float) -> float:
    """Cálculo rápido de harmonia CAOS"""
    engine = CAOSPlusEngine()
    components = CAOSComponents(C, A, O, S)
    return engine.compute_harmony(components)


def validate_caos_stability(C: float, A: float, O: float, S: float,
                           kappa: float = 2.0) -> Dict[str, Any]:
    """
    Valida estabilidade numérica do CAOS⁺
    
    Returns:
        Dict com resultados de validação
    """
    engine = CAOSPlusEngine(kappa=kappa)
    components = CAOSComponents(C, A, O, S)
    
    # Computar φ
    phi, details = engine.compute_phi(components)
    
    # Verificar monotonicidade
    monotonic = engine.check_monotonicity(components)
    
    # Análise de sensibilidade
    sensitivity = engine.analyze_sensitivity(components)
    
    return {
        "phi": phi,
        "details": details,
        "monotonic": monotonic,
        "sensitivity": sensitivity,
        "stable": details["stable"] and all(monotonic.values()),
        "components_valid": all(0 <= v <= 1 for v in [C, A, O, S])
    }