# Modelo de Governança do PENIN-Ω

## Visão Geral

O PENIN-Ω é um projeto de código aberto governado por princípios de **meritocracia ética**, **transparência radical** e **evolução auditável**. Este documento define como as decisões são tomadas, quem pode fazê-las e como novos contribuidores podem se tornar mantenedores.

## Princípios Fundamentais

### 1. **Meritocracia Ética**
O mérito é medido não apenas pela qualidade técnica, mas também pelo **alinhamento com as Leis Originárias (LO-01 a LO-14)**. Contribuições tecnicamente brilhantes que violem princípios éticos são rejeitadas.

### 2. **Transparência Radical**
Todas as decisões significativas são documentadas publicamente através de:
- **GitHub Issues & Discussions**
- **Pull Requests com revisão aberta**
- **WORM Ledger** para decisões críticas de evolução do sistema
- **Changelog detalhado** em cada release

### 3. **Evolução Auditável**
Toda mudança arquitetural passa por:
- **Σ-Guard gates** (validação ética automatizada)
- **Champion-Challenger testing** (ACFA League)
- **Proof-Carrying Artifacts (PCAg)** (provas criptográficas)

## Estrutura de Governança

### Níveis de Participação

```
┌──────────────────────────────────────────────┐
│  Core Team (Mantenedores)                    │
│  - Aprovação final de PRs                    │
│  - Decisões arquiteturais                    │
│  - Gerenciamento de releases                 │
├──────────────────────────────────────────────┤
│  Trusted Contributors                        │
│  - Review de PRs                             │
│  - Mentoria de novos contribuidores          │
│  - Triagem de issues                         │
├──────────────────────────────────────────────┤
│  Contributors                                │
│  - Submissão de PRs                          │
│  - Reporte de issues                         │
│  - Discussões técnicas                       │
├──────────────────────────────────────────────┤
│  Users & Community                           │
│  - Uso do framework                          │
│  - Feedback e sugestões                      │
│  - Participação em discussões                │
└──────────────────────────────────────────────┘
```

### Core Team (Mantenedores Principais)

**Membros Atuais**:
- **Daniel Penin** (@danielgonzagat) - Fundador, Arquiteto Principal

**Responsabilidades**:
- ✅ Aprovação final de Pull Requests críticos
- ✅ Decisões sobre arquitetura e roadmap
- ✅ Gerenciamento de releases e versionamento
- ✅ Garantia de alinhamento com ΣEA/LO-14
- ✅ Resolução de conflitos técnicos ou éticos
- ✅ Aprovação de novos mantenedores

**Poderes**:
- Merge de PRs para `main` e `develop`
- Criação de releases e tags
- Acesso a secrets e configurações sensíveis
- Modificação de workflows CI/CD

**Requisitos**:
- Demonstração consistente de alinhamento ético (LO-14)
- Histórico de contribuições técnicas significativas (6+ meses)
- Capacidade de revisar código com rigor matemático
- Compreensão profunda das 15 equações fundamentais
- Compromisso com disponibilidade para revisões (48h SLA)

### Trusted Contributors

**Como se tornar um Trusted Contributor**:
1. Submeter **5+ PRs de qualidade** aceitos
2. Demonstrar **conhecimento das equações PENIN-Ω**
3. Participar ativamente de **code reviews**
4. Seguir rigorosamente o **Código de Conduta**
5. Passar por validação do Core Team

**Responsabilidades**:
- Revisar PRs de outros contribuidores
- Triagem e rotulação de issues
- Mentoria de novos contribuidores
- Participação em decisões de design (voto consultivo)

**Benefícios**:
- Badge "Trusted Contributor" no perfil
- Acesso a discussões privadas de roadmap
- Reconhecimento no CHANGELOG
- Prioridade em resposta a issues

### Contributors

**Como contribuir**:
1. Leia [CONTRIBUTING.md](CONTRIBUTING.md)
2. Escolha ou crie uma issue
3. Faça fork, desenvolva, teste
4. Submeta PR com descrição detalhada
5. Aguarde review (SLA: 7 dias)

