#!/usr/bin/env python3
"""
Análise e Otimização do Sistema PENIN-Ω
========================================

Script para analisar o desempenho do sistema e aplicar otimizações.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import statistics

def analyze_performance(db_path: str = "penin_omega_worm.db") -> Dict[str, Any]:
    """Analisa o desempenho do sistema baseado nos logs WORM."""
    
    if not Path(db_path).exists():
        return {"error": "Database not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='events'
    """)
    
    if not cursor.fetchone():
        conn.close()
        return {"error": "No events table found"}
    
    # Analyze events
    cursor.execute("SELECT * FROM events ORDER BY timestamp")
    events = cursor.fetchall()
    
    if not events:
        conn.close()
        return {"error": "No events found"}
    
    # Parse events
    cycle_times = []
    decisions = {"PROMOTE": 0, "ABORT": 0}
    ethics_violations = 0
    
    for event in events:
        try:
            data = json.loads(event[2])  # Assuming JSON in third column
            
            if "cycle_time" in data:
                cycle_times.append(data["cycle_time"])
            
            if "decision" in data:
                decision = data["decision"]
                if decision in decisions:
                    decisions[decision] += 1
            
            if "ethics_violations" in data and data["ethics_violations"] > 0:
                ethics_violations += 1
                
        except (json.JSONDecodeError, IndexError):
            continue
    
    conn.close()
    
    # Calculate statistics
    analysis = {
        "total_events": len(events),
        "decisions": decisions,
        "ethics_violations": ethics_violations,
        "performance": {}
    }
    
    if cycle_times:
        analysis["performance"] = {
            "avg_cycle_time": statistics.mean(cycle_times),
            "median_cycle_time": statistics.median(cycle_times),
            "min_cycle_time": min(cycle_times),
            "max_cycle_time": max(cycle_times),
            "std_dev": statistics.stdev(cycle_times) if len(cycle_times) > 1 else 0
        }
    
    # Calculate success rate
    total_decisions = sum(decisions.values())
    if total_decisions > 0:
        analysis["success_rate"] = decisions["PROMOTE"] / total_decisions
    else:
        analysis["success_rate"] = 0
    
    return analysis

