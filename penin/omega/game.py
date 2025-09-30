def ema_grad(prev_grad: float, current_grad: float, beta: float = 0.9) -> float:
    return float(beta) * float(prev_grad) + (1.0 - float(beta)) * float(current_grad)
