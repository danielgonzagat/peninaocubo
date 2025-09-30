def ema_grad(g_prev: float, g_now: float, beta: float = 0.9) -> float:
    return beta * g_prev + (1 - beta) * g_now

