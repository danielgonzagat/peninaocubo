# Chaos Engineering Test Suite

## Overview

This test suite validates the resilience and fail-closed design of the PENIN-Ω system under adverse conditions.

## Test Scenarios

### 1. Service Death (Σ-Guard Pod Kill)
**File**: `test_chaos_engineering.py::test_chaos_service_death_*`

Tests that the system maintains fail-closed behavior when the Σ-Guard service is killed during validation.

**Expected Behavior**:
- ✅ Promotions MUST fail when guard is unavailable
- ✅ No silent failures
- ✅ System defaults to DENY (fail-closed)
- ✅ Service recovery works correctly

**Implementation**:
- Starts mock Σ-Guard service
- Validates service is healthy
- Kills the service during validation
- Verifies all validation attempts fail
- Tests service recovery

### 2. Network Latency (Ω-META ↔ SR-Ω∞)
**File**: `test_chaos_engineering.py::test_chaos_network_latency_*`

Tests timeout handling and retry logic under slow network conditions.

**Expected Behavior**:
- ✅ Requests timeout appropriately (don't hang)
- ✅ Retry logic works correctly
- ✅ Slow services don't cascade to fast operations
- ✅ Timeouts are detected and handled

**Implementation**:
- Simulates network delays using mocks
- Tests timeout behavior (6s delay with 5s timeout)
- Validates retry logic with intermittent failures
- Ensures cascading failures are prevented

### 3. Data Corruption (Malformed API Inputs)
**File**: `test_chaos_engineering.py::test_chaos_data_corruption_*`

Tests system stability when receiving malformed or malicious data.

**Expected Behavior**:
- ✅ Invalid JSON is rejected gracefully
- ✅ Wrong data types are validated
- ✅ Boundary values (infinity, NaN) handled safely
- ✅ Injection attempts (SQL, XSS) are sanitized
- ✅ Service remains stable after bad inputs

**Implementation**:
- Sends malformed JSON payloads
- Tests invalid data types
- Tests extreme boundary values
- Tests injection patterns (SQL, XSS, command injection)
- Verifies service health after each test

### 4. Combined Failure Scenarios
**File**: `test_chaos_engineering.py::test_chaos_combined_failures`

Tests system behavior under multiple simultaneous failures.

**Expected Behavior**:
- ✅ System maintains fail-closed under compound stress
- ✅ Multiple chaos conditions don't break guarantees
- ✅ All retry attempts fail appropriately

### 5. Fail-Closed Guarantee Validation
**File**: `test_chaos_engineering.py::test_chaos_fail_closed_guarantee`

Meta-test that validates the core fail-closed principle across all scenarios.

## Running the Tests

### Basic Run
```bash
# Run all chaos tests
pytest tests/test_chaos_engineering.py -v

# Run specific test
pytest tests/test_chaos_engineering.py::test_chaos_service_death_guard_killed_during_validation -v

# Run with output
pytest tests/test_chaos_engineering.py -v -s
```

### With Markers
```bash
# Run only slow tests (includes chaos tests)
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### Coverage
```bash
# Run with coverage
pytest tests/test_chaos_engineering.py --cov=penin --cov-report=html
```

## Tools and Dependencies

### Required
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-timeout` - Timeout handling
- `requests` - HTTP client

### Optional (for advanced chaos)
- `toxiproxy` - Network chaos injection (Docker)
  ```bash
  docker run -d -p 8474:8474 -p 20000-20009:20000-20009 shopify/toxiproxy
  ```
- `kube-monkey` - Kubernetes pod killing (for production)

## Chaos Utilities

The `chaos_utils.py` module provides helper utilities:

### ToxiproxyClient
```python
from tests.chaos_utils import ToxiproxyClient

client = ToxiproxyClient()
client.create_proxy("guard", "127.0.0.1:20000", "127.0.0.1:8011")
client.add_latency("guard", 500, 100)  # 500ms ± 100ms
```

### Chaos Proxy Context Manager
```python
from tests.chaos_utils import chaos_proxy

with chaos_proxy("guard", 20000, 8011) as proxy:
    proxy.add_latency(500)
    # Run tests through proxy at port 20000
```

### Network Chaos
```python
from tests.chaos_utils import NetworkChaos

with NetworkChaos.inject_latency(requests.get, 2.0):
    # All requests will have 2s delay
    pass

with NetworkChaos.simulate_packet_loss(0.5):
    # 50% of packets will be lost
    pass
```

## Test Results Interpretation

### Success Criteria
All chaos tests should PASS, meaning:
1. **Service Death**: System correctly denies operations when guard is unavailable
2. **Network Latency**: Timeouts are handled, no hanging requests
3. **Data Corruption**: Invalid inputs are rejected, service remains stable
4. **Combined Failures**: System maintains fail-closed under stress

### Failure Indicators
If tests FAIL, investigate:
- ❌ **Silent failures**: Operations succeeded when they should have failed
- ❌ **Crashes**: Service crashed instead of gracefully handling error
- ❌ **Hangs**: Requests hung indefinitely instead of timing out
- ❌ **Cascading failures**: One failure caused widespread system issues

## Extending the Suite

### Adding New Chaos Scenarios

1. Create test function in `test_chaos_engineering.py`:
```python
def test_chaos_new_scenario():
    """
    Chaos Test: Description
    
    Scenario: What you're testing
    Expected: What should happen
    """
    print("\n" + "=" * 70)
    print("CHAOS TEST: New Scenario")
    print("=" * 70)
    
    # Test implementation
    pass
```

2. Use chaos utilities:
```python
from tests.chaos_utils import ServiceChaos, NetworkChaos

with ServiceChaos.intermittent_failures(0.3):
    # Test with 30% failure rate
    pass
```

3. Validate fail-closed:
```python
from tests.chaos_utils import validate_fail_closed

@validate_fail_closed
def test_something():
    # Test code
    return should_deny  # Return True if properly denied
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Chaos Tests

on: [push, pull_request]

jobs:
  chaos:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      - name: Run chaos tests
        run: |
          pytest tests/test_chaos_engineering.py -v
```

### Kubernetes Deployment (kube-monkey)
For production chaos testing:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-monkey-config
data:
  config.toml: |
    [kubemonkey]
    dry_run = false
    run_hour = 10
    start_hour = 9
    end_hour = 17
    blacklisted_namespaces = ["kube-system"]
```

## Best Practices

1. **Run Regularly**: Include chaos tests in CI/CD pipeline
2. **Monitor Metrics**: Observe Prometheus metrics during chaos tests
3. **Review Logs**: Check structured logs for error handling
4. **Test in Staging**: Run chaos tests in staging before production
5. **Gradual Rollout**: Start with mild chaos, increase severity
6. **Document Findings**: Update this README with new scenarios and learnings

## References

- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [Toxiproxy Documentation](https://github.com/Shopify/toxiproxy)
- [kube-monkey Documentation](https://github.com/asobti/kube-monkey)
- [Netflix Chaos Engineering](https://netflixtechblog.com/tagged/chaos-engineering)

## Troubleshooting

### Tests Failing
1. Check service ports are available (8011, 8012, 20000-20009)
2. Ensure no services are already running on test ports
3. Verify pytest and dependencies are installed
4. Check system resources (memory, CPU)

### Toxiproxy Issues
1. Verify Docker is running
2. Check Toxiproxy container is running:
   ```bash
   docker ps | grep toxiproxy
   ```
3. Test Toxiproxy API:
   ```bash
   curl http://localhost:8474/version
   ```

### Performance Issues
1. Increase timeouts if system is slow
2. Reduce number of parallel tests
3. Skip slow tests during development:
   ```bash
   pytest -m "not slow"
   ```

## Metrics and Observability

During chaos tests, monitor:
- **Response Times**: Should timeout appropriately
- **Error Rates**: Should increase but not crash system
- **Service Health**: Should recover after chaos ends
- **Resource Usage**: Should not exhaust memory/CPU

Use Prometheus queries:
```promql
# Error rate during chaos
rate(http_requests_total{status=~"5.."}[1m])

# Request duration
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m]))

# Service health
up{job="penin"}
```
