# Guia de Configuração dos Provedores de LLM

## Visão Geral

O **Multi-Provider Router** do PENIN-Ω é uma funcionalidade poderosa que permite usar múltiplos provedores de Large Language Models (LLMs) de forma inteligente e econômica. O sistema:

- 🔀 **Roteamento Inteligente**: Seleciona automaticamente o melhor provedor baseado em custo, latência e qualidade
- 💰 **Gestão de Orçamento**: Controla gastos diários com limites soft (95%) e hard (100%)
- 🔄 **Circuit Breaker**: Protege contra provedores instáveis com falhas consecutivas
- 📊 **Analytics Detalhado**: Rastreia custo, latência e taxa de sucesso por provedor
- 🗂️ **Cache L1/L2**: Cache com verificação de integridade HMAC-SHA256
- ⚡ **Paralelização**: Invoca múltiplos provedores em paralelo e seleciona a melhor resposta

## Provedores Suportados

O PENIN-Ω suporta os seguintes provedores de LLM:

| Provedor | Modelos Principais | Variável de Ambiente |
|----------|-------------------|---------------------|
| **OpenAI** | GPT-4o, GPT-4 Turbo, GPT-3.5 | `OPENAI_API_KEY` |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus | `ANTHROPIC_API_KEY` |
| **DeepSeek** | DeepSeek Chat, DeepSeek Coder | `DEEPSEEK_API_KEY` |
| **Mistral AI** | Mistral Large, Mistral Medium | `MISTRAL_API_KEY` |
| **Google Gemini** | Gemini 1.5 Pro, Gemini 1.5 Flash | `GEMINI_API_KEY` |
| **xAI (Grok)** | Grok Beta | `XAI_API_KEY` |

## Configuração de Variáveis de Ambiente

### Passo 1: Criar arquivo `.env`

Crie um arquivo `.env` na raiz do projeto (ou copie o `.env.example`):

```bash
cp .env.example .env
```

### Passo 2: Configurar as Chaves de API

Edite o arquivo `.env` e adicione as chaves dos provedores que deseja usar:

```bash
# Providers
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
MISTRAL_API_KEY=xxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxx
XAI_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxx

# Configurações do PENIN-Ω
PENIN_BUDGET_DAILY_USD=5.0
PENIN_MAX_PARALLEL_PROVIDERS=3
PENIN_METRICS_TOKEN=change-me
PENIN_CACHE_HMAC_KEY=change-me
```

### Passo 3: (Opcional) Configurar Modelos Específicos

Por padrão, o PENIN-Ω usa modelos otimizados para cada provedor. Você pode personalizar:

```bash
# Modelos padrão (opcional - já configurados)
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
DEEPSEEK_MODEL=deepseek-chat
MISTRAL_MODEL=mistral-large-latest
GEMINI_MODEL=gemini-1.5-pro
GROK_MODEL=grok-beta
```

## Obtendo as Chaves de API

### OpenAI

1. Acesse: https://platform.openai.com/api-keys
2. Faça login ou crie uma conta
3. Clique em "Create new secret key"
4. Copie a chave (começa com `sk-proj-` ou `sk-`)
5. Configure billing em: https://platform.openai.com/account/billing

### Anthropic (Claude)

1. Acesse: https://console.anthropic.com/
2. Faça login ou crie uma conta
3. Vá em "API Keys" no menu lateral
4. Clique em "Create Key"
5. Copie a chave (começa com `sk-ant-`)

### DeepSeek

1. Acesse: https://platform.deepseek.com/
2. Faça login ou crie uma conta
3. Vá em "API Keys"
4. Clique em "Create API Key"
5. Copie a chave (começa com `sk-`)

### Mistral AI

1. Acesse: https://console.mistral.ai/
2. Faça login ou crie uma conta
3. Vá em "API Keys"
4. Clique em "Create new key"
5. Copie a chave

### Google Gemini

1. Acesse: https://makersuite.google.com/app/apikey
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Selecione um projeto do Google Cloud (ou crie um novo)
5. Copie a chave

### xAI (Grok)

1. Acesse: https://x.ai/api
2. Faça login ou crie uma conta
3. Solicite acesso à API (pode haver waitlist)
4. Uma vez aprovado, obtenha sua chave na console
5. Copie a chave (começa com `xai-`)

## Uso Básico

### Exemplo 1: Uso Simples com Router

