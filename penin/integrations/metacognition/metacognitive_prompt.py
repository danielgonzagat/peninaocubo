"""
Metacognitive-Prompting Integration (NAACL 2024).

Repository: https://github.com/EternityYW/Metacognitive-Prompting
Technology: 5-stage metacognitive reasoning framework
Performance: Significant improvements across 5 major LLMs
Publication: NAACL 2024

Integration with PENIN-Ω:
- Enhance SR-Ω∞ reflection scoring with structured metacognition
- Improve CAOS+ consistency metrics via multi-stage reasoning
- Multi-stage decision validation for Σ-Guard
- Confidence calibration for uncertainty quantification

References:
- Paper: "Metacognitive Prompting Improves LLM Understanding of User-Provided Context" (NAACL 2024)
- GitHub: https://github.com/EternityYW/Metacognitive-Prompting
- Stages: Understanding → Judgment → Evaluation → Decision → Confidence
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any

from pydantic import Field

from penin.integrations.base import (
    BaseIntegrationAdapter,
    IntegrationConfig,
    IntegrationExecutionError,
    IntegrationInitializationError,
    IntegrationPriority,
    IntegrationStatus,
)

logger = logging.getLogger(__name__)


class MetacognitiveStage(str, Enum):
    """Five stages of metacognitive reasoning"""

    UNDERSTANDING = "understanding"  # Comprehend context and task
    JUDGMENT = "judgment"  # Assess relevance and quality
    EVALUATION = "evaluation"  # Evaluate options and constraints
    DECISION = "decision"  # Make informed decision
    CONFIDENCE = "confidence"  # Quantify certainty


class MetacognitivePromptConfig(IntegrationConfig):
    """Configuration for Metacognitive-Prompting integration"""

    priority: IntegrationPriority = Field(default=IntegrationPriority.P1_CRITICAL)

    # Metacognitive stages
    enable_all_stages: bool = Field(
        default=True, description="Enable all 5 metacognitive stages"
    )
    custom_stages: list[MetacognitiveStage] | None = Field(
        default=None,
        description="Custom subset of stages (overrides enable_all_stages)",
    )

    # Reasoning depth
    reasoning_depth: int = Field(
        default=2, ge=1, le=5, description="Depth of recursive reasoning per stage"
    )
    enable_self_critique: bool = Field(
        default=True, description="Enable self-critique loops"
    )
    max_critique_iterations: int = Field(
        default=3, ge=1, le=10, description="Max self-critique iterations"
    )

    # Integration with PENIN-Ω
    integrate_with_sr: bool = Field(
        default=True, description="Integrate with SR-Ω∞ scoring"
    )
    integrate_with_caos: bool = Field(
        default=True, description="Integrate with CAOS+ consistency"
    )
    integrate_with_sigma_guard: bool = Field(
        default=True, description="Integrate with Σ-Guard validation"
    )

    # Confidence calibration
    enable_confidence_calibration: bool = Field(
        default=True, description="Calibrate confidence scores to reduce ECE"
    )
    temperature_scaling: bool = Field(
        default=True, description="Apply temperature scaling for calibration"
    )


class MetacognitiveReasoner(BaseIntegrationAdapter):
    """
    Adapter for Metacognitive-Prompting framework.

    Enables PENIN-Ω to:
    1. Perform structured 5-stage metacognitive reasoning
    2. Enhance SR-Ω∞ with explicit self-awareness
    3. Improve consistency metrics for CAOS+
    4. Validate decisions multi-stage for Σ-Guard
    5. Calibrate confidence for uncertainty quantification
    """

    def __init__(self, config: MetacognitivePromptConfig | None = None):
        super().__init__(config or MetacognitivePromptConfig())
        self.config: MetacognitivePromptConfig = self.config  # type narrowing
        self._llm_client = None
        self._calibration_params = {"temperature": 1.0, "scale": 1.0}

    def is_available(self) -> bool:
        """
        Check if dependencies are available.

        Note: Metacognitive-Prompting is primarily a prompting technique,
        so availability depends on having an LLM client available.
        """
        # Always available as it's a prompting technique
        return True

    def initialize(self) -> bool:
        """Initialize metacognitive reasoning engine"""
        try:
            # Initialize prompting templates for each stage
            self._stage_templates = self._load_stage_templates()

            # Initialize confidence calibration if enabled
            if self.config.enable_confidence_calibration:
                self._calibration_params = self._initialize_calibration()

            self.status = IntegrationStatus.INITIALIZED
            self._initialized = True
            logger.info(
                f"Metacognitive-Prompting initialized: "
                f"stages={len(self._get_active_stages())}, "
                f"depth={self.config.reasoning_depth}"
            )
            return True

        except Exception as e:
            self.status = IntegrationStatus.FAILED
            raise IntegrationInitializationError(
                "metacognitive", f"Initialization failed: {e}", e
            ) from e

    def _load_stage_templates(self) -> dict[MetacognitiveStage, str]:
        """
        Load prompting templates for each metacognitive stage.

        Based on NAACL 2024 paper methodology.
        """
        return {
            MetacognitiveStage.UNDERSTANDING: """
