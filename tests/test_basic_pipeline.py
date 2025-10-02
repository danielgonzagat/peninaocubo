"""
Test Basic Evolution Pipeline
==============================

Test the first working E2E pipeline!
"""

import pytest


class TestBasicPipeline:
    """Test basic evolution pipeline"""

    def test_pipeline_instantiates(self):
        """Test pipeline can be created"""
        from penin.pipelines.basic_pipeline import BasicEvolutionPipeline
        
        pipeline = BasicEvolutionPipeline(budget_usd=10.0, seed=42)
        
        assert pipeline is not None
        assert pipeline.state.current_linf > 0

    def test_pipeline_generates_mutation(self):
        """Test pipeline generates mutations"""
        from penin.pipelines.basic_pipeline import BasicEvolutionPipeline
        
        pipeline = BasicEvolutionPipeline(seed=42)
        mutation = pipeline.generate_mutation(cycle_num=1)
        
        assert mutation is not None
        assert mutation.id == "mut_0001"
        assert mutation.type in ['caos_component', 'linf_weight', 'kappa', 'lambda_cost']

    def test_pipeline_tests_mutation(self):
        """Test pipeline tests mutations"""
        from penin.pipelines.basic_pipeline import BasicEvolutionPipeline
        
        pipeline = BasicEvolutionPipeline(seed=42)
        mutation = pipeline.generate_mutation(1)
        test_results = pipeline.test_mutation(mutation)
        
        assert test_results is not None
        assert hasattr(test_results, 'caos')
        assert hasattr(test_results, 'linf')
        assert hasattr(test_results, 'delta_linf')

    def test_pipeline_guard_decides(self):
        """Test Σ-Guard makes decisions"""
        from penin.pipelines.basic_pipeline import BasicEvolutionPipeline
        
        pipeline = BasicEvolutionPipeline(seed=42)
        mutation = pipeline.generate_mutation(1)
        test_results = pipeline.test_mutation(mutation)
        decision = pipeline.decide(test_results)
        
        assert decision.verdict in ["PASS", "FAIL"]
        assert isinstance(decision.gates, dict)

    def test_pipeline_full_cycle(self):
        """Test one complete pipeline cycle"""
        from penin.pipelines.basic_pipeline import BasicEvolutionPipeline
        
        pipeline = BasicEvolutionPipeline(seed=42)
        
        initial_linf = pipeline.state.current_linf
        
        result = pipeline.run_cycle(1)
        
        # Should complete cycle
        assert result is not None
        assert 'decision' in result
        
        # Should have recorded in ledger
        assert len(pipeline.ledger_entries) == 1

    def test_pipeline_multiple_cycles(self):
        """Test running multiple cycles"""
        from penin.pipelines.basic_pipeline import BasicEvolutionPipeline
        
        pipeline = BasicEvolutionPipeline(seed=42)
        
        summary = pipeline.run_n_cycles(5)
        
        # Should have run 5 cycles
        assert summary['cycles'] == 5
        
        # Should have promotions or rejections
        assert summary['promoted'] + summary['rejected'] == 5
        
        # Should have ledger entries
        assert len(pipeline.ledger_entries) == 5

    def test_mutation_generator_variability(self):
        """Test mutation generator produces different mutations"""
        from penin.pipelines.basic_pipeline import SimpleMutationGenerator
        
        gen = SimpleMutationGenerator(seed=42)
        
        mutations = [gen.generate(f"test_{i}") for i in range(10)]
        
        # Should generate various types
        types = set(m.type for m in mutations)
        assert len(types) >= 2  # At least 2 different types

    def test_guard_passes_good_mutation(self):
        """Test guard passes good mutations"""
        from penin.pipelines.basic_pipeline import SimpleGuard, TestResults, PipelineState
        
        guard = SimpleGuard()
        state = PipelineState()
        
        # Good mutation (improvement)
        test_results = TestResults(
            caos=2.0,
            linf=0.85,
            delta_linf=0.05,  # 5% improvement
            cost=0.01,
        )
        
        decision = guard.evaluate(test_results, state)
        
        assert decision.verdict == "PASS"

    def test_guard_rejects_bad_mutation(self):
        """Test guard rejects bad mutations"""
        from penin.pipelines.basic_pipeline import SimpleGuard, TestResults, PipelineState
        
        guard = SimpleGuard()
        state = PipelineState()
        
        # Bad mutation (degradation)
        test_results = TestResults(
            caos=0.5,  # Too low
            linf=0.3,  # Too low
            delta_linf=-0.05,  # Negative
            cost=0.01,
        )
        
        decision = guard.evaluate(test_results, state)
        
        assert decision.verdict == "FAIL"
        assert len(decision.failed_gates) > 0