```python
import asyncio
from penin.providers.openai_provider import OpenAIProvider
from penin.providers.anthropic_provider import AnthropicProvider
from penin.router import MultiLLMRouterComplete as MultiLLMRouter

async def main():
    # Inicializar provedores
    providers = [
        OpenAIProvider(),
        AnthropicProvider(),
    ]
    
    # Criar router com orçamento diário de $5
    router = MultiLLMRouter(providers, daily_budget_usd=5.0)
    
    # Fazer uma pergunta
    response = await router.ask(
        messages=[{"role": "user", "content": "O que é IA ao cubo?"}],
        system="Responda de forma concisa e técnica."
    )
    
    # Exibir resultado
    print(f"Provedor: {response.provider}")
    print(f"Modelo: {response.model}")
    print(f"Custo: ${response.cost_usd:.6f}")
    print(f"Tokens: {response.tokens_in + response.tokens_out}")
    print(f"Latência: {response.latency_s:.2f}s")
    print(f"\nResposta:\n{response.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Exemplo 2: Verificar Status do Orçamento

```python
# Obter status do orçamento
budget_status = router.get_budget_status()
print(f"Orçamento diário: ${budget_status['daily_budget_usd']}")
print(f"Gasto hoje: ${budget_status['daily_spend_usd']:.6f}")
print(f"Restante: ${budget_status['budget_remaining_usd']:.6f}")
print(f"Uso: {budget_status['budget_used_pct']:.1f}%")
print(f"Requisições: {budget_status['request_count']}")
```

### Exemplo 3: Analytics por Provedor

```python
# Obter estatísticas detalhadas
stats = router.get_usage_stats()

for provider_id, provider_stats in stats['providers'].items():
    print(f"\n📊 {provider_id.upper()}")
    print(f"  Requisições: {provider_stats['total_requests']}")
    print(f"  Taxa de sucesso: {provider_stats['success_rate']*100:.1f}%")
    print(f"  Custo médio: ${provider_stats['avg_cost_per_request']:.6f}")
    print(f"  Latência média: {provider_stats['avg_latency_s']:.3f}s")
    print(f"  Health: {provider_stats['health']}")
```

### Exemplo 4: Demo Completo

Execute o exemplo de demonstração incluído:

```bash
python examples/demo_router.py
```

## Gestão de Custos e Orçamento

### Configuração de Limites

O router implementa dois níveis de controle:

1. **Soft Cutoff (95%)**: Emite alerta mas continua operando
2. **Hard Cutoff (100%)**: Bloqueia novas requisições até o reset diário

```python
# Configurar orçamento personalizado
router = MultiLLMRouter(
    providers=providers,
    daily_budget_usd=10.0,  # $10 por dia
)

# Resetar orçamento manualmente
router.reset_daily_budget(new_budget=15.0)
```

### Pesos de Seleção

O router pondera três fatores ao selecionar o provedor:

```python
router = MultiLLMRouter(
    providers=providers,
    daily_budget_usd=5.0,
    cost_weight=0.4,      # 40% peso no custo (menor é melhor)
    latency_weight=0.3,   # 30% peso na latência (menor é melhor)
    quality_weight=0.3,   # 30% peso na qualidade (taxa de sucesso)
)
```

### Monitoramento de Gastos

```python
# Histórico de gastos (últimos 30 dias)
budget_status = router.get_budget_status()
for day in budget_status['history']:
    print(f"{day['date']}: ${day['spend_usd']:.4f} ({day['requests']} req)")
```

## Circuit Breaker

O sistema protege contra provedores instáveis:

- **Threshold**: 3 falhas consecutivas → circuit OPEN
- **Recovery**: 60 segundos de timeout
- **Half-Open**: Permite 1 tentativa para verificar recuperação

```python
# Verificar estado dos circuit breakers
stats = router.get_usage_stats()
for provider_id, state in stats['circuit_breakers'].items():
    print(f"{provider_id}: {state}")  # healthy, degraded, unhealthy, circuit_open
```

## Cache L1/L2

O router implementa cache em dois níveis com verificação de integridade:

- **L1 Cache**: Rápido, máximo 1.000 entradas
- **L2 Cache**: Mais lento, máximo 10.000 entradas
- **TTL**: 3.600 segundos (1 hora)
- **Integridade**: HMAC-SHA256

```python
# Habilitar/desabilitar cache
router = MultiLLMRouter(
    providers=providers,
    enable_cache=True,  # Padrão: True
)

# Limpar cache manualmente
router.clear_cache()

# Estatísticas de cache
stats = router.get_usage_stats()
cache_stats = stats['cache']
print(f"Hit rate: {cache_stats['hit_rate']*100:.1f}%")
print(f"L1 size: {cache_stats['l1_size']}")
print(f"L2 size: {cache_stats['l2_size']}")
```

## Modos de Operação

### Production (Padrão)

Modo normal de produção com todas as features ativas:

```python
from penin.router import RouterMode