# Stage 1: Understanding
Carefully read and comprehend the following context, task, and constraints.

Context: {context}
Task: {task}
Constraints: {constraints}

Demonstrate your understanding by:
1. Identifying key concepts and relationships
2. Restating the task in your own words
3. Noting any ambiguities or uncertainties
""",
            MetacognitiveStage.JUDGMENT: """
# Stage 2: Judgment
Assess the relevance and quality of available information.

Available Information: {information}

Judge each piece by:
1. Relevance to the task (0-1 score)
2. Quality and reliability (0-1 score)
3. Potential biases or limitations
4. Information gaps that need addressing
""",
            MetacognitiveStage.EVALUATION: """
# Stage 3: Evaluation
Evaluate possible approaches and their trade-offs.

Possible Approaches: {approaches}
Evaluation Criteria: {criteria}

For each approach:
1. Assess alignment with task goals
2. Identify strengths and weaknesses
3. Estimate likelihood of success
4. Note resource requirements
""",
            MetacognitiveStage.DECISION: """
# Stage 4: Decision
Make an informed decision based on prior stages.

Understanding: {understanding}
Judgment: {judgment}
Evaluation: {evaluation}

Provide:
1. Your decision with clear justification
2. Key factors influencing the decision
3. Potential risks and mitigation strategies
4. Expected outcomes
""",
            MetacognitiveStage.CONFIDENCE: """
# Stage 5: Confidence
Quantify your confidence in the decision.

Decision: {decision}
Reasoning: {reasoning}

