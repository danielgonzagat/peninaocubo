"""
Enhanced Multi-LLM Router with Advanced Features
================================================

Improvements over base router:
- Better async/await handling
- Enhanced cost tracking with persistence
- Provider health monitoring
- Circuit breaker pattern
- Request queuing and rate limiting
- Detailed metrics and analytics
"""

import asyncio
import time
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import deque
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from penin.config import settings
    from penin.providers.base import BaseProvider, LLMResponse
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, '/workspace')
    from penin.config import settings
    from penin.providers.base import BaseProvider, LLMResponse


class ProviderHealth(Enum):
    """Provider health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ProviderStats:
    """Statistics for a provider"""
    provider_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    avg_latency_s: float = 0.0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    consecutive_failures: int = 0
    health: ProviderHealth = ProviderHealth.HEALTHY
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            **asdict(self),
            "health": self.health.value,
            "success_rate": self.success_rate()
        }


@dataclass
class BudgetTracker:
    """Track daily budget usage"""
    daily_budget_usd: float
    current_spend_usd: float = 0.0
    total_tokens: int = 0
    request_count: int = 0
    last_reset: date = None
    spend_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.last_reset is None:
            self.last_reset = date.today()
        if self.spend_history is None:
            self.spend_history = []
    
    def reset_if_needed(self) -> bool:
        """Reset budget if new day"""
        today = date.today()
        if today > self.last_reset:
            # Save yesterday's stats
            self.spend_history.append({
                "date": self.last_reset.isoformat(),
                "spend_usd": self.current_spend_usd,
                "tokens": self.total_tokens,
                "requests": self.request_count
            })
            
            # Keep only last 30 days
            if len(self.spend_history) > 30:
                self.spend_history = self.spend_history[-30:]
            
            # Reset counters
            self.current_spend_usd = 0.0
            self.total_tokens = 0
            self.request_count = 0
            self.last_reset = today
            return True
        return False
    
    def add_usage(self, cost_usd: float, tokens: int = 0):
        """Add usage to tracker"""
        self.reset_if_needed()
        self.current_spend_usd += cost_usd
        self.total_tokens += tokens
        self.request_count += 1
    
    def is_budget_exceeded(self) -> bool:
        """Check if budget is exceeded"""
        self.reset_if_needed()
        return self.current_spend_usd >= self.daily_budget_usd
    
    def remaining_budget(self) -> float:
        """Get remaining budget"""
        self.reset_if_needed()
        return max(0.0, self.daily_budget_usd - self.current_spend_usd)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        self.reset_if_needed()
        return {
            "daily_budget_usd": self.daily_budget_usd,
            "current_spend_usd": self.current_spend_usd,
            "remaining_usd": self.remaining_budget(),
            "total_tokens": self.total_tokens,
            "request_count": self.request_count,
            "last_reset": self.last_reset.isoformat(),
            "usage_percentage": (self.current_spend_usd / self.daily_budget_usd) * 100,
            "budget_exceeded": self.is_budget_exceeded(),
            "recent_history": self.spend_history[-7:]  # Last 7 days
        }


class CircuitBreaker:
    """Circuit breaker for provider failures"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout_s: float = 60.0,
                 half_open_max_calls: int = 1):
        """
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout_s: Time to wait before trying again
            half_open_max_calls: Max calls in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_s
        self.half_open_max_calls = half_open_max_calls
        
        self.state = ProviderHealth.HEALTHY
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
    
    def record_success(self):
        """Record successful call"""
        self.failure_count = 0
        self.state = ProviderHealth.HEALTHY
        self.half_open_calls = 0
    
    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = ProviderHealth.CIRCUIT_OPEN
    
    def can_attempt(self) -> bool:
        """Check if can attempt call"""
        if self.state == ProviderHealth.HEALTHY:
            return True
        
        if self.state == ProviderHealth.CIRCUIT_OPEN:
            # Check if enough time has passed
            if (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = ProviderHealth.DEGRADED
                self.half_open_calls = 0
                return True
            return False
        
        # DEGRADED state - limited attempts
        if self.half_open_calls < self.half_open_max_calls:
            self.half_open_calls += 1
            return True
        return False
    
    def get_state(self) -> ProviderHealth:
        """Get current circuit breaker state"""
        return self.state


class EnhancedMultiLLMRouter:
    """
    Enhanced Multi-LLM router with:
    - Advanced cost tracking and budgeting
    - Provider health monitoring
    - Circuit breaker pattern
    - Request analytics
    - Persistent state
    """
    
    def __init__(
        self,
        providers: List[BaseProvider],
        daily_budget_usd: Optional[float] = None,
        cost_weight: float = 0.3,
        latency_weight: float = 0.3,
        quality_weight: float = 0.4,
        enable_circuit_breaker: bool = True,
        state_file: Optional[Path] = None
    ):
        """
        Args:
            providers: List of LLM providers
            daily_budget_usd: Daily budget limit
            cost_weight: Weight for cost in scoring
            latency_weight: Weight for latency in scoring
            quality_weight: Weight for quality in scoring
            enable_circuit_breaker: Enable circuit breaker pattern
            state_file: Path to persist state
        """
        self.providers = providers[:settings.PENIN_MAX_PARALLEL_PROVIDERS]
        self.cost_weight = cost_weight
        self.latency_weight = latency_weight
        self.quality_weight = quality_weight
        self.enable_circuit_breaker = enable_circuit_breaker
        self.state_file = state_file or Path.home() / ".penin_router_state.json"
        
        # Budget tracking
        self.budget_tracker = BudgetTracker(
            daily_budget_usd=daily_budget_usd or settings.PENIN_BUDGET_DAILY_USD
        )
        
        # Provider stats and circuit breakers
        self.provider_stats: Dict[str, ProviderStats] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        for provider in self.providers:
            provider_id = provider.provider_id
            self.provider_stats[provider_id] = ProviderStats(provider_id=provider_id)
            if enable_circuit_breaker:
                self.circuit_breakers[provider_id] = CircuitBreaker()
        
        # Request queue for rate limiting
        self.request_queue = deque(maxlen=1000)
        
        # Load persisted state
        self._load_state()
    
    def _save_state(self):
        """Save router state to disk"""
        try:
            state = {
                "budget_tracker": {
                    "current_spend_usd": self.budget_tracker.current_spend_usd,
                    "total_tokens": self.budget_tracker.total_tokens,
                    "request_count": self.budget_tracker.request_count,
                    "last_reset": self.budget_tracker.last_reset.isoformat(),
                    "spend_history": self.budget_tracker.spend_history
                },
                "provider_stats": {
                    pid: stats.to_dict() 
                    for pid, stats in self.provider_stats.items()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save router state: {e}")
    
    def _load_state(self):
        """Load router state from disk"""
        try:
            if not self.state_file.exists():
                return
            
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # Restore budget tracker
            bt = state.get("budget_tracker", {})
            if bt:
                self.budget_tracker.current_spend_usd = bt.get("current_spend_usd", 0.0)
                self.budget_tracker.total_tokens = bt.get("total_tokens", 0)
                self.budget_tracker.request_count = bt.get("request_count", 0)
                last_reset_str = bt.get("last_reset")
                if last_reset_str:
                    self.budget_tracker.last_reset = date.fromisoformat(last_reset_str)
                self.budget_tracker.spend_history = bt.get("spend_history", [])
            
            # Restore provider stats
            ps = state.get("provider_stats", {})
            for pid, stats_dict in ps.items():
                if pid in self.provider_stats:
                    # Update existing stats
                    stats = self.provider_stats[pid]
                    stats.total_requests = stats_dict.get("total_requests", 0)
                    stats.successful_requests = stats_dict.get("successful_requests", 0)
                    stats.failed_requests = stats_dict.get("failed_requests", 0)
                    stats.total_cost_usd = stats_dict.get("total_cost_usd", 0.0)
                    stats.total_tokens = stats_dict.get("total_tokens", 0)
        except Exception as e:
            print(f"Warning: Failed to load router state: {e}")
    
    def _score_response(self, response: LLMResponse, provider_stats: ProviderStats) -> float:
        """
        Score a response considering multiple factors
        
        Args:
            response: LLM response
            provider_stats: Provider statistics
            
        Returns:
            float: Score (higher is better)
        """
        # Base score for having content
        has_content = 1.0 if response.content else 0.0
        
        # Latency score (normalize to 0-1, lower is better)
        # Assume 5s is worst case
        latency_score = max(0.0, 1.0 - (response.latency_s / 5.0))
        
        # Cost score (normalize to 0-1, lower is better)
        # Use exponential decay for cost
        cost_score = 1.0 / (1.0 + response.cost_usd * 100)
        
        # Quality score based on provider success rate
        quality_score = provider_stats.success_rate()
        
        # Weighted combination
        final_score = (
            has_content * 0.3 +  # Must have content
            latency_score * self.latency_weight +
            cost_score * self.cost_weight +
            quality_score * self.quality_weight
        )
        
        return final_score
    
    async def _call_provider_with_tracking(
        self,
        provider: BaseProvider,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """Call provider with tracking and circuit breaker"""
        provider_id = provider.provider_id
        stats = self.provider_stats[provider_id]
        
        # Check circuit breaker
        if self.enable_circuit_breaker:
            breaker = self.circuit_breakers[provider_id]
            if not breaker.can_attempt():
                raise RuntimeError(f"Circuit breaker open for {provider_id}")
        
        try:
            # Call provider
            start_time = time.time()
            response = await provider.chat(messages, **kwargs)
            latency = time.time() - start_time
            
            # Update stats
            stats.total_requests += 1
            stats.successful_requests += 1
            stats.total_cost_usd += response.cost_usd
            stats.total_tokens += response.prompt_tokens + response.completion_tokens
            stats.last_success = time.time()
            stats.consecutive_failures = 0
            
            # Update avg latency (EMA)
            alpha = 0.2
            if stats.avg_latency_s == 0:
                stats.avg_latency_s = latency
            else:
                stats.avg_latency_s = (1 - alpha) * stats.avg_latency_s + alpha * latency
            
            # Update circuit breaker
            if self.enable_circuit_breaker:
                self.circuit_breakers[provider_id].record_success()
            
            # Update health
            if stats.success_rate() >= 0.95:
                stats.health = ProviderHealth.HEALTHY
            elif stats.success_rate() >= 0.80:
                stats.health = ProviderHealth.DEGRADED
            else:
                stats.health = ProviderHealth.UNHEALTHY
            
            return response
            
        except Exception as e:
            # Update failure stats
            stats.total_requests += 1
            stats.failed_requests += 1
            stats.last_failure = time.time()
            stats.consecutive_failures += 1
            
            # Update circuit breaker
            if self.enable_circuit_breaker:
                self.circuit_breakers[provider_id].record_failure()
            
            # Update health
            if stats.consecutive_failures >= 5:
                stats.health = ProviderHealth.CIRCUIT_OPEN
            elif stats.consecutive_failures >= 3:
                stats.health = ProviderHealth.UNHEALTHY
            elif stats.success_rate() < 0.95:
                stats.health = ProviderHealth.DEGRADED
            
            raise e
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5))
    async def ask(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        force_budget_override: bool = False,
    ) -> LLMResponse:
        """
        Ask all providers in parallel and return best response
        
        Args:
            messages: Chat messages
            system: System prompt
            tools: Tool definitions
            temperature: Sampling temperature
            force_budget_override: Force call even if budget exceeded
            
        Returns:
            LLMResponse: Best response
        """
        # Check budget
        if not force_budget_override and self.budget_tracker.is_budget_exceeded():
            raise RuntimeError(
                f"Daily budget exceeded: "
                f"${self.budget_tracker.current_spend_usd:.2f} >= "
                f"${self.budget_tracker.daily_budget_usd:.2f}"
            )
        
        # Filter providers by health
        available_providers = [
            p for p in self.providers
            if self.provider_stats[p.provider_id].health != ProviderHealth.CIRCUIT_OPEN
        ]
        
        if not available_providers:
            raise RuntimeError("No providers available (all circuit breakers open)")
        
        # Call all providers in parallel
        tasks = [
            self._call_provider_with_tracking(
                p, messages, tools=tools, system=system, temperature=temperature
            )
            for p in available_providers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter valid responses
        valid_responses = [
            (r, self.provider_stats[r.provider_id])
            for r in results
            if isinstance(r, LLMResponse)
        ]
        
        if not valid_responses:
            errors = [str(r) for r in results if isinstance(r, Exception)]
            raise RuntimeError(f"All providers failed. Errors: {errors}")
        
        # Score and select best response
        scored_responses = [
            (r, stats, self._score_response(r, stats))
            for r, stats in valid_responses
        ]
        best_response, best_stats, best_score = max(
            scored_responses, key=lambda x: x[2]
        )
        
        # Update budget tracker
        self.budget_tracker.add_usage(
            best_response.cost_usd,
            best_response.prompt_tokens + best_response.completion_tokens
        )
        
        # Save state periodically
        if self.budget_tracker.request_count % 10 == 0:
            self._save_state()
        
        return best_response
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics"""
        return {
            "budget": self.budget_tracker.to_dict(),
            "providers": {
                pid: stats.to_dict()
                for pid, stats in self.provider_stats.items()
            },
            "circuit_breakers": {
                pid: breaker.get_state().value
                for pid, breaker in self.circuit_breakers.items()
            } if self.enable_circuit_breaker else {},
            "config": {
                "cost_weight": self.cost_weight,
                "latency_weight": self.latency_weight,
                "quality_weight": self.quality_weight,
                "circuit_breaker_enabled": self.enable_circuit_breaker
            }
        }
    
    def reset_provider_stats(self, provider_id: Optional[str] = None):
        """Reset provider statistics"""
        if provider_id:
            if provider_id in self.provider_stats:
                self.provider_stats[provider_id] = ProviderStats(provider_id=provider_id)
                if self.enable_circuit_breaker:
                    self.circuit_breakers[provider_id] = CircuitBreaker()
        else:
            # Reset all
            for pid in self.provider_stats:
                self.provider_stats[pid] = ProviderStats(provider_id=pid)
                if self.enable_circuit_breaker:
                    self.circuit_breakers[pid] = CircuitBreaker()
        
        self._save_state()


# Convenience function
def create_enhanced_router(
    providers: List[BaseProvider],
    daily_budget_usd: float = 5.0,
    **kwargs
) -> EnhancedMultiLLMRouter:
    """Create an enhanced router with sensible defaults"""
    return EnhancedMultiLLMRouter(
        providers=providers,
        daily_budget_usd=daily_budget_usd,
        cost_weight=0.3,
        latency_weight=0.3,
        quality_weight=0.4,
        enable_circuit_breaker=True,
        **kwargs
    )


if __name__ == "__main__":
    print("✅ Enhanced Router module loaded")
    print("Features:")
    print("  - Advanced cost tracking with persistence")
    print("  - Provider health monitoring")
    print("  - Circuit breaker pattern")
    print("  - Request analytics")
    print("  - Budget management")