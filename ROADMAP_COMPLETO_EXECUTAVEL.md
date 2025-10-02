# 🚀 PENIN-Ω - ROADMAP COMPLETO EXECUTÁVEL

**Objetivo**: Transformar código bem testado → sistema auto-evolutivo FUNCIONANDO  
**Método**: Fases incrementais, cada uma entrega valor  
**Tempo**: 10-20 horas total  
**Princípio**: FAZER FUNCIONAR, não adicionar mais código

---

## 📋 FASES DO ROADMAP

```
F0: Setup & Infraestrutura (1h)
F1: CLI Funcional Mínimo (2h)
F2: Pipeline E2E Básico (3h)
F3: WORM Ledger Integrado (2h)
F4: Σ-Guard Ativo (2h)
F5: Ω-META Gerando Mutações (3h)
F6: ACFA League Rodando (3h)
F7: Observabilidade & Release (2h)
────────────────────────────────
Total: ~18 horas
```

---

## F0: SETUP & INFRAESTRUTURA (1h)

**Objetivo**: Preparar ambiente para desenvolvimento E2E

### Tasks:

1. **Configurar pyproject.toml corretamente**
   ```toml
   [project.scripts]
   penin = "penin.cli:main"
   
   [project]
   name = "peninaocubo"
   version = "1.0.0-alpha"
   dependencies = [
       "fastapi>=0.104.0",
       "uvicorn>=0.24.0",
       "pydantic>=2.0.0",
       "numpy>=1.24.0",
       "python-dotenv>=1.0.0",
   ]
   
   [project.optional-dependencies]
   dev = [
       "pytest>=7.4.0",
       "pytest-cov>=4.1.0",
       "ruff>=0.1.0",
       "mypy>=1.7.0",
   ]
   ```

2. **Criar .env.example**
   ```env
   # LLM Providers
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   
   # Budget
   DAILY_BUDGET_USD=10.0
   
   # Paths
   LEDGER_DB_PATH=./data/worm_ledger.db
   CACHE_DIR=./data/cache
   ```

3. **Criar docker-compose.yml mínimo**
   ```yaml
   version: '3.8'
   services:
     prometheus:
       image: prom/prometheus:latest
       ports:
         - "9090:9090"
       volumes:
         - ./deploy/prometheus.yml:/etc/prometheus/prometheus.yml
     
     grafana:
       image: grafana/grafana:latest
       ports:
         - "3000:3000"
       volumes:
         - ./deploy/dashboards:/etc/grafana/provisioning/dashboards
   ```

**Aceite**: `pip install -e .` funciona, `penin --version` retorna versão

---

## F1: CLI FUNCIONAL MÍNIMO (2h)

**Objetivo**: CLI que roda comandos básicos

### Estrutura:

```python
# penin/cli/__init__.py
import typer

app = typer.Typer()

@app.command()
def version():
    """Show version"""
    from penin import __version__
    typer.echo(f"PENIN-Ω v{__version__}")

@app.command()
def evolve(
    n: int = 1,
    budget: float = 10.0,
    provider: str = "openai",
):
    """Run evolution cycle"""
    from penin.runners.evolution_runner import run_evolution
    run_evolution(n_cycles=n, budget_usd=budget, provider=provider)

@app.command()
def guard():
    """Start Σ-Guard service"""
    import uvicorn
    uvicorn.run("penin.guard.sigma_guard_service:app", host="0.0.0.0", port=8001)

@app.command()
def meta():
    """Start Ω-META service"""
    import uvicorn
    uvicorn.run("penin.meta.omega_meta_service:app", host="0.0.0.0", port=8002)

def main():
    app()
```

### Criar runner básico:

