"""Tests for Ω-META Mutation Generator"""

import pytest
from penin.meta.mutation_generator import (
    MutationGenerator,
    MutationResult,
    MutationType,
    generate_safe_mutations,
)


class TestMutationGenerator:
    """Test mutation generation"""
    
    def test_hyperparameter_mutation_spec(self):
        """Test generating hyperparameter mutation spec"""
        generator = MutationGenerator()
        
        spec = generator.generate_hyperparameter_mutation(
            target_file="test.py",
            parameter_name="kappa",
            current_value=20.0,
            perturbation_pct=0.10,
        )
        
        assert spec.mutation_type == MutationType.PARAMETER_TUNING
        assert spec.changes["parameter"] == "kappa"
        assert spec.changes["old_value"] == 20.0
        assert spec.changes["new_value"] == 22.0  # 20.0 + 10%
    
    def test_apply_hyperparameter_mutation(self):
        """Test applying hyperparameter mutation to code"""
        generator = MutationGenerator()
        
        original_code = """
def compute():
    kappa = 20.0
    return kappa * 2
"""
        
        spec = generator.generate_hyperparameter_mutation(
            target_file="test.py",
            parameter_name="kappa",
            current_value=20.0,
            perturbation_pct=0.10,
        )
        
        result = generator.apply_hyperparameter_mutation(spec, original_code)
        
        assert result.success is True
        assert result.syntax_valid is True
        assert "kappa = 22.0" in result.mutated_code
        assert result.code_hash is not None
    
    def test_mutation_batch_generation(self):
        """Test generating batch of mutations"""
        generator = MutationGenerator()
        
        mutations = generator.generate_mutation_batch(
            strategy="conservative",
            max_mutations=5,
        )
        
        assert len(mutations) <= 5
        assert all(m.risk_level in ["low", "medium"] for m in mutations)
    
    def test_mutation_validation(self):
        """Test mutation safety validation"""
        generator = MutationGenerator()
        
        # Safe mutation
        safe_result = MutationResult(
            mutation_id="test",
            success=True,
            original_code="x = 1",
            mutated_code="x = 2",
            diff="",
            syntax_valid=True,
            imports_valid=True,
            code_hash="abc123",
        )
        
        assert generator.validate_mutation(safe_result) is True
    
    def test_dangerous_mutation_blocked(self):
        """Test that dangerous mutations are blocked"""
        generator = MutationGenerator()
        
        # Dangerous mutation (contains eval)
        dangerous_result = MutationResult(
            mutation_id="test",
            success=True,
            original_code="x = 1",
            mutated_code="x = eval('1+1')",  # DANGEROUS
            diff="",
            syntax_valid=True,
            imports_valid=True,
            code_hash="abc123",
        )
        
        assert generator.validate_mutation(dangerous_result) is False
        assert any("eval" in e for e in dangerous_result.errors)
    
    def test_policy_mutation_generation(self):
        """Test generating policy mutations"""
        generator = MutationGenerator()
        
        spec = generator.generate_policy_mutation(
            threshold_name="beta_min",
            current_value=0.01,
            proposed_value=0.015,
            justification="Increase quality threshold",
        )
        
        assert spec.mutation_type == MutationType.POLICY_UPDATE
        assert spec.target_file == "policies/foundation.yaml"
        assert spec.risk_level == "low"
    
    def test_architecture_mutation_generation(self):
        """Test generating architecture mutations"""
        generator = MutationGenerator()
        
        spec = generator.generate_architecture_mutation(
            target_file="penin/models/model.py",
            modification_type="add_layer",
            details={"layer_type": "dense", "units": 128},
        )
        
        assert spec.mutation_type == MutationType.ARCHITECTURE_MOD
        assert spec.risk_level == "medium"
        assert spec.requires_approval is True
    
    def test_convenience_function(self):
        """Test convenience function for safe mutations"""
        mutations = generate_safe_mutations(strategy="conservative", max_count=3)
        
        assert len(mutations) <= 3
        assert all(m.risk_level == "low" for m in mutations)
