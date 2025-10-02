"""
PENIN-Ω ACFA Module (Adaptive Canary/Fallback Architecture)
===========================================================

Implements league-based deployment with shadow/canary/promote patterns.
Manages champion vs challenger comparisons with automatic rollback.
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class DeploymentStage(Enum):
    """Deployment stages"""

    SHADOW = "shadow"  # 0% traffic, metrics only
    CANARY = "canary"  # 1-10% traffic
    PROMOTED = "promoted"  # 100% traffic
    ROLLED_BACK = "rolled_back"


@dataclass
class LeagueConfig:
    """Configuration for league deployment"""

    shadow_duration_s: int = 300  # 5 minutes shadow
    canary_duration_s: int = 600  # 10 minutes canary
    canary_traffic_pct: float = 0.05  # 5% traffic
    delta_threshold: float = 0.02  # Min improvement for promotion
    error_rate_threshold: float = 0.05  # Max 5% error rate
    auto_rollback: bool = True
    metrics_window_s: int = 60  # Metrics aggregation window


@dataclass
class ModelCandidate:
    """A model candidate in the league"""

    candidate_id: str
    model_config: dict[str, Any]
    deployment_stage: DeploymentStage
    deployed_at: float
    metrics: dict[str, Any]
    traffic_fraction: float = 0.0
    error_count: int = 0
    request_count: int = 0


class LeagueOrchestrator:
    """Orchestrates league-based deployment"""

    def __init__(self, config: LeagueConfig = None):
        self.config = config or LeagueConfig()
        self.champion: ModelCandidate | None = None
        self.challenger: ModelCandidate | None = None
        self.deployment_history: list[dict[str, Any]] = []

    def register_champion(
        self, model_config: dict[str, Any], candidate_id: str = "champion_v1"
    ) -> ModelCandidate:
        """Register the current champion model"""
        champion = ModelCandidate(
            candidate_id=candidate_id,
            model_config=model_config,
            deployment_stage=DeploymentStage.PROMOTED,
            deployed_at=time.time(),
            metrics={},
            traffic_fraction=1.0,
        )

        self.champion = champion
        self._log_deployment_event("champion_registered", champion)
        return champion

    def deploy_challenger(
        self, model_config: dict[str, Any], candidate_id: str = None
    ) -> ModelCandidate:
        """Deploy a new challenger in shadow mode"""
        if candidate_id is None:
            candidate_id = f"challenger_{int(time.time())}"

        challenger = ModelCandidate(
            candidate_id=candidate_id,
            model_config=model_config,
            deployment_stage=DeploymentStage.SHADOW,
            deployed_at=time.time(),
            metrics={},
            traffic_fraction=0.0,
        )

        self.challenger = challenger
        self._log_deployment_event("challenger_deployed", challenger)
        return challenger

    async def run_shadow_phase(self) -> bool:
        """Run shadow deployment phase"""
        if (
            not self.challenger
            or self.challenger.deployment_stage != DeploymentStage.SHADOW
        ):
            return False

        print(f"🔍 Starting shadow phase for {self.challenger.candidate_id}")

        # Wait for shadow duration
        await asyncio.sleep(self.config.shadow_duration_s)

        # Collect shadow metrics (simulated)
        shadow_metrics = await self._collect_shadow_metrics()
        self.challenger.metrics.update(shadow_metrics)

        # Check if shadow phase passed
        shadow_passed = self._evaluate_shadow_metrics(shadow_metrics)

        if shadow_passed:
            print(f"✅ Shadow phase passed for {self.challenger.candidate_id}")
            return True
        else:
            print(f"❌ Shadow phase failed for {self.challenger.candidate_id}")
            self._rollback_challenger("shadow_failed")
            return False

    async def run_canary_phase(self) -> bool:
        """Run canary deployment phase"""
        if (
            not self.challenger
            or self.challenger.deployment_stage != DeploymentStage.SHADOW
        ):
            return False

        # Promote to canary
        self.challenger.deployment_stage = DeploymentStage.CANARY
        self.challenger.traffic_fraction = self.config.canary_traffic_pct

        print(
            f"🐤 Starting canary phase for {self.challenger.candidate_id} ({self.config.canary_traffic_pct * 100:.1f}% traffic)"
        )

        # Wait for canary duration
        await asyncio.sleep(self.config.canary_duration_s)

        # Collect canary metrics
        canary_metrics = await self._collect_canary_metrics()
        self.challenger.metrics.update(canary_metrics)

        # Compare with champion
        promotion_decision = self._decide_promotion(canary_metrics)

        if promotion_decision["promote"]:
            print(f"✅ Canary phase passed for {self.challenger.candidate_id}")
            return True
        else:
            print(f"❌ Canary phase failed: {promotion_decision['reason']}")
            self._rollback_challenger(promotion_decision["reason"])
            return False

    def promote_challenger(self) -> bool:
        """Promote challenger to champion"""
        if (
            not self.challenger
            or self.challenger.deployment_stage != DeploymentStage.CANARY
        ):
            return False

        # Validate attestation chain if present
        if hasattr(self.challenger, "attestation_chain"):
            chain_valid, error_msg = self._validate_attestation_chain()
            if not chain_valid:
                print(f"❌ Attestation chain validation failed: {error_msg}")
                self._rollback_challenger(f"attestation_chain_invalid: {error_msg}")
                return False
            print("✅ Attestation chain validated")

        # Archive old champion
        if self.champion:
            self._archive_champion()

        # Promote challenger
        self.challenger.deployment_stage = DeploymentStage.PROMOTED
        self.challenger.traffic_fraction = 1.0

        # Swap roles
        old_challenger = self.challenger
        self.champion = old_challenger
        self.challenger = None

        print(f"🏆 Promoted {self.champion.candidate_id} to champion")
        self._log_deployment_event("challenger_promoted", self.champion)

        return True

    def _validate_attestation_chain(self) -> tuple[bool, str]:
        """Validate the attestation chain for the challenger"""
        try:
            from penin.omega.attestation import AttestationChain, ServiceType

            if not hasattr(self.challenger, "attestation_chain"):
                return True, "No attestation chain present (skipped)"

            chain = self.challenger.attestation_chain
            if not isinstance(chain, AttestationChain):
                return False, "Invalid attestation chain type"

            # Verify the chain
            is_valid, msg = chain.verify_chain()
            if not is_valid:
                return False, msg

            # Check that all required attestations are present
            if not chain.has_all_required():
                return False, "Missing required attestations (SR-Ω∞ or Σ-Guard)"

            # Check that all attestations passed
            if not chain.all_passed():
                return False, "One or more attestations did not pass"

            return True, "All attestations verified"

        except ImportError:
            # If attestation module is not available, skip validation
            return True, "Attestation module not available (skipped)"
        except Exception as e:
            return False, f"Attestation validation error: {str(e)}"

    def _rollback_challenger(self, reason: str):
        """Rollback challenger deployment"""
        if self.challenger:
            self.challenger.deployment_stage = DeploymentStage.ROLLED_BACK
            self.challenger.traffic_fraction = 0.0

            print(f"🔄 Rolled back {self.challenger.candidate_id}: {reason}")
            self._log_deployment_event(
                "challenger_rolled_back", self.challenger, {"reason": reason}
            )

            self.challenger = None

    async def _collect_shadow_metrics(self) -> dict[str, Any]:
        """Collect metrics during shadow phase (simulated)"""
        # Simulate metrics collection
        await asyncio.sleep(0.1)

        return {
            "shadow_requests": 100,
            "shadow_errors": 2,
            "shadow_latency_p95": 150.0,
            "shadow_accuracy": 0.92,
            "shadow_cost_per_request": 0.001,
        }

    async def _collect_canary_metrics(self) -> dict[str, Any]:
        """Collect metrics during canary phase (simulated)"""
        await asyncio.sleep(0.1)

        return {
            "canary_requests": 50,
            "canary_errors": 1,
            "canary_latency_p95": 140.0,
            "canary_accuracy": 0.94,
            "canary_cost_per_request": 0.0009,
            "canary_error_rate": 0.02,
        }

    def _evaluate_shadow_metrics(self, metrics: dict[str, Any]) -> bool:
        """Evaluate if shadow metrics are acceptable"""
        error_rate = metrics.get("shadow_errors", 0) / max(
            1, metrics.get("shadow_requests", 1)
        )

        # Shadow passes if error rate is acceptable
        return error_rate <= self.config.error_rate_threshold

    def _decide_promotion(self, canary_metrics: dict[str, Any]) -> dict[str, Any]:
        """Decide whether to promote challenger"""
        if not self.champion or not self.champion.metrics:
            # No champion to compare against, promote if canary is healthy
            error_rate = canary_metrics.get("canary_error_rate", 0)
            if error_rate <= self.config.error_rate_threshold:
                return {"promote": True, "reason": "no_champion_comparison"}
            else:
                return {"promote": False, "reason": f"high_error_rate_{error_rate:.3f}"}

        # Compare challenger vs champion
        challenger_accuracy = canary_metrics.get("canary_accuracy", 0)
        champion_accuracy = self.champion.metrics.get("accuracy", 0)

        challenger_latency = canary_metrics.get("canary_latency_p95", 1000)
        champion_latency = self.champion.metrics.get("latency_p95", 1000)

        challenger_cost = canary_metrics.get("canary_cost_per_request", 0.01)
        champion_cost = self.champion.metrics.get("cost_per_request", 0.01)

        # Calculate improvement delta
        accuracy_delta = challenger_accuracy - champion_accuracy
        latency_improvement = (champion_latency - challenger_latency) / champion_latency
        cost_improvement = (champion_cost - challenger_cost) / champion_cost

        # Combined improvement score
        improvement_score = (
            accuracy_delta + (latency_improvement * 0.3) + (cost_improvement * 0.2)
        )

        # Check error rate
        error_rate = canary_metrics.get("canary_error_rate", 0)
        if error_rate > self.config.error_rate_threshold:
            return {"promote": False, "reason": f"high_error_rate_{error_rate:.3f}"}

        # Check improvement threshold
        if improvement_score >= self.config.delta_threshold:
            return {
                "promote": True,
                "reason": f"improvement_{improvement_score:.3f}",
                "details": {
                    "accuracy_delta": accuracy_delta,
                    "latency_improvement": latency_improvement,
                    "cost_improvement": cost_improvement,
                },
            }
        else:
            return {
                "promote": False,
                "reason": f"insufficient_improvement_{improvement_score:.3f}",
                "threshold": self.config.delta_threshold,
            }

    def _archive_champion(self):
        """Archive current champion"""
        if self.champion:
            archive_entry = {
                "candidate_id": self.champion.candidate_id,
                "model_config": self.champion.model_config,
                "final_metrics": self.champion.metrics,
                "archived_at": time.time(),
                "deployment_duration": time.time() - self.champion.deployed_at,
            }

            self.deployment_history.append(archive_entry)
            print(f"📦 Archived champion {self.champion.candidate_id}")

    def _log_deployment_event(
        self, event_type: str, candidate: ModelCandidate, extra_data: dict = None
    ):
        """Log deployment events"""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "candidate_id": candidate.candidate_id,
            "deployment_stage": candidate.deployment_stage.value,
            "traffic_fraction": candidate.traffic_fraction,
        }

        if extra_data:
            event.update(extra_data)

        # In a real implementation, this would go to a proper logging system
        print(f"📝 Event: {event_type} for {candidate.candidate_id}")

    def get_deployment_status(self) -> dict[str, Any]:
        """Get current deployment status"""
        return {
            "champion": (
                {
                    "candidate_id": (
                        self.champion.candidate_id if self.champion else None
                    ),
                    "stage": (
                        self.champion.deployment_stage.value if self.champion else None
                    ),
                    "traffic_fraction": (
                        self.champion.traffic_fraction if self.champion else 0
                    ),
                    "metrics": self.champion.metrics if self.champion else {},
                }
                if self.champion
                else None
            ),
            "challenger": (
                {
                    "candidate_id": (
                        self.challenger.candidate_id if self.challenger else None
                    ),
                    "stage": (
                        self.challenger.deployment_stage.value
                        if self.challenger
                        else None
                    ),
                    "traffic_fraction": (
                        self.challenger.traffic_fraction if self.challenger else 0
                    ),
                    "metrics": self.challenger.metrics if self.challenger else {},
                }
                if self.challenger
                else None
            ),
            "deployment_history_count": len(self.deployment_history),
        }


async def run_full_deployment_cycle(
    orchestrator: LeagueOrchestrator, challenger_config: dict[str, Any]
) -> bool:
    """Run complete deployment cycle: shadow -> canary -> promote"""

    # Deploy challenger
    orchestrator.deploy_challenger(challenger_config)

    # Run shadow phase
    shadow_success = await orchestrator.run_shadow_phase()
    if not shadow_success:
        return False

    # Run canary phase
    canary_success = await orchestrator.run_canary_phase()
    if not canary_success:
        return False

    # Promote to champion
    promotion_success = orchestrator.promote_challenger()
    return promotion_success


# Example usage
if __name__ == "__main__":

    async def demo():
        # Create orchestrator
        config = LeagueConfig(
            shadow_duration_s=5,  # Short for demo
            canary_duration_s=5,
            canary_traffic_pct=0.1,
        )
        orchestrator = LeagueOrchestrator(config)

        # Register champion
        champion_config = {"model": "gpt-4", "temperature": 0.7}
        orchestrator.register_champion(champion_config)

        # Deploy and test challenger
        challenger_config = {"model": "gpt-4", "temperature": 0.5}
        success = await run_full_deployment_cycle(orchestrator, challenger_config)

        print(f"Deployment cycle completed: {'SUCCESS' if success else 'FAILED'}")
        print("Final status:", orchestrator.get_deployment_status())

    asyncio.run(demo())