Provide:
1. Confidence score (0-1, calibrated)
2. Sources of uncertainty
3. Conditions that would change your confidence
4. Epistemic vs. aleatoric uncertainty breakdown
""",
        }

    def _initialize_calibration(self) -> dict[str, float]:
        """
        Initialize confidence calibration parameters.

        Uses temperature scaling by default (Guo et al., 2017).
        """
        logger.info("Initializing confidence calibration (temperature scaling)")
        # TODO: Learn optimal temperature from validation set
        # For now, use default temperature=1.0
        return {"temperature": 1.0, "scale": 1.0}

    def _get_active_stages(self) -> list[MetacognitiveStage]:
        """Get list of active metacognitive stages"""
        if self.config.custom_stages is not None:
            return self.config.custom_stages
        elif self.config.enable_all_stages:
            return list(MetacognitiveStage)
        else:
            return [MetacognitiveStage.UNDERSTANDING, MetacognitiveStage.DECISION]

    def get_status(self) -> dict[str, Any]:
        """Get current status of Metacognitive-Prompting integration"""
        return {
            "adapter": "Metacognitive-Prompting",
            "status": self.status.value,
            "available": self.is_available(),
            "initialized": self._initialized,
            "active_stages": [s.value for s in self._get_active_stages()],
            "reasoning_depth": self.config.reasoning_depth,
            "self_critique_enabled": self.config.enable_self_critique,
            "confidence_calibration": self.config.enable_confidence_calibration,
            "metrics": self.get_metrics(),
        }

    async def execute(
        self,
        operation: str,
        prompt: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute metacognitive reasoning operation.

        Args:
            operation: Operation type ("reason", "validate", "calibrate")
            prompt: Input prompt/query
            context: Additional context dictionary

        Returns:
            Dictionary with reasoning results and metadata

        Raises:
            IntegrationExecutionError: On failure
        """
        if not self._initialized:
            raise IntegrationExecutionError("metacognitive", "Adapter not initialized")

        start_time = time.time()
        try:
            if operation == "reason":
                result = await self._full_reasoning_chain(prompt, context or {})
            elif operation == "validate":
                result = await self._validate_decision(prompt, context or {})
            elif operation == "calibrate":
                result = await self._calibrate_confidence(context or {})
            else:
                raise ValueError(f"Unknown operation: {operation}")

            latency_ms = (time.time() - start_time) * 1000
            self.record_invocation(success=True, latency_ms=latency_ms)
            self.status = IntegrationStatus.ACTIVE

            return result

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.record_invocation(success=False, latency_ms=latency_ms)
            self.status = IntegrationStatus.FAILED

            if self.config.fail_open:
                logger.warning(f"Metacognitive reasoning failed (fail-open): {e}")
                return {
                    "status": "failed",
                    "fallback": True,
                    "decision": None,
                    "confidence": 0.0,
                }
            else:
                raise IntegrationExecutionError(
                    "metacognitive", f"Execution failed: {e}", e
                ) from e

    async def _full_reasoning_chain(
        self, prompt: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute full 5-stage metacognitive reasoning chain.

        Placeholder implementation - will integrate with actual LLM calls.
        """
        logger.info("Executing full metacognitive reasoning chain")

        stages_output = {}
        active_stages = self._get_active_stages()

        for stage in active_stages:
            stage_prompt = self._stage_templates[stage].format(
                context=context.get("context", ""),
                task=prompt,
                constraints=context.get("constraints", ""),
                information=context.get("information", ""),
                approaches=context.get("approaches", ""),
                criteria=context.get("criteria", ""),
                understanding=stages_output.get("understanding", ""),
                judgment=stages_output.get("judgment", ""),
                evaluation=stages_output.get("evaluation", ""),
                decision=stages_output.get("decision", ""),
                reasoning=stages_output.get("reasoning", ""),
            )

            # TODO: Call actual LLM with stage_prompt
            # For now, placeholder
            stage_result = await self._execute_stage(stage, stage_prompt)
            stages_output[stage.value] = stage_result

        # Extract final decision and confidence
        decision = stages_output.get("decision", {}).get("decision")
        confidence_raw = stages_output.get("confidence", {}).get(
            "confidence_score", 0.5
        )

        # Apply calibration
        confidence_calibrated = self._apply_calibration(confidence_raw)

        return {
            "reasoning_id": f"metacog_{int(time.time())}",
            "prompt": prompt,
            "stages": stages_output,
            "decision": decision,
            "confidence_raw": confidence_raw,
            "confidence_calibrated": confidence_calibrated,
            "calibration_params": self._calibration_params,
            "metadata": {
                "active_stages": [s.value for s in active_stages],
                "reasoning_depth": self.config.reasoning_depth,
                "timestamp": time.time(),
            },
        }

    async def _execute_stage(
        self, stage: MetacognitiveStage, prompt: str
    ) -> dict[str, Any]:
        """
        Execute single metacognitive stage.

        Placeholder - will call actual LLM.
        """
        # TODO: Implement actual LLM call with self-critique loops if enabled
        # Example:
        # response = await self._llm_client.generate(prompt, max_tokens=500)
        # if self.config.enable_self_critique:
        #     response = await self._self_critique_loop(prompt, response)

        # Placeholder response
        return {
            "stage": stage.value,
            "output": f"[Placeholder output for {stage.value} stage]",
            "confidence_score": 0.75,
            "critique_iterations": 0,
        }

    async def _validate_decision(
        self, decision: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate a decision using metacognitive stages.

        Useful for Σ-Guard integration.
        """
        logger.info("Validating decision via metacognitive reasoning")

        # Run judgment and evaluation stages on the decision
        validation_result = await self._full_reasoning_chain(
            f"Validate: {decision}", context
        )

        return {
            "validation_id": f"metacog_val_{int(time.time())}",
            "decision": decision,
            "valid": validation_result["confidence_calibrated"] > 0.7,
            "confidence": validation_result["confidence_calibrated"],
            "reasoning": validation_result["stages"],
            "metadata": {"timestamp": time.time()},
        }

    async def _calibrate_confidence(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Calibrate confidence scores to reduce ECE.

        Uses temperature scaling or Platt scaling.
        """
        logger.info("Calibrating confidence scores (placeholder)")

        # TODO: Implement actual calibration on validation set
        # Learn optimal temperature T that minimizes ECE

        return {
            "calibration_id": f"metacog_calib_{int(time.time())}",
            "method": (
                "temperature_scaling" if self.config.temperature_scaling else "none"
            ),
            "params": self._calibration_params,
            "ece_before": 0.15,  # Placeholder
            "ece_after": 0.008,  # Placeholder (calibrated)
            "metadata": {"timestamp": time.time()},
        }

    def _apply_calibration(self, confidence_raw: float) -> float:
        """
        Apply calibration to raw confidence score.

        Uses learned temperature scaling parameters.
        """
        if not self.config.enable_confidence_calibration:
            return confidence_raw

        # Temperature scaling: conf_calibrated = softmax(logit / T)
        # Simplified: scale confidence directly
        import math

        T = self._calibration_params["temperature"]
        logit = math.log(
            confidence_raw / (1 - confidence_raw + 1e-9)
        )  # Convert prob to logit
        calibrated_logit = logit / T
        confidence_calibrated = 1.0 / (1.0 + math.exp(-calibrated_logit))  # Sigmoid

        return max(0.0, min(1.0, confidence_calibrated))

    async def reason(
        self,
        prompt: str,
        stages: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        High-level interface for metacognitive reasoning.

        Args:
            prompt: Query/task to reason about
            stages: Specific stages to execute (optional)
            context: Additional context

        Returns:
            Reasoning result with decision and confidence
        """
        logger.info(f"Starting metacognitive reasoning: {prompt[:100]}...")

        # Override stages if specified
        original_stages = self.config.custom_stages
        if stages:
            self.config.custom_stages = [MetacognitiveStage(s) for s in stages]

        try:
            result = await self.execute("reason", prompt=prompt, context=context or {})
            return result
        finally:
            # Restore original stages
            self.config.custom_stages = original_stages


__all__ = ["MetacognitiveReasoner", "MetacognitivePromptConfig", "MetacognitiveStage"]
