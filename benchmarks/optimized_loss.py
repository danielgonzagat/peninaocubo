"""
Optimized Loss Functions for Benchmarking
==========================================

Demonstrates how to write efficient loss functions for the Master Equation cycle.
"""

import numpy as np


class OptimizedQuadraticLoss:
    """Optimized quadratic loss function with minimal overhead."""

    def __init__(self, regularization: float = 0.01):
        self.reg = regularization
        # Pre-compute regularization factor
        self.reg_factor = regularization

    def __call__(self, state: np.ndarray, evidence=None, policies=None) -> float:
        """
        Compute quadratic loss with L2 regularization.

        Optimizations:
        - Uses np.dot for faster computation
        - Pre-computed regularization factor
        - Avoids np.linalg.norm overhead
        """
        # Quadratic term: sum(state^2) = state.dot(state)
        quadratic = np.dot(state, state)

        # L2 regularization: ||state|| = sqrt(state.dot(state))
        # We already have state.dot(state), so just take sqrt and multiply
        regularization = self.reg_factor * np.sqrt(quadratic)

        return quadratic + regularization


class CachedLossFunction:
    """Loss function with caching for gradient estimation."""

    def __init__(self, base_loss_fn):
        self.base_loss_fn = base_loss_fn
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def __call__(self, state: np.ndarray, evidence=None, policies=None) -> float:
        """Evaluate loss with caching."""
        # Use state hash as cache key (note: this is approximate)
        key = hash(state.tobytes())

        if key in self.cache:
            self.hits += 1
            return self.cache[key]

        self.misses += 1
        result = self.base_loss_fn(state, evidence, policies)
        self.cache[key] = result
        return result

    def clear_cache(self):
        """Clear cache and reset statistics."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
        }


def create_optimized_loss_fn():
    """Create an optimized loss function for testing."""
    loss = OptimizedQuadraticLoss(regularization=0.01)
    return loss


def create_cached_loss_fn(base_loss_fn):
    """Wrap a loss function with caching."""
    return CachedLossFunction(base_loss_fn)
