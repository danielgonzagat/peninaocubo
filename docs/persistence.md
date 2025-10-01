# PENIN-Ω Persistence System

## Overview

This document describes the **Phase 2: Persistence and Resilience** implementation for the PENIN-Ω system. The goal is to cure the system's "Systemic Amnesia" by implementing long-term memory through state serialization and deserialization.

## Architecture

### Components

1. **NumericVectorArtifact** (`penin/core/artifacts.py`)
   - Data structure for knowledge representation
   - Contains a numeric vector and optional metadata
   - Supports serialization to/from dictionary format

2. **State Serialization** (`penin/core/serialization.py`)
   - Custom JSON encoder (`StateEncoder`) for PENIN-specific types
   - Custom JSON decoder (`state_decoder`) for deserialization
   - Handles:
     - `NumericVectorArtifact` objects
     - `deque` collections with maxlen support

3. **OmegaMetaOrchestrator** (`penin/core/orchestrator.py`)
   - Main orchestrator with state management
   - Maintains:
     - `knowledge_base`: Dictionary of NumericVectorArtifact objects
     - `task_history`: Deque of task records
     - `score_history`: Deque of performance scores
   - Methods:
     - `save_state(filepath)`: Persist state to JSON file
     - `load_state(filepath)`: Restore state from JSON file
     - `get_statistics()`: Get current state statistics

4. **Application Entry Point** (`penin/__main__.py`)
   - Main entry point with lifecycle management
   - Features:
     - Signal handlers for graceful shutdown (SIGINT/SIGTERM)
     - Automatic state loading on startup
     - Automatic state saving on shutdown
     - Default state file: `.penin_omega/state.json`

## Usage

### Basic Usage

```python
from penin.core import OmegaMetaOrchestrator, NumericVectorArtifact

# Create orchestrator
orchestrator = OmegaMetaOrchestrator()

# Add knowledge
artifact = NumericVectorArtifact(vector=[0.1, 0.2, 0.3])
orchestrator.add_knowledge("embedding_1", artifact)

# Add task history
orchestrator.add_task({
    "task_id": 1,
    "type": "evolution",
    "status": "completed"
})

# Add performance scores
orchestrator.add_score(0.85)

# Save state
orchestrator.save_state(".penin_omega/state.json")

# Load state
orchestrator.load_state(".penin_omega/state.json")
```

### Running the Application

```bash
# Run the application
python -m penin

# State is automatically loaded on startup (if exists)
# State is automatically saved on shutdown
```

### Custom History Length

```python
# Create orchestrator with custom history size
orchestrator = OmegaMetaOrchestrator(history_maxlen=500)
```

## State File Format

The state is saved as JSON with the following structure:

```json
{
  "knowledge_base": {
    "key1": {
      "__type__": "NumericVectorArtifact",
      "vector": [0.1, 0.2, 0.3],
      "metadata": {}
    }
  },
  "task_history": {
    "__type__": "deque",
    "items": [
      {"task_id": 1, "type": "evolution"}
    ],
    "maxlen": 1000
  },
  "score_history": {
    "__type__": "deque",
    "items": [0.85, 0.90],
    "maxlen": 1000
  }
}
```

## Testing

Comprehensive test suite in `tests/core/test_persistence.py`:

```bash
# Run persistence tests
python -m pytest tests/core/test_persistence.py -v

# Results: 24/24 tests passing
```

### Test Coverage

- ✅ NumericVectorArtifact serialization/deserialization
- ✅ StateEncoder for custom types
- ✅ state_decoder for custom types
- ✅ OmegaMetaOrchestrator initialization
- ✅ Knowledge base operations
- ✅ Task history operations
- ✅ Score history operations
- ✅ State save/load cycle
- ✅ Missing file handling
- ✅ History maxlen enforcement
- ✅ Statistics calculation
- ✅ Multiple save/load cycles
- ✅ Directory creation

## Features

### Graceful Shutdown

The application handles SIGINT and SIGTERM signals to ensure state is saved before exit:

```python
# Press Ctrl+C to trigger graceful shutdown
^C
🛑 Received signal 2, saving state...
✅ State saved to .penin_omega/state.json
```

### Automatic State Recovery

On startup, the application automatically loads previous state:

```
🚀 Starting PENIN-Ω Orchestrator...
✅ State loaded from .penin_omega/state.json
   Knowledge base: 2 items
   Task history: 2 entries
   Score history: 3 entries
```

### First Run Detection

The system handles first runs gracefully:

```
🚀 Starting PENIN-Ω Orchestrator...
ℹ️  No previous state found (first run)
```

## Integration Points

### Future Enhancements

1. **Compression**: Add gzip compression for large state files
2. **Versioning**: State format versioning for backward compatibility
3. **Incremental Saves**: Save only deltas for performance
4. **Cloud Backup**: Sync state to cloud storage
5. **Encryption**: Encrypt sensitive knowledge artifacts
6. **Checkpointing**: Multiple checkpoint files with timestamps
7. **Migration**: Tools to migrate between state formats

### Integration with Other Modules

The persistence system is designed to integrate with:

- **WORM Ledger**: Audit trail of state changes
- **Ω-META**: Mutation and evolution state
- **Ethics Metrics**: Historical ethics scores
- **Performance Tracking**: Long-term performance analytics

## Error Handling

The system is designed to be fail-safe:

1. **Missing Files**: Returns `False` without error on load
2. **I/O Errors**: Raises clear exceptions for write failures
3. **JSON Errors**: Raises clear exceptions for invalid JSON
4. **Directory Creation**: Automatically creates parent directories
5. **Signal Handling**: Gracefully saves state on interruption

## Performance Considerations

1. **Memory**: Deque with maxlen prevents unbounded growth
2. **I/O**: Async operations possible for future enhancement
3. **Serialization**: JSON is human-readable but can be optimized with orjson
4. **File Size**: History limits keep state files manageable

## Security Considerations

1. **File Permissions**: State files should be protected
2. **Sensitive Data**: Consider encryption for production
3. **Validation**: JSON schema validation possible for future enhancement
4. **Integrity**: HMAC or checksums could be added for verification

## Compliance

This implementation fulfills the requirements specified in Phase 2 of the Scientific Roadmap:

✅ State serialization/deserialization for custom types
✅ Memory methods in orchestrator (save_state/load_state)
✅ Integration into node lifecycle with signal handlers
✅ Comprehensive test suite with 24 passing tests
✅ Graceful handling of missing files
✅ Parent directory creation
✅ Statistics and monitoring

## References

- Problem Statement: Phase 2: Persistence and Resilience
- Related: WORM Ledger (`penin/ledger/worm_ledger_complete.py`)
- Related: Router Persistence (`penin/router.py`)
