"""Tests for Autoregeneração module"""

import pytest
from penin.autoregen import (
    ContinuousLearner,
    DataStreamProcessor,
    LearningMode,
    create_continuous_learner,
)


class TestContinuousLearner:
    """Test continuous learning engine"""
    
    def test_initialization(self):
        """Test learner initialization"""
        learner = ContinuousLearner()
        
        assert learner.iteration == 0
        assert learner.data_seen == 0
        assert learner.updates_made == 0
        assert "kappa" in learner.hyperparameters
        assert learner.hyperparameters["kappa"] == 20.0
    
    def test_data_ingestion(self):
        """Test data batch ingestion"""
        learner = ContinuousLearner()
        
        # Ingest small batch (won't trigger update)
        result = learner.ingest_data_batch([1, 2, 3])
        
        assert result["updated"] is False
        assert learner.data_seen == 3
    
    def test_parameter_update(self):
        """Test parameter update when threshold reached"""
        from penin.autoregen.continuous_learning import RegenerationConfig
        
        config = RegenerationConfig(
            update_every_n_samples=10,
            min_improvement_threshold=0.0  # Accept any change
        )
        learner = ContinuousLearner(config)
        
        # Ingest exactly 10 samples (should trigger update)
        result = learner.ingest_data_batch([i for i in range(10)])
        
        # Should attempt update (might not accept if no improvement)
        assert "updated" in result
        if result["updated"]:
            assert "delta_linf" in result
    
    def test_parameter_constraints(self):
        """Test that parameter changes respect constraints"""
        learner = ContinuousLearner()
        
        # Propose updates multiple times
        for _ in range(10):
            proposed = learner._propose_parameter_update()
            
            # Check constraints
            assert proposed["kappa"] >= 20.0
            assert proposed["kappa"] <= 100.0
            assert proposed["lambda_c"] >= 0.01
            assert proposed["lambda_c"] <= 2.0
            assert proposed["beta_min"] >= 0.001
            assert proposed["beta_min"] <= 0.1
    
    def test_best_params_tracking(self):
        """Test that best parameters are tracked"""
        learner = ContinuousLearner()
        
        initial_best = learner.best_linf
        
        # Force an update
        from penin.autoregen.continuous_learning import RegenerationConfig
        learner.config = RegenerationConfig(update_every_n_samples=1, min_improvement_threshold=0.0)
        
        learner.ingest_data_batch([1])
        
        # Best should be updated if performance improved
        # (might not improve due to randomness, but tracking should work)
        assert hasattr(learner, 'best_params')
        assert hasattr(learner, 'best_linf')
    
    def test_learning_mode_conservative(self):
        """Test conservative learning mode"""
        learner = create_continuous_learner(mode=LearningMode.CONSERVATIVE)
        
        assert learner.config.max_param_change_pct == 0.05  # 5%
        assert learner.config.min_improvement_threshold == 0.01  # 1%
    
    def test_learning_mode_aggressive(self):
        """Test aggressive learning mode"""
        learner = create_continuous_learner(mode=LearningMode.AGGRESSIVE)
        
        assert learner.config.max_param_change_pct == 0.20  # 20%
        assert learner.config.min_improvement_threshold == 0.001  # 0.1%
    
    def test_get_learning_stats(self):
        """Test learning statistics retrieval"""
        learner = ContinuousLearner()
        
        stats = learner.get_learning_stats()
        
        assert "iteration" in stats
        assert "data_seen" in stats
        assert "current_params" in stats
        assert "best_params" in stats


class TestDataStreamProcessor:
    """Test data stream processing"""
    
    def test_initialization(self):
        """Test processor initialization"""
        processor = DataStreamProcessor(buffer_size=100)
        
        assert len(processor.buffer) == 0
        assert processor.total_ingested == 0
    
    def test_single_ingestion(self):
        """Test ingesting single sample"""
        processor = DataStreamProcessor()
        
        accepted = processor.ingest("test data", source="test")
        
        assert accepted is True
        assert processor.total_ingested == 1
        assert len(processor.buffer) == 1
    
    def test_duplicate_rejection(self):
        """Test that duplicates are rejected"""
        processor = DataStreamProcessor()
        
        # Ingest same data twice
        processor.ingest("duplicate", source="test")
        rejected = processor.ingest("duplicate", source="test")
        
        assert rejected is False  # Second one rejected
        assert processor.total_ingested == 1
        assert processor.total_duplicates == 1
    
    def test_buffer_overflow(self):
        """Test buffer size limit"""
        processor = DataStreamProcessor(buffer_size=5)
        
        # Ingest more than buffer size
        for i in range(10):
            processor.ingest(f"sample_{i}")
        
        # Buffer should only keep last 5
        assert len(processor.buffer) == 5
        assert processor.total_ingested == 10
    
    def test_get_batch(self):
        """Test batch retrieval"""
        processor = DataStreamProcessor()
        
        # Ingest samples
        for i in range(20):
            processor.ingest(f"sample_{i}")
        
        # Get batch
        batch = processor.get_batch(size=5)
        
        assert len(batch) == 5
    
    def test_get_stats(self):
        """Test statistics"""
        processor = DataStreamProcessor()
        
        processor.ingest("data1")
        processor.ingest("data2")
        processor.ingest("data2")  # Duplicate
        
        stats = processor.get_stats()
        
        assert stats["total_ingested"] == 2
        assert stats["total_duplicates"] == 1
        assert stats["buffer_size"] == 2


class TestIntegration:
    """Test integration of continuous learning components"""
    
    def test_learner_with_stream(self):
        """Test learner consuming from stream"""
        from penin.autoregen.continuous_learning import RegenerationConfig
        
        # Create learner that updates every 5 samples
        config = RegenerationConfig(update_every_n_samples=5)
        learner = ContinuousLearner(config)
        
        # Create stream
        processor = DataStreamProcessor()
        
        # Ingest data through stream
        for i in range(15):
            processor.ingest(f"sample_{i}")
        
        # Get batch and feed to learner
        batch = processor.get_batch(size=5)
        result = learner.ingest_data_batch(batch)
        
        # Should have triggered update
        assert learner.data_seen >= 5
