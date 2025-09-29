# PENIN-Ω v7.1 → v8.0 - Próximos Passos Técnicos

**Base:** v7.1 com P0 completo  
**Objetivo:** Sistema auto-evolutivo universal end-to-end  
**Timeline:** 3-6 sprints (6-12 semanas)

---

## 🎯 Visão Geral

Com P0 completo (ethics, security, WAL, budget), temos fundação sólida para:

1. **Refatoração modular** (`penin/omega/`)
2. **Auto-evolução end-to-end** (mutate→evaluate→promote)
3. **Fine-tuning via APIs** (Mistral/OpenAI/Grok)
4. **CLI operacional** (`penin` command)

---

## 📋 Roadmap Detalhado

### Sprint 1-2: Kernel Ω (Módulos Base)

#### Semana 1: Scoring & CAOS⁺

**Tasks:**

1. **`penin/omega/scoring.py`**
   ```python
   # Funções a implementar:
   - normalize_series(values, method='minmax|sigmoid')
   - ema(series, alpha=0.2)
   - linf_harmonic(weights, metrics, cost, lambda_c, ethical_ok)
   - score_gate(U, S, C, L, wU, wS, wC, wL, tau) -> Verdict
   ```
   
   **Tests:**
   - L∞ com métrica zero → reduz muito
   - ethical_ok=False → retorna 0
   - score_gate com C alto penaliza

2. **`penin/omega/caos.py`**
   ```python
   # Implementar:
   - caos_plus(C, A, O, S, kappa, gamma, kappa_max)
   # Fórmula: phi = tanh(gamma * (O*S) * log(1 + kappa*C*A))
   ```
   
   **Tests:**
   - Overflow com κ grande não estoura
   - Monotonicidade em C, A
   - phi ∈ [0,1)

**Entrega:** 2 módulos + testes (cobertura >90%)

---

#### Semana 2: SR & Guards

**Tasks:**

1. **`penin/omega/sr.py`**
   ```python
   # SR-Ω∞: Self-Reflection non-compensatory
   - sr_omega(awareness, ethics_ok, autocorr, metacog)
   # Usar média harmônica ou min-soft p-norm
   ```

2. **`penin/omega/guards.py`**
   ```python
   # Σ-Guard + IR→IC
   - sigma_guard(ece, rho_bias, fairness, consent, eco_ok, thresholds)
     -> (ok: bool, details: dict)
   
   - ir_to_ic_contractive(risk_series, rho_threshold=1.0)
     -> (contractive: bool, rho: float)
   ```
   
   **Integração com ethics_metrics:**
   ```python
   from penin.omega.ethics_metrics import compute_ethics_attestation
   
   attestation = compute_ethics_attestation(...)
   
   sigma_ok, details = sigma_guard(
       ece=attestation.ece,
       rho_bias=attestation.rho_bias,
       fairness=attestation.fairness_score,
       consent=attestation.consent_ok,
       eco_ok=(attestation.eco_impact_kg < threshold),
       thresholds={...}
   )
   ```

**Entrega:** 2 módulos + testes + integração com ethics

---

### Sprint 3: WORM & Mutators

#### Semana 3: Ledger Refactored

**Tasks:**

1. **`penin/omega/ledger.py`**
   - Refatorar `WORMLedger` do `1_de_8_v7.py`
   - Manter WAL + busy_timeout (P0-3)
   - Adicionar:
     - `runs/<ts_id>/` structure
     - `artifacts/` subdirectory
     - Atomic promotion pointer (`champion.json`)
   
   **Schema expandido:**
   ```sql
   CREATE TABLE runs (
       id TEXT PRIMARY KEY,
       ts REAL,
       git_sha TEXT,
       seed INTEGER,
       provider_id TEXT,
       candidate_cfg_hash TEXT,
       
       -- Metrics
       u_score REAL,
       s_score REAL,
       c_score REAL,
       l_score REAL,
       linf REAL,
       score REAL,
       cost_usd REAL,
       latency_ms REAL,
       
       -- Gates
       sigma_guard_ok INTEGER,
       ir_ic_ok INTEGER,
       sr REAL,
       caos_phi REAL,
       
       -- Decision
       verdict TEXT,  -- 'promote'|'canary'|'fail'
       reason TEXT,
       
       -- Diffs vs champion
       delta_linf REAL,
       delta_score REAL,
       
       -- Artifacts
       artifacts_path TEXT,
       
       -- Evidence
       ethics_attest_hash TEXT,
       config_hash TEXT
   );
   ```

