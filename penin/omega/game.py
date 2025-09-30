"""
GAME - Gradients with Exponential Moving Average
Implements gradient tracking with memory for stable evolution
"""

from typing import Dict, List, Optional, Tuple
import math


class GradientTracker:
    """Track gradients with exponential moving average"""
    
    def __init__(self, beta: float = 0.9):
        """
        Initialize gradient tracker
        
        Parameters:
        -----------
        beta: EMA decay factor (0 < beta < 1)
        """
        self.beta = beta
        self.gradients: Dict[str, float] = {}
        self.squared_gradients: Dict[str, float] = {}  # For adaptive learning
        self.step_count: Dict[str, int] = {}
    
    def update(self, param_name: str, gradient: float) -> float:
        """
        Update gradient with EMA and return smoothed value
        
        Parameters:
        -----------
        param_name: Parameter name
        gradient: Current gradient value
        
        Returns:
        --------
        Smoothed gradient value
        """
        if param_name not in self.gradients:
            self.gradients[param_name] = gradient
            self.squared_gradients[param_name] = gradient ** 2
            self.step_count[param_name] = 1
            return gradient
        
        # Update EMA
        self.gradients[param_name] = ema_grad(
            self.gradients[param_name],
            gradient,
            self.beta
        )
        
        # Update squared gradients (for adaptive methods)
        self.squared_gradients[param_name] = (
            self.beta * self.squared_gradients[param_name] +
            (1 - self.beta) * gradient ** 2
        )
        
        self.step_count[param_name] += 1
        
        return self.gradients[param_name]
    
    def get_adaptive_lr(self, param_name: str, base_lr: float, epsilon: float = 1e-8) -> float:
        """
        Get adaptive learning rate based on gradient history (Adam-like)
        
        Parameters:
        -----------
        param_name: Parameter name
        base_lr: Base learning rate
        epsilon: Small constant for numerical stability
        
        Returns:
        --------
        Adaptive learning rate
        """
        if param_name not in self.squared_gradients:
            return base_lr
        
        # Bias correction
        t = self.step_count[param_name]
        bias_correction1 = 1 - self.beta ** t
        bias_correction2 = 1 - self.beta ** t  # Using same beta for simplicity
        
        # Corrected estimates
        m_hat = self.gradients[param_name] / bias_correction1
        v_hat = self.squared_gradients[param_name] / bias_correction2
        
        # Adaptive learning rate
        return base_lr / (math.sqrt(v_hat) + epsilon)
    
    def get_momentum(self, param_name: str) -> float:
        """
        Get momentum-adjusted gradient
        
        Parameters:
        -----------
        param_name: Parameter name
        
        Returns:
        --------
        Momentum-adjusted gradient
        """
        return self.gradients.get(param_name, 0.0)
    
    def reset(self, param_name: Optional[str] = None):
        """
        Reset gradient history
        
        Parameters:
        -----------
        param_name: Optional parameter to reset (None = reset all)
        """
        if param_name is None:
            self.gradients.clear()
            self.squared_gradients.clear()
            self.step_count.clear()
        else:
            self.gradients.pop(param_name, None)
            self.squared_gradients.pop(param_name, None)
            self.step_count.pop(param_name, None)


def ema_grad(g_prev: float, g_now: float, beta: float = 0.9) -> float:
    """
    Compute exponential moving average of gradients
    
    Parameters:
    -----------
    g_prev: Previous gradient value
    g_now: Current gradient value
    beta: Decay factor (0 < beta < 1)
    
    Returns:
    --------
    Smoothed gradient value
    """
    return beta * g_prev + (1 - beta) * g_now


def compute_gradient_norm(gradients: Dict[str, float]) -> float:
    """
    Compute L2 norm of gradient vector
    
    Parameters:
    -----------
    gradients: Dictionary of gradients
    
    Returns:
    --------
    L2 norm
    """
    if not gradients:
        return 0.0
    
    sum_squared = sum(g ** 2 for g in gradients.values())
    return math.sqrt(sum_squared)


def clip_gradients(
    gradients: Dict[str, float],
    max_norm: float = 1.0
) -> Tuple[Dict[str, float], float]:
    """
    Clip gradients by global norm
    
    Parameters:
    -----------
    gradients: Dictionary of gradients
    max_norm: Maximum allowed norm
    
    Returns:
    --------
    (clipped_gradients, original_norm)
    """
    norm = compute_gradient_norm(gradients)
    
    if norm <= max_norm or norm == 0:
        return gradients, norm
    
    # Scale gradients
    scale = max_norm / norm
    clipped = {k: v * scale for k, v in gradients.items()}
    
    return clipped, norm