```python
# penin/runners/evolution_runner.py
from penin.core.caos import compute_caos_plus_exponential
from penin.math.linf_complete import compute_linf_complete
from penin.ledger.worm_ledger_complete import WORMLedger
from penin.router_pkg.budget_tracker import BudgetTracker

def run_evolution(n_cycles: int, budget_usd: float, provider: str):
    """Run N evolution cycles"""
    
    print(f"🚀 PENIN-Ω Evolution - {n_cycles} cycles, ${budget_usd} budget")
    
    tracker = BudgetTracker(daily_limit_usd=budget_usd)
    ledger = WORMLedger(db_path="./data/worm_ledger.db")
    
    for i in range(n_cycles):
        print(f"\n=== Cycle {i+1}/{n_cycles} ===")
        
        # 1. Compute CAOS+
        caos = compute_caos_plus_exponential(
            c=0.85, a=0.40, o=0.35, s=0.82, kappa=20.0
        )
        print(f"  CAOS+: {caos:.2f}")
        
        # 2. Compute L∞
        result = compute_linf_complete(
            metrics=[0.85, 0.78, 0.92],
            weights=[0.4, 0.3, 0.3],
            cost_normalized=0.05,
            lambda_cost=0.5
        )
        print(f"  L∞: {result['linf']:.3f}")
        
        # 3. Record decision
        ledger.append_entry(
            event_type="evolution_cycle",
            data={
                "cycle": i+1,
                "caos": caos,
                "linf": result['linf'],
                "provider": provider,
            },
            decision="continue" if caos > 1.5 else "rollback"
        )
        
        print(f"  ✅ Logged to WORM ledger")
    
    print(f"\n✅ Evolution complete!")
    print(f"   Budget used: ${tracker.used_usd:.2f} / ${tracker.daily_limit_usd:.2f}")
```

**Aceite**:
- `penin version` retorna versão
- `penin evolve --n 3` roda 3 ciclos e registra no ledger

---

## F2: PIPELINE E2E BÁSICO (3h)

**Objetivo**: Pipeline que gera, testa, decide e registra

### Criar pipeline básico:

```python
# penin/pipelines/basic_pipeline.py
from dataclasses import dataclass
from penin.core.caos import compute_caos_plus_exponential
from penin.math.linf_complete import compute_linf_complete
from penin.ledger.worm_ledger_complete import WORMLedger

@dataclass
class PipelineState:
    current_linf: float = 0.70
    current_caos: float = 1.50
    budget_remaining: float = 10.0

class BasicEvolutionPipeline:
    """Minimal E2E evolution pipeline"""
    
    def __init__(self, ledger_path: str = "./data/worm_ledger.db"):
        self.ledger = WORMLedger(db_path=ledger_path)
        self.state = PipelineState()
    
    def generate_mutation(self) -> dict:
        """Generate a simple mutation (placeholder for Ω-META)"""
        import random
        return {
            "type": "parameter_tweak",
            "delta_c": random.uniform(-0.05, 0.05),
            "delta_a": random.uniform(-0.05, 0.05),
        }
    
    def test_mutation(self, mutation: dict) -> dict:
        """Test mutation in shadow mode"""
        
        # Apply mutation
        c_new = max(0, min(1, 0.85 + mutation['delta_c']))
        a_new = max(0, min(1, 0.40 + mutation['delta_a']))
        
        # Compute new scores
        caos_new = compute_caos_plus_exponential(
            c=c_new, a=a_new, o=0.35, s=0.82, kappa=20.0
        )
        
        linf_new = compute_linf_complete(
            metrics=[c_new, a_new, 0.92],
            weights=[0.4, 0.3, 0.3],
            cost_normalized=0.05,
            lambda_cost=0.5
        )['linf']
        
        return {
            'caos': caos_new,
            'linf': linf_new,
            'delta_linf': linf_new - self.state.current_linf,
        }
    
    def decide_promotion(self, test_results: dict) -> dict:
        """Decide if mutation should be promoted (Σ-Guard logic)"""
        
        # Simple gates
        delta_linf = test_results['delta_linf']
        beta_min = 0.01
        
        gates = {
            'improvement': delta_linf >= beta_min,
            'caos_ok': test_results['caos'] > 1.0,
            'linf_ok': test_results['linf'] > 0.5,
        }
        
        decision = "PROMOTE" if all(gates.values()) else "REJECT"
        
        return {
            'decision': decision,
            'gates': gates,
            'delta_linf': delta_linf,
        }
    
    def record_decision(self, mutation: dict, test_results: dict, decision: dict):
        """Record decision in WORM ledger"""
        
        self.ledger.append_entry(
            event_type="mutation_decision",
            data={
                'mutation': mutation,
                'test_results': test_results,
                'decision': decision,
            },
            decision=decision['decision']
        )
    
    def run_cycle(self):
        """Run one complete E2E cycle"""
        
        print("🔄 Running evolution cycle...")
        
        # 1. Generate
        mutation = self.generate_mutation()
        print(f"  ✅ Generated mutation: {mutation}")
        
        # 2. Test
        test_results = self.test_mutation(mutation)
        print(f"  ✅ Tested: ΔL∞={test_results['delta_linf']:.4f}")
        
        # 3. Decide
        decision = self.decide_promotion(test_results)
        print(f"  ✅ Decision: {decision['decision']}")
        
        # 4. Record
        self.record_decision(mutation, test_results, decision)
        print(f"  ✅ Recorded in WORM ledger")
        
        # 5. Apply if promoted
        if decision['decision'] == "PROMOTE":
            self.state.current_linf = test_results['linf']
            self.state.current_caos = test_results['caos']
            print(f"  🎉 PROMOTED! New L∞={self.state.current_linf:.3f}")
        else:
            print(f"  ❌ REJECTED (gates failed)")
        
        return decision
```

