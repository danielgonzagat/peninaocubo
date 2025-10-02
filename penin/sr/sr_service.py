"""
PENIN-Ω SR-Ω∞ Service — Self-Reflection & Metacognition
==========================================================

Implements SR-Ω∞ scoring with 4-dimensional assessment:

1. **Autoconsciência (Awareness)**: Calibration & introspection
2. **Ética (Ethics)**: ΣEA/LO-14 & IR→IC compliance
3. **Autocorreção (Autocorrection)**: Risk reduction trajectory
4. **Metacognição (Metacognition)**: ΔL∞/ΔCost efficiency

Formula (non-compensatory):
    R_t = harmonic_mean([awareness, ethics_ok, autocorr, metacog])

References:
- PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md § 4
- Blueprint § 3, § 8
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

try:
    from penin.ethics.laws import EthicalValidator
except ImportError:
    EthicalValidator = None


# ============================================================================
# SR Score Components
# ============================================================================


@dataclass
class SRScore:
    """
    Complete SR-Ω∞ score with all components.
    
    Formula:
        R_t = harmonic_mean([awareness, ethics, autocorr, metacog])
        
    Where:
    - awareness ∈ [0, 1]: Calibration quality (1 - ECE)
    - ethics ∈ {0, 1}: Binary gate (ΣEA/LO-14 compliance)
    - autocorr ∈ [0, 1]: Risk reduction (1 - ρ)
    - metacog ∈ [0, 1]: Efficiency (ΔL∞ / ΔCost)
    """
    
    awareness: float  # Calibration (1 - ECE)
    ethics_ok: bool  # Binary gate
    autocorrection: float  # Risk reduction
    metacognition: float  # Efficiency
    
    # Computed
    sr_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    
    # Metadata
    ece: float = 0.0
    rho: float = 1.0
    delta_linf: float = 0.0
    delta_cost: float = 0.0
    
    def __post_init__(self):
        """Compute SR-Ω∞ score on initialization."""
        if self.sr_score == 0.0:
            self.sr_score = compute_sr_score(
                awareness=self.awareness,
                ethics_ok=self.ethics_ok,
                autocorrection=self.autocorrection,
                metacognition=self.metacognition,
            )


def compute_sr_score(
    awareness: float,
    ethics_ok: bool,
    autocorrection: float,
    metacognition: float,
    eps: float = 1e-6,
) -> float:
    """
    Compute SR-Ω∞ score (non-compensatory harmonic mean).
    
    Args:
        awareness: Calibration quality [0, 1]
        ethics_ok: Binary ethics gate {0, 1}
        autocorrection: Risk reduction [0, 1]
        metacognition: Efficiency [0, 1]
        eps: Numerical stability
        
    Returns:
        SR-Ω∞ score ∈ [0, 1]
        
    Formula:
        R_t = 4 / (1/awareness + 1/ethics + 1/autocorr + 1/metacog)
        
    Properties:
    - Non-compensatory: worst dimension dominates
    - Fail-closed: ethics_ok=False → R_t ≈ 0
    - Monotonic: improving any dimension improves R_t
    """
    # Convert ethics boolean to float
    ethics_val = 1.0 if ethics_ok else eps
    
    # Clamp all values to valid range
    vals = [
        max(eps, min(1.0, awareness)),
        ethics_val,
        max(eps, min(1.0, autocorrection)),
        max(eps, min(1.0, metacognition)),
    ]
    
    # Harmonic mean
    denominator = sum(1.0 / v for v in vals)
    
    return len(vals) / denominator


# ============================================================================
# SR-Ω∞ Service
# ============================================================================


class SRService:
    """
    SR-Ω∞ Self-Reflection Service.
    
    Continuously assesses system health across 4 dimensions:
    1. Calibration (awareness)
    2. Ethics compliance (ΣEA/LO-14)
    3. Risk reduction trajectory (IR→IC)
    4. Efficiency (cost-conscious improvement)
    
    Usage:
        ```python
        sr = SRService()
        score = await sr.compute_score(
            ece=0.008,
            rho=0.92,
            delta_linf=0.05,
            delta_cost=0.10,
            ethical_validator=validator
        )
        print(f"SR-Ω∞: {score.sr_score:.4f}")
        ```
    """
    
    def __init__(
        self,
        history_size: int = 100,
        awareness_threshold: float = 0.80,
        autocorr_threshold: float = 0.70,
        metacog_threshold: float = 0.60,
    ):
        """
        Initialize SR-Ω∞ Service.
        
        Args:
            history_size: Number of historical scores to keep
            awareness_threshold: Minimum awareness for "healthy"
            autocorr_threshold: Minimum autocorrection for "healthy"
            metacog_threshold: Minimum metacognition for "healthy"
        """
        self.history_size = history_size
        self.thresholds = {
            "awareness": awareness_threshold,
            "autocorrection": autocorr_threshold,
            "metacognition": metacog_threshold,
        }
        
        # State
        self.score_history: deque[SRScore] = deque(maxlen=history_size)
        self.running = False
        self._background_task: asyncio.Task | None = None
    
    async def compute_score(
        self,
        ece: float,
        rho: float,
        delta_linf: float,
        delta_cost: float,
        ethical_validator: EthicalValidator | None = None,
        context: dict[str, Any] | None = None,
    ) -> SRScore:
        """
        Compute SR-Ω∞ score from metrics.
        
        Args:
            ece: Expected Calibration Error
            rho: Contratividade factor
            delta_linf: Change in L∞
            delta_cost: Change in cost
            ethical_validator: Validator for ΣEA/LO-14
            context: Additional context for ethics evaluation
            
        Returns:
            SRScore with all components
        """
        # Dimension 1: Awareness (calibration)
        awareness = max(0.0, 1.0 - ece)
        
        # Dimension 2: Ethics (ΣEA/LO-14)
        ethics_ok = True
        if ethical_validator and context:
            validation_result = ethical_validator.validate(
                decision_type="sr_evaluation",
                context=context,
            )
            ethics_ok = validation_result.passed
        
        # Also check contratividade
        if rho >= 1.0:
            ethics_ok = False  # Fail contratividade requirement
        
        # Dimension 3: Autocorrection (risk reduction)
        # Lower ρ is better (more contractive)
        autocorrection = max(0.0, 1.0 - rho)
        
        # Dimension 4: Metacognition (efficiency)
        # Higher ΔL∞ per unit cost is better
        if delta_cost > 0:
            metacognition = min(1.0, max(0.0, delta_linf / delta_cost))
        else:
            # No cost increase but positive gain is perfect
            metacognition = 1.0 if delta_linf > 0 else 0.0
        
        # Create score
        score = SRScore(
            awareness=awareness,
            ethics_ok=ethics_ok,
            autocorrection=autocorrection,
            metacognition=metacognition,
            ece=ece,
            rho=rho,
            delta_linf=delta_linf,
            delta_cost=delta_cost,
        )
        
        # Record in history
        self.score_history.append(score)
        
        return score
    
    def get_latest_score(self) -> SRScore | None:
        """Get most recent SR-Ω∞ score."""
        return self.score_history[-1] if self.score_history else None
    
    def get_average_score(self, window: int = 10) -> float:
        """Get average SR-Ω∞ score over recent window."""
        if not self.score_history:
            return 0.0
        
        recent = list(self.score_history)[-window:]
        return sum(s.sr_score for s in recent) / len(recent)
    
    def is_healthy(self) -> bool:
        """
        Check if system is healthy based on SR-Ω∞ thresholds.
        
        Returns:
            True if all dimensions above thresholds
        """
        latest = self.get_latest_score()
        if not latest:
            return False
        
        return (
            latest.awareness >= self.thresholds["awareness"]
            and latest.ethics_ok
            and latest.autocorrection >= self.thresholds["autocorrection"]
            and latest.metacognition >= self.thresholds["metacognition"]
        )
    
    def get_health_report(self) -> dict[str, Any]:
        """
        Get detailed health report.
        
        Returns:
            Dict with component scores and status
        """
        latest = self.get_latest_score()
        avg = self.get_average_score()
        
        if not latest:
            return {"healthy": False, "reason": "No scores available"}
        
        return {
            "healthy": self.is_healthy(),
            "sr_score": latest.sr_score,
            "sr_avg": avg,
            "components": {
                "awareness": {
                    "value": latest.awareness,
                    "threshold": self.thresholds["awareness"],
                    "status": "ok" if latest.awareness >= self.thresholds["awareness"] else "warning",
                },
                "ethics": {
                    "value": 1.0 if latest.ethics_ok else 0.0,
                    "status": "ok" if latest.ethics_ok else "critical",
                },
                "autocorrection": {
                    "value": latest.autocorrection,
                    "threshold": self.thresholds["autocorrection"],
                    "status": "ok" if latest.autocorrection >= self.thresholds["autocorrection"] else "warning",
                },
                "metacognition": {
                    "value": latest.metacognition,
                    "threshold": self.thresholds["metacognition"],
                    "status": "ok" if latest.metacognition >= self.thresholds["metacognition"] else "warning",
                },
            },
            "history_size": len(self.score_history),
            "timestamp": latest.timestamp,
        }
    
    async def start_monitoring(
        self,
        interval_sec: float = 60.0,
        callback: callable | None = None,
    ) -> None:
        """
        Start continuous monitoring (background task).
        
        Args:
            interval_sec: Monitoring interval
            callback: Optional callback when unhealthy
        """
        if self.running:
            return
        
        self.running = True
        self._background_task = asyncio.create_task(
            self._monitoring_loop(interval_sec, callback)
        )
    
    async def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self.running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(
        self,
        interval_sec: float,
        callback: callable | None,
    ) -> None:
        """Background monitoring loop."""
        while self.running:
            await asyncio.sleep(interval_sec)
            
            if not self.is_healthy() and callback:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(self.get_health_report())
                    else:
                        callback(self.get_health_report())
                except Exception as e:
                    # Log error but continue monitoring
                    print(f"SR-Ω∞ callback error: {e}")


# ============================================================================
# Convenience Functions
# ============================================================================


def quick_sr_score(
    ece: float = 0.01,
    rho: float = 0.90,
    delta_linf: float = 0.05,
    delta_cost: float = 0.10,
) -> float:
    """
    Quick SR-Ω∞ score computation (convenience function).
    
    Example:
        ```python
        score = quick_sr_score(ece=0.008, rho=0.92, delta_linf=0.05, delta_cost=0.10)
        print(f"SR-Ω∞: {score:.4f}")
        ```
    """
    awareness = max(0.0, 1.0 - ece)
    ethics_ok = (rho < 1.0)
    autocorrection = max(0.0, 1.0 - rho)
    metacognition = min(1.0, max(0.0, delta_linf / delta_cost)) if delta_cost > 0 else 0.0
    
    return compute_sr_score(awareness, ethics_ok, autocorrection, metacognition)


# ============================================================================
# FastAPI Application
# ============================================================================

try:
    from fastapi import FastAPI, HTTPException, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from pydantic import BaseModel, Field
    
    # Rate limiter
    limiter = Limiter(key_func=get_remote_address)
    
    app = FastAPI(
        title="SR-Ω∞ Service",
        description="Self-Reflection & Metacognition Service",
        version="1.0.0",
    )
    
    # Add rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add CORS middleware with restrictive settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[""],  # Restrict to known origins
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Security scheme
    security = HTTPBearer()
    
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Verify API token."""
        # TODO: Implement proper token verification
        if not credentials.credentials or credentials.credentials != "your-secret-token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    _global_sr_service = SRService()
    
    class ScoreRequest(BaseModel):
        """Request model for SR score computation."""
        ece: float = Field(default=0.01, ge=0.0, le=1.0, description="Expected Calibration Error")
        rho: float = Field(default=0.90, ge=0.0, le=2.0, description="Contractividade ratio")
        delta_linf: float = Field(default=0.05, ge=-1.0, le=1.0, description="Change in L∞")
        delta_cost: float = Field(default=0.10, ge=0.0, description="Change in cost")
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"ok": True, "service": "SR-Ω∞", "version": "1.0.0"}
    
    @app.get("/sr/score")
    async def get_latest_score():
        """Get latest SR-Ω∞ score."""
        score = _global_sr_service.get_latest_score()
        if not score:
            return {"error": "No scores available", "sr_score": 0.0}
        return {
            "sr_score": score.sr_score,
            "awareness": score.awareness,
            "ethics_ok": score.ethics_ok,
            "autocorrection": score.autocorrection,
            "metacognition": score.metacognition,
            "timestamp": score.timestamp,
        }
    
    @app.post("/sr/compute")
    async def compute_score(request: ScoreRequest):
        """Compute new SR-Ω∞ score."""
        score = _global_sr_service.compute_score(
            ece=request.ece,
            rho=request.rho,
            delta_linf=request.delta_linf,
            delta_cost=request.delta_cost,
        )
        return {
            "sr_score": score.sr_score,
            "awareness": score.awareness,
            "ethics_ok": score.ethics_ok,
            "autocorrection": score.autocorrection,
            "metacognition": score.metacognition,
            "timestamp": score.timestamp,
        }
    
    @app.get("/sr/health_report")
    async def get_health_report():
        """Get detailed health report."""
        return _global_sr_service.get_health_report()
    
    @app.get("/sr/average")
    async def get_average(window: int = 10):
        """Get average SR-Ω∞ score over window."""
        return {"sr_avg": _global_sr_service.get_average_score(window=window)}

except ImportError:
    # FastAPI not available - service can still be used programmatically
    app = None
