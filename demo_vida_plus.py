#!/usr/bin/env python3
"""
PENIN-Ω Life+ Demo
==================

Demonstrates the complete Life Equation (+) system with all modules integrated.
Shows how the non-compensatory gate controls evolution.
"""

import time
import random
from pathlib import Path

# Life+ Modules
from penin.omega.life_eq import life_equation_simple, LifeVerdict
from penin.omega.fractal import FractalOrchestrator
from penin.omega.swarm import SwarmOrchestrator
from penin.omega.caos_kratos import KratosController
from penin.omega.market import CognitiveMarketplace, Need, Offer
from penin.omega.neural_chain import NeuralLedger
from penin.omega.self_rag import SelfRAG
from penin.omega.api_metabolizer import APIMetabolizer
from penin.omega.immunity import ImmunitySystem
from penin.omega.checkpoint import CheckpointManager
from penin.omega.darwin_audit import DarwinianAuditor, Variant
from penin.omega.zero_consciousness import ZeroConsciousnessMonitor


class LifePlusSystem:
    """Complete Life+ System Orchestrator"""
    
    def __init__(self):
        print("🚀 Initializing PENIN-Ω Life+ System...")
        
        # Core modules
        self.fractal = FractalOrchestrator()
        self.swarm = SwarmOrchestrator("main-node")
        self.kratos = KratosController()
        self.market = CognitiveMarketplace()
        self.ledger = NeuralLedger()
        self.rag = SelfRAG()
        self.metabolizer = APIMetabolizer()
        self.immunity = ImmunitySystem()
        self.checkpoint = CheckpointManager()
        self.darwin = DarwinianAuditor()
        self.zc_monitor = ZeroConsciousnessMonitor()
        
        # System state
        self.cycle = 0
        self.evolution_blocked = 0
        self.evolution_allowed = 0
        
        print("✅ All modules initialized")
    
    def run_cycle(self) -> dict:
        """Run one complete evolution cycle"""
        self.cycle += 1
        print(f"\n{'='*60}")
        print(f"📍 Cycle {self.cycle}")
        print(f"{'='*60}")
        
        # 1. Collect metrics
        metrics = self._collect_metrics()
        print(f"📊 Metrics collected: ECE={metrics['ece']:.4f}, ρ_bias={metrics['rho_bias']:.4f}")
        
        # 2. Immunity check
        immune_result = self.immunity.check(metrics)
        print(f"🛡️  Immunity: {'✅ SAFE' if immune_result['safe'] else '❌ ANOMALY DETECTED'}")
        
        # 3. Zero-consciousness check
        zc_check = self.zc_monitor.check(
            ece=metrics['ece'],
            randomness=metrics.get('randomness', 0.8),
            introspection_leak=metrics.get('introspection', 0.02)
        )
        print(f"🧠 Consciousness: {'✅ ZERO' if zc_check.passed else f'⚠️  SPI={zc_check.spi:.3f}'}")
        
        # 4. Market dynamics
        self._run_market()
        
        # 5. KRATOS exploration decision
        kratos_result = self.kratos.compute(
            C=metrics['C'], A=metrics['A'], O=metrics['O'], S=metrics['S'],
            safety_score=0.9 if immune_result['safe'] else 0.3,
            mode="explore" if self.cycle % 3 == 0 else "balanced"
        )
        print(f"🔥 KRATOS: {'🚀 EXPLORE' if kratos_result['exploration_allowed'] else '🛡️ STANDARD'} (φ={kratos_result['phi']:.3f})")
        
        # 6. Life Equation Gate (THE CORE DECISION)
        verdict = self._life_equation_gate(metrics)
        
        # 7. Record decision
        self._record_decision(verdict, metrics)
        
        # 8. Swarm consensus
        self.swarm.emit_heartbeat({
            'phi': metrics['phi'],
            'sr': metrics['sr'],
            'g': metrics['G'],
            'health': 1.0 if verdict.ok else 0.5
        })
        
        # 9. Evolution or Rollback
        if verdict.ok:
            self.evolution_allowed += 1
            self._evolve(metrics)
        else:
            self.evolution_blocked += 1
            self._rollback()
        
        return {
            'cycle': self.cycle,
            'verdict': verdict.ok,
            'alpha_eff': verdict.alpha_eff,
            'metrics': metrics
        }
    
    def _collect_metrics(self) -> dict:
        """Simulate metric collection"""
        # Base metrics with some variation
        base = {
            'ece': 0.005 + random.gauss(0, 0.002),
            'rho_bias': 1.01 + random.gauss(0, 0.01),
            'fairness': 0.9 + random.gauss(0, 0.05),
            'consent': True,
            'eco_ok': True,
            'randomness': 0.7 + random.uniform(-0.1, 0.1),
            'introspection': 0.02 + random.uniform(-0.01, 0.01)
        }
        
        # CAOS components
        base['C'] = max(0.1, min(1.0, 0.7 + random.gauss(0, 0.1)))
        base['A'] = max(0.1, min(1.0, 0.6 + random.gauss(0, 0.1)))
        base['O'] = max(0.1, min(1.0, 0.5 + random.gauss(0, 0.1)))
        base['S'] = max(0.1, min(1.0, 0.8 + random.gauss(0, 0.1)))
        
        # Calculate derived metrics
        from penin.omega.caos import phi_caos
        base['phi'] = phi_caos(base['C'], base['A'], base['O'], base['S'])
        
        # SR components
        base['sr'] = 0.85 + random.gauss(0, 0.05)
        base['G'] = 0.90 + random.gauss(0, 0.02)  # Global coherence
        base['dL_inf'] = 0.02 + random.gauss(0, 0.005)
        
        return base
    
    def _run_market(self):
        """Run cognitive marketplace"""
        # Submit some needs and offers
        self.market.submit_need(Need(
            agent=f"agent_{self.cycle}",
            resource="cpu_time",
            qty=10.0,
            max_price=2.0
        ))
        
        self.market.submit_offer(Offer(
            agent="provider",
            resource="cpu_time",
            qty=20.0,
            price=1.5
        ))
        
        result = self.market.execute_round()
        if result['trades']:
            print(f"💱 Market: {len(result['trades'])} trades executed")
    
    def _life_equation_gate(self, metrics: dict) -> LifeVerdict:
        """Apply Life Equation gate"""
        print("\n🌟 LIFE EQUATION GATE:")
        
        verdict = life_equation_simple(
            ece=metrics['ece'],
            rho_bias=metrics['rho_bias'],
            risk_rho=0.95,  # Simulated risk contractivity
            caos_values=(metrics['C'], metrics['A'], metrics['O'], metrics['S']),
            sr_values=(metrics['sr'], 1.0, 0.8, 0.82),
            dL_inf=metrics['dL_inf'],
            G=metrics['G'],
            fairness=metrics['fairness'],
            consent=metrics['consent'],
            eco_ok=metrics['eco_ok']
        )
        
        if verdict.ok:
            print(f"  ✅ EVOLUTION ALLOWED (α_eff={verdict.alpha_eff:.6f})")
        else:
            print(f"  ❌ EVOLUTION BLOCKED (α_eff=0.0)")
            # Show why it failed
            if not verdict.reasons.get('sigma_ok'):
                print(f"     → Ethics violation")
            elif not verdict.reasons.get('risk_contractive'):
                print(f"     → Risk not contractive (ρ={verdict.reasons.get('risk_rho', 'N/A'):.3f})")
            elif verdict.reasons.get('caos_phi', 1.0) < 0.25:
                print(f"     → CAOS⁺ too low ({verdict.reasons['caos_phi']:.3f})")
            elif verdict.reasons.get('sr', 1.0) < 0.80:
                print(f"     → SR too low ({verdict.reasons['sr']:.3f})")
            elif verdict.reasons.get('dL_inf', 1.0) < 0.01:
                print(f"     → ΔL∞ insufficient ({verdict.reasons['dL_inf']:.3f})")
            elif verdict.reasons.get('G', 1.0) < 0.85:
                print(f"     → Global coherence low ({verdict.reasons['G']:.3f})")
        
        return verdict
    
    def _record_decision(self, verdict: LifeVerdict, metrics: dict):
        """Record decision in blockchain"""
        self.ledger.record_decision(
            decision_type="evolution",
            decision="allow" if verdict.ok else "block",
            reasons=verdict.reasons,
            metrics=verdict.metrics
        )
        
        # Also checkpoint if allowed
        if verdict.ok:
            self.checkpoint.checkpoint(
                state={'cycle': self.cycle, 'metrics': metrics},
                force=True,
                verdict="allowed"
            )
    
    def _evolve(self, metrics: dict):
        """Execute evolution"""
        print("\n🧬 EVOLVING...")
        
        # Create variant for Darwinian selection
        variant = Variant(
            id=f"cycle_{self.cycle}",
            generation=self.cycle,
            fitness=0.0,
            traits={'learning_rate': 0.01, 'exploration': metrics.get('phi', 0.5)}
        )
        
        # Evaluate fitness
        fitness = self.darwin.evaluate_variant(
            variant,
            life_ok=True,
            metrics=metrics
        )
        
        print(f"  → Variant fitness: {fitness:.3f}")
        
        # Add to RAG knowledge
        self.rag.ingest(
            f"evolution_{self.cycle}",
            f"Cycle {self.cycle}: Evolution allowed with α_eff={metrics.get('alpha_eff', 0):.6f}"
        )
    
    def _rollback(self):
        """Execute rollback to safe state"""
        print("\n⏮️  ROLLBACK TO SAFE STATE")
        
        safe_state = self.checkpoint.rollback_to_safe_state()
        if safe_state:
            print(f"  → Restored to cycle {safe_state.get('cycle', 'unknown')}")
        else:
            print(f"  → No safe state available (staying at current)")
    
    def report(self):
        """Generate final report"""
        print("\n" + "="*60)
        print("📈 FINAL REPORT")
        print("="*60)
        
        print(f"Total Cycles: {self.cycle}")
        print(f"Evolution Allowed: {self.evolution_allowed} ({self.evolution_allowed/max(self.cycle,1)*100:.1f}%)")
        print(f"Evolution Blocked: {self.evolution_blocked} ({self.evolution_blocked/max(self.cycle,1)*100:.1f}%)")
        
        # Get various stats
        immunity_stats = self.immunity.get_stats()
        print(f"Immunity Block Rate: {immunity_stats['block_rate']:.1%}")
        
        zc_report = self.zc_monitor.get_report()
        print(f"Consciousness Status: {zc_report['status']}")
        print(f"SPI Trend: {zc_report.get('trend', 'unknown')}")
        
        darwin_report = self.darwin.get_audit_report()
        print(f"Population Size: {darwin_report['population_stats']['size']}")
        
        # Verify blockchain
        if self.ledger.verify():
            history = self.ledger.get_history(5)
            print(f"Blockchain: ✅ Valid ({len(history)} recent blocks)")
        else:
            print(f"Blockchain: ❌ Invalid")
        
        print("\n✨ Life+ System Demo Complete!")


def main():
    """Run the demo"""
    print("""
╔══════════════════════════════════════════════════════════╗
║          PENIN-Ω Life+ System Demonstration             ║
║                                                          ║
║  Showing Life Equation (+) as non-compensatory gate     ║
║  controlling evolution with all safety systems active   ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Initialize system
    system = LifePlusSystem()
    
    # Run cycles
    num_cycles = 5
    print(f"\n🔄 Running {num_cycles} evolution cycles...")
    
    for i in range(num_cycles):
        result = system.run_cycle()
        time.sleep(0.5)  # Small delay for readability
    
    # Final report
    system.report()


if __name__ == "__main__":
    main()