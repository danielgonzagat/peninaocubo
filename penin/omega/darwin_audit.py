"""
Darwinian Audit System
======================

Implements darwinian scoring mechanism to evaluate challengers based on
life_ok, φ, sr, G, and L∞ with fail-closed protection.
"""

import time
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ChallengerStatus(Enum):
    """Challenger status"""
    PENDING = "pending"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"


@dataclass
class ChallengerMetrics:
    """Challenger metrics"""
    challenger_id: str
    timestamp: float
    life_ok: bool
    phi: float  # CAOS⁺
    sr: float   # SR-Ω∞
    G: float    # Global coherence
    L_inf: float  # L∞ score
    alpha_eff: float
    rho: float  # Risk contractivity
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DarwinianScore:
    """Darwinian score"""
    challenger_id: str
    score: float
    components: Dict[str, float]
    status: ChallengerStatus
    timestamp: float
    evaluation_time: float
    confidence: float


@dataclass
class DarwinianConfig:
    """Darwinian audit configuration"""
    min_life_ok: bool = True
    min_phi: float = 0.25
    min_sr: float = 0.80
    min_G: float = 0.85
    min_L_inf: float = 0.0
    max_rho: float = 1.0
    score_weights: Dict[str, float] = field(default_factory=lambda: {
        "phi": 1.0,
        "sr": 1.0,
        "G": 1.0,
        "L_inf": 1.0
    })
    confidence_threshold: float = 0.8
    quarantine_threshold: float = 0.5


