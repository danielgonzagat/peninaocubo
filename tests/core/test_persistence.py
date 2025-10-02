"""
Tests for PENIN-Ω State Persistence
====================================

Tests for state serialization, deserialization, and persistence.
"""

from __future__ import annotations

import json
import tempfile
from collections import deque
from pathlib import Path

from penin.core import (
    NumericVectorArtifact,
    OmegaMetaOrchestrator,
    StateEncoder,
    state_decoder,
)


class TestNumericVectorArtifact:
    """Test NumericVectorArtifact serialization."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        artifact = NumericVectorArtifact(vector=[0.1, 0.2, 0.3])
        result = artifact.to_dict()

        assert result["__type__"] == "NumericVectorArtifact"
        assert result["vector"] == [0.1, 0.2, 0.3]
        assert result["metadata"] == {}

    def test_to_dict_with_metadata(self):
        """Test conversion to dictionary with metadata."""
        artifact = NumericVectorArtifact(
            vector=[0.4, 0.5, 0.6],
            metadata={"source": "test", "version": 1}
        )
        result = artifact.to_dict()

        assert result["metadata"] == {"source": "test", "version": 1}

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "__type__": "NumericVectorArtifact",
            "vector": [0.7, 0.8, 0.9],
            "metadata": {"test": True}
        }
        artifact = NumericVectorArtifact.from_dict(data)

        assert artifact.vector == [0.7, 0.8, 0.9]
        assert artifact.metadata == {"test": True}

    def test_roundtrip(self):
        """Test roundtrip serialization."""
        original = NumericVectorArtifact(
            vector=[1.0, 2.0, 3.0],
            metadata={"key": "value"}
        )
        data = original.to_dict()
        restored = NumericVectorArtifact.from_dict(data)

        assert restored.vector == original.vector
        assert restored.metadata == original.metadata


class TestStateEncoder:
    """Test custom JSON encoder."""

    def test_encode_artifact(self):
        """Test encoding NumericVectorArtifact."""
        artifact = NumericVectorArtifact(vector=[0.1, 0.2])
        result = json.dumps(artifact, cls=StateEncoder)
        data = json.loads(result)

        assert data["__type__"] == "NumericVectorArtifact"
        assert data["vector"] == [0.1, 0.2]

    def test_encode_deque(self):
        """Test encoding deque."""
        d = deque([1, 2, 3], maxlen=10)
        result = json.dumps(d, cls=StateEncoder)
        data = json.loads(result)

        assert data["__type__"] == "deque"
        assert data["items"] == [1, 2, 3]
        assert data["maxlen"] == 10

    def test_encode_deque_no_maxlen(self):
        """Test encoding deque without maxlen."""
        d = deque([4, 5, 6])
        result = json.dumps(d, cls=StateEncoder)
        data = json.loads(result)

        assert data["__type__"] == "deque"
        assert data["items"] == [4, 5, 6]
        assert data["maxlen"] is None

    def test_encode_nested(self):
        """Test encoding nested structures."""
        data = {
            "artifact": NumericVectorArtifact(vector=[0.5]),
            "history": deque([1, 2], maxlen=5)
        }
        result = json.dumps(data, cls=StateEncoder)
        decoded = json.loads(result)

        assert decoded["artifact"]["__type__"] == "NumericVectorArtifact"
        assert decoded["history"]["__type__"] == "deque"


class TestStateDecoder:
    """Test custom JSON decoder."""

    def test_decode_artifact(self):
        """Test decoding NumericVectorArtifact."""
        data = {
            "__type__": "NumericVectorArtifact",
            "vector": [0.1, 0.2],
            "metadata": {}
        }
        result = state_decoder(data)

        assert isinstance(result, NumericVectorArtifact)
        assert result.vector == [0.1, 0.2]

    def test_decode_deque(self):
        """Test decoding deque."""
        data = {
            "__type__": "deque",
            "items": [1, 2, 3],
            "maxlen": 10
        }
        result = state_decoder(data)

        assert isinstance(result, deque)
        assert list(result) == [1, 2, 3]
        assert result.maxlen == 10

    def test_decode_regular_dict(self):
        """Test decoding regular dictionary."""
        data = {"key": "value", "number": 42}
        result = state_decoder(data)

        assert result == data

    def test_decode_full_json(self):
        """Test decoding full JSON with custom types."""
        json_str = json.dumps({
            "artifact": NumericVectorArtifact(vector=[0.3, 0.4]),
            "history": deque([5, 6, 7], maxlen=20)
        }, cls=StateEncoder)

        result = json.loads(json_str, object_hook=state_decoder)

        assert isinstance(result["artifact"], NumericVectorArtifact)
        assert isinstance(result["history"], deque)
        assert result["artifact"].vector == [0.3, 0.4]
        assert list(result["history"]) == [5, 6, 7]


class TestOmegaMetaOrchestrator:
    """Test OmegaMetaOrchestrator state persistence."""

    def test_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = OmegaMetaOrchestrator()

        assert len(orchestrator.knowledge_base) == 0
        assert len(orchestrator.task_history) == 0
        assert len(orchestrator.score_history) == 0

    def test_add_knowledge(self):
        """Test adding knowledge artifacts."""
        orchestrator = OmegaMetaOrchestrator()
        artifact = NumericVectorArtifact(vector=[0.1, 0.2, 0.3])

        orchestrator.add_knowledge("test_key", artifact)

        assert "test_key" in orchestrator.knowledge_base
        assert orchestrator.knowledge_base["test_key"] == artifact

    def test_add_task(self):
        """Test adding tasks to history."""
        orchestrator = OmegaMetaOrchestrator()
        task = {"task_id": 1, "type": "test", "status": "completed"}

        orchestrator.add_task(task)

        assert len(orchestrator.task_history) == 1
        assert orchestrator.task_history[0] == task

    def test_add_score(self):
        """Test adding scores to history."""
        orchestrator = OmegaMetaOrchestrator()

        orchestrator.add_score(0.85)
        orchestrator.add_score(0.90)

        assert len(orchestrator.score_history) == 2
        assert orchestrator.score_history[0] == 0.85
        assert orchestrator.score_history[1] == 0.90

    def test_save_state(self):
        """Test saving state to file."""
        orchestrator = OmegaMetaOrchestrator()
        orchestrator.add_knowledge(
            "artifact1",
            NumericVectorArtifact(vector=[0.1, 0.2])
        )
        orchestrator.add_task({"task_id": 1})
        orchestrator.add_score(0.75)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            orchestrator.save_state(filepath)

            # Verify file exists and contains valid JSON
            assert Path(filepath).exists()
            with open(filepath) as f:
                data = json.load(f)

            assert "knowledge_base" in data
            assert "task_history" in data
            assert "score_history" in data
        finally:
            Path(filepath).unlink()

    def test_load_state_missing_file(self):
        """Test loading state when file doesn't exist."""
        orchestrator = OmegaMetaOrchestrator()

        result = orchestrator.load_state("/nonexistent/path/state.json")

        assert result is False
        assert len(orchestrator.knowledge_base) == 0

    def test_save_and_load_state(self):
        """Test complete save/load cycle."""
        # Create and populate original orchestrator
        original = OmegaMetaOrchestrator()
        original.add_knowledge(
            "artifact1",
            NumericVectorArtifact(vector=[0.1, 0.2, 0.3])
        )
        original.add_knowledge(
            "artifact2",
            NumericVectorArtifact(vector=[0.4, 0.5, 0.6], metadata={"test": True})
        )
        original.add_task({"task_id": 1, "type": "evolution"})
        original.add_task({"task_id": 2, "type": "evaluation"})
        original.add_score(0.85)
        original.add_score(0.90)
        original.add_score(0.88)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            # Save state
            original.save_state(filepath)

            # Create new orchestrator and load state
            restored = OmegaMetaOrchestrator()
            result = restored.load_state(filepath)

            # Verify load succeeded
            assert result is True

            # Verify knowledge base
            assert len(restored.knowledge_base) == 2
            assert "artifact1" in restored.knowledge_base
            assert "artifact2" in restored.knowledge_base
            assert restored.knowledge_base["artifact1"].vector == [0.1, 0.2, 0.3]
            assert restored.knowledge_base["artifact2"].vector == [0.4, 0.5, 0.6]
            assert restored.knowledge_base["artifact2"].metadata == {"test": True}

            # Verify task history
            assert len(restored.task_history) == 2
            assert restored.task_history[0] == {"task_id": 1, "type": "evolution"}
            assert restored.task_history[1] == {"task_id": 2, "type": "evaluation"}

            # Verify score history
            assert len(restored.score_history) == 3
            assert restored.score_history[0] == 0.85
            assert restored.score_history[1] == 0.90
            assert restored.score_history[2] == 0.88

        finally:
            Path(filepath).unlink()

    def test_history_maxlen(self):
        """Test that history respects maxlen."""
        orchestrator = OmegaMetaOrchestrator(history_maxlen=3)

        # Add more items than maxlen
        for i in range(5):
            orchestrator.add_task({"task_id": i})
            orchestrator.add_score(float(i))

        # Only last 3 items should remain
        assert len(orchestrator.task_history) == 3
        assert len(orchestrator.score_history) == 3
        assert orchestrator.task_history[0]["task_id"] == 2
        assert orchestrator.score_history[0] == 2.0

    def test_get_statistics(self):
        """Test statistics calculation."""
        orchestrator = OmegaMetaOrchestrator()
        orchestrator.add_knowledge("k1", NumericVectorArtifact(vector=[0.1]))
        orchestrator.add_knowledge("k2", NumericVectorArtifact(vector=[0.2]))
        orchestrator.add_task({"task_id": 1})
        orchestrator.add_score(0.8)
        orchestrator.add_score(0.9)

        stats = orchestrator.get_statistics()

        assert stats["knowledge_base_size"] == 2
        assert stats["task_history_size"] == 1
        assert stats["score_history_size"] == 2
        assert abs(stats["avg_score"] - 0.85) < 1e-10

    def test_statistics_empty(self):
        """Test statistics with empty state."""
        orchestrator = OmegaMetaOrchestrator()

        stats = orchestrator.get_statistics()

        assert stats["knowledge_base_size"] == 0
        assert stats["task_history_size"] == 0
        assert stats["score_history_size"] == 0
        assert stats["avg_score"] == 0.0


class TestPersistenceIntegration:
    """Integration tests for persistence system."""

    def test_multiple_save_load_cycles(self):
        """Test multiple save/load cycles."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            # First cycle
            orch1 = OmegaMetaOrchestrator()
            orch1.add_knowledge("k1", NumericVectorArtifact(vector=[0.1]))
            orch1.add_score(0.5)
            orch1.save_state(filepath)

            # Second cycle - load and add more
            orch2 = OmegaMetaOrchestrator()
            orch2.load_state(filepath)
            orch2.add_knowledge("k2", NumericVectorArtifact(vector=[0.2]))
            orch2.add_score(0.6)
            orch2.save_state(filepath)

            # Third cycle - verify all data
            orch3 = OmegaMetaOrchestrator()
            orch3.load_state(filepath)

            assert len(orch3.knowledge_base) == 2
            assert len(orch3.score_history) == 2

        finally:
            Path(filepath).unlink()

    def test_state_directory_creation(self):
        """Test that save_state creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "state.json"

            orchestrator = OmegaMetaOrchestrator()
            orchestrator.add_score(0.7)
            orchestrator.save_state(str(filepath))

            assert filepath.exists()
            assert filepath.parent.exists()
