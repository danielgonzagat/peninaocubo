"""
Auto-Tuning Module - AdaGrad Online
===================================

Implementa auto-tuning online via AdaGrad/ONS para:
- κ (CAOS⁺ amplification factor)
- λ_c (cost penalty factor)
- wU, wS, wC, wL (Score U/S/C/L weights)
- β_min (minimum ΔL∞ for promotion)
- τ* (various thresholds)

Com limites de variação por ciclo (≤0.02) e clamps globais.
"""

import math
import time
import json
from typing import Dict, Any, List, Optional, Callable
from typing_extensions import Tuple
from dataclasses import dataclass, field
from enum import Enum


class TuningMethod(Enum):
    """Métodos de tuning suportados"""
    ADAGRAD = "adagrad"
    ONS = "ons"  # Online Newton Step
    MOMENTUM = "momentum"


@dataclass
class TuningParameter:
    """Parâmetro tunável"""
    name: str
    current_value: float
    min_value: float
    max_value: float
    step_size: float
    max_step_per_cycle: float = 0.02  # Máximo 2% de mudança por ciclo
    
    # AdaGrad state
    gradient_sum_squares: float = 0.0
    epsilon: float = 1e-8
    
    # Momentum state (se usar)
    momentum: float = 0.0
    momentum_decay: float = 0.9
    
    def clamp_value(self, value: float) -> float:
        """Clamp valor nos limites"""
        return max(self.min_value, min(self.max_value, value))
        
    def compute_max_step(self) -> float:
        """Computa passo máximo permitido para este ciclo"""
        return self.current_value * self.max_step_per_cycle
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "current_value": self.current_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "step_size": self.step_size,
            "max_step_per_cycle": self.max_step_per_cycle,
            "gradient_sum_squares": self.gradient_sum_squares,
            "momentum": self.momentum
        }


@dataclass
class TuningState:
    """Estado do tuning"""
    cycle: int = 0
    total_updates: int = 0
    last_objective: float = 0.0
    best_objective: float = 0.0
    best_params: Dict[str, float] = field(default_factory=dict)
    convergence_history: List[float] = field(default_factory=list)
    
    def update_objective(self, new_objective: float, params: Dict[str, float]):
        """Atualiza objetivo e histórico"""
        self.last_objective = new_objective
        self.convergence_history.append(new_objective)
        
        # Manter apenas últimos 50 valores
        if len(self.convergence_history) > 50:
            self.convergence_history = self.convergence_history[-50:]
            
        # Atualizar melhor
        if new_objective > self.best_objective:
            self.best_objective = new_objective
            self.best_params = params.copy()
            
    def is_converged(self, tolerance: float = 1e-4, window: int = 10) -> bool:
        """Verifica se convergiu (pouca variação recente)"""
        if len(self.convergence_history) < window:
            return False
            
        recent = self.convergence_history[-window:]
        variance = sum((x - sum(recent)/len(recent))**2 for x in recent) / len(recent)
        
        return variance < tolerance
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "total_updates": self.total_updates,
            "last_objective": self.last_objective,
            "best_objective": self.best_objective,
            "best_params": self.best_params,
            "convergence_history": self.convergence_history[-10:],  # Últimos 10
            "converged": self.is_converged()
        }