**Entrega:** Ledger refatorado + testes de concorrência

---

#### Semana 4: Mutators v1 (Param Sweeps)

**Tasks:**

1. **`penin/omega/mutators.py`**
   ```python
   # v1: Param sweeps + prompt variants (sem treinar)
   
   def generate_param_sweeps(base_cfg, n_challengers, seed):
       """Gera variantes de parâmetros"""
       sweeps = []
       for i in range(n_challengers):
           variant = base_cfg.copy()
           variant['temperature'] = random.uniform(0.1, 1.5)
           variant['top_p'] = random.uniform(0.5, 1.0)
           variant['max_tokens'] = random.choice([100, 200, 500, 1000])
           sweeps.append(variant)
       return sweeps
   
   def generate_prompt_variants(base_prompt, templates, seed):
       """Gera variantes de prompt"""
       variants = []
       for template in templates:
           variant = template.format(base=base_prompt)
           variants.append(variant)
       return variants
   ```

**Tests:**
- Determinismo com seed
- N variantes sem colisão de hash

**Entrega:** Mutators v1 + testes

---

### Sprint 4: Evaluators & ACFA

#### Semana 5: Evaluators (U/S/C/L)

**Tasks:**

1. **`penin/omega/evaluators.py`**
   ```python
   # Bateria de tarefas determinísticas
   
   class TaskBattery:
       def evaluate_utility(self, model, tasks):
           """U: exact match, F1, ROUGE"""
           # Tasks: regex→json, summarization, field extraction
       
       def evaluate_stability(self, model, tasks):
           """S: ECE, robustez, OOD"""
           # ECE (já temos em ethics_metrics)
           # Robustez: perturbações no prompt
       
       def evaluate_cost(self, model, tasks):
           """C: tokens, latency, $$"""
           # Normalizar por baseline
       
       def evaluate_learning(self, model, tasks):
           """L: reuso, composição, tooling"""
           # Heurísticas: redução latência, novos tools, etc.
   ```

**Saída:**
```python
{
    "U": 0.85,  # Normalizado [0,1]
    "S": 0.92,
    "C": 0.65,  # Menor é melhor (invertido no score)
    "L": 0.70,
    "raw": {
        "U": {"em": 0.8, "f1": 0.9, "rouge": 0.85},
        "S": {"ece": 0.08, "robustness": 0.96},
        "C": {"tokens": 1500, "cost_usd": 0.03, "latency_ms": 850},
        "L": {"reuse": 0.7, "composition": 0.7}
    },
    "usage": {"tokens_in": 500, "tokens_out": 1000},
    "latency_ms": 850,
    "cost_usd": 0.03
}
```

**Entrega:** Evaluators + tarefas toy + testes

---

#### Semana 6: ACFA (Liga & Canário)

**Tasks:**

1. **`penin/omega/acfa.py`**
   ```python
   # Liga champion↔challenger com shadow/canary
   
   class LeagueOrchestrator:
       def canary_test(
           self,
           provider,
           champion,
           challenger,
           fraction=0.05,
           duration_s=300
       ):
           """Testa challenger com fração de tráfego"""
       
       def decide_promotion(
           self,
           score_result,
           delta_linf,
           guards_ok,
           beta_min=0.02
       ):
           """Decide: promote|rollback|canary"""
           # Regras:
           # - promote: score≥tau AND ΔL∞≥β_min AND guards_ok
           # - canary: score≥tau_low AND guards_ok
           # - rollback: score<tau_low OR not guards_ok
   ```

**Tests:**
- Caso borderline → canário
- Caso excelente → promote
- Caso ruim → rollback

**Entrega:** ACFA + testes

---

### Sprint 5: Tuner & Runners

#### Semana 7: Auto-Tuning

**Tasks:**

1. **`penin/omega/tuner.py`**
   ```python
   # AdaGrad/ONS para hiperparâmetros
   
   class OnlineTuner:
       def __init__(self, params, learning_rate=0.01, max_delta=0.02):
           self.params = params  # κ, λ_c, wU, wS, wC, wL, β_min, τ
           self.learning_rate = learning_rate
           self.max_delta = max_delta  # Limite de variação por ciclo
           self.history = []
       
       def update(self, objective, gradients):
           """Atualiza params com AdaGrad"""
           # Objetivo: maximizar L∞ com penalidade de custo
           # Clamps: Δ≤max_delta por ciclo
       
       def get_params(self):
           """Retorna params atuais"""
   ```

