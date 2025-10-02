# PENIN Network Discovery

**Phase 5: The Agora - Curing Social Isolation**

## Overview

The Network Discovery module enables PENIN nodes to automatically discover each other on the local network using UDP broadcast. This implements the first part of Phase 5 of the Scientific Roadmap: "The Agora", which aims to cure "Social Isolation" by allowing nodes to form a distributed network of intelligence.

## Architecture

### Components

1. **PeerDiscoveryService** (`penin/network/discovery.py`)
   - UDP-based peer discovery service
   - Broadcasts node presence periodically
   - Listens for broadcasts from other nodes
   - Thread-safe peer management
   - Callback system for peer discovery events

2. **PeninNode Integration** (`penin/p2p/node.py`)
   - Integrated discovery service lifecycle
   - Context manager support for automatic start/stop
   - Automatic peer tracking
   - Optional orchestrator integration

3. **OmegaMetaOrchestrator Extension** (`penin/core/orchestrator.py`)
   - `known_peers` set attribute
   - State persistence for discovered peers
   - Backward-compatible serialization

4. **Configuration** (`penin/config.py`)
   - `PENIN_DISCOVERY_PORT`: UDP port for discovery (default: 51515)
   - `PENIN_DISCOVERY_INTERVAL`: Broadcast interval in seconds (default: 10)

## Features

### UDP Broadcasting

- Periodic broadcast of node information to `255.255.255.255`
- JSON-encoded messages with node ID, port, and timestamp
- Configurable broadcast interval (default: 10 seconds)
- Automatic retry and error handling

### UDP Listening

- Binds to `0.0.0.0` on configured port
- Non-blocking socket with timeout
- Validates incoming messages
- Ignores self-broadcasts
- Thread-safe peer tracking

### Peer Management

- Thread-safe set of discovered peer IDs
- Callback system for new peer discovery
- Automatic integration with orchestrator's `known_peers`
- Persistent state across restarts

### Lifecycle Management

- Simple start/stop methods
- Context manager support
- Graceful shutdown with thread cleanup
- Daemon threads for background operation

## Usage

### Basic Usage

```python
from penin.p2p.node import PeninNode

# Create node with discovery enabled
node = PeninNode(node_id="my-node", enable_discovery=True)

# Start discovery
node.start_discovery()

# ... node operates and discovers peers ...

# Stop discovery
node.stop_discovery()
```

### Context Manager

```python
from penin.p2p.node import PeninNode

node = PeninNode(node_id="my-node", enable_discovery=True)

with node:
    # Discovery automatically started
    # ... node operates ...
    pass
# Discovery automatically stopped
```

### With Orchestrator Integration

```python
from penin.core.orchestrator import OmegaMetaOrchestrator
from penin.p2p.node import PeninNode

# Create orchestrator
orchestrator = OmegaMetaOrchestrator()

# Create node with orchestrator
node = PeninNode(
    node_id="my-node",
    orchestrator=orchestrator,
    enable_discovery=True,
)

node.start_discovery()
# ... peers are automatically added to orchestrator.known_peers ...
node.stop_discovery()

# Save state with discovered peers
orchestrator.save_state("state.json")

# Later, load state
orchestrator.load_state("state.json")
# known_peers are restored
```

### Custom Callback

```python
from penin.network.discovery import PeerDiscoveryService

def on_peer_discovered(peer_info):
    print(f"Discovered peer: {peer_info['id']} at {peer_info['address']}")

service = PeerDiscoveryService(
    node_id="my-node",
    port=51515,
    broadcast_interval=10,
    on_peer_discovered=on_peer_discovered,
)

service.start()
# ... discovery operates ...
service.stop()
```

## Configuration

### Environment Variables

```bash
# Discovery port (default: 51515)
export PENIN_DISCOVERY_PORT=51515

# Broadcast interval in seconds (default: 10)
export PENIN_DISCOVERY_INTERVAL=10
```

### In Code

```python
from penin.config import settings

# Access configuration
print(f"Discovery port: {settings.PENIN_DISCOVERY_PORT}")
print(f"Discovery interval: {settings.PENIN_DISCOVERY_INTERVAL}")
```

## State Persistence

The `known_peers` set is automatically persisted with the orchestrator state:

```python
orchestrator = OmegaMetaOrchestrator()

# Discovered peers are added
orchestrator.known_peers.add("192.168.1.100:51515")
orchestrator.known_peers.add("192.168.1.101:51515")

# Save state
orchestrator.save_state("penin_state.json")

# Load state
new_orchestrator = OmegaMetaOrchestrator()
new_orchestrator.load_state("penin_state.json")
# known_peers are restored
```