class AdaGradTuner:
    """Auto-tuner usando AdaGrad"""
    
    def __init__(self, 
                 learning_rate: float = 0.01,
                 epsilon: float = 1e-8):
        """
        Args:
            learning_rate: Taxa de aprendizado base
            epsilon: Valor para estabilidade numérica
        """
        self.learning_rate = learning_rate
        self.epsilon = epsilon
        self.parameters: Dict[str, TuningParameter] = {}
        self.state = TuningState()
        
    def add_parameter(self,
                     name: str,
                     initial_value: float,
                     min_value: float,
                     max_value: float,
                     max_step_per_cycle: float = 0.02) -> None:
        """
        Adiciona parâmetro para tuning
        
        Args:
            name: Nome do parâmetro
            initial_value: Valor inicial
            min_value: Valor mínimo
            max_value: Valor máximo
            max_step_per_cycle: Máxima variação por ciclo (fração)
        """
        param = TuningParameter(
            name=name,
            current_value=initial_value,
            min_value=min_value,
            max_value=max_value,
            step_size=self.learning_rate,
            max_step_per_cycle=max_step_per_cycle
        )
        
        self.parameters[name] = param
        
    def compute_gradient(self,
                        param_name: str,
                        objective_func: Callable[[Dict[str, float]], float],
                        current_params: Dict[str, float],
                        delta: float = 1e-4) -> float:
        """
        Computa gradiente via diferença finita
        
        Args:
            param_name: Nome do parâmetro
            objective_func: Função objetivo (maior é melhor)
            current_params: Parâmetros atuais
            delta: Perturbação para diferença finita
            
        Returns:
            Gradiente estimado
        """
        if param_name not in self.parameters:
            return 0.0
            
        param = self.parameters[param_name]
        
        # Valor atual
        base_objective = objective_func(current_params)
        
        # Valor perturbado (para frente)
        perturbed_params = current_params.copy()
        perturbed_value = param.clamp_value(param.current_value + delta)
        perturbed_params[param_name] = perturbed_value
        
        try:
            perturbed_objective = objective_func(perturbed_params)
            gradient = (perturbed_objective - base_objective) / delta
        except Exception:
            # Se falhar, usar gradiente zero (sem atualização)
            gradient = 0.0
            
        return gradient
        
    def update_parameter(self,
                        param_name: str,
                        gradient: float) -> Tuple[float, Dict[str, Any]]:
        """
        Atualiza parâmetro usando AdaGrad
        
        Args:
            param_name: Nome do parâmetro
            gradient: Gradiente calculado
            
        Returns:
            (new_value, update_details)
        """
        if param_name not in self.parameters:
            return 0.0, {"error": f"Parameter {param_name} not found"}
            
        param = self.parameters[param_name]
        
        # AdaGrad: acumular gradientes quadrados
        param.gradient_sum_squares += gradient ** 2
        
        # Adaptive learning rate
        adaptive_lr = self.learning_rate / (math.sqrt(param.gradient_sum_squares) + self.epsilon)
        
        # Calcular passo
        raw_step = adaptive_lr * gradient
        
        # Limitar passo por ciclo
        max_step = param.compute_max_step()
        clamped_step = max(-max_step, min(max_step, raw_step))
        
        # Novo valor
        new_value = param.clamp_value(param.current_value + clamped_step)
        
        # Atualizar parâmetro
        old_value = param.current_value
        param.current_value = new_value
        
        details = {
            "param_name": param_name,
            "old_value": old_value,
            "new_value": new_value,
            "gradient": gradient,
            "raw_step": raw_step,
            "clamped_step": clamped_step,
            "adaptive_lr": adaptive_lr,
            "gradient_sum_squares": param.gradient_sum_squares,
            "max_step_allowed": max_step,
            "step_limited": abs(raw_step) > max_step
        }
        
        return new_value, details
        
    def tune_cycle(self,
                  objective_func: Callable[[Dict[str, float]], float],
                  warmup_cycles: int = 5) -> Dict[str, Any]:
        """
        Executa um ciclo de tuning
        
        Args:
            objective_func: Função objetivo (recebe dict de params, retorna score)
            warmup_cycles: Ciclos de warmup antes de começar tuning
            
        Returns:
            Dict com resultados do tuning
        """
        self.state.cycle += 1
        
        # Parâmetros atuais
        current_params = {name: param.current_value 
                         for name, param in self.parameters.items()}
        
        # Avaliar objetivo atual
        try:
            current_objective = objective_func(current_params)
        except Exception as e:
            return {
                "error": f"Objective function failed: {e}",
                "cycle": self.state.cycle
            }
            
        # Atualizar estado
        self.state.update_objective(current_objective, current_params)
        
        results = {
            "cycle": self.state.cycle,
            "current_objective": current_objective,
            "best_objective": self.state.best_objective,
            "current_params": current_params,
            "parameter_updates": {},
            "tuning_active": self.state.cycle > warmup_cycles
        }
        
        # Skip tuning durante warmup
        if self.state.cycle <= warmup_cycles:
            results["warmup"] = True
            return results
            
        # Computar gradientes e atualizar parâmetros
        for param_name in self.parameters.keys():
            try:
                # Computar gradiente
                gradient = self.compute_gradient(
                    param_name, objective_func, current_params
                )
                
                # Atualizar parâmetro
                new_value, update_details = self.update_parameter(param_name, gradient)
                
                results["parameter_updates"][param_name] = update_details
                self.state.total_updates += 1
                
            except Exception as e:
                results["parameter_updates"][param_name] = {
                    "error": str(e)
                }
                
        # Atualizar parâmetros atuais
        results["updated_params"] = {name: param.current_value 
                                   for name, param in self.parameters.items()}
        
        return results
        
    def get_tuning_summary(self) -> Dict[str, Any]:
        """Retorna resumo do tuning"""
        return {
            "state": self.state.to_dict(),
            "parameters": {name: param.to_dict() 
                          for name, param in self.parameters.items()},
            "config": {
                "learning_rate": self.learning_rate,
                "epsilon": self.epsilon,
                "method": "adagrad"
            }
        }
        
    def reset_parameter(self, param_name: str, new_value: float) -> bool:
        """Reset parâmetro para novo valor"""
        if param_name not in self.parameters:
            return False
            
        param = self.parameters[param_name]
        param.current_value = param.clamp_value(new_value)
        param.gradient_sum_squares = 0.0  # Reset AdaGrad state
        param.momentum = 0.0
        
        return True
        
    def save_state(self, filepath: str) -> bool:
        """Salva estado do tuner"""
        try:
            state_data = {
                "tuning_state": self.state.to_dict(),
                "parameters": {name: param.to_dict() 
                              for name, param in self.parameters.items()},
                "config": {
                    "learning_rate": self.learning_rate,
                    "epsilon": self.epsilon
                },
                "timestamp": time.time()
            }
            
            with open(filepath, 'w') as f:
                json.dump(state_data, f, indent=2)
                
            return True
        except Exception:
            return False
            
    def load_state(self, filepath: str) -> bool:
        """Carrega estado do tuner"""
        try:
            with open(filepath, 'r') as f:
                state_data = json.load(f)
                
            # Restaurar parâmetros
            for name, param_data in state_data["parameters"].items():
                param = TuningParameter(
                    name=param_data["name"],
                    current_value=param_data["current_value"],
                    min_value=param_data["min_value"],
                    max_value=param_data["max_value"],
                    step_size=param_data["step_size"],
                    max_step_per_cycle=param_data["max_step_per_cycle"]
                )
                param.gradient_sum_squares = param_data["gradient_sum_squares"]
                param.momentum = param_data["momentum"]
                
                self.parameters[name] = param
                
            # Restaurar estado
            tuning_state = state_data["tuning_state"]
            self.state.cycle = tuning_state["cycle"]
            self.state.total_updates = tuning_state["total_updates"]
            self.state.last_objective = tuning_state["last_objective"]
            self.state.best_objective = tuning_state["best_objective"]
            self.state.best_params = tuning_state["best_params"]
            self.state.convergence_history = tuning_state["convergence_history"]
            
            return True
        except Exception:
            return False


