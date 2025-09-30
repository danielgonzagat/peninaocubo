"""
GAME - Gradient with Adaptive Memory Exponential
================================================

Implements EMA (exponential moving average) for gradients.
"""


def ema_grad(g_prev: float, g_now: float, beta: float = 0.9) -> float:
    """
    Compute EMA of gradients.
    
    Args:
        g_prev: Previous gradient
        g_now: Current gradient
        beta: EMA decay factor
        
    Returns:
        Smoothed gradient
    """
    return beta * g_prev + (1 - beta) * g_now


class GAMEOptimizer:
    """
    Gradient optimizer with exponential memory.
    
    Maintains EMA of gradients for smoother updates.
    """
    
    def __init__(self, beta: float = 0.9):
        self.beta = beta
        self.grad_ema: float = 0.0
        self.steps: int = 0
        
        print(f"📈 GAME Optimizer initialized (beta={beta})")
    
    def step(self, gradient: float) -> float:
        """
        Update with new gradient.
        
        Args:
            gradient: Current gradient
            
        Returns:
            Smoothed gradient
        """
        self.grad_ema = ema_grad(self.grad_ema, gradient, self.beta)
        self.steps += 1
        return self.grad_ema
    
    def get_stats(self) -> dict:
        """Get optimizer statistics"""
        return {
            "beta": self.beta,
            "grad_ema": self.grad_ema,
            "steps": self.steps
        }


# Quick test
def quick_game_test():
    """Quick test of GAME optimizer"""
    opt = GAMEOptimizer(beta=0.9)
    
    gradients = [1.0, 0.8, 1.2, 0.9, 1.1]
    
    print("\n📈 Gradient updates:")
    for g in gradients:
        smoothed = opt.step(g)
        print(f"   g={g:.2f} → smoothed={smoothed:.4f}")
    
    stats = opt.get_stats()
    print(f"\n📊 Stats: {stats}")
    
    return opt