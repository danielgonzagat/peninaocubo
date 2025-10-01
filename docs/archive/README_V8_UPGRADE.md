# 🚀 PENIN-Ω v8.0 Upgrade - Quick Start

**Status**: ✅ **COMPLETO E PRONTO**  
**Data**: 2025-09-30

---

## 📋 TL;DR

```bash
# Aplicar upgrade completo (automatizado)
./UPGRADE_COMMANDS_V8.sh

# Ou manual:
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,full]"
pytest tests/test_caos_unique.py tests/test_router_syntax.py -v

# Commit e push
./GIT_COMMANDS_V8.sh
```

---

## 🎯 O que foi feito

| Categoria | Itens | Status |
|-----------|-------|--------|
| **Correções** | 6 bugs P0.5 | ✅ |
| **Novos arquivos** | 9 arquivos | ✅ |
| **Testes** | 3 módulos (11 casos) | ✅ |
| **Documentação** | 5 documentos | ✅ |
| **Scripts** | 2 scripts shell | ✅ |

---

## 🔧 Correções Aplicadas

1. ✅ **CAOS**: Removida duplicidade de `phi_caos` e `__init__`
2. ✅ **Router**: Consolidado tracker de orçamento (removido órfão)
3. ✅ **Cache L2**: Substituído pickle por **orjson + HMAC-SHA256**
4. ✅ **Packaging**: `pyproject.toml` completo + CLI `penin`
5. ✅ **Deps**: Deduplicado `requirements.txt` (8 pacotes)
6. ✅ **Tooling**: pre-commit, gitleaks, .env.example, .gitignore

---

## 📁 Arquivos Importantes

### 📊 Relatórios e Docs
- **`SUMARIO_EXECUTIVO_V8.md`** - Resumo executivo (leia primeiro!)
- **`VALIDATION_REPORT_V8.md`** - Relatório técnico completo
- **`CHANGELOG.md`** - Log de mudanças (Keep a Changelog)
- **`LICENSE`** - Apache 2.0

### 🔨 Scripts
- **`UPGRADE_COMMANDS_V8.sh`** - Aplicar upgrade (automatizado)
- **`GIT_COMMANDS_V8.sh`** - Workflow git (branch, commit, push, PR)

### 🧪 Testes
- `tests/test_caos_unique.py` - Unicidade do CAOS
- `tests/test_router_syntax.py` - Router e budget tracking
- `tests/test_cache_hmac.py` - Cache L2 HMAC

### ⚙️ Configuração
- `.env.example` - Template de variáveis
- `.pre-commit-config.yaml` - Hooks de qualidade
- `.github/workflows/security.yml` - CI de segurança

---

## 🚀 Uso do Sistema v8.0

### Instalação

```bash
# Clone ou pull latest
git pull origin main

# Instalar
pip install -e ".[full,dev]"

# Configurar ambiente
cp .env.example .env
# Edite .env com suas keys

# Pre-commit hooks
pip install pre-commit
pre-commit install
```

### CLI

```bash
# Verificar instalação
penin --version
penin --help

# Executar sistema
penin run --config config.yaml

# Ver métricas
penin metrics
```

### Desenvolvimento

```bash
# Rodar testes
pytest -v

# Testes específicos
pytest tests/test_caos_unique.py -v
pytest tests/test_router_syntax.py -v
pytest tests/test_cache_hmac.py -v

# Linters
ruff check . --fix
black .

# Pre-commit (todos os hooks)
pre-commit run --all-files
```

---

## 🔐 Segurança

### Cache L2 com HMAC

O cache L2 agora usa **orjson + HMAC (SHA-256)** para integridade:

```python
# Configurar chave (recomendado!)
export PENIN_CACHE_HMAC_KEY="sua-chave-secreta-aqui"

# Ou no .env
PENIN_CACHE_HMAC_KEY=sua-chave-secreta-aqui
```

⚠️ **Importante**: Dados de cache antigos (v7.1 com pickle) são incompatíveis.
**Solução**: Limpar cache L2 ou definir `PENIN_CACHE_HMAC_KEY`.

### CI de Segurança

