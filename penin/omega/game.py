"""
GAME - Gradientes com Memória Exponencial
==========================================

EMA de gradientes para aprendizado online.
"""


def ema_grad(g_prev: float, g_now: float, beta: float = 0.9) -> float:
    """
    EMA de gradiente.
    
    Args:
        g_prev: Gradiente anterior (EMA)
        g_now: Gradiente atual
        beta: Fator de decaimento
        
    Returns:
        Novo EMA do gradiente
    """
    return beta * g_prev + (1.0 - beta) * g_now


class GAMEOptimizer:
    """Otimizador GAME (Gradient with Adaptive Memory Exponential)"""
    
    def __init__(self, beta: float = 0.9, lr: float = 0.01):
        self.beta = beta
        self.lr = lr
        self.ema = 0.0
    
    def step(self, gradient: float) -> float:
        """
        Passo de otimização.
        
        Args:
            gradient: Gradiente atual
            
        Returns:
            Update (delta para aplicar)
        """
        self.ema = ema_grad(self.ema, gradient, self.beta)
        return -self.lr * self.ema
    
    def reset(self) -> None:
        """Reseta EMA"""
        self.ema = 0.0