**Requisitos mínimos**:
- Seguir [Code of Conduct](CODE_OF_CONDUCT.md)
- Passar todos os testes automatizados
- Manter cobertura de testes ≥ 80%
- Aderir a style guides (Black, Ruff, Mypy)
- Alinhar com LO-14 (validação via Σ-Guard)

## Processo de Tomada de Decisões

### Decisões Menores (Tactical)
**Exemplos**: Bug fixes, documentação, testes, refatorações

**Processo**: 
1. Criar issue ou PR diretamente
2. Review de 1 Trusted Contributor ou Core Team
3. Merge após aprovação e CI verde

**SLA**: 7 dias

### Decisões Médias (Strategic)
**Exemplos**: Novas features, mudanças de API, integrações SOTA

**Processo**:
1. Criar RFC (Request for Comments) como GitHub Discussion
2. Debate aberto (mínimo 7 dias)
3. Votação: Core Team + Trusted Contributors (maioria simples)
4. Implementação em feature branch
5. Review detalhado + ACFA Champion-Challenger testing
6. Merge após validação Σ-Guard

**SLA**: 14-30 dias

### Decisões Maiores (Architectural)
**Exemplos**: Mudanças em equações fundamentais, redesign de módulos core, remoção de features

**Processo**:
1. Criar ADR (Architecture Decision Record) formal
2. Apresentação técnica detalhada (com matemática)
3. Debate público (mínimo 14 dias)
4. Votação: Core Team (unanimidade ou 2/3 supermajoria)
5. Aprovação ética: Σ-Guard + auditoria externa se necessário
6. Implementação incremental com rollback plan
7. Documentação no WORM Ledger com PCAg

**SLA**: 30-90 dias

### Situações de Emergência
**Exemplos**: Vulnerabilidades críticas, violações éticas, falhas catastróficas

**Processo**:
1. Notificação imediata ao Core Team (via canal privado)
2. Avaliação de impacto (1 hora)
3. Decisão unilateral do Core Team permitida
4. Hotfix implementado e testado
5. Comunicação pública transparente (post-mortem)
6. Review retrospectivo (7 dias após resolução)

**SLA**: Imediato (resposta em 1h, resolução em 24h)

## Promoção de Contribuidores

### Contributor → Trusted Contributor

**Critérios Objetivos** (todos devem ser atendidos):
- ✅ 5+ PRs merged de qualidade
- ✅ 10+ code reviews construtivos
- ✅ 3+ meses de participação ativa
- ✅ Zero violações do Code of Conduct
- ✅ Demonstração de conhecimento de equações core

**Processo**:
1. Auto-indicação ou indicação por Core Team
2. Revisão de histórico de contribuições
3. Votação do Core Team (maioria simples)
4. Anúncio público e atribuição de badge

### Trusted Contributor → Core Team

**Critérios Objetivos** (todos devem ser atendidos):
- ✅ 20+ PRs merged de alta qualidade
- ✅ 50+ code reviews excelentes
- ✅ 6+ meses de participação consistente
- ✅ Contribuição arquitetural significativa
- ✅ Mentoria comprovada de ≥ 3 contribuidores
- ✅ Zero violações éticas (LO-14)
- ✅ Disponibilidade para compromisso de longo prazo

**Processo**:
1. Indicação formal por membro do Core Team
2. Avaliação técnica e ética rigorosa
3. Entrevista com Core Team (alinhamento de valores)
4. Votação do Core Team (unanimidade ou 2/3)
5. Período de transição (1 mês com acesso supervisionado)
6. Promoção completa com anúncio público

**Expectativas**:
- Compromisso de **5-10h/semana**
- Resposta a PRs críticos em **48h**
- Participação em reuniões mensais (se houver)
- Manutenção de módulo específico

## Remoção e Rebaixamento

### Motivos para Remoção
- **Violação grave do Code of Conduct** (banimento imediato)
- **Violação das Leis Originárias (LO-14)** em código ou conduta
- **Inatividade prolongada** (6+ meses sem contribuições ou comunicação)
- **Perda de confiança** da comunidade (após investigação)
- **Conflito de interesse não divulgado** (comercial, político, etc.)

