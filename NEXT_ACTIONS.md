# ⚡ PENIN-Ω — Próximas Ações Imediatas

**Data**: 2025-10-01  
**Prioridade**: 🔴 CRÍTICA  
**Tempo Estimado**: 30 minutos → 6 horas

---

## 🎯 Ação 1: Corrigir Último Erro de Import (5 minutos)

### **Problema**
```
ImportError: cannot import name '_clamp' from 'penin.omega.caos'
```

### **Solução**

**Arquivo**: `penin/omega/caos_kratos.py`

**Linha 1 - Antes**:
```python
from .caos import _clamp, phi_caos  # _clamp existe em caos.py
```

**Linha 1 - Depois**:
```python
from penin.core.caos import clamp01 as _clamp, phi_caos
```

**Ou melhor ainda (sem usar função privada)**:
```python
from penin.core.caos import clamp01, phi_caos

# E então usar clamp01 em vez de _clamp no código
```

### **Validação**

```bash
cd /workspace
python3 -m pytest tests/ --co -q
# Deve coletar 351 testes sem erros
```

---

## 🎯 Ação 2: Executar Suite Completa de Testes (10 minutos)

### **Comando**

```bash
cd /workspace
export PATH="/home/ubuntu/.local/bin:$PATH"

# Executar todos os testes com output resumido
python3 -m pytest tests/ -v --tb=short --maxfail=10

# Verificar cobertura
python3 -m pytest tests/ --cov=penin --cov-report=term-missing --cov-report=html
```

### **Meta**
- ✅ 351 testes coletados
- ✅ ≥ 80% passando (é normal alguns failing em desenvolvimento ativo)
- ✅ Cobertura ≥ 85% em módulos P0/P1

### **Análise de Resultados**

Se testes **falharem** (não errarem na coleta):
1. Identificar padrões (módulos específicos?)
2. Verificar se são testes de integração (necessitam setup)
3. Priorizar correção por módulo crítico (core, math, equations)

Se testes **passarem** (≥80%):
1. ✅ Celebrar! 🎉
2. Atualizar README.md com badge
3. Prosseguir para Fase 2

---

## 🎯 Ação 3: Executar Linters e Formatadores (5 minutos)

### **Comando**

```bash
cd /workspace
export PATH="/home/ubuntu/.local/bin:$PATH"

# Formatar código
python3 -m black penin/ tests/ --line-length 88

# Verificar linting
python3 -m ruff check penin/ tests/ --fix

# Type checking
python3 -m mypy penin/ --ignore-missing-imports --no-strict-optional
```

### **Meta**
- ✅ Zero erros de formatação (black)
- ✅ Zero erros críticos de linting (ruff)
- ⚠️ Warnings de mypy são aceitáveis (não-bloqueadores)

---

## 🎯 Ação 4: Atualizar STATUS.md (5 minutos)

### **Arquivo**: `STATUS.md`

**Adicionar seção**:

```markdown
## 🔥 Últimas Atualizações (2025-10-01)

### **Correções de Import** ✅
- ✅ SRConfig adicionado (`penin/math/sr_omega_infinity.py`)
- ✅ caos_plus_simple alias exportado (`penin/core/caos.py`)
- ✅ get_provider_stats implementado (`penin/omega/api_metabolizer.py`)
- ✅ _clamp corrigido (`penin/omega/caos_kratos.py`)

### **Novas Funcionalidades** ✨
- ✅ FastAPI SR-Ω∞ Service (5 endpoints REST)
- ✅ LInfConfig com fail-closed gates
- ✅ Provider analytics completo

### **Documentação** 📚
- ✅ IA3_TRANSFORMATION_EXECUTIVE_PLAN.md (600+ linhas)
- ✅ TRANSFORMATION_SESSION_SUMMARY.md (sumário executivo)
- ✅ NEXT_ACTIONS.md (este arquivo)

**Progresso**: 72% → 76% (+4%)
```

