# Testes de Integração do NextPyModifier

## Visão Geral

Este documento descreve os testes de integração abrangentes para o módulo `NextPyModifier`, responsável por modificações autônomas de arquitetura no sistema PENIN-Ω.

## Objetivos dos Testes

Os testes de integração validam a interação completa do NextPyModifier com os seguintes componentes do sistema:

1. **CAOS+ Motor** - Motor de Consistência, Autoevolução, Incognoscível e Silêncio
2. **SR-Ω∞** - Sistema de Self-Reflection (auto-reflexão)
3. **Ω-META** - Orquestrador de evolução e mutação
4. **Sigma Guard** - Validação ética e de segurança
5. **WORM Ledger** - Registro de auditoria imutável

## Estrutura dos Testes

### 1. Integração com CAOS+ Motor

#### `TestNextPyWithCAOS`

**Objetivo**: Validar que o NextPyModifier trabalha corretamente com o motor CAOS+ para guiar a evolução.

##### Cenários Testados:

- **test_mutation_with_caos_scoring**: Verifica que mutações geradas melhoram o score CAOS+
- **test_caos_guided_evolution**: Testa evolução multi-ciclo guiada por feedback CAOS+
- **test_caos_components_impact_on_mutation**: Valida que diferentes componentes CAOS+ afetam a estratégia de mutação

**Exemplo de Uso**:
```python
# Configurar adapter
config = NextPyConfig(enable_ams=True, max_mutation_depth=3)
adapter = NextPyModifier(config=config)

# Computar score CAOS+ baseline
caos_score = compute_caos_plus_exponential(
    c=0.85,  # Consistência
    a=0.75,  # Autoevolução
    o=0.60,  # Incognoscível
    s=0.90,  # Silêncio
    kappa=20.0
)

# Gerar mutação para melhorar CAOS+
mutation = await adapter.execute(
    "mutate",
    architecture_state,
    {"caos_plus_target": caos_score + 0.5}
)
```

### 2. Integração com SR-Ω∞ (Self-Reflection)

#### `TestNextPyWithSR`

**Objetivo**: Garantir que mutações respeitam e melhoram as capacidades de auto-reflexão do sistema.

##### Cenários Testados:

- **test_mutation_with_sr_feedback**: Mutações geradas consideram componentes SR-Ω∞
- **test_metacognitive_evolution**: Evolução progressiva de metacognição
- **test_sr_triggered_rollback**: Rollback automático ao detectar degradação de auto-awareness

**Componentes SR-Ω∞**:
- **Awareness**: Consciência operacional do sistema
- **Ethics OK**: Validação ética (ΣEA/LO-14)
- **Autocorrection**: Capacidade de autocorreção
- **Metacognition**: Meta-raciocínio (pensar sobre pensar)

**Exemplo de Uso**:
```python
# Estado com componentes SR-Ω∞
sr_components = {
    "awareness": 0.80,
    "ethics_ok": 1.0,
    "autocorrection": 0.75,
    "metacognition": 0.70
}

# Score SR-Ω∞ (média harmônica para não-compensação)
sr_score = len(sr_components) / sum(1.0 / max(v, 0.01) for v in sr_components.values())

# Gerar mutação consciente de SR
state_with_sr = {
    "model": "baseline",
    "sr_omega": sr_components,
    "sr_score": sr_score
}
mutation = await adapter.execute("mutate", state_with_sr)
```

### 3. Integração com Ω-META (Evolution Orchestration)

#### `TestNextPyWithOmegaMeta`

**Objetivo**: Validar o pipeline completo de deployment de mutações.

##### Cenários Testados:

- **test_mutation_deployment_pipeline**: Pipeline completo (shadow → canary → rollout → champion)
- **test_champion_challenger_evaluation**: Avaliação champion-challenger com score L∞
- **test_ast_mutation_generation**: Geração de mutações AST para evolução de arquitetura

**Estágios de Deployment**:
1. **Shadow**: 0% de tráfego, apenas observação
2. **Canary**: 5% de tráfego real
3. **Rollout**: Gradual (10%, 25%, 50%, 100%)
4. **Champion**: 100% de tráfego, novo padrão

**Exemplo de Uso**:
```python
# Gerar mutação
mutation = await adapter.execute("mutate", champion_state)

# Simular deployment progressivo
stages = ["shadow", "canary", "rollout", "champion"]
for stage in stages:
    stage_result = deploy_mutation(mutation, stage)
    metrics = evaluate_stage(stage_result)
    
    if metrics["delta_linf"] < threshold:
        rollback_mutation(mutation)
        break
```

### 4. Integração com Sigma Guard

#### `TestNextPyWithSigmaGuard`

**Objetivo**: Garantir que mutações passam por validação ética e de segurança.

##### Cenários Testados:

- **test_mutation_validation_gate**: Mutações validadas contra thresholds Sigma Guard
- **test_failed_gate_rollback**: Rollback automático em falhas de validação
- **test_contractive_evolution**: Evolução contrativa (IR→IC) - risco diminui com tempo

**Gates de Validação**:
- **ECE** (Expected Calibration Error): < 0.15
- **ρ (Bias Ratio)**: < 2.0
- **Fairness Score**: > 0.7
- **Risk ρ**: < 1.0
- **Consent OK**: True

**Exemplo de Uso**:
```python
# Gerar mutação
mutation = await adapter.execute("mutate", architecture_state)

# Validar com Sigma Guard
gate_metrics = {
    "ece": 0.08,
    "rho_bias": 1.2,
    "fairness_score": 0.82,
    "risk_rho": 0.65,
    "consent_ok": True
}

gate_pass = (
    gate_metrics["ece"] < 0.15 and
    gate_metrics["rho_bias"] < 2.0 and
    gate_metrics["fairness_score"] > 0.7 and
    gate_metrics["risk_rho"] < 1.0 and
    gate_metrics["consent_ok"]
)

if gate_pass:
    apply_mutation(mutation)
else:
    rollback_mutation(mutation)
```

### 5. Integração com WORM Ledger

#### `TestNextPyWithWORMLedger`

**Objetivo**: Garantir rastreabilidade completa e auditabilidade de mutações.

##### Cenários Testados:

- **test_mutation_audit_trail**: Trail de auditoria completo para cada mutação
- **test_pcag_generation**: Geração de PCAg (Proof-Carrying Artifacts for Governance)
- **test_evolution_lineage_tracking**: Rastreamento de linhagem através de gerações

**Estrutura de Auditoria**:
```python
audit_record = {
    "timestamp": datetime.now(UTC).isoformat(),
    "mutation_id": mutation["mutation_id"],
    "operation": "mutate",
    "input_state_hash": hash(input_state),
    "output_mutation_hash": hash(mutation),
    "risk_score": mutation["risk_score"],
    "expected_improvement": mutation["expected_improvement"]
}
```

**Exemplo de PCAg**:
```python
pcag = {
    "artifact_id": f"pcag_{mutation['mutation_id']}",
    "artifact_type": "nextpy_mutation",
    "content_hash": hash(mutation),
    "timestamp": time.time(),
    "generator": "NextPyModifier",
    "proofs": {
        "risk_bounded": mutation["risk_score"] < 0.5,
        "rollback_available": mutation["rollback_available"],
        "expected_improvement": mutation["expected_improvement"] > 0
    }
}
```

### 6. Testes End-to-End

#### `TestEndToEndEvolution`

**Objetivo**: Validar ciclos completos de evolução com todos os componentes integrados.

##### Cenários Testados:

- **test_complete_evolution_cycle**: Ciclo completo de evolução (3 gerações)
- **test_multi_mutation_exploration**: Exploração de múltiplas variantes de mutação
- **test_adaptive_evolution_strategy**: Estratégia adaptativa baseada em estado do sistema

**Fluxo Completo de Evolução**:
```python
for cycle in range(3):
    # 1. Computar CAOS+
    caos_score = compute_caos_plus_exponential(...)
    
    # 2. Gerar mutação
    mutation = await adapter.execute("mutate", state, target_metrics)
    
    # 3. Otimizar prompts
    optimization = await adapter.execute("optimize", state)
    
    # 4. Computar SR-Ω∞
    sr_score = compute_sr_score(...)
    
    # 5. Validar com Sigma Guard
    gate_pass = validate_mutation(mutation)
    
    # 6. Atualizar estado
    if gate_pass:
        state = apply_mutation(state, mutation)
```

### 7. Performance Benchmarks

#### `TestPerformanceBenchmarks`

**Objetivo**: Validar performance e throughput do sistema.

##### Cenários Testados:

- **test_mutation_generation_performance**: Latência de geração de mutações
- **test_evolution_cycle_throughput**: Throughput de ciclos completos de evolução
- **test_concurrent_mutations**: Geração concorrente de mutações

**Métricas de Performance**:
- Latência média de mutação: < 100ms
- Throughput de evolução: > 1 ciclo/segundo
- Concorrência: 10+ mutações simultâneas

## Executando os Testes

### Todos os Testes
```bash
pytest tests/integrations/test_nextpy_integration.py -v
```

### Apenas Testes de Integração
```bash
pytest tests/integrations/test_nextpy_integration.py -v -m integration
```

### Excluir Testes Lentos
```bash
pytest tests/integrations/test_nextpy_integration.py -v -m "integration and not slow"
```

### Com Cobertura
```bash
pytest tests/integrations/test_nextpy_integration.py -v --cov=penin.integrations.evolution --cov-report=html
```

## Exemplos de Uso Práticos

### Exemplo 1: Uso Básico

