"""
Mutators Module - Param Sweeps + Prompt Variants
===============================================

Implementa geradores de variantes (challengers) determinísticos:
- Parameter sweeps (temperatura, top-p, top-k, max_tokens, etc.)
- Prompt template variations (few-shot, system constraints, etc.)
- Determinístico com seed para reprodutibilidade
- Extensível para LoRA/PEFT e quantização no futuro
"""

import hashlib
import json
import random
from typing import Dict, Any, List, Optional, Iterator
from typing_extensions import Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class MutationType(Enum):
    """Tipos de mutação suportados"""
    PARAM_SWEEP = "param_sweep"
    PROMPT_VARIANT = "prompt_variant"
    SYSTEM_VARIANT = "system_variant"
    TEMPLATE_VARIANT = "template_variant"


@dataclass
class MutationConfig:
    """Configuração de uma mutação"""
    mutation_type: MutationType
    base_config: Dict[str, Any]
    mutations: Dict[str, Any]
    mutation_id: str
    parent_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Converter enum para string
        data["mutation_type"] = self.mutation_type.value
        return data
        
    def compute_hash(self) -> str:
        """Computa hash determinístico da configuração"""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()


class ParameterSweeper:
    """Gerador de parameter sweeps determinísticos"""
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        
    def generate_temperature_sweep(self, 
                                 base_temp: float = 0.7,
                                 n_variants: int = 5,
                                 temp_range: Tuple[float, float] = (0.1, 1.5)) -> List[Dict[str, Any]]:
        """Gera sweep de temperatura"""
        variants = []
        min_temp, max_temp = temp_range
        
        # Distribuição uniforme
        for i in range(n_variants):
            if n_variants == 1:
                temp = base_temp
            else:
                temp = min_temp + (max_temp - min_temp) * i / (n_variants - 1)
                
            variants.append({
                "temperature": round(temp, 2),
                "variant_id": f"temp_{temp:.2f}",
                "base_temperature": base_temp
            })
            
        return variants
        
    def generate_top_p_sweep(self,
                           base_top_p: float = 0.9,
                           n_variants: int = 4,
                           top_p_range: Tuple[float, float] = (0.5, 1.0)) -> List[Dict[str, Any]]:
        """Gera sweep de top-p"""
        variants = []
        min_p, max_p = top_p_range
        
        for i in range(n_variants):
            if n_variants == 1:
                top_p = base_top_p
            else:
                top_p = min_p + (max_p - min_p) * i / (n_variants - 1)
                
            variants.append({
                "top_p": round(top_p, 2),
                "variant_id": f"top_p_{top_p:.2f}",
                "base_top_p": base_top_p
            })
            
        return variants
        
    def generate_max_tokens_sweep(self,
                                base_max_tokens: int = 1000,
                                n_variants: int = 3,
                                token_multipliers: List[float] = [0.5, 1.0, 1.5]) -> List[Dict[str, Any]]:
        """Gera sweep de max_tokens"""
        variants = []
        
        for i, multiplier in enumerate(token_multipliers[:n_variants]):
            max_tokens = int(base_max_tokens * multiplier)
            
            variants.append({
                "max_tokens": max_tokens,
                "variant_id": f"tokens_{max_tokens}",
                "base_max_tokens": base_max_tokens,
                "multiplier": multiplier
            })
            
        return variants
        
    def generate_combined_sweep(self,
                              base_config: Dict[str, Any],
                              n_variants: int = 8) -> List[Dict[str, Any]]:
        """Gera sweep combinado de múltiplos parâmetros"""
        variants = []
        
        # Parâmetros base
        base_temp = base_config.get("temperature", 0.7)
        base_top_p = base_config.get("top_p", 0.9)
        base_tokens = base_config.get("max_tokens", 1000)
        
        # Gerar variações
        for i in range(n_variants):
            # Usar RNG determinístico
            temp_factor = 0.5 + self.rng.random() * 1.0  # [0.5, 1.5]
            top_p_factor = 0.7 + self.rng.random() * 0.3  # [0.7, 1.0]
            token_factor = 0.5 + self.rng.random() * 1.0  # [0.5, 1.5]
            
            variant = base_config.copy()
            variant.update({
                "temperature": round(base_temp * temp_factor, 2),
                "top_p": round(base_top_p * top_p_factor, 2),
                "max_tokens": int(base_tokens * token_factor),
                "variant_id": f"combined_{i:02d}",
                "mutation_factors": {
                    "temp_factor": temp_factor,
                    "top_p_factor": top_p_factor,
                    "token_factor": token_factor
                }
            })
            
            variants.append(variant)
            
        return variants