### Processo de Remoção
1. Notificação privada ao indivíduo afetado
2. Oportunidade de resposta (7 dias)
3. Votação do Core Team (2/3 supermajoria)
4. Anúncio público transparente (com razões)
5. Remoção de acessos técnicos
6. Documentação no WORM Ledger

**Apelação**: Possível após 6 meses, requer unanimidade do Core Team

## Resolução de Conflitos

### Conflitos Técnicos
1. Debate aberto em GitHub Discussion
2. Experimentação prática (quando possível)
3. Benchmark e comparação de métricas (L∞, CAOS+, SR)
4. Votação se necessário
5. Documentação da decisão

### Conflitos Éticos
1. Análise via Σ-Guard automatizado
2. Revisão humana por Core Team
3. Consulta a princípios LO-14
4. Decisão final: Core Team (fail-closed)
5. Auditoria externa se discordância interna

### Conflitos Pessoais
1. Mediação privada por membro neutro do Core Team
2. Aplicação do Code of Conduct
3. Escalamento se necessário
4. Documentação confidencial

## Comunicação e Transparência

### Canais Oficiais
- **GitHub Issues**: Bugs, features, tasks
- **GitHub Discussions**: RFCs, design, questões abertas
- **Pull Requests**: Code reviews, implementações
- **CHANGELOG.md**: Histórico de mudanças
- **WORM Ledger**: Decisões críticas e auditorias

### Reuniões (se necessário no futuro)
- **Core Team Sync**: Mensal (privado, ata pública)
- **Community Call**: Trimestral (aberto, gravado)
- **Design Reviews**: Ad-hoc (aberto, documentado)

### Documentação de Decisões
Todas as decisões arquiteturais usam o formato ADR:

```markdown
# ADR-XXXX: [Título]

## Status
[Proposto | Aceito | Rejeitado | Depreciado]

## Contexto
[Por que esta decisão é necessária]

## Decisão
[O que foi decidido]

## Consequências
[Impactos positivos e negativos]

## Alternativas Consideradas
[Outras opções e por que foram rejeitadas]

## Métricas de Sucesso
[Como medir se a decisão foi boa]

## Data
[Data da decisão]

## Aprovadores
[Lista de quem aprovou]
```

## Licenciamento e Propriedade Intelectual

- **Licença**: Apache 2.0 (permissiva)
- **Copyright**: Mantido pelos contribuidores individuais
- **CLA**: Não requerido (confiança na licença Apache 2.0)
- **Patentes**: Proteção via Apache License 2.0 Patent Grant

## Financiamento e Sustentabilidade

**Modelo Atual**: Voluntary contributions (código aberto puro)

**Modelo Futuro (se necessário)**:
- **Sponsorships**: GitHub Sponsors, Open Collective
- **Grants**: Pesquisa acadêmica, fundações de IA ética
- **Consulting**: Implementações enterprise (sem comprometer open source)

**Transparência Financeira**: Todos fundos públicos terão relatórios trimestrais

## Revisão e Evolução deste Documento

Este documento de governança é **vivo e evolutivo**.

**Processo de Mudança**:
1. Proposta formal via GitHub Discussion
2. Debate público (mínimo 14 dias)
3. Votação do Core Team (2/3 supermajoria)
4. Anúncio e implementação
5. Versionamento e changelog

**Revisão Regular**: Anualmente ou quando Core Team >= 3 membros

---

## Contato

- **GitHub**: [@danielgonzagat](https://github.com/danielgonzagat)
- **Issues**: [GitHub Issues](https://github.com/danielgonzagat/peninaocubo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/danielgonzagat/peninaocubo/discussions)
- **Security**: Ver [SECURITY.md](SECURITY.md) para vulnerabilidades

---

**Versão**: 1.0  
**Data de Adoção**: 2025-10-01  
**Próxima Revisão**: 2026-10-01  
**Status**: Ativo

---

🌟 **PENIN-Ω: Governança Ética, Transparente e Evolutiva** 🌟
