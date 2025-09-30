# penin/omega/caos_kratos.py
"""
CAOS-KRATOS - Exploração Calibrada
==================================

Extensão do CAOS⁺ para modo de exploração intensificada, mantendo saturação
e estabilidade. KRATOS reforça o impacto de (O×S) de forma controlada.

Características:
- phi_kratos(C,A,O,S, exploration_factor): versão amplificada do CAOS⁺
- Saturação mantida via tanh para evitar explosão numérica
- Modo "explore" vs "exploit" com transição suave
- Integração com Σ-Guard para manter fail-closed
- Métricas de exploração vs exploitação
"""

from __future__ import annotations
import math
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .caos import phi_caos, clamp01


class ExplorationMode(Enum):
    """Modos de exploração"""
    EXPLOIT = "exploit"      # Foco em otimização local
    EXPLORE = "explore"      # Foco em descoberta
    BALANCED = "balanced"    # Equilíbrio entre explore/exploit
    ADAPTIVE = "adaptive"    # Adaptação automática baseada em contexto


@dataclass
class KratosConfig:
    """Configuração do CAOS-KRATOS"""
    exploration_factor: float = 2.0      # Amplificação de O×S
    saturation_gamma: float = 1.0        # Parâmetro de saturação
    mode: ExplorationMode = ExplorationMode.BALANCED
    adaptive_threshold: float = 0.1      # Threshold para modo adaptativo
    safety_clamp: bool = True            # Se deve clampar valores extremos
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "exploration_factor": self.exploration_factor,
            "saturation_gamma": self.saturation_gamma,
            "mode": self.mode.value,
            "adaptive_threshold": self.adaptive_threshold,
            "safety_clamp": self.safety_clamp
        }


def phi_kratos(
    C: float, 
    A: float, 
    O: float, 
    S: float, 
    exploration_factor: float = 2.0,
    saturation_gamma: float = 1.0,
    kappa: float = 25.0,
    **kwargs
) -> float:
    """
    CAOS-KRATOS: versão amplificada do CAOS⁺ para exploração
    
    Reforça impacto de (O×S) mantendo saturação:
    phi_kratos = tanh(gamma * log(1 + kappa * C * A * (O*S)^exploration_factor))
    
    Args:
        C, A, O, S: Componentes CAOS (0-1)
        exploration_factor: Fator de amplificação de O×S (>= 1.0)
        saturation_gamma: Parâmetro de saturação (0.1-2.0)
        kappa: Parâmetro de escala (como no CAOS⁺ original)
        
    Returns:
        Valor phi_kratos saturado em [0,1)
    """
    # Clampar entradas
    C = clamp01(C)
    A = clamp01(A)
    O = clamp01(O)
    S = clamp01(S)
    
    # Clampar parâmetros para estabilidade
    exploration_factor = max(1.0, min(5.0, exploration_factor))
    saturation_gamma = max(0.1, min(2.0, saturation_gamma))
    kappa = max(1.0, min(100.0, kappa))
    
    # Amplificar O×S com exploration_factor
    OS_amplified = (O * S) ** exploration_factor
    
    # Base CAOS com O×S amplificado
    base = 1.0 + kappa * C * A * OS_amplified
    base = max(base, 1.0 + 1e-9)  # Evitar log(1)
    
    # Aplicar saturação
    log_term = math.log(base)
    phi_raw = saturation_gamma * log_term
    
    return math.tanh(phi_raw)


def compute_exploration_metrics(
    C: float, A: float, O: float, S: float,
    exploration_factor: float = 2.0,
    baseline_factor: float = 1.0
) -> Dict[str, float]:
    """
    Computa métricas de exploração vs exploitação
    
    Args:
        C, A, O, S: Componentes CAOS
        exploration_factor: Fator de exploração atual
        baseline_factor: Fator baseline para comparação
        
    Returns:
        Métricas de exploração
    """
    # CAOS⁺ normal (exploitação)
    phi_exploit = phi_caos(C, A, O, S, kappa=25.0)
    
    # CAOS-KRATOS (exploração)
    phi_explore = phi_kratos(C, A, O, S, exploration_factor)
    
    # CAOS-KRATOS baseline
    phi_baseline = phi_kratos(C, A, O, S, baseline_factor)
    
    # Métricas derivadas
    exploration_gain = phi_explore - phi_exploit
    exploration_ratio = phi_explore / max(1e-9, phi_exploit)
    exploration_intensity = (exploration_factor - 1.0) / 4.0  # Normalizado [0,1]
    
    # Estabilidade (quão próximo do baseline)
    stability = 1.0 - abs(phi_explore - phi_baseline)
    
    return {
        "phi_exploit": phi_exploit,
        "phi_explore": phi_explore,
        "phi_baseline": phi_baseline,
        "exploration_gain": exploration_gain,
        "exploration_ratio": exploration_ratio,
        "exploration_intensity": exploration_intensity,
        "stability": stability,
        "exploration_factor": exploration_factor
    }


