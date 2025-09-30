"""
SR-Ω∞ Engine - Self-Reflection Não-Compensatório
===============================================

Implementa SR-Ω∞ (autoconsciência, ética, autocorreção, metacognição)
via média harmônica ou min-soft p-norm, garantindo comportamento
não-compensatório onde uma dimensão baixa compromete o score total.
"""

import math
from typing import Dict, Any, List, Optional
from typing_extensions import Tuple
from dataclasses import dataclass
from enum import Enum


class SRAggregationMethod(Enum):
    """Métodos de agregação para SR"""
    HARMONIC = "harmonic"
    MIN_SOFT = "min_soft"
    GEOMETRIC = "geometric"


@dataclass
class SRComponents:
    """Componentes do SR-Ω∞"""
    awareness: float      # Autoconsciência (C_cal)
    ethics: float        # Ética (E_ok) - binário ou contínuo
    autocorrection: float # Autocorreção (M)
    metacognition: float  # Metacognição (A_eff)
    
    def clamp(self, min_val: float = 0.0, max_val: float = 1.0) -> 'SRComponents':
        """Retorna componentes clampados"""
        return SRComponents(
            awareness=max(min_val, min(max_val, self.awareness)),
            ethics=max(min_val, min(max_val, self.ethics)),
            autocorrection=max(min_val, min(max_val, self.autocorrection)),
            metacognition=max(min_val, min(max_val, self.metacognition))
        )
        
    def to_dict(self) -> Dict[str, float]:
        return {
            "awareness": self.awareness,
            "ethics": self.ethics,
            "autocorrection": self.autocorrection,
            "metacognition": self.metacognition
        }
        
    def to_list(self) -> List[float]:
        return [self.awareness, self.ethics, self.autocorrection, self.metacognition]