### State Format

The state file includes `known_peers` as a JSON array:

```json
{
  "knowledge_base": {},
  "task_history": {"__type__": "deque", "items": [], "maxlen": 1000},
  "score_history": {"__type__": "deque", "items": [], "maxlen": 1000},
  "known_peers": [
    "192.168.1.100:51515",
    "192.168.1.101:51515"
  ]
}
```

## Discovery Protocol

### Broadcast Message Format

```json
{
  "id": "node-id-123",
  "port": 51515,
  "timestamp": 1234567890.123
}
```

### Message Validation

- Must be valid JSON
- Must contain `id` field
- Self-messages are ignored
- Invalid messages logged but don't crash service

## Thread Safety

- Uses `threading.Lock` for peer set access
- Safe concurrent access via `get_discovered_peers()`
- Thread-safe callback invocation
- Clean shutdown coordination

## Error Handling

- Graceful handling of network errors
- Logs errors without crashing
- Continues operation after transient failures
- Validates message structure before processing
- Timeout-based socket operations

## Examples

See `examples/network_discovery_example.py` for comprehensive usage examples:

1. Basic peer discovery with two nodes
2. Discovery with orchestrator integration
3. State persistence with known peers
4. Context manager lifecycle
5. Multiple nodes discovery

Run the examples:

```bash
python examples/network_discovery_example.py
```

## Testing

Comprehensive test suite in `tests/network/`:

- `test_discovery.py`: UDP broadcasting and listening tests
- `test_node_integration.py`: PeninNode integration tests

Run tests:

```bash
# All network tests
pytest tests/network/ -v

# Discovery tests only
pytest tests/network/test_discovery.py -v

# Integration tests only
pytest tests/network/test_node_integration.py -v

# Persistence tests (includes known_peers)
pytest tests/core/test_persistence.py::TestKnownPeersPersistence -v
```

## Limitations

### Current Limitations

1. **Local Network Only**: Uses UDP broadcast (255.255.255.255), limited to local subnet
2. **No Authentication**: Peers are trusted; no authentication mechanism
3. **No Encryption**: Messages sent in plaintext
4. **Best-Effort Delivery**: UDP doesn't guarantee message delivery
5. **IPv4 Only**: Currently supports IPv4 only

### Future Enhancements

1. **mDNS/Bonjour**: For zero-configuration service discovery
2. **DHT**: For distributed hash table based peer discovery
3. **NAT Traversal**: Support for discovering peers across NAT
4. **Authentication**: Cryptographic peer authentication
5. **Encryption**: TLS/DTLS for secure communication
6. **IPv6 Support**: Dual-stack IPv4/IPv6 support

## Security Considerations

1. **Firewall**: Ensure UDP port 51515 is open on firewall
2. **Network Segmentation**: Run on trusted network segments only
3. **Message Validation**: All messages validated before processing
4. **Rate Limiting**: Consider implementing rate limiting for production
5. **Access Control**: Implement authentication for production deployments

## Performance

- **Memory**: O(n) where n is number of discovered peers
- **CPU**: Minimal, periodic broadcasts only
- **Network**: Low bandwidth (~100 bytes every 10 seconds per node)
- **Threads**: 2 daemon threads per node (broadcaster + listener)

## Troubleshooting

### Peers Not Discovered

1. Check firewall allows UDP on port 51515
2. Verify nodes are on same network segment
3. Check broadcast permission (may fail in restricted environments)
4. Verify `PENIN_DISCOVERY_PORT` matches across nodes
5. Check logs for "Operation not permitted" errors

### High Network Traffic

1. Increase `PENIN_DISCOVERY_INTERVAL` to reduce broadcasts
2. Consider using different discovery mechanism (mDNS)

### State Not Persisting

1. Verify `orchestrator.save_state()` is called
2. Check file write permissions
3. Verify state file path is correct

## Related Documentation

- [Persistence System](persistence.md) - State serialization
- [P2P Protocol](../penin/p2p/README.md) - PENIN P2P protocol
- [Scientific Roadmap](../docs/archive/TRANSFORMATION_FINAL_STATUS.md) - Phase 5: The Agora

## Contributing

When extending the network discovery system:

1. Maintain thread safety
2. Add comprehensive tests
3. Update documentation
4. Follow existing code patterns
5. Consider backward compatibility

## References

- RFC 919: Broadcasting Internet Datagrams
- RFC 1122: Requirements for Internet Hosts
- UDP broadcast best practices
- Peer-to-peer network design patterns
