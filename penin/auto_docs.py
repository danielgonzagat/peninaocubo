# penin/auto_docs.py
"""
Livro Autoescrito / Docs Vivas
==============================

Gera documentação automática do sistema PENIN-Ω baseada no estado atual,
métricas do WORM, blockchain neural e histórico de evolução.
"""

from pathlib import Path
import datetime
import time
from typing import Dict, Any, List, Optional

try:
    import orjson as json
except ImportError:
    import json


def get_system_metrics() -> Dict[str, Any]:
    """Coleta métricas atuais do sistema"""
    try:
        from penin.omega.swarm import sample_global_state, swarm_health_check
        from penin.omega.neural_chain import get_chain_summary, get_cognitive_history
        from penin.omega.life_eq import quick_life_check
        
        # Métricas do swarm
        swarm_state = sample_global_state()
        swarm_health = swarm_health_check()
        
        # Blockchain neural
        chain_summary = get_chain_summary()
        cognitive_history = get_cognitive_history(5)
        
        # Equação de Vida
        life_verdict = quick_life_check()
        
        return {
            "timestamp": time.time(),
            "swarm": {
                "active_nodes": swarm_state.get("active_nodes", 0),
                "global_G": swarm_state.get("global_state", {}).get("G", 0),
                "health_status": swarm_health.get("overall_status", "unknown")
            },
            "neural_chain": {
                "total_blocks": chain_summary.get("total_blocks", 0),
                "chain_valid": chain_summary.get("validation", {}).get("valid", False),
                "latest_phi": (
                    chain_summary.get("latest_block", {})
                    .get("cognitive_state", {}).get("phi", 0)
                    if chain_summary.get("latest_block") else 0
                )
            },
            "life_equation": {
                "verdict_ok": life_verdict.ok,
                "alpha_eff": life_verdict.alpha_eff,
                "phi": life_verdict.metrics.get("phi", 0),
                "sr": life_verdict.metrics.get("sr", 0),
                "G": life_verdict.metrics.get("G", 0)
            }
        }
    except Exception as e:
        return {"error": str(e), "timestamp": time.time()}


def generate_readme_auto() -> str:
    """Gera README_AUTO.md com estado atual do sistema"""
    
    now = datetime.datetime.utcnow()
    metrics = get_system_metrics()
    
    content = f"""# PENIN-Ω — Docs Autoatualizadas

_Gerado automaticamente em {now.isoformat()}Z_

## Estado Atual do Sistema

### Equação de Vida (+)
- **Status**: {'✅ ATIVO' if metrics.get('life_equation', {}).get('verdict_ok') else '❌ INATIVO'}
- **Alpha Efetivo**: {metrics.get('life_equation', {}).get('alpha_eff', 0):.6f}
- **CAOS⁺ (φ)**: {metrics.get('life_equation', {}).get('phi', 0):.4f}
- **SR-Ω∞**: {metrics.get('life_equation', {}).get('sr', 0):.4f}
- **Coerência Global (G)**: {metrics.get('life_equation', {}).get('G', 0):.4f}

### Swarm Cognitivo
- **Nós Ativos**: {metrics.get('swarm', {}).get('active_nodes', 0)}
- **Coerência Global**: {metrics.get('swarm', {}).get('global_G', 0):.4f}
- **Status de Saúde**: {metrics.get('swarm', {}).get('health_status', 'unknown')}

### Blockchain Neural
- **Total de Blocos**: {metrics.get('neural_chain', {}).get('total_blocks', 0)}
- **Cadeia Válida**: {'✅' if metrics.get('neural_chain', {}).get('chain_valid') else '❌'}
- **Último φ**: {metrics.get('neural_chain', {}).get('latest_phi', 0):.4f}

## Módulos Implementados

### ✅ Núcleo (Lemniscata 8+1)
1. **Equação de Vida (+)** - Gate não-compensatório e orquestrador positivo
2. **DSL Fractal** - Propagação auto-similar de configurações
3. **Swarm Cognitivo** - Gossip protocol e agregação global
4. **CAOS-KRATOS** - Exploração calibrada com saturação
5. **Marketplace Cognitivo** - Ω-tokens para alocação de recursos
6. **Blockchain Neural** - Cadeia leve sobre WORM com HMAC
7. **Σ-Guard** - Verificação ética fail-closed
8. **SR-Ω∞** - Self-Reflection não-compensatório
9. **+1 Ω-ΣEA Total** - Coerência global dos 8 módulos

### 🔄 Em Desenvolvimento
- Metabolização de APIs (I/O recorder/replayer)
- Self-RAG recursivo
- Imunidade Digital
- Checkpoint & Reparo
- GAME + Darwiniano-Auditável
- Zero-Consciousness Proof

## Arquitetura

```
PENIN-Ω (Lemniscata 8+1)
├── Equação de Vida (+) ← Gate não-compensatório
├── DSL Fractal ← Propagação auto-similar
├── Swarm Cognitivo ← Gossip + agregação G
├── CAOS-KRATOS ← Exploração calibrada
├── Marketplace ← Ω-tokens internos
├── Blockchain Neural ← WORM + HMAC
├── Σ-Guard ← Ética fail-closed
├── SR-Ω∞ ← Self-Reflection
└── +1 Ω-ΣEA ← Coerência global
```

## Como Rodar

```bash
# Ambiente
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD

# Teste rápido
python3 -c "from penin.omega.life_eq import quick_life_check; print(quick_life_check().ok)"

# Swarm
python3 -c "from penin.omega.swarm import quick_swarm_test; print(quick_swarm_test())"

# Blockchain
python3 -c "from penin.omega.neural_chain import quick_neural_chain_test; print(quick_neural_chain_test())"
```

## Métricas de Segurança

- **Fail-Closed**: ✅ Implementado em todos os gates
- **Contratividade**: ρ < 1.0 verificado via IR→IC
- **Calibração Ética**: ECE ≤ 0.01, ρ_bias ≤ 1.05
- **Não-Compensatório**: Falha em qualquer gate bloqueia evolução
- **WORM Ledger**: Todas as decisões auditáveis
- **HMAC Integrity**: Blockchain neural protegida contra tampering

## Próximos Passos

1. **Completar módulos restantes** (API metabolizer, Self-RAG, etc.)
2. **Integração completa** dos módulos no ciclo evolutivo
3. **Testes de stress** e validação de performance
4. **Observabilidade** com métricas Prometheus
5. **Deployment** com systemd/docker
6. **Documentação** de operação e troubleshooting

## Histórico de Evolução

### v0.1.0 → Vida+ (Atual)
- ✅ Equação de Vida (+) implementada e testada
- ✅ DSL Fractal com propagação não-compensatória
- ✅ Swarm Cognitivo com SQLite e agregação G
- ✅ CAOS-KRATOS para exploração calibrada
- ✅ Marketplace com Ω-tokens e matching
- ✅ Blockchain Neural com detecção de tampering
- ✅ Todos os gates fail-closed funcionais

### Próxima Release (v0.2.0)
- 🔄 Metabolização de APIs completa
- 🔄 Self-RAG recursivo operacional
- 🔄 Sistema de imunidade digital
- 🔄 Checkpoint/reparo automático
- 🔄 Algoritmos GAME + Darwin auditável
- 🔄 Zero-Consciousness Proof formal

---

_Sistema PENIN-Ω em evolução contínua. Documentação atualizada automaticamente._
"""
    
    return content