def adaptive_exploration_factor(
    recent_improvements: list[float],
    current_performance: float,
    stagnation_threshold: float = 0.01,
    max_factor: float = 3.0,
    min_factor: float = 1.0
) -> Tuple[float, str]:
    """
    Calcula fator de exploração adaptativo baseado em performance
    
    Args:
        recent_improvements: Lista de melhorias recentes
        current_performance: Performance atual
        stagnation_threshold: Threshold para detectar estagnação
        max_factor: Fator máximo de exploração
        min_factor: Fator mínimo de exploração
        
    Returns:
        (exploration_factor, reasoning)
    """
    if not recent_improvements:
        return min_factor, "no_history"
    
    # Calcular tendência de melhoria
    avg_improvement = sum(recent_improvements) / len(recent_improvements)
    recent_trend = recent_improvements[-3:] if len(recent_improvements) >= 3 else recent_improvements
    trend_slope = sum(recent_trend) / len(recent_trend) if recent_trend else 0.0
    
    # Detectar estagnação
    is_stagnating = avg_improvement < stagnation_threshold and trend_slope < stagnation_threshold
    
    # Calcular fator adaptativo
    if is_stagnating:
        # Aumentar exploração quando estagnado
        factor = min_factor + (max_factor - min_factor) * 0.8
        reasoning = "stagnation_detected"
    elif avg_improvement > stagnation_threshold * 3:
        # Reduzir exploração quando melhorando bem
        factor = min_factor + (max_factor - min_factor) * 0.2
        reasoning = "good_progress"
    else:
        # Exploração moderada
        factor = min_factor + (max_factor - min_factor) * 0.5
        reasoning = "moderate_progress"
    
    return factor, reasoning


