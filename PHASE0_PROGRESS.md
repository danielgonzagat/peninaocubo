# FASE 0: CLEANUP CRÍTICO - Progresso

**Objetivo**: Eliminar confusão, consolidar código, fontes canônicas  
**Iniciado**: 2025-10-02  
**Status**: EM PROGRESSO  

---

## ✅ P0-1: Consolidar penin/omega/ - PARCIAL

### Progresso Atual

**Removidos (6 arquivos, 109 linhas)**:
- ✅ market.py (41 linhas) - Mercado interno não usado
- ✅ game.py (3 linhas) - Função EMA trivial
- ✅ zero_consciousness.py (10 linhas) - SPI proxy não integrado
- ✅ neural_chain.py (32 linhas) - Ledger obsoleto
- ✅ checkpoint.py (22 linhas) - Snapshots não usados
- ✅ darwin_audit.py (7 linhas) - Função única não usada

**Status**: 7,466 → 7,357 linhas (↓1.5%)

### Próximos Passos

**Analisar Grandes Arquivos** (possíveis duplicatas):

1. **sr.py** (1,157 linhas)
   - Comparar com: `penin.sr.sr_service.py` (553 linhas)
   - Comparar com: `penin.math.sr_omega_infinity.py`
   - Ação: Determinar fonte canônica

2. **ethics_metrics.py** (958 linhas)
   - Comparar com: `penin.ethics.laws.py`
   - Comparar com: `penin.ethics.validators.py`
   - Ação: Consolidar ou clarificar

3. **ledger.py** (801 linhas)
   - Comparar com: `penin.ledger.worm_ledger_complete.py` (673 linhas)
   - Ação: Determinar qual é canônico

4. **guards.py** (764 linhas)
   - Comparar com: `penin.guard.sigma_guard_complete.py` (638 linhas)
   - Ação: Consolidar duplicações

### Estimativa

- Tempo: 2-3 horas para análise completa
- Redução esperada: 1,000-2,000 linhas adicionais (13-26%)
- Objetivo final: omega/ com ≤ 5,000 linhas

---

## ⏳ P0-2: Unificar CLI - PENDENTE

### Problema

Temos 3 CLIs diferentes:
- `penin/__main__.py` (executável)
- `penin/cli.py` (23,401 linhas!)
- `penin/cli/peninctl` (script bash)

### Plano

1. Analisar qual é o principal
2. Consolidar comandos
3. Criar estrutura modular:
   ```
   cli/
     commands/
       evolve.py
       guard.py
       sr.py
       meta.py
   ```
4. Deletar redundâncias

### Estimativa

- Tempo: 3-4 horas
- Objetivo: 1 CLI, ≤ 1,000 linhas

---

## ⏳ P0-3: Modularizar router.py - PENDENTE

### Problema

`router.py` tem 34,035 linhas em arquivo único!

### Plano

1. Quebrar em módulos:
   - `router_pkg/core.py`
   - `router_pkg/circuit_breaker.py`
   - `router_pkg/cache.py`
   - `router_pkg/analytics.py`
   - `router_pkg/fallback.py`

2. Manter `router.py` como facade

3. Cada arquivo ≤ 500 linhas

### Estimativa

- Tempo: 4-5 horas
- Objetivo: 7-8 arquivos modulares

---

## 📊 Métricas Atuais

```
Total Python:     30,465 linhas
Removido:         109 linhas
Pendente remoção: ~1,500-2,500 linhas estimadas

Testes:           561/603 passing (93.0%)
Skipped:          44 (legitimate + incomplete)
```

---

## 🎯 Próximo Passo

Analisar **sr.py** vs outros módulos SR para determinar duplicações.

**Comando**:
```bash
# Comparar sr.py com outros módulos
diff -u penin/omega/sr.py penin/sr/sr_service.py
```

Continuando análise...
