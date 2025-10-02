#!/usr/bin/env python3
"""
Chaos Engineering Utilities
============================

Helper utilities for chaos engineering tests.
Provides:
- Toxiproxy client wrapper
- Network chaos injection
- Service lifecycle management
- Failure simulation utilities
"""

import time
from contextlib import contextmanager

import requests


class ToxiproxyClient:
    """
    Client for Toxiproxy - a framework for simulating network conditions.

    Toxiproxy is a TCP proxy that can inject latency, bandwidth limitations,
    and connection failures to simulate real-world network conditions.

    Install: docker run -d -p 8474:8474 -p 20000-20009:20000-20009 shopify/toxiproxy
    """

    def __init__(self, host: str = "localhost", port: int = 8474):
        self.base_url = f"http://{host}:{port}"
        self.proxies = {}

    def is_available(self) -> bool:
        """Check if Toxiproxy server is running"""
        try:
            r = requests.get(f"{self.base_url}/version", timeout=2)
            return r.ok
        except Exception:
            return False

    def create_proxy(self, name: str, listen: str, upstream: str) -> dict:
        """
        Create a new proxy

        Args:
            name: Proxy name
            listen: Address to listen on (e.g., "127.0.0.1:20000")
            upstream: Upstream service address (e.g., "127.0.0.1:8011")

        Returns:
            Proxy configuration
        """
        payload = {"name": name, "listen": listen, "upstream": upstream, "enabled": True}

        r = requests.post(f"{self.base_url}/proxies", json=payload, timeout=5)
        if r.ok:
            proxy = r.json()
            self.proxies[name] = proxy
            return proxy
        else:
            raise Exception(f"Failed to create proxy: {r.text}")

    def delete_proxy(self, name: str):
        """Delete a proxy"""
        try:
            requests.delete(f"{self.base_url}/proxies/{name}", timeout=5)
            self.proxies.pop(name, None)
        except Exception:
            pass

    def add_latency(self, proxy_name: str, latency_ms: int, jitter_ms: int = 0):
        """
        Add latency toxic to proxy

        Args:
            proxy_name: Name of the proxy
            latency_ms: Base latency in milliseconds
            jitter_ms: Jitter in milliseconds (randomness)
        """
        toxic = {
            "name": f"{proxy_name}_latency",
            "type": "latency",
            "stream": "downstream",
            "toxicity": 1.0,
            "attributes": {"latency": latency_ms, "jitter": jitter_ms},
        }

        r = requests.post(
            f"{self.base_url}/proxies/{proxy_name}/toxics", json=toxic, timeout=5
        )
        if not r.ok:
            raise Exception(f"Failed to add latency: {r.text}")

    def add_bandwidth_limit(self, proxy_name: str, rate_kbps: int):
        """
        Add bandwidth limitation toxic

        Args:
            proxy_name: Name of the proxy
            rate_kbps: Bandwidth limit in KB/s
        """
        toxic = {
            "name": f"{proxy_name}_bandwidth",
            "type": "bandwidth",
            "stream": "downstream",
            "toxicity": 1.0,
            "attributes": {"rate": rate_kbps},
        }

        r = requests.post(
            f"{self.base_url}/proxies/{proxy_name}/toxics", json=toxic, timeout=5
        )
        if not r.ok:
            raise Exception(f"Failed to add bandwidth limit: {r.text}")

    def add_timeout(self, proxy_name: str, timeout_ms: int):
        """
        Add timeout toxic - connections time out after specified duration

        Args:
            proxy_name: Name of the proxy
            timeout_ms: Timeout in milliseconds
        """
        toxic = {
            "name": f"{proxy_name}_timeout",
            "type": "timeout",
            "stream": "downstream",
            "toxicity": 1.0,
            "attributes": {"timeout": timeout_ms},
        }

        r = requests.post(
            f"{self.base_url}/proxies/{proxy_name}/toxics", json=toxic, timeout=5
        )
        if not r.ok:
            raise Exception(f"Failed to add timeout: {r.text}")

    def reset_proxy(self, proxy_name: str):
        """Remove all toxics from a proxy"""
        try:
            r = requests.get(
                f"{self.base_url}/proxies/{proxy_name}/toxics", timeout=5
            )
            if r.ok:
                toxics = r.json()
                for toxic in toxics:
                    requests.delete(
                        f"{self.base_url}/proxies/{proxy_name}/toxics/{toxic['name']}",
                        timeout=5,
                    )
        except Exception:
            pass

    def disable_proxy(self, proxy_name: str):
        """Disable a proxy (simulates service down)"""
        payload = {"enabled": False}
        requests.post(
            f"{self.base_url}/proxies/{proxy_name}", json=payload, timeout=5
        )

    def enable_proxy(self, proxy_name: str):
        """Enable a proxy"""
        payload = {"enabled": True}
        requests.post(
            f"{self.base_url}/proxies/{proxy_name}", json=payload, timeout=5
        )


