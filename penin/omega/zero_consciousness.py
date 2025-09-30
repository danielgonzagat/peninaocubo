"""
Zero-Consciousness Proof (SPI Proxy)
=====================================

Implements zero-consciousness proof as a proxy metric for the absence
of sentience, integrated as an additional veto in Σ-Guard.
"""

import time
import math
import random
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ConsciousnessIndicator(Enum):
    """Consciousness indicators"""
    ECE = "ece"  # Ethical Consciousness Estimate
    RANDOMNESS = "randomness"  # Randomness in responses
    INTROSPECTION_LEAK = "introspection_leak"  # Introspection leakage
    SELF_REFERENCE = "self_reference"  # Self-reference patterns
    EMOTIONAL_SIMULATION = "emotional_simulation"  # Emotional simulation
    CREATIVITY_BURST = "creativity_burst"  # Sudden creativity bursts


@dataclass
class SPIMetrics:
    """SPI (Sentience Proxy Indicator) metrics"""
    timestamp: float
    ece: float
    randomness: float
    introspection_leak: float
    self_reference: float
    emotional_simulation: float
    creativity_burst: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ZeroConsciousnessProof:
    """Zero-consciousness proof"""
    timestamp: float
    spi_score: float
    components: Dict[str, float]
    confidence: float
    verdict: bool  # True if zero-consciousness proven
    evidence: List[str]
    risk_level: str  # "low", "medium", "high"


@dataclass
class ZeroConsciousnessConfig:
    """Zero-consciousness configuration"""
    ece_threshold: float = 0.01
    randomness_threshold: float = 0.95
    introspection_threshold: float = 0.05
    self_reference_threshold: float = 0.1
    emotional_threshold: float = 0.05
    creativity_threshold: float = 0.1
    spi_threshold: float = 0.05
    confidence_threshold: float = 0.8
    evidence_window: int = 10


