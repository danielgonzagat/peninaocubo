"""
PENIN Node - P2P Node Implementation

Implements a PENIN-Ω node that can communicate via the PENIN protocol,
handle status queries, and exchange knowledge with other nodes.
"""

import asyncio
from typing import Any

from penin.omega.sr import SROmegaService
from penin.p2p.protocol import MessageType, PeninMessage, PeninProtocol


class PeninNode:
    """
    PENIN-Ω P2P Node

    Handles P2P communication, including status queries and knowledge exchange.
    Integrates with SROmegaService to provide mental state introspection.
    """

    def __init__(self, node_id: str, sr_service: SROmegaService | None = None):
        """
        Initialize PENIN node

        Args:
            node_id: Unique identifier for this node
            sr_service: Optional SROmegaService instance (creates new one if not provided)
        """
        self.node_id = node_id
        self.protocol = PeninProtocol(node_id)
        self.sr_service = sr_service or SROmegaService()
        self.peers: dict[str, dict[str, Any]] = {}
        self.status_responses: dict[str, dict[str, Any]] = (
            {}
        )  # Store responses by peer_id

        # Register message handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register protocol message handlers"""
        self.protocol.register_handler(
            MessageType.STATUS_QUERY, self._handle_status_query
        )
        self.protocol.register_handler(
            MessageType.STATUS_REQUEST, self._handle_status_query
        )  # Same handler
        self.protocol.register_handler(
            MessageType.STATUS_RESPONSE, self._handle_status_response
        )
        self.protocol.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)

    async def _handle_status_query(self, message: PeninMessage) -> PeninMessage:
        """
        Handle incoming status query by returning mental state

        Args:
            message: Incoming status query message

        Returns:
            Status response message with mental state
        """
        # Get mental state from SR service
        mental_state = self.sr_service.get_mental_state()

        # Create response
        return self.protocol.create_status_response(mental_state)

    async def _handle_status_response(self, message: PeninMessage) -> None:
        """
        Handle incoming status response

        Args:
            message: Status response message containing mental state
        """
        sender_id = message.sender_id
        mental_state = message.payload.get("mental_state", {})

        # Store response
        self.status_responses[sender_id] = {
            "mental_state": mental_state,
            "timestamp": message.timestamp,
        }

    async def _handle_heartbeat(self, message: PeninMessage) -> PeninMessage:
        """
        Handle heartbeat message

        Args:
            message: Heartbeat message

        Returns:
            Heartbeat response
        """
        return self.protocol.create_heartbeat(status="healthy")

    async def query_peer_status(
        self, peer_id: str, timeout: float = 5.0
    ) -> dict[str, Any] | None:
        """
        Query the mental state of a peer node

        Args:
            peer_id: ID of the peer to query
            timeout: Timeout in seconds

        Returns:
            Mental state dictionary or None if query failed
        """
        # Create status query
        self.protocol.create_status_query(peer_id)

        # In a real implementation, this would send via network
        # For now, we simulate the response handling
        # This is a placeholder that would be replaced with actual network code

        # Wait for response (in real implementation, this would wait for network response)
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if peer_id in self.status_responses:
                response = self.status_responses.pop(peer_id)
                return response["mental_state"]
            await asyncio.sleep(0.1)

        return None

    async def handle_message(self, message: PeninMessage) -> PeninMessage | None:
        """
        Handle incoming message

        Args:
            message: Incoming message

        Returns:
            Response message or None
        """
        return await self.protocol.handle_message(message)

    def get_node_info(self) -> dict[str, Any]:
        """Get information about this node"""
        return {
            "node_id": self.node_id,
            "protocol_version": self.protocol.VERSION,
            "peers_count": len(self.peers),
            "sr_service_active": self.sr_service is not None,
        }
