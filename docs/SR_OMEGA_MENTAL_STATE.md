# SR-Omega Mental State Querying

## Overview

This feature provides introspection capabilities for the SR-Omega service, allowing you to query the internal "mental state" of any PENIN-Ω instance on the network. This gives you a direct window into what the system is thinking, what it's concerned about, and how well it's performing.

## Features

### 1. Mental State Tracking (`SROmegaService`)

The `SROmegaService` class tracks three key aspects of the system's state:

- **Pending Recommendations**: Tasks or optimizations that have been recommended but haven't been reported on yet
- **Recent Outcomes**: A log of the success/failure of recent recommendations
- **Current Concerns**: Tasks or metrics with low success rates that need attention

### 2. P2P Status Queries

The system extends the PENIN protocol with status query capabilities:

- `STATUS_QUERY` message type for requesting mental state
- `STATUS_RESPONSE` message type for returning mental state
- Full integration with the P2P node architecture

### 3. CLI Interface

Query peer status from the command line:

```bash
# Text format (human-readable)
python examples/demo_cli_query.py peer-001

# JSON format (machine-readable)
python examples/demo_cli_query.py peer-001 --format json
```

## Usage Examples

### Basic Usage

```python
from penin.omega.sr import SROmegaService

# Create service
service = SROmegaService()

# Add recommendations
service.add_recommendation(
    "rec-001", 
    "optimize_latency", 
    expected_sr=0.85,
    metadata={"priority": "high"}
)

# Report outcomes
service.report_outcome(
    "rec-001",
    success=True,
    actual_sr=0.92,
    message="Optimization successful"
)

# Get mental state
state = service.get_mental_state()
print(state)
```

### P2P Status Query

```python
import asyncio
from penin.omega.sr import SROmegaService
from penin.p2p.node import PeninNode

async def query_peer():
    # Create nodes
    node1 = PeninNode("node-001", SROmegaService())
    node2 = PeninNode("node-002", SROmegaService())
    
    # Query node-001 from node-002
    query = node2.protocol.create_status_query("node-001")
    response = await node1.handle_message(query)
    await node2.handle_message(response)
    
    # Get the mental state
    mental_state = node2.status_responses["node-001"]["mental_state"]
    return mental_state

asyncio.run(query_peer())
```

## Mental State Structure

The mental state dictionary contains:

```json
{
  "pending_recommendations": [
    {
      "id": "rec-001",
      "task": "optimize_latency",
      "expected_sr": 0.85,
      "age_seconds": 12.5,
      "metadata": {"priority": "high"}
    }
  ],
  "recent_outcomes": [
    {
      "id": "rec-002",
      "success": true,
      "actual_sr": 0.92,
      "message": "Success",
      "timestamp": 1759348888.12
    }
  ],
  "current_concerns": [
    {
      "task": "risky_task",
      "success_rate": 0.2,
      "total_attempts": 10,
      "severity": "high"
    }
  ],
  "sr_statistics": {
    "count": 50,
    "avg_sr": 0.85,
    "latest_sr": 0.88,
    "stability": "high"
  },
  "timestamp": 1759348888.12
}
```

## Concern Detection

The system automatically detects "concerns" - tasks that are performing poorly:

- **Threshold**: Tasks with ≥3 attempts and <50% success rate
- **Severity Levels**:
  - `high`: Success rate < 30%
  - `medium`: Success rate 30-50%

Example:

```python
service = SROmegaService()

# Create a failing task
for i in range(10):
    service.add_recommendation(f"rec-{i}", "risky_task", 0.85)
    success = i % 5 == 0  # 20% success rate
    service.report_outcome(f"rec-{i}", success=success, actual_sr=0.3)

state = service.get_mental_state()
# state["current_concerns"] will contain "risky_task" with severity "high"
```

## Configuration

### Service Configuration

```python
service = SROmegaService(
    max_pending=100,    # Max pending recommendations to track
    max_outcomes=50     # Max recent outcomes to track
)
```

### Protocol Configuration

The protocol uses the existing PENIN message types and is fully compatible with the existing P2P infrastructure.

## Testing

Run the comprehensive test suite:

```bash
# Run all mental state tests
pytest tests/test_sr_omega_mental_state.py -v

# Run specific test class
pytest tests/test_sr_omega_mental_state.py::TestSROmegaService -v

# Run integration tests
pytest tests/test_sr_omega_mental_state.py::TestIntegration -v
```

## Demos

### Full Feature Demo

```bash
python examples/demo_sr_omega_mental_state.py
```

This demonstrates:
1. Basic mental state tracking
2. P2P status queries
3. Concern detection

### CLI Query Demo

```bash
# Text format
python examples/demo_cli_query.py test-peer-001

# JSON format
python examples/demo_cli_query.py test-peer-001 --format json
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PENIN-Ω Network                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │  PeninNode   │         │  PeninNode   │            │
│  │  (node-001)  │◄───────►│  (node-002)  │            │
│  └──────┬───────┘         └──────┬───────┘            │
│         │                        │                     │
│         │ STATUS_QUERY           │                     │
│         │ STATUS_RESPONSE        │                     │
│         │                        │                     │
│  ┌──────▼───────┐         ┌──────▼───────┐            │
│  │ SROmegaService│        │ SROmegaService│           │
│  ├──────────────┤         ├──────────────┤            │
│  │ • Pending    │         │ • Pending    │            │
│  │ • Outcomes   │         │ • Outcomes   │            │
│  │ • Concerns   │         │ • Concerns   │            │
│  └──────────────┘         └──────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## API Reference

### SROmegaService

#### Methods

- `add_recommendation(id, task, expected_sr, metadata)`: Add a new recommendation
- `report_outcome(id, success, actual_sr, message)`: Report outcome of a recommendation
- `get_mental_state()`: Get current mental state dictionary

### PeninNode

#### Methods

- `query_peer_status(peer_id, timeout)`: Query a peer's mental state
- `handle_message(message)`: Handle incoming P2P messages

### Protocol Messages

- `create_status_query(target_peer_id)`: Create a status query message
- `create_status_response(mental_state)`: Create a status response message

## Future Enhancements

Potential improvements:

1. **Persistent State**: Store mental state to disk for recovery
2. **Historical Trends**: Track mental state over time
3. **Alerts**: Automatic alerts when concerns are detected
4. **Network-Wide Dashboard**: Aggregate mental state from all peers
5. **Adaptive Thresholds**: Learn optimal concern detection thresholds

## Integration with Existing Systems

This feature integrates seamlessly with:

- **SR-Ω∞ Engine**: Uses the same SR scoring system
- **PENIN Protocol**: Extends existing P2P message types
- **Omega Meta**: Can inform mutation and evolution decisions
- **Observability**: Mental state can be exported to metrics systems

## License

Apache 2.0 - See LICENSE file for details