router = MultiLLMRouter(
    providers=providers,
    mode=RouterMode.PRODUCTION,
)
```

### Dry Run

Testa a lógica do router sem fazer chamadas reais:

```python
router = MultiLLMRouter(
    providers=providers,
    mode=RouterMode.DRY_RUN,
)
```

### Shadow Mode

Executa normalmente mas registra métricas adicionais para análise:

```python
router = MultiLLMRouter(
    providers=providers,
    mode=RouterMode.SHADOW,
)
```

## Troubleshooting

### Erro: "API Key não configurada"

**Sintoma**: `ValueError: OPENAI_API_KEY is not configured`

**Solução**:
1. Verifique se o arquivo `.env` existe na raiz do projeto
2. Confirme que a variável está definida: `OPENAI_API_KEY=sk-...`
3. Reinicie o processo Python após modificar o `.env`

### Erro: "Circuit breaker open"

**Sintoma**: `RuntimeError: Circuit breaker open for provider 'openai'`

**Solução**:
1. O provedor teve 3+ falhas consecutivas
2. Aguarde 60 segundos para recovery automático
3. Verifique sua API key e billing status
4. Verifique status da API do provedor: https://status.openai.com/

### Erro: "Daily budget exceeded"

**Sintoma**: `RuntimeError: Daily budget exceeded (hard cutoff)`

**Solução**:
1. Aumente o orçamento diário: `PENIN_BUDGET_DAILY_USD=10.0`
2. Ou aguarde até meia-noite UTC para reset automático
3. Ou reset manual: `router.reset_daily_budget(new_budget=10.0)`

### Erro de autenticação do provedor

**Sintomas**:
- OpenAI: `401 Unauthorized` ou `Incorrect API key`
- Anthropic: `authentication_error`
- Outros: Similar `401` ou `403`

**Solução**:
1. Verifique se a chave está correta (sem espaços extras)
2. Confirme que a chave não expirou
3. Verifique se tem créditos/billing configurado
4. Teste a chave diretamente no playground do provedor

### Provider não encontrado

**Sintoma**: `ImportError: No module named 'openai'`

**Solução**:
```bash
# Instalar dependências dos provedores
pip install openai anthropic google-generativeai mistralai
```

### Performance lenta

**Sintomas**: Alta latência nas respostas

**Solução**:
1. Reduza número de provedores paralelos:
   ```bash
   PENIN_MAX_PARALLEL_PROVIDERS=2
   ```
2. Habilite cache se desabilitado
3. Considere usar modelos mais rápidos (ex: gpt-4o-mini)

## Configurações Avançadas

### Paralelização Limitada

```bash
# Limitar número de provedores consultados em paralelo
PENIN_MAX_PARALLEL_PROVIDERS=2
```

### Persistência de Estado

O router salva estado automaticamente em:
- `~/.penin_router_complete_state.json`

Inclui:
- Orçamento e histórico
- Estatísticas por provedor
- Estatísticas de cache

### HMAC Cache Secret

Para ambientes de produção, configure uma chave HMAC personalizada:

```bash
PENIN_CACHE_HMAC_KEY=seu-segredo-super-secreto-aqui
```

### Integração com Métricas

O router está pronto para integração com Prometheus:

```python
# Obter métricas completas
analytics = router.get_analytics()

# Exportar para Prometheus (implementar exportador)
# prometheus_metrics.gauge('penin_budget_used_pct', analytics['budget_used_pct'])
# prometheus_metrics.gauge('penin_provider_health', analytics['providers'][pid]['success_rate'])
```

## Boas Práticas

### 1. Sempre Configure Múltiplos Provedores

Use pelo menos 2-3 provedores para garantir alta disponibilidade:

```python
providers = [
    OpenAIProvider(),      # Primário
    AnthropicProvider(),   # Fallback 1
    DeepSeekProvider(),    # Fallback 2 (custo-benefício)
]
```

### 2. Monitore o Orçamento

Configure alertas quando atingir o soft cutoff (95%):

```python
budget = router.get_budget_status()
if budget['soft_cutoff_reached']:
    print("⚠️  ALERTA: Orçamento em 95%!")
```

### 3. Use Cache para Queries Repetidas

Perfeito para cenários com perguntas similares:

```python
# Cache ativo por padrão
response = await router.ask(messages, use_cache=True)
```

### 4. Ajuste Pesos Conforme Necessidade

Para priorizar custo:
```python
router = MultiLLMRouter(
    providers=providers,
    cost_weight=0.6,      # 60% peso no custo
    latency_weight=0.2,   # 20% peso na latência
    quality_weight=0.2,   # 20% peso na qualidade
)
```

Para priorizar velocidade:
```python
router = MultiLLMRouter(
    providers=providers,
    cost_weight=0.1,      # 10% peso no custo
    latency_weight=0.6,   # 60% peso na latência
    quality_weight=0.3,   # 30% peso na qualidade
)
```

### 5. Teste em Dry Run Primeiro

Antes de deployar mudanças:

```python
router = MultiLLMRouter(
    providers=providers,
    mode=RouterMode.DRY_RUN,  # Sem chamadas reais
)
```

## Recursos Adicionais

- **Código do Router**: `penin/router.py` e `penin/router_complete.py`
- **Provedores**: `penin/providers/`
- **Exemplo Completo**: `examples/demo_router.py`
- **Documentação da Arquitetura**: `docs/architecture.md`
- **README Principal**: `README.md`

## Suporte e Comunidade

- **Issues**: https://github.com/danielgonzagat/peninaocubo/issues
- **Discussões**: https://github.com/danielgonzagat/peninaocubo/discussions
- **Contributing**: Veja `CONTRIBUTING.md`

---

**🚀 Pronto!** Agora você está preparado para usar o Multi-Provider Router do PENIN-Ω com total controle sobre custos, performance e confiabilidade.
