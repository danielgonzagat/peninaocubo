"""
Benchmark Master Equation Cycle Performance
===========================================

This benchmark measures the performance of the master_equation_cycle function
under various conditions to identify bottlenecks and validate optimizations.

Usage:
    python benchmarks/benchmark_master_equation.py
    python benchmarks/benchmark_master_equation.py --profile
    python benchmarks/benchmark_master_equation.py --memory
"""

import argparse
import cProfile
import io
import json
import pstats
import time
from pathlib import Path
from typing import Any

import numpy as np

from penin.math.penin_master_equation import (
    MasterEquationState,
    master_equation_cycle,
)


def create_test_loss_fn():
    """Create a simple loss function for testing."""

    LOSS_SQRT_COEFF = 0.01

    def loss_fn(state: np.ndarray, evidence: Any, policies: dict) -> float:
        # Optimized quadratic loss: use dot product instead of sum + norm
        # This is faster as it reuses the same computation
        dot_product = np.dot(state, state)
        return dot_product + LOSS_SQRT_COEFF * np.sqrt(dot_product)

    return loss_fn


class BenchmarkSuite:
    """Suite of benchmarks for Master Equation cycle."""

    def __init__(self):
        self.results = {}
        self.baseline_times = None

    def benchmark_small_state(self, n_iterations: int = 100) -> dict:
        """Benchmark with small state vector (10 dimensions)."""
        state = MasterEquationState(
            I=np.random.randn(10) * 0.5,
            n=0,
            alpha_n=0.0,
            caos_plus=1.5,
            sr_score=0.85,
            Linf=0.75,
        )

        loss_fn = create_test_loss_fn()
        evidence = None
        policies = {}

        times = []
        for _ in range(n_iterations):
            start = time.perf_counter()
            new_state = master_equation_cycle(
                state=state,
                evidence=evidence,
                policies=policies,
                loss_fn=loss_fn,
                alpha_0=0.1,
                caos_plus=1.5,
                sr_score=0.85,
                gamma=0.8,
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            state = new_state

        return {
            "name": "small_state",
            "dimensions": 10,
            "iterations": n_iterations,
            "mean_time_ms": np.mean(times) * 1000,
            "std_time_ms": np.std(times) * 1000,
            "min_time_ms": np.min(times) * 1000,
            "max_time_ms": np.max(times) * 1000,
            "total_time_s": np.sum(times),
        }

    def benchmark_medium_state(self, n_iterations: int = 100) -> dict:
        """Benchmark with medium state vector (100 dimensions)."""
        state = MasterEquationState(
            I=np.random.randn(100) * 0.5,
            n=0,
            alpha_n=0.0,
            caos_plus=1.5,
            sr_score=0.85,
            Linf=0.75,
        )

        loss_fn = create_test_loss_fn()
        evidence = None
        policies = {}

        times = []
        for _ in range(n_iterations):
            start = time.perf_counter()
            new_state = master_equation_cycle(
                state=state,
                evidence=evidence,
                policies=policies,
                loss_fn=loss_fn,
                alpha_0=0.1,
                caos_plus=1.5,
                sr_score=0.85,
                gamma=0.8,
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            state = new_state

        return {
            "name": "medium_state",
            "dimensions": 100,
            "iterations": n_iterations,
            "mean_time_ms": np.mean(times) * 1000,
            "std_time_ms": np.std(times) * 1000,
            "min_time_ms": np.min(times) * 1000,
            "max_time_ms": np.max(times) * 1000,
            "total_time_s": np.sum(times),
        }

    def benchmark_large_state(self, n_iterations: int = 50) -> dict:
        """Benchmark with large state vector (1000 dimensions)."""
        state = MasterEquationState(
            I=np.random.randn(1000) * 0.5,
            n=0,
            alpha_n=0.0,
            caos_plus=1.5,
            sr_score=0.85,
            Linf=0.75,
        )

        loss_fn = create_test_loss_fn()
        evidence = None
        policies = {}

        times = []
        for _ in range(n_iterations):
            start = time.perf_counter()
            new_state = master_equation_cycle(
                state=state,
                evidence=evidence,
                policies=policies,
                loss_fn=loss_fn,
                alpha_0=0.1,
                caos_plus=1.5,
                sr_score=0.85,
                gamma=0.8,
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            state = new_state

        return {
            "name": "large_state",
            "dimensions": 1000,
            "iterations": n_iterations,
            "mean_time_ms": np.mean(times) * 1000,
            "std_time_ms": np.std(times) * 1000,
            "min_time_ms": np.min(times) * 1000,
            "max_time_ms": np.max(times) * 1000,
            "total_time_s": np.sum(times),
        }

    def benchmark_with_constraints(self, n_iterations: int = 100) -> dict:
        """Benchmark with H and S constraints enabled."""
        state = MasterEquationState(
            I=np.random.randn(100) * 0.5,
            n=0,
            alpha_n=0.0,
            caos_plus=1.5,
            sr_score=0.85,
            Linf=0.75,
        )

        loss_fn = create_test_loss_fn()
        evidence = None
        policies = {}
        H_constraints = {"bounds": (0.0, 1.0), "max_norm": 10.0}
        S_constraints = {}

        times = []
        for _ in range(n_iterations):
            start = time.perf_counter()
            new_state = master_equation_cycle(
                state=state,
                evidence=evidence,
                policies=policies,
                loss_fn=loss_fn,
                alpha_0=0.1,
                caos_plus=1.5,
                sr_score=0.85,
                gamma=0.8,
                H_constraints=H_constraints,
                S_constraints=S_constraints,
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            state = new_state

        return {
            "name": "with_constraints",
            "dimensions": 100,
            "iterations": n_iterations,
            "mean_time_ms": np.mean(times) * 1000,
            "std_time_ms": np.std(times) * 1000,
            "min_time_ms": np.min(times) * 1000,
            "max_time_ms": np.max(times) * 1000,
            "total_time_s": np.sum(times),
        }

    def run_all_benchmarks(self) -> dict:
        """Run all benchmarks and return results."""
        print("🔬 Running Master Equation Benchmarks")
        print("=" * 60)

        benchmarks = [
            ("Small State (10D)", self.benchmark_small_state),
            ("Medium State (100D)", self.benchmark_medium_state),
            ("Large State (1000D)", self.benchmark_large_state),
            ("With Constraints (100D)", self.benchmark_with_constraints),
        ]

        results = []
        for name, benchmark_fn in benchmarks:
            print(f"\n⏱️  {name}...")
            result = benchmark_fn()
            results.append(result)
            print(f"   Mean: {result['mean_time_ms']:.3f}ms ± {result['std_time_ms']:.3f}ms")
            print(f"   Range: [{result['min_time_ms']:.3f}ms - {result['max_time_ms']:.3f}ms]")
            print(f"   Total: {result['total_time_s']:.3f}s")

        print("\n" + "=" * 60)
        print("✅ Benchmarks complete!")

        return {"timestamp": time.time(), "results": results}

    def profile_master_equation(self, state_size: int = 100, n_iterations: int = 50) -> str:
        """Profile the master equation cycle with cProfile."""
        print(f"\n🔍 Profiling Master Equation (state_size={state_size}, iterations={n_iterations})")
        print("=" * 60)

        state = MasterEquationState(
            I=np.random.randn(state_size) * 0.5,
            n=0,
            alpha_n=0.0,
            caos_plus=1.5,
            sr_score=0.85,
            Linf=0.75,
        )

        loss_fn = create_test_loss_fn()
        evidence = None
        policies = {}

        profiler = cProfile.Profile()
        profiler.enable()

        for _ in range(n_iterations):
            state = master_equation_cycle(
                state=state,
                evidence=evidence,
                policies=policies,
                loss_fn=loss_fn,
                alpha_0=0.1,
                caos_plus=1.5,
                sr_score=0.85,
                gamma=0.8,
            )

        profiler.disable()

        # Get profiling results
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
        ps.print_stats(20)  # Top 20 functions

        profile_output = s.getvalue()
        print(profile_output)

        return profile_output

    def memory_benchmark(self, state_size: int = 100, n_iterations: int = 50) -> dict:
        """Benchmark memory usage during execution."""
        import tracemalloc

        print(f"\n💾 Memory Profiling (state_size={state_size}, iterations={n_iterations})")
        print("=" * 60)

        tracemalloc.start()

        state = MasterEquationState(
            I=np.random.randn(state_size) * 0.5,
            n=0,
            alpha_n=0.0,
            caos_plus=1.5,
            sr_score=0.85,
            Linf=0.75,
        )

        loss_fn = create_test_loss_fn()
        evidence = None
        policies = {}

        snapshot_before = tracemalloc.take_snapshot()

        for _ in range(n_iterations):
            state = master_equation_cycle(
                state=state,
                evidence=evidence,
                policies=policies,
                loss_fn=loss_fn,
                alpha_0=0.1,
                caos_plus=1.5,
                sr_score=0.85,
                gamma=0.8,
            )

        snapshot_after = tracemalloc.take_snapshot()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Compute memory delta
        top_stats = snapshot_after.compare_to(snapshot_before, "lineno")

        print(f"Current memory: {current / 1024:.1f} KB")
        print(f"Peak memory: {peak / 1024:.1f} KB")
        print("\nTop memory allocations:")
        for stat in top_stats[:5]:
            print(f"  {stat}")

        return {
            "current_kb": current / 1024,
            "peak_kb": peak / 1024,
            "state_size": state_size,
            "iterations": n_iterations,
        }


def save_results(results: dict, filename: str = "benchmark_results.json"):
    """Save benchmark results to JSON file."""
    output_path = Path(__file__).parent / filename
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark Master Equation performance")
    parser.add_argument("--profile", action="store_true", help="Run CPU profiling")
    parser.add_argument("--memory", action="store_true", help="Run memory profiling")
    parser.add_argument("--save", action="store_true", help="Save results to JSON")
    parser.add_argument("--baseline", action="store_true", help="Save as baseline for comparison")

    args = parser.parse_args()

    suite = BenchmarkSuite()

    # Run standard benchmarks
    results = suite.run_all_benchmarks()

    # Run profiling if requested
    if args.profile:
        profile_output = suite.profile_master_equation(state_size=100, n_iterations=50)
        results["profile"] = profile_output

    # Run memory profiling if requested
    if args.memory:
        memory_results = suite.memory_benchmark(state_size=100, n_iterations=50)
        results["memory"] = memory_results

    # Save results
    if args.save:
        filename = "benchmark_baseline.json" if args.baseline else "benchmark_results.json"
        save_results(results, filename)

    return results


if __name__ == "__main__":
    main()
