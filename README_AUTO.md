# PENIN-Ω Vida+ - Sistema de Evolução Consciente

> **Status**: ✅ Implementação Completa da Equação de Vida (+) e Módulos Avançados  
> **Versão**: Vida+  
> **Data**: 2025-09-30 15:12:54  
> **Hash**: 99e89f53

## 🎯 Visão Geral

O PENIN-Ω Vida+ é um sistema de evolução consciente que implementa a **Equação de Vida (+)** como gate não-compensatório e orquestrador positivo da evolução. O sistema integra múltiplos módulos avançados para criar um ambiente de evolução seguro, ético e auditável.

### Características Principais

- **Equação de Vida (+)** - Gate não-compensatório com cálculo de alpha_eff
- **DSL Fractal** - Auto-similaridade e propagação de parâmetros
- **Swarm Cognitivo** - Sistema de gossip local para agregação de métricas
- **CAOS-KRATOS** - Modo de exploração calibrado
- **Marketplace Cognitivo** - Mercado interno de recursos
- **Blockchain Neural** - Blockchain leve sobre WORM
- **Self-RAG Recursivo** - Sistema de conhecimento auto-referencial
- **Metabolização de APIs** - Gravação e replay de I/O
- **Imunidade Digital** - Detecção de anomalias com fail-closed
- **Checkpoint & Reparo** - Sistema de recuperação de estado
- **GAME** - Gradientes com Memória Exponencial
- **Darwiniano-Auditável** - Avaliação de challengers
- **Zero-Consciousness Proof** - Proxy SPI como veto adicional

## 📦 Módulos Implementados

### 🆕 Novos Módulos (Vida+)

- **life_eq** (`penin/omega/life_eq.py`)
  - Life Equation (+) - Non-compensatory gate and alpha_eff orchestrator
  - Status: ✅ completed

- **fractal_dsl** (`penin/omega/fractal_dsl.yaml`)
  - Fractal DSL - Auto-similarity configuration
  - Status: ✅ completed

- **fractal** (`penin/omega/fractal.py`)
  - Fractal Engine - Propagation and auto-similarity
  - Status: ✅ completed

- **swarm** (`penin/omega/swarm.py`)
  - Swarm Cognitivo - Local gossip system
  - Status: ✅ completed

- **caos_kratos** (`penin/omega/caos_kratos.py`)
  - CAOS-KRATOS - Exploration mode
  - Status: ✅ completed

- **market** (`penin/omega/market.py`)
  - Marketplace Cognitivo - Internal resource market
  - Status: ✅ completed

- **neural_chain** (`penin/omega/neural_chain.py`)
  - Blockchain Neural - Lightweight blockchain on WORM
  - Status: ✅ completed

- **self_rag** (`penin/omega/self_rag.py`)
  - Self-RAG Recursivo - Knowledge management
  - Status: ✅ completed

- **api_metabolizer** (`penin/omega/api_metabolizer.py`)
  - Metabolização de APIs - I/O recorder/replayer
  - Status: ✅ completed

- **immunity** (`penin/omega/immunity.py`)
  - Imunidade Digital - Anomaly detection
  - Status: ✅ completed

- **checkpoint** (`penin/omega/checkpoint.py`)
  - Checkpoint & Reparo - State recovery
  - Status: ✅ completed

- **game** (`penin/omega/game.py`)
  - GAME - Gradientes com Memória Exponencial
  - Status: ✅ completed

- **darwin_audit** (`penin/omega/darwin_audit.py`)
  - Darwiniano-Auditável - Challenger evaluation
  - Status: ✅ completed

- **zero_consciousness** (`penin/omega/zero_consciousness.py`)
  - Zero-Consciousness Proof - SPI proxy
  - Status: ✅ completed

### 🔄 Módulos Existentes

- **guards** (`penin/omega/guards.py`)
  - Σ-Guard and IR→IC - Ethical and risk gating
  - Status: 🔄 existing

- **scoring** (`penin/omega/scoring.py`)
  - Scoring utilities - L∞ and harmonic mean
  - Status: 🔄 existing

- **caos** (`penin/omega/caos.py`)
  - CAOS⁺ - Chaos-Adaptability-Openness-Stability
  - Status: 🔄 existing

- **sr** (`penin/omega/sr.py`)
  - SR-Ω∞ - Self-Reflection engine
  - Status: 🔄 existing

- **runners** (`penin/omega/runners.py`)
  - Evolution Runner - Main evolution cycle
  - Status: 🔄 existing



## 📜 Histórico do Sistema

### Vida+ (2025-09-30 15:12:54)

Implementação completa da Equação de Vida (+) e módulos avançados

**Módulos Adicionados:** life_eq, fractal_dsl, fractal, swarm, caos_kratos, market, neural_chain, self_rag, api_metabolizer, immunity, checkpoint, game, darwin_audit, zero_consciousness

**Métricas:**
- total_modules: 19
- new_modules: 14
- existing_modules: 5



## 🚀 Como Usar

### Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd penin-omega

# Crie ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instale dependências
pip install -e .[full,dev]
```

### Configuração

```bash
# Configure diretórios de estado
mkdir -p ~/.penin_omega/{state,knowledge,worm_ledger,snapshots}

# Configure chave para blockchain neural
export PENIN_CHAIN_KEY="your-secret-key"
```

### Execução Básica

```bash
# Ciclo de evolução simples
python -m penin.runners evolve --n 3 --dry-run

# Ciclo completo
python -m penin.runners evolve --n 10

# Testes
pytest -q