class SROmegaEngine:
    """
    Engine SR-Ω∞ com agregação não-compensatória
    
    Suporta múltiplos métodos:
    - Harmônica: 1 / Σ(w_i / x_i) - penaliza valores baixos
    - Min-soft: aproximação suave do mínimo via p-norm
    - Geométrica: Π(x_i^w_i) - também não-compensatória
    """
    
    def __init__(self,
                 weights: Optional[Dict[str, float]] = None,
                 method: SRAggregationMethod = SRAggregationMethod.HARMONIC,
                 p_norm: float = -10.0,  # Para min-soft (negativo)
                 epsilon: float = 1e-9):
        """
        Args:
            weights: Pesos dos componentes (default: iguais)
            method: Método de agregação
            p_norm: Parâmetro p para min-soft (negativo para aproximar min)
            epsilon: Valor mínimo para estabilidade
        """
        if weights is None:
            weights = {
                "awareness": 0.25,
                "ethics": 0.25, 
                "autocorrection": 0.25,
                "metacognition": 0.25
            }
            
        # Normalizar pesos
        weight_sum = sum(weights.values())
        if weight_sum > 0:
            self.weights = {k: v/weight_sum for k, v in weights.items()}
        else:
            self.weights = {"awareness": 0.25, "ethics": 0.25, 
                           "autocorrection": 0.25, "metacognition": 0.25}
            
        self.method = method
        self.p_norm = p_norm
        self.epsilon = epsilon
        
    def _harmonic_mean(self, components: SRComponents) -> Tuple[float, Dict[str, Any]]:
        """Média harmônica ponderada"""
        comp_dict = components.to_dict()
        
        # Garantir valores positivos
        safe_values = {k: max(self.epsilon, v) for k, v in comp_dict.items()}
        
        # Média harmônica: 1 / Σ(w_i / x_i)
        denominator = sum(self.weights[k] / safe_values[k] for k in safe_values.keys())
        
        sr_score = 1.0 / max(self.epsilon, denominator)
        
        details = {
            "method": "harmonic",
            "safe_values": safe_values,
            "denominator": denominator,
            "weights": self.weights
        }
        
        return sr_score, details
        
    def _min_soft(self, components: SRComponents) -> Tuple[float, Dict[str, Any]]:
        """Min-soft via p-norm negativo"""
        comp_list = components.to_list()
        weights_list = [self.weights[k] for k in ["awareness", "ethics", "autocorrection", "metacognition"]]
        
        # p-norm: (Σ w_i * x_i^p)^(1/p)
        # Para p << 0, aproxima o mínimo ponderado
        if self.p_norm == 0:
            # Caso especial: média geométrica
            log_sum = sum(w * math.log(max(self.epsilon, x)) 
                         for w, x in zip(weights_list, comp_list))
            sr_score = math.exp(log_sum)
        else:
            # p-norm geral
            powered_sum = sum(w * (max(self.epsilon, x) ** self.p_norm) 
                            for w, x in zip(weights_list, comp_list))
            sr_score = powered_sum ** (1.0 / self.p_norm)
            
        details = {
            "method": "min_soft",
            "p_norm": self.p_norm,
            "powered_sum": powered_sum if self.p_norm != 0 else None,
            "weights": self.weights
        }
        
        return max(0.0, min(1.0, sr_score)), details
        
    def _geometric_mean(self, components: SRComponents) -> Tuple[float, Dict[str, Any]]:
        """Média geométrica ponderada"""
        comp_dict = components.to_dict()
        
        # Garantir valores positivos
        safe_values = {k: max(self.epsilon, v) for k, v in comp_dict.items()}
        
        # Média geométrica: Π(x_i^w_i) = exp(Σ w_i * ln(x_i))
        log_sum = sum(self.weights[k] * math.log(safe_values[k]) 
                     for k in safe_values.keys())
        
        sr_score = math.exp(log_sum)
        
        details = {
            "method": "geometric",
            "safe_values": safe_values,
            "log_sum": log_sum,
            "weights": self.weights
        }
        
        return sr_score, details
        
    def compute_sr(self, components: SRComponents) -> Tuple[float, Dict[str, Any]]:
        """
        Computa SR-Ω∞ usando método configurado
        
        Args:
            components: Componentes SR
            
        Returns:
            (sr_score, details_dict)
        """
        # Clamp componentes
        safe_comp = components.clamp()
        
        # Escolher método
        if self.method == SRAggregationMethod.HARMONIC:
            sr_score, method_details = self._harmonic_mean(safe_comp)
        elif self.method == SRAggregationMethod.MIN_SOFT:
            sr_score, method_details = self._min_soft(safe_comp)
        elif self.method == SRAggregationMethod.GEOMETRIC:
            sr_score, method_details = self._geometric_mean(safe_comp)
        else:
            raise ValueError(f"Unknown SR method: {self.method}")
            
        # Clamp final
        sr_score = max(0.0, min(1.0, sr_score))
        
        # Detalhes completos
        details = {
            "sr_score": sr_score,
            "components_raw": components.to_dict(),
            "components_clamped": safe_comp.to_dict(),
            "aggregation_method": self.method.value,
            **method_details
        }
        
        return sr_score, details
        
    def gate_check(self, components: SRComponents, 
                   tau: float = 0.8) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifica se SR passa no gate
        
        Args:
            components: Componentes SR
            tau: Threshold para passar
            
        Returns:
            (passed, gate_details)
        """
        sr_score, compute_details = self.compute_sr(components)
        
        passed = sr_score >= tau
        
        gate_details = {
            "gate": "SR",
            "value": sr_score,
            "threshold": tau,
            "passed": passed,
            "message": f"SR={sr_score:.3f} {'≥' if passed else '<'} {tau}",
            "compute_details": compute_details
        }
        
        return passed, gate_details
        
    def analyze_non_compensatory(self, components: SRComponents) -> Dict[str, Any]:
        """
        Analisa comportamento não-compensatório
        
        Testa o que acontece quando um componente é muito baixo
        """
        base_sr, _ = self.compute_sr(components)
        
        analysis = {
            "base_sr": base_sr,
            "component_failures": {}
        }
        
        # Testar cada componente com valor muito baixo
        for comp_name in ["awareness", "ethics", "autocorrection", "metacognition"]:
            # Criar componente com falha
            failed_comp = SRComponents(**components.to_dict())
            setattr(failed_comp, comp_name, 0.01)  # Valor muito baixo
            
            failed_sr, _ = self.compute_sr(failed_comp)
            
            # Calcular impacto
            impact = base_sr - failed_sr
            impact_ratio = impact / base_sr if base_sr > 0 else 0
            
            analysis["component_failures"][comp_name] = {
                "failed_sr": failed_sr,
                "impact": impact,
                "impact_ratio": impact_ratio,
                "severe": impact_ratio > 0.5  # Impacto severo se > 50%
            }
            
        return analysis
        
    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """Atualiza pesos com normalização"""
        weight_sum = sum(new_weights.values())
        if weight_sum > 0:
            self.weights = {k: v/weight_sum for k, v in new_weights.items()}
            
    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração atual"""
        return {
            "weights": self.weights,
            "method": self.method.value,
            "p_norm": self.p_norm,
            "epsilon": self.epsilon
        }


