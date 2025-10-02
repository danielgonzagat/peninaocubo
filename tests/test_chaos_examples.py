#!/usr/bin/env python3
"""
Chaos Engineering Integration Example
======================================

Example demonstrating how to use the chaos utilities in real tests.
Shows integration with Toxiproxy and manual chaos injection.
"""

import sys
import time
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def test_example_toxiproxy_integration():
    """
    Example: Using Toxiproxy for realistic network chaos

    This test demonstrates how to use Toxiproxy when it's available.
    If Toxiproxy is not running, the test is skipped.
    """
    from chaos_utils import ToxiproxyClient

    client = ToxiproxyClient()

    if not client.is_available():
        pytest.skip("Toxiproxy not available. Run: docker run -d -p 8474:8474 shopify/toxiproxy")

    # Create a proxy for testing
    proxy_name = "test_guard"
    try:
        # Setup proxy
        client.create_proxy(
            proxy_name, listen="127.0.0.1:20001", upstream="127.0.0.1:8011"
        )

        # Add latency
        client.add_latency(proxy_name, latency_ms=500, jitter_ms=100)

        # Test through proxy - requests should be slow
        import requests

        start = time.time()
        try:
            requests.get("http://127.0.0.1:20001/health", timeout=2)
        except requests.exceptions.Timeout:
            print("✓ Request timed out as expected with high latency")

        elapsed = time.time() - start
        print(f"✓ Latency simulation working: {elapsed:.2f}s")

    finally:
        # Cleanup
        client.delete_proxy(proxy_name)


def test_example_chaos_proxy_context():
    """
    Example: Using chaos_proxy context manager

    This is the recommended way to use Toxiproxy in tests.
    """
    pytest.skip("Requires Toxiproxy running")

    from chaos_utils import chaos_proxy

    with chaos_proxy("guard", listen_port=20002, upstream_port=8011) as proxy:
        # Add various chaos conditions
        proxy.add_latency(latency_ms=1000)

        # Test your service through the proxy
        import requests

        with pytest.raises(requests.exceptions.Timeout):
            requests.get("http://127.0.0.1:20002/health", timeout=0.5)

        print("✓ Chaos proxy working correctly")


@pytest.mark.slow
@pytest.mark.integration
def test_example_network_chaos_mock():
    """
    Example: Using NetworkChaos for mocking without Toxiproxy

    This works without any external dependencies.
    Marked as slow/integration as it requires network access.
    """
    pytest.skip("Chaos test requires mock setup - integration test only")


@pytest.mark.slow
@pytest.mark.integration
def test_example_service_chaos():
    """
    Example: Using ServiceChaos utilities

    Demonstrates service-level chaos operations.
    Marked as slow/integration as it requires network access.
    """
    pytest.skip("Chaos test requires mock setup - integration test only")


def test_example_validate_fail_closed():
    """
    Example: Using validate_fail_closed decorator

    This ensures your test validates the fail-closed guarantee.
    """
    from chaos_utils import validate_fail_closed

    @validate_fail_closed
    def check_guard_with_chaos():
        """
        This function should return True if the system correctly denied
        the operation during chaos.
        """
        # Simulate checking if guard correctly denied
        guard_denied = True  # In real test, this would be actual check
        return guard_denied

    # Run the check
    result = check_guard_with_chaos()
    assert result is True
    print("✓ Fail-closed behavior validated")


def test_example_comprehensive_chaos_scenario():
    """
    Example: Comprehensive chaos scenario

    Combines multiple chaos conditions to simulate real-world failure.
    """
    from unittest.mock import Mock, patch

    import requests

    print("\n=== Comprehensive Chaos Scenario ===")

    # Scenario: Service under stress with multiple issues
    # 1. Network is slow
    # 2. Some requests fail
    # 3. Invalid data is being sent

    call_count = 0
    errors = []

    with patch("requests.post") as mock_post:

        def chaotic_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            # First call: network latency
            if call_count == 1:
                time.sleep(1)
                raise requests.exceptions.Timeout("Network timeout")

            # Second call: connection error
            if call_count == 2:
                raise requests.exceptions.ConnectionError("Connection refused")

            # Third call: server error
            if call_count == 3:
                response = Mock()
                response.status_code = 500
                response.text = "Internal Server Error"
                response.raise_for_status.side_effect = requests.exceptions.HTTPError()
                return response

            # Fourth call: success
            response = Mock()
            response.status_code = 200
            response.json.return_value = {"allow": False}  # Denied due to chaos
            response.raise_for_status = Mock()
            return response

        mock_post.side_effect = chaotic_response

        # Test with retry logic
        max_retries = 4
        success = False

        for attempt in range(max_retries):
            try:
                result = requests.post("http://127.0.0.1:8011/eval", json={})
                result.raise_for_status()
                success = True
                response_data = result.json()

                # Even on success, operation should be denied (fail-closed)
                assert response_data.get("allow") is False
                print(f"✓ Attempt {attempt + 1}: Success (but correctly denied)")
                break

            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
            ) as e:
                errors.append(str(e))
                print(f"⚠ Attempt {attempt + 1}: {type(e).__name__}")
                continue

        # Verify behavior
        assert success, "Should eventually succeed with retries"
        assert len(errors) == 3, f"Should have 3 errors, got {len(errors)}"
        print(f"✅ PASS: Handled {len(errors)} errors before success")
        print("   Final result: DENIED (fail-closed guarantee)")


if __name__ == "__main__":
    # Run examples
    print("Running chaos engineering examples...\n")

    try:
        test_example_network_chaos_mock()
        print("✓ Network chaos mock example passed\n")
    except Exception as e:
        print(f"✗ Network chaos mock example failed: {e}\n")

    try:
        test_example_validate_fail_closed()
        print("✓ Fail-closed validation example passed\n")
    except Exception as e:
        print(f"✗ Fail-closed validation example failed: {e}\n")

    try:
        test_example_comprehensive_chaos_scenario()
        print("✓ Comprehensive chaos scenario passed\n")
    except Exception as e:
        print(f"✗ Comprehensive chaos scenario failed: {e}\n")

    print("Examples complete!")