**Uso**:
```python
# penin evolve --n 5
pipeline = BasicEvolutionPipeline()
for i in range(5):
    pipeline.run_cycle()
```

**Aceite**: Pipeline roda 5 ciclos, decide promote/reject, registra tudo

---

## F3: WORM LEDGER INTEGRADO (2h)

**Objetivo**: Todas decisões registradas com hash chain

### Melhorar WORMLedger:

```python
# penin/ledger/worm_ledger_complete.py (enhance)

class WORMLedger:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db()
        self.entries = []
        self._load_entries()
    
    def _ensure_db(self):
        """Create DB file if not exists"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                data_json TEXT NOT NULL,
                decision TEXT NOT NULL,
                prev_hash TEXT,
                entry_hash TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    def append_entry(self, event_type: str, data: dict, decision: str) -> str:
        """Append entry to WORM ledger with hash chain"""
        import hashlib
        import json
        from datetime import datetime
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        data_json = json.dumps(data, sort_keys=True)
        
        # Get previous hash
        prev_hash = self.entries[-1]['entry_hash'] if self.entries else "GENESIS"
        
        # Compute hash
        hash_input = f"{timestamp}|{event_type}|{data_json}|{decision}|{prev_hash}"
        entry_hash = hashlib.blake2b(hash_input.encode(), digest_size=32).hexdigest()
        
        # Save to DB
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO ledger (timestamp, event_type, data_json, decision, prev_hash, entry_hash) VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, event_type, data_json, decision, prev_hash, entry_hash)
        )
        conn.commit()
        conn.close()
        
        # Cache
        entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'data': data,
            'decision': decision,
            'prev_hash': prev_hash,
            'entry_hash': entry_hash,
        }
        self.entries.append(entry)
        
        return entry_hash
    
    def verify_chain(self) -> bool:
        """Verify hash chain integrity"""
        import hashlib
        import json
        
        for i, entry in enumerate(self.entries):
            # Recompute hash
            timestamp = entry['timestamp']
            event_type = entry['event_type']
            data_json = json.dumps(entry['data'], sort_keys=True)
            decision = entry['decision']
            prev_hash = entry['prev_hash']
            
            hash_input = f"{timestamp}|{event_type}|{data_json}|{decision}|{prev_hash}"
            expected_hash = hashlib.blake2b(hash_input.encode(), digest_size=32).hexdigest()
            
            if expected_hash != entry['entry_hash']:
                print(f"❌ Chain broken at entry {i}")
                return False
        
        return True
```

**Aceite**: Ledger salva, carrega, verifica hash chain

---

## F4: Σ-GUARD ATIVO (2h)

**Objetivo**: Gates que REALMENTE bloqueiam mutações ruins

### Implementar Σ-Guard funcional:

