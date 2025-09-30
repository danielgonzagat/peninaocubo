# penin/omega/game.py
"""
GAME - Gradientes com Memória Exponencial
==========================================

Algoritmo de gradientes com memória exponencial para otimização adaptativa.
"""


def ema_grad(g_prev: float, g_now: float, beta: float = 0.9) -> float:
    """Exponential Moving Average de gradientes"""
    return beta * g_prev + (1 - beta) * g_now


def adaptive_step_size(grad_history: list, base_lr: float = 0.01) -> float:
    """Calcula step size adaptativo baseado no histórico"""
    if len(grad_history) < 2:
        return base_lr
    
    # Variância dos gradientes recentes
    recent = grad_history[-5:]
    mean_grad = sum(recent) / len(recent)
    variance = sum((g - mean_grad) ** 2 for g in recent) / len(recent)
    
    # Step size inversamente proporcional à variância
    return base_lr / (1 + variance)


class GAMEOptimizer:
    """Otimizador GAME com memória exponencial"""
    
    def __init__(self, beta: float = 0.9, base_lr: float = 0.01):
        self.beta = beta
        self.base_lr = base_lr
        self.grad_ema = 0.0
        self.grad_history = []
    
    def step(self, gradient: float) -> float:
        """Executa passo de otimização"""
        # Atualizar EMA
        self.grad_ema = ema_grad(self.grad_ema, gradient, self.beta)
        
        # Adicionar ao histórico
        self.grad_history.append(gradient)
        if len(self.grad_history) > 20:  # Manter apenas últimos 20
            self.grad_history.pop(0)
        
        # Calcular step size adaptativo
        step_size = adaptive_step_size(self.grad_history, self.base_lr)
        
        return -step_size * self.grad_ema  # Direção oposta ao gradiente