def optimize_configuration(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Sugere otimizações baseadas na análise."""
    
    optimizations = []
    config_updates = {}
    
    # Check success rate
    if "success_rate" in analysis:
        if analysis["success_rate"] < 0.5:
            optimizations.append("Low success rate detected - consider relaxing thresholds")
            config_updates["evolution"] = {"convergence_threshold": 0.002}
        elif analysis["success_rate"] > 0.9:
            optimizations.append("High success rate - can tighten thresholds for better quality")
            config_updates["evolution"] = {"convergence_threshold": 0.0005}
    
    # Check performance
    if "performance" in analysis and analysis["performance"]:
        avg_time = analysis["performance"]["avg_cycle_time"]
        if avg_time > 1.0:
            optimizations.append("Slow cycle times - enable caching and reduce complexity")
            config_updates["fibonacci"] = {"cache": True, "max_interval_s": 150}
        
        std_dev = analysis["performance"]["std_dev"]
        if std_dev > avg_time * 0.5:
            optimizations.append("High variance in cycle times - stabilize with EWMA")
            config_updates["caos_plus"] = {"ewma_alpha": 0.3, "min_stability_cycles": 7}
    
    # Check ethics
    if analysis.get("ethics_violations", 0) > analysis.get("total_events", 1) * 0.1:
        optimizations.append("High ethics violation rate - adjust ethics parameters")
        config_updates["ethics"] = {
            "ece_max": 0.2,
            "bias_max": 2.5,
            "fairness_min": 0.6
        }
    
    return {
        "optimizations": optimizations,
        "config_updates": config_updates,
        "analysis": analysis
    }

def apply_optimizations(config_path: str = "optimized_config.json") -> None:
    """Aplica otimizações e salva configuração."""
    
    # Analyze current performance
    print("Analyzing system performance...")
    analysis = analyze_performance()
    
    if "error" in analysis:
        print(f"Error: {analysis['error']}")
        return
    
    # Get optimizations
    optimization_result = optimize_configuration(analysis)
    
    # Print analysis
    print("\n" + "="*60)
    print("Performance Analysis")
    print("="*60)
    print(f"Total events: {analysis.get('total_events', 0)}")
    print(f"Success rate: {analysis.get('success_rate', 0):.1%}")
    print(f"Ethics violations: {analysis.get('ethics_violations', 0)}")
    
    if "performance" in analysis and analysis["performance"]:
        print(f"\nCycle Times:")
        print(f"  Average: {analysis['performance']['avg_cycle_time']:.3f}s")
        print(f"  Median: {analysis['performance']['median_cycle_time']:.3f}s")
        print(f"  Min/Max: {analysis['performance']['min_cycle_time']:.3f}s / {analysis['performance']['max_cycle_time']:.3f}s")
        print(f"  Std Dev: {analysis['performance']['std_dev']:.3f}s")
    
    # Print optimizations
    print("\n" + "="*60)
    print("Recommended Optimizations")
    print("="*60)
    
    if optimization_result["optimizations"]:
        for i, opt in enumerate(optimization_result["optimizations"], 1):
            print(f"{i}. {opt}")
    else:
        print("No optimizations needed - system is performing well!")
    
    # Save optimized config
    if optimization_result["config_updates"]:
        with open(config_path, 'w') as f:
            json.dump(optimization_result["config_updates"], f, indent=2)
        print(f"\nOptimized configuration saved to {config_path}")
    
    print("="*60 + "\n")

def benchmark_system() -> Dict[str, float]:
    """Executa benchmark do sistema."""
    
    print("Running system benchmark...")
    benchmarks = {}
    
    # Test import speed
    start = time.time()
    try:
        from importlib import import_module
        module = import_module('1_de_8_v7')
        benchmarks["import_time"] = time.time() - start
        print(f"✓ Import time: {benchmarks['import_time']:.3f}s")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return benchmarks
    
    # Test initialization
    start = time.time()
    try:
        config = {"evolution": {"seed": 42}}
        core = module.PeninOmegaCore(config)
        benchmarks["init_time"] = time.time() - start
        print(f"✓ Init time: {benchmarks['init_time']:.3f}s")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return benchmarks
    
    # Test single cycle (sync version)
    start = time.time()
    try:
        import asyncio
        result = asyncio.run(core.master_equation_cycle())
        benchmarks["cycle_time"] = time.time() - start
        print(f"✓ Cycle time: {benchmarks['cycle_time']:.3f}s")
    except Exception as e:
        print(f"✗ Cycle failed: {e}")
    
    # Calculate total
    benchmarks["total_time"] = sum(benchmarks.values())
    print(f"\nTotal benchmark time: {benchmarks['total_time']:.3f}s")
    
    return benchmarks

def main():
    """Main function."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║        PENIN-Ω - Análise e Otimização do Sistema        ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run benchmark
    print("\n1. BENCHMARK")
    print("-" * 60)
    benchmarks = benchmark_system()
    
    # Analyze performance
    print("\n2. ANÁLISE DE DESEMPENHO")
    print("-" * 60)
    apply_optimizations()
    
    # Provide recommendations
    print("\n3. RECOMENDAÇÕES")
    print("-" * 60)
    
    if benchmarks:
        if benchmarks.get("cycle_time", 999) > 0.5:
            print("⚠️  Cycle time is high. Consider:")
            print("   - Enable caching for Fibonacci calculations")
            print("   - Reduce CAOS complexity")
            print("   - Use lighter ethics validation")
        else:
            print("✅ Performance is good!")
        
        if benchmarks.get("import_time", 999) > 1.0:
            print("⚠️  Import time is high. Consider:")
            print("   - Lazy loading of heavy dependencies")
            print("   - Pre-compiling Python files")
        
        if benchmarks.get("init_time", 999) > 0.5:
            print("⚠️  Initialization is slow. Consider:")
            print("   - Defer non-critical initialization")
            print("   - Use connection pooling for databases")
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()