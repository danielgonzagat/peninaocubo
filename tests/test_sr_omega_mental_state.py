"""
Tests for SROmegaService mental state tracking and P2P status queries
"""


import pytest

from penin.omega.sr import SROmegaService
from penin.p2p.node import PeninNode
from penin.p2p.protocol import MessageType, PeninProtocol


class TestSROmegaService:
    """Test SROmegaService mental state tracking"""

    def test_service_initialization(self):
        """Test service initializes correctly"""
        service = SROmegaService()
        assert service.pending_recommendations == []
        assert service.recent_outcomes == []
        assert service.task_success_rates == {}

    def test_add_recommendation(self):
        """Test adding recommendations"""
        service = SROmegaService()
        service.add_recommendation("rec-001", "task-1", 0.85, {"priority": "high"})

        assert len(service.pending_recommendations) == 1
        rec = service.pending_recommendations[0]
        assert rec.recommendation_id == "rec-001"
        assert rec.task == "task-1"
        assert rec.expected_sr == 0.85
        assert rec.metadata["priority"] == "high"

    def test_report_outcome_success(self):
        """Test reporting successful outcome"""
        service = SROmegaService()
        service.add_recommendation("rec-001", "task-1", 0.85)
        service.report_outcome("rec-001", success=True, actual_sr=0.90, message="Great!")

        # Should be removed from pending
        assert len(service.pending_recommendations) == 0

        # Should be in outcomes
        assert len(service.recent_outcomes) == 1
        outcome = service.recent_outcomes[0]
        assert outcome.recommendation_id == "rec-001"
        assert outcome.success is True
        assert outcome.actual_sr == 0.90
        assert outcome.message == "Great!"

    def test_report_outcome_failure(self):
        """Test reporting failed outcome"""
        service = SROmegaService()
        service.add_recommendation("rec-001", "task-1", 0.85)
        service.report_outcome("rec-001", success=False, actual_sr=0.40, message="Failed")

        assert len(service.recent_outcomes) == 1
        outcome = service.recent_outcomes[0]
        assert outcome.success is False

    def test_max_pending_limit(self):
        """Test that pending recommendations are limited"""
        service = SROmegaService(max_pending=3)
        for i in range(5):
            service.add_recommendation(f"rec-{i}", f"task-{i}", 0.85)

        # Should only keep last 3
        assert len(service.pending_recommendations) == 3
        assert service.pending_recommendations[0].recommendation_id == "rec-2"

    def test_max_outcomes_limit(self):
        """Test that outcomes are limited"""
        service = SROmegaService(max_outcomes=3)
        for i in range(5):
            service.report_outcome(f"rec-{i}", success=True, actual_sr=0.85)

        # Should only keep last 3
        assert len(service.recent_outcomes) == 3
        assert service.recent_outcomes[0].recommendation_id == "rec-2"

    def test_get_mental_state_empty(self):
        """Test get_mental_state with no data"""
        service = SROmegaService()
        state = service.get_mental_state()

        assert "pending_recommendations" in state
        assert "recent_outcomes" in state
        assert "current_concerns" in state
        assert "sr_statistics" in state
        assert "timestamp" in state

        assert len(state["pending_recommendations"]) == 0
        assert len(state["recent_outcomes"]) == 0
        assert len(state["current_concerns"]) == 0

    def test_get_mental_state_with_data(self):
        """Test get_mental_state with data"""
        service = SROmegaService()
        service.add_recommendation("rec-001", "task-1", 0.85, {"priority": "high"})
        service.add_recommendation("rec-002", "task-2", 0.75)
        service.report_outcome("rec-003", success=True, actual_sr=0.90, message="Success")

        state = service.get_mental_state()

        # Check pending recommendations
        assert len(state["pending_recommendations"]) == 2
        assert state["pending_recommendations"][0]["id"] == "rec-001"
        assert state["pending_recommendations"][0]["task"] == "task-1"
        assert state["pending_recommendations"][0]["expected_sr"] == 0.85
        assert "age_seconds" in state["pending_recommendations"][0]

        # Check recent outcomes
        assert len(state["recent_outcomes"]) == 1
        assert state["recent_outcomes"][0]["id"] == "rec-003"
        assert state["recent_outcomes"][0]["success"] is True

    def test_current_concerns_detection(self):
        """Test that concerns are detected for low success rates"""
        service = SROmegaService()

        # Add a task with low success rate
        for i in range(5):
            service.add_recommendation(f"rec-{i}", "failing-task", 0.85)
            # Report mostly failures
            success = i == 4  # Only last one succeeds
            service.report_outcome(f"rec-{i}", success=success, actual_sr=0.5 if success else 0.2)

        state = service.get_mental_state()

        # Should detect concern
        assert len(state["current_concerns"]) > 0
        concern = state["current_concerns"][0]
        assert concern["task"] == "failing-task"
        assert concern["success_rate"] < 0.5
        assert "severity" in concern


