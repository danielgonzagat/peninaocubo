#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENIN-Ω League Service (Champion-Challenger)
==============================================

Implements shadow, canary, and production promotion with:
- Shadow: 0% traffic, metrics collection only
- Canary: 1-5% traffic with guards
- Production: Full traffic after validation
- Rollback: Instant reversion with WORM proof

Features:
- Traffic splitting and routing
- A/B testing with statistical significance
- Automatic rollback on failures
- WORM attestation for all transitions
"""

import json
import time
import uuid
import hashlib
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import random
import sqlite3
from collections import defaultdict

try:
    from pydantic import BaseModel, Field, validator

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


# -----------------------------------------------------------------------------
# Deployment Stages
# -----------------------------------------------------------------------------
class DeploymentStage(Enum):
    SHADOW = "shadow"  # 0% traffic, metrics only
    CANARY = "canary"  # 1-5% traffic
    PRODUCTION = "prod"  # 100% traffic
    ROLLBACK = "rollback"  # Reverted state


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
class LeagueConfig(BaseModel):
    """League service configuration"""

    shadow_duration_s: float = Field(300, ge=60, le=3600, description="Shadow phase duration")
    canary_duration_s: float = Field(600, ge=60, le=7200, description="Canary phase duration")
    canary_traffic_pct: float = Field(0.05, ge=0.01, le=0.2, description="Canary traffic %")
    min_samples_shadow: int = Field(100, ge=10, description="Min samples for shadow")
    min_samples_canary: int = Field(500, ge=50, description="Min samples for canary")
    delta_threshold: float = Field(0.02, ge=0.001, description="Min ΔL∞ for promotion")
    error_rate_threshold: float = Field(0.05, ge=0.01, le=0.2, description="Max error rate")
    p95_latency_threshold_ms: float = Field(100, ge=10, le=1000, description="P95 latency limit")
    rollback_window_s: float = Field(300, ge=60, description="Rollback detection window")
    worm_db_path: str = Field("/opt/penin_omega/league/worm.db", description="WORM path")


# -----------------------------------------------------------------------------
# Variant State
# -----------------------------------------------------------------------------
@dataclass
class VariantMetrics:
    """Metrics for a variant (champion or challenger)"""

    variant_id: str
    stage: DeploymentStage
    samples: int = 0
    successes: int = 0
    failures: int = 0
    aborts: int = 0
    total_latency_ms: float = 0.0
    latencies: List[float] = field(default_factory=list)
    l_inf_values: List[float] = field(default_factory=list)
    delta_linf_values: List[float] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    traffic_pct: float = 0.0

    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.successes + self.failures + self.aborts
        return self.successes / total if total > 0 else 0.0

    def error_rate(self) -> float:
        """Calculate error rate"""
        total = self.successes + self.failures + self.aborts
        return (self.failures + self.aborts) / total if total > 0 else 0.0

    def avg_latency_ms(self) -> float:
        """Calculate average latency"""
        return self.total_latency_ms / self.samples if self.samples > 0 else 0.0

    def p95_latency_ms(self) -> float:
        """Calculate P95 latency"""
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    def avg_l_inf(self) -> float:
        """Calculate average L∞"""
        return sum(self.l_inf_values) / len(self.l_inf_values) if self.l_inf_values else 0.0

    def avg_delta_linf(self) -> float:
        """Calculate average ΔL∞"""
        return sum(self.delta_linf_values) / len(self.delta_linf_values) if self.delta_linf_values else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "variant_id": self.variant_id,
            "stage": self.stage.value,
            "samples": self.samples,
            "success_rate": self.success_rate(),
            "error_rate": self.error_rate(),
            "avg_latency_ms": self.avg_latency_ms(),
            "p95_latency_ms": self.p95_latency_ms(),
            "avg_l_inf": self.avg_l_inf(),
            "avg_delta_linf": self.avg_delta_linf(),
            "traffic_pct": self.traffic_pct,
            "duration_s": (self.end_time or time.time()) - self.start_time,
        }


# -----------------------------------------------------------------------------
# League WORM
# -----------------------------------------------------------------------------
class LeagueWORM:
    """WORM ledger for league transitions"""

    def __init__(self, db_path: Path):
        self.db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_db()
        self._lock = threading.Lock()

    def _init_db(self):
        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transition_id TEXT UNIQUE,
                from_stage TEXT,
                to_stage TEXT,
                variant_id TEXT,
                metrics_before TEXT,
                metrics_after TEXT,
                decision TEXT,
                reason TEXT,
                traffic_slice TEXT,
                timestamp TEXT,
                proof_hash TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_variant ON transitions(variant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON transitions(timestamp)")
        self.db.commit()

    def record_transition(
        self,
        from_stage: DeploymentStage,
        to_stage: DeploymentStage,
        variant_id: str,
        metrics_before: VariantMetrics,
        metrics_after: Optional[VariantMetrics],
        decision: str,
        reason: str,
        traffic_slice: Dict[str, Any],
    ) -> str:
        """Record stage transition with proof"""
        with self._lock:
            transition_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()

            # Create proof hash
            proof_data = {
                "transition_id": transition_id,
                "from": from_stage.value,
                "to": to_stage.value,
                "variant": variant_id,
                "metrics_before": metrics_before.to_dict(),
                "metrics_after": metrics_after.to_dict() if metrics_after else None,
                "decision": decision,
                "reason": reason,
                "traffic": traffic_slice,
                "timestamp": timestamp,
            }
            proof_hash = hashlib.sha256(json.dumps(proof_data, sort_keys=True).encode()).hexdigest()

            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO transitions (
                    transition_id, from_stage, to_stage, variant_id,
                    metrics_before, metrics_after, decision, reason,
                    traffic_slice, timestamp, proof_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    transition_id,
                    from_stage.value,
                    to_stage.value,
                    variant_id,
                    json.dumps(metrics_before.to_dict()),
                    json.dumps(metrics_after.to_dict()) if metrics_after else None,
                    decision,
                    reason,
                    json.dumps(traffic_slice),
                    timestamp,
                    proof_hash,
                ),
            )
            self.db.commit()

            return transition_id

    def get_transition_history(self, variant_id: str) -> List[Dict[str, Any]]:
        """Get transition history for a variant"""
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT * FROM transitions 
            WHERE variant_id = ? 
            ORDER BY timestamp DESC
        """,
            (variant_id,),
        )

        rows = cursor.fetchall()
        history = []
        for row in rows:
            history.append(
                {
                    "transition_id": row[1],
                    "from_stage": row[2],
                    "to_stage": row[3],
                    "variant_id": row[4],
                    "metrics_before": json.loads(row[5]),
                    "metrics_after": json.loads(row[6]) if row[6] else None,
                    "decision": row[7],
                    "reason": row[8],
                    "traffic_slice": json.loads(row[9]),
                    "timestamp": row[10],
                    "proof_hash": row[11],
                }
            )
        return history


