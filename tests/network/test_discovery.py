"""
Tests for PENIN Network Discovery
==================================

Tests for UDP-based peer discovery service.
"""

import json
import socket
import time

import pytest

from penin.network.discovery import PeerDiscoveryService


class TestPeerDiscoveryService:
    """Test PeerDiscoveryService functionality."""

    def test_initialization(self):
        """Test service initialization."""
        service = PeerDiscoveryService(
            node_id="test-node-1",
            port=51515,
            broadcast_interval=10,
        )

        assert service.node_id == "test-node-1"
        assert service.port == 51515
        assert service.broadcast_interval == 10
        assert not service.is_running
        assert len(service.get_discovered_peers()) == 0

    def test_start_and_stop(self):
        """Test starting and stopping the service."""
        service = PeerDiscoveryService(
            node_id="test-node-2",
            port=51516,  # Use different port
            broadcast_interval=1,
        )

        # Start service
        service.start()
        assert service.is_running

        # Give threads time to start
        time.sleep(0.5)

        # Stop service
        service.stop()
        assert not service.is_running

    def test_callback_on_peer_discovered(self):
        """Test that callback is called when peer is discovered."""
        discovered_peers = []

        def callback(peer_info):
            discovered_peers.append(peer_info)

        # Create two services with different IDs
        service1 = PeerDiscoveryService(
            node_id="node-1",
            port=51517,
            broadcast_interval=1,
            on_peer_discovered=callback,
        )

        service2 = PeerDiscoveryService(
            node_id="node-2",
            port=51517,
            broadcast_interval=1,
        )

        try:
            # Start both services
            service1.start()
            service2.start()

            # Wait for discovery to happen
            time.sleep(2.5)

            # Check that node-1 discovered node-2
            assert len(discovered_peers) > 0
            peer_ids = [p["id"] for p in discovered_peers]
            assert "node-2" in peer_ids

            # Verify discovered peer structure
            peer_info = discovered_peers[0]
            assert "id" in peer_info
            assert "address" in peer_info
            assert "port" in peer_info
            assert "timestamp" in peer_info

        finally:
            service1.stop()
            service2.stop()

    def test_broadcast_message_format(self):
        """Test that broadcast messages have correct format."""
        service = PeerDiscoveryService(
            node_id="test-broadcast",
            port=51518,
            broadcast_interval=1,
        )

        # Create a listener to capture broadcast
        listener_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listener_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener_sock.bind(("0.0.0.0", 51518))
        listener_sock.settimeout(3.0)

        try:
            service.start()

            # Wait for broadcast
            data, addr = listener_sock.recvfrom(1024)
            message = json.loads(data.decode("utf-8"))

            # Validate message structure
            assert "id" in message
            assert message["id"] == "test-broadcast"
            assert "port" in message
            assert message["port"] == 51518
            assert "timestamp" in message
            assert isinstance(message["timestamp"], (int, float))

        finally:
            service.stop()
            listener_sock.close()

    def test_ignore_self_messages(self):
        """Test that a node ignores its own broadcast messages."""
        discovered_peers = []

        def callback(peer_info):
            discovered_peers.append(peer_info)

        service = PeerDiscoveryService(
            node_id="self-test",
            port=51519,
            broadcast_interval=1,
            on_peer_discovered=callback,
        )

        try:
            service.start()
            time.sleep(2.5)

            # Should not have discovered itself
            peer_ids = [p["id"] for p in discovered_peers]
            assert "self-test" not in peer_ids

        finally:
            service.stop()

    def test_get_discovered_peers(self):
        """Test getting the list of discovered peers."""
        service1 = PeerDiscoveryService(
            node_id="getter-1",
            port=51520,
            broadcast_interval=1,
        )

        service2 = PeerDiscoveryService(
            node_id="getter-2",
            port=51520,
            broadcast_interval=1,
        )

        try:
            service1.start()
            service2.start()

            # Wait for discovery
            time.sleep(2.5)

            # Check discovered peers
            peers1 = service1.get_discovered_peers()
            peers2 = service2.get_discovered_peers()

            assert "getter-2" in peers1
            assert "getter-1" in peers2

        finally:
            service1.stop()
            service2.stop()

    def test_multiple_peers_discovery(self):
        """Test discovery with multiple peers."""
        services = []
        node_ids = ["multi-1", "multi-2", "multi-3"]

        try:
            # Create and start multiple services
            for node_id in node_ids:
                service = PeerDiscoveryService(
                    node_id=node_id,
                    port=51521,
                    broadcast_interval=1,
                )
                service.start()
                services.append(service)

            # Wait for discovery
            time.sleep(3.5)

            # Each node should discover all others
            for i, service in enumerate(services):
                discovered = service.get_discovered_peers()
                # Should discover all except self
                expected_peers = set(node_ids) - {node_ids[i]}
                # At least some peers should be discovered
                assert len(discovered) > 0
                assert discovered.issubset(expected_peers)

        finally:
            for service in services:
                service.stop()

    def test_invalid_json_handling(self):
        """Test that invalid JSON messages are handled gracefully."""
        service = PeerDiscoveryService(
            node_id="json-test",
            port=51522,
            broadcast_interval=10,
        )

        try:
            service.start()
            time.sleep(0.5)

            # Send invalid JSON
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(b"not valid json", ("127.0.0.1", 51522))
            sock.close()

            # Service should continue running
            time.sleep(0.5)
            assert service.is_running

        finally:
            service.stop()

    def test_invalid_message_structure(self):
        """Test handling of messages with invalid structure."""
        discovered_peers = []

        def callback(peer_info):
            discovered_peers.append(peer_info)

        service = PeerDiscoveryService(
            node_id="struct-test",
            port=51523,
            broadcast_interval=10,
            on_peer_discovered=callback,
        )

        try:
            service.start()
            time.sleep(0.5)

            # Send valid JSON but invalid structure (missing 'id')
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = json.dumps({"port": 51523, "timestamp": time.time()})
            sock.sendto(message.encode("utf-8"), ("127.0.0.1", 51523))
            sock.close()

            time.sleep(0.5)

            # Callback should not be called for invalid message
            assert len(discovered_peers) == 0
            assert service.is_running

        finally:
            service.stop()

    def test_thread_safety(self):
        """Test thread-safe access to discovered peers."""
        service = PeerDiscoveryService(
            node_id="thread-test",
            port=51524,
            broadcast_interval=1,
        )

        try:
            service.start()

            # Access discovered peers from multiple threads
            import threading

            results = []

            def access_peers():
                for _ in range(10):
                    peers = service.get_discovered_peers()
                    results.append(len(peers))
                    time.sleep(0.1)

            threads = [threading.Thread(target=access_peers) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Should complete without errors
            assert len(results) == 30

        finally:
            service.stop()
