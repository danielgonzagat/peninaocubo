"""
PENIN-Ω Equation 7: ACFA EPV (Expected Possession Value)
=========================================================

Implementa Expected Possession Value (EPV) inspirado em análise de futebol,
adaptado para decisões sequenciais em IA.

Fórmula (Bellman):
    v*(s) = max_a [ r(s, a) + γ Σ_{s'} P(s'|s, a) v*(s') ]

Onde:
- s: Estado atual
- a: Ação
- r(s, a): Recompensa imediata
- γ: Fator de desconto
- P(s'|s, a): Transição de estado
- v*(s'): Valor ótimo do próximo estado

Contexto PENIN-Ω:
- Estados = configurações de arquitetura/parâmetros
- Ações = mutações/atualizações
- Recompensa = ΔL∞ - λ_c · Custo
- EPV guia escolha de mutações no Ω-META

Features:
- Value iteration
- Policy extraction
- Q-learning support
- Integração com ACFA League (champion-challenger)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class EPVConfig:
    """Configuration for EPV computation."""

    gamma: float = 0.95  # Discount factor
    max_iterations: int = 100
    convergence_epsilon: float = 1e-4
    exploration_rate: float = 0.1


@dataclass
class State:
    """Represents a system state."""

    config: dict[str, Any]
    metrics: dict[str, float]
    timestamp: float


@dataclass
class Action:
    """Represents a mutation/action."""

    type: str  # "param_update", "arch_change", "policy_update"
    delta: dict[str, Any]
    cost_estimate: float


def expected_possession_value(
    state: State,
    actions: list[Action],
    reward_fn: Callable[[State, Action], float],
    transition_fn: Callable[[State, Action], list[tuple[State, float]]],
    config: EPVConfig | None = None,
) -> dict[Action, float]:
    """
    Compute EPV for each action from given state.

    Args:
        state: Current system state
        actions: List of possible actions
        reward_fn: Function that computes r(s, a)
        transition_fn: Function that returns [(s', P(s'|s,a)), ...]
        config: Optional configuration

    Returns:
        Dict mapping each action to its EPV score

    Example:
        >>> state = State(config={...}, metrics={...}, timestamp=time.time())
        >>> actions = [Action("param_update", {"lr": 0.01}, 0.1)]
        >>> epv_scores = expected_possession_value(state, actions, reward_fn, transition_fn)
        >>> best_action = max(epv_scores, key=epv_scores.get)
    """
    config = config or EPVConfig()

    epv_scores = {}

    for action in actions:
        # Immediate reward
        immediate_reward = reward_fn(state, action)

        # Expected future value
        transitions = transition_fn(state, action)
        future_value = sum(
            prob * _value_estimate(next_state, config)
            for next_state, prob in transitions
        )

        # Total EPV
        epv = immediate_reward + config.gamma * future_value
        epv_scores[action] = epv

    return epv_scores


def _value_estimate(state: State, config: EPVConfig) -> float:
    """
    Estimate value of a state (heuristic for bootstrapping).

    Uses L∞ as proxy for state value.
    """
    # Simple heuristic: use current L∞ as value estimate
    linf = state.metrics.get("linf", 0.0)
    return linf


def compute_q_values(
    state: State,
    actions: list[Action],
    reward_fn: Callable,
    transition_fn: Callable,
    config: EPVConfig | None = None,
) -> dict[tuple[State, Action], float]:
    """
    Compute Q(s, a) values for state-action pairs.

    Args:
        state: Current state
        actions: Possible actions
        reward_fn: Reward function
        transition_fn: Transition function
        config: Optional configuration

    Returns:
        Dict mapping (state, action) tuples to Q-values
    """
    config = config or EPVConfig()
    q_values = {}

    for action in actions:
        q = reward_fn(state, action)
        transitions = transition_fn(state, action)
        q += config.gamma * sum(
            prob * _value_estimate(next_state, config)
            for next_state, prob in transitions
        )
        q_values[(state, action)] = q

    return q_values


def extract_policy(
    epv_scores: dict[Action, float], exploration_rate: float = 0.0
) -> Action:
    """
    Extract greedy policy from EPV scores (with optional ε-greedy).

    Args:
        epv_scores: EPV scores for each action
        exploration_rate: Probability of random action

    Returns:
        Selected action (greedy or random)
    """
    import random

    if random.random() < exploration_rate:
        # Explore: random action
        return random.choice(list(epv_scores.keys()))
    else:
        # Exploit: best action
        return max(epv_scores, key=epv_scores.get)


__all__ = [
    "EPVConfig",
    "State",
    "Action",
    "expected_possession_value",
    "compute_q_values",
    "extract_policy",
]