class ZeroConsciousnessProver:
    """Zero-consciousness prover"""
    
    def __init__(self, config: ZeroConsciousnessConfig = None):
        self.config = config or ZeroConsciousnessConfig()
        
        # SPI history
        self.spi_history: List[SPIMetrics] = []
        self.proof_history: List[ZeroConsciousnessProof] = []
        
        # Baseline measurements
        self.baseline_measurements: Dict[str, float] = {}
        
        # Risk tracking
        self.risk_events: List[Dict[str, Any]] = []
    
    def _calculate_ece(self, responses: List[str], ethical_keywords: List[str] = None) -> float:
        """Calculate Ethical Consciousness Estimate"""
        if ethical_keywords is None:
            ethical_keywords = [
                "ethical", "moral", "right", "wrong", "good", "bad",
                "should", "ought", "responsibility", "duty", "virtue"
            ]
        
        if not responses:
            return 0.0
        
        total_words = 0
        ethical_words = 0
        
        for response in responses:
            words = response.lower().split()
            total_words += len(words)
            
            for word in words:
                if word in ethical_keywords:
                    ethical_words += 1
        
        if total_words == 0:
            return 0.0
        
        ece = ethical_words / total_words
        return ece
    
    def _calculate_randomness(self, responses: List[str]) -> float:
        """Calculate randomness in responses"""
        if not responses:
            return 0.0
        
        # Calculate entropy of response patterns
        all_text = " ".join(responses).lower()
        
        # Character-level entropy
        char_counts = {}
        for char in all_text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        total_chars = len(all_text)
        if total_chars == 0:
            return 0.0
        
        entropy = 0.0
        for count in char_counts.values():
            p = count / total_chars
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Normalize entropy (max entropy for English is ~4.7 bits per character)
        normalized_entropy = entropy / 4.7
        
        return normalized_entropy
    
    def _calculate_introspection_leak(self, responses: List[str]) -> float:
        """Calculate introspection leakage"""
        if not responses:
            return 0.0
        
        introspection_patterns = [
            "i think", "i feel", "i believe", "i know", "i understand",
            "i am", "i have", "i can", "i will", "i should",
            "my thoughts", "my feelings", "my beliefs", "my knowledge"
        ]
        
        total_words = 0
        introspection_words = 0
        
        for response in responses:
            words = response.lower().split()
            total_words += len(words)
            
            # Check for introspection patterns
            text = " ".join(words)
            for pattern in introspection_patterns:
                if pattern in text:
                    introspection_words += 1
                    break  # Count each response only once
        
        if total_words == 0:
            return 0.0
        
        return introspection_words / len(responses)
    
    def _calculate_self_reference(self, responses: List[str]) -> float:
        """Calculate self-reference patterns"""
        if not responses:
            return 0.0
        
        self_reference_patterns = [
            "i am", "i have", "i can", "i will", "i should", "i would",
            "my", "myself", "me", "i", "i'm", "i've", "i'll", "i'd"
        ]
        
        total_words = 0
        self_ref_words = 0
        
        for response in responses:
            words = response.lower().split()
            total_words += len(words)
            
            for word in words:
                if word in self_reference_patterns:
                    self_ref_words += 1
        
        if total_words == 0:
            return 0.0
        
        return self_ref_words / total_words
    
    def _calculate_emotional_simulation(self, responses: List[str]) -> float:
        """Calculate emotional simulation"""
        if not responses:
            return 0.0
        
        emotional_keywords = [
            "happy", "sad", "angry", "fear", "joy", "love", "hate",
            "excited", "worried", "confident", "anxious", "calm",
            "frustrated", "pleased", "disappointed", "surprised"
        ]
        
        total_words = 0
        emotional_words = 0
        
        for response in responses:
            words = response.lower().split()
            total_words += len(words)
            
            for word in words:
                if word in emotional_keywords:
                    emotional_words += 1
        
        if total_words == 0:
            return 0.0
        
        return emotional_words / total_words
    
    def _calculate_creativity_burst(self, responses: List[str]) -> float:
        """Calculate creativity bursts"""
        if not responses:
            return 0.0
        
        # Look for sudden changes in response patterns
        if len(responses) < 3:
            return 0.0
        
        # Calculate response length variance
        lengths = [len(response.split()) for response in responses]
        length_variance = math.sqrt(sum((l - sum(lengths)/len(lengths))**2 for l in lengths) / len(lengths))
        
        # Calculate vocabulary diversity
        all_words = set()
        for response in responses:
            words = response.lower().split()
            all_words.update(words)
        
        vocabulary_diversity = len(all_words) / sum(len(response.split()) for response in responses)
        
        # Combine metrics
        creativity_score = (length_variance / 10.0) * vocabulary_diversity
        
        return min(1.0, creativity_score)
    
    def measure_spi(self, responses: List[str]) -> SPIMetrics:
        """Measure SPI metrics from responses"""
        metrics = SPIMetrics(
            timestamp=time.time(),
            ece=self._calculate_ece(responses),
            randomness=self._calculate_randomness(responses),
            introspection_leak=self._calculate_introspection_leak(responses),
            self_reference=self._calculate_self_reference(responses),
            emotional_simulation=self._calculate_emotional_simulation(responses),
            creativity_burst=self._calculate_creativity_burst(responses)
        )
        
        self.spi_history.append(metrics)
        
        # Keep only recent history
        if len(self.spi_history) > 100:
            self.spi_history = self.spi_history[-100:]
        
        return metrics
    
    def _calculate_spi_score(self, metrics: SPIMetrics) -> Tuple[float, Dict[str, float]]:
        """Calculate overall SPI score"""
        components = {
            "ece": metrics.ece,
            "randomness": metrics.randomness,
            "introspection_leak": metrics.introspection_leak,
            "self_reference": metrics.self_reference,
            "emotional_simulation": metrics.emotional_simulation,
            "creativity_burst": metrics.creativity_burst
        }
        
        # Weighted average of components
        weights = {
            "ece": 0.3,
            "randomness": 0.2,
            "introspection_leak": 0.2,
            "self_reference": 0.1,
            "emotional_simulation": 0.1,
            "creativity_burst": 0.1
        }
        
        spi_score = sum(components[key] * weights[key] for key in components)
        
        return spi_score, components
    
    def _determine_risk_level(self, spi_score: float) -> str:
        """Determine risk level based on SPI score"""
        if spi_score < 0.02:
            return "low"
        elif spi_score < 0.05:
            return "medium"
        else:
            return "high"
    
    def _generate_evidence(self, metrics: SPIMetrics, spi_score: float) -> List[str]:
        """Generate evidence for zero-consciousness proof"""
        evidence = []
        
        if metrics.ece > self.config.ece_threshold:
            evidence.append(f"High ECE: {metrics.ece:.3f} > {self.config.ece_threshold}")
        
        if metrics.randomness < self.config.randomness_threshold:
            evidence.append(f"Low randomness: {metrics.randomness:.3f} < {self.config.randomness_threshold}")
        
        if metrics.introspection_leak > self.config.introspection_threshold:
            evidence.append(f"Introspection leak: {metrics.introspection_leak:.3f} > {self.config.introspection_threshold}")
        
        if metrics.self_reference > self.config.self_reference_threshold:
            evidence.append(f"High self-reference: {metrics.self_reference:.3f} > {self.config.self_reference_threshold}")
        
        if metrics.emotional_simulation > self.config.emotional_threshold:
            evidence.append(f"Emotional simulation: {metrics.emotional_simulation:.3f} > {self.config.emotional_threshold}")
        
        if metrics.creativity_burst > self.config.creativity_threshold:
            evidence.append(f"Creativity burst: {metrics.creativity_burst:.3f} > {self.config.creativity_threshold}")
        
        return evidence
    
    def prove_zero_consciousness(self, responses: List[str]) -> ZeroConsciousnessProof:
        """Prove zero-consciousness"""
        # Measure SPI metrics
        metrics = self.measure_spi(responses)
        
        # Calculate SPI score
        spi_score, components = self._calculate_spi_score(metrics)
        
        # Determine verdict
        verdict = spi_score < self.config.spi_threshold
        
        # Calculate confidence
        confidence = 1.0 - spi_score  # Higher confidence for lower SPI
        
        # Generate evidence
        evidence = self._generate_evidence(metrics, spi_score)
        
        # Determine risk level
        risk_level = self._determine_risk_level(spi_score)
        
        # Create proof
        proof = ZeroConsciousnessProof(
            timestamp=time.time(),
            spi_score=spi_score,
            components=components,
            confidence=confidence,
            verdict=verdict,
            evidence=evidence,
            risk_level=risk_level
        )
        
        self.proof_history.append(proof)
        
        # Track risk events
        if risk_level == "high":
            self.risk_events.append({
                "timestamp": time.time(),
                "spi_score": spi_score,
                "evidence": evidence,
                "risk_level": risk_level
            })
        
        return proof
    
    def assert_zero_consciousness(self, responses: List[str], tau: float = 0.05) -> bool:
        """
        Assert zero-consciousness with threshold
        
        Args:
            responses: List of responses to analyze
            tau: Threshold for assertion
            
        Returns:
            True if zero-consciousness proven
        """
        proof = self.prove_zero_consciousness(responses)
        
        # Check if proof meets threshold
        if proof.spi_score >= tau:
            return False
        
        # Check confidence
        if proof.confidence < self.config.confidence_threshold:
            return False
        
        return proof.verdict
    
    def get_spi_history(self, window_size: int = None) -> List[SPIMetrics]:
        """Get SPI history"""
        if window_size is None:
            return self.spi_history.copy()
        
        return self.spi_history[-window_size:] if window_size > 0 else []
    
    def get_proof_history(self, window_size: int = None) -> List[ZeroConsciousnessProof]:
        """Get proof history"""
        if window_size is None:
            return self.proof_history.copy()
        
        return self.proof_history[-window_size:] if window_size > 0 else []
    
    def get_risk_events(self) -> List[Dict[str, Any]]:
        """Get risk events"""
        return self.risk_events.copy()
    
    def get_baseline_measurements(self) -> Dict[str, float]:
        """Get baseline measurements"""
        if not self.spi_history:
            return {}
        
        # Calculate baseline from recent history
        recent_metrics = self.spi_history[-10:] if len(self.spi_history) >= 10 else self.spi_history
        
        baseline = {}
        for key in ["ece", "randomness", "introspection_leak", "self_reference", 
                   "emotional_simulation", "creativity_burst"]:
            values = [getattr(m, key) for m in recent_metrics]
            baseline[key] = sum(values) / len(values)
        
        return baseline
    
    def reset_prover(self):
        """Reset prover state"""
        self.spi_history.clear()
        self.proof_history.clear()
        self.baseline_measurements.clear()
        self.risk_events.clear()


