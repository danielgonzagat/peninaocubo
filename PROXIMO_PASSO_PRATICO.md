# ⚡ PRÓXIMO PASSO PRÁTICO - Implementação Imediata

**Data**: 2025-10-01  
**Status**: Pronto para Execução  
**Tempo Estimado**: 4 horas  
**Impacto**: Router + WORM production-ready

---

## 🎯 OBJETIVO

Implementar os componentes P0 críticos que estão **especificados mas não implementados**:

1. ✅ **BudgetTracker** (Router Multi-LLM)
2. ✅ **CircuitBreaker** (Router Multi-LLM)
3. ✅ **HMACCache melhorado** (Router Multi-LLM)
4. ✅ **ProofCarryingArtifact** (WORM Ledger)
5. ✅ **WORMLedger completo** (Auditability)

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### **Preparação (5 min)**

```bash
cd /workspace
git checkout -b feature/p0-router-worm-implementation
pip install -e ".[dev]"
```

---

### **COMPONENTE 1: BudgetTracker (45 min)**

**Arquivo**: `penin/router_complete.py` (ou novo `penin/router/budget.py`)

**Código**:
```python
# penin/router/budget.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

@dataclass
class BudgetUsage:
    """Track budget usage metrics"""
    daily_limit_usd: float
    current_spend_usd: float
    requests_count: int
    tokens_used: int
    last_reset: datetime
    
    @property
    def percent_used(self) -> float:
        """Percentage of budget used"""
        return (self.current_spend_usd / self.daily_limit_usd) * 100
    
    @property
    def remaining_usd(self) -> float:
        """Remaining budget in USD"""
        return self.daily_limit_usd - self.current_spend_usd


class BudgetTracker:
    """Track and enforce daily budget limits"""
    
    SOFT_LIMIT_PCT = 95.0  # Soft stop at 95%
    HARD_LIMIT_PCT = 100.0  # Hard stop at 100%
    
    def __init__(self, daily_limit_usd: float = 100.0):
        self.daily_limit = daily_limit_usd
        self.current_spend = 0.0
        self.requests_count = 0
        self.tokens_used = 0
        self.last_reset = datetime.utcnow()
        
    def check_budget(self) -> tuple[bool, float, str]:
        """
        Check if within budget.
        
        Returns:
            (allowed, remaining_pct, reason)
        """
        self._check_daily_reset()
        
        pct_used = (self.current_spend / self.daily_limit) * 100
        remaining_pct = 100.0 - pct_used
        
        if pct_used >= self.HARD_LIMIT_PCT:
            return False, remaining_pct, "HARD_LIMIT_EXCEEDED"
        elif pct_used >= self.SOFT_LIMIT_PCT:
            return False, remaining_pct, "SOFT_LIMIT_EXCEEDED"
        else:
            return True, remaining_pct, "OK"
    
    def record_usage(self, cost_usd: float, tokens: int = 0):
        """Record a request's cost"""
        self.current_spend += cost_usd
        self.tokens_used += tokens
        self.requests_count += 1
    
    def get_usage(self) -> BudgetUsage:
        """Get current usage stats"""
        return BudgetUsage(
            daily_limit_usd=self.daily_limit,
            current_spend_usd=self.current_spend,
            requests_count=self.requests_count,
            tokens_used=self.tokens_used,
            last_reset=self.last_reset
        )
    
    def _check_daily_reset(self):
        """Reset daily budget if 24h elapsed"""
        now = datetime.utcnow()
        if now - self.last_reset > timedelta(days=1):
            self.current_spend = 0.0
            self.requests_count = 0
            self.tokens_used = 0
            self.last_reset = now
```

**Testes**: `tests/test_budget_tracker.py`

```python
import pytest
from penin.router.budget import BudgetTracker, BudgetUsage

def test_budget_tracker_initialization():
    tracker = BudgetTracker(daily_limit_usd=100.0)
    assert tracker.daily_limit == 100.0
    assert tracker.current_spend == 0.0

def test_budget_check_ok():
    tracker = BudgetTracker(daily_limit_usd=100.0)
    tracker.record_usage(10.0, tokens=1000)
    
    allowed, remaining_pct, reason = tracker.check_budget()
    assert allowed is True
    assert remaining_pct == 90.0
    assert reason == "OK"

def test_budget_soft_limit():
    tracker = BudgetTracker(daily_limit_usd=100.0)
    tracker.record_usage(96.0, tokens=10000)
    
    allowed, remaining_pct, reason = tracker.check_budget()
    assert allowed is False
    assert remaining_pct < 5.0
    assert reason == "SOFT_LIMIT_EXCEEDED"

def test_budget_hard_limit():
    tracker = BudgetTracker(daily_limit_usd=100.0)
    tracker.record_usage(100.0, tokens=20000)
    
    allowed, remaining_pct, reason = tracker.check_budget()
    assert allowed is False
    assert remaining_pct == 0.0
    assert reason == "HARD_LIMIT_EXCEEDED"

def test_budget_usage_metrics():
    tracker = BudgetTracker(daily_limit_usd=100.0)
    tracker.record_usage(25.0, tokens=5000)
    tracker.record_usage(25.0, tokens=5000)
    
    usage = tracker.get_usage()
    assert usage.current_spend_usd == 50.0
    assert usage.requests_count == 2
    assert usage.tokens_used == 10000
    assert usage.percent_used == 50.0
    assert usage.remaining_usd == 50.0
```

