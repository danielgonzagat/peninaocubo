"""
Darwinian Audit System
======================

Implements challenger evaluation and selection based on evolutionary principles.
Provides scoring mechanism for evaluating system changes.
"""

import time
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import orjson


class SelectionPressure(Enum):
    """Types of selection pressure"""
    STABILIZING = "stabilizing"      # Maintains current state
    DIRECTIONAL = "directional"      # Favors specific direction
    DISRUPTIVE = "disruptive"        # Favors extreme values
    BALANCED = "balanced"            # Balanced selection


@dataclass
class Challenger:
    """System challenger for evolution"""
    id: str
    timestamp: float
    description: str
    metrics: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "description": self.description,
            "metrics": self.metrics,
            "metadata": self.metadata
        }


@dataclass
class AuditResult:
    """Audit result for challenger"""
    challenger_id: str
    score: float
    fitness: float
    selection_pressure: SelectionPressure
    verdict: str  # "accepted", "rejected", "pending"
    reasons: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "challenger_id": self.challenger_id,
            "score": self.score,
            "fitness": self.fitness,
            "selection_pressure": self.selection_pressure.value,
            "verdict": self.verdict,
            "reasons": self.reasons,
            "timestamp": self.timestamp
        }


class DarwinianAuditor:
    """Darwinian audit system for challenger evaluation"""
    
    def __init__(self):
        self.challengers: Dict[str, Challenger] = {}
        self.audit_results: Dict[str, AuditResult] = {}
        self.selection_history: List[AuditResult] = []
        
        # Selection parameters
        self.selection_pressure = SelectionPressure.BALANCED
        self.fitness_threshold = 0.5
        self.score_threshold = 0.3
        
        # Weighting factors for different metrics
        self.metric_weights = {
            "life_ok": 0.3,      # Life equation result
            "caos_phi": 0.2,     # CAOS+ metric
            "sr": 0.2,          # Self-reflection
            "G": 0.15,          # Global coherence
            "L_inf": 0.1,       # L∞ score
            "cost": -0.05       # Cost (negative weight)
        }
        
        # Performance tracking
        self.total_audits = 0
        self.accepted_count = 0
        self.rejected_count = 0
    
    def register_challenger(self, challenger: Challenger) -> str:
        """Register a new challenger"""
        self.challengers[challenger.id] = challenger
        return challenger.id
    
    def audit_challenger(self, challenger_id: str, 
                        reference_metrics: Optional[Dict[str, float]] = None) -> AuditResult:
        """
        Audit a challenger against evolutionary criteria
        
        Args:
            challenger_id: ID of challenger to audit
            reference_metrics: Reference metrics for comparison
            
        Returns:
            Audit result
        """
        if challenger_id not in self.challengers:
            raise ValueError(f"Challenger {challenger_id} not found")
        
        challenger = self.challengers[challenger_id]
        
        # Calculate fitness score
        fitness = self._calculate_fitness(challenger.metrics, reference_metrics)
        
        # Calculate overall score
        score = self._calculate_score(challenger.metrics, fitness)
        
        # Determine selection pressure
        selection_pressure = self._determine_selection_pressure(challenger.metrics)
        
        # Make verdict
        verdict = self._make_verdict(score, fitness)
        
        # Generate reasons
        reasons = self._generate_reasons(challenger.metrics, score, fitness, verdict)
        
        # Create audit result
        result = AuditResult(
            challenger_id=challenger_id,
            score=score,
            fitness=fitness,
            selection_pressure=selection_pressure,
            verdict=verdict,
            reasons=reasons
        )
        
        # Store result
        self.audit_results[challenger_id] = result
        self.selection_history.append(result)
        
        # Update tracking
        self.total_audits += 1
        if verdict == "accepted":
            self.accepted_count += 1
        else:
            self.rejected_count += 1
        
        return result
    
    def _calculate_fitness(self, metrics: Dict[str, float], 
                         reference: Optional[Dict[str, float]] = None) -> float:
        """Calculate fitness score for challenger"""
        if not metrics:
            return 0.0
        
        # Base fitness from individual metrics
        fitness_components = []
        
        for metric_name, value in metrics.items():
            if metric_name in self.metric_weights:
                weight = self.metric_weights[metric_name]
                
                # Normalize value to [0, 1] range
                normalized_value = self._normalize_metric(metric_name, value)
                
                # Apply weight
                fitness_components.append(weight * normalized_value)
        
        # Calculate weighted fitness
        if fitness_components:
            fitness = sum(fitness_components)
        else:
            fitness = 0.0
        
        # Apply selection pressure
        fitness = self._apply_selection_pressure(fitness, metrics)
        
        return max(0.0, min(1.0, fitness))
    
    def _normalize_metric(self, metric_name: str, value: float) -> float:
        """Normalize metric value to [0, 1] range"""
        # Define expected ranges for different metrics
        ranges = {
            "life_ok": (0.0, 1.0),
            "caos_phi": (0.0, 1.0),
            "sr": (0.0, 1.0),
            "G": (0.0, 1.0),
            "L_inf": (0.0, 1.0),
            "cost": (0.0, 1.0),
            "latency": (0.0, 1.0),
            "memory": (0.0, 1.0),
            "cpu": (0.0, 1.0)
        }
        
        if metric_name in ranges:
            min_val, max_val = ranges[metric_name]
            if max_val > min_val:
                normalized = (value - min_val) / (max_val - min_val)
                return max(0.0, min(1.0, normalized))
        
        # Default normalization
        return max(0.0, min(1.0, value))
    
    def _apply_selection_pressure(self, fitness: float, metrics: Dict[str, float]) -> float:
        """Apply selection pressure to fitness"""
        if self.selection_pressure == SelectionPressure.STABILIZING:
            # Favor values close to 0.5
            return fitness * (1.0 - abs(fitness - 0.5))
        
        elif self.selection_pressure == SelectionPressure.DIRECTIONAL:
            # Favor higher values
            return fitness ** 0.8
        
        elif self.selection_pressure == SelectionPressure.DISRUPTIVE:
            # Favor extreme values
            return fitness * (2.0 - fitness) if fitness > 0.5 else fitness * 2.0
        
        else:  # BALANCED
            return fitness
    
    def _calculate_score(self, metrics: Dict[str, float], fitness: float) -> float:
        """Calculate overall score for challenger"""
        # Base score from fitness
        score = fitness
        
        # Bonus for meeting multiple criteria
        criteria_met = 0
        total_criteria = len(self.metric_weights)
        
        for metric_name, value in metrics.items():
            if metric_name in self.metric_weights:
                normalized_value = self._normalize_metric(metric_name, value)
                if normalized_value > 0.5:  # Above threshold
                    criteria_met += 1
        
        # Bonus for meeting multiple criteria
        if total_criteria > 0:
            criteria_bonus = (criteria_met / total_criteria) * 0.2
            score += criteria_bonus
        
        # Penalty for high cost
        if "cost" in metrics:
            cost_penalty = metrics["cost"] * 0.1
            score -= cost_penalty
        
        return max(0.0, min(1.0, score))
    
    def _determine_selection_pressure(self, metrics: Dict[str, float]) -> SelectionPressure:
        """Determine appropriate selection pressure based on metrics"""
        # Analyze metric distribution
        values = list(metrics.values())
        if not values:
            return SelectionPressure.BALANCED
        
        mean_value = sum(values) / len(values)
        variance = sum((v - mean_value) ** 2 for v in values) / len(values)
        
        # High variance suggests disruptive selection
        if variance > 0.1:
            return SelectionPressure.DISRUPTIVE
        
        # Low mean suggests directional selection
        if mean_value < 0.3:
            return SelectionPressure.DIRECTIONAL
        
        # High mean suggests stabilizing selection
        if mean_value > 0.7:
            return SelectionPressure.STABILIZING
        
        return SelectionPressure.BALANCED
    
    def _make_verdict(self, score: float, fitness: float) -> str:
        """Make verdict based on score and fitness"""
        if score >= self.score_threshold and fitness >= self.fitness_threshold:
            return "accepted"
        elif score < self.score_threshold * 0.5 or fitness < self.fitness_threshold * 0.5:
            return "rejected"
        else:
            return "pending"
    
    def _generate_reasons(self, metrics: Dict[str, float], score: float, 
                         fitness: float, verdict: str) -> Dict[str, Any]:
        """Generate reasons for verdict"""
        reasons = {
            "score": score,
            "fitness": fitness,
            "verdict": verdict,
            "metric_analysis": {}
        }
        
        # Analyze individual metrics
        for metric_name, value in metrics.items():
            if metric_name in self.metric_weights:
                weight = self.metric_weights[metric_name]
                normalized_value = self._normalize_metric(metric_name, value)
                
                reasons["metric_analysis"][metric_name] = {
                    "value": value,
                    "normalized": normalized_value,
                    "weight": weight,
                    "contribution": weight * normalized_value,
                    "status": "good" if normalized_value > 0.5 else "poor"
                }
        
        # Overall assessment
        if verdict == "accepted":
            reasons["assessment"] = "Challenger meets evolutionary criteria"
        elif verdict == "rejected":
            reasons["assessment"] = "Challenger fails evolutionary criteria"
        else:
            reasons["assessment"] = "Challenger requires further evaluation"
        
        return reasons
    
    def get_selection_stats(self) -> Dict[str, Any]:
        """Get selection statistics"""
        if self.total_audits == 0:
            return {
                "total_audits": 0,
                "acceptance_rate": 0.0,
                "rejection_rate": 0.0,
                "average_score": 0.0,
                "average_fitness": 0.0
            }
        
        acceptance_rate = self.accepted_count / self.total_audits
        rejection_rate = self.rejected_count / self.total_audits
        
        # Calculate averages
        scores = [result.score for result in self.selection_history]
        fitnesses = [result.fitness for result in self.selection_history]
        
        average_score = sum(scores) / len(scores) if scores else 0.0
        average_fitness = sum(fitnesses) / len(fitnesses) if fitnesses else 0.0
        
        return {
            "total_audits": self.total_audits,
            "acceptance_rate": acceptance_rate,
            "rejection_rate": rejection_rate,
            "average_score": average_score,
            "average_fitness": average_fitness,
            "selection_pressure": self.selection_pressure.value,
            "fitness_threshold": self.fitness_threshold,
            "score_threshold": self.score_threshold
        }
    
    def get_recent_selections(self, limit: int = 10) -> List[AuditResult]:
        """Get recent selection results"""
        return self.selection_history[-limit:]
    
    def set_selection_pressure(self, pressure: SelectionPressure) -> None:
        """Set selection pressure type"""
        self.selection_pressure = pressure
    
    def set_thresholds(self, fitness_threshold: float, score_threshold: float) -> None:
        """Set selection thresholds"""
        self.fitness_threshold = max(0.0, min(1.0, fitness_threshold))
        self.score_threshold = max(0.0, min(1.0, score_threshold))
    
    def export_selection_history(self) -> List[Dict[str, Any]]:
        """Export selection history"""
        return [result.to_dict() for result in self.selection_history]


