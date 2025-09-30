"""
Auto-Tuning Online — AdaGrad/ONS via APIs (Mistral, OpenAI, Anthropic)
========================================================================

Implementa auto-tuning contínuo de hiperparâmetros via fine-tuning remoto:
- κ (CAOS+ multiplier)
- λ_c (L∞ confidence weight)
- w_U, w_S, w_C, w_L (U/S/C/L gate weights)
- β_min (minimum ΔL∞ for promotion)
- τ_* (limiares de decisão)

Estratégias:
1. Mistral AI: Fine-tuning supervisionado + chat para validação
2. OpenAI: RFT (Reinforcement Fine-Tuning) + DPO + SFT
3. Anthropic: Prompt optimization + few-shot learning

Limites de segurança:
- Δ máximo por ciclo: ±0.02
- Clipping: mantém valores dentro de ranges válidos
- Warmup: N ciclos antes de ativar tuning
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from pydantic import BaseModel, Field

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object

# API Clients
try:
    from mistralai import Mistral as MistralClient

    HAS_MISTRAL = True
except ImportError:
    HAS_MISTRAL = False

try:
    from openai import OpenAI as OpenAIClient

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import Anthropic as AnthropicClient

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

logger = logging.getLogger(__name__)


# ============================================================================
# Schema de Configuração de Tuning
# ============================================================================

if HAS_PYDANTIC:

    class TuningConfig(BaseModel):
        """Configuração de auto-tuning."""

        # Hiperparâmetros a tunar
        kappa: float = Field(default=1.0, ge=1.0, le=5.0)
        lambda_c: float = Field(default=0.5, ge=0.0, le=1.0)
        w_U: float = Field(default=0.3, ge=0.0, le=1.0)
        w_S: float = Field(default=0.3, ge=0.0, le=1.0)
        w_C: float = Field(default=0.2, ge=0.0, le=1.0)
        w_L: float = Field(default=0.2, ge=0.0, le=1.0)
        beta_min: float = Field(default=0.01, ge=0.0, le=0.1)

        # Controles de tuning
        max_delta_per_cycle: float = Field(default=0.02, ge=0.001, le=0.05)
        warmup_cycles: int = Field(default=10, ge=5)
        learning_rate: float = Field(default=0.001, ge=0.0001, le=0.01)

        # API preferences
        prefer_provider: str = Field(default="openai")  # openai, mistral, anthropic
        enable_mistral: bool = True
        enable_openai: bool = True
        enable_anthropic: bool = True

        class Config:
            extra = "ignore"

else:

    @dataclass
    class TuningConfig:
        kappa: float = 1.0
        lambda_c: float = 0.5
        w_U: float = 0.3
        w_S: float = 0.3
        w_C: float = 0.2
        w_L: float = 0.2
        beta_min: float = 0.01
        max_delta_per_cycle: float = 0.02
        warmup_cycles: int = 10
        learning_rate: float = 0.001
        prefer_provider: str = "openai"
        enable_mistral: bool = True
        enable_openai: bool = True
        enable_anthropic: bool = True


# ============================================================================
# AdaGrad State
# ============================================================================


@dataclass
class AdaGradState:
    """Estado do otimizador AdaGrad."""

    accumulated_gradients: dict[str, float] = field(default_factory=dict)
    epsilon: float = 1e-8

    def update(self, param_name: str, gradient: float, learning_rate: float) -> float:
        """
        Calcula step adaptativo usando AdaGrad.

        Args:
            param_name: Nome do parâmetro
            gradient: Gradiente calculado
            learning_rate: Taxa de aprendizado base

        Returns:
            Delta para aplicar ao parâmetro
        """
        # Acumular quadrado do gradiente
        if param_name not in self.accumulated_gradients:
            self.accumulated_gradients[param_name] = 0.0

        self.accumulated_gradients[param_name] += gradient**2

        # Step adaptativo
        adjusted_lr = learning_rate / (
            (self.accumulated_gradients[param_name] + self.epsilon) ** 0.5
        )

        return -adjusted_lr * gradient


# ============================================================================
# Mistral AI Fine-Tuning
# ============================================================================


class MistralTuner:
    """Auto-tuner usando Mistral AI API."""

    def __init__(self, api_key: str, model: str = "codestral-latest"):
        if not HAS_MISTRAL:
            raise ImportError("mistralai package not installed")

        self.client = MistralClient(api_key=api_key)
        self.model = model
        self.jobs = []

    def prepare_training_data(
        self, cycles: list[dict[str, Any]], output_path: str = "/tmp/mistral_tuning.jsonl"
    ) -> str:
        """
        Prepara dados de treinamento no formato Mistral (instruct).

        Args:
            cycles: Lista de ciclos com métricas e hiperparâmetros
            output_path: Caminho do arquivo JSONL

        Returns:
            Path do arquivo criado
        """
        training_data = []

        for cycle in cycles:
            # Extrair estado e resultado
            params = cycle.get("hyperparams", {})
            metrics = cycle.get("metrics", {})

            L_inf = metrics.get("L_inf", 0.0)
            delta_L_inf = metrics.get("delta_L_inf", 0.0)

            # Criar exemplo de instrução
            messages = [
                {
                    "role": "user",
                    "content": (
                        f"Given hyperparameters κ={params.get('kappa', 1.0):.3f}, "
                        f"λ_c={params.get('lambda_c', 0.5):.3f}, "
                        f"w_U={params.get('w_U', 0.3):.3f}, "
                        f"w_S={params.get('w_S', 0.3):.3f}, "
                        f"w_C={params.get('w_C', 0.2):.3f}, "
                        f"w_L={params.get('w_L', 0.2):.3f}, "
                        f"β_min={params.get('beta_min', 0.01):.4f}, "
                        f"the system achieved L∞={L_inf:.4f} with ΔL∞={delta_L_inf:.4f}. "
                        "Suggest improved hyperparameters to maximize L∞."
                    ),
                },
                {
                    "role": "assistant",
                    "content": self._generate_assistant_response(params, metrics),
                },
            ]

            training_data.append({"messages": messages})

        # Escrever JSONL
        path = Path(output_path)
        with path.open("w") as f:
            for item in training_data:
                f.write(json.dumps(item) + "\n")

        logger.info(
            f"Mistral training data prepared: {output_path} ({len(training_data)} examples)"
        )
        return str(path)

    def _generate_assistant_response(self, params: dict, metrics: dict) -> str:
        """Gera resposta do assistente baseada em heurísticas."""
        delta_L = metrics.get("delta_L_inf", 0.0)

        suggestions = []

        # Heurísticas simples para demonstração
        if delta_L < 0.01:
            suggestions.append("Increase κ slightly to boost exploration.")
        if metrics.get("cost", 0) > 0.8:
            suggestions.append("Decrease w_C weight to reduce cost sensitivity.")
        if metrics.get("stability", 0) < 0.9:
            suggestions.append("Increase w_S to prioritize stability.")

        if not suggestions:
            suggestions.append("Current hyperparameters are well-tuned. Minor adjustments only.")

        return " ".join(suggestions)

    def start_fine_tune(self, training_file_id: str) -> str:
        """
        Inicia job de fine-tuning no Mistral.

        Args:
            training_file_id: ID do arquivo de treino (já uploadado)

        Returns:
            Job ID
        """
        job = self.client.fine_tuning.jobs.create(
            model="open-mistral-7b",
            training_files=[{"file_id": training_file_id, "weight": 1}],
            hyperparameters={"training_steps": 10, "learning_rate": 0.0001},
            auto_start=True,
        )

        self.jobs.append(job.id)
        logger.info(f"Mistral fine-tune job started: {job.id}")
        return job.id

    def query_tuned_model(self, model_id: str, current_state: dict) -> dict[str, float]:
        """
        Consulta modelo tunado para sugerir novos hiperparâmetros.

        Args:
            model_id: ID do modelo fine-tunado
            current_state: Estado atual dos hiperparâmetros

        Returns:
            Novos hiperparâmetros sugeridos
        """
        prompt = (
            f"Current state: κ={current_state.get('kappa', 1.0):.3f}, "
            f"λ_c={current_state.get('lambda_c', 0.5):.3f}. "
            "Suggest optimized values."
        )

        response = self.client.chat.complete(
            model=model_id, messages=[{"role": "user", "content": prompt}]
        )

        # Parse resposta (simplificado)
        content = response.choices[0].message.content
        logger.info(f"Mistral suggestion: {content}")

        # Retornar estado atual com pequeno ajuste (placeholder)
        return {k: v * 1.01 for k, v in current_state.items()}


# ============================================================================
# OpenAI Fine-Tuning (RFT/DPO/SFT)
# ============================================================================


class OpenAITuner:
    """Auto-tuner usando OpenAI API (RFT/DPO/SFT)."""

    def __init__(self, api_key: str, model: str = "gpt-4.1-nano-2025-04-14"):
        if not HAS_OPENAI:
            raise ImportError("openai package not installed")

        self.client = OpenAIClient(api_key=api_key)
        self.model = model
        self.jobs = []

    def prepare_sft_data(
        self, cycles: list[dict[str, Any]], output_path: str = "/tmp/openai_sft.jsonl"
    ) -> str:
        """Prepara dados para Supervised Fine-Tuning."""
        training_data = []

        for cycle in cycles:
            params = cycle.get("hyperparams", {})
            metrics = cycle.get("metrics", {})

            messages = [
                {"role": "user", "content": self._format_state(params, metrics)},
                {"role": "assistant", "content": self._format_optimized_params(params, metrics)},
            ]

            training_data.append({"messages": messages})

        path = Path(output_path)
        with path.open("w") as f:
            for item in training_data:
                f.write(json.dumps(item) + "\n")

        logger.info(f"OpenAI SFT data prepared: {output_path}")
        return str(path)

    def prepare_dpo_data(
        self, cycles: list[dict[str, Any]], output_path: str = "/tmp/openai_dpo.jsonl"
    ) -> str:
        """Prepara dados para Direct Preference Optimization."""
        training_data = []

        # Ordenar ciclos por performance
        sorted_cycles = sorted(cycles, key=lambda c: c.get("metrics", {}).get("L_inf", 0))

        for i in range(len(sorted_cycles) - 1):
            worse = sorted_cycles[i]
            better = sorted_cycles[i + 1]

            item = {
                "input": {
                    "messages": [
                        {"role": "user", "content": "Optimize hyperparameters for maximum L∞."}
                    ]
                },
                "preferred_output": [
                    {
                        "role": "assistant",
                        "content": self._format_optimized_params(
                            better["hyperparams"], better["metrics"]
                        ),
                    }
                ],
                "non_preferred_output": [
                    {
                        "role": "assistant",
                        "content": self._format_optimized_params(
                            worse["hyperparams"], worse["metrics"]
                        ),
                    }
                ],
            }

            training_data.append(item)

        path = Path(output_path)
        with path.open("w") as f:
            for item in training_data:
                f.write(json.dumps(item) + "\n")

        logger.info(f"OpenAI DPO data prepared: {output_path}")
        return str(path)

    def _format_state(self, params: dict, metrics: dict) -> str:
        """Formata estado atual como prompt."""
        return (
            f"Hyperparameters: κ={params.get('kappa', 1.0):.3f}, "
            f"λ_c={params.get('lambda_c', 0.5):.3f}, "
            f"weights=[{params.get('w_U', 0.3):.2f}, {params.get('w_S', 0.3):.2f}, "
            f"{params.get('w_C', 0.2):.2f}, {params.get('w_L', 0.2):.2f}]. "
            f"Current L∞={metrics.get('L_inf', 0.0):.4f}. Optimize."
        )

    def _format_optimized_params(self, params: dict, metrics: dict) -> str:
        """Formata parâmetros otimizados como JSON."""
        return json.dumps(
            {
                "kappa": params.get("kappa", 1.0),
                "lambda_c": params.get("lambda_c", 0.5),
                "w_U": params.get("w_U", 0.3),
                "w_S": params.get("w_S", 0.3),
                "w_C": params.get("w_C", 0.2),
                "w_L": params.get("w_L", 0.2),
                "beta_min": params.get("beta_min", 0.01),
            }
        )

    def start_fine_tune(self, training_file_id: str, method: str = "supervised") -> str:
        """
        Inicia fine-tuning job.

        Args:
            training_file_id: ID do arquivo (já uploadado via files API)
            method: 'supervised', 'dpo', ou 'reinforcement'

        Returns:
            Job ID
        """
        job_params = {"training_file": training_file_id, "model": self.model}

        if method == "dpo":
            job_params["method"] = {"type": "dpo", "dpo": {"hyperparameters": {"beta": 0.1}}}
        elif method == "reinforcement":
            # RFT requer grader - placeholder
            logger.warning("RFT requires grader configuration - using SFT instead")
            method = "supervised"

        job = self.client.fine_tuning.jobs.create(**job_params)

        self.jobs.append(job.id)
        logger.info(f"OpenAI {method} fine-tune job started: {job.id}")
        return job.id


# ============================================================================
# Anthropic Tuner (Prompt Optimization)
# ============================================================================


class AnthropicTuner:
    """
    Auto-tuner usando Anthropic Claude.

    Nota: Anthropic não tem fine-tuning API pública, então usamos
    prompt optimization + few-shot learning.
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-1-20250805"):
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic package not installed")

        self.client = AnthropicClient(api_key=api_key)
        self.model = model

    def optimize_hyperparameters(
        self, cycles: list[dict[str, Any]], current_state: dict[str, float]
    ) -> dict[str, float]:
        """
        Usa Claude para sugerir hiperparâmetros ótimos via few-shot.

        Args:
            cycles: Histórico de ciclos
            current_state: Estado atual

        Returns:
            Novos hiperparâmetros sugeridos
        """
        # Construir few-shot examples
        examples = self._build_few_shot_examples(cycles)

        prompt = f"""You are an expert in hyperparameter optimization for reinforcement learning systems.

Previous optimization history:
{examples}

Current state:
{json.dumps(current_state, indent=2)}

Suggest optimized hyperparameters to maximize L∞ score while maintaining:
- ECE ≤ 0.01 (calibration)
- ρ_bias ≤ 1.05 (fairness)
- Cost efficiency
- Stability

Return ONLY a JSON object with suggested values."""

        message = self.client.messages.create(
            model=self.model, max_tokens=1024, messages=[{"role": "user", "content": prompt}]
        )

        # Parse resposta
        response_text = message.content[0].text

        try:
            suggested = json.loads(response_text)
            logger.info(f"Anthropic suggestion: {suggested}")
            return suggested
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Anthropic response: {response_text}")
            return current_state

    def _build_few_shot_examples(self, cycles: list[dict]) -> str:
        """Constrói exemplos few-shot do histórico."""
        examples = []

        for i, cycle in enumerate(cycles[-5:]):  # Últimos 5 ciclos
            params = cycle.get("hyperparams", {})
            metrics = cycle.get("metrics", {})

            examples.append(
                f"Cycle {i+1}: κ={params.get('kappa', 1.0):.3f}, "
                f"λ_c={params.get('lambda_c', 0.5):.3f} → L∞={metrics.get('L_inf', 0.0):.4f}"
            )

        return "\n".join(examples)


