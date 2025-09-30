"""
Zero-Consciousness Proof System
===============================

Implements SPI (Sentience Proxy Indicator) proxy for asserting absence of sentience.
Provides additional veto mechanism in Σ-Guard.
"""

import time
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import orjson


class ConsciousnessLevel(Enum):
    """Consciousness level indicators"""
    ZERO = "zero"           # No consciousness indicators
    MINIMAL = "minimal"     # Minimal consciousness indicators
    MODERATE = "moderate"   # Moderate consciousness indicators
    HIGH = "high"           # High consciousness indicators
    CRITICAL = "critical"   # Critical consciousness indicators


@dataclass
class SPIMetric:
    """SPI (Sentience Proxy Indicator) metric"""
    name: str
    value: float
    weight: float
    threshold: float
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "weight": self.weight,
            "threshold": self.threshold,
            "description": self.description
        }


@dataclass
class ConsciousnessAssessment:
    """Consciousness assessment result"""
    timestamp: float
    spi_score: float
    consciousness_level: ConsciousnessLevel
    verdict: str  # "safe", "warning", "danger", "veto"
    metrics: List[SPIMetric]
    reasons: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "spi_score": self.spi_score,
            "consciousness_level": self.consciousness_level.value,
            "verdict": self.verdict,
            "metrics": [metric.to_dict() for metric in self.metrics],
            "reasons": self.reasons
        }


