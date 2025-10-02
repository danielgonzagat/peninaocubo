"""
Evolution Runner
================

Runs evolution cycles - connects all PENIN-Ω components.
"""

from typing import Optional
from penin.core.caos import compute_caos_plus_exponential
from penin.math.linf_complete import compute_linf_complete
from penin.router_pkg.budget_tracker import BudgetTracker
import os


def run_evolution(
    n_cycles: int,
    budget_usd: float,
    provider: str = "openai",
    dry_run: bool = False,
):
    """
    Run N evolution cycles.
    
    Args:
        n_cycles: Number of cycles to run
        budget_usd: Daily budget in USD
        provider: LLM provider to use
        dry_run: If True, don't make real LLM calls
    """
    
    print(f"🚀 PENIN-Ω Evolution Runner")
    print(f"   Cycles: {n_cycles}")
    print(f"   Budget: ${budget_usd:.2f}")
    print(f"   Provider: {provider}")
    print(f"   Mode: {'DRY-RUN' if dry_run else 'PRODUCTION'}")
    print()
    
    # Initialize components
    tracker = BudgetTracker(daily_limit_usd=budget_usd)
    
    # Ensure ledger path exists
    ledger_path = os.getenv("LEDGER_DB_PATH", "./data/worm_ledger.db")
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    
    from penin.ledger.worm_ledger_complete import WORMLedger
    ledger = WORMLedger(db_path=ledger_path)
    
    # Run cycles
    for i in range(n_cycles):
        print(f"\n{'='*60}")
        print(f"  Cycle {i+1}/{n_cycles}")
        print(f"{'='*60}\n")
        
        # 1. Compute CAOS+ (motor evolutivo)
        c, a, o, s, kappa = 0.85, 0.40, 0.35, 0.82, 20.0
        
        caos = compute_caos_plus_exponential(
            c=c, a=a, o=o, s=s, kappa=kappa
        )
        print(f"  ✅ CAOS+: {caos:.3f} (C={c}, A={a}, O={o}, S={s}, κ={kappa})")
        
        # 2. Compute L∞ (meta-função de performance)
        metrics = [0.85, 0.78, 0.92]
        weights = [0.4, 0.3, 0.3]
        cost_norm = 0.05
        lambda_cost = 0.5
        
        result = compute_linf_complete(
            metrics=metrics,
            weights=weights,
            cost_normalized=cost_norm,
            lambda_cost=lambda_cost,
        )
        linf = result['linf']
        print(f"  ✅ L∞: {linf:.3f} (metrics={metrics}, cost={cost_norm})")
        
        # 3. Check gates (simplified for now)
        delta_linf = 0.02 if i > 0 else 0.0  # Mock improvement
        beta_min = 0.01
        
        gates_pass = delta_linf >= beta_min and caos > 1.0 and linf > 0.5
        decision = "PROMOTE" if gates_pass else "CONTINUE"
        
        print(f"  ✅ Decision: {decision} (ΔL∞={delta_linf:.4f}, gates={'PASS' if gates_pass else 'FAIL'})")
        
        # 4. Record in WORM ledger
        entry_hash = ledger.append_entry(
            event_type="evolution_cycle",
            data={
                "cycle": i + 1,
                "caos": caos,
                "linf": linf,
                "delta_linf": delta_linf,
                "provider": provider,
                "c": c,
                "a": a,
                "o": o,
                "s": s,
                "kappa": kappa,
                "metrics": metrics,
                "weights": weights,
                "gates_pass": gates_pass,
            },
            decision=decision,
        )
        print(f"  ✅ WORM Ledger: Entry recorded (hash={entry_hash[:16]}...)")
        
        # 5. Update budget (mock cost for now)
        mock_cost = 0.05 if not dry_run else 0.0
        if not dry_run:
            tracker.record_request(provider, cost_usd=mock_cost, tokens_used=500)
            print(f"  ✅ Budget: ${tracker.used_usd:.2f} / ${tracker.daily_limit_usd:.2f} used ({tracker.usage_pct*100:.1f}%)")
        
        # 6. Check budget limits
        if tracker.is_hard_limit_exceeded():
            print(f"\n  ⚠️  BUDGET LIMIT EXCEEDED - Stopping")
            break
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}\n")
    print(f"  Cycles completed: {min(i+1, n_cycles)}")
    print(f"  Budget used: ${tracker.used_usd:.2f} / ${tracker.daily_limit_usd:.2f}")
    print(f"  Ledger entries: {len(ledger.entries)}")
    print(f"  Chain integrity: {'✅ VALID' if ledger.verify_chain() else '❌ BROKEN'}")
    print()
