class OnlineTuner:
    """Simple AdaGrad-like online tuner for step size adaptation."""

    def __init__(self, eta0: float = 0.1):
        self.g2 = 1e-9
        self.eta0 = eta0

    def step(self, grad: float) -> float:
        self.g2 += grad * grad
        eta = self.eta0 / (1.0 + self.g2) ** 0.5
        return -eta * grad