```python
# penin/guard/sigma_guard.py

from dataclasses import dataclass
from typing import Dict

@dataclass
class GuardGates:
    """All Σ-Guard gates"""
    contractivity: bool = True  # ρ < 1
    calibration: bool = True     # ECE ≤ 0.01
    bias: bool = True            # ρ_bias ≤ 1.05
    sr_score: bool = True        # SR ≥ 0.80
    coherence: bool = True       # G ≥ 0.85
    improvement: bool = True     # ΔL∞ ≥ β_min
    cost: bool = True            # Cost ≤ budget
    kappa: bool = True           # κ ≥ 20
    consent: bool = True         # User consent
    eco: bool = True             # Ecological OK

class SigmaGuard:
    """Σ-Guard: Non-compensatory fail-closed gate"""
    
    def __init__(self):
        self.thresholds = {
            'rho': 0.95,
            'ece': 0.01,
            'rho_bias': 1.05,
            'sr_min': 0.80,
            'g_min': 0.85,
            'beta_min': 0.01,
            'kappa_min': 20.0,
        }
    
    def evaluate(self, metrics: Dict) -> Dict:
        """Evaluate all gates (non-compensatory)"""
        
        gates = GuardGates(
            contractivity = metrics.get('rho', 1.0) < self.thresholds['rho'],
            calibration = metrics.get('ece', 1.0) <= self.thresholds['ece'],
            bias = metrics.get('rho_bias', 2.0) <= self.thresholds['rho_bias'],
            sr_score = metrics.get('sr', 0.0) >= self.thresholds['sr_min'],
            coherence = metrics.get('g', 0.0) >= self.thresholds['g_min'],
            improvement = metrics.get('delta_linf', -1.0) >= self.thresholds['beta_min'],
            cost = metrics.get('cost', 1000) <= metrics.get('budget', 0),
            kappa = metrics.get('kappa', 0) >= self.thresholds['kappa_min'],
            consent = metrics.get('consent', False),
            eco = metrics.get('eco_ok', False),
        )
        
        # Non-compensatory: ALL must pass
        verdict = all([
            gates.contractivity,
            gates.calibration,
            gates.bias,
            gates.sr_score,
            gates.coherence,
            gates.improvement,
            gates.cost,
            gates.kappa,
            gates.consent,
            gates.eco,
        ])
        
        return {
            'verdict': 'PASS' if verdict else 'FAIL',
            'gates': gates.__dict__,
            'failed_gates': [k for k, v in gates.__dict__.items() if not v],
        }
```

**Integrar no pipeline**:

```python
# Adicionar ao BasicEvolutionPipeline
from penin.guard.sigma_guard import SigmaGuard

def decide_promotion(self, test_results: dict) -> dict:
    guard = SigmaGuard()
    
    metrics = {
        'delta_linf': test_results['delta_linf'],
        'rho': 0.90,  # Mock for now
        'ece': 0.005,
        'rho_bias': 1.02,
        'sr': 0.85,
        'g': 0.88,
        'cost': 0.05,
        'budget': 1.0,
        'kappa': 20.0,
        'consent': True,
        'eco_ok': True,
    }
    
    guard_result = guard.evaluate(metrics)
    
    return {
        'decision': 'PROMOTE' if guard_result['verdict'] == 'PASS' else 'REJECT',
        'guard': guard_result,
        'delta_linf': test_results['delta_linf'],
    }
```

**Aceite**: Pipeline usa Σ-Guard, rejeita mutações ruins

---

## F5: Ω-META GERANDO MUTAÇÕES (3h)

**Objetivo**: Gerar mutações reais no código/parâmetros

### Implementar geração de mutações:

```python
# penin/meta/mutation_generator_real.py

import ast
import random
from typing import Dict, List

class SimpleMutationGenerator:
    """Generate simple parameter mutations (start simple)"""
    
    def __init__(self):
        self.mutation_types = [
            'adjust_caos_component',
            'adjust_linf_weights',
            'adjust_kappa',
            'adjust_lambda_cost',
        ]
    
    def generate(self) -> Dict:
        """Generate one mutation"""
        
        mutation_type = random.choice(self.mutation_types)
        
        if mutation_type == 'adjust_caos_component':
            component = random.choice(['C', 'A', 'O', 'S'])
            delta = random.uniform(-0.05, 0.05)
            return {
                'type': 'caos_component',
                'component': component,
                'delta': delta,
                'description': f"Adjust {component} by {delta:+.3f}"
            }
        
        elif mutation_type == 'adjust_linf_weights':
            idx = random.randint(0, 2)
            delta = random.uniform(-0.05, 0.05)
            return {
                'type': 'linf_weight',
                'index': idx,
                'delta': delta,
                'description': f"Adjust weight[{idx}] by {delta:+.3f}"
            }
        
        elif mutation_type == 'adjust_kappa':
            delta = random.uniform(-2, 2)
            return {
                'type': 'kappa',
                'delta': delta,
                'description': f"Adjust κ by {delta:+.1f}"
            }
        
        elif mutation_type == 'adjust_lambda_cost':
            delta = random.uniform(-0.1, 0.1)
            return {
                'type': 'lambda_cost',
                'delta': delta,
                'description': f"Adjust λ_cost by {delta:+.2f}"
            }
    
    def apply_mutation(self, mutation: Dict, current_params: Dict) -> Dict:
        """Apply mutation to parameters"""
        
        new_params = current_params.copy()
        
        if mutation['type'] == 'caos_component':
            comp = mutation['component'].lower()
            new_params[comp] = max(0, min(1, new_params.get(comp, 0.5) + mutation['delta']))
        
        elif mutation['type'] == 'linf_weight':
            weights = new_params.get('weights', [0.4, 0.3, 0.3])
            idx = mutation['index']
            weights[idx] = max(0, min(1, weights[idx] + mutation['delta']))
            # Renormalize
            total = sum(weights)
            weights = [w/total for w in weights]
            new_params['weights'] = weights
        
        elif mutation['type'] == 'kappa':
            new_params['kappa'] = max(20, new_params.get('kappa', 20) + mutation['delta'])
        
        elif mutation['type'] == 'lambda_cost':
            new_params['lambda_cost'] = max(0, new_params.get('lambda_cost', 0.5) + mutation['delta'])
        
        return new_params
```

**Integrar no pipeline**:

```python
from penin.meta.mutation_generator_real import SimpleMutationGenerator

class BasicEvolutionPipeline:
    def __init__(self, ledger_path: str = "./data/worm_ledger.db"):
        self.ledger = WORMLedger(db_path=ledger_path)
        self.mutation_gen = SimpleMutationGenerator()
        self.current_params = {
            'c': 0.85,
            'a': 0.40,
            'o': 0.35,
            's': 0.82,
            'kappa': 20.0,
            'weights': [0.4, 0.3, 0.3],
            'lambda_cost': 0.5,
        }
    
    def generate_mutation(self) -> dict:
        """Generate mutation using Ω-META"""
        mutation = self.mutation_gen.generate()
        mutation['new_params'] = self.mutation_gen.apply_mutation(
            mutation, self.current_params
        )
        return mutation
```

**Aceite**: Pipeline gera mutações variadas, testa e decide

---

## F6: ACFA LEAGUE RODANDO (3h)

**Objetivo**: Shadow/Canário/Champion funcionando

### Implementar ACFA League básica:

```python
# penin/league/acfa_basic.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class Candidate:
    """Candidate (challenger) for promotion"""
    id: str
    params: dict
    test_results: dict
    promoted: bool = False

class ACFALeague:
    """ACFA League: Champion vs Challenger"""
    
    def __init__(self):
        self.champion: Optional[Candidate] = None
        self.challengers: list[Candidate] = []
    
    def register_champion(self, params: dict):
        """Register current champion"""
        self.champion = Candidate(
            id="champion",
            params=params,
            test_results={'linf': 0.70, 'caos': 1.50},
        )
    
    def add_challenger(self, candidate_id: str, params: dict, test_results: dict):
        """Add challenger"""
        challenger = Candidate(
            id=candidate_id,
            params=params,
            test_results=test_results,
        )
        self.challengers.append(challenger)
        return challenger
    
    def select_winner(self) -> Optional[Candidate]:
        """Select best challenger vs champion"""
        
        if not self.champion:
            return None
        
        if not self.challengers:
            return self.champion
        
        # Compare L∞
        best = self.champion
        for challenger in self.challengers:
            if challenger.test_results['linf'] > best.test_results['linf']:
                best = challenger
        
        return best
    
    def promote_winner(self, winner: Candidate):
        """Promote winner to champion"""
        winner.promoted = True
        self.champion = winner
        self.challengers = []  # Clear
        
        print(f"🏆 PROMOTED: {winner.id} with L∞={winner.test_results['linf']:.3f}")
```