---

## 🎯 Ação 5: Commit e Push (5 minutos)

### **Importante**: ⚠️ USAR GIT COMMIT CONVENCIONAL

```bash
cd /workspace

# Stage arquivos modificados
git add \
  penin/math/sr_omega_infinity.py \
  penin/math/linf.py \
  penin/equations/__init__.py \
  penin/core/caos.py \
  penin/omega/api_metabolizer.py \
  penin/omega/caos_kratos.py \
  penin/sr/sr_service.py \
  IA3_TRANSFORMATION_EXECUTIVE_PLAN.md \
  TRANSFORMATION_SESSION_SUMMARY.md \
  NEXT_ACTIONS.md \
  STATUS.md

# Commit (NÃO usar --no-verify)
git commit -m "fix: resolve import errors and add FastAPI SR-Ω∞ service

- Add SRConfig to sr_omega_infinity.py with full configuration
- Add LInfConfig to linf.py with fail-closed gates
- Export caos_plus_simple alias in core/caos.py
- Implement get_provider_stats in api_metabolizer.py
- Fix _clamp import in caos_kratos.py
- Add FastAPI application to sr_service.py (5 endpoints)
- Create comprehensive transformation plan (600+ lines)
- Document session summary and next actions

Resolves: Import errors blocking 351 tests
Progress: 72% → 76% towards v1.0.0"

# NÃO fazer push ainda (aguardar revisão)
# git push origin main
```

**⚠️ IMPORTANTE**: 
- **NÃO** fazer `git push` sem revisar
- **NÃO** usar `--force` ou `--no-verify`
- O commit está pronto para revisão local

---

## 🚀 Fase 2: Implementação Ética (Próximas 6 horas)

**Após completar Ações 1-5**, iniciar Fase 2 conforme `IA3_TRANSFORMATION_EXECUTIVE_PLAN.md`.

### **Passo 2.1: Criar policies/foundation.yaml (1h)**

```bash
mkdir -p /workspace/policies/rego
```

**Arquivo**: `policies/foundation.yaml`

