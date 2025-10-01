# PENIN-Ω v7.1 - Quick Start P0

**Para desenvolvedores que querem usar as correções P0 imediatamente.**

---

## ⚡ TL;DR

```bash
# 1. Clone e setup
git clone https://github.com/danielgonzagat/peninaocubo && cd peninaocubo
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Instale dependências P0
pip install tenacity pydantic-settings

# 3. Teste P0
python3 test_p0_audit_corrections.py
# Esperado: 4/4 testes passando

# 4. Teste backward compatibility
python3 test_p0_corrections.py
# Esperado: 6/6 testes passando
```

---

## 📦 Correções P0 Implementadas

### 1. Ethics Metrics (P0-1)

**Uso básico:**

```python
from penin.omega.ethics_metrics import compute_ethics_attestation

# Prepare data
model_outputs = {
    "predicted_probs": [0.1, 0.9, 0.3, ...],  # Confidence scores
    "predictions": [0, 1, 0, ...],             # Binary predictions
    "protected_groups": ["A", "B", "A", ...],  # Group labels
    "estimated_tokens": 1000,
}

ground_truth = {
    "labels": [0, 1, 1, ...],                  # True labels
    "dataset_hash": "sha256_of_dataset",
    "consent_verified": True,
}

# Compute attestation
attestation = compute_ethics_attestation(
    model_outputs,
    ground_truth,
    seed=42
)

# Check results
print(f"Pass Σ-Guard: {attestation.pass_sigma_guard}")
print(f"ECE: {attestation.ece:.4f}")
print(f"ρ_bias: {attestation.rho_bias:.4f}")
print(f"Fairness: {attestation.fairness_score:.4f}")

# Store in WORM
worm.record('ETHICS_ATTEST', attestation.to_dict())
```

**Limiares padrão:**
- ECE ≤ 0.01
- ρ_bias ≤ 1.05
- Fairness ≥ 0.8

**Override limiares:**

```python
from penin.omega.ethics_metrics import EthicsMetricsCalculator

calculator = EthicsMetricsCalculator(
    ece_bins=15,                # Mais bins = mais preciso
    ece_threshold=0.02,         # Mais permissivo
    bias_threshold=1.10,        # Mais permissivo
    fairness_threshold=0.7,     # Mais permissivo
)

attestation = calculator.compute_full_attestation(...)
```

---

### 2. Secure Metrics Endpoint (P0-2)

**Uso básico (localhost only):**

```python
from observability import ObservabilityConfig, ObservabilityManager

# Default: bind 127.0.0.1
config = ObservabilityConfig(
    enable_metrics=True,
    metrics_port=8000,
    # metrics_bind_host="127.0.0.1" <- default implícito
)

obs = ObservabilityManager(config)
obs.start()

# Metrics disponíveis em http://127.0.0.1:8000/metrics
```

**Expor externamente (com cautela):**

```python
# ATENÇÃO: Use proxy reverso com autenticação!
config = ObservabilityConfig(
    metrics_bind_host="0.0.0.0",  # Todas as interfaces
    metrics_port=8000,
)
```

**Nginx reverse proxy (recomendado):**

```nginx
server {
    listen 9090 ssl;
    server_name metrics.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /metrics {
        auth_basic "Metrics";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

---

### 3. WORM WAL Mode (P0-3)

**Uso automático:**

```python
from importlib import import_module

module = import_module('1_de_8_v7')

# WORMLedger agora usa WAL + busy_timeout automaticamente
core = module.PeninOmegaCore()

# Nada muda no código do usuário!
# WAL e busy_timeout são aplicados no __init__ do WORMLedger
```

**Verificar pragmas manualmente:**

```bash
sqlite3 /path/to/omega_core_1of8_v7.db <<EOF
PRAGMA journal_mode;
PRAGMA busy_timeout;
EOF

# Output esperado:
# wal
# 3000
```

**Benefícios:**
- Leitores não bloqueiam escritores
- Escritores não bloqueiam leitores
- Retry automático até 3s antes de falhar

---

### 4. Cost-Aware Router (P0-4)

**Uso básico:**

```python
from penin.router import MultiLLMRouter
from penin.providers.openai_provider import OpenAIProvider
from penin.providers.anthropic_provider import AnthropicProvider

# Create providers
providers = [
    OpenAIProvider(),
    AnthropicProvider(),
]

# Create router with budget
router = MultiLLMRouter(
    providers,
    daily_budget_usd=10.0,    # $10/dia
    cost_weight=0.3,          # 30% peso para custo
    latency_weight=0.3,       # 30% peso para latência
    quality_weight=0.4,       # 40% peso para qualidade
)

# Make requests
messages = [{"role": "user", "content": "Hello!"}]
response = await router.ask(messages)

print(f"Provider: {response.provider}")
print(f"Cost: ${response.cost_usd:.4f}")
print(f"Latency: {response.latency_s:.2f}s")
```

**Monitorar orçamento:**

```python
# Get usage stats
stats = router.get_usage_stats()

