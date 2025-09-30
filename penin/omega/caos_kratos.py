"""
CAOS-KRATOS - Calibrated exploration mode for PENIN-Ω
Enhanced CAOS⁺ with exploration factor for controlled discovery
"""

from .caos import phi_caos


def phi_kratos(
    C: float,
    A: float, 
    O: float,
    S: float,
    exploration_factor: float = 2.0,
    **kwargs
) -> float:
    """
    CAOS-KRATOS: Enhanced exploration through amplified O×S
    
    Reinforces impact of (O×S) while maintaining saturation stability.
    Used only in exploration mode with Σ-Guard fail-closed protection.
    
    Parameters:
    -----------
    C: Coherence/Consistency [0, 1]
    A: Awareness/Attention [0, 1]
    O: Openness to exploration [0, 1]
    S: Stability/Safety [0, 1]
    exploration_factor: Amplification for O and S (default: 2.0)
    **kwargs: Additional parameters passed to phi_caos
    
    Returns:
    --------
    Enhanced phi value for exploration
    """
    # Amplify openness and stability with exploration factor
    # This increases the impact of exploration while maintaining bounds
    O_enhanced = min(1.0, O ** (1.0 / exploration_factor))
    S_enhanced = min(1.0, S ** (1.0 / exploration_factor))
    
    # Call base phi_caos with enhanced values
    return phi_caos(C, A, O_enhanced, S_enhanced, **kwargs)


def adaptive_exploration_factor(
    current_performance: float,
    target_performance: float,
    min_factor: float = 1.0,
    max_factor: float = 3.0
) -> float:
    """
    Compute adaptive exploration factor based on performance gap
    
    Parameters:
    -----------
    current_performance: Current system performance [0, 1]
    target_performance: Target performance level [0, 1]
    min_factor: Minimum exploration factor
    max_factor: Maximum exploration factor
    
    Returns:
    --------
    Adaptive exploration factor
    """
    # Larger gap = more exploration needed
    gap = max(0, target_performance - current_performance)
    
    # Linear interpolation between min and max based on gap
    factor = min_factor + (max_factor - min_factor) * gap
    
    return min(max_factor, max(min_factor, factor))


def kratos_gate(
    phi_kratos_val: float,
    phi_base_val: float,
    safety_ratio: float = 1.5
) -> bool:
    """
    Safety gate for KRATOS mode
    
    Ensures KRATOS exploration doesn't exceed safety bounds.
    
    Parameters:
    -----------
    phi_kratos_val: KRATOS-enhanced phi value
    phi_base_val: Base CAOS⁺ phi value
    safety_ratio: Maximum allowed amplification ratio
    
    Returns:
    --------
    True if safe to proceed with KRATOS, False otherwise
    """
    if phi_base_val <= 0:
        return False
    
    ratio = phi_kratos_val / phi_base_val
    return ratio <= safety_ratio


def compute_exploration_metrics(
    C: float,
    A: float,
    O: float,
    S: float,
    exploration_factor: float = 2.0,
    **kwargs
) -> dict:
    """
    Compute full exploration metrics for monitoring
    
    Returns:
    --------
    Dictionary with base phi, kratos phi, amplification, and safety status
    """
    # Compute base and enhanced values
    phi_base = phi_caos(C, A, O, S, **kwargs)
    phi_enhanced = phi_kratos(C, A, O, S, exploration_factor, **kwargs)
    
    # Check safety gate
    safe = kratos_gate(phi_enhanced, phi_base)
    
    # Compute amplification ratio
    amplification = phi_enhanced / phi_base if phi_base > 0 else 0.0
    
    return {
        "phi_base": phi_base,
        "phi_kratos": phi_enhanced,
        "amplification": amplification,
        "exploration_factor": exploration_factor,
        "safe": safe,
        "O_effective": min(1.0, O ** (1.0 / exploration_factor)),
        "S_effective": min(1.0, S ** (1.0 / exploration_factor))
    }


def quick_test():
    """Quick test of CAOS-KRATOS"""
    # Test parameters
    C, A, O, S = 0.7, 0.6, 0.8, 0.9
    
    # Compute metrics with different exploration factors
    results = []
    for factor in [1.0, 1.5, 2.0, 2.5, 3.0]:
        metrics = compute_exploration_metrics(
            C, A, O, S,
            exploration_factor=factor,
            kappa=25.0
        )
        results.append(metrics)
    
    # Test adaptive factor
    adaptive = adaptive_exploration_factor(
        current_performance=0.6,
        target_performance=0.9
    )
    
    return {
        "results": results,
        "adaptive_factor": adaptive
    }


if __name__ == "__main__":
    test = quick_test()
    print("CAOS-KRATOS Exploration Test:")
    print(f"Adaptive factor for 0.6→0.9 performance: {test['adaptive_factor']:.2f}")
    print("\nExploration factors and amplification:")
    for r in test['results']:
        print(f"  Factor {r['exploration_factor']:.1f}: "
              f"φ_base={r['phi_base']:.3f}, "
              f"φ_kratos={r['phi_kratos']:.3f}, "
              f"amp={r['amplification']:.2f}x, "
              f"safe={r['safe']}")