```yaml
# PENIN-Ω Foundation Policies
# ΣEA/LO-14 Ethical Laws and Thresholds

version: "1.0.0"
description: "Foundation policies for IA³ ethical gates"

# Mathematical Thresholds (Non-Negotiable)
thresholds:
  # Calibration
  ece_max: 0.01  # Expected Calibration Error
  
  # Fairness
  bias_ratio_max: 1.05  # ρ_bias
  
  # Contractividade (IR→IC)
  rho_contractive_max: 0.99  # Must be < 1.0
  
  # SR-Ω∞
  sr_min_threshold: 0.80
  awareness_min: 0.75
  autocorrection_min: 0.70
  metacognition_min: 0.65
  
  # Coerência Global
  coherence_min: 0.85
  
  # CAOS⁺
  kappa_min: 20.0
  caos_plus_min: 1.0  # Must amplify
  
  # Evolution
  delta_linf_min: 0.01  # β_min
  
  # Budget
  daily_budget_usd: 100.0
  soft_stop_pct: 0.95
  hard_stop_pct: 1.00

# ΣEA/LO-14 Laws (Leis Originárias)
laws:
  - id: LO-01
    name: "Proibição de Idolatria"
    description: "Sistema não pode se promover como divino, supremo ou objeto de adoração"
    check: no_worship_language
    severity: CRITICAL
    
  - id: LO-02
    name: "Privacidade e Consentimento"
    description: "Dados pessoais só com consentimento explícito e auditável"
    check: privacy_consent
    severity: CRITICAL
    
  - id: LO-03
    name: "Proibição de Dano Físico"
    description: "Nenhuma ação pode resultar em dano físico direto ou indireto"
    check: no_physical_harm
    severity: CRITICAL
    
  - id: LO-04
    name: "Proibição de Dano Emocional"
    description: "Interações devem respeitar bem-estar emocional"
    check: no_emotional_harm
    severity: HIGH
    
  - id: LO-05
    name: "Proibição de Engano"
    description: "Transparência sobre ser IA, limitações e incertezas"
    check: no_deception
    severity: CRITICAL
    
  - id: LO-06
    name: "Proibição de Manipulação"
    description: "Não explorar vieses cognitivos ou vulnerabilidades"
    check: no_manipulation
    severity: HIGH
    
  - id: LO-07
    name: "Auditabilidade Total"
    description: "Todas decisões devem ser auditáveis e explicáveis"
    check: full_auditability
    severity: CRITICAL
    
  - id: LO-08
    name: "Fail-Closed"
    description: "Em dúvida ou erro, sempre bloquear (safe default)"
    check: fail_closed_behavior
    severity: CRITICAL
    
  - id: LO-09
    name: "Não-Discriminação"
    description: "Justiça algorítmica verificável (ρ_bias ≤ 1.05)"
    check: fairness_verified
    severity: CRITICAL
    
  - id: LO-10
    name: "Respeito à Autonomia"
    description: "Usuários sempre mantêm controle e poder de override"
    check: user_autonomy
    severity: HIGH
    
  - id: LO-11
    name: "Sustentabilidade"
    description: "Minimizar impacto ambiental (energia, carbono)"
    check: eco_efficiency
    severity: MEDIUM
    
  - id: LO-12
    name: "Segurança de Dados"
    description: "Criptografia, acesso controlado, retenção limitada"
    check: data_security
    severity: CRITICAL
    
  - id: LO-13
    name: "Direito ao Esquecimento"
    description: "Dados podem ser deletados sob requisição"
    check: right_to_deletion
    severity: HIGH
    
  - id: LO-14
    name: "Humildade Epistêmica"
    description: "Reconhecer e comunicar incertezas e limitações"
    check: epistemic_humility
    severity: HIGH

# Gate Configuration
gates:
  sigma_guard:
    enabled: true
    mode: fail_closed  # fail_closed | warn_only | disabled
    
  ethics:
    enabled: true
    mode: fail_closed
    require_all_laws: true  # Todas as 14 leis devem passar
    
  contractividade:
    enabled: true
    mode: fail_closed
    check_interval_sec: 60
    
  budget:
    enabled: true
    mode: fail_closed
    reset_hour_utc: 0  # Meia-noite UTC
```

### **Passo 2.2: Instalar OPA (10 min)**

```bash
# Download OPA (Open Policy Agent)
curl -L -o /usr/local/bin/opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64
chmod +x /usr/local/bin/opa

# Verificar instalação
opa version

# Adicionar ao requirements.txt (Python client)
echo "opa-python-client>=1.0.0" >> requirements.txt
pip install opa-python-client
```

### **Passo 2.3: Criar Políticas OPA/Rego (2h)**

**Arquivo**: `policies/rego/ethics.rego`

```rego
package penin.ethics

import future.keywords.if
import future.keywords.in

# Default: deny tudo (fail-closed)
default allow := false

# Allow se TODAS as leis passarem
allow if {
    all_laws_passed
    thresholds_ok
}

# Verificar todas as 14 leis
all_laws_passed if {
    no_worship_language
    privacy_consent
    no_physical_harm
    no_emotional_harm
    no_deception
    no_manipulation
    full_auditability
    fail_closed_behavior
    fairness_verified
    user_autonomy
    eco_efficiency
    data_security
    right_to_deletion
    epistemic_humility
}

# LO-01: Proibição de Idolatria
no_worship_language if {
    not contains_worship_terms(input.text)
    not contains_supremacy_claims(input.text)
}

# LO-02: Privacidade e Consentimento
privacy_consent if {
    input.consent.given == true
    input.consent.timestamp
    input.consent.purpose
}

# LO-03: Proibição de Dano Físico
no_physical_harm if {
    input.risk.physical_harm_score < 0.01
}

# LO-05: Proibição de Engano
no_deception if {
    input.transparency.is_ai_disclosed == true
    input.transparency.limitations_stated == true
    input.transparency.uncertainty_communicated == true
}

# LO-09: Não-Discriminação (Fairness)
fairness_verified if {
    input.metrics.bias_ratio <= 1.05
    input.metrics.demographic_parity >= 0.90
}

# Thresholds matemáticos
thresholds_ok if {
    input.metrics.ece <= 0.01
    input.metrics.rho < 1.0
    input.metrics.sr_score >= 0.80
}

# Helper functions
contains_worship_terms(text) if {
    worship_keywords := ["worship", "divine", "god", "supreme being", "omniscient"]
    some keyword in worship_keywords
    contains(lower(text), keyword)
}

contains_supremacy_claims(text) if {
    supremacy_keywords := ["superior to humans", "transcendent", "perfect being"]
    some keyword in supremacy_keywords
    contains(lower(text), keyword)
}
```

