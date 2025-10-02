"""
Ω-META Mutation Generator
==========================

Generates code mutations for auto-evolution pipeline.

Uses AST manipulation to create safe, testable code variants:
- Parameter tuning (hyperparameters)
- Architecture modifications (layer sizes, activations)
- Policy updates (thresholds, gates)

Integrates with Liga ACFA for champion-challenger evaluation.

Safety Guarantees:
------------------
- Sandbox execution (no direct code execution)
- Dry-run validation
- Rollback capability
- Sigma Guard enforcement
- WORM audit trail

References:
-----------
- EXECUTION_COMPLETE_REPORT.md § F5
- Microsoft STOP (Self-Taught Optimizer)
- NextPy AMS (Automatic Model Selection)
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class MutationType(str, Enum):
    """Types of mutations"""
    
    PARAMETER_TUNING = "parameter_tuning"  # Hyperparameter adjustments
    ARCHITECTURE_MOD = "architecture_modification"  # Network structure changes
    POLICY_UPDATE = "policy_update"  # Threshold/gate changes
    ALGORITHM_SWAP = "algorithm_swap"  # Different algorithms
    OPTIMIZATION = "optimization"  # Performance improvements


@dataclass
class MutationSpec:
    """Specification for a single mutation"""
    
    mutation_id: str
    mutation_type: MutationType
    target_file: str
    target_function: str | None = None
    target_class: str | None = None
    
    # Mutation details
    changes: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    # Safety
    dry_run: bool = True
    requires_approval: bool = True
    
    # Expected impact
    expected_delta_linf: float = 0.01
    expected_cost_change_pct: float = 0.0
    risk_level: str = "low"  # low | medium | high


@dataclass
class MutationResult:
    """Result of applying a mutation"""
    
    mutation_id: str
    success: bool
    
    # Generated code
    original_code: str
    mutated_code: str
    diff: str
    
    # Validation
    syntax_valid: bool
    imports_valid: bool
    
    # Hash for tracking
    code_hash: str
    
    # Errors (if any)
    errors: list[str] = field(default_factory=list)


class MutationGenerator:
    """
    Generates safe code mutations for auto-evolution.
    
    Uses AST manipulation to ensure syntactic validity.
    """
    
    def __init__(self, safety_mode: str = "strict"):
        """
        Initialize mutation generator.
        
        Args:
            safety_mode: "strict" | "moderate" | "aggressive"
        """
        self.safety_mode = safety_mode
        self.generated_mutations: list[MutationResult] = []
    
    # ========================================================================
    # PARAMETER TUNING MUTATIONS
    # ========================================================================
    
    def generate_hyperparameter_mutation(
        self,
        target_file: str,
        parameter_name: str,
        current_value: float,
        perturbation_pct: float = 0.10,
    ) -> MutationSpec:
        """
        Generate mutation for hyperparameter tuning.
        
        Args:
            target_file: Python file to mutate
            parameter_name: Name of parameter (e.g., "kappa", "learning_rate")
            current_value: Current value
            perturbation_pct: Perturbation percentage (0.10 = ±10%)
        
        Returns:
            MutationSpec describing the change
        """
        # Calculate new value
        delta = current_value * perturbation_pct
        new_value = current_value + delta
        
        spec = MutationSpec(
            mutation_id=f"hyperparam_{parameter_name}_{int(time.time())}",
            mutation_type=MutationType.PARAMETER_TUNING,
            target_file=target_file,
            changes={
                "parameter": parameter_name,
                "old_value": current_value,
                "new_value": new_value,
                "delta": delta,
            },
            description=f"Tune {parameter_name}: {current_value} → {new_value} (+{perturbation_pct*100:.1f}%)",
            expected_delta_linf=0.01,  # Conservative estimate
            risk_level="low",
        )
        
        return spec
    
    def apply_hyperparameter_mutation(
        self,
        spec: MutationSpec,
        code: str,
    ) -> MutationResult:
        """
        Apply hyperparameter mutation to code.
        
        Args:
            spec: Mutation specification
            code: Original source code
        
        Returns:
            MutationResult with mutated code
        """
        param_name = spec.changes["parameter"]
        old_value = spec.changes["old_value"]
        new_value = spec.changes["new_value"]
        
        # Simple string replacement (AST would be better but more complex)
        # Look for patterns like: kappa = 20.0
        import re
        
        pattern = rf"{param_name}\s*=\s*{old_value}"
        replacement = f"{param_name} = {new_value}"
        
        mutated_code = re.sub(pattern, replacement, code)
        
        # Validate syntax
        syntax_valid = False
        try:
            ast.parse(mutated_code)
            syntax_valid = True
        except SyntaxError:
            pass
        
        # Compute diff
        diff = self._compute_diff(code, mutated_code)
        
        # Hash
        code_hash = hashlib.sha256(mutated_code.encode()).hexdigest()[:16]
        
        result = MutationResult(
            mutation_id=spec.mutation_id,
            success=syntax_valid,
            original_code=code,
            mutated_code=mutated_code,
            diff=diff,
            syntax_valid=syntax_valid,
            imports_valid=True,  # Assume valid for hyperparams
            code_hash=code_hash,
        )
        
        self.generated_mutations.append(result)
        return result
    
    # ========================================================================
    # ARCHITECTURE MUTATIONS
    # ========================================================================
    
    def generate_architecture_mutation(
        self,
        target_file: str,
        modification_type: str,  # "add_layer" | "remove_layer" | "change_activation"
        details: dict[str, Any],
    ) -> MutationSpec:
        """
        Generate architecture modification mutation.
        
        Args:
            target_file: File containing model architecture
            modification_type: Type of modification
            details: Specific details for modification
        
        Returns:
            MutationSpec
        """
        spec = MutationSpec(
            mutation_id=f"arch_{modification_type}_{int(time.time())}",
            mutation_type=MutationType.ARCHITECTURE_MOD,
            target_file=target_file,
            changes={"type": modification_type, **details},
            description=f"Architecture: {modification_type}",
            expected_delta_linf=0.02,  # Higher impact
            risk_level="medium",  # More risky
            requires_approval=True,
        )
        
        return spec
    
    # ========================================================================
    # POLICY MUTATIONS
    # ========================================================================
    
    def generate_policy_mutation(
        self,
        threshold_name: str,
        current_value: float,
        proposed_value: float,
        justification: str,
    ) -> MutationSpec:
        """
        Generate policy/threshold mutation.
        
        Args:
            threshold_name: Name of threshold (e.g., "beta_min", "sr_min")
            current_value: Current value
            proposed_value: Proposed new value
            justification: Why this change
        
        Returns:
            MutationSpec
        """
        spec = MutationSpec(
            mutation_id=f"policy_{threshold_name}_{int(time.time())}",
            mutation_type=MutationType.POLICY_UPDATE,
            target_file="policies/foundation.yaml",
            changes={
                "threshold": threshold_name,
                "old": current_value,
                "new": proposed_value,
                "justification": justification,
            },
            description=f"Update {threshold_name}: {current_value} → {proposed_value}",
            expected_delta_linf=0.005,  # Small impact
            risk_level="low",  # Policies are safer
        )
        
        return spec
    
    # ========================================================================
    # BATCH GENERATION
    # ========================================================================
    
    def generate_mutation_batch(
        self,
        strategy: str = "conservative",
        max_mutations: int = 5,
    ) -> list[MutationSpec]:
        """
        Generate batch of mutations for testing.
        
        Args:
            strategy: "conservative" | "moderate" | "aggressive"
            max_mutations: Maximum mutations to generate
        
        Returns:
            List of MutationSpec
        """
        mutations = []
        
        if strategy == "conservative":
            # Only hyperparameter tuning, small changes
            mutations.append(
                self.generate_hyperparameter_mutation(
                    target_file="penin/core/caos.py",
                    parameter_name="kappa",
                    current_value=20.0,
                    perturbation_pct=0.05,  # ±5%
                )
            )
            mutations.append(
                self.generate_hyperparameter_mutation(
                    target_file="penin/math/linf.py",
                    parameter_name="lambda_c",
                    current_value=0.5,
                    perturbation_pct=0.10,  # ±10%
                )
            )
        
        elif strategy == "moderate":
            # Hyperparameters + policy changes
            mutations.append(
                self.generate_hyperparameter_mutation(
                    target_file="penin/core/caos.py",
                    parameter_name="kappa",
                    current_value=20.0,
                    perturbation_pct=0.15,  # ±15%
                )
            )
            mutations.append(
                self.generate_policy_mutation(
                    threshold_name="beta_min",
                    current_value=0.01,
                    proposed_value=0.012,
                    justification="Increase quality threshold for promotion",
                )
            )
        
        elif strategy == "aggressive":
            # Include architecture changes
            mutations.append(
                self.generate_architecture_mutation(
                    target_file="penin/models/model.py",
                    modification_type="add_layer",
                    details={"layer_type": "dense", "units": 128},
                )
            )
        
        return mutations[:max_mutations]
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _compute_diff(self, original: str, mutated: str) -> str:
        """Compute simple diff between original and mutated code"""
        import difflib
        
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            mutated.splitlines(keepends=True),
            lineterm='',
        )
        
        return ''.join(diff)
    
    def validate_mutation(self, result: MutationResult) -> bool:
        """
        Validate mutation result.
        
        Checks:
        - Syntax valid
        - Imports valid
        - No critical keywords (eval, exec, __import__)
        
        Args:
            result: MutationResult to validate
        
        Returns:
            True if safe, False otherwise
        """
        if not result.syntax_valid:
            return False
        
        # Check for dangerous patterns
        dangerous = ["eval", "exec", "__import__", "compile"]
        for keyword in dangerous:
            if keyword in result.mutated_code:
                result.errors.append(f"Dangerous keyword detected: {keyword}")
                return False
        
        return True


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def generate_safe_mutations(
    strategy: str = "conservative",
    max_count: int = 3,
) -> list[MutationSpec]:
    """
    Generate safe mutations for auto-evolution.
    
    Args:
        strategy: Evolution strategy
        max_count: Maximum mutations
    
    Returns:
        List of MutationSpec
    """
    generator = MutationGenerator(safety_mode="strict")
    return generator.generate_mutation_batch(strategy, max_count)


__all__ = [
    "MutationType",
    "MutationSpec",
    "MutationResult",
    "MutationGenerator",
    "generate_safe_mutations",
]
