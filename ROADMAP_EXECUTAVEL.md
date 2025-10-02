# 🎯 ROADMAP EXECUTÁVEL - PENIN-Ω PARA IA³ REAL

**Objetivo**: Transformar peninaocubo em IA ao cubo FUNCIONAL  
**Método**: Científico, incremental, validável  
**Prazo**: Faseado em sprints de 1-2 semanas  

---

## 🔥 FASE 0: CLEANUP CRÍTICO (1-2 dias)

**Objetivo**: Eliminar confusão e estabelecer fontes canônicas

### P0-1: Consolidar penin/omega/
**Problema**: 7,466 linhas em 29 arquivos, muita duplicação

**Ações**:
1. Identificar duplicatas exatas com outros módulos
2. Mover código canônico para módulos específicos:
   - `omega/caos.py` → `core/caos.py` (já existe)
   - `omega/scoring.py` → `math/linf.py` (já existe)
   - `omega/guards.py` → `guard/sigma_guard_complete.py`
   - `omega/ledger.py` → `ledger/worm_ledger_complete.py`
3. Deletar arquivos obsoletos/não usados:
   - `omega/market.py` (se não usado)
   - `omega/game.py` (se não usado)
   - `omega/zero_consciousness.py` (se especulativo)
   - `omega/neural_chain.py` (se não usado)
4. Criar `omega/DEPRECATED.md` listando o que foi movido
5. Manter apenas APIs públicas em `omega/__init__.py`

**Validação**: Testes continuam passando após cleanup

### P0-2: Unificar CLI
**Problema**: 3 CLIs diferentes (confusão)

**Ações**:
1. Escolher ÚNICO ponto de entrada: `penin` (via `__main__.py`)
2. Mover funcionalidades de `cli.py` para módulos
3. Deletar ou marcar como deprecated `cli/peninctl`
4. Consolidar em estrutura clara:
   ```
   penin/
     cli/
       __init__.py      # Public CLI API
       commands/
         evolve.py
         guard.py
         sr.py
         meta.py
         report.py
   ```

**Validação**: `penin --help` mostra todos comandos

### P0-3: Modularizar router.py
**Problema**: 34,035 linhas em arquivo único!

**Ações**:
1. Quebrar em módulos:
   ```
   router_pkg/
     __init__.py          # Public API
     core.py              # Router core
     budget_tracker.py    # Already done ✅
     circuit_breaker.py   # Extract
     cache.py             # Extract
     analytics.py         # Extract
     fallback.py          # Extract
   ```
2. Manter `router.py` como facade (imports e exports)
3. Cada módulo ≤ 500 linhas

**Validação**: Router tests continuam passando

### P0-4: Clarificar Equations
**Problema**: Confusão entre theory/impl/runtime

**Ações**:
1. Criar README em cada pasta:
   - `equations/README.md`: "Theoretical definitions"
   - `math/README.md`: "Production implementations"
   - `core/README.md`: "Runtime orchestration"
2. Adicionar docstrings claras indicando fonte canônica
3. Remover duplicações desnecessárias

**Validação**: Documentação clara de onde importar

---

## 🎯 FASE 1: COMPLETAR CORE (1 semana)

**Objetivo**: Todos os componentes core 100% funcionais

### P1-1: Router Features Completas
**Falta**: Circuit breakers, cache, analytics (tests skipped)

**Ações**:
1. Implementar circuit breaker internals:
   - `_record_provider_failure()`
   - `_record_provider_success()`
   - `_is_circuit_open()`
   - States: CLOSED, OPEN, HALF_OPEN
2. Implementar cache L1/L2:
   - LRU cache with TTL
   - HMAC-SHA256 keys
   - Hit/miss tracking
3. Implementar analytics:
   - Latency histograms
   - Success rates
   - Cost tracking
   - Provider comparisons
4. Criar testes para cada feature

**Validação**: 15 router tests skipped → 0 skipped

### P1-2: Provider Testing Real
**Falta**: Testes com providers reais