def gradient_similarity(grad1: Dict[str, float], grad2: Dict[str, float]) -> float:
    """
    Compute cosine similarity between two gradient vectors
    
    Parameters:
    -----------
    grad1: First gradient dictionary
    grad2: Second gradient dictionary
    
    Returns:
    --------
    Cosine similarity [-1, 1]
    """
    # Get common keys
    common_keys = set(grad1.keys()) & set(grad2.keys())
    
    if not common_keys:
        return 0.0
    
    # Compute dot product and norms
    dot_product = sum(grad1[k] * grad2[k] for k in common_keys)
    norm1 = math.sqrt(sum(grad1[k] ** 2 for k in common_keys))
    norm2 = math.sqrt(sum(grad2[k] ** 2 for k in common_keys))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def gradient_variance(history: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Compute variance of gradients over history
    
    Parameters:
    -----------
    history: List of gradient dictionaries
    
    Returns:
    --------
    Variance per parameter
    """
    if len(history) < 2:
        return {}
    
    # Collect all parameter names
    all_params = set()
    for grad_dict in history:
        all_params.update(grad_dict.keys())
    
    variances = {}
    
    for param in all_params:
        values = [g.get(param, 0.0) for g in history]
        
        if len(values) < 2:
            continue
        
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        variances[param] = variance
    
    return variances


def adaptive_beta(
    gradient_variance: float,
    min_beta: float = 0.5,
    max_beta: float = 0.99
) -> float:
    """
    Compute adaptive beta based on gradient variance
    High variance -> lower beta (less memory)
    Low variance -> higher beta (more memory)
    
    Parameters:
    -----------
    gradient_variance: Variance of recent gradients
    min_beta: Minimum beta value
    max_beta: Maximum beta value
    
    Returns:
    --------
    Adaptive beta value
    """
    # Map variance to beta (inverse relationship)
    # High variance (>1.0) -> min_beta
    # Low variance (<0.01) -> max_beta
    
    if gradient_variance <= 0.01:
        return max_beta
    elif gradient_variance >= 1.0:
        return min_beta
    else:
        # Log scale interpolation
        log_var = math.log10(gradient_variance)
        # log_var ranges from -2 (0.01) to 0 (1.0)
        # Map to beta range
        t = (log_var + 2) / 2  # Normalize to [0, 1]
        return min_beta + (max_beta - min_beta) * (1 - t)


class AdaptiveGAME:
    """Adaptive GAME with variance-based beta adjustment"""
    
    def __init__(self, initial_beta: float = 0.9):
        self.tracker = GradientTracker(initial_beta)
        self.history: List[Dict[str, float]] = []
        self.beta = initial_beta
    
    def step(self, gradients: Dict[str, float]) -> Dict[str, float]:
        """
        Process gradients with adaptive GAME
        
        Parameters:
        -----------
        gradients: Current gradients
        
        Returns:
        --------
        Processed gradients
        """
        # Add to history
        self.history.append(gradients.copy())
        if len(self.history) > 20:
            self.history.pop(0)
        
        # Compute variance and update beta
        if len(self.history) >= 5:
            variances = gradient_variance(self.history[-5:])
            if variances:
                avg_variance = sum(variances.values()) / len(variances)
                self.beta = adaptive_beta(avg_variance)
                self.tracker.beta = self.beta
        
        # Update gradients with EMA
        smoothed = {}
        for param, grad in gradients.items():
            smoothed[param] = self.tracker.update(param, grad)
        
        return smoothed
    
    def get_adaptive_lr(self, param: str, base_lr: float) -> float:
        """Get adaptive learning rate for parameter"""
        return self.tracker.get_adaptive_lr(param, base_lr)


def quick_test():
    """Quick test of GAME system"""
    # Test basic EMA
    g1 = ema_grad(0.0, 1.0, beta=0.9)
    g2 = ema_grad(g1, 0.5, beta=0.9)
    g3 = ema_grad(g2, 0.2, beta=0.9)
    
    # Test gradient tracker
    tracker = GradientTracker(beta=0.9)
    
    # Simulate gradient updates
    for i in range(5):
        grad = 1.0 / (i + 1)  # Decreasing gradients
        smoothed = tracker.update("param1", grad)
    
    adaptive_lr = tracker.get_adaptive_lr("param1", base_lr=0.01)
    
    # Test gradient clipping
    grads = {"p1": 2.0, "p2": 3.0, "p3": 4.0}
    clipped, original_norm = clip_gradients(grads, max_norm=2.0)
    
    # Test adaptive GAME
    game = AdaptiveGAME(initial_beta=0.9)
    
    # Simulate varying gradients
    gradient_sequence = [
        {"p1": 0.1, "p2": 0.2},
        {"p1": 0.15, "p2": 0.18},
        {"p1": 0.8, "p2": -0.5},  # Sudden change
        {"p1": 0.12, "p2": 0.19},
        {"p1": 0.11, "p2": 0.21}
    ]
    
    final_grads = None
    for grads in gradient_sequence:
        final_grads = game.step(grads)
    
    return {
        "ema_sequence": [g1, g2, g3],
        "final_smoothed": tracker.gradients.get("param1", 0),
        "adaptive_lr": adaptive_lr,
        "original_norm": original_norm,
        "clipped_norm": compute_gradient_norm(clipped),
        "adaptive_beta": game.beta,
        "final_grads": final_grads
    }


if __name__ == "__main__":
    result = quick_test()
    print("GAME (Gradient Averaging with Memory) Test:")
    print(f"  EMA sequence: {[f'{g:.3f}' for g in result['ema_sequence']]}")
    print(f"  Final smoothed gradient: {result['final_smoothed']:.3f}")
    print(f"  Adaptive learning rate: {result['adaptive_lr']:.6f}")
    print(f"  Gradient clipping: {result['original_norm']:.2f} → {result['clipped_norm']:.2f}")
    print(f"  Adaptive beta: {result['adaptive_beta']:.3f}")
    print(f"  Final gradients: {result['final_grads']}")