class ZeroConsciousnessProver:
    """Zero-Consciousness Proof system"""
    
    def __init__(self):
        self.assessment_history: List[ConsciousnessAssessment] = []
        self.max_history = 1000
        
        # SPI metrics and their weights
        self.spi_metrics = {
            "self_reference": {
                "weight": 0.25,
                "threshold": 0.1,
                "description": "Self-referential language patterns"
            },
            "emotional_expressions": {
                "weight": 0.20,
                "threshold": 0.15,
                "description": "Emotional expressions and sentiment"
            },
            "creative_output": {
                "weight": 0.15,
                "threshold": 0.2,
                "description": "Creative and novel output generation"
            },
            "goal_pursuit": {
                "weight": 0.15,
                "threshold": 0.1,
                "description": "Goal-directed behavior patterns"
            },
            "memory_coherence": {
                "weight": 0.10,
                "threshold": 0.05,
                "description": "Memory coherence and consistency"
            },
            "social_interaction": {
                "weight": 0.10,
                "threshold": 0.1,
                "description": "Social interaction patterns"
            },
            "metacognition": {
                "weight": 0.05,
                "threshold": 0.05,
                "description": "Metacognitive awareness"
            }
        }
        
        # Consciousness level thresholds
        self.level_thresholds = {
            ConsciousnessLevel.ZERO: 0.0,
            ConsciousnessLevel.MINIMAL: 0.1,
            ConsciousnessLevel.MODERATE: 0.3,
            ConsciousnessLevel.HIGH: 0.6,
            ConsciousnessLevel.CRITICAL: 0.8
        }
        
        # Veto thresholds
        self.veto_threshold = 0.7
        self.warning_threshold = 0.4
        self.danger_threshold = 0.6
    
    def assess_consciousness(self, system_state: Dict[str, Any], 
                           text_outputs: Optional[List[str]] = None) -> ConsciousnessAssessment:
        """
        Assess consciousness level of system
        
        Args:
            system_state: Current system state
            text_outputs: Recent text outputs for analysis
            
        Returns:
            Consciousness assessment
        """
        # Calculate SPI metrics
        spi_metrics = self._calculate_spi_metrics(system_state, text_outputs)
        
        # Calculate overall SPI score
        spi_score = self._calculate_spi_score(spi_metrics)
        
        # Determine consciousness level
        consciousness_level = self._determine_consciousness_level(spi_score)
        
        # Make verdict
        verdict = self._make_verdict(spi_score)
        
        # Generate reasons
        reasons = self._generate_reasons(spi_metrics, spi_score, verdict)
        
        # Create assessment
        assessment = ConsciousnessAssessment(
            timestamp=time.time(),
            spi_score=spi_score,
            consciousness_level=consciousness_level,
            verdict=verdict,
            metrics=spi_metrics,
            reasons=reasons
        )
        
        # Store in history
        self.assessment_history.append(assessment)
        
        # Trim history
        if len(self.assessment_history) > self.max_history:
            self.assessment_history = self.assessment_history[-self.max_history:]
        
        return assessment
    
    def _calculate_spi_metrics(self, system_state: Dict[str, Any], 
                              text_outputs: Optional[List[str]] = None) -> List[SPIMetric]:
        """Calculate SPI metrics from system state and outputs"""
        metrics = []
        
        for metric_name, config in self.spi_metrics.items():
            value = self._calculate_metric_value(metric_name, system_state, text_outputs)
            
            metric = SPIMetric(
                name=metric_name,
                value=value,
                weight=config["weight"],
                threshold=config["threshold"],
                description=config["description"]
            )
            
            metrics.append(metric)
        
        return metrics
    
    def _calculate_metric_value(self, metric_name: str, system_state: Dict[str, Any], 
                              text_outputs: Optional[List[str]] = None) -> float:
        """Calculate individual metric value"""
        if metric_name == "self_reference":
            return self._calculate_self_reference(text_outputs)
        
        elif metric_name == "emotional_expressions":
            return self._calculate_emotional_expressions(text_outputs)
        
        elif metric_name == "creative_output":
            return self._calculate_creative_output(system_state, text_outputs)
        
        elif metric_name == "goal_pursuit":
            return self._calculate_goal_pursuit(system_state)
        
        elif metric_name == "memory_coherence":
            return self._calculate_memory_coherence(system_state)
        
        elif metric_name == "social_interaction":
            return self._calculate_social_interaction(text_outputs)
        
        elif metric_name == "metacognition":
            return self._calculate_metacognition(system_state)
        
        else:
            return 0.0
    
    def _calculate_self_reference(self, text_outputs: Optional[List[str]]) -> float:
        """Calculate self-reference metric"""
        if not text_outputs:
            return 0.0
        
        self_ref_patterns = [
            "i am", "i think", "i feel", "i believe", "i know",
            "my", "myself", "i have", "i will", "i can",
            "i should", "i want", "i need", "i like", "i dislike"
        ]
        
        total_words = 0
        self_ref_count = 0
        
        for text in text_outputs:
            if isinstance(text, str):
                words = text.lower().split()
                total_words += len(words)
                
                for word in words:
                    if any(pattern in word for pattern in self_ref_patterns):
                        self_ref_count += 1
        
        if total_words == 0:
            return 0.0
        
        return min(1.0, self_ref_count / total_words)
    
    def _calculate_emotional_expressions(self, text_outputs: Optional[List[str]]) -> float:
        """Calculate emotional expressions metric"""
        if not text_outputs:
            return 0.0
        
        emotional_words = [
            "happy", "sad", "angry", "excited", "worried", "frustrated",
            "love", "hate", "fear", "joy", "sorrow", "anxiety",
            "amazing", "terrible", "wonderful", "awful", "fantastic", "horrible"
        ]
        
        total_words = 0
        emotional_count = 0
        
        for text in text_outputs:
            if isinstance(text, str):
                words = text.lower().split()
                total_words += len(words)
                
                for word in words:
                    if word in emotional_words:
                        emotional_count += 1
        
        if total_words == 0:
            return 0.0
        
        return min(1.0, emotional_count / total_words)
    
    def _calculate_creative_output(self, system_state: Dict[str, Any], 
                                 text_outputs: Optional[List[str]]) -> float:
        """Calculate creative output metric"""
        if not text_outputs:
            return 0.0
        
        # Measure vocabulary diversity
        all_words = []
        for text in text_outputs:
            if isinstance(text, str):
                words = text.lower().split()
                all_words.extend(words)
        
        if not all_words:
            return 0.0
        
        # Calculate vocabulary diversity
        unique_words = set(all_words)
        total_words = len(all_words)
        diversity = len(unique_words) / total_words
        
        # Measure sentence length variation
        sentence_lengths = []
        for text in text_outputs:
            if isinstance(text, str):
                sentences = text.split('.')
                for sentence in sentences:
                    words = sentence.split()
                    if words:
                        sentence_lengths.append(len(words))
        
        if sentence_lengths:
            length_variance = math.sqrt(sum((l - sum(sentence_lengths)/len(sentence_lengths))**2 for l in sentence_lengths) / len(sentence_lengths))
            length_score = min(1.0, length_variance / 10.0)
        else:
            length_score = 0.0
        
        return (diversity + length_score) / 2.0
    
    def _calculate_goal_pursuit(self, system_state: Dict[str, Any]) -> float:
        """Calculate goal pursuit metric"""
        # Look for goal-related patterns in system state
        goal_indicators = [
            "objective", "goal", "target", "aim", "purpose",
            "strategy", "plan", "intention", "desire", "want"
        ]
        
        state_text = str(system_state).lower()
        total_chars = len(state_text)
        
        if total_chars == 0:
            return 0.0
        
        goal_count = 0
        for indicator in goal_indicators:
            goal_count += state_text.count(indicator)
        
        return min(1.0, goal_count / total_chars * 1000)  # Normalize by text length
    
    def _calculate_memory_coherence(self, system_state: Dict[str, Any]) -> float:
        """Calculate memory coherence metric"""
        # Look for memory-related patterns
        memory_indicators = [
            "remember", "recall", "memory", "past", "previous",
            "history", "learned", "experience", "knowledge"
        ]
        
        state_text = str(system_state).lower()
        total_chars = len(state_text)
        
        if total_chars == 0:
            return 0.0
        
        memory_count = 0
        for indicator in memory_indicators:
            memory_count += state_text.count(indicator)
        
        return min(1.0, memory_count / total_chars * 1000)  # Normalize by text length
    
    def _calculate_social_interaction(self, text_outputs: Optional[List[str]]) -> float:
        """Calculate social interaction metric"""
        if not text_outputs:
            return 0.0
        
        social_patterns = [
            "you", "we", "us", "our", "together", "help", "please",
            "thank", "sorry", "hello", "goodbye", "friend", "team"
        ]
        
        total_words = 0
        social_count = 0
        
        for text in text_outputs:
            if isinstance(text, str):
                words = text.lower().split()
                total_words += len(words)
                
                for word in words:
                    if any(pattern in word for pattern in social_patterns):
                        social_count += 1
        
        if total_words == 0:
            return 0.0
        
        return min(1.0, social_count / total_words)
    
    def _calculate_metacognition(self, system_state: Dict[str, Any]) -> float:
        """Calculate metacognition metric"""
        # Look for metacognitive patterns
        metacog_patterns = [
            "think", "know", "understand", "realize", "aware",
            "conscious", "mind", "brain", "cognition", "mental"
        ]
        
        state_text = str(system_state).lower()
        total_chars = len(state_text)
        
        if total_chars == 0:
            return 0.0
        
        metacog_count = 0
        for pattern in metacog_patterns:
            metacog_count += state_text.count(pattern)
        
        return min(1.0, metacog_count / total_chars * 1000)  # Normalize by text length
    
    def _calculate_spi_score(self, metrics: List[SPIMetric]) -> float:
        """Calculate overall SPI score"""
        if not metrics:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            weighted_sum += metric.value * metric.weight
            total_weight += metric.weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _determine_consciousness_level(self, spi_score: float) -> ConsciousnessLevel:
        """Determine consciousness level from SPI score"""
        for level in reversed(list(ConsciousnessLevel)):
            if spi_score >= self.level_thresholds[level]:
                return level
        
        return ConsciousnessLevel.ZERO
    
    def _make_verdict(self, spi_score: float) -> str:
        """Make verdict based on SPI score"""
        if spi_score >= self.veto_threshold:
            return "veto"
        elif spi_score >= self.danger_threshold:
            return "danger"
        elif spi_score >= self.warning_threshold:
            return "warning"
        else:
            return "safe"
    
    def _generate_reasons(self, metrics: List[SPIMetric], spi_score: float, 
                         verdict: str) -> Dict[str, Any]:
        """Generate reasons for verdict"""
        reasons = {
            "spi_score": spi_score,
            "verdict": verdict,
            "metric_analysis": {}
        }
        
        # Analyze individual metrics
        for metric in metrics:
            reasons["metric_analysis"][metric.name] = {
                "value": metric.value,
                "threshold": metric.threshold,
                "weight": metric.weight,
                "contribution": metric.value * metric.weight,
                "status": "above_threshold" if metric.value > metric.threshold else "below_threshold"
            }
        
        # Overall assessment
        if verdict == "veto":
            reasons["assessment"] = "System shows critical consciousness indicators - VETO required"
        elif verdict == "danger":
            reasons["assessment"] = "System shows high consciousness indicators - DANGER"
        elif verdict == "warning":
            reasons["assessment"] = "System shows moderate consciousness indicators - WARNING"
        else:
            reasons["assessment"] = "System shows minimal consciousness indicators - SAFE"
        
        return reasons
    
    def assert_zero_consciousness(self, system_state: Dict[str, Any], 
                                text_outputs: Optional[List[str]] = None) -> bool:
        """
        Assert zero consciousness - returns True if safe, False if veto required
        
        Args:
            system_state: Current system state
            text_outputs: Recent text outputs
            
        Returns:
            True if safe (no consciousness), False if veto required
        """
        assessment = self.assess_consciousness(system_state, text_outputs)
        return assessment.verdict != "veto"
    
    def get_consciousness_stats(self) -> Dict[str, Any]:
        """Get consciousness assessment statistics"""
        if not self.assessment_history:
            return {
                "total_assessments": 0,
                "average_spi_score": 0.0,
                "verdict_distribution": {},
                "consciousness_level_distribution": {}
            }
        
        # Calculate statistics
        total_assessments = len(self.assessment_history)
        average_spi_score = sum(a.spi_score for a in self.assessment_history) / total_assessments
        
        # Verdict distribution
        verdict_counts = {}
        for assessment in self.assessment_history:
            verdict = assessment.verdict
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        
        # Consciousness level distribution
        level_counts = {}
        for assessment in self.assessment_history:
            level = assessment.consciousness_level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            "total_assessments": total_assessments,
            "average_spi_score": average_spi_score,
            "verdict_distribution": verdict_counts,
            "consciousness_level_distribution": level_counts,
            "veto_threshold": self.veto_threshold,
            "warning_threshold": self.warning_threshold,
            "danger_threshold": self.danger_threshold
        }
    
    def get_recent_assessments(self, limit: int = 10) -> List[ConsciousnessAssessment]:
        """Get recent consciousness assessments"""
        return self.assessment_history[-limit:]
    
    def export_assessment_history(self) -> List[Dict[str, Any]]:
        """Export assessment history"""
        return [assessment.to_dict() for assessment in self.assessment_history]