# Global Darwinian auditor instance
_global_darwin_auditor: Optional[DarwinianAuditor] = None


def get_global_darwin_auditor() -> DarwinianAuditor:
    """Get global Darwinian auditor instance"""
    global _global_darwin_auditor
    
    if _global_darwin_auditor is None:
        _global_darwin_auditor = DarwinianAuditor()
    
    return _global_darwin_auditor


def audit_challenger(challenger_id: str, metrics: Dict[str, float], 
                    reference: Optional[Dict[str, float]] = None) -> AuditResult:
    """Convenience function to audit challenger"""
    auditor = get_global_darwin_auditor()
    
    # Create challenger if not exists
    if challenger_id not in auditor.challengers:
        challenger = Challenger(
            id=challenger_id,
            timestamp=time.time(),
            description=f"Challenger {challenger_id}",
            metrics=metrics
        )
        auditor.register_challenger(challenger)
    
    return auditor.audit_challenger(challenger_id, reference)


def test_darwin_audit_system() -> Dict[str, Any]:
    """Test Darwinian audit system functionality"""
    auditor = get_global_darwin_auditor()
    
    # Test challengers
    test_challengers = [
        {
            "id": "test_1",
            "metrics": {
                "life_ok": 0.8,
                "caos_phi": 0.7,
                "sr": 0.9,
                "G": 0.85,
                "L_inf": 0.75,
                "cost": 0.1
            }
        },
        {
            "id": "test_2",
            "metrics": {
                "life_ok": 0.3,
                "caos_phi": 0.2,
                "sr": 0.4,
                "G": 0.3,
                "L_inf": 0.2,
                "cost": 0.8
            }
        },
        {
            "id": "test_3",
            "metrics": {
                "life_ok": 0.6,
                "caos_phi": 0.5,
                "sr": 0.6,
                "G": 0.5,
                "L_inf": 0.5,
                "cost": 0.3
            }
        }
    ]
    
    # Register and audit challengers
    results = []
    for challenger_data in test_challengers:
        challenger = Challenger(
            id=challenger_data["id"],
            timestamp=time.time(),
            description=f"Test challenger {challenger_data['id']}",
            metrics=challenger_data["metrics"]
        )
        
        auditor.register_challenger(challenger)
        result = auditor.audit_challenger(challenger.id)
        results.append(result)
    
    # Get statistics
    stats = auditor.get_selection_stats()
    recent_selections = auditor.get_recent_selections()
    
    return {
        "audit_results": [result.to_dict() for result in results],
        "selection_stats": stats,
        "recent_selections": [result.to_dict() for result in recent_selections]
    }