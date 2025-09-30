#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Benchmark for PENIN-Ω System

This script benchmarks the performance improvements made to the system,
including caching, resource monitoring optimization, and computational efficiency.
"""

import time
import asyncio
import statistics
from typing import List, Dict, Any
import sys
import os

# Add the workspace to the path
sys.path.insert(0, '/workspace')

async def benchmark_master_equation_cycles(core, num_cycles: int = 10) -> Dict[str, Any]:
    """Benchmark master equation cycles"""
    times = []
    results = []
    
    print(f"Running {num_cycles} master equation cycles...")
    
    for i in range(num_cycles):
        start_time = time.time()
        result = await core.master_equation_cycle()
        cycle_time = time.time() - start_time
        
        times.append(cycle_time)
        results.append(result)
        
        if i % 5 == 0:
            print(f"  Cycle {i+1}: {cycle_time:.4f}s")
    
    return {
        "times": times,
        "results": results,
        "mean_time": statistics.mean(times),
        "median_time": statistics.median(times),
        "min_time": min(times),
        "max_time": max(times),
        "std_time": statistics.stdev(times) if len(times) > 1 else 0.0
    }

async def benchmark_ethics_computation(core, num_iterations: int = 100) -> Dict[str, Any]:
    """Benchmark ethics computation with caching"""
    times = []
    
    print(f"Running {num_iterations} ethics computations...")
    
    for i in range(num_iterations):
        start_time = time.time()
        # This should use the cached version after the first call
        ethics_metrics = core._compute_real_ethics_metrics(core.xt)
        computation_time = time.time() - start_time
        
        times.append(computation_time)
        
        if i % 20 == 0:
            print(f"  Iteration {i+1}: {computation_time:.6f}s")
    
    return {
        "times": times,
        "mean_time": statistics.mean(times),
        "median_time": statistics.median(times),
        "min_time": min(times),
        "max_time": max(times),
        "std_time": statistics.stdev(times) if len(times) > 1 else 0.0,
        "first_call": times[0],
        "subsequent_calls": times[1:] if len(times) > 1 else []
    }

async def benchmark_alpha_computation(core, num_iterations: int = 100) -> Dict[str, Any]:
    """Benchmark alpha computation with caching"""
    times = []
    
    print(f"Running {num_iterations} alpha computations...")
    
    for i in range(num_iterations):
        start_time = time.time()
        alpha = core._compute_alpha()
        computation_time = time.time() - start_time
        
        times.append(computation_time)
        
        if i % 20 == 0:
            print(f"  Iteration {i+1}: {computation_time:.6f}s")
    
    return {
        "times": times,
        "mean_time": statistics.mean(times),
        "median_time": statistics.median(times),
        "min_time": min(times),
        "max_time": max(times),
        "std_time": statistics.stdev(times) if len(times) > 1 else 0.0,
        "first_call": times[0],
        "subsequent_calls": times[1:] if len(times) > 1 else []
    }

def benchmark_resource_monitoring(num_iterations: int = 1000) -> Dict[str, Any]:
    """Benchmark resource monitoring with and without caching"""
    import psutil
    
    print(f"Running {num_iterations} resource monitoring calls...")
    
    # Without caching
    start_time = time.time()
    for _ in range(num_iterations):
        cpu = psutil.cpu_percent(interval=None) / 100.0
        mem = psutil.virtual_memory().percent / 100.0
    no_cache_time = time.time() - start_time
    
    # With caching (simulated)
    try:
        from penin.omega.performance import get_cpu_usage, get_memory_usage
        
        start_time = time.time()
        for _ in range(num_iterations):
            cpu = get_cpu_usage()
            mem = get_memory_usage()
        cache_time = time.time() - start_time
        
        cache_improvement = (no_cache_time - cache_time) / no_cache_time * 100
        
        return {
            "no_cache_time": no_cache_time,
            "cache_time": cache_time,
            "improvement_percent": cache_improvement,
            "speedup": no_cache_time / cache_time if cache_time > 0 else float('inf')
        }
    except ImportError:
        return {
            "no_cache_time": no_cache_time,
            "cache_time": None,
            "improvement_percent": None,
            "speedup": None,
            "note": "Performance optimization module not available"
        }

async def run_comprehensive_benchmark():
    """Run comprehensive performance benchmark"""
    print("=" * 60)
    print("PENIN-Ω PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    # Import the core system
    try:
        sys.path.insert(0, '/workspace')
        import importlib.util
        spec = importlib.util.spec_from_file_location("penin_core", "/workspace/1_de_8_v7.py")
        penin_core = importlib.util.module_from_spec(spec)
        sys.modules["penin_core"] = penin_core
        spec.loader.exec_module(penin_core)
        PeninOmegaCore = penin_core.PeninOmegaCore
    except Exception as e:
        print(f"Failed to import core system: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Initialize core
    config = {"evolution": {"seed": 42}}
    core = PeninOmegaCore(config)
    
    results = {}
    
    try:
        # Benchmark 1: Master equation cycles
        print("\n[Benchmark 1] Master Equation Cycles")
        print("-" * 40)
        results["master_equation"] = await benchmark_master_equation_cycles(core, 10)
        
        # Benchmark 2: Ethics computation caching
        print("\n[Benchmark 2] Ethics Computation Caching")
        print("-" * 40)
        results["ethics_computation"] = await benchmark_ethics_computation(core, 50)
        
        # Benchmark 3: Alpha computation caching
        print("\n[Benchmark 3] Alpha Computation Caching")
        print("-" * 40)
        results["alpha_computation"] = await benchmark_alpha_computation(core, 50)
        
        # Benchmark 4: Resource monitoring
        print("\n[Benchmark 4] Resource Monitoring")
        print("-" * 40)
        results["resource_monitoring"] = benchmark_resource_monitoring(1000)
        
        # Get performance stats if available
        try:
            from penin.omega.performance import get_performance_stats
            results["performance_stats"] = get_performance_stats()
        except ImportError:
            results["performance_stats"] = {"note": "Performance stats not available"}
        
    finally:
        core.shutdown()
    
    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    
    # Master equation cycles
    me_stats = results["master_equation"]
    print(f"\nMaster Equation Cycles (10 cycles):")
    print(f"  Mean time: {me_stats['mean_time']:.4f}s")
    print(f"  Median time: {me_stats['median_time']:.4f}s")
    print(f"  Min time: {me_stats['min_time']:.4f}s")
    print(f"  Max time: {me_stats['max_time']:.4f}s")
    print(f"  Std dev: {me_stats['std_time']:.4f}s")
    
    # Ethics computation
    ethics_stats = results["ethics_computation"]
    print(f"\nEthics Computation (50 iterations):")
    print(f"  Mean time: {ethics_stats['mean_time']:.6f}s")
    print(f"  First call: {ethics_stats['first_call']:.6f}s")
    if ethics_stats['subsequent_calls']:
        subsequent_mean = statistics.mean(ethics_stats['subsequent_calls'])
        print(f"  Subsequent calls mean: {subsequent_mean:.6f}s")
        cache_speedup = ethics_stats['first_call'] / subsequent_mean if subsequent_mean > 0 else float('inf')
        print(f"  Cache speedup: {cache_speedup:.2f}x")
    
    # Alpha computation
    alpha_stats = results["alpha_computation"]
    print(f"\nAlpha Computation (50 iterations):")
    print(f"  Mean time: {alpha_stats['mean_time']:.6f}s")
    print(f"  First call: {alpha_stats['first_call']:.6f}s")
    if alpha_stats['subsequent_calls']:
        subsequent_mean = statistics.mean(alpha_stats['subsequent_calls'])
        print(f"  Subsequent calls mean: {subsequent_mean:.6f}s")
        cache_speedup = alpha_stats['first_call'] / subsequent_mean if subsequent_mean > 0 else float('inf')
        print(f"  Cache speedup: {cache_speedup:.2f}x")
    
    # Resource monitoring
    res_stats = results["resource_monitoring"]
    print(f"\nResource Monitoring (1000 iterations):")
    print(f"  No cache time: {res_stats['no_cache_time']:.4f}s")
    if res_stats['cache_time'] is not None:
        print(f"  Cache time: {res_stats['cache_time']:.4f}s")
        print(f"  Improvement: {res_stats['improvement_percent']:.1f}%")
        print(f"  Speedup: {res_stats['speedup']:.2f}x")
    else:
        print(f"  {res_stats.get('note', 'Cache not available')}")
    
    # Performance stats
    perf_stats = results["performance_stats"]
    if "cache_stats" in perf_stats:
        cache_stats = perf_stats["cache_stats"]
        print(f"\nOverall Cache Statistics:")
        print(f"  Cache hit rate: {cache_stats['cache_hit_rate']:.2%}")
        print(f"  Total computation time: {cache_stats['total_computation_time']:.4f}s")
        print(f"  Memory usage: {perf_stats['memory_usage_mb']:.1f}MB")
    
    print("\n" + "=" * 60)
    print("Benchmark completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_comprehensive_benchmark())