class PromptVariator:
    """Gerador de variações de prompt determinísticas"""
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        
    def generate_few_shot_variants(self,
                                 base_prompt: str,
                                 examples: List[Dict[str, str]],
                                 n_variants: int = 4) -> List[Dict[str, Any]]:
        """Gera variantes few-shot com diferentes números de exemplos"""
        variants = []
        
        if not examples:
            return [{"prompt": base_prompt, "variant_id": "no_examples", "n_examples": 0}]
            
        # Diferentes números de exemplos
        example_counts = [0, 1, 2, min(len(examples), 3)][:n_variants]
        
        for i, n_examples in enumerate(example_counts):
            if n_examples == 0:
                prompt = base_prompt
            else:
                # Selecionar exemplos determinísticamente
                selected_examples = examples[:n_examples]
                
                # Formatar exemplos
                examples_text = "\n\nExemplos:\n"
                for j, ex in enumerate(selected_examples, 1):
                    examples_text += f"{j}. Input: {ex.get('input', '')}\n"
                    examples_text += f"   Output: {ex.get('output', '')}\n"
                    
                prompt = base_prompt + examples_text
                
            variants.append({
                "prompt": prompt,
                "variant_id": f"few_shot_{n_examples}ex",
                "n_examples": n_examples,
                "base_prompt": base_prompt
            })
            
        return variants
        
    def generate_system_variants(self,
                               base_system: str,
                               system_templates: List[str],
                               n_variants: int = 3) -> List[Dict[str, Any]]:
        """Gera variantes de system message"""
        variants = []
        
        # Incluir sistema base
        variants.append({
            "system": base_system,
            "variant_id": "base_system",
            "template": "base"
        })
        
        # Aplicar templates
        for i, template in enumerate(system_templates[:n_variants-1]):
            try:
                # Template simples com {base_system}
                if "{base_system}" in template:
                    system = template.format(base_system=base_system)
                else:
                    system = template + "\n\n" + base_system
                    
                variants.append({
                    "system": system,
                    "variant_id": f"template_{i:02d}",
                    "template": template[:50] + "..." if len(template) > 50 else template
                })
            except Exception:
                # Skip invalid templates
                continue
                
        return variants
        
    def generate_constraint_variants(self,
                                   base_prompt: str,
                                   constraints: List[str],
                                   n_variants: int = 4) -> List[Dict[str, Any]]:
        """Gera variantes com diferentes constraints"""
        variants = []
        
        # Sem constraints
        variants.append({
            "prompt": base_prompt,
            "variant_id": "no_constraints",
            "constraints": []
        })
        
        # Com constraints
        for i in range(min(n_variants - 1, len(constraints))):
            # Adicionar constraints progressivamente
            active_constraints = constraints[:i+1]
            
            constraint_text = "\n\nRestrições:\n"
            for j, constraint in enumerate(active_constraints, 1):
                constraint_text += f"{j}. {constraint}\n"
                
            prompt = base_prompt + constraint_text
            
            variants.append({
                "prompt": prompt,
                "variant_id": f"constraints_{i+1}",
                "constraints": active_constraints,
                "base_prompt": base_prompt
            })
            
        return variants