print(f"Spend: ${stats['daily_spend_usd']:.4f}")
print(f"Budget: ${stats['daily_budget_usd']:.2f}")
print(f"Used: {stats['budget_used_pct']:.1f}%")
print(f"Remaining: ${stats['budget_remaining_usd']:.4f}")
print(f"Requests: {stats['request_count']}")
print(f"Avg cost/req: ${stats['avg_cost_per_request']:.4f}")
```

**Fail-closed behavior:**

```python
# Budget excedido → RuntimeError
try:
    response = await router.ask(messages)
except RuntimeError as e:
    if "budget" in str(e).lower():
        print("Daily budget exceeded!")
        # Alertar time, parar requests, etc.
```

**Ajustar pesos dinamicamente:**

```python
# Priorizar custo (para economizar)
router.cost_weight = 0.6
router.latency_weight = 0.2
router.quality_weight = 0.2

# Priorizar latência (para performance)
router.cost_weight = 0.1
router.latency_weight = 0.7
router.quality_weight = 0.2
```

---

## 🧪 Testes

### Executar todos os testes P0

```bash
# Testes das correções v7.1
python3 test_p0_audit_corrections.py

# Testes de retrocompatibilidade v7.0
python3 test_p0_corrections.py
```

### Testes individuais

```python
# Somente ethics metrics
python3 -c "
from test_p0_audit_corrections import test_p0_1_ethics_metrics
test_p0_1_ethics_metrics()
"

# Somente metrics security
python3 -c "
from test_p0_audit_corrections import test_p0_2_metrics_security
test_p0_2_metrics_security()
"

# Somente WORM WAL
python3 -c "
from test_p0_audit_corrections import test_p0_3_worm_wal
test_p0_3_worm_wal()
"

# Somente router budget
python3 -c "
from test_p0_audit_corrections import test_p0_4_router_cost_budget
test_p0_4_router_cost_budget()
"
```

---

## 🚨 Troubleshooting

### "ModuleNotFoundError: No module named 'tenacity'"

```bash
pip install tenacity
```

### "ModuleNotFoundError: No module named 'pydantic_settings'"

```bash
pip install pydantic-settings
```

### "prometheus_client not installed"

Opcional. Se quiser métricas Prometheus:

```bash
pip install prometheus-client
```

### "Metrics endpoint não responde"

Verifique o bind host:

```bash
# Local funciona
curl http://127.0.0.1:8000/metrics

# Externo não (correto)
curl http://0.0.0.0:8000/metrics  # Timeout
```

Se precisa expor, configure `metrics_bind_host="0.0.0.0"` e use proxy reverso com auth.

### "Budget exceeded logo no primeiro request"

Ajuste o budget:

```python
router = MultiLLMRouter(
    providers,
    daily_budget_usd=100.0,  # Aumentar limite
)
```

Ou resete manualmente:

```python
router._daily_spend = 0.0
router._last_reset = datetime.now().date()
```

### "database is locked" ainda acontece

Verifique se WAL está ativo:

```bash
sqlite3 /path/to/db.db "PRAGMA journal_mode;"
# Deve retornar: wal
```

Se não estiver, force:

```python
import sqlite3
conn = sqlite3.connect("/path/to/db.db")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=3000")
conn.close()
```

---

## 📚 Documentação Completa

- **Auditoria P0:** `AUDITORIA_P0_COMPLETA.md`
- **Commit details:** `COMMIT_P0_V7.1.md`
- **Sumário executivo:** `SUMARIO_EXECUTIVO_P0.md`
- **README principal:** `README.md`

---

## 🤝 Contribuindo

### Reportar bugs P0

```bash
# Template de issue
Title: [P0-X] Brief description

**Correção afetada:** P0-1 / P0-2 / P0-3 / P0-4

**Descrição:**
[O que aconteceu]

**Esperado:**
[O que deveria acontecer]

**Como reproduzir:**
1. Step 1
2. Step 2
3. ...

**Logs/Stack trace:**
```
[paste here]
```

**Ambiente:**
- OS: Linux/Mac/Windows
- Python: 3.11/3.12/3.13
- PENIN-Ω: v7.1
```

### Sugerir melhorias P0

```bash
# Template de feature request
Title: [P0-X] Enhancement suggestion

**Correção afetada:** P0-1 / P0-2 / P0-3 / P0-4

**Problema atual:**
[O que não é ideal]

**Solução proposta:**
[Como melhorar]

**Alternativas consideradas:**
[Outras abordagens]

**Impacto:**
- Breaking: Yes/No
- Performance: Better/Same/Worse
- Security: Better/Same/Worse
```

---

## ⚖️ Licença

[Pending - adicionar MIT ou Apache-2.0]

---

## 📞 Suporte

- **Issues:** GitHub Issues
- **Docs:** `docs/` directory
- **Email:** [pending]
- **Slack:** [pending]

---

**Última atualização:** 2025-01-XX  
**Versão:** v7.1  
**Status:** ✅ Produção