**Tests:**
- Converge suavemente
- Nunca estoura faixas
- Respeita max_delta

**Entrega:** Tuner + testes

---

#### Semana 8: Runner (Orquestrador)

**Tasks:**

1. **`penin/omega/runners.py`**
   ```python
   # Ciclo completo: mutate→evaluate→decide→(promote|rollback)
   
   async def evolve_one_cycle(
       n_challengers=8,
       budget_minutes=30,
       provider_id="openai",
       dry_run=False
   ):
       """
       1. Gerar challengers (mutators)
       2. Avaliar challengers (evaluators)
       3. Calcular gates (Σ-Guard, SR, CAOS⁺, L∞)
       4. Decidir (ACFA)
       5. Registrar ledger
       6. Promover/rollback/canário
       7. Atualizar tuner
       """
       
       # 1. Mutate
       challengers = mutators.generate_param_sweeps(...)
       
       # 2. Evaluate
       for challenger in challengers:
           metrics = evaluators.evaluate(challenger)
           
           # 3. Gates
           ethics = ethics_metrics.compute_ethics_attestation(...)
           sigma_ok, _ = guards.sigma_guard(...)
           sr = sr.sr_omega(...)
           caos = caos.caos_plus(...)
           linf = scoring.linf_harmonic(...)
           score = scoring.score_gate(...)
           
           # 4. Decide
           verdict = acfa.decide_promotion(...)
           
           # 5. Ledger
           ledger.record_run(...)
           
           # 6. Promote/rollback
           if verdict == 'promote':
               acfa.promote(challenger)
           elif verdict == 'canary':
               acfa.deploy_canary(challenger)
           else:
               acfa.rollback()
       
       # 7. Tune
       tuner.update(...)
       
       return {
           "best_challenger": ...,
           "verdict": ...,
           "metrics": ...,
       }
   ```

**Tests:**
- Cria `runs/<id>/` e apenda no ledger
- Retorna decisão coerente
- Dry-run não promove

**Entrega:** Runner completo + testes

---

### Sprint 6: CLI & Fine-Tuning APIs

#### Semana 9: CLI

**Tasks:**

1. **`penin/cli.py`**
   ```python
   # CLI principal: penin <command>
   
   import click
   
   @click.group()
   def cli():
       """PENIN-Ω CLI"""
   
   @cli.command()
   @click.option('--n', default=8, help='Number of challengers')
   @click.option('--budget', default='30m', help='Budget (e.g. 30m, 2h)')
   @click.option('--provider', default='openai', help='Provider ID')
   @click.option('--dry-run', is_flag=True, help='Dry run (no promotion)')
   def evolve(n, budget, provider, dry_run):
       """Run evolution cycle"""
       asyncio.run(runners.evolve_one_cycle(...))
   
   @cli.command()
   @click.option('--model', required=True, help='Model path or provider')
   @click.option('--suite', default='basic', help='Test suite')
   def evaluate(model, suite):
       """Evaluate model"""
       evaluators.run_suite(model, suite)
   
   @cli.command()
   @click.argument('run_id')
   def promote(run_id):
       """Promote a run to champion"""
       acfa.promote(run_id)
   
   @cli.command()
   @click.option('--to', default='LAST_GOOD', help='Rollback target')
   def rollback(to):
       """Rollback to previous champion"""
       acfa.rollback(to)
   
   @cli.command()
   @click.option('--serve', is_flag=True, help='Serve dashboard')
   def dashboard(serve):
       """Launch dashboard"""
       if serve:
           # Launch MkDocs or Streamlit dashboard
           pass
   ```

**Instalação:**
```python
# setup.py
setup(
    name="penin-omega",
    entry_points={
        'console_scripts': [
            'penin=penin.cli:cli',
        ],
    },
)
```

**Entrega:** CLI funcional + smoke tests

---

#### Semana 10-12: Fine-Tuning via APIs

**Tasks:**

1. **Integração Mistral AI**
   ```python
   # penin/finetuning/mistral.py
   
   from mistralai import Mistral
   
   class MistralFineTuner:
       def upload_data(self, training_file, validation_file):
           """Upload JSONL files"""
       
       def create_job(self, model, hyperparams):
           """Create fine-tuning job"""
       
       def monitor_job(self, job_id):
           """Poll job status"""
       
       def get_model(self, job_id):
           """Get fine-tuned model ID"""
   ```

