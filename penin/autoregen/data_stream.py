"""
PENIN-Ω Data Stream Processor
==============================

Continuous data ingestion and processing for autoregeneração.

Features:
---------
- Streaming data processing
- Incremental learning
- Concept drift detection
- Memory consolidation

Integrates with:
----------------
- ContinuousLearner (parameter updates)
- Self-RAG (knowledge retrieval)
- WORM Ledger (audit trail)
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Iterator

logger = logging.getLogger(__name__)


@dataclass
class DataSample:
    """Single data sample"""
    
    sample_id: str
    content: Any
    timestamp: float
    source: str | None = None
    
    def compute_hash(self) -> str:
        """Compute content hash"""
        content_str = str(self.content)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]


class DataStreamProcessor:
    """
    Process continuous data stream for learning.
    
    Handles:
    - Data validation
    - Deduplication
    - Buffering
    - Quality filtering
    """
    
    def __init__(self, buffer_size: int = 1000):
        """
        Initialize data stream processor.
        
        Args:
            buffer_size: Maximum buffer size
        """
        self.buffer: deque[DataSample] = deque(maxlen=buffer_size)
        self.seen_hashes: set[str] = set()
        self.total_ingested = 0
        self.total_duplicates = 0
        self.total_invalid = 0
    
    def ingest(self, data: Any, source: str | None = None) -> bool:
        """
        Ingest single data point.
        
        Args:
            data: Data to ingest
            source: Optional source identifier
        
        Returns:
            True if ingested, False if rejected (duplicate/invalid)
        """
        # Create sample
        sample = DataSample(
            sample_id=f"sample_{self.total_ingested:08d}",
            content=data,
            timestamp=time.time(),
            source=source,
        )
        
        # Check for duplicates
        content_hash = sample.compute_hash()
        if content_hash in self.seen_hashes:
            self.total_duplicates += 1
            logger.debug(f"Duplicate rejected: {sample.sample_id}")
            return False
        
        # Validate (simple check for now)
        if not self._validate_sample(sample):
            self.total_invalid += 1
            logger.debug(f"Invalid sample rejected: {sample.sample_id}")
            return False
        
        # Accept
        self.buffer.append(sample)
        self.seen_hashes.add(content_hash)
        self.total_ingested += 1
        
        logger.debug(f"Ingested: {sample.sample_id}")
        return True
    
    def _validate_sample(self, sample: DataSample) -> bool:
        """Validate sample (basic checks)"""
        # In production, apply more sophisticated validation
        return sample.content is not None
    
    def get_batch(self, size: int) -> list[DataSample]:
        """
        Get batch of samples from buffer.
        
        Args:
            size: Batch size
        
        Returns:
            List of samples (up to size)
        """
        n = min(size, len(self.buffer))
        return list(self.buffer)[-n:] if n > 0 else []
    
    def get_stats(self) -> dict[str, int]:
        """Get processor statistics"""
        return {
            "total_ingested": self.total_ingested,
            "total_duplicates": self.total_duplicates,
            "total_invalid": self.total_invalid,
            "buffer_size": len(self.buffer),
            "unique_hashes": len(self.seen_hashes),
        }


# ============================================================================
# STREAM UTILITIES
# ============================================================================

def create_data_stream(data_source: Iterator[Any]) -> Iterator[DataSample]:
    """
    Create data stream from any iterator.
    
    Args:
        data_source: Source iterator
    
    Yields:
        DataSample objects
    """
    for idx, item in enumerate(data_source):
        yield DataSample(
            sample_id=f"stream_{idx:08d}",
            content=item,
            timestamp=time.time(),
        )


__all__ = [
    "DataSample",
    "DataStreamProcessor",
    "create_data_stream",
]