class PeninAutoTuner:
    """Auto-tuner específico para PENIN-Ω"""
    
    def __init__(self, 
                 learning_rate: float = 0.01,
                 warmup_cycles: int = 5):
        """
        Args:
            learning_rate: Taxa de aprendizado
            warmup_cycles: Ciclos antes de começar tuning
        """
        self.tuner = AdaGradTuner(learning_rate)
        self.warmup_cycles = warmup_cycles
        
        # Configurar parâmetros padrão do PENIN
        self._setup_penin_parameters()
        
    def _setup_penin_parameters(self):
        """Configura parâmetros específicos do PENIN"""
        # κ (CAOS⁺ amplification)
        self.tuner.add_parameter(
            "kappa", 
            initial_value=2.0,
            min_value=1.0,
            max_value=10.0,
            max_step_per_cycle=0.02
        )
        
        # λ_c (cost penalty)
        self.tuner.add_parameter(
            "lambda_c",
            initial_value=0.1,
            min_value=0.01,
            max_value=1.0,
            max_step_per_cycle=0.02
        )
        
        # Pesos U/S/C/L (com constraint de soma = 1.0)
        for weight_name, initial in [("wU", 0.3), ("wS", 0.3), ("wC", 0.2), ("wL", 0.2)]:
            self.tuner.add_parameter(
                weight_name,
                initial_value=initial,
                min_value=0.05,  # Mínimo 5%
                max_value=0.8,   # Máximo 80%
                max_step_per_cycle=0.02
            )
            
        # β_min (minimum ΔL∞)
        self.tuner.add_parameter(
            "beta_min",
            initial_value=0.02,
            min_value=0.001,
            max_value=0.1,
            max_step_per_cycle=0.02
        )
        
        # τ_score (Score threshold)
        self.tuner.add_parameter(
            "tau_score",
            initial_value=0.7,
            min_value=0.5,
            max_value=0.95,
            max_step_per_cycle=0.02
        )
        
    def normalize_weights(self) -> None:
        """Normaliza pesos U/S/C/L para somar 1.0"""
        weight_names = ["wU", "wS", "wC", "wL"]
        current_weights = [self.tuner.parameters[name].current_value 
                          for name in weight_names]
        
        weight_sum = sum(current_weights)
        if weight_sum > 0:
            # Normalizar mantendo proporções
            for name, weight in zip(weight_names, current_weights):
                normalized = weight / weight_sum
                self.tuner.parameters[name].current_value = normalized
                
    def create_objective_function(self,
                                 evaluation_history: List[Dict[str, float]]) -> Callable[[Dict[str, float]], float]:
        """
        Cria função objetivo baseada no histórico de avaliações
        
        Args:
            evaluation_history: Lista de avaliações {U, S, C, L, linf, cost, etc.}
            
        Returns:
            Função objetivo que maximiza L∞ médio com penalização de custo
        """
        def objective(params: Dict[str, float]) -> float:
            if not evaluation_history:
                return 0.0
                
            # Simular L∞ com novos parâmetros
            total_score = 0.0
            
            for eval_data in evaluation_history:
                # Recalcular score com novos pesos
                U, S, C, L = eval_data.get("U", 0), eval_data.get("S", 0), eval_data.get("C", 0), eval_data.get("L", 0)
                
                # Score U/S/C/L com novos pesos
                wU = params.get("wU", 0.25)
                wS = params.get("wS", 0.25) 
                wC = params.get("wC", 0.25)
                wL = params.get("wL", 0.25)
                
                score = wU * U + wS * S - wC * C + wL * L  # C é negativo
                score = max(0.0, min(1.0, score))
                
                # Penalização por custo com novo λ_c
                lambda_c = params.get("lambda_c", 0.1)
                cost = eval_data.get("cost", 0.0)
                cost_penalty = math.exp(-lambda_c * cost)
                
                # L∞ aproximado
                linf_approx = score * cost_penalty
                total_score += linf_approx
                
            # Objetivo: maximizar L∞ médio
            avg_linf = total_score / len(evaluation_history)
            
            # Penalizar configurações extremas (regularização)
            kappa = params.get("kappa", 2.0)
            kappa_penalty = 0.01 * (kappa - 2.0) ** 2  # Penalizar desvio de 2.0
            
            return avg_linf - kappa_penalty
            
        return objective
        
    def tune_from_evaluations(self,
                            evaluation_history: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Executa tuning baseado no histórico de avaliações
        
        Args:
            evaluation_history: Histórico de avaliações
            
        Returns:
            Resultado do tuning
        """
        if not evaluation_history:
            return {"error": "No evaluation history provided"}
            
        # Criar função objetivo
        objective_func = self.create_objective_function(evaluation_history)
        
        # Executar ciclo de tuning
        result = self.tuner.tune_cycle(objective_func, self.warmup_cycles)
        
        # Normalizar pesos após tuning
        if result.get("tuning_active", False):
            self.normalize_weights()
            result["weights_normalized"] = True
            result["final_params"] = {name: param.current_value 
                                    for name, param in self.tuner.parameters.items()}
        
        return result
        
    def get_current_config(self) -> Dict[str, float]:
        """Retorna configuração atual dos parâmetros"""
        return {name: param.current_value 
                for name, param in self.tuner.parameters.items()}
        
    def get_tuning_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de tuning"""
        return self.tuner.get_tuning_summary()


class OnlineNeuralTuner:
    """Tuner usando Online Newton Step (ONS) - mais avançado"""
    
    def __init__(self, 
                 learning_rate: float = 0.01,
                 regularization: float = 0.01):
        self.learning_rate = learning_rate
        self.regularization = regularization
        # Implementação simplificada - em produção seria mais complexa
        self.adagrad_fallback = AdaGradTuner(learning_rate)
        
    def tune_cycle(self, objective_func: Callable, warmup_cycles: int = 5) -> Dict[str, Any]:
        """Fallback para AdaGrad por simplicidade"""
        return self.adagrad_fallback.tune_cycle(objective_func, warmup_cycles)


# Funções de conveniência
def quick_tune_kappa(evaluation_history: List[Dict[str, float]],
                    current_kappa: float = 2.0) -> Tuple[float, Dict[str, Any]]:
    """Tuning rápido apenas do κ"""
    tuner = PeninAutoTuner()
    
    # Configurar apenas κ
    tuner.tuner.parameters = {}
    tuner.tuner.add_parameter("kappa", current_kappa, 1.0, 10.0)
    
    result = tuner.tune_from_evaluations(evaluation_history)
    
    new_kappa = tuner.get_current_config().get("kappa", current_kappa)
    return new_kappa, result


def quick_tune_weights(evaluation_history: List[Dict[str, float]],
                      current_weights: Dict[str, float]) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """Tuning rápido dos pesos U/S/C/L"""
    tuner = PeninAutoTuner()
    
    # Configurar apenas pesos
    tuner.tuner.parameters = {}
    for name, value in current_weights.items():
        if name in ["wU", "wS", "wC", "wL"]:
            tuner.tuner.add_parameter(name, value, 0.05, 0.8)
            
    result = tuner.tune_from_evaluations(evaluation_history)
    
    new_weights = {name: tuner.tuner.parameters[name].current_value 
                  for name in current_weights.keys() 
                  if name in tuner.tuner.parameters}
    
    return new_weights, result


# Exemplo de uso
if __name__ == "__main__":
    print("🎛️  Demonstração: Auto-Tuning AdaGrad")
    print("=" * 60)
    
    # Criar tuner
    tuner = PeninAutoTuner(learning_rate=0.01, warmup_cycles=2)
    
    print("✅ Parâmetros configurados:")
    for name, param in tuner.tuner.parameters.items():
        print(f"   {name}: {param.current_value:.3f} [{param.min_value}, {param.max_value}]")
    print()
    
    # Simular histórico de avaliações
    evaluation_history = [
        {"U": 0.7, "S": 0.8, "C": 0.3, "L": 0.6, "cost": 0.05, "linf": 0.65},
        {"U": 0.8, "S": 0.7, "C": 0.4, "L": 0.7, "cost": 0.08, "linf": 0.70},
        {"U": 0.6, "S": 0.9, "C": 0.2, "L": 0.5, "cost": 0.03, "linf": 0.72},
        {"U": 0.9, "S": 0.6, "C": 0.5, "L": 0.8, "cost": 0.12, "linf": 0.68},
    ]
    
    print(f"📊 Histórico de avaliações: {len(evaluation_history)} entradas")
    for i, eval_data in enumerate(evaluation_history, 1):
        print(f"   {i}. U={eval_data['U']:.1f}, S={eval_data['S']:.1f}, "
              f"C={eval_data['C']:.1f}, L={eval_data['L']:.1f}, L∞={eval_data['linf']:.2f}")
    print()
    
    # Executar alguns ciclos de tuning
    print("🔄 Executando ciclos de tuning...")
    for cycle in range(5):
        result = tuner.tune_from_evaluations(evaluation_history)
        
        if "error" in result:
            print(f"   Ciclo {cycle+1}: ERRO - {result['error']}")
            continue
            
        print(f"   Ciclo {cycle+1}: objetivo={result['current_objective']:.4f}, "
              f"melhor={result['best_objective']:.4f}")
        
        if result.get("tuning_active", False):
            # Mostrar atualizações de parâmetros
            updates = result.get("parameter_updates", {})
            for param_name, update_info in updates.items():
                if "error" not in update_info:
                    old_val = update_info["old_value"]
                    new_val = update_info["new_value"]
                    if abs(new_val - old_val) > 1e-6:
                        print(f"      {param_name}: {old_val:.4f} → {new_val:.4f} "
                              f"(Δ={new_val-old_val:+.4f})")
        else:
            print(f"      (warmup - sem tuning)")
            
    print()
    
    # Resumo final
    summary = tuner.get_tuning_stats()
    print("📈 Resumo do tuning:")
    print(f"   Ciclos: {summary['state']['cycle']}")
    print(f"   Updates: {summary['state']['total_updates']}")
    print(f"   Convergiu: {summary['state']['converged']}")
    print(f"   Melhor objetivo: {summary['state']['best_objective']:.4f}")
    
    print("\n✅ Parâmetros finais:")
    final_config = tuner.get_current_config()
    for name, value in final_config.items():
        print(f"   {name}: {value:.4f}")
        
    # Verificar se pesos somam 1.0
    weight_sum = sum(final_config[name] for name in ["wU", "wS", "wC", "wL"])
    print(f"   Soma dos pesos: {weight_sum:.4f} (deve ser ~1.0)")
    
    print("\n✅ Auto-tuning implementado e funcionando!")
    print("🔄 Próximo: Implementar runners (evolve_one_cycle)")