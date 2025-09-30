PENIN-Ω — Lemniscata 8+1 Monorepo

This repository contains a minimal, local-first implementation of the PENIN-Ω system:
- FastAPI services: Ω-META (:8010), Σ-Guard (:8011), SR-Ω∞ (:8012), ACFA League (:8013)
- Core modules: Master Equation, CAOS+, Fibonacci scheduler, Online tuner
- Math modules: L∞ aggregator (non-compensatory), Agápe, OCI
- IR→IC: Lψ projection (placeholder) with contractive behavior
- WORM + Merkle ledger and CLI support
- Plugin routes for NextPy, NASLib, Mammoth, SymbolicAI (with safe fallbacks)
- Tests and demo script

Quick start
1) Create venv and install
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   export PYTHONPATH=$PWD
   chmod +x penin/cli/peninctl

2) Start services (separate terminals)
   ./penin/cli/peninctl guard   # :8011
   ./penin/cli/peninctl sr      # :8012
   ./penin/cli/peninctl meta    # :8010
   ./penin/cli/peninctl league  # :8013

3) Demo
   python demo/run_demo.py

Notes
- Plugin libraries are optional. Routes will return realistic stub data if the plugin package is not installed.
- Promotion gates are fail-closed and require CAOS+ ≥ 1.0, SR ≥ 0.80, ΔL∞ ≥ 0.01, and Σ-Guard allow==true.

# PENIN-Ω v7.1 - Sistema de Evolução Mestre

## 📋 Status das Correções

### ✅ P0 - Correções Críticas AUDITADAS (Concluídas v7.1)

**Nova Auditoria Completa:** Ver `AUDITORIA_P0_COMPLETA.md`

1. **Métricas Éticas Computadas** ✓
   - Módulo `penin/omega/ethics_metrics.py` implementado
   - ECE (Expected Calibration Error) com binning
   - ρ_bias (Bias Ratio) por grupo protegido
   - Fairness Score (demographic parity/equalized odds)
   - Ateste completo com hash de evidência para WORM
   - Fail-closed: retorna valores piores se dados insuficientes

2. **Endpoint /metrics Seguro** ✓
   - Bind default em `127.0.0.1` (localhost only)
   - Config `metrics_bind_host` em `ObservabilityConfig`
   - Previne exposição de métricas sensíveis em hosts públicos

3. **WORM com WAL + busy_timeout** ✓
   - `PRAGMA journal_mode=WAL` ativado
   - `PRAGMA busy_timeout=3000` configurado
   - Melhor concorrência e durabilidade
   - Alinhado com cache L2

4. **Router Cost-Aware com Budget** ✓
   - Score multi-fator: quality (40%) + latency (30%) + cost (30%)
   - Budget diário configurável (default: $5 USD)
   - Tracking automático de spend/tokens/requests
   - Fail-closed: RuntimeError se budget excedido
   - Método `get_usage_stats()` para monitoring

**Testes:** 4/4 passando (`test_p0_audit_corrections.py`)

### ✅ P0 - Correções Críticas (Base v7.0)

1. **Seed Determinístico** ✓
   - Implementado `DeterministicRandom` para gerenciar toda aleatoriedade
   - Seed registrado no WORM a cada ciclo
   - Estado do RNG rastreável para replay completo

2. **psutil Obrigatório (Fail-Closed)** ✓
   - Sistema assume alto uso de recursos (CPU=99%, MEM=99%) quando psutil não está disponível
   - Comportamento fail-closed garante segurança
   - Modo determinístico quando seed é fornecido

3. **PROMOTE_ATTEST Atômico** ✓
   - Evento único com hashes pre/post estado
   - Gate trace completo registrado
   - Prevenção de TOCTOU com verificação atômica

4. **Fibonacci Boost Limitado** ✓
   - Boost máximo de 5% com clamp configurável
   - EWMA tracker para estabilidade de padrão
   - Mínimo de 5 ciclos antes de aplicar boost

5. **Validação Pydantic** ✓
   - Configuração totalmente validada com Pydantic v2
   - Falha em boot se configuração inválida
   - Tipos e ranges enforçados

### ✅ P1 - Melhorias de Observabilidade (Concluídas)

1. **Export Prometheus + JSON Logs** ✓
   - Métricas Prometheus completas (α, ΔL∞, CAOS⁺, SR, G, OCI, L∞)
   - Logs JSON estruturados com trace_id
   - Servidor de métricas HTTP integrado

2. **SQLite WAL Mode** ✓
   - PRAGMA journal_mode=WAL configurado
   - busy_timeout=3000ms para concorrência
   - Melhor performance em escritas concorrentes

3. **League Service (Shadow/Canary)** ✓
   - Shadow: 0% tráfego, coleta de métricas
   - Canary: 1-5% tráfego configurável
   - Promoção automática com gates
   - Rollback instantâneo com WORM proof

## 🚀 Como Usar

### Instalação

```bash
# Instalar dependências obrigatórias
pip install pydantic psutil

# Instalar dependências opcionais
pip install prometheus-client structlog redis numpy
```

### Executar Core v7

```python
from importlib import import_module

# Importar módulo v7
module = import_module('1_de_8_v7')

# Configurar com seed para determinismo
config = {
    "evolution": {"seed": 12345},
    "fibonacci": {"enabled": True},
    "caos_plus": {"max_boost": 0.05}
}

# Criar instância
core = module.PeninOmegaCore(config)

# Executar ciclo
import asyncio
result = asyncio.run(core.master_equation_cycle())
```