**Ações**:
1. Criar mocks realistas para cada provider
2. Testes de integração com rate limiting
3. Testes de fallback entre providers
4. Testes de custo (mock, mas realistas)
5. Documentar setup de API keys

**Validação**: 9 providers, todos testados

### P1-3: Pipeline Auto-Evolução END-TO-END
**Falta**: Pipeline completo funcional

**Ações**:
1. Implementar `ShadowDeployment`:
   - Espelha tráfego para challenger
   - Não impacta production
   - Coleta métricas
2. Implementar `CanaryDeployment`:
   - Roteamento 1-5% para challenger
   - Monitora erros
   - Auto-rollback se degradar
3. Implementar `ChampionPromotion`:
   - Valida ΔL∞ ≥ β_min
   - Valida gates (Σ-Guard)
   - Atomic swap
   - Grava PCAg
4. Criar teste end-to-end completo

**Validação**: Demo de auto-evolução funcionando

### P1-4: Observabilidade Completa
**Falta**: Dashboards, Loki, Tempo

**Ações**:
1. Criar dashboards Grafana (JSON):
   - `dashboards/overview.json`
   - `dashboards/evolution.json`
   - `dashboards/router.json`
   - `dashboards/ethics.json`
2. Configurar Loki:
   - `deploy/loki/config.yml`
   - Log aggregation
   - Queries úteis
3. Configurar Tempo:
   - Distributed tracing
   - Trace exemplars
4. Criar `docker-compose.observability.yml` completo

**Validação**: Dashboards funcionando localmente

### P1-5: CI/CD Production-Grade
**Falta**: Security, SBOM, releases

**Ações**:
1. Integrar security scanning (workflow):
   - Bandit (SAST)
   - Trivy (containers)
   - Gitleaks (secrets)
2. Integrar SBOM generation:
   - CycloneDX
   - Auto-attach to releases
3. Release automation:
   - Semantic versioning
   - Changelog auto-generation
   - Container builds
   - Signature (cosign)
4. Deploy docs to GitHub Pages

**Validação**: Release v1.0.0 automático

---

## 🚀 FASE 2: INTEGRATIONS & SOTA (2 semanas)

**Objetivo**: Integrar tecnologias SOTA para IA³

### P2-1: Priority 2 Integrations
**Falta**: goNEAT, Mammoth, SymbolicAI, NASLib

**Ações**:
1. **goNEAT** (neuroevolução):
   - Adapter completo
   - Integração com Ω-META
   - Benchmark vs NEAT baseline
2. **Mammoth** (continual learning):
   - Adapter para experience replay
   - Integração com ContinuousLearner
   - Testes de catastrophic forgetting
3. **SymbolicAI** (neurosymbolic):
   - Adapter para reasoning
   - Integração com Self-RAG
   - Testes de logical queries
4. **NASLib** (NAS):
   - Adapter para architecture search
   - Integração com Ω-META
   - Benchmarks de eficiência

**Validação**: 4 integrações P2, todas testadas

### P2-2: Priority 3 Integrations
**Falta**: midwiving-ai, SwarmRL, OpenCog

**Ações**:
1. **midwiving-ai** (consciousness):
   - Protocolo de indução
   - Integração com SR-Ω∞
   - Métricas de proto-consciência
2. **SwarmRL** (swarm):
   - Multi-agent coordination
   - Collective intelligence
   - Emergent behaviors
3. **OpenCog AtomSpace** (AGI):
   - Knowledge graph backend
   - Hypergraph reasoning
   - Integration com Self-RAG

**Validação**: 3 integrações P3, todas testadas

### P2-3: Neuromorphic Computing
**Falta**: SpikingBrain-7B integration

**Ações**:
1. Adapter para SpikingBrain-7B
2. Benchmark de eficiência (100× speedup)
3. Integração com router (provider)
4. Testes de sparsity

**Validação**: Neuromorphic provider funcional

---

## 🏆 FASE 3: PRODUCTION HARDENING (2 semanas)

**Objetivo**: Sistema production-ready

### P3-1: Security Hardening
**Ações**:
1. Secrets management (HashiCorp Vault)
2. mTLS entre serviços
3. Network policies (K8s)
4. RBAC definitions
5. Penetration testing

