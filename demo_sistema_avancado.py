#!/usr/bin/env python3
"""
Sistema PENIN-Ω v7.2 - Demonstração Avançada
=============================================

Demonstração completa do sistema com todas as funcionalidades P0/P1 integradas.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

# Import core modules
from importlib import import_module

# Import P0/P1 modules
from penin.omega.ethics_metrics import EthicsCalculator, EthicsGate
from penin.omega.ledger import WORMLedger
from penin.router import MultiLLMRouter
from observability import ObservabilityConfig, integrate_observability

# Import utilities
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)


class PeninOmegaSystem:
    """
    Sistema PENIN-Ω completo com todas as funcionalidades P0/P1.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the complete system."""
        self.config = config or self._get_default_config()
        self.stats = {
            "cycles_run": 0,
            "cycles_successful": 0,
            "cycles_aborted": 0,
            "total_runtime": 0,
            "ethics_violations": 0,
            "budget_spent": 0,
        }

        # Initialize components
        self._initialize_components()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "evolution": {"seed": 42, "max_cycles": 10, "convergence_threshold": 0.001},
            "fibonacci": {
                "enabled": True,
                "cache": True,
                "trust_region": True,
                "search_method": "fibonacci",
                "max_interval_s": 300,
            },
            "caos_plus": {"max_boost": 0.05, "ewma_alpha": 0.2, "min_stability_cycles": 5},
            "ethics": {
                "ece_max": 0.15,
                "bias_max": 2.0,
                "fairness_min": 0.7,
                "require_consent": True,
                "require_eco": True,
            },
            "observability": {
                "metrics_enabled": True,
                "metrics_port": 8000,
                "metrics_bind_host": "127.0.0.1",
                "log_level": "INFO",
            },
            "budget": {"daily_limit_usd": 5.0, "alert_threshold": 0.8},
        }

    def _initialize_components(self):
        """Initialize all system components."""
        log.info("Initializing PENIN-Ω system components...")

        # Initialize core v7
        try:
            self.core_module = import_module("1_de_8_v7")
            self.core = self.core_module.PeninOmegaCore(self.config)
            log.info("✓ Core v7 initialized")
        except Exception as e:
            log.error(f"Failed to initialize core: {e}")
            raise

        # Initialize ethics
        self.ethics_calculator = EthicsCalculator(
            ece_max=self.config["ethics"]["ece_max"],
            bias_max=self.config["ethics"]["bias_max"],
            fairness_min=self.config["ethics"]["fairness_min"],
        )
        self.ethics_gate = EthicsGate()
        log.info("✓ Ethics system initialized")

        # Initialize WORM ledger
        self.worm = WORMLedger("penin_omega_worm.db")
        log.info("✓ WORM ledger initialized")

        # Initialize observability
        if self.config["observability"]["metrics_enabled"]:
            self.observability = integrate_observability(
                self.core,
                ObservabilityConfig(
                    metrics_port=self.config["observability"]["metrics_port"],
                    metrics_bind_host=self.config["observability"]["metrics_bind_host"],
                ),
            )
            log.info("✓ Observability initialized")
        else:
            self.observability = None

        log.info("System initialization complete")

    async def run_cycle(self) -> Dict[str, Any]:
        """Run a single evolution cycle."""
        cycle_start = time.time()
        self.stats["cycles_run"] += 1

        log.info(f"\n{'=' * 60}")
        log.info(f"Starting cycle {self.stats['cycles_run']}")
        log.info(f"{'=' * 60}")

        try:
            # Run core cycle
            result = await self.core.master_equation_cycle()

            # Check ethics
            if hasattr(self.core, "_last_ethics_metrics"):
                ethics_metrics = self.core._last_ethics_metrics
                passed, violations = self.ethics_gate.validate(ethics_metrics)

                if not passed:
                    log.warning(f"Ethics violations detected: {violations}")
                    self.stats["ethics_violations"] += 1
                    result["ethics_passed"] = False
                else:
                    log.info("✓ Ethics check passed")
                    result["ethics_passed"] = True

            # Check decision
            if result.get("decision") == "PROMOTE":
                self.stats["cycles_successful"] += 1
                log.info("✅ Cycle successful - PROMOTE decision")
            else:
                self.stats["cycles_aborted"] += 1
                log.warning(f"⚠️ Cycle aborted: {result.get('reason', 'Unknown')}")

            # Track runtime
            cycle_time = time.time() - cycle_start
            self.stats["total_runtime"] += cycle_time
            result["cycle_time"] = cycle_time

            # Log to WORM
            self.worm.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "cycle": self.stats["cycles_run"],
                    "decision": result.get("decision"),
                    "metrics": {
                        "alpha": result.get("xt", {}).get("alpha"),
                        "delta_linf": result.get("xt", {}).get("delta_linf"),
                        "caos": result.get("xt", {}).get("caos"),
                    },
                    "cycle_time": cycle_time,
                }
            )

            return result

        except Exception as e:
            log.error(f"Cycle failed with error: {e}")
            self.stats["cycles_aborted"] += 1
            return {"error": str(e), "decision": "ABORT"}

    async def run_evolution(self, max_cycles: Optional[int] = None) -> Dict[str, Any]:
        """Run complete evolution process."""
        max_cycles = max_cycles or self.config["evolution"]["max_cycles"]

        log.info(f"\n{'=' * 60}")
        log.info(f"Starting PENIN-Ω Evolution")
        log.info(f"Max cycles: {max_cycles}")
        log.info(f"Seed: {self.config['evolution']['seed']}")
        log.info(f"{'=' * 60}\n")

        results = []
        converged = False

        for i in range(max_cycles):
            result = await self.run_cycle()
            results.append(result)

            # Check convergence
            if self._check_convergence(results):
                converged = True
                log.info(f"✨ System converged after {i + 1} cycles")
                break

            # Small delay between cycles
            await asyncio.sleep(0.1)

        # Generate summary
        summary = self._generate_summary(results, converged)

        # Save results
        self._save_results(summary)

        return summary

    def _check_convergence(self, results: list) -> bool:
        """Check if system has converged."""
        if len(results) < 5:
            return False

        # Check if last 5 cycles had stable alpha
        recent_alphas = [r.get("xt", {}).get("alpha", 0) for r in results[-5:]]

        if not all(recent_alphas):
            return False

        # Check variance
        mean_alpha = sum(recent_alphas) / len(recent_alphas)
        variance = sum((a - mean_alpha) ** 2 for a in recent_alphas) / len(recent_alphas)

        threshold = self.config["evolution"]["convergence_threshold"]
        return variance < threshold

    def _generate_summary(self, results: list, converged: bool) -> Dict[str, Any]:
        """Generate evolution summary."""
        successful_cycles = [r for r in results if r.get("decision") == "PROMOTE"]

        summary = {
            "timestamp": datetime.now().isoformat(),
            "converged": converged,
            "stats": self.stats,
            "cycles": {
                "total": len(results),
                "successful": len(successful_cycles),
                "aborted": len(results) - len(successful_cycles),
            },
            "performance": {
                "avg_cycle_time": self.stats["total_runtime"] / max(1, self.stats["cycles_run"]),
                "success_rate": len(successful_cycles) / max(1, len(results)),
            },
        }

        # Add final metrics if available
        if results and "xt" in results[-1]:
            summary["final_metrics"] = {
                "alpha": results[-1]["xt"].get("alpha"),
                "delta_linf": results[-1]["xt"].get("delta_linf"),
                "caos": results[-1]["xt"].get("caos"),
                "sr": results[-1]["xt"].get("sr"),
                "g": results[-1]["xt"].get("g"),
            }

        return summary

    def _save_results(self, summary: Dict[str, Any]):
        """Save evolution results."""
        filename = f"evolution_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(summary, f, indent=2)
        log.info(f"Results saved to {filename}")

    def print_summary(self, summary: Dict[str, Any]):
        """Print formatted summary."""
        print(f"\n{'=' * 60}")
        print("PENIN-Ω Evolution Summary")
        print(f"{'=' * 60}")
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Converged: {'✓' if summary['converged'] else '✗'}")
        print(f"\nCycles:")
        print(f"  Total: {summary['cycles']['total']}")
        print(f"  Successful: {summary['cycles']['successful']}")
        print(f"  Aborted: {summary['cycles']['aborted']}")
        print(f"\nPerformance:")
        print(f"  Avg cycle time: {summary['performance']['avg_cycle_time']:.3f}s")
        print(f"  Success rate: {summary['performance']['success_rate']:.1%}")

        if "final_metrics" in summary:
            print(f"\nFinal Metrics:")
            for key, value in summary["final_metrics"].items():
                if value is not None:
                    print(f"  {key}: {value:.4f}")

        print(f"\nEthics:")
        print(f"  Violations: {summary['stats']['ethics_violations']}")

        print(f"{'=' * 60}\n")


async def main():
    """Main demonstration function."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║          PENIN-Ω v7.2 - Sistema de Evolução Mestre      ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Auto-evolução com garantias éticas e observabilidade   ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Create system
    system = PeninOmegaSystem()

    # Run evolution
    summary = await system.run_evolution(max_cycles=10)

    # Print summary
    system.print_summary(summary)

    # Shutdown
    if system.observability:
        system.observability.stop()

    print("System shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nEvolution interrupted by user.")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
