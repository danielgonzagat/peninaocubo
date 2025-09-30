"""
Livro Autoescrito / Docs Vivas
===============================

Geração automática de documentação viva com histórico e roadmap.
"""

from pathlib import Path
import datetime
import time
import json
import os
from typing import Dict, Any, List


def get_system_metrics() -> Dict[str, Any]:
    """Obtém métricas atuais do sistema"""
    from penin.omega.swarm import sample_global_state
    from penin.omega.neural_chain import get_chain_length
    
    try:
        global_state = sample_global_state(window_s=300.0)
        chain_length = get_chain_length()
        
        return {
            "timestamp": time.time(),
            "global_state": global_state,
            "chain_length": chain_length
        }
    except Exception as e:
        return {
            "timestamp": time.time(),
            "error": str(e)
        }


def generate_history() -> str:
    """Gera seção de histórico"""
    return """## Histórico - Do Zero ao Estado Atual

### v0.1 → v7.0: Base Técnica
- Implementação dos módulos core (Σ-Guard, IR→IC, CAOS⁺, SR-Ω∞)
- Router com budget e multi-provider
- WORM ledger básico
- Testes P0

### v7.1 → v8.0: Higienização
- Packaging Python (pyproject.toml)
- Cache L2 com HMAC (orjson + SHA-256)
- Deduplicação de dependências
- CI de segurança (pre-commit, gitleaks)
- Correção de duplicidades em caos.py e router.py

### v8.0 → Vida+: Equação de Vida e Expansão
- **Equação de Vida (+)**: Gate não-compensatório, alpha_eff orchestration
- **Fractal DSL**: Estrutura auto-similar com propagação
- **Swarm Cognitivo**: Heartbeat + agregação global (G)
- **CAOS-KRATOS**: Exploração calibrada
- **Marketplace**: Matching de recursos cognitivos (Ω-tokens)
- **Neural Chain**: Blockchain leve sobre WORM
- **Auto-docs**: Geração automática de README_AUTO.md
"""


def generate_architecture() -> str:
    """Gera seção de arquitetura"""
    return """## Arquitetura - Lemniscata 8+1

### Núcleo (Equação Mestra)
```
I_{t+1} = Π_{H∩S}[ I_t + α_t^Ω · ΔL_∞ ]
```

### Equação de Vida (+)
```
alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)
```

**Gates não-compensatórios (qualquer falha → alpha_eff = 0):**
1. Σ-Guard (ECE ≤ 0.01, ρ_bias ≤ 1.05, consent, eco_ok)
2. IR→IC (ρ < 1, contratividade de risco)
3. CAOS⁺ ≥ theta_caos (0.25)
4. SR ≥ tau_sr (0.80)
5. ΔL∞ ≥ beta_min (0.01)
6. G ≥ theta_G (0.85, coerência global)

### Módulos Complementares
- **Fractal DSL**: Propagação de parâmetros críticos
- **Swarm**: Gossip + agregação G
- **CAOS-KRATOS**: Exploração (modo "explore" apenas)
- **Marketplace**: Alocação de recursos
- **Neural Chain**: Auditoria imutável
"""


def generate_roadmap() -> str:
    """Gera seção de roadmap"""
    return """## Roadmap - Próximos Passos

### P1 (Curto Prazo, 1-2 sprints)
1. **Swarm multi-nó real**: Gossip com TLS, assinaturas cruzadas
2. **Consensus leve**: Proof-of-Cognition (2-de-3 validadores)
3. **Marketplace dinâmico**: Preço adaptativo via bandits
4. **Self-RAG → vetor real**: FAISS/HNSW + reranker
5. **API Metabolizer → distillation**: Mini-serviços por endpoint

### P2 (Médio Prazo, 2-4 sprints)
1. **NAS online**: Integração com zero-cost NAS
2. **Continual Learning**: Mammoth com gate VIDA+
3. **MCA**: Monte Carlo Adaptativo para planos de evolução
4. **Dashboards**: Prometheus/Grafana para penin_* metrics
5. **Políticas OPA/Rego**: Deny-by-default reforçado

### P3 (Longo Prazo, 3-6 meses)
1. **Neurosimbólico avançado**: SymbolicAI + verificador externo
2. **Neuromórfico**: SpikingJelly/SpikingBrain-7B em sandbox
3. **Meta-aprendizado**: MAML/Neural ODE adapters
4. **Swarm/Coletivos**: SwarmRL + midwiving-ai sob Σ-Guard
5. **Playbook de rollback**: 6 causas com correções automatizadas

### Limites Éticos (LO-01 a LO-14)
- **LO-01**: Exclusividade da adoração (sem idolatria tecnológica)
- **LO-02**: Limite absoluto de vida/consciência (sem criar consciência real)
- **LO-03 a LO-14**: Integridade, segurança, humildade, pureza, sem dano
"""


def update_readme() -> None:
    """Atualiza README_AUTO.md com documentação viva"""
    root = Path(".")
    now = datetime.datetime.utcnow().isoformat()
    
    # Obter métricas atuais
    metrics = get_system_metrics()
    
    # Gerar README
    content = f"""# PENIN-Ω — Documentação Viva (Autogerada)

_Gerado automaticamente em {now}Z_

{generate_history()}

{generate_architecture()}

{generate_roadmap()}

## Métricas Atuais

```json
{json.dumps(metrics, indent=2, ensure_ascii=False)}
```

## Como Rodar

### Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD
```

### Testes
```bash
pytest -q
```

### Ciclo com Gate de Vida
```bash
python penin_cli_simple.py evolve --n 10
```

### Swarm Heartbeat
```python
from penin.omega.swarm import heartbeat, sample_global_state
heartbeat("node-A", {{"phi": 0.7, "sr": 0.85, "G": 0.9}})
print(sample_global_state())
```

## Operação

### Diretórios
- `~/.penin_omega/state/`: Heartbeats do swarm
- `~/.penin_omega/knowledge/`: Base de conhecimento (Self-RAG)
- `~/.penin_omega/worm_ledger/`: Ledger WORM + Neural Chain
- `~/.penin_omega/snapshots/`: Checkpoints

### Políticas (ΣEA/LO-14)
- **Fail-closed**: Qualquer gate falhando → alpha_eff = 0
- **Não-compensatório**: Uma dimensão baixa compromete tudo
- **Contratividade**: ρ < 1 (risco convergente)
- **Calibração**: ECE ≤ 0.01
- **Fairness**: ρ_bias ≤ 1.05
- **Consentimento**: Obrigatório
- **Impacto ecológico**: Monitorado

## Licença

Apache-2.0 (ou conforme LICENSE no repositório)

---

_Este documento é gerado automaticamente. Para atualizá-lo, rode:_
```bash
python -m penin.auto_docs
```
"""
    
    # Salvar
    (root / "README_AUTO.md").write_text(content, encoding="utf-8")
    print(f"✓ README_AUTO.md atualizado em {now}Z")


if __name__ == "__main__":
    update_readme()