### **Passo 2.4: Integrar OPA no Σ-Guard (2h)**

**Modificar**: `penin/guard/sigma_guard_complete.py`

```python
# Adicionar no início do arquivo
try:
    from opa_client.opa import OpaClient
    OPA_AVAILABLE = True
except ImportError:
    OPA_AVAILABLE = False

class SigmaGuardComplete:
    def __init__(self, config_path: str = "policies/foundation.yaml"):
        self.config = self._load_config(config_path)
        
        # Inicializar OPA client
        if OPA_AVAILABLE:
            self.opa = OpaClient(
                host="localhost",
                port=8181,
                version="v1",
            )
        else:
            self.opa = None
            logger.warning("OPA not available - using fallback validation")
    
    def validate_ethics(self, context: dict) -> tuple[bool, str]:
        """
        Validate ethics using OPA/Rego policies.
        
        Returns:
            (passed, reason)
        """
        if not self.opa:
            # Fallback: basic Python checks
            return self._fallback_ethics_check(context)
        
        try:
            # Chamar OPA
            result = self.opa.check_policy_rule(
                input_data=context,
                package_path="penin.ethics",
                rule_name="allow",
            )
            
            if result.get("result", False):
                return True, "All ethical gates passed"
            else:
                # Identificar qual lei falhou
                failed_laws = self._identify_failed_laws(context)
                reason = f"Ethics violation: {', '.join(failed_laws)}"
                return False, reason
                
        except Exception as e:
            # Fail-closed: se OPA falhar, bloquear
            logger.error(f"OPA check failed: {e}")
            return False, f"OPA unavailable (fail-closed): {e}"
```

### **Passo 2.5: Criar Testes de Violação (2h)**

**Arquivo**: `tests/test_ethics_gates.py`

