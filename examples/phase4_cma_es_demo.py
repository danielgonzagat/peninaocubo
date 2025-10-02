#!/usr/bin/env python3
"""
Phase 4 Demo: The Forge of Hephaestus
======================================

Demonstrates CMA-ES local optimization for NumericVectorArtifacts.

This example shows how to:
1. Initialize an orchestrator with a knowledge base
2. Define an evaluation function for artifacts
3. Run CMA-ES optimization to find better solutions
4. Integrate optimized artifacts back into the knowledge base

Example uses the Ackley function - a challenging multi-modal optimization
benchmark with many local minima and a global minimum at the origin.
"""

import numpy as np

from penin.core import NumericVectorArtifact, OmegaMetaOrchestrator


def ackley_function(x: np.ndarray) -> float:
    """
    Ackley function - a challenging optimization benchmark.

    Global minimum: f(0, 0, ..., 0) = 0
    Search space: typically [-5, 5]^n
    
    Features:
    - Multi-modal (many local minima)
    - Nearly flat outer region
    - Sharp global minimum at origin
    """
    n = len(x)
    sum1 = np.sum(x**2)
    sum2 = np.sum(np.cos(2 * np.pi * x))
    return -20 * np.exp(-0.2 * np.sqrt(sum1 / n)) - np.exp(sum2 / n) + 20 + np.e


def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
    """
    Evaluate a NumericVectorArtifact using the Ackley function.
    
    Lower scores are better (CMA-ES minimizes).
    """
    return ackley_function(np.array(artifact.vector))


def main():
    print("=" * 70)
    print("Phase 4: The Forge of Hephaestus - CMA-ES Optimization Demo")
    print("=" * 70)
    print()

    # Step 1: Initialize orchestrator
    print("Step 1: Initialize orchestrator with initial knowledge base")
    print("-" * 70)
    orchestrator = OmegaMetaOrchestrator()

    # Create initial population with random solutions
    np.random.seed(42)
    dimension = 5
    
    print(f"\nCreating {3} initial artifacts in {dimension}D space...")
    for i in range(3):
        vector = np.random.uniform(-5, 5, size=dimension).tolist()
        artifact = NumericVectorArtifact(
            vector=vector,
            metadata={"source": "random_init", "id": i}
        )
        orchestrator.add_knowledge(f"init_{i}", artifact)
        score = evaluate_artifact(artifact)
        print(f"  init_{i}: score = {score:.4f}")

    print("\nInitial knowledge base statistics:")
    stats = orchestrator.get_statistics()
    print(f"  Knowledge base size: {stats['knowledge_base_size']}")

    # Step 2: Find best initial artifact
    print("\n" + "=" * 70)
    print("Step 2: Identify best artifact in knowledge base")
    print("-" * 70)
    
    best_key = None
    best_score = float("inf")
    for key, artifact in orchestrator.knowledge_base.items():
        score = evaluate_artifact(artifact)
        if score < best_score:
            best_score = score
            best_key = key

    print(f"\nBest initial artifact: {best_key}")
    print(f"Best initial score: {best_score:.4f}")
    print(f"Best initial vector: {orchestrator.knowledge_base[best_key].vector}")

    # Step 3: Run CMA-ES optimization
    print("\n" + "=" * 70)
    print("Step 3: Run CMA-ES local optimization")
    print("-" * 70)
    print("\nOptimization parameters:")
    print("  Algorithm: CMA-ES (Covariance Matrix Adaptation)")
    print("  Max generations: 100")
    print("  Initial sigma: 1.0")
    print("  Starting point: Best artifact from knowledge base")
    print("\nRunning optimization...")

    optimized_artifact = orchestrator._initiate_local_training(
        evaluate_artifact,
        max_generations=100,
        sigma0=1.0
    )

    optimized_score = evaluate_artifact(optimized_artifact)
    
    print("\n✓ Optimization complete!")
    print(f"\nOptimized score: {optimized_score:.4f}")
    print(f"Improvement: {best_score - optimized_score:.4f}")
    print(f"Improvement %: {((best_score - optimized_score) / best_score * 100):.1f}%")
    print(f"Optimized vector: {optimized_artifact.vector}")

    # Step 4: Analyze metadata
    print("\n" + "=" * 70)
    print("Step 4: Analyze optimization metadata")
    print("-" * 70)
    print("\nMetadata from optimization:")
    for key, value in optimized_artifact.metadata.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.6f}")
        else:
            print(f"  {key}: {value}")

    # Step 5: Integrate back into knowledge base
    print("\n" + "=" * 70)
    print("Step 5: Integrate optimized artifact into knowledge base")
    print("-" * 70)
    
    orchestrator.add_knowledge("cma_optimized", optimized_artifact)
    
    print("\nUpdated knowledge base:")
    all_scores = {}
    for key, artifact in orchestrator.knowledge_base.items():
        score = evaluate_artifact(artifact)
        all_scores[key] = score
        print(f"  {key}: score = {score:.4f}")

    best_overall_key = min(all_scores, key=all_scores.get)
    print(f"\n✓ Best artifact in knowledge base: {best_overall_key}")
    print(f"  Score: {all_scores[best_overall_key]:.4f}")

    # Step 6: Compare to global optimum
    print("\n" + "=" * 70)
    print("Step 6: Compare to theoretical global optimum")
    print("-" * 70)
    
    global_optimum = np.zeros(dimension)
    global_optimum_score = ackley_function(global_optimum)
    
    print(f"\nGlobal optimum (origin):")
    print(f"  Vector: {global_optimum.tolist()}")
    print(f"  Score: {global_optimum_score:.4f}")
    
    distance_to_optimum = np.linalg.norm(
        np.array(optimized_artifact.vector) - global_optimum
    )
    print(f"\nOptimized solution:")
    print(f"  Distance to global optimum: {distance_to_optimum:.4f}")
    print(f"  Score gap: {optimized_score - global_optimum_score:.4f}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\n✓ Phase 4 'The Forge of Hephaestus' successfully demonstrated!")
    print(f"\nKey Results:")
    print(f"  • Starting score: {best_score:.4f}")
    print(f"  • Final score: {optimized_score:.4f}")
    print(f"  • Total improvement: {best_score - optimized_score:.4f} ({((best_score - optimized_score) / best_score * 100):.1f}%)")
    print(f"  • Generations: {optimized_artifact.metadata['generations']}")
    print(f"  • Final distance to global optimum: {distance_to_optimum:.4f}")
    print(f"\n✓ The 'Primitive Local Intelligence' has been cured with CMA-ES!")
    print()


if __name__ == "__main__":
    main()
