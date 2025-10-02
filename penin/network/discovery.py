"""
PENIN Peer Discovery Service
=============================

UDP-based peer discovery for local network.
Implements Phase 5: The Agora - curing "Social Isolation".
"""

import json
import logging
import socket
import threading
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PeerDiscoveryService:
    """
    Peer Discovery Service using UDP broadcast.
    
    Allows PENIN nodes to discover each other on the local network.
    Broadcasts node information periodically and listens for other nodes.
    """

    def __init__(
        self,
        node_id: str,
        port: int = 51515,
        broadcast_interval: int = 10,
        on_peer_discovered: Callable[[dict[str, Any]], None] | None = None,
    ):
        """
        Initialize Peer Discovery Service.

        Args:
            node_id: Unique identifier for this node
            port: UDP port for discovery (default: 51515)
            broadcast_interval: Seconds between broadcasts (default: 10)
            on_peer_discovered: Callback when a new peer is discovered
        """
        self.node_id = node_id
        self.port = port
        self.broadcast_interval = broadcast_interval
        self.on_peer_discovered = on_peer_discovered

        self._running = False
        self._broadcaster_thread: threading.Thread | None = None
        self._listener_thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._discovered_peers: set[str] = set()

    def start(self) -> None:
        """Start the discovery service (broadcaster and listener)."""
        if self._running:
            logger.warning("Discovery service already running")
            return

        self._running = True

        # Start broadcaster thread
        self._broadcaster_thread = threading.Thread(
            target=self._broadcast_loop,
            daemon=True,
            name=f"PeerDiscovery-Broadcaster-{self.node_id}",
        )
        self._broadcaster_thread.start()

        # Start listener thread
        self._listener_thread = threading.Thread(
            target=self._listener_loop,
            daemon=True,
            name=f"PeerDiscovery-Listener-{self.node_id}",
        )
        self._listener_thread.start()

        logger.info(
            f"Peer discovery service started on port {self.port} "
            f"(broadcast interval: {self.broadcast_interval}s)"
        )

    def stop(self) -> None:
        """Stop the discovery service."""
        if not self._running:
            return

        self._running = False

        # Wait for threads to finish (with timeout)
        if self._broadcaster_thread:
            self._broadcaster_thread.join(timeout=2.0)
        if self._listener_thread:
            self._listener_thread.join(timeout=2.0)

        logger.info("Peer discovery service stopped")

    def _broadcast_loop(self) -> None:
        """Broadcast node information periodically."""
        while self._running:
            try:
                self._broadcast_presence()
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}", exc_info=True)

            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.broadcast_interval * 10):
                if not self._running:
                    break
                time.sleep(0.1)

    def _broadcast_presence(self) -> None:
        """Send a single broadcast message."""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Prepare message
            message = {
                "id": self.node_id,
                "port": self.port,
                "timestamp": time.time(),
            }
            message_bytes = json.dumps(message).encode("utf-8")

            # Broadcast to the network
            sock.sendto(message_bytes, ("255.255.255.255", self.port))
            sock.close()

            logger.debug(f"Broadcasted presence: {message}")

        except Exception as e:
            logger.error(f"Error broadcasting presence: {e}")

    def _listener_loop(self) -> None:
        """Listen for broadcast messages from other nodes."""
        sock = None
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", self.port))
            sock.settimeout(1.0)  # Timeout to allow checking _running flag

            logger.info(f"Listening for peers on 0.0.0.0:{self.port}")

            while self._running:
                try:
                    data, addr = sock.recvfrom(1024)
                    self._handle_discovery_message(data, addr)
                except socket.timeout:
                    # Timeout is expected, just continue
                    continue
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")

        except Exception as e:
            logger.error(f"Error in listener loop: {e}", exc_info=True)
        finally:
            if sock:
                sock.close()

    def _handle_discovery_message(self, data: bytes, addr: tuple) -> None:
        """
        Handle a received discovery message.

        Args:
            data: Raw message bytes
            addr: Source address (ip, port)
        """
        try:
            message = json.loads(data.decode("utf-8"))

            # Validate message structure
            if not isinstance(message, dict) or "id" not in message:
                logger.warning(f"Invalid discovery message from {addr}: {message}")
                return

            peer_id = message["id"]

            # Ignore messages from self
            if peer_id == self.node_id:
                return

            # Check if this is a new peer
            with self._lock:
                is_new_peer = peer_id not in self._discovered_peers
                if is_new_peer:
                    self._discovered_peers.add(peer_id)

            if is_new_peer:
                logger.info(f"Discovered new peer: {peer_id} at {addr[0]}")

                # Call the callback if provided
                if self.on_peer_discovered:
                    peer_info = {
                        "id": peer_id,
                        "address": addr[0],
                        "port": message.get("port", self.port),
                        "timestamp": message.get("timestamp", time.time()),
                    }
                    try:
                        self.on_peer_discovered(peer_info)
                    except Exception as e:
                        logger.error(f"Error in peer discovered callback: {e}")

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from {addr}: {e}")
        except Exception as e:
            logger.error(f"Error handling discovery message: {e}", exc_info=True)

    def get_discovered_peers(self) -> set[str]:
        """
        Get the set of discovered peer IDs.

        Returns:
            Set of peer IDs
        """
        with self._lock:
            return self._discovered_peers.copy()

    @property
    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._running