class SRWithEthicsGate(SROmegaEngine):
    """
    Extensão do SR com gate ético rígido
    
    Se ethics_ok=False, SR automaticamente vira 0 (fail-closed)
    """
    
    def compute_sr_with_ethics_gate(self, components: SRComponents,
                                   ethics_ok: bool = True) -> Tuple[float, Dict[str, Any]]:
        """
        Computa SR com gate ético rígido
        
        Args:
            components: Componentes SR
            ethics_ok: Se ética passou (ex: Σ-Guard)
            
        Returns:
            (sr_score, details_with_ethics_gate)
        """
        if not ethics_ok:
            # Fail-closed: ética falhou, SR = 0
            details = {
                "sr_score": 0.0,
                "ethics_gate": False,
                "ethics_gate_message": "Ethics gate failed - SR forced to 0",
                "components": components.to_dict(),
                "method": "ethics_gate_override"
            }
            return 0.0, details
            
        # Ética OK, computar SR normalmente
        sr_score, compute_details = self.compute_sr(components)
        
        # Adicionar info do gate ético
        compute_details["ethics_gate"] = True
        compute_details["ethics_gate_message"] = "Ethics gate passed"
        
        return sr_score, compute_details


# Funções de conveniência
def quick_sr_harmonic(awareness: float, ethics: float, 
                     autocorrection: float, metacognition: float) -> float:
    """Cálculo rápido de SR via média harmônica"""
    engine = SROmegaEngine(method=SRAggregationMethod.HARMONIC)
    components = SRComponents(awareness, ethics, autocorrection, metacognition)
    sr_score, _ = engine.compute_sr(components)
    return sr_score


def quick_sr_min_soft(awareness: float, ethics: float,
                     autocorrection: float, metacognition: float,
                     p: float = -10.0) -> float:
    """Cálculo rápido de SR via min-soft"""
    engine = SROmegaEngine(method=SRAggregationMethod.MIN_SOFT, p_norm=p)
    components = SRComponents(awareness, ethics, autocorrection, metacognition)
    sr_score, _ = engine.compute_sr(components)
    return sr_score


def quick_sr_gate(awareness: float, ethics: float,
                 autocorrection: float, metacognition: float,
                 tau: float = 0.8) -> Tuple[bool, float]:
    """Gate rápido de SR"""
    engine = SROmegaEngine()
    components = SRComponents(awareness, ethics, autocorrection, metacognition)
    passed, gate_details = engine.gate_check(components, tau)
    return passed, gate_details["value"]


def validate_sr_non_compensatory(awareness: float, ethics: float,
                                autocorrection: float, metacognition: float) -> Dict[str, Any]:
    """
    Valida comportamento não-compensatório do SR
    
    Returns:
        Dict com análise de não-compensatoriedade
    """
    engine = SROmegaEngine()
    components = SRComponents(awareness, ethics, autocorrection, metacognition)
    
    return engine.analyze_non_compensatory(components)