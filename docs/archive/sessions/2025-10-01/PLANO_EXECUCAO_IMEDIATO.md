# ⚡ PLANO DE EXECUÇÃO IMEDIATO - PENIN-Ω IA³

**Data**: 2025-10-01  
**Duração**: Esta sessão de trabalho  
**Objetivo**: Máximo impacto em mínimo tempo

---

## 🎯 FOCO ABSOLUTO: P0 BLOCKERS

### **Problema 1: Testes de Ética Quebrados** 🔴
**Status**: 10 testes falhando  
**Impacto**: Bloqueio de validação ética  
**Solução**: Refatorar interface de testes  
**Tempo estimado**: 30 minutos  
**Prioridade**: #1

### **Problema 2: Router Multi-LLM Incompleto** 🔴
**Status**: Budget/CB/Cache parciais  
**Impacto**: Orquestração limitada  
**Solução**: Completar componentes críticos  
**Tempo estimado**: 2 horas  
**Prioridade**: #2

### **Problema 3: WORM Ledger PCAg** 🔴
**Status**: Integração parcial  
**Impacto**: Auditabilidade comprometida  
**Solução**: Completar templates PCAg  
**Tempo estimado**: 1 hora  
**Prioridade**: #3

---

## 📋 EXECUÇÃO SEQUENCIAL

### **BLOCO 1: Correção de Testes (30 min)**

```python
# tests/ethics/test_laws.py - REFATORAR

# ANTES (interface antiga - dict):
context = {"metrics": {"privacy": 0.99}, "consent": True}
result = validator.validate_all(decision, context)

# DEPOIS (interface nova - DecisionContext):
from penin.ethics.laws import DecisionContext
context = DecisionContext(
    decision_id="test_001",
    decision_type="inference",
    privacy_score=0.99,
    consent_obtained=True
)
result = EthicsValidator.validate_all(context)
```

**Ações**:
1. Atualizar todos 10 testes para usar `DecisionContext`
2. Remover parâmetro `decision` (não usado)
3. Validar que todos passam

---

### **BLOCO 2: Router Multi-LLM (2 horas)**

#### **2.1: Budget Tracker (45 min)**

```python
# penin/router_complete.py - ADICIONAR

class BudgetTracker:
    def __init__(self, daily_limit_usd: float = 100.0):
        self.daily_limit = daily_limit_usd
        self.current_spend = 0.0
        self.requests_count = 0
        self.tokens_used = 0
        
    def check_budget(self) -> tuple[bool, float]:
        """Check if within budget. Returns (allowed, remaining_pct)"""
        pct_used = (self.current_spend / self.daily_limit) * 100
        
        if pct_used >= 100:
            return False, 0.0  # Hard stop
        elif pct_used >= 95:
            return False, (100 - pct_used)  # Soft stop
        else:
            return True, (100 - pct_used)
    
    def record_usage(self, cost_usd: float, tokens: int):
        """Record a request's cost"""
        self.current_spend += cost_usd
        self.tokens_used += tokens
        self.requests_count += 1
```

#### **2.2: Circuit Breaker (45 min)**

```python
# penin/router_complete.py - ADICIONAR

from enum import Enum
from datetime import datetime, timedelta

class CircuitState(str, Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = None
        
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker logic"""
        if self.state == CircuitState.OPEN:
            if datetime.utcnow() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        self.failures = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
    
    def on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.utcnow()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

#### **2.3: Cache HMAC (30 min)**

```python
# penin/cache.py - MELHORAR

import hmac
import hashlib
from typing import Optional

class HMACCache:
    def __init__(self, secret_key: bytes):
        self.secret_key = secret_key
        self.cache = {}  # L1: memory
        
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
        self.cache[key] = {
            'value': value,
            'hmac': hmac_value,
            'expires': datetime.utcnow() + timedelta(seconds=ttl)
        }
    
    def get(self, key: str) -> Optional[str]:
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
```

---

### **BLOCO 3: WORM Ledger PCAg (1 hora)**

```python
# penin/ledger/worm_ledger_complete.py - ADICIONAR

from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import json

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


class WORMLedger:
    def __init__(self, filepath: str = ".penin_omega/worm_ledger.jsonl"):
        self.filepath = filepath
        self.last_hash = "0" * 64  # Genesis hash
        
    def append(self, decision_data: dict) -> ProofCarryingArtifact:
        """Append decision with PCAg"""
        pcag = ProofCarryingArtifact.create(decision_data, self.last_hash)
        
        # Write to ledger (append-only)
        with open(self.filepath, 'a') as f:
            f.write(json.dumps(asdict(pcag)) + '\n')
        
        self.last_hash = pcag.current_hash
        return pcag
    
    def verify_all(self) -> bool:
        """Verify entire ledger integrity"""
        with open(self.filepath, 'r') as f:
            lines = f.readlines()
        
        previous_pcag = None
        for line in lines:
            pcag_dict = json.loads(line)
            pcag = ProofCarryingArtifact(**pcag_dict)
            
            if not pcag.verify(previous_pcag):
                return False
            
            previous_pcag = pcag
        
        return True
```

---

## ✅ CRITÉRIOS DE SUCESSO

### **Após BLOCO 1** (30 min):
- [ ] 10 testes de ética passando
- [ ] Zero erros de importação em ethics

### **Após BLOCO 2** (2h 30min):
- [ ] `BudgetTracker` funcional com gates 95%/100%
- [ ] `CircuitBreaker` com estados CLOSED/OPEN/HALF-OPEN
- [ ] `HMACCache` com verificação de integridade
- [ ] Testes unitários para cada componente

### **Após BLOCO 3** (3h 30min):
- [ ] `ProofCarryingArtifact` completo
- [ ] Hash chain verificável
- [ ] WORM ledger append-only
- [ ] Teste de verificação de integridade

---

## 🎯 RESULTADOS ESPERADOS (FIM DA SESSÃO)

### **Métricas**:
- Testes passando: 85% → 95% (+10%)
- Componentes P0 completos: 60% → 85% (+25%)
- Auditabilidade: 65% → 90% (+25%)

### **Entregáveis**:
1. ✅ Testes de ética 100% funcionais
2. ✅ Router Multi-LLM production-ready
3. ✅ WORM Ledger + PCAg auditável
4. ✅ Documentação atualizada
5. ✅ Relatório de progresso

### **Impacto**:
- 🔓 **Desbloqueio**: Validação ética funcional
- 🚀 **Aceleração**: Router robusto para orquestração
- 📊 **Transparência**: Auditabilidade completa
- ✅ **Qualidade**: Cobertura de testes melhorada

---

## 📝 DOCUMENTAÇÃO CONTÍNUA

A cada bloco completado, atualizar:
- `TRANSFORMATION_STATUS.md` (progresso)
- `CHANGELOG.md` (mudanças)
- Docstrings dos módulos modificados

---

## 🚦 PRÓXIMOS PASSOS (PÓS-SESSÃO)

Se tempo permitir, atacar em ordem:
1. **Σ-Guard OPA/Rego** (Fase 2)
2. **Matemática rigorosa** (Fase 1)
3. **Observabilidade** (Fase 7)

---

**Preparado por**: Background Agent Autonomous System  
**Status**: ✅ **PRONTO PARA EXECUÇÃO**  
**Início**: 2025-10-01 (AGORA)

**💪 Let's build!**