class TestPeninNode:
    """Test PeninNode P2P functionality"""

    def test_node_initialization(self):
        """Test node initializes correctly"""
        node = PeninNode("test-node")
        assert node.node_id == "test-node"
        assert node.sr_service is not None
        assert node.protocol is not None

    def test_node_with_custom_service(self):
        """Test node with custom SR service"""
        service = SROmegaService()
        service.add_recommendation("rec-001", "task-1", 0.85)

        node = PeninNode("test-node", service)
        assert node.sr_service == service
        assert len(node.sr_service.pending_recommendations) == 1

    @pytest.mark.asyncio
    async def test_handle_status_query(self):
        """Test handling status query"""
        service = SROmegaService()
        service.add_recommendation("rec-001", "task-1", 0.85)

        node = PeninNode("test-node", service)

        # Create a status query
        query = node.protocol.create_status_query("test-node")

        # Handle it
        response = await node.handle_message(query)

        assert response is not None
        assert response.msg_type == MessageType.STATUS_RESPONSE
        assert "mental_state" in response.payload

        # Check mental state content
        mental_state = response.payload["mental_state"]
        assert "pending_recommendations" in mental_state
        assert len(mental_state["pending_recommendations"]) == 1

    @pytest.mark.asyncio
    async def test_handle_heartbeat(self):
        """Test handling heartbeat"""
        node = PeninNode("test-node")
        heartbeat = node.protocol.create_heartbeat()
        response = await node.handle_message(heartbeat)

        assert response is not None
        assert response.msg_type == MessageType.HEARTBEAT

    def test_get_node_info(self):
        """Test getting node info"""
        node = PeninNode("test-node")
        info = node.get_node_info()

        assert info["node_id"] == "test-node"
        assert "protocol_version" in info
        assert "sr_service_active" in info
        assert info["sr_service_active"] is True


class TestPeninProtocol:
    """Test protocol message creation"""

    def test_create_status_query(self):
        """Test creating status query message"""
        protocol = PeninProtocol("node-001")
        query = protocol.create_status_query("target-node")

        assert query.msg_type == MessageType.STATUS_QUERY
        assert query.sender_id == "node-001"
        assert query.payload["requester_id"] == "node-001"
        assert query.payload["target_peer_id"] == "target-node"

    def test_create_status_response(self):
        """Test creating status response message"""
        protocol = PeninProtocol("node-001")
        mental_state = {
            "pending_recommendations": [],
            "recent_outcomes": [],
            "current_concerns": [],
        }
        response = protocol.create_status_response(mental_state)

        assert response.msg_type == MessageType.STATUS_RESPONSE
        assert response.sender_id == "node-001"
        assert response.payload["mental_state"] == mental_state

    def test_message_serialization(self):
        """Test message serialization/deserialization"""
        protocol = PeninProtocol("node-001")
        mental_state = {"test": "data"}
        response = protocol.create_status_response(mental_state)

        # Serialize to JSON
        json_str = response.to_json()
        assert isinstance(json_str, str)

        # Deserialize back
        from penin.p2p.protocol import PeninMessage

        restored = PeninMessage.from_json(json_str)
        assert restored.msg_type == response.msg_type
        assert restored.sender_id == response.sender_id
        assert restored.payload == response.payload


class TestIntegration:
    """Integration tests for complete flow"""

    @pytest.mark.asyncio
    async def test_complete_status_query_flow(self):
        """Test complete status query flow"""
        # Create two nodes
        service1 = SROmegaService()
        service1.add_recommendation("rec-001", "task-1", 0.85, {"priority": "high"})
        service1.report_outcome("rec-002", success=True, actual_sr=0.92)

        node1 = PeninNode("node-001", service1)
        node2 = PeninNode("node-002", SROmegaService())

        # Node 2 queries Node 1
        query = node2.protocol.create_status_query("node-001")

        # Simulate message passing (in real implementation, this would go over network)
        response = await node1.handle_message(query)

        # Node 2 handles response
        await node2.handle_message(response)

        # Verify response was stored
        assert "node-001" in node2.status_responses
        stored_state = node2.status_responses["node-001"]["mental_state"]

        assert len(stored_state["pending_recommendations"]) == 1
        assert stored_state["pending_recommendations"][0]["id"] == "rec-001"
        assert len(stored_state["recent_outcomes"]) == 1
        assert stored_state["recent_outcomes"][0]["success"] is True

    @pytest.mark.asyncio
    async def test_mental_state_with_concerns(self):
        """Test mental state includes concerns when appropriate"""
        service = SROmegaService()

        # Create a task with multiple failures
        task_name = "problematic-task"
        for i in range(5):
            service.add_recommendation(f"rec-{i}", task_name, 0.85)
            # Only 1 out of 5 succeeds
            success = i == 0
            service.report_outcome(f"rec-{i}", success=success, actual_sr=0.8 if success else 0.3)

        state = service.get_mental_state()

        # Should have a concern
        concerns = state["current_concerns"]
        assert len(concerns) > 0

        concern = concerns[0]
        assert concern["task"] == task_name
        assert concern["success_rate"] == 0.2  # 1/5
        assert concern["total_attempts"] == 5
        assert concern["severity"] == "high"  # Since rate < 0.3
