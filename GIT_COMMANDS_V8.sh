#!/bin/bash
# Git Commands para Upgrade v8.0
# Execute linha por linha ou rode o script completo

set -e

echo "========================================="
echo "Git Workflow - PENIN-Ω v8.0"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar se estamos em um repositório git
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Não é um repositório git${NC}"
    echo "Execute: git init && git remote add origin <URL>"
    exit 1
fi

echo -e "${BLUE}1. Verificando status atual...${NC}"
git status --short
echo ""

echo -e "${YELLOW}Deseja continuar? (y/n)${NC}"
read -r CONTINUE
if [ "$CONTINUE" != "y" ]; then
    echo "Abortado pelo usuário"
    exit 0
fi

echo -e "${BLUE}2. Criando branch de upgrade...${NC}"
BRANCH_NAME="chore/v8-upgrade"
git checkout -b "$BRANCH_NAME" 2>/dev/null || git checkout "$BRANCH_NAME"
echo -e "${GREEN}✅ Branch: $BRANCH_NAME${NC}"
echo ""

echo -e "${BLUE}3. Adicionando arquivos modificados...${NC}"
git add pyproject.toml
git add requirements.txt
git add penin/omega/caos.py
git add penin/router.py
git add 1_de_8
echo -e "${GREEN}✅ Arquivos core adicionados${NC}"
echo ""

echo -e "${BLUE}4. Adicionando novos arquivos...${NC}"
git add .env.example
git add .gitignore
git add .pre-commit-config.yaml
git add .github/workflows/security.yml
git add LICENSE
git add CHANGELOG.md
git add tests/test_caos_unique.py
git add tests/test_router_syntax.py
git add tests/test_cache_hmac.py
echo -e "${GREEN}✅ Novos arquivos adicionados${NC}"
echo ""

echo -e "${BLUE}5. Adicionando documentação...${NC}"
git add VALIDATION_REPORT_V8.md
git add SUMARIO_EXECUTIVO_V8.md
git add UPGRADE_COMMANDS_V8.sh
git add COMMIT_MESSAGE_V8.txt
git add GIT_COMMANDS_V8.sh
echo -e "${GREEN}✅ Documentação adicionada${NC}"
echo ""

echo -e "${BLUE}6. Verificando staged files...${NC}"
git status --short
echo ""

echo -e "${BLUE}7. Criando commit...${NC}"
if [ -f "COMMIT_MESSAGE_V8.txt" ]; then
    git commit -F COMMIT_MESSAGE_V8.txt
    echo -e "${GREEN}✅ Commit criado com mensagem estruturada${NC}"
else
    git commit -m "chore(v8): packaging + deps dedup + fix(caos/router) + cache L2 HMAC + tooling

BREAKING CHANGE: Cache L2 agora usa orjson+HMAC

- Adiciona pyproject.toml completo com CLI 'penin'
- Deduplica requirements.txt (remove 8 duplicados)
- Remove definições duplicadas em caos.py e router.py
- Substitui pickle por orjson+HMAC no cache L2
- Adiciona tooling: pre-commit, gitleaks, .env.example
- Adiciona LICENSE (Apache 2.0) e CHANGELOG.md
- Adiciona 3 módulos de teste (11 casos)

Refs: P0.5 audit, v7.1→v8.0 upgrade"
    echo -e "${GREEN}✅ Commit criado${NC}"
fi
echo ""

echo -e "${BLUE}8. Mostrando último commit...${NC}"
git log -1 --stat
echo ""

echo -e "${YELLOW}Deseja fazer push? (y/n)${NC}"
read -r DO_PUSH
if [ "$DO_PUSH" = "y" ]; then
    echo -e "${BLUE}9. Fazendo push para origin...${NC}"
    git push origin "$BRANCH_NAME" || git push --set-upstream origin "$BRANCH_NAME"
    echo -e "${GREEN}✅ Push realizado${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  Push pulado - execute manualmente:${NC}"
    echo "   git push origin $BRANCH_NAME"
    echo ""
fi

# Verificar se gh CLI está disponível
if command -v gh &> /dev/null; then
    echo -e "${YELLOW}Deseja criar PR automaticamente com gh CLI? (y/n)${NC}"
    read -r DO_PR
    if [ "$DO_PR" = "y" ]; then
        echo -e "${BLUE}10. Criando Pull Request...${NC}"
        
        # Criar PR com título e corpo estruturado
        gh pr create \
            --title "chore(v8): Upgrade estruturante (packaging, deps, security)" \
            --body "## Contexto
Este PR promove o peninaocubo para v8.0 com foco em empacotamento, segurança de cache, higiene de deps e correção de duplicidades.

## Mudanças Principais
- **Packaging**: pyproject.toml completo + CLI \`penin\`
- **Deps**: requirements.txt deduplicado (8 pacotes)
- **CAOS**: remove \`phi_caos\` duplicado + teste
- **Router**: consolida tracker de orçamento + teste
- **Cache L2**: orjson+HMAC no lugar de pickle + teste
- **Tooling**: pre-commit, gitleaks, .env.example, .gitignore
- **Docs**: LICENSE (Apache 2.0) + CHANGELOG.md

## Testes
\`\`\`bash
pip install -e \".[dev,full]\"
pytest tests/test_caos_unique.py -v
pytest tests/test_router_syntax.py -v
pytest tests/test_cache_hmac.py -v
ruff check . --fix
black .
\`\`\`

## Riscos
- **Cache L2**: HMAC mismatch em dados antigos → limpar L2 ou setar \`PENIN_CACHE_HMAC_KEY\`
- **Router**: possível regressão → testes cobrem cenários principais

## Rollback
\`\`\`bash
git revert HEAD
\`\`\`

## Checklist
- [x] Testes passam
- [x] Linters OK
- [x] Documentação completa
- [x] Breaking changes documentados

## Docs
- \`VALIDATION_REPORT_V8.md\` - relatório técnico
- \`SUMARIO_EXECUTIVO_V8.md\` - resumo executivo
- \`CHANGELOG.md\` - log de mudanças

Refs: #upgrade-v8 #p0.5 #security" \
            --base main \
            --head "$BRANCH_NAME" \
            --label "type:chore" \
            --label "security" \
            --label "ready-for-review"
        
        echo -e "${GREEN}✅ Pull Request criado${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠️  gh CLI não instalado - crie PR manualmente:${NC}"
    echo "   https://github.com/<owner>/<repo>/compare/$BRANCH_NAME"
    echo ""
fi

echo "========================================="
echo -e "${GREEN}✅ Workflow Git Completo!${NC}"
echo "========================================="
echo ""
echo "Resumo:"
echo "  Branch: $BRANCH_NAME"
echo "  Commit: $(git rev-parse --short HEAD)"
echo "  Files: $(git diff --name-only HEAD~1 HEAD | wc -l) modificados"
echo ""
echo "Próximos passos:"
if [ "$DO_PUSH" != "y" ]; then
    echo "  1. git push origin $BRANCH_NAME"
fi
if [ "$DO_PR" != "y" ] || [ -z "$(command -v gh)" ]; then
    echo "  2. Abrir PR no GitHub"
fi
echo "  3. Aguardar CI/CD (gitleaks, safety, bandit)"
echo "  4. Code review"
echo "  5. Merge!"
echo ""
echo "Comandos úteis:"
echo "  • git log --oneline -5               # Ver últimos commits"
echo "  • git diff HEAD~1                    # Ver mudanças"
echo "  • git show HEAD --stat               # Ver resumo do commit"
echo "  • gh pr view                         # Ver PR (se criado)"
echo ""