### Usar Observabilidade

```python
from observability import integrate_observability

# Integrar observabilidade no core
obs = integrate_observability(core)
obs.start()

# Métricas disponíveis em http://localhost:8000/metrics
```

### Usar League Service

```python
from league_service import LeagueOrchestrator, LeagueConfig

# Configurar league
config = LeagueConfig(
    shadow_duration_s=300,
    canary_duration_s=600,
    canary_traffic_pct=0.05
)

# Criar orquestrador
league = LeagueOrchestrator(config)

# Registrar champion e challenger
league.register_champion("v1")
league.deploy_challenger("v2")

# Executar com roteamento
from league_service import run_with_league
result = await run_with_league(core, league)
```

## 🧪 Testes

### Executar Testes P0

```bash
python3 test_p0_corrections.py
```

Testes verificam:
- Determinismo com mesmo seed
- Comportamento fail-closed sem psutil
- Eventos PROMOTE_ATTEST
- Clamp do boost Fibonacci
- Validação Pydantic
- Replay determinístico

## 📊 Métricas Disponíveis

### Prometheus Metrics

- `penin_alpha` - Valor atual de α_t^Ω
- `penin_delta_linf` - Valor atual de ΔL∞
- `penin_caos` - Valor atual de CAOS⁺
- `penin_sr` - Score SR atual
- `penin_g` - Score de coerência global
- `penin_oci` - Score OCI atual
- `penin_linf` - Score L∞ atual
- `penin_cpu` - Uso de CPU (0-1)
- `penin_mem` - Uso de memória (0-1)
- `penin_decisions_total{type}` - Total de decisões por tipo
- `penin_gate_fail_total{gate}` - Falhas de gate por tipo
- `penin_cycle_duration_seconds` - Duração dos ciclos

### JSON Logs

Todos os logs incluem:
- `timestamp` - ISO 8601
- `trace_id` - ID único por ciclo
- `level` - INFO/WARNING/ERROR
- Dados estruturados específicos do evento

## 🔐 Garantias de Segurança

1. **Fail-Closed por Default**
   - Sem psutil → assume recursos altos → abort
   - Config inválida → falha em boot
   - Gates não-compensatórios

2. **Auditabilidade Completa**
   - WORM com hash chain
   - PROMOTE_ATTEST com pre/post hashes
   - Seed state em todos eventos

3. **Determinismo Garantido**
   - Mesmo seed → mesmos resultados
   - RNG state rastreado
   - Replay possível para debug

## 📝 Próximos Passos

### P1 - Melhorias Importantes (2-3 semanas)
- [ ] Suites de testes de concorrência (WORM/League/Ethics)
- [ ] Redaction de logs (segredos/tokens/payloads)
- [ ] Substituir pickle no cache L2 por orjson + HMAC
- [ ] Fix imports dos testes (sem sys.path.insert)
- [ ] Testes de falhas de rede e timeout
- [ ] Calibração de limiares éticos com dados reais

### P2 - Higiene e Escala

- [ ] Integração OPA/Rego para políticas
- [ ] Bridge LLM com accounting real
- [ ] Separação CAOS⁺ exploratório/promotor
- [ ] Testes unitários completos
- [ ] Testes de integração
- [ ] Testes E2E

## 📚 Arquivos do Projeto

- `1_de_8_v7.py` - Core v7 com todas correções P0/P1
- `observability.py` - Módulo de observabilidade
- `league_service.py` - Serviço de league (shadow/canary)
- `test_p0_corrections.py` - Suite de testes P0
- `requirements.txt` - Dependências do projeto

## 🔧 Configuração Avançada

### Fibonacci Research

```python
config = {
    "fibonacci": {
        "enabled": True,
        "cache": True,           # TTLs Fibonacci
        "trust_region": True,    # Modulação de trust
        "search_method": "fibonacci",  # ou "golden"
        "max_interval_s": 300
    }
}
```

### CAOS⁺ com EWMA

```python
config = {
    "caos_plus": {
        "max_boost": 0.05,       # Máximo 5%
        "ewma_alpha": 0.2,       # Suavização EWMA
        "min_stability_cycles": 5  # Ciclos antes do boost
    }
}
```

### League Deployment

```python
config = {
    "shadow_duration_s": 300,    # 5 minutos shadow
    "canary_duration_s": 600,    # 10 minutos canary
    "canary_traffic_pct": 0.05,  # 5% tráfego
    "delta_threshold": 0.02,     # Min ΔL∞ para promoção
    "error_rate_threshold": 0.05 # Max 5% erros
}
```

## 🏆 Critérios de Aceitação

### P0 ✅
- [x] 100 ciclos com mesmo seed → mesmos eventos WORM
- [x] Sem psutil → ciclo abortado por RISK
- [x] PROMOTE_ATTEST presente em todas promoções
- [x] Boost Fibonacci ≤ 5% com estabilidade EWMA
- [x] Config inválida → falha em boot

### P1 ✅
- [x] Métricas Prometheus exportadas
- [x] Logs JSON estruturados com trace_id
- [x] SQLite com WAL mode
- [x] Shadow/Canary com rollback automático

## 📞 Suporte

Para questões sobre o PENIN-Ω v7.0, consulte a documentação completa ou abra uma issue no repositório.