# ============================================================================
# Tuner Orquestrador
# ============================================================================


class AutoTuner:
    """Orquestrador de auto-tuning multi-provider."""

    def __init__(self, config: TuningConfig):
        self.config = config
        self.state = AdaGradState()
        self.cycle_count = 0
        self.history: list[dict] = []

        # Inicializar clientes
        self.mistral_tuner = None
        self.openai_tuner = None
        self.anthropic_tuner = None

        if config.enable_mistral and HAS_MISTRAL:
            mistral_key = os.getenv("MISTRAL_API_KEY")
            if mistral_key:
                self.mistral_tuner = MistralTuner(mistral_key)

        if config.enable_openai and HAS_OPENAI:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.openai_tuner = OpenAITuner(openai_key)

        if config.enable_anthropic and HAS_ANTHROPIC:
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key:
                self.anthropic_tuner = AnthropicTuner(anthropic_key)

    def update(self, metrics: dict[str, float]) -> dict[str, float]:
        """
        Atualiza hiperparâmetros baseado em métricas observadas.

        Args:
            metrics: Métricas do ciclo atual (L_inf, delta_L_inf, etc.)

        Returns:
            Novos hiperparâmetros
        """
        self.cycle_count += 1

        # Registrar no histórico
        self.history.append(
            {
                "cycle": self.cycle_count,
                "hyperparams": {
                    "kappa": self.config.kappa,
                    "lambda_c": self.config.lambda_c,
                    "w_U": self.config.w_U,
                    "w_S": self.config.w_S,
                    "w_C": self.config.w_C,
                    "w_L": self.config.w_L,
                    "beta_min": self.config.beta_min,
                },
                "metrics": metrics,
            }
        )

        # Warmup: não tunar ainda
        if self.cycle_count < self.config.warmup_cycles:
            logger.info(f"Warmup cycle {self.cycle_count}/{self.config.warmup_cycles}")
            return self._get_current_hyperparams()

        # Calcular gradientes (simplificado: usar ΔL∞ como sinal)
        delta_L = metrics.get("delta_L_inf", 0.0)

        # AdaGrad updates com clipping
        updates = {}
        for param_name in ["kappa", "lambda_c", "w_U", "w_S", "w_C", "w_L", "beta_min"]:
            gradient = -delta_L  # Queremos maximizar L∞
            delta = self.state.update(param_name, gradient, self.config.learning_rate)

            # Clip delta
            delta = max(
                -self.config.max_delta_per_cycle, min(self.config.max_delta_per_cycle, delta)
            )

            updates[param_name] = delta

        # Aplicar updates com bounds
        self.config.kappa = self._clip(self.config.kappa + updates["kappa"], 1.0, 5.0)
        self.config.lambda_c = self._clip(self.config.lambda_c + updates["lambda_c"], 0.0, 1.0)
        self.config.w_U = self._clip(self.config.w_U + updates["w_U"], 0.0, 1.0)
        self.config.w_S = self._clip(self.config.w_S + updates["w_S"], 0.0, 1.0)
        self.config.w_C = self._clip(self.config.w_C + updates["w_C"], 0.0, 1.0)
        self.config.w_L = self._clip(self.config.w_L + updates["w_L"], 0.0, 1.0)
        self.config.beta_min = self._clip(self.config.beta_min + updates["beta_min"], 0.0, 0.1)

        # Normalizar weights para somar 1.0
        total_w = self.config.w_U + self.config.w_S + self.config.w_C + self.config.w_L
        if total_w > 0:
            self.config.w_U /= total_w
            self.config.w_S /= total_w
            self.config.w_C /= total_w
            self.config.w_L /= total_w

        logger.info(
            f"Auto-tuned hyperparams (cycle {self.cycle_count}): {self._get_current_hyperparams()}"
        )

        return self._get_current_hyperparams()

    def _clip(self, value: float, min_val: float, max_val: float) -> float:
        """Clip valor dentro de range."""
        return max(min_val, min(max_val, value))

    def _get_current_hyperparams(self) -> dict[str, float]:
        """Retorna hiperparâmetros atuais."""
        return {
            "kappa": self.config.kappa,
            "lambda_c": self.config.lambda_c,
            "w_U": self.config.w_U,
            "w_S": self.config.w_S,
            "w_C": self.config.w_C,
            "w_L": self.config.w_L,
            "beta_min": self.config.beta_min,
        }

    def save_state(self, path: str = "/tmp/tuner_state.json") -> None:
        """Persiste estado do tuner."""
        state = {
            "config": self._get_current_hyperparams(),
            "cycle_count": self.cycle_count,
            "history": self.history,
            "adagrad_state": {"accumulated_gradients": self.state.accumulated_gradients},
        }

        with open(path, "w") as f:
            json.dump(state, f, indent=2)

        logger.info(f"Tuner state saved: {path}")

    def load_state(self, path: str = "/tmp/tuner_state.json") -> None:
        """Carrega estado do tuner."""
        if not Path(path).exists():
            logger.warning(f"Tuner state not found: {path}")
            return

        with open(path) as f:
            state = json.load(f)

        # Restaurar config
        for k, v in state["config"].items():
            setattr(self.config, k, v)

        self.cycle_count = state["cycle_count"]
        self.history = state["history"]
        self.state.accumulated_gradients = state["adagrad_state"]["accumulated_gradients"]

        logger.info(f"Tuner state loaded: {path}")
