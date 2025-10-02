"""
PENIN Protocol - Core P2P Protocol Implementation

Defines message types, serialization, and protocol handlers for PENIN-Ω P2P communication.
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    """Protocol message types"""

    # Discovery
    PEER_ANNOUNCE = "peer_announce"
    PEER_QUERY = "peer_query"
    PEER_RESPONSE = "peer_response"

    # Knowledge Exchange
    KNOWLEDGE_OFFER = "knowledge_offer"
    KNOWLEDGE_REQUEST = "knowledge_request"
    KNOWLEDGE_TRANSFER = "knowledge_transfer"
    KNOWLEDGE_ACK = "knowledge_ack"

    # Metrics & Status
    METRICS_BROADCAST = "metrics_broadcast"
    STATUS_REQUEST = "status_request"
    STATUS_QUERY = "status_request"  # Alias for STATUS_REQUEST
    STATUS_RESPONSE = "status_response"

    # Consensus & Governance
    PROPOSAL = "proposal"
    VOTE = "vote"
    CONSENSUS_REACHED = "consensus_reached"

    # System
    HEARTBEAT = "heartbeat"
    ERROR = "error"


@dataclass
class PeninMessage:
    """Base PENIN Protocol message"""

    msg_type: MessageType
    sender_id: str
    timestamp: float
    payload: dict[str, Any]
    signature: str | None = None
    msg_id: str | None = None

    def __post_init__(self):
        if self.msg_id is None:
            self.msg_id = self._generate_msg_id()

    def _generate_msg_id(self) -> str:
        """Generate unique message ID"""
        content = f"{self.msg_type}:{self.sender_id}:{self.timestamp}:{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "msg_type": self.msg_type.value,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "signature": self.signature,
            "msg_id": self.msg_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PeninMessage":
        """Deserialize from dictionary"""
        return cls(
            msg_type=MessageType(data["msg_type"]),
            sender_id=data["sender_id"],
            timestamp=data["timestamp"],
            payload=data["payload"],
            signature=data.get("signature"),
            msg_id=data.get("msg_id"),
        )

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "PeninMessage":
        """Deserialize from JSON"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class PeerInfo:
    """Peer information structure"""

    peer_id: str
    multiaddrs: list[str]
    specializations: list[str]
    metrics: dict[str, float]
    version: str
    timestamp: float


@dataclass
class KnowledgeAsset:
    """Knowledge asset (model, topology, function, etc.)"""

    asset_id: str
    asset_type: str  # "model", "topology", "function", "dataset"
    name: str
    description: str
    size_bytes: int
    hash: str  # Content hash (SHA-256)
    metadata: dict[str, Any]
    performance: dict[str, float]  # Metrics (accuracy, L∞, CAOS+, etc.)
    cost: float  # Training cost or value
    created_at: float
    owner_id: str


class PeninProtocol:
    """PENIN Protocol implementation"""

    VERSION = "1.0.0"
    PROTOCOL_ID = "/penin/1.0.0"

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.message_handlers: dict[MessageType, callable] = {}

    def register_handler(self, msg_type: MessageType, handler: callable):
        """Register message handler"""
        self.message_handlers[msg_type] = handler

    def create_message(
        self, msg_type: MessageType, payload: dict[str, Any]
    ) -> PeninMessage:
        """Create a new protocol message"""
        return PeninMessage(
            msg_type=msg_type,
            sender_id=self.node_id,
            timestamp=time.time(),
            payload=payload,
        )

    async def handle_message(self, message: PeninMessage) -> PeninMessage | None:
        """Handle incoming message"""
        handler = self.message_handlers.get(message.msg_type)
        if handler:
            return await handler(message)
        return None

    # --- Message Creators ---

    def create_peer_announce(
        self,
        multiaddrs: list[str],
        specializations: list[str],
        metrics: dict[str, float],
    ) -> PeninMessage:
        """Create peer announcement message"""
        return self.create_message(
            MessageType.PEER_ANNOUNCE,
            {
                "multiaddrs": multiaddrs,
                "specializations": specializations,
                "metrics": metrics,
                "version": self.VERSION,
            },
        )

    def create_knowledge_offer(self, asset: KnowledgeAsset) -> PeninMessage:
        """Create knowledge offer message"""
        return self.create_message(MessageType.KNOWLEDGE_OFFER, asdict(asset))

    def create_knowledge_request(
        self, asset_id: str, offer_terms: dict[str, Any]
    ) -> PeninMessage:
        """Create knowledge request message"""
        return self.create_message(
            MessageType.KNOWLEDGE_REQUEST,
            {"asset_id": asset_id, "terms": offer_terms, "requester_id": self.node_id},
        )

    def create_metrics_broadcast(
        self,
        linf: float,
        caos_plus: float,
        sr_score: float,
        rho: float,
        ece: float,
        rho_bias: float,
    ) -> PeninMessage:
        """Create metrics broadcast message"""
        return self.create_message(
            MessageType.METRICS_BROADCAST,
            {
                "linf": linf,
                "caos_plus": caos_plus,
                "sr_score": sr_score,
                "rho": rho,
                "ece": ece,
                "rho_bias": rho_bias,
                "timestamp": time.time(),
            },
        )

    def create_heartbeat(self, status: str = "healthy") -> PeninMessage:
        """Create heartbeat message"""
        return self.create_message(
            MessageType.HEARTBEAT, {"status": status, "node_id": self.node_id}
        )

    def create_error(
        self, error_msg: str, context: dict[str, Any] | None = None
    ) -> PeninMessage:
        """Create error message"""
        return self.create_message(
            MessageType.ERROR,
            {"error": error_msg, "context": context or {}, "timestamp": time.time()},
        )

    def create_status_query(self, target_peer_id: str | None = None) -> PeninMessage:
        """Create status query message"""
        return self.create_message(
            MessageType.STATUS_QUERY,
            {"requester_id": self.node_id, "target_peer_id": target_peer_id},
        )

    def create_status_response(self, mental_state: dict[str, Any]) -> PeninMessage:
        """Create status response message with mental state"""
        return self.create_message(
            MessageType.STATUS_RESPONSE, {"mental_state": mental_state}
        )