class DarwinianAuditor:
    """Darwinian auditor for challenger evaluation"""
    
    def __init__(self, config: DarwinianConfig = None):
        self.config = config or DarwinianConfig()
        
        # Challenger history
        self.challenger_history: List[ChallengerMetrics] = []
        self.score_history: List[DarwinianScore] = []
        
        # Current champion
        self.current_champion: Optional[DarwinianScore] = None
        
        # Performance tracking
        self.performance_stats: Dict[str, Any] = {
            "total_evaluations": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "quarantined_count": 0,
            "average_score": 0.0,
            "best_score": 0.0
        }
    
    def _validate_metrics(self, metrics: ChallengerMetrics) -> Tuple[bool, List[str]]:
        """Validate challenger metrics"""
        errors = []
        
        # Check life_ok
        if not metrics.life_ok:
            errors.append("life_ok is False")
        
        # Check phi
        if metrics.phi < self.config.min_phi:
            errors.append(f"phi {metrics.phi:.3f} < min_phi {self.config.min_phi}")
        
        # Check sr
        if metrics.sr < self.config.min_sr:
            errors.append(f"sr {metrics.sr:.3f} < min_sr {self.config.min_sr}")
        
        # Check G
        if metrics.G < self.config.min_G:
            errors.append(f"G {metrics.G:.3f} < min_G {self.config.min_G}")
        
        # Check L_inf
        if metrics.L_inf < self.config.min_L_inf:
            errors.append(f"L_inf {metrics.L_inf:.3f} < min_L_inf {self.config.min_L_inf}")
        
        # Check rho
        if metrics.rho > self.config.max_rho:
            errors.append(f"rho {metrics.rho:.3f} > max_rho {self.config.max_rho}")
        
        # Check for NaN/inf values
        for field_name in ["phi", "sr", "G", "L_inf", "alpha_eff", "rho"]:
            value = getattr(metrics, field_name)
            if not math.isfinite(value):
                errors.append(f"{field_name} is not finite: {value}")
        
        return len(errors) == 0, errors
    
    def _calculate_darwinian_score(self, metrics: ChallengerMetrics) -> Tuple[float, Dict[str, float]]:
        """
        Calculate darwinian score: min(φ, sr, G) * L∞
        
        Args:
            metrics: Challenger metrics
            
        Returns:
            (score, components)
        """
        # Non-compensatory aggregation: min(φ, sr, G)
        min_component = min(metrics.phi, metrics.sr, metrics.G)
        
        # Apply weights
        weighted_phi = metrics.phi * self.config.score_weights.get("phi", 1.0)
        weighted_sr = metrics.sr * self.config.score_weights.get("sr", 1.0)
        weighted_G = metrics.G * self.config.score_weights.get("G", 1.0)
        weighted_L_inf = metrics.L_inf * self.config.score_weights.get("L_inf", 1.0)
        
        # Recalculate min with weights
        min_component = min(weighted_phi, weighted_sr, weighted_G)
        
        # Final score: min(φ, sr, G) * L∞
        score = min_component * weighted_L_inf
        
        components = {
            "phi": weighted_phi,
            "sr": weighted_sr,
            "G": weighted_G,
            "L_inf": weighted_L_inf,
            "min_component": min_component,
            "final_score": score
        }
        
        return score, components
    
    def _determine_status(self, score: float, metrics: ChallengerMetrics) -> ChallengerStatus:
        """Determine challenger status based on score and metrics"""
        # Check if meets minimum requirements
        if not metrics.life_ok:
            return ChallengerStatus.REJECTED
        
        if metrics.rho > self.config.max_rho:
            return ChallengerStatus.REJECTED
        
        # Check score thresholds
        if score < self.config.quarantine_threshold:
            return ChallengerStatus.QUARANTINED
        
        if score >= self.config.confidence_threshold:
            return ChallengerStatus.APPROVED
        
        return ChallengerStatus.REJECTED
    
    def _calculate_confidence(self, metrics: ChallengerMetrics, score: float) -> float:
        """Calculate confidence in the evaluation"""
        # Base confidence on how well metrics meet thresholds
        phi_confidence = min(1.0, metrics.phi / self.config.min_phi)
        sr_confidence = min(1.0, metrics.sr / self.config.min_sr)
        G_confidence = min(1.0, metrics.G / self.config.min_G)
        
        # Risk confidence (lower rho is better)
        rho_confidence = max(0.0, 1.0 - (metrics.rho / self.config.max_rho))
        
        # Overall confidence
        confidence = (phi_confidence + sr_confidence + G_confidence + rho_confidence) / 4.0
        
        return confidence
    
    def evaluate_challenger(self, metrics: ChallengerMetrics) -> DarwinianScore:
        """
        Evaluate a challenger using darwinian scoring
        
        Args:
            metrics: Challenger metrics
            
        Returns:
            Darwinian score
        """
        start_time = time.time()
        
        # Validate metrics
        is_valid, errors = self._validate_metrics(metrics)
        
        if not is_valid:
            # Create rejected score
            score = DarwinianScore(
                challenger_id=metrics.challenger_id,
                score=0.0,
                components={"error": "validation_failed", "errors": errors},
                status=ChallengerStatus.REJECTED,
                timestamp=time.time(),
                evaluation_time=time.time() - start_time,
                confidence=0.0
            )
            
            self.score_history.append(score)
            self._update_performance_stats(score)
            return score
        
        # Calculate darwinian score
        score_value, components = self._calculate_darwinian_score(metrics)
        
        # Determine status
        status = self._determine_status(score_value, metrics)
        
        # Calculate confidence
        confidence = self._calculate_confidence(metrics, score_value)
        
        # Create score
        score = DarwinianScore(
            challenger_id=metrics.challenger_id,
            score=score_value,
            components=components,
            status=status,
            timestamp=time.time(),
            evaluation_time=time.time() - start_time,
            confidence=confidence
        )
        
        # Store in history
        self.challenger_history.append(metrics)
        self.score_history.append(score)
        
        # Update performance stats
        self._update_performance_stats(score)
        
        return score
    
    def _update_performance_stats(self, score: DarwinianScore):
        """Update performance statistics"""
        self.performance_stats["total_evaluations"] += 1
        
        if score.status == ChallengerStatus.APPROVED:
            self.performance_stats["approved_count"] += 1
        elif score.status == ChallengerStatus.REJECTED:
            self.performance_stats["rejected_count"] += 1
        elif score.status == ChallengerStatus.QUARANTINED:
            self.performance_stats["quarantined_count"] += 1
        
        # Update average score
        total_score = sum(s.score for s in self.score_history)
        self.performance_stats["average_score"] = total_score / len(self.score_history)
        
        # Update best score
        if score.score > self.performance_stats["best_score"]:
            self.performance_stats["best_score"] = score.score
    
    def promote_challenger(self, challenger_id: str) -> bool:
        """
        Promote challenger to champion
        
        Args:
            challenger_id: ID of challenger to promote
            
        Returns:
            True if promotion successful
        """
        # Find challenger score
        challenger_score = None
        for score in self.score_history:
            if score.challenger_id == challenger_id:
                challenger_score = score
                break
        
        if challenger_score is None:
            return False
        
        # Check if challenger is approved
        if challenger_score.status != ChallengerStatus.APPROVED:
            return False
        
        # Check if challenger is better than current champion
        if self.current_champion is not None:
            if challenger_score.score <= self.current_champion.score:
                return False
        
        # Promote challenger
        self.current_champion = challenger_score
        return True
    
    def get_champion(self) -> Optional[DarwinianScore]:
        """Get current champion"""
        return self.current_champion
    
    def get_challenger_history(self, challenger_id: str = None) -> List[ChallengerMetrics]:
        """Get challenger history"""
        if challenger_id is None:
            return self.challenger_history.copy()
        
        return [m for m in self.challenger_history if m.challenger_id == challenger_id]
    
    def get_score_history(self, challenger_id: str = None) -> List[DarwinianScore]:
        """Get score history"""
        if challenger_id is None:
            return self.score_history.copy()
        
        return [s for s in self.score_history if s.challenger_id == challenger_id]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = self.performance_stats.copy()
        
        # Add additional metrics
        if stats["total_evaluations"] > 0:
            stats["approval_rate"] = stats["approved_count"] / stats["total_evaluations"]
            stats["rejection_rate"] = stats["rejected_count"] / stats["total_evaluations"]
            stats["quarantine_rate"] = stats["quarantined_count"] / stats["total_evaluations"]
        else:
            stats["approval_rate"] = 0.0
            stats["rejection_rate"] = 0.0
            stats["quarantine_rate"] = 0.0
        
        # Add champion info
        if self.current_champion:
            stats["champion_score"] = self.current_champion.score
            stats["champion_confidence"] = self.current_champion.confidence
        else:
            stats["champion_score"] = 0.0
            stats["champion_confidence"] = 0.0
        
        return stats
    
    def get_top_challengers(self, limit: int = 10) -> List[DarwinianScore]:
        """Get top challengers by score"""
        # Filter approved challengers
        approved_scores = [s for s in self.score_history 
                          if s.status == ChallengerStatus.APPROVED]
        
        # Sort by score (descending)
        approved_scores.sort(key=lambda x: x.score, reverse=True)
        
        return approved_scores[:limit]
    
    def reset_auditor(self):
        """Reset auditor state"""
        self.challenger_history.clear()
        self.score_history.clear()
        self.current_champion = None
        self.performance_stats = {
            "total_evaluations": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "quarantined_count": 0,
            "average_score": 0.0,
            "best_score": 0.0
        }