**Validação**:
```bash
pytest tests/test_budget_tracker.py -v
```

---

### **COMPONENTE 2: CircuitBreaker (45 min)**

**Arquivo**: `penin/router/circuit_breaker.py`

**Código**:
```python
# penin/router/circuit_breaker.py

from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec('P')
R = TypeVar('R')


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time: datetime | None = None
        
    def call(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Execute function with circuit breaker logic"""
        
        # Check if should attempt recovery
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and datetime.utcnow() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.successes = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Retry after {self.timeout.seconds}s"
                )
        
        # Attempt call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.failures = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.successes += 1
            if self.successes >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.successes = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failures += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time = None
```

**Testes**: `tests/test_circuit_breaker.py`

```python
import pytest
import time
from penin.router.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState
)

def test_circuit_breaker_closed_success():
    cb = CircuitBreaker(failure_threshold=3)
    
    def success_func():
        return "success"
    
    result = cb.call(success_func)
    assert result == "success"
    assert cb.state == CircuitState.CLOSED

def test_circuit_breaker_opens_after_failures():
    cb = CircuitBreaker(failure_threshold=3)
    
    def failing_func():
        raise Exception("fail")
    
    for _ in range(3):
        with pytest.raises(Exception):
            cb.call(failing_func)
    
    assert cb.state == CircuitState.OPEN
    
    # Next call should raise CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError):
        cb.call(failing_func)

def test_circuit_breaker_half_open_recovery():
    cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1, success_threshold=2)
    
    def failing_func():
        raise Exception("fail")
    
    # Trip the breaker
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(failing_func)
    
    assert cb.state == CircuitState.OPEN
    
    # Wait for timeout
    time.sleep(1.1)
    
    def success_func():
        return "success"
    
    # Should transition to HALF_OPEN on next call
    result = cb.call(success_func)
    assert result == "success"
    assert cb.state == CircuitState.HALF_OPEN
    
    # After success_threshold successes, should go CLOSED
    cb.call(success_func)
    assert cb.state == CircuitState.CLOSED
```

---

### **COMPONENTE 3: HMACCache (30 min)**

**Melhorar arquivo existente**: `penin/cache.py`

**Adicionar ao arquivo existente**:

```python
# Adicionar imports
import hmac
import hashlib
from datetime import datetime, timedelta

class HMACCache:
    """Cache with HMAC-SHA256 integrity verification"""
    
    def __init__(self, secret_key: bytes = b"penin-omega-secret"):
        self.secret_key = secret_key
        self.cache: dict = {}
        
    def _compute_hmac(self, data: str) -> str:
        """Compute HMAC-SHA256 of data"""
        return hmac.new(
            self.secret_key,
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def set(self, key: str, value: str, ttl: int = 3600):
        """Store with HMAC integrity check"""
        hmac_value = self._compute_hmac(value)
        expires = datetime.utcnow() + timedelta(seconds=ttl)
        
        self.cache[key] = {
            'value': value,
            'hmac': hmac_value,
            'expires': expires
        }
    
    def get(self, key: str) -> str | None:
        """Retrieve and verify HMAC"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if datetime.utcnow() > entry['expires']:
            del self.cache[key]
            return None
        
        # Verify HMAC
        expected_hmac = self._compute_hmac(entry['value'])
        if not hmac.compare_digest(expected_hmac, entry['hmac']):
            raise ValueError("HMAC verification failed - cache corrupted")
        
        return entry['value']
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
    
    def stats(self) -> dict:
        """Get cache statistics"""
        return {
            'entries': len(self.cache),
            'expired': sum(1 for e in self.cache.values() if datetime.utcnow() > e['expires'])
        }
```

---

### **COMPONENTE 4: ProofCarryingArtifact (30 min)**

**Arquivo**: `penin/ledger/pcag.py`