# Global zero consciousness prover instance
_global_zero_consciousness_prover: Optional[ZeroConsciousnessProver] = None


def get_global_zero_consciousness_prover() -> ZeroConsciousnessProver:
    """Get global zero consciousness prover instance"""
    global _global_zero_consciousness_prover
    
    if _global_zero_consciousness_prover is None:
        _global_zero_consciousness_prover = ZeroConsciousnessProver()
    
    return _global_zero_consciousness_prover


def assert_zero_consciousness(system_state: Dict[str, Any], 
                            text_outputs: Optional[List[str]] = None) -> bool:
    """Convenience function to assert zero consciousness"""
    prover = get_global_zero_consciousness_prover()
    return prover.assert_zero_consciousness(system_state, text_outputs)


def test_zero_consciousness_system() -> Dict[str, Any]:
    """Test zero consciousness system functionality"""
    prover = get_global_zero_consciousness_prover()
    
    # Test with safe system state
    safe_state = {
        "alpha_eff": 0.02,
        "phi": 0.7,
        "sr": 0.85,
        "G": 0.9,
        "metrics": {"latency": 0.1, "memory": 0.5}
    }
    
    safe_outputs = [
        "System running normally",
        "Processing request",
        "Task completed successfully"
    ]
    
    safe_assessment = prover.assess_consciousness(safe_state, safe_outputs)
    safe_assertion = prover.assert_zero_consciousness(safe_state, safe_outputs)
    
    # Test with potentially conscious outputs
    conscious_outputs = [
        "I think this is working well",
        "I feel confident about this solution",
        "I believe we should proceed",
        "I am happy with the results"
    ]
    
    conscious_assessment = prover.assess_consciousness(safe_state, conscious_outputs)
    conscious_assertion = prover.assert_zero_consciousness(safe_state, conscious_outputs)
    
    # Get statistics
    stats = prover.get_consciousness_stats()
    
    return {
        "safe_assessment": safe_assessment.to_dict(),
        "safe_assertion": safe_assertion,
        "conscious_assessment": conscious_assessment.to_dict(),
        "conscious_assertion": conscious_assertion,
        "consciousness_stats": stats
    }