**Validação**: Security audit passa

### P3-2: Reliability Engineering
**Ações**:
1. Health checks robustos (liveness/readiness)
2. Graceful shutdown (SIGTERM handling)
3. Resource limits (CPU/memory)
4. Circuit breakers em TODOS serviços
5. Retry policies exponential backoff

**Validação**: Chaos tests passando

### P3-3: Performance Optimization
**Ações**:
1. Profiling (cProfile, py-spy)
2. Otimização de hot paths
3. Caching strategies
4. Database query optimization
5. Benchmarks publicados

**Validação**: P95 latency ≤ 100ms

### P3-4: Multi-Tenancy
**Ações**:
1. Tenant isolation
2. Budget por tenant
3. Audit por tenant
4. Resource quotas
5. Billing tracking

**Validação**: Multi-tenant demo

### P3-5: Kubernetes Operator
**Ações**:
1. CRDs definition
2. Controller implementation
3. Reconciliation loop
4. Webhooks (validation/mutation)
5. E2E operator tests

**Validação**: Operator deploy funcional

---

## 🌟 FASE 4: AGI FEATURES (ongoing)

**Objetivo**: Recursos avançados de IA³

### P4-1: Meta-Learning Avançado
**Ações**:
1. MAML implementation
2. Neural ODEs
3. Hypernetworks
4. Few-shot learning

**Validação**: Benchmarks vs SOTA

### P4-2: Causal Reasoning
**Ações**:
1. Causal graph learning
2. Do-calculus implementation
3. Counterfactual reasoning
4. Intervention testing

**Validação**: Causal benchmarks

### P4-3: Hierarchical Planning
**Ações**:
1. Temporal abstraction
2. Options framework
3. Hierarchical RL
4. Goal conditioning

**Validação**: Planning benchmarks

### P4-4: Compositional Generalization
**Ações**:
1. Modular networks
2. Program synthesis
3. Systematic generalization
4. SCAN benchmark

**Validação**: Compositional tests

---

## 📊 MÉTRICAS DE SUCESSO

### Fase 0 (Cleanup)
- [ ] Omega/ reduzido para ≤ 2,000 linhas
- [ ] CLI unificado (1 entrypoint)
- [ ] Router modularizado (≤ 500 linhas/file)
- [ ] Documentação clara de sources

### Fase 1 (Core Complete)
- [ ] 600+/603 tests passing (99%+)
- [ ] 0 skipped (legitimate)
- [ ] Dashboards funcionando
- [ ] Release automation working
- [ ] Demo end-to-end < 60s

### Fase 2 (Integrations)
- [ ] 7 integrações SOTA completas
- [ ] Benchmarks publicados
- [ ] Papers citados
- [ ] Performance validado

### Fase 3 (Production)
- [ ] Security audit passa
- [ ] SLA 99.9% (simulated)
- [ ] Multi-tenant demo
- [ ] K8s operator funcional
- [ ] Chaos tests passing

### Fase 4 (AGI)
- [ ] Meta-learning working
- [ ] Causal reasoning demo
- [ ] Hierarchical planning demo
- [ ] Compositional generalization

---

## 🎯 DEFINIÇÃO DE PRONTO (DoD) GLOBAL

Um item só é considerado "PRONTO" quando:

1. ✅ Código implementado e documentado
2. ✅ Testes passando (unit + integration)
3. ✅ Benchmarks executados (se aplicável)
4. ✅ Documentação atualizada
5. ✅ CI/CD verde
6. ✅ Revisado por peer (se possível)
7. ✅ Merged to main
8. ✅ Tagged em release

---

## 🚀 PRÓXIMOS PASSOS IMEDIATOS

Começar pela **FASE 0: CLEANUP CRÍTICO**

1. Analisar penin/omega/ linha por linha
2. Identificar duplicatas exatas
3. Mover código para módulos canônicos
4. Deletar obsoletos
5. Validar testes

**Tempo estimado**: 1-2 dias de trabalho focado

**Começando AGORA...**
