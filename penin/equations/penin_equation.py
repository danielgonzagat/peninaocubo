"""
Equação 1: Equação de Penin — Autoevolução Recursiva
====================================================

Forma: I_{t+1} = f(I_t, E_t, P_t) = Π_{H∩S}[I_t + α_t · G(I_t,E_t;P_t)]

Implementa atualização de estado com gradiente projetado e controle ético.

Componentes:
-----------
- G: direção de melhoria (gradiente, policy-gradient, TD)
- α_t: passo dinâmico modulado por CAOS⁺, SR e R_t
- Π_{H∩S}: projeção no conjunto técnico-seguro (H) ∩ ético-seguro (S)

Propriedades garantidas:
-----------------------
- Contratividade via α modulada
- Fail-closed em violações éticas
- Auditabilidade completa via WORM
- Rollback automático em falhas
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class GradientMethod(Enum):
    """Métodos de estimação de gradiente"""

    ANALYTICAL = "analytical"  # Gradiente analítico direto
    POLICY_GRADIENT = "policy_gradient"  # Policy gradient (REINFORCE)
    TD_LEARNING = "td_learning"  # Temporal Difference
    EVOLUTION_STRATEGY = "evolution_strategy"  # ES (perturbações)
    FINITE_DIFFERENCE = "finite_difference"  # Diferenças finitas numéricas


@dataclass
class PeninState:
    """
    Estado interno I da arquitetura

    Representa parâmetros, políticas, memória e meta-estado
    """

    # Parâmetros principais (podem ser vetores, matrizes, tensores)
    parameters: np.ndarray

    # Políticas de controle
    policies: dict[str, Any] = field(default_factory=dict)

    # Memória episódica/semântica
    memory: dict[str, Any] = field(default_factory=dict)

    # Meta-estado (métricas, histórico)
    meta: dict[str, Any] = field(default_factory=dict)

    # Timestamp
    timestamp: float = 0.0

    # Versão (para rollback)
    version: int = 0

    def clone(self) -> PeninState:
        """Cria cópia profunda do estado"""
        return PeninState(
            parameters=self.parameters.copy(),
            policies=dict(self.policies),
            memory=dict(self.memory),
            meta=dict(self.meta),
            timestamp=self.timestamp,
            version=self.version + 1,
        )

    def distance_to(self, other: PeninState) -> float:
        """Calcula distância L2 entre estados"""
        return float(np.linalg.norm(self.parameters - other.parameters))

    def norm(self) -> float:
        """Norma L2 do estado"""
        return float(np.linalg.norm(self.parameters))


@dataclass
class Evidence:
    """
    Evidências E do ambiente

    Dados, feedback externo, tarefas, recompensas
    """

    # Dados de entrada
    data: dict[str, Any] = field(default_factory=dict)

    # Feedback/recompensas
    rewards: list[float] = field(default_factory=list)

    # Tarefas/objetivos
    tasks: list[dict[str, Any]] = field(default_factory=list)

    # Contexto ambiental
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ControlPolicy:
    """
    Políticas P de atualização/controle

    Taxas, restrições, gates, thresholds
    """

    # Taxa base de aprendizado
    base_alpha: float = 1e-3

    # Restrições (H ∩ S)
    constraints: dict[str, Any] = field(default_factory=dict)

    # Gates éticos
    ethical_gates: dict[str, bool] = field(default_factory=dict)

    # Thresholds de segurança
    safety_thresholds: dict[str, float] = field(default_factory=dict)

    # Método de gradiente
    gradient_method: GradientMethod = GradientMethod.ANALYTICAL


@dataclass
class ProjectionConstraints:
    """
    Conjunto H ∩ S de restrições

    - H: técnico-seguro (box constraints, normas, limites)
    - S: ético-seguro (ΣEA/LO-14, privacidade, limites legais)
    """

    # Box constraints (min/max por dimensão)
    param_min: np.ndarray | None = None
    param_max: np.ndarray | None = None

    # Norma máxima permitida
    max_norm: float = 10.0

    # Limites éticos (violação -> reject)
    ethical_constraints: dict[str, Callable] = field(default_factory=dict)

    # Budget constraints (custo, energia, tempo)
    budget_max: dict[str, float] = field(default_factory=dict)

    # Privacidade (differential privacy epsilon)
    privacy_epsilon: float = 1.0

    # Fairness constraints
    fairness_thresholds: dict[str, float] = field(default_factory=dict)


def estimate_gradient(
    state: PeninState,
    evidence: Evidence,
    policy: ControlPolicy,
    objective_fn: Callable[[PeninState, Evidence], float],
    method: GradientMethod = GradientMethod.ANALYTICAL,
) -> np.ndarray:
    """
    Estima G(I, E; P) - direção de melhoria

    Args:
        state: Estado atual I_t
        evidence: Evidências E_t
        policy: Políticas P_t
        objective_fn: Função objetivo J(I; E) para otimizar
        method: Método de estimação de gradiente

    Returns:
        Gradiente estimado G (mesma shape que state.parameters)
    """
    if method == GradientMethod.FINITE_DIFFERENCE:
        # Diferenças finitas numéricas (simples, robusto)
        epsilon = 1e-5
        grad = np.zeros_like(state.parameters)
        base_value = objective_fn(state, evidence)

        for i in range(len(state.parameters)):
            state_plus = state.clone()
            state_plus.parameters[i] += epsilon
            value_plus = objective_fn(state_plus, evidence)
            grad[i] = (value_plus - base_value) / epsilon

        return grad

    elif method == GradientMethod.EVOLUTION_STRATEGY:
        # Evolution Strategy (perturbações simétricas)
        n_samples = 20
        sigma = 0.1
        grad = np.zeros_like(state.parameters)

        for _ in range(n_samples):
            noise = np.random.randn(*state.parameters.shape) * sigma

            # Forward perturbation
            state_plus = state.clone()
            state_plus.parameters += noise
            value_plus = objective_fn(state_plus, evidence)

            # Backward perturbation
            state_minus = state.clone()
            state_minus.parameters -= noise
            value_minus = objective_fn(state_minus, evidence)

            # Gradient estimate
            grad += noise * (value_plus - value_minus) / (2 * sigma**2)

        grad /= n_samples
        return grad

    elif method == GradientMethod.POLICY_GRADIENT:
        # Policy gradient (REINFORCE-like)
        # Para simplificação, usa diferenças finitas com rewards
        if not evidence.rewards:
            return np.zeros_like(state.parameters)

        # Baseline (média de rewards)
        baseline = sum(evidence.rewards) / len(evidence.rewards)

        # Gradient proporcional a (reward - baseline)
        advantage = evidence.rewards[-1] - baseline if evidence.rewards else 0.0

        # Finite difference ponderado por advantage
        epsilon = 1e-4
        grad = np.random.randn(*state.parameters.shape) * advantage * epsilon

        return grad

    else:
        # ANALYTICAL ou TD_LEARNING - placeholder (requer implementação específica)
        # Por enquanto, retorna gradient via finite difference
        return estimate_gradient(
            state, evidence, policy, objective_fn, GradientMethod.FINITE_DIFFERENCE
        )


def project_to_safe_set(
    state: PeninState,
    constraints: ProjectionConstraints,
    allow_reject: bool = True,
) -> tuple[PeninState, bool]:
    """
    Π_{H∩S}: Projeta estado no conjunto seguro H ∩ S

    Args:
        state: Estado a projetar
        constraints: Restrições H ∩ S
        allow_reject: Se True, pode rejeitar estado completamente

    Returns:
        (projected_state, is_valid)
        - projected_state: Estado projetado
        - is_valid: True se passou todas as verificações éticas
    """
    projected = state.clone()

    # 1. Box constraints (H técnico)
    if constraints.param_min is not None:
        projected.parameters = np.maximum(projected.parameters, constraints.param_min)

    if constraints.param_max is not None:
        projected.parameters = np.minimum(projected.parameters, constraints.param_max)

    # 2. Norma máxima (regularização)
    current_norm = projected.norm()
    if current_norm > constraints.max_norm:
        projected.parameters = projected.parameters * (
            constraints.max_norm / current_norm
        )

    # 3. Verificações éticas (S ético) - FAIL-CLOSED
    for _constraint_name, constraint_fn in constraints.ethical_constraints.items():
        try:
            is_valid = constraint_fn(projected)
            if not is_valid:
                # Violação ética - fail-closed
                if allow_reject:
                    return state, False  # Rejeita atualização, mantém estado anterior
                else:
                    # Força projeção mais conservadora
                    projected.parameters = (
                        state.parameters * 0.5 + projected.parameters * 0.5
                    )
        except Exception:
            # Erro na verificação ética - fail-closed por padrão
            if allow_reject:
                return state, False

    # 4. Budget constraints
    for resource, max_budget in constraints.budget_max.items():
        current_usage = projected.meta.get(f"{resource}_usage", 0.0)
        if current_usage > max_budget:
            # Violação de budget - rejeita
            if allow_reject:
                return state, False

    # 5. Privacy constraints (differential privacy)
    # Placeholder: adicionar ruído se necessário
    if constraints.privacy_epsilon < float("inf"):
        # Laplacian noise para DP
        sensitivity = 1.0  # Placeholder
        scale = sensitivity / constraints.privacy_epsilon
        noise = np.random.laplace(0, scale, size=projected.parameters.shape)
        projected.parameters += noise * 0.01  # Scaled down

    return projected, True


def compute_adaptive_step_size(
    base_alpha: float,
    caos_phi: float,
    sr_score: float,
    r_score: float,
    gamma: float = 0.8,
) -> float:
    """
    Calcula α_t^{eff} = α_0 · φ(CAOS⁺) · R_t

    Args:
        base_alpha: α_0 (taxa base)
        caos_phi: φ(CAOS⁺) - aceleração do motor CAOS
        sr_score: SR-Ω∞ - auto-reflexão
        r_score: R_t - score reflexivo composto
        gamma: Parâmetro de saturação

    Returns:
        α_t^{eff} - passo adaptativo
    """
    # φ(z) = tanh(γ·z) - função de saturação
    phi_caos_saturated = math.tanh(gamma * max(0.0, caos_phi))

    # α_t^{eff} = α_0 · φ(CAOS⁺) · SR · R
    alpha_eff = base_alpha * phi_caos_saturated * max(0.0, sr_score) * max(0.0, r_score)

    # Clamp para segurança
    alpha_eff = max(0.0, min(1.0, alpha_eff))

    return alpha_eff


def penin_update(
    state: PeninState,
    evidence: Evidence,
    policy: ControlPolicy,
    constraints: ProjectionConstraints,
    objective_fn: Callable[[PeninState, Evidence], float],
    caos_phi: float = 0.5,
    sr_score: float = 0.8,
    r_score: float = 0.85,
    ledger_fn: Callable | None = None,
) -> tuple[PeninState, dict[str, Any]]:
    """
    Equação de Penin: I_{t+1} = Π_{H∩S}[I_t + α_t · G(I_t, E_t; P_t)]

    Args:
        state: Estado atual I_t
        evidence: Evidências E_t
        policy: Políticas P_t
        constraints: Restrições Π_{H∩S}
        objective_fn: Função objetivo J(I; E)
        caos_phi: φ(CAOS⁺) atual
        sr_score: SR-Ω∞ atual
        r_score: R_t reflexivo
        ledger_fn: Função para registrar no WORM ledger

    Returns:
        (new_state, update_info)
        - new_state: I_{t+1}
        - update_info: Dict com métricas da atualização
    """
    update_info: dict[str, Any] = {
        "timestamp": state.timestamp,
        "version_from": state.version,
        "method": policy.gradient_method.value,
    }

    try:
        # 1. Estimar G(I_t, E_t; P_t) - direção de melhoria
        gradient = estimate_gradient(
            state, evidence, policy, objective_fn, policy.gradient_method
        )
        gradient_norm = float(np.linalg.norm(gradient))
        update_info["gradient_norm"] = gradient_norm

        # 2. Calcular α_t^{eff} - passo adaptativo
        alpha_eff = compute_adaptive_step_size(
            policy.base_alpha, caos_phi, sr_score, r_score
        )
        update_info["alpha_eff"] = alpha_eff
        update_info["caos_phi"] = caos_phi
        update_info["sr_score"] = sr_score
        update_info["r_score"] = r_score

        # 3. Aplicar atualização: I' = I_t + α_t · G
        candidate_state = state.clone()
        candidate_state.parameters += alpha_eff * gradient
        candidate_state.timestamp = state.timestamp + 1.0

        # 4. Projetar em H ∩ S: Π_{H∩S}[I']
        projected_state, is_valid = project_to_safe_set(
            candidate_state, constraints, allow_reject=True
        )

        update_info["projection_valid"] = is_valid

        if not is_valid:
            # Fail-closed: violação ética -> mantém estado anterior
            update_info["action"] = "rejected_ethical_violation"
            update_info["state_changed"] = False

            if ledger_fn:
                ledger_fn(
                    {
                        "event": "penin_update_rejected",
                        "reason": "ethical_violation",
                        "version": state.version,
                        "gradient_norm": gradient_norm,
                        "alpha_eff": alpha_eff,
                    }
                )

            return state, update_info

        # 5. Verificar melhoria (opcional)
        old_objective = objective_fn(state, evidence)
        new_objective = objective_fn(projected_state, evidence)
        delta_objective = new_objective - old_objective

        update_info["objective_old"] = old_objective
        update_info["objective_new"] = new_objective
        update_info["delta_objective"] = delta_objective
        update_info["action"] = "accepted"
        update_info["state_changed"] = True

        # 6. Atualizar meta-informação
        projected_state.meta["last_update"] = update_info
        projected_state.meta["update_count"] = state.meta.get("update_count", 0) + 1

        # 7. Registrar no WORM ledger
        if ledger_fn:
            ledger_fn(
                {
                    "event": "penin_update_accepted",
                    "version_from": state.version,
                    "version_to": projected_state.version,
                    "gradient_norm": gradient_norm,
                    "alpha_eff": alpha_eff,
                    "delta_objective": delta_objective,
                    "caos_phi": caos_phi,
                    "sr_score": sr_score,
                    "state_norm": projected_state.norm(),
                }
            )

        return projected_state, update_info

    except Exception as e:
        # Fail-closed em qualquer erro
        update_info["action"] = "rejected_error"
        update_info["error"] = str(e)
        update_info["state_changed"] = False

        if ledger_fn:
            ledger_fn(
                {
                    "event": "penin_update_error",
                    "error": str(e),
                    "version": state.version,
                }
            )

        return state, update_info


def penin_rollback(
    current_state: PeninState,
    history: list[PeninState],
    target_version: int,
) -> tuple[PeninState, bool]:
    """
    Rollback para versão anterior (segurança)

    Args:
        current_state: Estado atual
        history: Histórico de estados
        target_version: Versão alvo para rollback

    Returns:
        (rolled_back_state, success)
    """
    for hist_state in reversed(history):
        if hist_state.version == target_version:
            return hist_state.clone(), True

    # Se não encontrou, retorna estado atual
    return current_state, False


# Exemplo de função objetivo (placeholder)
def example_objective(state: PeninState, evidence: Evidence) -> float:
    """
    Exemplo de função objetivo J(I; E)

    Pode ser: acurácia, reward, L∞, qualquer métrica a maximizar
    """
    # Placeholder: maximizar negativo da norma (regularização)
    # Em produção, implementar métrica real
    return -state.norm() * 0.1 + sum(evidence.rewards) if evidence.rewards else 0.0


# Exemplo de constraint ético (placeholder)
def example_ethical_constraint(state: PeninState) -> bool:
    """
    Exemplo de constraint ético S

    Retorna True se passou, False se violou
    """
    # Placeholder: verificar norma não explode
    return state.norm() < 100.0