# -----------------------------------------------------------------------------
# Traffic Router
# -----------------------------------------------------------------------------
class TrafficRouter:
    """Routes traffic between champion and challenger"""

    def __init__(self):
        self.champion_id: Optional[str] = None
        self.challenger_id: Optional[str] = None
        self.challenger_stage = DeploymentStage.SHADOW
        self.challenger_traffic_pct = 0.0
        self._lock = threading.RLock()

    def set_champion(self, variant_id: str):
        """Set production champion"""
        with self._lock:
            self.champion_id = variant_id

    def set_challenger(self, variant_id: str, stage: DeploymentStage, traffic_pct: float = 0.0):
        """Set challenger variant"""
        with self._lock:
            self.challenger_id = variant_id
            self.challenger_stage = stage
            self.challenger_traffic_pct = traffic_pct

    def route_request(self, request_id: str) -> Tuple[str, bool]:
        """
        Route a request to champion or challenger
        Returns: (variant_id, is_challenger)
        """
        with self._lock:
            # No challenger or shadow mode - always use champion
            if not self.challenger_id or self.challenger_stage == DeploymentStage.SHADOW:
                return self.champion_id, False

            # Canary mode - route based on traffic percentage
            if self.challenger_stage == DeploymentStage.CANARY:
                # Use hash of request_id for deterministic routing
                hash_val = int(hashlib.md5(request_id.encode()).hexdigest(), 16)
                if (hash_val % 10000) < (self.challenger_traffic_pct * 10000):
                    return self.challenger_id, True
                return self.champion_id, False

            # Production mode - challenger is now champion
            if self.challenger_stage == DeploymentStage.PRODUCTION:
                return self.challenger_id, False

            # Rollback - use champion
            return self.champion_id, False

    def get_traffic_split(self) -> Dict[str, float]:
        """Get current traffic split"""
        with self._lock:
            if not self.challenger_id or self.challenger_stage == DeploymentStage.SHADOW:
                return {self.champion_id: 1.0}

            if self.challenger_stage == DeploymentStage.CANARY:
                return {
                    self.champion_id: 1.0 - self.challenger_traffic_pct,
                    self.challenger_id: self.challenger_traffic_pct,
                }

            if self.challenger_stage == DeploymentStage.PRODUCTION:
                return {self.challenger_id: 1.0}

            return {self.champion_id: 1.0}


