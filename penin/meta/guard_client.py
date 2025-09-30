import requests
from typing import Dict, Any


class GuardClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8011"):
        self.base = base_url

    def health(self) -> bool:
        r = requests.get(f"{self.base}/health", timeout=2)
        return r.ok and r.json().get("ok", False)

    def eval(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        r = requests.post(f"{self.base}/sigma_guard/eval", json=metrics, timeout=5)
        r.raise_for_status()
        return r.json()


class SRClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8012"):
        self.base = base_url

    def health(self) -> bool:
        r = requests.get(f"{self.base}/health", timeout=2)
        return r.ok and r.json().get("ok", False)

    def eval(self, ece: float, rho: float, risk: float, dlinf_dc: float) -> Dict[str, float]:
        r = requests.post(
            f"{self.base}/sr/eval",
            json={"ece": ece, "rho": rho, "risk": risk, "dlinf_dc": dlinf_dc},
            timeout=5,
        )
        r.raise_for_status()
        return r.json()