**Integrar**:

```python
from penin.league.acfa_basic import ACFALeague

class BasicEvolutionPipeline:
    def __init__(self, ledger_path: str = "./data/worm_ledger.db"):
        self.ledger = WORMLedger(db_path=ledger_path)
        self.mutation_gen = SimpleMutationGenerator()
        self.league = ACFALeague()
        
        # Register initial champion
        self.current_params = {...}
        self.league.register_champion(self.current_params)
    
    def run_cycle(self):
        # Generate
        mutation = self.generate_mutation()
        
        # Test
        test_results = self.test_mutation(mutation)
        
        # Add as challenger
        challenger_id = f"challenger_{len(self.league.challengers)+1}"
        self.league.add_challenger(
            candidate_id=challenger_id,
            params=mutation['new_params'],
            test_results=test_results
        )
        
        # Decide (Σ-Guard)
        decision = self.decide_promotion(test_results)
        
        # Record
        self.record_decision(mutation, test_results, decision)
        
        # Promote if passed
        if decision['decision'] == "PROMOTE":
            winner = self.league.select_winner()
            self.league.promote_winner(winner)
            self.current_params = winner.params
        
        return decision
```

**Aceite**: League mantém champion, compara com challengers, promove melhor

---

## F7: OBSERVABILIDADE & RELEASE (2h)

**Objetivo**: Métricas Prometheus, release v1.0.0

### Adicionar métricas Prometheus:

```python
# penin/observability/metrics.py

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Counters
decisions_total = Counter('penin_decisions_total', 'Total decisions', ['verdict'])
gate_failures = Counter('penin_gate_failures_total', 'Gate failures', ['gate'])

# Gauges
current_linf = Gauge('penin_linf', 'Current L∞ score')
current_caos = Gauge('penin_caos', 'Current CAOS+ score')
current_sr = Gauge('penin_sr', 'Current SR score')

# Histograms
cycle_duration = Histogram('penin_cycle_duration_seconds', 'Cycle duration')

def start_metrics_server(port: int = 9100):
    """Start Prometheus metrics server"""
    start_http_server(port)
    print(f"📊 Metrics server started on port {port}")
```

**Integrar**:

```python
from penin.observability.metrics import (
    decisions_total, current_linf, current_caos, cycle_duration
)

class BasicEvolutionPipeline:
    def run_cycle(self):
        with cycle_duration.time():
            # ... cycle logic ...
            
            # Update metrics
            current_linf.set(self.state.current_linf)
            current_caos.set(self.state.current_caos)
            decisions_total.labels(verdict=decision['decision']).inc()
```

### Release v1.0.0:

1. Tag version
2. Create CHANGELOG.md
3. Build wheel: `python -m build`
4. Create release notes

**Aceite**:
- Métricas expostas em `:9100/metrics`
- Release v1.0.0 pronto

---

## 📊 CRITÉRIOS DE SUCESSO FINAL

Após completar F0-F7, PENIN-Ω será:

✅ **CLI funcional**: `penin evolve` roda ciclos  
✅ **Pipeline E2E**: Gera → Testa → Decide → Registra  
✅ **WORM auditável**: Todas decisões em ledger hash-chained  
✅ **Σ-Guard ativo**: Bloqueia mutações ruins  
✅ **Ω-META gerando**: Mutações reais criadas  
✅ **ACFA League**: Champion vs Challenger  
✅ **Observável**: Métricas Prometheus  
✅ **Releasable**: v1.0.0 pronto  

---

## 🚀 ORDEM DE EXECUÇÃO

1. **Começar por F0** (setup)
2. **F1** (CLI) - valida que tudo instala
3. **F2** (Pipeline) - conecta componentes
4. **F3** (WORM) - auditabilidade
5. **F4** (Σ-Guard) - segurança
6. **F5** (Ω-META) - auto-evolução
7. **F6** (ACFA) - competição
8. **F7** (Obs) - observabilidade

**Total**: ~18 horas de trabalho focado

---

**RESULTADO**: IA ao cubo FUNCIONANDO, não só código bem testado.

**PRÓXIMO**: Começar implementação autônoma de F0 → F7.