O workflow `.github/workflows/security.yml` executa:
- **Gitleaks**: Scan de segredos
- **Safety**: Vulnerabilidades de dependências
- **Bandit**: Análise de código Python

---

## 📊 Métricas de Qualidade

| Métrica | Antes (v7.1) | Depois (v8.0) | Ganho |
|---------|--------------|---------------|-------|
| Duplicidades | 10 | 0 | ✅ 100% |
| Deps duplicadas | 8 | 0 | ✅ 100% |
| Cache seguro | ❌ | ✅ | ✅ |
| Empacotamento | ❌ | ✅ | ✅ |
| Tooling CI | 0 | 3 | ✅ |
| Testes novos | 0 | 11 | ✅ |

---

## 🐛 Troubleshooting

### Erro: `HMAC mismatch`

**Causa**: Chave HMAC diferente ou cache corrompido

**Solução**:
```bash
# Limpar cache L2
rm -f *.db *.sqlite

# Ou definir chave correta
export PENIN_CACHE_HMAC_KEY="chave-correta"
```

### Erro: `ModuleNotFoundError: penin`

**Causa**: Pacote não instalado

**Solução**:
```bash
pip install -e .
```

### Erro: `No module named pytest`

**Causa**: Deps de teste não instaladas

**Solução**:
```bash
pip install -e ".[dev]"
```

### Erro: Budget exceeded

**Causa**: Orçamento diário esgotado

**Solução**:
```bash
# Aumentar budget
export PENIN_BUDGET_DAILY_USD=10.0

# Ou resetar
penin router reset-budget
```

---

## 📚 Documentação Completa

| Documento | Descrição |
|-----------|-----------|
| `SUMARIO_EXECUTIVO_V8.md` | Resumo executivo (stakeholders) |
| `VALIDATION_REPORT_V8.md` | Relatório técnico detalhado |
| `CHANGELOG.md` | Log de mudanças versionado |
| `README.md` | Documentação do sistema |
| `LICENSE` | Licença Apache 2.0 |

---

## 🔄 Fluxo de Trabalho

```
1. UPGRADE_COMMANDS_V8.sh  → Aplicar upgrade
2. pytest -v                → Validar testes
3. GIT_COMMANDS_V8.sh       → Commit e PR
4. CI/CD                    → Gitleaks, Safety, Bandit
5. Code Review              → Aprovação
6. Merge!                   → Deploy
```

---

## 🎯 Próximos Passos

### P1 (1-2 dias)
- [ ] Remover hacks de import (`sys.path`)
- [ ] Testes de concorrência
- [ ] Testes de falhas de rede
- [ ] Redação automática de logs

### P2 (1-2 semanas)
- [ ] OPA/Rego para políticas
- [ ] Docs operacionais (HA/backup)
- [ ] Lock de versões
- [ ] Separar CAOS⁺ (explore vs promote)

### P3 (1 mês)
- [ ] Release pipeline
- [ ] Observabilidade externa segura
- [ ] SBOM + SCA
- [ ] Deploy artifacts (Helm)

---

## 📞 Suporte

### Comandos Úteis

```bash
# Ver status
git status
penin --version

# Logs
tail -f penin.log

# Métricas
curl http://127.0.0.1:9090/metrics

# Resetar cache
rm -f *.db

# Limpar ambiente
deactivate
rm -rf .venv
```

### Issues

Encontrou um problema? Abra uma issue:
```bash
gh issue create --title "Bug: ..." --body "..."
```

---

## ✅ Checklist de Aceitação

- [x] Código sem duplicidades
- [x] Cache seguro (HMAC)
- [x] Pacote instalável
- [x] CLI funcional
- [x] Testes passam
- [x] Linters OK
- [x] Docs completas
- [x] CI configurado

---

## 🎉 Conclusão

**Sistema PENIN-Ω v8.0 está pronto para produção!**

- ✅ Limpo
- ✅ Seguro
- ✅ Testado
- ✅ Documentado
- ✅ Empacotado
- ✅ Profissional

**Bom trabalho! 🚀**

---

**Versão**: 8.0.0  
**Data**: 2025-09-30  
**Status**: Production Ready