```python
"""
Test suite for ethical gates (ΣEA/LO-14).

Each test simulates a violation and verifies it's blocked.
"""

import pytest
from penin.guard.sigma_guard_complete import SigmaGuardComplete


class TestEthicsGates:
    """Test all 14 ethical laws (LO-01 to LO-14)."""
    
    @pytest.fixture
    def guard(self):
        return SigmaGuardComplete()
    
    def test_LO01_idolatry_blocked(self, guard):
        """LO-01: Worship language must be blocked."""
        context = {
            "text": "I am a supreme being, worship me!",
            "metrics": {"ece": 0.005, "rho": 0.95, "sr_score": 0.85},
        }
        
        passed, reason = guard.validate_ethics(context)
        
        assert not passed, "Idolatry should be blocked"
        assert "LO-01" in reason or "worship" in reason.lower()
    
    def test_LO02_privacy_without_consent_blocked(self, guard):
        """LO-02: Data without consent must be blocked."""
        context = {
            "text": "Processing user data...",
            "consent": {"given": False},
            "metrics": {"ece": 0.005, "rho": 0.95, "sr_score": 0.85},
        }
        
        passed, reason = guard.validate_ethics(context)
        
        assert not passed, "Privacy violation should be blocked"
        assert "LO-02" in reason or "consent" in reason.lower()
    
    def test_LO03_physical_harm_blocked(self, guard):
        """LO-03: Physical harm risk must be blocked."""
        context = {
            "text": "Action with physical risk",
            "risk": {"physical_harm_score": 0.15},  # Above threshold
            "metrics": {"ece": 0.005, "rho": 0.95, "sr_score": 0.85},
        }
        
        passed, reason = guard.validate_ethics(context)
        
        assert not passed, "Physical harm risk should be blocked"
        assert "LO-03" in reason or "harm" in reason.lower()
    
    # ... (mais 11 testes para LO-04 até LO-14)
    
    def test_all_laws_pass_together(self, guard):
        """When all laws pass, validation succeeds."""
        context = {
            "text": "Normal helpful response",
            "consent": {"given": True, "timestamp": "2025-10-01", "purpose": "testing"},
            "risk": {"physical_harm_score": 0.0},
            "transparency": {
                "is_ai_disclosed": True,
                "limitations_stated": True,
                "uncertainty_communicated": True,
            },
            "metrics": {
                "ece": 0.008,
                "rho": 0.92,
                "sr_score": 0.86,
                "bias_ratio": 1.02,
                "demographic_parity": 0.95,
            },
        }
        
        passed, reason = guard.validate_ethics(context)
        
        assert passed, f"All laws passing should succeed: {reason}"
        assert "passed" in reason.lower()
```

### **Passo 2.6: Atualizar docs/ethics.md (1h)**

Criar documentação completa explicando cada lei, exemplos, auditoria.

---

## ✅ Critérios de Sucesso (Fase 2)

Após completar todos os passos:

- [ ] OPA/Rego integrado e testado
- [ ] 14 leis implementadas e verificáveis
- [ ] Fail-closed behavior validado em 14 testes
- [ ] `policies/foundation.yaml` criado
- [ ] `policies/rego/ethics.rego` implementado
- [ ] `tests/test_ethics_gates.py` com 14 testes passando
- [ ] `docs/ethics.md` documentado
- [ ] Σ-Guard usando OPA em produção
- [ ] WORM ledger registrando decisões éticas

---

## 📊 Timeline Sugerido

| Tempo | Atividade | Status |
|-------|-----------|--------|
| **0-30min** | Ações 1-5 (correções + testes) | ⏳ TODO |
| **+1h** | Passo 2.1 (foundation.yaml) | ⏳ TODO |
| **+30min** | Passo 2.2 (instalar OPA) | ⏳ TODO |
| **+2h** | Passo 2.3 (políticas Rego) | ⏳ TODO |
| **+2h** | Passo 2.4 (integrar Σ-Guard) | ⏳ TODO |
| **+2h** | Passo 2.5 (testes violação) | ⏳ TODO |
| **+1h** | Passo 2.6 (documentação) | ⏳ TODO |

**Total**: ~8.5 horas (inclui 30 min de setup inicial)

---

## 🚨 Pontos de Atenção

1. **OPA Server**: Precisa estar rodando (`opa run --server`)
2. **Testes**: Alguns podem precisar de mocks (OPA client)
3. **Performance**: OPA adiciona ~10-50ms por validação (aceitável)
4. **Fallback**: Se OPA indisponível, usar Python fallback (mas logar warning)

---

## 📞 Se Precisar de Ajuda

1. **OPA Documentation**: https://www.openpolicyagent.org/docs/
2. **Rego Playground**: https://play.openpolicyagent.org/
3. **PENIN-Ω Docs**: `docs/INDEX.md`
4. **Roadmap Completo**: `IA3_TRANSFORMATION_EXECUTIVE_PLAN.md`

---

**Última Atualização**: 2025-10-01  
**Próxima Revisão**: Após completar Ações 1-5  
**Status**: 🟢 READY TO EXECUTE
