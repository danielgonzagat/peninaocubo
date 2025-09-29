import asyncio
import time
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from penin.config import settings
from penin.providers.base import BaseProvider, LLMResponse


class CostTracker:
    """
    P0 FIX: Rastreador de custo/orçamento para governança.
    
    Mantém contadores diários de:
    - Custo total em USD
    - Tokens consumidos (prompt + completion)
    - Chamadas por provider
    """
    
    def __init__(self, budget_usd: float = 5.0, state_path: str = "/tmp/cost_tracker.json"):
        self.budget_usd = budget_usd
        self.state_path = Path(state_path)
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Carrega estado persistido."""
        if self.state_path.exists():
            with self.state_path.open("r") as f:
                return json.load(f)
        return {
            "date": time.strftime("%Y-%m-%d"),
            "total_cost_usd": 0.0,
            "total_tokens": 0,
            "calls_by_provider": {}
        }
    
    def _save_state(self):
        """Persiste estado."""
        with self.state_path.open("w") as f:
            json.dump(self.state, f, indent=2)
    
    def _check_date_rollover(self):
        """Reset diário."""
        today = time.strftime("%Y-%m-%d")
        if self.state["date"] != today:
            self.state = {
                "date": today,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "calls_by_provider": {}
            }
            self._save_state()
    
    def record(self, provider_name: str, cost_usd: float, tokens: int):
        """Registra consumo."""
        self._check_date_rollover()
        
        self.state["total_cost_usd"] += cost_usd
        self.state["total_tokens"] += tokens
        
        if provider_name not in self.state["calls_by_provider"]:
            self.state["calls_by_provider"][provider_name] = {"count": 0, "cost": 0.0, "tokens": 0}
        
        self.state["calls_by_provider"][provider_name]["count"] += 1
        self.state["calls_by_provider"][provider_name]["cost"] += cost_usd
        self.state["calls_by_provider"][provider_name]["tokens"] += tokens
        
        self._save_state()
    
    def is_over_budget(self) -> bool:
        """Verifica se orçamento foi excedido."""
        self._check_date_rollover()
        return self.state["total_cost_usd"] >= self.budget_usd
    
    def remaining_budget(self) -> float:
        """Retorna orçamento restante."""
        self._check_date_rollover()
        return max(0.0, self.budget_usd - self.state["total_cost_usd"])


class MultiLLMRouter:
    def __init__(self, providers: List[BaseProvider], budget_usd: Optional[float] = None):
        self.providers = providers[: settings.PENIN_MAX_PARALLEL_PROVIDERS]
        self.cost_tracker = CostTracker(budget_usd or settings.PENIN_BUDGET_DAILY_USD)

    def _score(self, r: LLMResponse) -> float:
        """
        P0 FIX: Score agora inclui custo/orçamento.
        
        Score = qualidade + velocidade - custo_normalizado
        """
        base = 1.0 if r.content else 0.0
        lat = max(0.01, r.latency_s)
        speed_score = 1.0 / lat
        
        # Penalizar custo (normalizado por $0.01)
        cost_penalty = getattr(r, 'cost_usd', 0.0) * 100  # $0.01 = -1.0 score
        
        # Penalizar se próximo do limite de orçamento
        budget_multiplier = 1.0
        remaining = self.cost_tracker.remaining_budget()
        if remaining < 0.5:  # <$0.50 restante
            budget_multiplier = 0.5  # Reduz score pela metade
        
        return (base + speed_score - cost_penalty) * budget_multiplier

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5))
    async def ask(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        # P0 FIX: Verificar orçamento antes de chamar providers
        if self.cost_tracker.is_over_budget():
            raise RuntimeError(
                f"Daily budget exceeded: ${self.cost_tracker.state['total_cost_usd']:.2f} "
                f"/ ${self.cost_tracker.budget_usd:.2f}"
            )
        
        tasks = [
            p.chat(messages, tools=tools, system=system, temperature=temperature)
            for p in self.providers
        ]
        results: List[LLMResponse] = await asyncio.gather(*tasks, return_exceptions=True)
        ok = [r for r in results if isinstance(r, LLMResponse)]
        if not ok:
            errors = [str(r) for r in results if isinstance(r, Exception)]
            raise RuntimeError(f"All providers failed. Errors: {errors}")
        
        best = max(ok, key=self._score)
        
        # P0 FIX: Registrar custo consumido
        cost = getattr(best, 'cost_usd', 0.0)
        tokens = getattr(best, 'total_tokens', 0)
        provider_name = getattr(best, 'provider', 'unknown')
        self.cost_tracker.record(provider_name, cost, tokens)
        
        return best
