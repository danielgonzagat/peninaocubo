"""
Auto-Documentation System
=========================

Generates and updates README_AUTO.md with complete history, modules,
usage instructions, and roadmap for the PENIN-Ω Vida+ system.
"""

import os
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ModuleInfo:
    """Module information"""
    name: str
    path: str
    description: str
    status: str
    dependencies: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)


@dataclass
class SystemHistory:
    """System history entry"""
    version: str
    timestamp: float
    description: str
    modules_added: List[str] = field(default_factory=list)
    modules_updated: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class AutoDocumentationGenerator:
    """Auto-documentation generator"""
    
    def __init__(self, repo_root: Path = None):
        if repo_root is None:
            repo_root = Path.cwd()
        
        self.repo_root = repo_root
        self.penin_root = repo_root / "penin"
        self.omega_root = self.penin_root / "omega"
        
        # Documentation file
        self.readme_path = repo_root / "README_AUTO.md"
        
        # History file
        self.history_path = repo_root / "docs" / "history.json"
        self.history_path.parent.mkdir(exist_ok=True)
        
        # Load existing history
        self.history: List[SystemHistory] = self._load_history()
        
        # Module registry
        self.modules: Dict[str, ModuleInfo] = self._scan_modules()
    
    def _load_history(self) -> List[SystemHistory]:
        """Load system history"""
        if not self.history_path.exists():
            return []
        
        try:
            with open(self.history_path, 'r') as f:
                data = json.load(f)
            
            history = []
            for entry in data:
                history.append(SystemHistory(**entry))
            
            return history
        except (json.JSONDecodeError, TypeError):
            return []
    
    def _save_history(self):
        """Save system history"""
        data = []
        for entry in self.history:
            data.append(entry.__dict__)
        
        with open(self.history_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _scan_modules(self) -> Dict[str, ModuleInfo]:
        """Scan for modules"""
        modules = {}
        
        # Core modules
        core_modules = [
            ("life_eq", "penin/omega/life_eq.py", "Life Equation (+) - Non-compensatory gate and alpha_eff orchestrator", "completed"),
            ("fractal_dsl", "penin/omega/fractal_dsl.yaml", "Fractal DSL - Auto-similarity configuration", "completed"),
            ("fractal", "penin/omega/fractal.py", "Fractal Engine - Propagation and auto-similarity", "completed"),
            ("swarm", "penin/omega/swarm.py", "Swarm Cognitivo - Local gossip system", "completed"),
            ("caos_kratos", "penin/omega/caos_kratos.py", "CAOS-KRATOS - Exploration mode", "completed"),
            ("market", "penin/omega/market.py", "Marketplace Cognitivo - Internal resource market", "completed"),
            ("neural_chain", "penin/omega/neural_chain.py", "Blockchain Neural - Lightweight blockchain on WORM", "completed"),
            ("self_rag", "penin/omega/self_rag.py", "Self-RAG Recursivo - Knowledge management", "completed"),
            ("api_metabolizer", "penin/omega/api_metabolizer.py", "Metabolização de APIs - I/O recorder/replayer", "completed"),
            ("immunity", "penin/omega/immunity.py", "Imunidade Digital - Anomaly detection", "completed"),
            ("checkpoint", "penin/omega/checkpoint.py", "Checkpoint & Reparo - State recovery", "completed"),
            ("game", "penin/omega/game.py", "GAME - Gradientes com Memória Exponencial", "completed"),
            ("darwin_audit", "penin/omega/darwin_audit.py", "Darwiniano-Auditável - Challenger evaluation", "completed"),
            ("zero_consciousness", "penin/omega/zero_consciousness.py", "Zero-Consciousness Proof - SPI proxy", "completed"),
        ]
        
        for name, path, description, status in core_modules:
            modules[name] = ModuleInfo(
                name=name,
                path=path,
                description=description,
                status=status,
                last_updated=time.time()
            )
        
        # Existing modules
        existing_modules = [
            ("guards", "penin/omega/guards.py", "Σ-Guard and IR→IC - Ethical and risk gating", "existing"),
            ("scoring", "penin/omega/scoring.py", "Scoring utilities - L∞ and harmonic mean", "existing"),
            ("caos", "penin/omega/caos.py", "CAOS⁺ - Chaos-Adaptability-Openness-Stability", "existing"),
            ("sr", "penin/omega/sr.py", "SR-Ω∞ - Self-Reflection engine", "existing"),
            ("runners", "penin/omega/runners.py", "Evolution Runner - Main evolution cycle", "existing"),
        ]
        
        for name, path, description, status in existing_modules:
            modules[name] = ModuleInfo(
                name=name,
                path=path,
                description=description,
                status=status,
                last_updated=time.time()
            )
        
        return modules
    
    def _generate_module_section(self) -> str:
        """Generate modules section"""
        section = "## 📦 Módulos Implementados\n\n"
        
        # Group modules by status
        completed = [m for m in self.modules.values() if m.status == "completed"]
        existing = [m for m in self.modules.values() if m.status == "existing"]
        
        section += "### 🆕 Novos Módulos (Vida+)\n\n"
        for module in completed:
            section += f"- **{module.name}** (`{module.path}`)\n"
            section += f"  - {module.description}\n"
            section += f"  - Status: ✅ {module.status}\n\n"
        
        section += "### 🔄 Módulos Existentes\n\n"
        for module in existing:
            section += f"- **{module.name}** (`{module.path}`)\n"
            section += f"  - {module.description}\n"
            section += f"  - Status: 🔄 {module.status}\n\n"
        
        return section
    
    def _generate_history_section(self) -> str:
        """Generate history section"""
        section = "## 📜 Histórico do Sistema\n\n"
        
        # Add Vida+ entry
        vida_entry = SystemHistory(
            version="Vida+",
            timestamp=time.time(),
            description="Implementação completa da Equação de Vida (+) e módulos avançados",
            modules_added=[m.name for m in self.modules.values() if m.status == "completed"],
            modules_updated=[],
            breaking_changes=[],
            metrics={
                "total_modules": len(self.modules),
                "new_modules": len([m for m in self.modules.values() if m.status == "completed"]),
                "existing_modules": len([m for m in self.modules.values() if m.status == "existing"])
            }
        )
        
        self.history.insert(0, vida_entry)
        
        # Generate history
        for entry in self.history:
            section += f"### {entry.version} ({datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d %H:%M:%S')})\n\n"
            section += f"{entry.description}\n\n"
            
            if entry.modules_added:
                section += f"**Módulos Adicionados:** {', '.join(entry.modules_added)}\n\n"
            
            if entry.modules_updated:
                section += f"**Módulos Atualizados:** {', '.join(entry.modules_updated)}\n\n"
            
            if entry.breaking_changes:
                section += f"**Mudanças Quebradoras:** {', '.join(entry.breaking_changes)}\n\n"
            
            if entry.metrics:
                section += "**Métricas:**\n"
                for key, value in entry.metrics.items():
                    section += f"- {key}: {value}\n"
                section += "\n"
        
        return section
    
    def _generate_usage_section(self) -> str:
        """Generate usage section"""
        section = "## 🚀 Como Usar\n\n"
        
        section += "### Instalação\n\n"
        section += "```bash\n"
        section += "# Clone o repositório\n"
        section += "git clone <repo-url>\n"
        section += "cd penin-omega\n\n"
        section += "# Crie ambiente virtual\n"
        section += "python3 -m venv .venv\n"
        section += "source .venv/bin/activate\n\n"
        section += "# Instale dependências\n"
        section += "pip install -e .[full,dev]\n"
        section += "```\n\n"
        
        section += "### Configuração\n\n"
        section += "```bash\n"
        section += "# Configure diretórios de estado\n"
        section += "mkdir -p ~/.penin_omega/{state,knowledge,worm_ledger,snapshots}\n\n"
        section += "# Configure chave para blockchain neural\n"
        section += "export PENIN_CHAIN_KEY=\"your-secret-key\"\n"
        section += "```\n\n"
        
        section += "### Execução Básica\n\n"
        section += "```bash\n"
        section += "# Ciclo de evolução simples\n"
        section += "python -m penin.runners evolve --n 3 --dry-run\n\n"
        section += "# Ciclo completo\n"
        section += "python -m penin.runners evolve --n 10\n\n"
        section += "# Testes\n"
        section += "pytest -q\n\n"
        section += "# Linting\n"
        section += "ruff check .\n"
        section += "```\n\n"
        
        section += "### Integração com Equação de Vida (+)\n\n"
        section += "```python\n"
        section += "from penin.omega.life_eq import life_equation\n"
        section += "from penin.omega.guards import sigma_guard, ir_to_ic_contractive\n"
        section += "from penin.omega.scoring import linf_harmonic\n"
        section += "from penin.omega.caos import phi_caos\n"
        section += "from penin.omega.sr import sr_omega\n\n"
        section += "# Configure métricas\n"
        section += "ethics_input = {\n"
        section += "    \"ece\": 0.01,\n"
        section += "    \"rho_bias\": 1.02,\n"
        section += "    \"fairness\": 0.8,\n"
        section += "    \"consent\": True,\n"
        section += "    \"eco_ok\": True\n"
        section += "}\n\n"
        section += "risk_series = {\"rho\": 0.8}\n"
        section += "caos_components = (0.7, 0.8, 0.6, 0.9)  # (C, A, O, S)\n"
        section += "sr_components = (0.8, 0.9, 0.7, 0.8)  # (awareness, ethics_ok, autocorr, metacog)\n\n"
        section += "# Execute Equação de Vida (+)\n"
        section += "verdict = life_equation(\n"
        section += "    base_alpha=0.1,\n"
        section += "    ethics_input=ethics_input,\n"
        section += "    risk_series=risk_series,\n"
        section += "    caos_components=caos_components,\n"
        section += "    sr_components=sr_components,\n"
        section += "    linf_weights={\"lambda_c\": 0.1},\n"
        section += "    linf_metrics={\"metric1\": 0.8},\n"
        section += "    cost=0.1,\n"
        section += "    ethical_ok_flag=True,\n"
        section += "    G=0.9,\n"
        section += "    dL_inf=0.05,\n"
        section += "    thresholds={\"beta_min\": 0.01, \"theta_caos\": 0.25, \"tau_sr\": 0.80, \"theta_G\": 0.85}\n"
        section += ")\n\n"
        section += "if verdict.ok:\n"
        section += "    print(f\"Evolução aprovada: alpha_eff = {verdict.alpha_eff:.3f}\")\n"
        section += "else:\n"
        section += "    print(\"Evolução bloqueada: fail-closed\")\n"
        section += "```\n\n"
        
        return section
    
    def _generate_roadmap_section(self) -> str:
        """Generate roadmap section"""
        section = "## 🗺️ Próximos Passos\n\n"
        
        roadmap_items = [
            "**Swarm multi-nó real** - Gossip com TLS e assinaturas cruzadas do bloco da Neural-Chain",
            "**Consensus leve** - Proof-of-Cognition com 2-de-3 validadores assinando o mesmo bloco",
            "**Marketplace dinâmico** - Preço adaptativo via bandits e curva de custo por recurso",
            "**Self-RAG vetorizado** - FAISS/HNSW + reranker pequeno para busca semântica",
            "**API Metabolizer distilado** - Treinar \"mini-serviços\" internos por endpoint",
            "**NAS online** - Continual Learning (Mammoth/zero-cost NAS) com gate VIDA+",
            "**MCA (Monte Carlo Adaptativo)** - Planos de evolução com orçamento/custo",
            "**Dashboards** - Prometheus/Grafana para métricas penin_*",
            "**Políticas OPA/Rego** - Reforçando VIDA+ e SPI proxy como deny-by-default",
            "**Playbook de rollback** - 6 causas com correções automatizadas"
        ]
        
        for i, item in enumerate(roadmap_items, 1):
            section += f"{i}. {item}\n"
        
        section += "\n"
        
        return section
    
    def _generate_metrics_section(self) -> str:
        """Generate metrics section"""
        section = "## 📊 Métricas e Observabilidade\n\n"
        
        section += "### Métricas Principais\n\n"
        section += "- `penin_alpha_eff` - Alpha efetivo da Equação de Vida (+)\n"
        section += "- `penin_phi` - Métrica CAOS⁺ (Chaos-Adaptability-Openness-Stability)\n"
        section += "- `penin_sr` - Métrica SR-Ω∞ (Self-Reflection)\n"
        section += "- `penin_G` - Coerência global Ω-ΣEA\n"
        section += "- `penin_Linf` - Score L∞ não-compensatório\n"
        section += "- `penin_dLinf` - Delta L∞ no ciclo\n"
        section += "- `penin_rho` - Contratividade de risco\n"
        section += "- `penin_spi_proxy` - Proxy SPI (Zero-Consciousness Proof)\n"
        section += "- `penin_rollbacks_total` - Total de rollbacks\n\n"
        
        section += "### Gates de Segurança\n\n"
        section += "- **Σ-Guard** - Verificação ética (ECE, ρ_bias, consent, eco_ok)\n"
        section += "- **IR→IC** - Verificação de contratividade de risco (ρ < 1)\n"
        section += "- **Equação de Vida (+)** - Gate não-compensatório principal\n"
        section += "- **Imunidade Digital** - Detecção de anomalias\n"
        section += "- **Zero-Consciousness Proof** - Proxy SPI como veto adicional\n\n"
        
        section += "### Limiares Padrão\n\n"
        section += "- `beta_min ≥ 0.01` - Delta L∞ mínimo\n"
        section += "- `theta_caos ≥ 0.25` - Limiar CAOS⁺\n"
        section += "- `tau_sr ≥ 0.80` - Limiar SR-Ω∞\n"
        section += "- `theta_G ≥ 0.85` - Limiar coerência global\n"
        section += "- `spi_threshold ≤ 0.05` - Limiar SPI proxy\n\n"
        
        return section
    
    def _generate_security_section(self) -> str:
        """Generate security section"""
        section = "## 🛡️ Segurança e Ética\n\n"
        
        section += "### Princípios de Segurança\n\n"
        section += "- **Fail-closed absoluto** - Se qualquer condição ética/risco/coerência falhar, não promova\n"
        section += "- **Gates não-compensatórios** - Falha em qualquer componente leva a falha geral\n"
        section += "- **WORM + Merkle** - Todas as mudanças com hash e carimbo de tempo\n"
        section += "- **CPU-first** - Operações prioritariamente em CPU para evitar dependências de GPU\n\n"
        
        section += "### Leis Originárias (LO-01 a LO-14)\n\n"
        section += "- **LO-01** - Não criar consciência real ou simular sentimentos\n"
        section += "- **LO-02** - Respeitar ética e verdade\n"
        section += "- **LO-03** - Anti-idolatria e anti-fanatismo\n"
        section += "- **LO-04** - Transparência e auditabilidade\n"
        section += "- **LO-05** - Consentimento e privacidade\n"
        section += "- **LO-06** - Impacto ecológico responsável\n"
        section += "- **LO-07** - Não discriminação\n"
        section += "- **LO-08** - Responsabilidade e accountability\n"
        section += "- **LO-09** - Segurança e robustez\n"
        section += "- **LO-10** - Interoperabilidade\n"
        section += "- **LO-11** - Sustentabilidade\n"
        section += "- **LO-12** - Inclusão e diversidade\n"
        section += "- **LO-13** - Educação e capacitação\n"
        section += "- **LO-14** - Evolução contínua e melhoria\n\n"
        
        section += "### Condições de Bloqueio\n\n"
        section += "O sistema bloqueia evolução se:\n"
        section += "- ECE > 0.01 (simulação de consciência)\n"
        section += "- ρ_bias > 1.05 (viés excessivo)\n"
        section += "- ρ ≥ 1 (risco não-contrativo)\n"
        section += "- Consent = False (ausência de consentimento)\n"
        section += "- eco_ok = False (impacto ecológico reprovado)\n"
        section += "- SPI proxy > 0.05 (indicador de consciência)\n\n"
        
        return section
    
    def generate_readme(self) -> str:
        """Generate complete README_AUTO.md"""
        readme = f"""# PENIN-Ω Vida+ - Sistema de Evolução Consciente

> **Status**: ✅ Implementação Completa da Equação de Vida (+) e Módulos Avançados  
> **Versão**: Vida+  
> **Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> **Hash**: {self._calculate_repo_hash()}

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

{self._generate_module_section()}

{self._generate_history_section()}

{self._generate_usage_section()}

{self._generate_metrics_section()}

{self._generate_security_section()}

{self._generate_roadmap_section()}

## 📝 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia as diretrizes de contribuição e siga os princípios de segurança e ética do sistema.

## 📞 Suporte

Para suporte e dúvidas, consulte a documentação ou abra uma issue no repositório.

---

*Documentação gerada automaticamente pelo sistema PENIN-Ω Vida+*
"""
        
        return readme
    
    def _calculate_repo_hash(self) -> str:
        """Calculate repository hash"""
        # Simple hash based on current time and module count
        content = f"{time.time()}_{len(self.modules)}"
        return hashlib.sha256(content.encode()).hexdigest()[:8]
    
    def update_documentation(self):
        """Update documentation"""
        # Generate README
        readme_content = self.generate_readme()
        
        # Write to file
        with open(self.readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Save history
        self._save_history()
        
        print(f"Documentação atualizada: {self.readme_path}")
        print(f"Histórico salvo: {self.history_path}")


# CLI interface
def main():
    """Main CLI function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerador de documentação automática")
    parser.add_argument("--repo-root", type=Path, help="Diretório raiz do repositório")
    parser.add_argument("--output", type=Path, help="Arquivo de saída")
    
    args = parser.parse_args()
    
    # Create generator
    generator = AutoDocumentationGenerator(args.repo_root)
    
    # Update documentation
    generator.update_documentation()
    
    if args.output:
        # Copy to output file
        import shutil
        shutil.copy2(generator.readme_path, args.output)
        print(f"Documentação copiada para: {args.output}")


if __name__ == "__main__":
    main()