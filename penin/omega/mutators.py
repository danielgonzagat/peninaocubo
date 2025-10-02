"""
PENIN-Ω Mutators Module
=======================

Implements mutation strategies for model parameters, prompts, and configurations.
Uses BLAKE2b for configuration hashing (v2.0).
"""

import random
from dataclasses import dataclass
from typing import Any

from penin.ledger.hash_utils import hash_json


@dataclass
class MutationConfig:
    """Configuration for mutation strategies"""

    seed: int = 42
    max_variants: int = 8
    temperature_range: tuple[float, float] = (0.1, 1.5)
    top_p_range: tuple[float, float] = (0.5, 1.0)
    max_tokens_options: list[int] = None

    def __post_init__(self):
        if self.max_tokens_options is None:
            self.max_tokens_options = [100, 200, 500, 1000, 2000]


@dataclass
class MutationResult:
    """Result of a mutation operation"""

    variant_id: str
    original_config: dict[str, Any]
    mutated_config: dict[str, Any]
    mutation_type: str
    config_hash: str
    seed_used: int


class ParameterMutator:
    """Mutates model parameters for exploration"""

    def __init__(self, config: MutationConfig = None):
        self.config = config or MutationConfig()
        self.rng = random.Random(self.config.seed)

    def mutate_parameters(
        self, base_config: dict[str, Any], n_variants: int = None
    ) -> list[MutationResult]:
        """Generate parameter variants from base configuration"""
        n_variants = n_variants or self.config.max_variants
        variants = []

        for i in range(n_variants):
            variant_seed = self.config.seed + i
            variant_rng = random.Random(variant_seed)

            mutated = base_config.copy()

            # Mutate temperature
            if "temperature" in base_config:
                mutated["temperature"] = variant_rng.uniform(
                    *self.config.temperature_range
                )

            # Mutate top_p
            if "top_p" in base_config:
                mutated["top_p"] = variant_rng.uniform(*self.config.top_p_range)

            # Mutate max_tokens
            if "max_tokens" in base_config:
                mutated["max_tokens"] = variant_rng.choice(
                    self.config.max_tokens_options
                )

            # Create result
            variant_id = f"param_variant_{i:03d}"
            config_hash = self._hash_config(mutated)

            result = MutationResult(
                variant_id=variant_id,
                original_config=base_config,
                mutated_config=mutated,
                mutation_type="parameter_sweep",
                config_hash=config_hash,
                seed_used=variant_seed,
            )

            variants.append(result)

        return variants

    def _hash_config(self, config: dict[str, Any]) -> str:
        """Create deterministic hash of configuration using BLAKE2b"""
        return hash_json(config)


def generate_parameter_variants(
    base_config: dict[str, Any], n_variants: int = 8, seed: int = 42
) -> list[dict[str, Any]]:
    """Quick function to generate parameter variants"""
    config = MutationConfig(seed=seed, max_variants=n_variants)
    mutator = ParameterMutator(config)
    results = mutator.mutate_parameters(base_config, n_variants)
    return [r.mutated_config for r in results]