class MutationOrchestrator:
    """Orquestrador de mutações determinístico"""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self.param_sweeper = ParameterSweeper(seed)
        self.prompt_variator = PromptVariator(seed)
        self.mutation_count = 0
        
    def generate_challengers(self,
                           champion_config: Dict[str, Any],
                           n_challengers: int = 8,
                           mutation_types: Optional[List[MutationType]] = None) -> List[MutationConfig]:
        """
        Gera challengers determinísticos
        
        Args:
            champion_config: Configuração do champion atual
            n_challengers: Número de challengers a gerar
            mutation_types: Tipos de mutação (default: todos)
            
        Returns:
            Lista de MutationConfig
        """
        if mutation_types is None:
            mutation_types = [MutationType.PARAM_SWEEP, MutationType.PROMPT_VARIANT]
            
        challengers = []
        champion_hash = hashlib.sha256(
            json.dumps(champion_config, sort_keys=True).encode()
        ).hexdigest()
        
        # Distribuir challengers entre tipos de mutação
        per_type = max(1, n_challengers // len(mutation_types))
        
        for mutation_type in mutation_types:
            type_challengers = []
            
            if mutation_type == MutationType.PARAM_SWEEP:
                type_challengers = self._generate_param_challengers(
                    champion_config, per_type
                )
            elif mutation_type == MutationType.PROMPT_VARIANT:
                type_challengers = self._generate_prompt_challengers(
                    champion_config, per_type
                )
                
            # Converter para MutationConfig
            for challenger in type_challengers:
                self.mutation_count += 1
                mutation_id = f"mut_{self.mutation_count:04d}_{mutation_type.value}"
                
                config = MutationConfig(
                    mutation_type=mutation_type,
                    base_config=champion_config,
                    mutations=challenger,
                    mutation_id=mutation_id,
                    parent_hash=champion_hash
                )
                
                challengers.append(config)
                
                if len(challengers) >= n_challengers:
                    break
                    
            if len(challengers) >= n_challengers:
                break
                
        return challengers[:n_challengers]
        
    def _generate_param_challengers(self,
                                  base_config: Dict[str, Any],
                                  n_challengers: int) -> List[Dict[str, Any]]:
        """Gera challengers via parameter sweep"""
        challengers = []
        
        # Sweep combinado
        param_variants = self.param_sweeper.generate_combined_sweep(
            base_config, n_challengers
        )
        
        for variant in param_variants:
            challengers.append({
                "type": "param_sweep",
                "config": variant,
                "changed_params": self._find_changed_params(base_config, variant)
            })
            
        return challengers
        
    def _generate_prompt_challengers(self,
                                   base_config: Dict[str, Any],
                                   n_challengers: int) -> List[Dict[str, Any]]:
        """Gera challengers via prompt variation"""
        challengers = []
        
        base_prompt = base_config.get("prompt", "")
        base_system = base_config.get("system", "")
        
        # Templates de sistema
        system_templates = [
            "Você é um assistente especializado. {base_system}",
            "Responda de forma precisa e concisa. {base_system}",
            "Use raciocínio passo-a-passo. {base_system}"
        ]
        
        # Constraints
        constraints = [
            "Responda em no máximo 3 parágrafos",
            "Inclua fontes quando possível",
            "Use linguagem técnica apropriada",
            "Verifique a lógica antes de responder"
        ]
        
        # Gerar variantes de sistema
        if base_system:
            system_variants = self.prompt_variator.generate_system_variants(
                base_system, system_templates, min(n_challengers // 2, 3)
            )
            
            for variant in system_variants:
                config = base_config.copy()
                config["system"] = variant["system"]
                
                challengers.append({
                    "type": "system_variant",
                    "config": config,
                    "variant_info": variant
                })
                
        # Gerar variantes de prompt com constraints
        if base_prompt:
            constraint_variants = self.prompt_variator.generate_constraint_variants(
                base_prompt, constraints, min(n_challengers // 2, 4)
            )
            
            for variant in constraint_variants:
                config = base_config.copy()
                config["prompt"] = variant["prompt"]
                
                challengers.append({
                    "type": "prompt_variant",
                    "config": config,
                    "variant_info": variant
                })
                
        return challengers[:n_challengers]
        
    def _find_changed_params(self, 
                           base_config: Dict[str, Any],
                           variant_config: Dict[str, Any]) -> List[str]:
        """Encontra parâmetros que mudaram"""
        changed = []
        
        for key, value in variant_config.items():
            if key in base_config and base_config[key] != value:
                changed.append(key)
            elif key not in base_config:
                changed.append(key)
                
        return changed
        
    def get_mutation_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de mutação"""
        return {
            "total_mutations": self.mutation_count,
            "seed": self.seed,
            "supported_types": [t.value for t in MutationType]
        }


class ChallengerGenerator:
    """Gerador principal de challengers"""
    
    def __init__(self, seed: Optional[int] = None):
        self.orchestrator = MutationOrchestrator(seed)
        
    def generate_from_champion(self,
                             champion_config: Dict[str, Any],
                             n_challengers: int = 8,
                             strategy: str = "balanced") -> List[MutationConfig]:
        """
        Gera challengers a partir do champion
        
        Args:
            champion_config: Configuração do champion
            n_challengers: Número de challengers
            strategy: Estratégia de geração ('balanced', 'param_heavy', 'prompt_heavy')
            
        Returns:
            Lista de MutationConfig
        """
        if strategy == "param_heavy":
            mutation_types = [MutationType.PARAM_SWEEP] * 3 + [MutationType.PROMPT_VARIANT]
        elif strategy == "prompt_heavy":
            mutation_types = [MutationType.PROMPT_VARIANT] * 3 + [MutationType.PARAM_SWEEP]
        else:  # balanced
            mutation_types = [MutationType.PARAM_SWEEP, MutationType.PROMPT_VARIANT]
            
        return self.orchestrator.generate_challengers(
            champion_config, n_challengers, mutation_types
        )
        
    def validate_challenger(self, challenger: MutationConfig) -> Tuple[bool, List[str]]:
        """
        Valida se challenger é válido
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # Verificar se tem configuração
        if not challenger.mutations:
            errors.append("No mutations specified")
            
        # Verificar se config é válida
        if challenger.mutation_type == MutationType.PARAM_SWEEP:
            config = challenger.mutations.get("config", {})
            
            # Validar ranges de parâmetros
            temp = config.get("temperature")
            if temp is not None and not (0.0 <= temp <= 2.0):
                errors.append(f"Invalid temperature: {temp}")
                
            top_p = config.get("top_p")
            if top_p is not None and not (0.0 <= top_p <= 1.0):
                errors.append(f"Invalid top_p: {top_p}")
                
            max_tokens = config.get("max_tokens")
            if max_tokens is not None and not (1 <= max_tokens <= 100000):
                errors.append(f"Invalid max_tokens: {max_tokens}")
                
        return len(errors) == 0, errors
        
    def get_challenger_summary(self, challengers: List[MutationConfig]) -> Dict[str, Any]:
        """Retorna resumo dos challengers gerados"""
        if not challengers:
            return {"total": 0, "by_type": {}}
            
        by_type = {}
        for challenger in challengers:
            type_name = challenger.mutation_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            
        return {
            "total": len(challengers),
            "by_type": by_type,
            "first_mutation_id": challengers[0].mutation_id,
            "last_mutation_id": challengers[-1].mutation_id,
            "parent_hash": challengers[0].parent_hash[:8] if challengers[0].parent_hash else None
        }


# Funções de conveniência
def quick_param_sweep(base_config: Dict[str, Any], 
                     n_variants: int = 5,
                     seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Gera sweep rápido de parâmetros"""
    sweeper = ParameterSweeper(seed)
    return sweeper.generate_combined_sweep(base_config, n_variants)


def quick_prompt_variants(base_prompt: str,
                        n_variants: int = 3,
                        seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Gera variantes rápidas de prompt"""
    variator = PromptVariator(seed)
    
    constraints = [
        "Seja conciso e direto",
        "Use exemplos quando apropriado",
        "Explique o raciocínio"
    ]
    
    return variator.generate_constraint_variants(base_prompt, constraints, n_variants)


def quick_challengers(champion_config: Dict[str, Any],
                     n_challengers: int = 6,
                     seed: Optional[int] = None) -> List[MutationConfig]:
    """Gera challengers rapidamente"""
    generator = ChallengerGenerator(seed)
    return generator.generate_from_champion(champion_config, n_challengers)


# Exemplo de uso
if __name__ == "__main__":
    print("🧬 Demonstração: Mutators - Param Sweeps + Prompt Variants")
    print("=" * 60)
    
    # Configuração base do champion
    champion_config = {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 1000,
        "prompt": "Analise o seguinte texto e extraia as informações principais:",
        "system": "Você é um assistente de análise de texto especializado."
    }
    
    print("Champion config:")
    for k, v in champion_config.items():
        if isinstance(v, str) and len(v) > 50:
            v = v[:47] + "..."
        print(f"  {k}: {v}")
    print()
    
    # Gerar challengers
    generator = ChallengerGenerator(seed=42)
    challengers = generator.generate_from_champion(champion_config, n_challengers=6)
    
    print(f"✅ Gerados {len(challengers)} challengers:")
    
    for i, challenger in enumerate(challengers, 1):
        print(f"\n{i}. {challenger.mutation_id}")
        print(f"   Tipo: {challenger.mutation_type.value}")
        print(f"   Hash: {challenger.compute_hash()[:8]}...")
        
        # Mostrar mudanças
        if challenger.mutation_type == MutationType.PARAM_SWEEP:
            config = challenger.mutations.get("config", {})
            changed = challenger.mutations.get("changed_params", [])
            print(f"   Parâmetros alterados: {changed}")
            for param in changed:
                if param in config:
                    print(f"     {param}: {champion_config.get(param)} → {config[param]}")
                    
        elif challenger.mutation_type == MutationType.PROMPT_VARIANT:
            variant_info = challenger.mutations.get("variant_info", {})
            print(f"   Variante: {variant_info.get('variant_id', 'unknown')}")
            
    # Resumo
    summary = generator.get_challenger_summary(challengers)
    print(f"\n📊 Resumo:")
    print(f"   Total: {summary['total']}")
    print(f"   Por tipo: {summary['by_type']}")
    print(f"   Parent hash: {summary['parent_hash']}")
    
    # Estatísticas do orchestrator
    stats = generator.orchestrator.get_mutation_stats()
    print(f"   Mutações totais: {stats['total_mutations']}")
    print(f"   Seed: {stats['seed']}")
    
    print("\n✅ Mutators implementados e funcionando!")
    print("🔄 Próximo: Implementar evaluators para medir U/S/C/L")