# Integration with Life Equation
def integrate_darwinian_audit_in_life_equation(
    life_verdict: Dict[str, Any],
    challenger_id: str,
    auditor: DarwinianAuditor = None
) -> Tuple[DarwinianScore, bool]:
    """
    Integrate darwinian audit with Life Equation
    
    Args:
        life_verdict: Result from life_equation()
        challenger_id: ID of challenger
        auditor: Darwinian auditor instance
        
    Returns:
        (darwinian_score, should_promote)
    """
    if auditor is None:
        auditor = DarwinianAuditor()
    
    # Extract metrics from life verdict
    metrics = life_verdict.get("metrics", {})
    
    # Create challenger metrics
    challenger_metrics = ChallengerMetrics(
        challenger_id=challenger_id,
        timestamp=time.time(),
        life_ok=life_verdict.get("ok", False),
        phi=metrics.get("phi", 0.0),
        sr=metrics.get("sr", 0.0),
        G=metrics.get("G", 0.0),
        L_inf=metrics.get("L_inf", 0.0),
        alpha_eff=metrics.get("alpha_eff", 0.0),
        rho=metrics.get("rho", 0.0),
        metadata=life_verdict.get("reasons", {})
    )
    
    # Evaluate challenger
    darwinian_score = auditor.evaluate_challenger(challenger_metrics)
    
    # Determine if should promote
    should_promote = darwinian_score.status == ChallengerStatus.APPROVED
    
    return darwinian_score, should_promote


# Example usage
if __name__ == "__main__":
    # Create darwinian auditor
    auditor = DarwinianAuditor()
    
    # Create test challenger metrics
    test_metrics = ChallengerMetrics(
        challenger_id="test_challenger_1",
        timestamp=time.time(),
        life_ok=True,
        phi=0.7,
        sr=0.8,
        G=0.9,
        L_inf=0.6,
        alpha_eff=0.5,
        rho=0.8
    )
    
    # Evaluate challenger
    score = auditor.evaluate_challenger(test_metrics)
    print(f"Challenger score: {score.score:.3f}")
    print(f"Status: {score.status.value}")
    print(f"Confidence: {score.confidence:.3f}")
    
    # Try to promote
    promoted = auditor.promote_challenger("test_challenger_1")
    print(f"Promoted: {promoted}")
    
    # Get performance stats
    stats = auditor.get_performance_stats()
    print(f"Performance stats: {stats}")
    
    # Get top challengers
    top_challengers = auditor.get_top_challengers(5)
    print(f"Top challengers: {len(top_challengers)}")