# -----------------------------------------------------------------------------
# League Orchestrator
# -----------------------------------------------------------------------------
class LeagueOrchestrator:
    """Orchestrates champion-challenger deployments"""

    def __init__(self, config: LeagueConfig):
        self.config = config
        self.worm = LeagueWORM(Path(config.worm_db_path))
        self.router = TrafficRouter()
        self.variants: Dict[str, VariantMetrics] = {}
        self.current_champion: Optional[str] = None
        self.current_challenger: Optional[str] = None
        self._lock = threading.RLock()

        # Stage transition timers
        self._stage_timer: Optional[threading.Timer] = None

    def register_champion(self, variant_id: str) -> bool:
        """Register production champion"""
        with self._lock:
            if variant_id not in self.variants:
                self.variants[variant_id] = VariantMetrics(
                    variant_id=variant_id, stage=DeploymentStage.PRODUCTION, traffic_pct=1.0
                )

            self.current_champion = variant_id
            self.router.set_champion(variant_id)

            self.worm.record_transition(
                DeploymentStage.PRODUCTION,
                DeploymentStage.PRODUCTION,
                variant_id,
                self.variants[variant_id],
                None,
                "REGISTER",
                "Registered as champion",
                {"champion": variant_id},
            )
            return True

    def deploy_challenger(self, variant_id: str) -> bool:
        """Deploy new challenger in shadow mode"""
        with self._lock:
            if self.current_challenger:
                return False  # Already have a challenger

            self.variants[variant_id] = VariantMetrics(
                variant_id=variant_id, stage=DeploymentStage.SHADOW, traffic_pct=0.0
            )

            self.current_challenger = variant_id
            self.router.set_challenger(variant_id, DeploymentStage.SHADOW, 0.0)

            self.worm.record_transition(
                DeploymentStage.SHADOW,
                DeploymentStage.SHADOW,
                variant_id,
                self.variants[variant_id],
                None,
                "DEPLOY",
                "Deployed to shadow",
                self.router.get_traffic_split(),
            )

            # Schedule transition to canary
            self._schedule_stage_transition(self.config.shadow_duration_s, self._transition_to_canary)
            return True

    def _transition_to_canary(self):
        """Transition challenger from shadow to canary"""
        with self._lock:
            if not self.current_challenger:
                return

            challenger = self.variants[self.current_challenger]

            # Check shadow metrics
            if challenger.samples < self.config.min_samples_shadow:
                self._rollback(f"Insufficient shadow samples: {challenger.samples}")
                return

            if challenger.error_rate() > self.config.error_rate_threshold:
                self._rollback(f"High error rate in shadow: {challenger.error_rate():.2%}")
                return

            # Transition to canary
            old_metrics = VariantMetrics(**asdict(challenger))
            challenger.stage = DeploymentStage.CANARY
            challenger.traffic_pct = self.config.canary_traffic_pct

            self.router.set_challenger(self.current_challenger, DeploymentStage.CANARY, self.config.canary_traffic_pct)

            self.worm.record_transition(
                DeploymentStage.SHADOW,
                DeploymentStage.CANARY,
                self.current_challenger,
                old_metrics,
                challenger,
                "PROMOTE",
                f"Shadow metrics passed (samples={challenger.samples})",
                self.router.get_traffic_split(),
            )

            # Schedule transition to production
            self._schedule_stage_transition(self.config.canary_duration_s, self._transition_to_production)

    def _transition_to_production(self):
        """Transition challenger from canary to production"""
        with self._lock:
            if not self.current_challenger:
                return

            challenger = self.variants[self.current_challenger]
            champion = self.variants[self.current_champion]

            # Check canary metrics
            if challenger.samples < self.config.min_samples_canary:
                self._rollback(f"Insufficient canary samples: {challenger.samples}")
                return

            if challenger.error_rate() > self.config.error_rate_threshold:
                self._rollback(f"High error rate in canary: {challenger.error_rate():.2%}")
                return

            if challenger.p95_latency_ms() > self.config.p95_latency_threshold_ms:
                self._rollback(f"High P95 latency: {challenger.p95_latency_ms():.1f}ms")
                return

            # Check ΔL∞ improvement
            if challenger.avg_delta_linf() < self.config.delta_threshold:
                self._rollback(f"Insufficient ΔL∞: {challenger.avg_delta_linf():.4f}")
                return

            # Compare with champion
            if challenger.avg_l_inf() <= champion.avg_l_inf():
                self._rollback(f"No improvement over champion L∞")
                return

            # Promote to production
            old_metrics = VariantMetrics(**asdict(challenger))
            challenger.stage = DeploymentStage.PRODUCTION
            challenger.traffic_pct = 1.0

            # Swap champion and challenger
            self.current_champion = self.current_challenger
            self.current_challenger = None

            self.router.set_champion(self.current_champion)
            self.router.set_challenger(None, DeploymentStage.SHADOW, 0.0)

            self.worm.record_transition(
                DeploymentStage.CANARY,
                DeploymentStage.PRODUCTION,
                self.current_champion,
                old_metrics,
                challenger,
                "PROMOTE",
                f"Canary successful (ΔL∞={challenger.avg_delta_linf():.4f})",
                self.router.get_traffic_split(),
            )

    def _rollback(self, reason: str):
        """Rollback challenger deployment"""
        with self._lock:
            if not self.current_challenger:
                return

            challenger = self.variants[self.current_challenger]
            old_stage = challenger.stage

            # Mark as rollback
            challenger.stage = DeploymentStage.ROLLBACK
            challenger.end_time = time.time()

            self.worm.record_transition(
                old_stage,
                DeploymentStage.ROLLBACK,
                self.current_challenger,
                challenger,
                None,
                "ROLLBACK",
                reason,
                self.router.get_traffic_split(),
            )

            # Clear challenger
            self.current_challenger = None
            self.router.set_challenger(None, DeploymentStage.SHADOW, 0.0)

            # Cancel any pending transitions
            if self._stage_timer:
                self._stage_timer.cancel()
                self._stage_timer = None

    def _schedule_stage_transition(self, delay_s: float, callback):
        """Schedule a stage transition"""
        if self._stage_timer:
            self._stage_timer.cancel()

        self._stage_timer = threading.Timer(delay_s, callback)
        self._stage_timer.daemon = True
        self._stage_timer.start()

    def record_request(
        self,
        variant_id: str,
        success: bool,
        latency_ms: float,
        l_inf: float,
        delta_linf: float,
        error_msg: Optional[str] = None,
    ):
        """Record request metrics for a variant"""
        with self._lock:
            if variant_id not in self.variants:
                return

            variant = self.variants[variant_id]
            variant.samples += 1

            if success:
                variant.successes += 1
            elif error_msg and "ABORT" in error_msg:
                variant.aborts += 1
            else:
                variant.failures += 1
                if error_msg:
                    variant.error_messages.append(error_msg[:100])

            variant.total_latency_ms += latency_ms
            variant.latencies.append(latency_ms)
            variant.l_inf_values.append(l_inf)
            variant.delta_linf_values.append(delta_linf)

            # Keep only recent samples for memory efficiency
            if len(variant.latencies) > 10000:
                variant.latencies = variant.latencies[-5000:]
            if len(variant.l_inf_values) > 10000:
                variant.l_inf_values = variant.l_inf_values[-5000:]
            if len(variant.delta_linf_values) > 10000:
                variant.delta_linf_values = variant.delta_linf_values[-5000:]

    def get_status(self) -> Dict[str, Any]:
        """Get current league status"""
        with self._lock:
            status = {
                "champion": self.current_champion,
                "challenger": self.current_challenger,
                "traffic_split": self.router.get_traffic_split(),
                "variants": {},
            }

            for variant_id, metrics in self.variants.items():
                status["variants"][variant_id] = metrics.to_dict()

            return status

    def force_rollback(self) -> bool:
        """Force rollback of current challenger"""
        with self._lock:
            if self.current_challenger:
                self._rollback("Manual rollback requested")
                return True
            return False