2. **Integração OpenAI**
   ```python
   # penin/finetuning/openai.py
   
   class OpenAIFineTuner:
       # Similar à Mistral
   ```

3. **Integração Grok/XAI**
   ```python
   # penin/finetuning/grok.py
   
   class GrokFineTuner:
       # Similar
   ```

4. **Orquestração**
   ```python
   # penin/finetuning/orchestrator.py
   
   async def finetune_and_evolve(
       base_model="gpt-4o-mini",
       provider="openai",
       training_data_path="data/train.jsonl",
       validation_data_path="data/val.jsonl",
       hyperparams={"n_epochs": 3}
   ):
       """Fine-tune via API e integrar no ciclo"""
       
       # 1. Upload data
       train_file = finetuner.upload_data(training_data_path)
       val_file = finetuner.upload_data(validation_data_path)
       
       # 2. Create job
       job = finetuner.create_job(base_model, hyperparams)
       
       # 3. Monitor
       while job.status != "succeeded":
           await asyncio.sleep(60)
           job = finetuner.get_job(job.id)
       
       # 4. Get model
       ft_model = finetuner.get_model(job.id)
       
       # 5. Evaluate
       metrics = evaluators.evaluate(ft_model)
       
       # 6. Promote if good
       if metrics["score"] > threshold:
           acfa.promote(ft_model)
       
       return ft_model
   ```

**Entrega:** Fine-tuning integrado + exemplos

---

## 🎯 Milestones

### v7.2 (Sprint 1-2)
- ✅ Scoring, CAOS⁺, SR, Guards
- ✅ Testes >90% cobertura

### v7.5 (Sprint 3-4)
- ✅ Ledger refatorado
- ✅ Mutators v1 (param sweeps)
- ✅ Evaluators U/S/C/L
- ✅ ACFA (canário + decisão)

### v7.8 (Sprint 5)
- ✅ Tuner (AdaGrad/ONS)
- ✅ Runner (evolve_one_cycle)

### v8.0 (Sprint 6)
- ✅ CLI completo
- ✅ Fine-tuning via APIs (Mistral/OpenAI/Grok)
- ✅ Sistema auto-evolutivo end-to-end

---

## 📊 Critérios de Aceitação v8.0

- [ ] `penin evolve --dry-run` gera challengers e decide
- [ ] `penin evolve` promove/rollback coerentemente
- [ ] Ledger mostra ΔL∞≥β_min antes de promover
- [ ] Σ-Guard/IR→IC sempre checados
- [ ] CI verde (pytest + lint)
- [ ] Docs publicadas (MkDocs)
- [ ] Adapters "plug-and-play" (HF/vLLM/APIs)
- [ ] Tuner ajusta κ/λ_c/w/β/τ sem instabilidade
- [ ] Fine-tuning via API funciona (Mistral + OpenAI)

---

## 🚨 Riscos & Mitigações

### Risco 1: Complexidade aumenta muito
**Mitigação:** Módulos coesos, testes unitários, docs inline

### Risco 2: Fine-tuning caro
**Mitigação:** Router com budget (P0-4), começar com param sweeps

### Risco 3: Overfitting em challengers
**Mitigação:** Validação cruzada, canário antes de promover

### Risco 4: Tuner instável
**Mitigação:** max_delta por ciclo, clamps, warmup de N ciclos

---

## 📝 Template de Feature Branch

```bash
# Nomenclatura
git checkout -b sprint-X/module-name

# Exemplos
git checkout -b sprint-1/scoring
git checkout -b sprint-2/guards
git checkout -b sprint-3/ledger-refactor
```

---

## 🤝 Como Contribuir

1. Fork do repo
2. Criar feature branch (ver template acima)
3. Implementar módulo + testes (cobertura >80%)
4. Docs inline (docstrings) + README update
5. PR com template:
   ```markdown
   ## Sprint X - Módulo Y
   
   **O que foi feito:**
   - Lista de features
   
   **Testes:**
   - Cobertura: X%
   - Comandos: `pytest ...`
   
   **Docs:**
   - Docstrings completas: Yes/No
   - README atualizado: Yes/No
   
   **Checklist:**
   - [ ] Testes passando
   - [ ] Lint passando (ruff/black/mypy)
   - [ ] Docs completas
   - [ ] Backward compatible
   ```

---

**Última atualização:** 2025-01-XX  
**Versão base:** v7.1  
**Objetivo:** v8.0 (auto-evolução end-to-end)