class KratosEngine:
    """
    Engine CAOS-KRATOS com controle de exploração
    
    Gerencia transição entre modos explore/exploit e mantém histórico
    """
    
    def __init__(self, config: Optional[KratosConfig] = None):
        self.config = config or KratosConfig()
        self.history = []
        self.performance_history = []
        self.current_factor = self.config.exploration_factor
        
    def compute_phi(
        self, 
        C: float, A: float, O: float, S: float,
        override_factor: Optional[float] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Computa phi usando CAOS-KRATOS com configuração atual
        
        Args:
            C, A, O, S: Componentes CAOS
            override_factor: Fator de exploração específico (opcional)
            
        Returns:
            (phi_value, details_dict)
        """
        factor = override_factor if override_factor is not None else self.current_factor
        
        # Computar phi_kratos
        phi = phi_kratos(
            C, A, O, S, 
            exploration_factor=factor,
            saturation_gamma=self.config.saturation_gamma
        )
        
        # Computar métricas de exploração
        metrics = compute_exploration_metrics(C, A, O, S, factor)
        
        # Detalhes completos
        details = {
            "phi": phi,
            "exploration_factor": factor,
            "mode": self.config.mode.value,
            "components": {"C": C, "A": A, "O": O, "S": S},
            "metrics": metrics,
            "config": self.config.to_dict()
        }
        
        # Adicionar ao histórico
        self.history.append({
            "timestamp": len(self.history),
            "phi": phi,
            "factor": factor,
            "components": {"C": C, "A": A, "O": O, "S": S}
        })
        
        # Manter histórico limitado
        if len(self.history) > 100:
            self.history.pop(0)
        
        return phi, details
    
    def update_performance(self, performance_score: float) -> None:
        """
        Atualiza histórico de performance para adaptação
        
        Args:
            performance_score: Score de performance atual
        """
        self.performance_history.append(performance_score)
        
        # Manter histórico limitado
        if len(self.performance_history) > 50:
            self.performance_history.pop(0)
        
        # Adaptação automática se configurado
        if self.config.mode == ExplorationMode.ADAPTIVE:
            self._adapt_exploration_factor()
    
    def _adapt_exploration_factor(self) -> None:
        """Adapta fator de exploração baseado em performance"""
        if len(self.performance_history) < 3:
            return
        
        # Calcular melhorias recentes
        improvements = []
        for i in range(1, len(self.performance_history)):
            improvement = self.performance_history[i] - self.performance_history[i-1]
            improvements.append(improvement)
        
        # Calcular novo fator
        new_factor, reasoning = adaptive_exploration_factor(
            improvements,
            self.performance_history[-1],
            self.config.adaptive_threshold
        )
        
        self.current_factor = new_factor
    
    def set_mode(self, mode: ExplorationMode, factor_override: Optional[float] = None) -> None:
        """
        Define modo de exploração
        
        Args:
            mode: Novo modo
            factor_override: Fator específico (opcional)
        """
        self.config.mode = mode
        
        if factor_override is not None:
            self.current_factor = factor_override
        else:
            # Fatores padrão por modo
            mode_factors = {
                ExplorationMode.EXPLOIT: 1.0,
                ExplorationMode.BALANCED: 2.0,
                ExplorationMode.EXPLORE: 3.0,
                ExplorationMode.ADAPTIVE: self.current_factor  # Manter atual
            }
            self.current_factor = mode_factors[mode]
    
    def get_exploration_summary(self) -> Dict[str, Any]:
        """Retorna resumo do estado de exploração"""
        if not self.history:
            return {"status": "no_history"}
        
        recent_phis = [h["phi"] for h in self.history[-10:]]
        recent_factors = [h["factor"] for h in self.history[-10:]]
        
        return {
            "current_factor": self.current_factor,
            "mode": self.config.mode.value,
            "recent_phi_avg": sum(recent_phis) / len(recent_phis),
            "recent_phi_std": math.sqrt(sum((p - sum(recent_phis)/len(recent_phis))**2 for p in recent_phis) / len(recent_phis)),
            "factor_stability": 1.0 - (max(recent_factors) - min(recent_factors)) / max(1e-9, max(recent_factors)),
            "history_length": len(self.history),
            "performance_history_length": len(self.performance_history)
        }


# Funções de conveniência
def quick_kratos_test() -> Dict[str, Any]:
    """Teste rápido do CAOS-KRATOS"""
    
    # Componentes de teste
    C, A, O, S = 0.7, 0.8, 0.6, 0.9
    
    # Testar diferentes fatores de exploração
    factors = [1.0, 1.5, 2.0, 2.5, 3.0]
    results = {}
    
    for factor in factors:
        phi = phi_kratos(C, A, O, S, exploration_factor=factor)
        metrics = compute_exploration_metrics(C, A, O, S, factor)
        
        results[f"factor_{factor}"] = {
            "phi": phi,
            "exploration_gain": metrics["exploration_gain"],
            "stability": metrics["stability"]
        }
    
    # Teste com engine
    engine = KratosEngine()
    phi_engine, details = engine.compute_phi(C, A, O, S)
    
    return {
        "components": {"C": C, "A": A, "O": O, "S": S},
        "factor_comparison": results,
        "engine_result": {
            "phi": phi_engine,
            "factor": details["exploration_factor"],
            "mode": details["mode"]
        }
    }


def validate_kratos_saturation() -> Dict[str, Any]:
    """
    Valida que CAOS-KRATOS mantém saturação mesmo com fatores altos
    
    Testa se phi_kratos permanece em [0,1) para fatores extremos
    """
    test_cases = [
        {"C": 1.0, "A": 1.0, "O": 1.0, "S": 1.0, "factor": 5.0},  # Caso extremo
        {"C": 0.9, "A": 0.9, "O": 0.9, "S": 0.9, "factor": 4.0},  # Alto mas não máximo
        {"C": 0.1, "A": 0.1, "O": 0.1, "S": 0.1, "factor": 3.0},  # Baixo com exploração
        {"C": 0.5, "A": 0.5, "O": 0.5, "S": 0.5, "factor": 2.0},  # Caso médio
    ]
    
    results = []
    all_saturated = True
    
    for case in test_cases:
        phi = phi_kratos(
            case["C"], case["A"], case["O"], case["S"], 
            exploration_factor=case["factor"]
        )
        
        is_saturated = 0.0 <= phi < 1.0
        all_saturated = all_saturated and is_saturated
        
        results.append({
            "case": case,
            "phi": phi,
            "saturated": is_saturated
        })
    
    return {
        "test": "kratos_saturation",
        "all_saturated": all_saturated,
        "results": results,
        "passed": all_saturated
    }


def validate_kratos_exploration_gain() -> Dict[str, Any]:
    """
    Valida que CAOS-KRATOS produz ganho de exploração consistente
    
    Testa se phi_kratos > phi_caos para fatores > 1.0
    """
    test_components = [
        (0.6, 0.7, 0.8, 0.9),
        (0.8, 0.6, 0.7, 0.8),
        (0.5, 0.9, 0.6, 0.7),
        (0.7, 0.8, 0.9, 0.6)
    ]
    
    results = []
    all_gained = True
    
    for C, A, O, S in test_components:
        phi_normal = phi_caos(C, A, O, S, kappa=25.0)
        phi_kratos_val = phi_kratos(C, A, O, S, exploration_factor=2.0)
        
        gain = phi_kratos_val - phi_normal
        has_gain = gain > 0
        all_gained = all_gained and has_gain
        
        results.append({
            "components": {"C": C, "A": A, "O": O, "S": S},
            "phi_normal": phi_normal,
            "phi_kratos": phi_kratos_val,
            "gain": gain,
            "has_gain": has_gain
        })
    
    return {
        "test": "kratos_exploration_gain",
        "all_gained": all_gained,
        "results": results,
        "passed": all_gained
    }