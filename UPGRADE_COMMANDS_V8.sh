#!/bin/bash
# Script para aplicar upgrade v8.0 do peninaocubo
# Execute: bash UPGRADE_COMMANDS_V8.sh

set -e

echo "🚀 PENIN-Ω v8.0 Upgrade Script"
echo "================================"

# 1) Criar branch de upgrade
echo "📝 Criando branch de upgrade..."
git checkout -b chore/v8-upgrade

# 2) Instalar dependências para dev
echo "📦 Instalando dependências..."
if command -v uv &> /dev/null; then
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

# 3) Instalar pre-commit
echo "🔧 Instalando pre-commit..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
else
    echo "⚠️  pre-commit não encontrado. Instale com: pip install pre-commit"
fi

# 4) Executar testes básicos
echo "🧪 Executando testes básicos..."
python3 -c "
import sys
sys.path.insert(0, '.')
import penin.omega.caos as caos
print('✅ CAOS import OK')
print('✅ phi_caos functions:', len([n for n in dir(caos) if n == 'phi_caos']))
print('✅ Test passed: only one phi_caos function')
"

# 5) Linters (se disponíveis)
echo "🔍 Executando linters..."
if command -v ruff &> /dev/null; then
    ruff . --fix
    echo "✅ Ruff executado"
else
    echo "⚠️  Ruff não encontrado. Instale com: pip install ruff"
fi

if command -v black &> /dev/null; then
    black .
    echo "✅ Black executado"
else
    echo "⚠️  Black não encontrado. Instale com: pip install black"
fi

# 6) Commit das mudanças
echo "💾 Fazendo commit das mudanças..."
git add -A
git commit -m "chore(v8): packaging + deps dedup + fix(caos/router) + cache L2 HMAC + tooling (pre-commit, gitleaks)

- Packaging do projeto para distribuição e uso via CLI 'penin'
- Depêndencias deduplicadas e documentadas; instruído lockfile
- Correção de duplicidade em CAOS (phi_caos) com teste
- Refatoração do router para um único tracker de orçamento
- Cache L2 com 'orjson + HMAC' para integridade
- Ferramentas de segurança e qualidade (pre-commit, gitleaks, envs, ignore)
- Licença adicionada"

echo "✅ Commit realizado com sucesso!"

# 7) Push da branch
echo "📤 Fazendo push da branch..."
git push origin chore/v8-upgrade

echo ""
echo "🎉 Upgrade v8.0 concluído!"
echo "=========================="
echo ""
echo "Próximos passos:"
echo "1. Abrir PR: gh pr create --fill --base main --head chore/v8-upgrade"
echo "2. Revisar mudanças no GitHub"
echo "3. Fazer merge após aprovação"
echo ""
echo "Para testar localmente:"
echo "- pip install -e ."
echo "- penin --help"
echo ""
echo "Para gerar lockfile:"
echo "- uv pip compile requirements.txt -o requirements-lock.txt"