"""
Tests for CMA-ES Local Training
=================================

Tests for Phase 4: The Forge of Hephaestus - CMA-ES optimization.
"""

from __future__ import annotations

import numpy as np
import pytest

from penin.core import NumericVectorArtifact, OmegaMetaOrchestrator


class TestCMAESLocalTraining:
    """Test CMA-ES local training functionality."""

    def test_initiate_local_training_basic(self):
        """Test basic CMA-ES training with simple quadratic function."""
        orchestrator = OmegaMetaOrchestrator()

        # Add some initial artifacts to knowledge base
        # Target: minimize sum of squares (optimum at [0, 0, 0])
        orchestrator.add_knowledge(
            "artifact1", NumericVectorArtifact(vector=[1.0, 1.0, 1.0])
        )
        orchestrator.add_knowledge(
            "artifact2", NumericVectorArtifact(vector=[2.0, 2.0, 2.0])
        )
        orchestrator.add_knowledge(
            "artifact3", NumericVectorArtifact(vector=[0.5, 0.5, 0.5])
        )

        # Define evaluation function: sum of squares (lower is better)
        def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
            return sum(x**2 for x in artifact.vector)

        # Run optimization (short run for testing)
        result = orchestrator._initiate_local_training(
            evaluate_artifact, max_generations=10, sigma0=0.5
        )

        # Verify result is a NumericVectorArtifact
        assert isinstance(result, NumericVectorArtifact)
        assert len(result.vector) == 3

        # Verify result is better than initial best
        initial_best_score = evaluate_artifact(
            orchestrator.knowledge_base["artifact3"]
        )
        result_score = evaluate_artifact(result)
        assert result_score < initial_best_score

        # Verify metadata
        assert result.metadata["method"] == "cma-es"
        assert "generations" in result.metadata
        assert result.metadata["starting_point"] == "artifact3"

    def test_initiate_local_training_converges_to_optimum(self):
        """Test that CMA-ES converges close to known optimum."""
        orchestrator = OmegaMetaOrchestrator()

        # Start from a point far from optimum
        orchestrator.add_knowledge(
            "start", NumericVectorArtifact(vector=[5.0, 5.0, 5.0, 5.0, 5.0])
        )

        # Sphere function: optimum at origin
        def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
            return sum(x**2 for x in artifact.vector)

        # Run longer optimization
        result = orchestrator._initiate_local_training(
            evaluate_artifact, max_generations=50, sigma0=1.0
        )

        # Check convergence
        final_score = evaluate_artifact(result)
        assert final_score < 1.0  # Should be close to 0

        # Check that result vector is close to origin
        for x in result.vector:
            assert abs(x) < 1.0  # All dimensions should be close to 0

    def test_initiate_local_training_empty_knowledge_base(self):
        """Test that training fails gracefully with empty knowledge base."""
        orchestrator = OmegaMetaOrchestrator()

        def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
            return sum(x**2 for x in artifact.vector)

        with pytest.raises(ValueError, match="Knowledge base is empty"):
            orchestrator._initiate_local_training(evaluate_artifact)

    def test_initiate_local_training_with_custom_popsize(self):
        """Test CMA-ES with custom population size."""
        orchestrator = OmegaMetaOrchestrator()
        orchestrator.add_knowledge("start", NumericVectorArtifact(vector=[1.0, 1.0]))

        def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
            return sum(x**2 for x in artifact.vector)

        result = orchestrator._initiate_local_training(
            evaluate_artifact, max_generations=5, sigma0=0.5, popsize=8
        )

        assert isinstance(result, NumericVectorArtifact)
        assert result.metadata["method"] == "cma-es"

    def test_initiate_local_training_rosenbrock(self):
        """Test CMA-ES on Rosenbrock function (harder optimization)."""
        orchestrator = OmegaMetaOrchestrator()

        # Rosenbrock optimum is at [1, 1]
        orchestrator.add_knowledge("start", NumericVectorArtifact(vector=[0.0, 0.0]))

        def rosenbrock(artifact: NumericVectorArtifact) -> float:
            """Rosenbrock function: f(x,y) = (1-x)^2 + 100*(y-x^2)^2"""
            x, y = artifact.vector
            return (1 - x) ** 2 + 100 * (y - x**2) ** 2

        result = orchestrator._initiate_local_training(
            rosenbrock, max_generations=100, sigma0=0.5
        )

        # Should improve from initial position
        initial_score = rosenbrock(orchestrator.knowledge_base["start"])
        final_score = rosenbrock(result)
        assert final_score < initial_score

    def test_initiate_local_training_ackley(self):
        """Test CMA-ES on Ackley function (multi-modal)."""
        orchestrator = OmegaMetaOrchestrator()

        # Start from random point
        orchestrator.add_knowledge(
            "start", NumericVectorArtifact(vector=[3.0, 3.0, 3.0])
        )

        def ackley(artifact: NumericVectorArtifact) -> float:
            """Ackley function: global minimum at origin"""
            x = np.array(artifact.vector)
            n = len(x)
            sum1 = np.sum(x**2)
            sum2 = np.sum(np.cos(2 * np.pi * x))
            return (
                -20 * np.exp(-0.2 * np.sqrt(sum1 / n))
                - np.exp(sum2 / n)
                + 20
                + np.e
            )

        result = orchestrator._initiate_local_training(
            ackley, max_generations=100, sigma0=1.0
        )

        # Should significantly improve
        initial_score = ackley(orchestrator.knowledge_base["start"])
        final_score = ackley(result)
        assert final_score < initial_score
        assert final_score < 5.0  # Should get reasonably close to optimum (0)

    def test_initiate_local_training_selects_best_start(self):
        """Test that CMA-ES starts from the best artifact in knowledge base."""
        orchestrator = OmegaMetaOrchestrator()

        # Add artifacts with different scores
        orchestrator.add_knowledge("bad", NumericVectorArtifact(vector=[10.0, 10.0]))
        orchestrator.add_knowledge(
            "good", NumericVectorArtifact(vector=[0.1, 0.1])
        )  # Best
        orchestrator.add_knowledge("ok", NumericVectorArtifact(vector=[1.0, 1.0]))

        def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
            return sum(x**2 for x in artifact.vector)

        result = orchestrator._initiate_local_training(
            evaluate_artifact, max_generations=5, sigma0=0.5
        )

        # Should start from "good" artifact
        assert result.metadata["starting_point"] == "good"

    def test_initiate_local_training_metadata_complete(self):
        """Test that result metadata is complete and accurate."""
        orchestrator = OmegaMetaOrchestrator()
        orchestrator.add_knowledge("start", NumericVectorArtifact(vector=[1.0, 1.0]))

        def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
            return sum(x**2 for x in artifact.vector)

        max_gens = 20
        result = orchestrator._initiate_local_training(
            evaluate_artifact, max_generations=max_gens, sigma0=0.5
        )

        # Check all metadata fields
        assert "method" in result.metadata
        assert result.metadata["method"] == "cma-es"
        assert "generations" in result.metadata
        assert result.metadata["generations"] <= max_gens
        assert "final_sigma" in result.metadata
        assert result.metadata["final_sigma"] > 0
        assert "starting_point" in result.metadata
        assert result.metadata["starting_point"] == "start"

    def test_initiate_local_training_different_dimensions(self):
        """Test CMA-ES with different vector dimensions."""
        for dim in [1, 2, 5, 10]:
            orchestrator = OmegaMetaOrchestrator()
            orchestrator.add_knowledge(
                "start", NumericVectorArtifact(vector=[1.0] * dim)
            )

            def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
                return sum(x**2 for x in artifact.vector)

            result = orchestrator._initiate_local_training(
                evaluate_artifact, max_generations=10, sigma0=0.5
            )

            assert len(result.vector) == dim

    def test_initiate_local_training_integration(self):
        """Integration test: full workflow with knowledge base updates."""
        orchestrator = OmegaMetaOrchestrator()

        # Initial population (all non-optimal)
        for i in range(1, 4):
            orchestrator.add_knowledge(
                f"init_{i}", NumericVectorArtifact(vector=[float(i), float(i)])
            )

        def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
            return sum(x**2 for x in artifact.vector)

        # Run optimization
        optimized = orchestrator._initiate_local_training(
            evaluate_artifact, max_generations=20, sigma0=0.5
        )

        # Add optimized artifact to knowledge base
        orchestrator.add_knowledge("optimized", optimized)

        # Verify it's now the best in knowledge base
        scores = {
            key: evaluate_artifact(artifact)
            for key, artifact in orchestrator.knowledge_base.items()
        }
        assert scores["optimized"] == min(scores.values())


