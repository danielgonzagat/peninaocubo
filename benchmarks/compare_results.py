"""
Performance Comparison Tool
============================

Compare baseline and optimized benchmark results.
"""

import json
from pathlib import Path


def load_results(filename: str) -> dict:
    """Load benchmark results from JSON file."""
    path = Path(__file__).parent / filename
    with open(path) as f:
        return json.load(f)


def compare_benchmarks():
    """Compare baseline and optimized results."""
    print("📊 PENIN-Ω Master Equation Performance Comparison")
    print("=" * 70)

    try:
        baseline = load_results("benchmark_baseline.json")
        optimized = load_results("benchmark_results.json")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nRun benchmarks first:")
        print("  python benchmarks/benchmark_master_equation.py --save --baseline")
        print("  # Make optimizations...")
        print("  python benchmarks/benchmark_master_equation.py --save")
        return

    print("\n📈 Performance Improvements:")
    print("-" * 70)
    print(f"{'Benchmark':<25} {'Baseline':<15} {'Optimized':<15} {'Improvement':<15}")
    print("-" * 70)

    total_improvement = 0
    count = 0

    for baseline_res, optimized_res in zip(baseline["results"], optimized["results"], strict=False):
        name = baseline_res["name"]
        baseline_time = baseline_res["mean_time_ms"]
        optimized_time = optimized_res["mean_time_ms"]
        improvement = ((baseline_time - optimized_time) / baseline_time) * 100

        total_improvement += improvement
        count += 1

        status = "✅" if improvement >= 30 else "⚠️" if improvement >= 10 else "❌"

        print(
            f"{name:<25} {baseline_time:>10.3f}ms {optimized_time:>10.3f}ms "
            f"{status} {improvement:>8.1f}%"
        )

    print("-" * 70)
    avg_improvement = total_improvement / count
    print(f"{'Average Improvement':<25} {'':<15} {'':<15} {'✅' if avg_improvement >= 30 else '⚠️'} {avg_improvement:>8.1f}%")
    print("=" * 70)

    # Memory comparison
    if "memory" in baseline and "memory" in optimized:
        print("\n💾 Memory Usage Comparison:")
        print("-" * 70)
        baseline_mem = baseline["memory"]["peak_kb"]
        optimized_mem = optimized["memory"]["peak_kb"]
        mem_change = ((optimized_mem - baseline_mem) / baseline_mem) * 100
        mem_status = "✅" if mem_change <= 0 else "⚠️"

        print(f"Peak Memory:    {baseline_mem:.1f} KB → {optimized_mem:.1f} KB ({mem_status} {mem_change:+.1f}%)")

    # Function call comparison
    if "profile" in baseline and "profile" in optimized:
        print("\n🔍 Function Call Analysis:")
        print("-" * 70)

        # Extract function calls from profile string
        baseline_calls = extract_function_calls(baseline["profile"])
        optimized_calls = extract_function_calls(optimized["profile"])

        calls_reduction = ((baseline_calls - optimized_calls) / baseline_calls) * 100
        calls_status = "✅" if calls_reduction > 0 else "⚠️"

        print(f"Total function calls: {baseline_calls:,} → {optimized_calls:,} ({calls_status} {calls_reduction:+.1f}%)")

    print("\n✅ Analysis complete!")

    # Achievement check
    if avg_improvement >= 30:
        print("\n🎉 SUCCESS: Achieved >30% performance improvement!")
    elif avg_improvement >= 10:
        print(f"\n⚠️  PARTIAL: Achieved {avg_improvement:.1f}% improvement (target: 30%)")
    else:
        print(f"\n❌ WARNING: Only {avg_improvement:.1f}% improvement (target: 30%)")


def extract_function_calls(profile_str: str) -> int:
    """Extract total function calls from cProfile output."""
    lines = profile_str.split("\n")
    for line in lines:
        if "function calls in" in line:
            parts = line.strip().split()
            return int(parts[0])
    return 0


if __name__ == "__main__":
    compare_benchmarks()