```python
# penin/ledger/pcag.py

from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import json
from typing import Optional


@dataclass
class ProofCarryingArtifact:
    """PCAg - Proof-Carrying Artifact for auditable decisions"""
    
    # Identity
    decision_id: str
    timestamp: str
    version: str
    
    # Metrics
    delta_linf: float
    caos_plus: float
    sr_score: float
    ethical_score: float
    
    # Decision
    decision: str  # PROMOTE, ROLLBACK, BLOCK
    reason: str
    
    # Evidence
    metrics: dict
    violations: list
    gates_passed: dict
    
    # Cryptographic proof
    previous_hash: str
    current_hash: str
    
    @classmethod
    def create(cls, decision_data: dict, previous_hash: str) -> 'ProofCarryingArtifact':
        """Create new PCAg with hash chain"""
        pcag = cls(
            decision_id=decision_data['decision_id'],
            timestamp=datetime.utcnow().isoformat(),
            version="1.0",
            delta_linf=decision_data.get('delta_linf', 0.0),
            caos_plus=decision_data.get('caos_plus', 0.0),
            sr_score=decision_data.get('sr_score', 0.0),
            ethical_score=decision_data.get('ethical_score', 0.0),
            decision=decision_data['decision'],
            reason=decision_data['reason'],
            metrics=decision_data.get('metrics', {}),
            violations=decision_data.get('violations', []),
            gates_passed=decision_data.get('gates_passed', {}),
            previous_hash=previous_hash,
            current_hash=""  # Will be computed
        )
        
        # Compute current hash
        pcag_dict = asdict(pcag)
        pcag_dict.pop('current_hash')  # Exclude self
        pcag_json = json.dumps(pcag_dict, sort_keys=True)
        pcag.current_hash = hashlib.sha256(pcag_json.encode()).hexdigest()
        
        return pcag
    
    def verify(self, previous_pcag: Optional['ProofCarryingArtifact'] = None) -> bool:
        """Verify hash chain integrity"""
        # Verify self hash
        pcag_dict = asdict(self)
        expected_hash = pcag_dict.pop('current_hash')
        pcag_json = json.dumps(pcag_dict, sort_keys=True)
        actual_hash = hashlib.sha256(pcag_json.encode()).hexdigest()
        
        if actual_hash != expected_hash:
            return False
        
        # Verify chain
        if previous_pcag and self.previous_hash != previous_pcag.current_hash:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
```

---

### **COMPONENTE 5: WORMLedger completo (30 min)**

**Melhorar arquivo existente**: `penin/ledger/worm_ledger_complete.py`

```python
# Adicionar ao arquivo existente

from pathlib import Path
from penin.ledger.pcag import ProofCarryingArtifact


class WORMLedger:
    """Write-Once-Read-Many ledger with hash chain"""
    
    def __init__(self, filepath: str = ".penin_omega/worm_ledger.jsonl"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.last_hash = "0" * 64  # Genesis hash
        
        # Load last hash if ledger exists
        if self.filepath.exists():
            self._load_last_hash()
        
    def append(self, decision_data: dict) -> ProofCarryingArtifact:
        """Append decision with PCAg"""
        pcag = ProofCarryingArtifact.create(decision_data, self.last_hash)
        
        # Write to ledger (append-only)
        with open(self.filepath, 'a') as f:
            f.write(json.dumps(pcag.to_dict()) + '\n')
        
        self.last_hash = pcag.current_hash
        return pcag
    
    def verify_all(self) -> tuple[bool, str]:
        """Verify entire ledger integrity"""
        if not self.filepath.exists():
            return True, "Empty ledger"
        
        with open(self.filepath, 'r') as f:
            lines = f.readlines()
        
        if len(lines) == 0:
            return True, "Empty ledger"
        
        previous_pcag = None
        for i, line in enumerate(lines):
            try:
                pcag_dict = json.loads(line)
                pcag = ProofCarryingArtifact(**pcag_dict)
                
                if not pcag.verify(previous_pcag):
                    return False, f"Verification failed at entry {i}"
                
                previous_pcag = pcag
            except Exception as e:
                return False, f"Parse error at entry {i}: {str(e)}"
        
        return True, f"Verified {len(lines)} entries"
    
    def read_all(self) -> list[ProofCarryingArtifact]:
        """Read all entries"""
        if not self.filepath.exists():
            return []
        
        entries = []
        with open(self.filepath, 'r') as f:
            for line in f:
                pcag_dict = json.loads(line)
                entries.append(ProofCarryingArtifact(**pcag_dict))
        
        return entries
    
    def _load_last_hash(self):
        """Load last hash from existing ledger"""
        with open(self.filepath, 'r') as f:
            lines = f.readlines()
        
        if lines:
            last_entry = json.loads(lines[-1])
            self.last_hash = last_entry['current_hash']
```

---

## ✅ VALIDAÇÃO COMPLETA

```bash
# Rodar todos os testes
pytest tests/test_budget_tracker.py -v
pytest tests/test_circuit_breaker.py -v
pytest tests/test_hmac_cache.py -v
pytest tests/test_pcag.py -v
pytest tests/test_worm_ledger.py -v

# Cobertura
pytest --cov=penin.router --cov=penin.ledger --cov-report=term-missing

# Linters
ruff check .
black --check .
mypy penin/router/ penin/ledger/
```

---

## 📊 RESULTADO ESPERADO

✅ **5 componentes P0 implementados e testados**  
✅ **Router Multi-LLM production-ready**  
✅ **WORM Ledger auditável**  
✅ **+30% progresso em Fase 0 (P0)**  
✅ **Base sólida para Fases 1-2**

---

**Tempo Total**: 4 horas  
**Impacto**: Desbloqueio completo de P0 crítico  
**Próximo**: Fase 1 (Matemática) + Fase 2 (Σ-Guard)

**Status**: ✅ **PRONTO PARA COPIAR/COLAR E EXECUTAR**
