"""
PENIN-Ω Core Orchestrator
==========================

Main orchestrator for the auto-evolution system with state persistence.
Implements Phase 2: Persistence and Resilience.
Implements Phase 4: The Forge of Hephaestus (CMA-ES local optimization).
"""

from __future__ import annotations

import json
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from penin.core.artifacts import NumericVectorArtifact
from penin.core.serialization import StateEncoder, state_decoder


class OmegaMetaOrchestrator:
    """
    Ω-META Orchestrator with long-term memory.

    Manages:
    - Knowledge base (NumericVectorArtifact objects)
    - Task history (deque)
    - Score history (deque)
    - State persistence (save/load)

    Features:
    - Serialization/deserialization of custom types
    - Graceful handling of missing state files
    - Fail-safe state management
    """

    def __init__(
        self,
        history_maxlen: int = 1000,
    ):
        """
        Initialize orchestrator.

        Args:
            history_maxlen: Maximum length for history deques
        """
        self.knowledge_base: dict[str, NumericVectorArtifact] = {}
        self.task_history: deque = deque(maxlen=history_maxlen)
        self.score_history: deque = deque(maxlen=history_maxlen)

    def add_knowledge(self, key: str, artifact: NumericVectorArtifact) -> None:
        """
        Add knowledge artifact to the knowledge base.

        Args:
            key: Unique identifier for the artifact
            artifact: NumericVectorArtifact to store
        """
        self.knowledge_base[key] = artifact

    def add_task(self, task: dict[str, Any]) -> None:
        """
        Add task to history.

        Args:
            task: Task information dictionary
        """
        self.task_history.append(task)

    def add_score(self, score: float) -> None:
        """
        Add score to history.

        Args:
            score: Performance score
        """
        self.score_history.append(score)

    def save_state(self, filepath: str) -> None:
        """
        Save current state to file.

        Args:
            filepath: Path to save state file

        Raises:
            IOError: If file cannot be written
        """
        state = {
            "knowledge_base": self.knowledge_base,
            "task_history": self.task_history,
            "score_history": self.score_history,
        }

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(state, f, cls=StateEncoder, indent=2)

    def load_state(self, filepath: str) -> bool:
        """
        Load state from file.

        Args:
            filepath: Path to state file

        Returns:
            True if state was loaded, False if file doesn't exist

        Raises:
            IOError: If file exists but cannot be read
            json.JSONDecodeError: If file contains invalid JSON
        """
        path = Path(filepath)

        if not path.exists():
            return False

        with open(filepath) as f:
            state = json.load(f, object_hook=state_decoder)

        self.knowledge_base = state.get("knowledge_base", {})
        self.task_history = state.get(
            "task_history", deque(maxlen=self.task_history.maxlen)
        )
        self.score_history = state.get(
            "score_history", deque(maxlen=self.score_history.maxlen)
        )

        return True

    def get_statistics(self) -> dict[str, Any]:
        """
        Get orchestrator statistics.

        Returns:
            Dictionary with current state statistics
        """
        return {
            "knowledge_base_size": len(self.knowledge_base),
            "task_history_size": len(self.task_history),
            "score_history_size": len(self.score_history),
            "avg_score": (
                sum(self.score_history) / len(self.score_history)
                if self.score_history
                else 0.0
            ),
        }

    def _initiate_local_training(
        self,
        evaluate_artifact: Callable[[NumericVectorArtifact], float],
        max_generations: int = 50,
        sigma0: float = 0.5,
        popsize: int | None = None,
    ) -> NumericVectorArtifact:
        """
        Initiate local training using CMA-ES optimization.

        This implements Phase 4: The Forge of Hephaestus - a sophisticated local
        optimization algorithm to cure "Primitive Local Intelligence".

        Args:
            evaluate_artifact: Function that evaluates a NumericVectorArtifact and
                             returns a score (lower is better for CMA-ES)
            max_generations: Maximum number of CMA-ES generations (default: 50)
            sigma0: Initial standard deviation for CMA-ES (default: 0.5)
            popsize: Population size (default: None, auto-determined by CMA-ES)

        Returns:
            NumericVectorArtifact: Optimized artifact found by CMA-ES

        Raises:
            ValueError: If knowledge_base is empty or contains no valid artifacts
        """
        import cma

        # Step 1: Select starting point from knowledge base
        if not self.knowledge_base:
            raise ValueError("Knowledge base is empty. Cannot initiate local training.")

        # Find best artifact (lowest score)
        best_key = None
        best_score = float("inf")

        for key, artifact in self.knowledge_base.items():
            score = evaluate_artifact(artifact)
            if score < best_score:
                best_score = score
                best_key = key

        if best_key is None:
            raise ValueError("No valid artifacts found in knowledge base.")

        best_artifact = self.knowledge_base[best_key]
        x0 = np.array(best_artifact.vector, dtype=float)

        # Step 2: Configure the optimizer
        opts = {"maxiter": max_generations, "verbose": -9}  # -9 = silent
        if popsize is not None:
            opts["popsize"] = popsize

        es = cma.CMAEvolutionStrategy(x0, sigma0, opts)

        # Step 3: Run the optimization loop
        generation = 0
        while not es.stop() and generation < max_generations:
            # Ask for new population of candidate solutions
            solutions = es.ask()

            # Evaluate each candidate
            fitness_scores = []
            for solution in solutions:
                candidate_artifact = NumericVectorArtifact(
                    vector=solution.tolist(),
                    metadata={"generation": generation, "method": "cma-es"},
                )
                score = evaluate_artifact(candidate_artifact)
                fitness_scores.append(score)

            # Tell optimizer the results
            es.tell(solutions, fitness_scores)
            generation += 1

        # Step 4: Harvest the result
        best_solution = es.result.xbest

        # Step 5: Return the innovation
        optimized_artifact = NumericVectorArtifact(
            vector=best_solution.tolist(),
            metadata={
                "method": "cma-es",
                "generations": generation,
                "final_sigma": es.sigma,
                "starting_point": best_key,
            },
        )

        return optimized_artifact
