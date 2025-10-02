"""
PENIN-Ω Core Orchestrator
==========================

Main orchestrator for the auto-evolution system with state persistence.
Implements Phase 2: Persistence and Resilience.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

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
            
        with open(filepath, "r") as f:
            state = json.load(f, object_hook=state_decoder)
            
        self.knowledge_base = state.get("knowledge_base", {})
        self.task_history = state.get("task_history", deque(maxlen=self.task_history.maxlen))
        self.score_history = state.get("score_history", deque(maxlen=self.score_history.maxlen))
        
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
            "avg_score": sum(self.score_history) / len(self.score_history) if self.score_history else 0.0,
        }