@contextmanager
def chaos_proxy(
    name: str,
    listen_port: int,
    upstream_port: int,
    toxiproxy_host: str = "localhost",
):
    """
    Context manager for chaos proxy lifecycle

    Usage:
        with chaos_proxy("guard", 20000, 8011) as proxy:
            proxy.add_latency(500)  # Add 500ms latency
            # Run tests
    """
    client = ToxiproxyClient(toxiproxy_host)

    if not client.is_available():
        raise Exception(
            "Toxiproxy not available. Install: docker run -d -p 8474:8474 shopify/toxiproxy"
        )

    proxy_name = f"chaos_{name}"
    listen = f"127.0.0.1:{listen_port}"
    upstream = f"127.0.0.1:{upstream_port}"

    try:
        # Create proxy
        client.create_proxy(proxy_name, listen, upstream)

        # Yield a proxy controller
        class ProxyController:
            def add_latency(self, latency_ms: int, jitter_ms: int = 0):
                client.add_latency(proxy_name, latency_ms, jitter_ms)

            def add_bandwidth_limit(self, rate_kbps: int):
                client.add_bandwidth_limit(proxy_name, rate_kbps)

            def add_timeout(self, timeout_ms: int):
                client.add_timeout(proxy_name, timeout_ms)

            def disable(self):
                client.disable_proxy(proxy_name)

            def enable(self):
                client.enable_proxy(proxy_name)

            def reset(self):
                client.reset_proxy(proxy_name)

        yield ProxyController()

    finally:
        # Cleanup
        client.delete_proxy(proxy_name)


class NetworkChaos:
    """
    Helper class for simulating network chaos without Toxiproxy
    Uses Python mocking and delays
    """

    @staticmethod
    @contextmanager
    def inject_latency(target_func, latency_seconds: float):
        """
        Inject latency into a function call

        Usage:
            with NetworkChaos.inject_latency(requests.get, 2.0):
                # All requests.get calls will be delayed by 2 seconds
        """
        import time
        from unittest.mock import patch

        original_func = target_func

        def delayed_func(*args, **kwargs):
            time.sleep(latency_seconds)
            return original_func(*args, **kwargs)

        # Try to patch using import path string
        if hasattr(target_func, "__module__") and hasattr(target_func, "__name__"):
            patch_target = f"{target_func.__module__}.{target_func.__name__}"
            with patch(patch_target, delayed_func):
                yield
        else:
            raise TypeError(
                "target_func must be a function with __module__ and __name__ attributes (e.g., a module-level function)."
            )
    @staticmethod
    @contextmanager
    def simulate_packet_loss(loss_probability: float = 0.5):
        """
        Simulate packet loss by randomly failing requests

        Args:
            loss_probability: Probability of packet loss (0.0 to 1.0)
        """
        import random
        from unittest.mock import patch

        def lossy_request(*args, **kwargs):
            if random.random() < loss_probability:
                raise requests.exceptions.ConnectionError("Simulated packet loss")
            return requests.request(*args, **kwargs)

        with patch("requests.request", lossy_request):
            yield


class ServiceChaos:
    """Helper class for service-level chaos operations"""

    @staticmethod
    def kill_after_delay(process, delay_seconds: float):
        """
        Kill a process after a delay
        Useful for testing service death during operations
        """
        import threading

        def delayed_kill():
            time.sleep(delay_seconds)
            if process and hasattr(process, "kill"):
                process.kill()

        thread = threading.Thread(target=delayed_kill, daemon=True)
        thread.start()
        return thread

    @staticmethod
    @contextmanager
    def intermittent_failures(failure_rate: float = 0.3):
        """
        Simulate intermittent service failures

        Args:
            failure_rate: Probability of failure (0.0 to 1.0)
        """
        import random
        from unittest.mock import patch

        def flaky_request(*args, **kwargs):
            if random.random() < failure_rate:
                raise requests.exceptions.ConnectionError("Intermittent failure")
            return requests.request(*args, **kwargs)

        with patch("requests.request", flaky_request):
            yield


class ChaosScenario:
    """
    Predefined chaos scenarios for common failure patterns
    """

    @staticmethod
    def cascading_failure():
        """
        Simulate cascading failure scenario:
        1. Slow service causes backlog
        2. Backlog causes memory pressure
        3. System becomes unstable
        """
        pass  # Implementation would involve multiple chaos injections

    @staticmethod
    def network_partition():
        """
        Simulate network partition where some services can't reach others
        """
        pass

    @staticmethod
    def thundering_herd():
        """
        Simulate thundering herd problem:
        Multiple clients all retry at the same time after failure
        """
        pass


def validate_fail_closed(test_func):
    """
    Decorator to validate fail-closed behavior

    Usage:
        @validate_fail_closed
        def test_something():
            # Test code
            return should_deny  # Return True if properly denied
    """

    def wrapper(*args, **kwargs):
        result = test_func(*args, **kwargs)
        if not result:
            raise AssertionError(
                f"FAIL-CLOSED VIOLATION: {test_func.__name__} allowed operation during chaos"
            )
        return result

    return wrapper