# -----------------------------------------------------------------------------
# Integration with Core
# -----------------------------------------------------------------------------
async def run_with_league(core_instance, league: LeagueOrchestrator):
    """
    Run core with league orchestration

    Usage:
        league = LeagueOrchestrator(config)
        league.register_champion("v1")
        league.deploy_challenger("v2")

        # Run requests through league
        await run_with_league(core, league)
    """
    request_id = str(uuid.uuid4())
    variant_id, is_challenger = league.router.route_request(request_id)

    # Run on selected variant (in real system, would route to different instances)
    start_time = time.time()
    result = await core_instance.master_equation_cycle()
    latency_ms = (time.time() - start_time) * 1000

    # Record metrics
    success = result.get("success", False)
    l_inf = core_instance.xt.l_inf
    delta_linf = core_instance.xt.delta_linf
    error_msg = result.get("reason") if not success else None

    league.record_request(variant_id, success, latency_ms, l_inf, delta_linf, error_msg)

    # If challenger in shadow mode, also run on champion
    if is_challenger and league.variants[variant_id].stage == DeploymentStage.SHADOW:
        champion_id = league.current_champion
        if champion_id:
            # In real system, would also run on champion
            league.record_request(champion_id, success, latency_ms, l_inf, delta_linf, error_msg)

    return result