class TestCMAESEdgeCases:
    """Test edge cases and error handling."""

    def test_evaluation_function_with_nan(self):
        """Test handling of NaN from evaluation function."""
        orchestrator = OmegaMetaOrchestrator()
        orchestrator.add_knowledge("start", NumericVectorArtifact(vector=[1.0, 1.0]))

        def bad_evaluate(artifact: NumericVectorArtifact) -> float:
            # Return NaN for some inputs
            if sum(artifact.vector) < 0:
                return float("nan")
            return sum(x**2 for x in artifact.vector)

        # Should handle gracefully (CMA-ES has built-in NaN handling)
        result = orchestrator._initiate_local_training(
            bad_evaluate, max_generations=5, sigma0=0.5
        )
        assert isinstance(result, NumericVectorArtifact)

    def test_very_short_optimization(self):
        """Test with very short optimization (1 generation)."""
        orchestrator = OmegaMetaOrchestrator()
        orchestrator.add_knowledge("start", NumericVectorArtifact(vector=[1.0, 1.0]))

        def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
            return sum(x**2 for x in artifact.vector)

        result = orchestrator._initiate_local_training(
            evaluate_artifact, max_generations=1, sigma0=0.5
        )

        assert isinstance(result, NumericVectorArtifact)
        assert result.metadata["generations"] >= 1

    def test_different_sigma_values(self):
        """Test with different initial sigma values."""
        orchestrator = OmegaMetaOrchestrator()

        for sigma in [0.1, 0.5, 1.0, 2.0]:
            orchestrator.knowledge_base = {}  # Reset
            orchestrator.add_knowledge(
                "start", NumericVectorArtifact(vector=[1.0, 1.0])
            )

            def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
                return sum(x**2 for x in artifact.vector)

            result = orchestrator._initiate_local_training(
                evaluate_artifact, max_generations=10, sigma0=sigma
            )

            assert isinstance(result, NumericVectorArtifact)
            # Different sigmas should still produce valid results
            score = evaluate_artifact(result)
            assert score < 2.0  # Should improve from initial [1,1]
