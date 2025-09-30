"""
Livro Autoescrito / Docs Vivas
==============================

Gerador automático de documentação baseado no estado atual do sistema.
"""

from pathlib import Path
import datetime
import orjson
from typing import Dict, Any


def update_readme() -> None:
    """Atualiza README com estado atual do sistema"""
    root = Path(".")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Coletar métricas do sistema
    try:
        from penin.omega.swarm import sample_global_state
        swarm_state = sample_global_state()
    except:
        swarm_state = {"error": "swarm not available"}
    
    try:
        from penin.omega.neural_chain import get_chain_head, verify_chain
        chain_head = get_chain_head()
        chain_valid = verify_chain()
    except:
        chain_head = None
        chain_valid = False
    
    # Gerar conteúdo
    content = f"""# PENIN-Ω — Docs Autoatualizadas

_Gerado automaticamente em {now}Z_

## Estado Atual do Sistema

### Swarm Cognitivo
```json
{orjson.dumps(swarm_state, option=orjson.OPT_INDENT_2).decode()}
```

### Blockchain Neural
- Último bloco: {chain_head['hash'][:16] if chain_head else 'N/A'}
- Cadeia válida: {chain_valid}
- Timestamp: {datetime.datetime.fromtimestamp(chain_head['ts']).isoformat() if chain_head else 'N/A'}

### Módulos Implementados
- ✅ Equação de Vida (+) - Gate não-compensatório
- ✅ DSL Fractal - Propagação auto-similar
- ✅ Swarm Cognitivo - Gossip local + agregação G
- ✅ CAOS-KRATOS - Exploração calibrada
- ✅ Marketplace Cognitivo - Ω-tokens internos
- ✅ Blockchain Neural - Encadeamento HMAC
- ✅ Auto-docs - Documentação viva

### Próximos Passos
- Self-RAG recursivo
- Metabolização de APIs
- Imunidade Digital
- Checkpoint & Reparo
- GAME + Darwiniano-Auditável
- Zero-Consciousness Proof

## Como Usar

```bash
# Instalar dependências
pip install -e ".[full,dev]"

# Executar testes
python3 -m pytest tests/ -v

# Gerar docs
python -m penin.auto_docs
```

## Arquitetura

O sistema PENIN-Ω implementa a Lemniscata 8+1 com os seguintes componentes:

1. **Equação de Vida (+)**: Gate não-compensatório que determina α_eff
2. **DSL Fractal**: Propagação hierárquica de parâmetros
3. **Swarm Cognitivo**: Consenso distribuído via gossip
4. **CAOS-KRATOS**: Exploração adaptativa calibrada
5. **Marketplace**: Alocação de recursos cognitivos
6. **Blockchain Neural**: Auditoria com HMAC
7. **Auto-docs**: Documentação autogerada
8. **+1 Ω-ΣEA**: Coerência global fail-closed

Todos os componentes seguem o princípio fail-closed e são auditáveis via WORM.
"""
    
    # Salvar README
    readme_path = root / "README_AUTO.md"
    readme_path.write_text(content, encoding="utf-8")
    
    print(f"📚 README_AUTO.md atualizado em {now}")


if __name__ == "__main__":
    update_readme()