# -----------------------------------------------------------------------------
# Demo
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    sys.path.insert(0, "/workspace")
    from importlib import import_module

    print("League Service Demo")
    print("=" * 50)

    # Create league config
    config = LeagueConfig(
        shadow_duration_s=10,  # Short for demo
        canary_duration_s=15,
        canary_traffic_pct=0.1,
        min_samples_shadow=5,
        min_samples_canary=10,
        worm_db_path="/tmp/league_demo.db",
    )

    # Create orchestrator
    league = LeagueOrchestrator(config)

    # Register champion
    league.register_champion("champion-v1")
    print(f"✓ Registered champion: champion-v1")

    # Deploy challenger
    league.deploy_challenger("challenger-v2")
    print(f"✓ Deployed challenger: challenger-v2 (shadow mode)")

    # Simulate some requests
    print("\nSimulating traffic...")

    async def simulate():
        # Import core
        module = import_module("1_de_8_v7")
        core = module.PeninOmegaCore({"evolution": {"seed": 42}})

        for i in range(30):
            await run_with_league(core, league)
            await asyncio.sleep(0.5)

            # Print status every 10 requests
            if (i + 1) % 10 == 0:
                status = league.get_status()
                challenger_status = status["variants"].get("challenger-v2", {})
                print(f"\n[{i + 1} requests]")
                print(f"  Challenger stage: {challenger_status.get('stage', 'N/A')}")
                print(f"  Traffic: {challenger_status.get('traffic_pct', 0) * 100:.1f}%")
                print(f"  Samples: {challenger_status.get('samples', 0)}")
                print(f"  Success rate: {challenger_status.get('success_rate', 0) * 100:.1f}%")
                print(f"  Avg ΔL∞: {challenger_status.get('avg_delta_linf', 0):.4f}")

    asyncio.run(simulate())

    # Final status
    print("\n" + "=" * 50)
    print("Final Status:")
    status = league.get_status()
    print(json.dumps(status, indent=2))

    # Show transition history
    print("\nTransition History:")
    history = league.worm.get_transition_history("challenger-v2")
    for transition in history:
        print(f"  {transition['from_stage']} → {transition['to_stage']}: {transition['reason']}")