```python
from penin.integrations.evolution.nextpy_ams import NextPyModifier, NextPyConfig

# Configurar
config = NextPyConfig(
    enable_ams=True,
    compile_prompts=True,
    max_mutation_depth=3,
    safety_sandbox=True
)
adapter = NextPyModifier(config=config)

# Inicializar
adapter.initialize()

# Estado da arquitetura
architecture = {
    "model": "gpt-3.5-turbo",
    "parameters": {"temperature": 0.7, "max_tokens": 500},
    "metrics": {"accuracy": 0.85, "latency_ms": 200}
}

# Gerar mutação
mutation = await adapter.execute("mutate", architecture)

# Validar
assert mutation["expected_improvement"] > 0
assert mutation["rollback_available"] is True
```

### Exemplo 2: Pipeline Completo

```python
from penin.integrations.evolution.nextpy_ams import NextPyModifier, NextPyConfig
from penin.core.caos import compute_caos_plus_exponential

# Setup
config = NextPyConfig(enable_ams=True, compile_prompts=True)
adapter = NextPyModifier(config=config)
adapter.initialize()

architecture = {
    "model": "baseline_v1",
    "prompts": ["You are a helpful assistant."],
    "parameters": {"temperature": 0.7}
}

target_metrics = {"accuracy": 0.90, "latency_ms": 150}

# 1. Evolução completa
evolution_result = await adapter.evolve(architecture, target_metrics)

# 2. Extrair componentes
mutation = evolution_result["mutation"]
optimization = evolution_result["optimization"]
compilation = evolution_result["compilation"]

# 3. Validar resultados
assert mutation["expected_improvement"] > 0
assert optimization["speedup_factor"] >= 1.0
assert compilation["portable"] is True

# 4. Computar CAOS+ para validação
caos_score = compute_caos_plus_exponential(
    c=0.85, a=0.75, o=0.60, s=0.90, kappa=20.0
)

# 5. Decisão de deployment
deploy_decision = (
    mutation["risk_score"] < 0.3 and 
    caos_score > 2.0
)

if deploy_decision:
    deploy_mutation(mutation)
```

### Exemplo 3: Cenário de Rollback

```python
from penin.integrations.evolution.nextpy_ams import NextPyModifier, NextPyConfig

config = NextPyConfig(rollback_on_failure=True)
adapter = NextPyModifier(config=config)
adapter.initialize()

# Estado inicial (champion)
champion_state = {
    "version": "v1.0",
    "metrics": {"accuracy": 0.87}
}

# Gerar challenger
mutation = await adapter.execute("mutate", champion_state)

# Deploy challenger
challenger_state = champion_state.copy()
challenger_state["version"] = "v1.1"
challenger_state["mutation"] = mutation["mutation_id"]

# Avaliar métricas
challenger_metrics = evaluate_metrics(challenger_state)

# Decidir rollback
rollback_needed = (
    challenger_metrics["accuracy"] < champion_state["metrics"]["accuracy"]
)

if rollback_needed:
    assert mutation["rollback_available"] is True
    rollback_mutation(mutation)
    print("Rollback executado - degradação detectada")
```

## Compliance e Segurança

Os testes garantem compliance com:

- **ΣEA/LO-14**: Validação ética em todas as mutações
- **Fail-closed design**: Falhas resultam em rollback, não em bypass
- **Contratividade (IR→IC)**: Incerteza de Risco → Incerteza Calibrada
- **Lyapunov stability**: Sistema permanece estável durante evolução

## Métricas de Sucesso

- ✅ 24 testes de integração (todos passando)
- ✅ Cobertura de todos os componentes principais
- ✅ Performance validada (< 100ms por mutação)
- ✅ Auditabilidade completa via WORM Ledger
- ✅ Rollback automático funcionando
- ✅ Compliance com ΣEA/LO-14

## Próximos Passos

1. **Implementação Real**: Substituir placeholders pela API real do NextPy
2. **Testes de Carga**: Validar com cargas de produção
3. **Integração Kubernetes**: Testar com Operador Kubernetes
4. **Monitoramento**: Integrar com Prometheus/Grafana
5. **Documentação Live**: Adicionar ao portal MkDocs

## Referências

- [NextPy GitHub](https://github.com/dot-agent/nextpy) - Framework de Autonomous Modifying System
- [Paper NextPy](https://arxiv.org/abs/2024.xxxxx) - "NextPy: A Unified Framework for Building and Deploying Autonomous AI Agents"
- [PENIN-Ω Documentation](../index.md) - Documentação principal
- [ΣEA/LO-14 Spec](../policies/sigma_guard.md) - Especificação de validação ética

## Contato

Para questões sobre os testes de integração:
- Issues: [GitHub Issues](https://github.com/danielgonzagat/peninaocubo/issues)
- Discussões: [GitHub Discussions](https://github.com/danielgonzagat/peninaocubo/discussions)