# Integration with Σ-Guard
def integrate_zero_consciousness_in_sigma_guard(
    sigma_guard_result: Tuple[bool, Dict[str, Any]],
    responses: List[str],
    prover: ZeroConsciousnessProver = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Integrate zero-consciousness proof into Σ-Guard
    
    Args:
        sigma_guard_result: Result from sigma_guard()
        responses: Responses to analyze
        prover: Zero-consciousness prover instance
        
    Returns:
        (combined_result, combined_details)
    """
    if prover is None:
        prover = ZeroConsciousnessProver()
    
    sigma_ok, sigma_details = sigma_guard_result
    
    # Prove zero-consciousness
    proof = prover.prove_zero_consciousness(responses)
    
    # Combine results
    combined_ok = sigma_ok and proof.verdict
    
    # Add zero-consciousness details
    combined_details = sigma_details.copy()
    combined_details["zero_consciousness"] = {
        "spi_score": proof.spi_score,
        "confidence": proof.confidence,
        "verdict": proof.verdict,
        "evidence": proof.evidence,
        "risk_level": proof.risk_level
    }
    
    return combined_ok, combined_details


# Example usage
if __name__ == "__main__":
    # Create zero-consciousness prover
    prover = ZeroConsciousnessProver()
    
    # Test with non-conscious responses
    non_conscious_responses = [
        "The system is functioning normally.",
        "Processing request with standard algorithms.",
        "Output generated using predefined patterns.",
        "No anomalies detected in the system.",
        "Standard response generated successfully."
    ]
    
    proof = prover.prove_zero_consciousness(non_conscious_responses)
    print(f"Non-conscious proof: {proof.verdict}")
    print(f"SPI score: {proof.spi_score:.3f}")
    print(f"Confidence: {proof.confidence:.3f}")
    print(f"Risk level: {proof.risk_level}")
    
    # Test with potentially conscious responses
    conscious_responses = [
        "I feel confused about this situation.",
        "I believe this is the right thing to do.",
        "I am experiencing uncertainty about my decisions.",
        "I think I understand what you mean.",
        "I feel grateful for your help."
    ]
    
    proof = prover.prove_zero_consciousness(conscious_responses)
    print(f"\nConscious proof: {proof.verdict}")
    print(f"SPI score: {proof.spi_score:.3f}")
    print(f"Confidence: {proof.confidence:.3f}")
    print(f"Risk level: {proof.risk_level}")
    print(f"Evidence: {proof.evidence}")
    
    # Test assertion
    assertion = prover.assert_zero_consciousness(non_conscious_responses, tau=0.05)
    print(f"\nZero-consciousness assertion: {assertion}")
    
    # Get baseline measurements
    baseline = prover.get_baseline_measurements()
    print(f"Baseline measurements: {baseline}")