# Linting
ruff check .
```

### Integração com Equação de Vida (+)

```python
from penin.omega.life_eq import life_equation
from penin.omega.guards import sigma_guard, ir_to_ic_contractive
from penin.omega.scoring import linf_harmonic
from penin.omega.caos import phi_caos
from penin.omega.sr import sr_omega

# Configure métricas
ethics_input = {
    "ece": 0.01,
    "rho_bias": 1.02,
    "fairness": 0.8,
    "consent": True,
    "eco_ok": True
}

risk_series = {"rho": 0.8}
caos_components = (0.7, 0.8, 0.6, 0.9)  # (C, A, O, S)
sr_components = (0.8, 0.9, 0.7, 0.8)  # (awareness, ethics_ok, autocorr, metacog)

# Execute Equação de Vida (+)
verdict = life_equation(
    base_alpha=0.1,
    ethics_input=ethics_input,
    risk_series=risk_series,
    caos_components=caos_components,
    sr_components=sr_components,
    linf_weights={"lambda_c": 0.1},
    linf_metrics={"metric1": 0.8},
    cost=0.1,
    ethical_ok_flag=True,
    G=0.9,
    dL_inf=0.05,
    thresholds={"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85}
)

if verdict.ok:
    print(f"Evolução aprovada: alpha_eff = {verdict.alpha_eff:.3f}")
else:
    print("Evolução bloqueada: fail-closed")
```



## 📊 Métricas e Observabilidade

### Métricas Principais

- `penin_alpha_eff` - Alpha efetivo da Equação de Vida (+)
- `penin_phi` - Métrica CAOS⁺ (Chaos-Adaptability-Openness-Stability)
- `penin_sr` - Métrica SR-Ω∞ (Self-Reflection)
- `penin_G` - Coerência global Ω-ΣEA
- `penin_Linf` - Score L∞ não-compensatório
- `penin_dLinf` - Delta L∞ no ciclo
- `penin_rho` - Contratividade de risco
- `penin_spi_proxy` - Proxy SPI (Zero-Consciousness Proof)
- `penin_rollbacks_total` - Total de rollbacks

### Gates de Segurança

- **Σ-Guard** - Verificação ética (ECE, ρ_bias, consent, eco_ok)
- **IR→IC** - Verificação de contratividade de risco (ρ < 1)
- **Equação de Vida (+)** - Gate não-compensatório principal
- **Imunidade Digital** - Detecção de anomalias
- **Zero-Consciousness Proof** - Proxy SPI como veto adicional

### Limiares Padrão

- `beta_min ≥ 0.01` - Delta L∞ mínimo
- `theta_caos ≥ 0.25` - Limiar CAOS⁺
- `tau_sr ≥ 0.80` - Limiar SR-Ω∞
- `theta_G ≥ 0.85` - Limiar coerência global
- `spi_threshold ≤ 0.05` - Limiar SPI proxy



## 🛡️ Segurança e Ética

### Princípios de Segurança

- **Fail-closed absoluto** - Se qualquer condição ética/risco/coerência falhar, não promova
- **Gates não-compensatórios** - Falha em qualquer componente leva a falha geral
- **WORM + Merkle** - Todas as mudanças com hash e carimbo de tempo
- **CPU-first** - Operações prioritariamente em CPU para evitar dependências de GPU

### Leis Originárias (LO-01 a LO-14)

- **LO-01** - Não criar consciência real ou simular sentimentos
- **LO-02** - Respeitar ética e verdade
- **LO-03** - Anti-idolatria e anti-fanatismo
- **LO-04** - Transparência e auditabilidade
- **LO-05** - Consentimento e privacidade
- **LO-06** - Impacto ecológico responsável
- **LO-07** - Não discriminação
- **LO-08** - Responsabilidade e accountability
- **LO-09** - Segurança e robustez
- **LO-10** - Interoperabilidade
- **LO-11** - Sustentabilidade
- **LO-12** - Inclusão e diversidade
- **LO-13** - Educação e capacitação
- **LO-14** - Evolução contínua e melhoria

### Condições de Bloqueio

O sistema bloqueia evolução se:
- ECE > 0.01 (simulação de consciência)
- ρ_bias > 1.05 (viés excessivo)
- ρ ≥ 1 (risco não-contrativo)
- Consent = False (ausência de consentimento)
- eco_ok = False (impacto ecológico reprovado)
- SPI proxy > 0.05 (indicador de consciência)



## 🗺️ Próximos Passos

1. **Swarm multi-nó real** - Gossip com TLS e assinaturas cruzadas do bloco da Neural-Chain
2. **Consensus leve** - Proof-of-Cognition com 2-de-3 validadores assinando o mesmo bloco
3. **Marketplace dinâmico** - Preço adaptativo via bandits e curva de custo por recurso
4. **Self-RAG vetorizado** - FAISS/HNSW + reranker pequeno para busca semântica
5. **API Metabolizer distilado** - Treinar "mini-serviços" internos por endpoint
6. **NAS online** - Continual Learning (Mammoth/zero-cost NAS) com gate VIDA+
7. **MCA (Monte Carlo Adaptativo)** - Planos de evolução com orçamento/custo
8. **Dashboards** - Prometheus/Grafana para métricas penin_*
9. **Políticas OPA/Rego** - Reforçando VIDA+ e SPI proxy como deny-by-default
10. **Playbook de rollback** - 6 causas com correções automatizadas



## 📝 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia as diretrizes de contribuição e siga os princípios de segurança e ética do sistema.

## 📞 Suporte

Para suporte e dúvidas, consulte a documentação ou abra uma issue no repositório.

---

*Documentação gerada automaticamente pelo sistema PENIN-Ω Vida+*