def update_readme() -> Dict[str, Any]:
    """Atualiza README_AUTO.md com estado atual"""
    try:
        root = Path(".")
        readme_path = root / "README_AUTO.md"
        
        content = generate_readme_auto()
        readme_path.write_text(content, encoding="utf-8")
        
        return {
            "status": "success",
            "file": str(readme_path),
            "size_bytes": len(content.encode()),
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }


def generate_system_report() -> Dict[str, Any]:
    """Gera relatório completo do sistema"""
    metrics = get_system_metrics()
    
    # Análise de saúde geral
    life_ok = metrics.get("life_equation", {}).get("verdict_ok", False)
    swarm_healthy = metrics.get("swarm", {}).get("health_status") == "excellent"
    chain_valid = metrics.get("neural_chain", {}).get("chain_valid", False)
    
    overall_health = "excellent" if (life_ok and swarm_healthy and chain_valid) else \
                    "good" if (life_ok and chain_valid) else \
                    "fair" if life_ok else "poor"
    
    return {
        "timestamp": time.time(),
        "overall_health": overall_health,
        "components": {
            "life_equation": "healthy" if life_ok else "unhealthy",
            "swarm": metrics.get("swarm", {}).get("health_status", "unknown"),
            "neural_chain": "healthy" if chain_valid else "unhealthy"
        },
        "metrics": metrics,
        "recommendations": _generate_recommendations(metrics)
    }


def _generate_recommendations(metrics: Dict[str, Any]) -> List[str]:
    """Gera recomendações baseadas nas métricas"""
    recommendations = []
    
    life_eq = metrics.get("life_equation", {})
    if not life_eq.get("verdict_ok"):
        recommendations.append("Investigate Life Equation failure - check gates")
    
    if life_eq.get("alpha_eff", 0) < 0.0001:
        recommendations.append("Alpha effective is very low - system may be stagnant")
    
    swarm = metrics.get("swarm", {})
    if swarm.get("active_nodes", 0) < 2:
        recommendations.append("Add more swarm nodes for redundancy")
    
    if swarm.get("global_G", 0) < 0.7:
        recommendations.append("Global coherence is low - check individual node metrics")
    
    chain = metrics.get("neural_chain", {})
    if not chain.get("chain_valid"):
        recommendations.append("Neural chain validation failed - check for tampering")
    
    if chain.get("total_blocks", 0) == 0:
        recommendations.append("No neural blocks recorded - start cognitive snapshots")
    
    return recommendations


if __name__ == "__main__":
    # Atualizar README quando executado diretamente
    result = update_readme()
    print(f"README updated: {result}")
    
    # Gerar relatório
    report = generate_system_report()
    print(f"System health: {report['overall_health']}")
    if report['recommendations']:
        print("Recommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")