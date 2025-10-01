"""
Tests for F7 Fractal Coherence feature in SR-Ω∞ Service
Tests the implementation of fractal coherence metric and endpoint
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from penin.omega.fractal import build_fractal, fractal_coherence, propagate_update


class TestFractalCoherenceF7:
    """Test F7: Fractal Coherence implementation"""

    def test_perfect_coherence(self):
        """Test perfect coherence (all nodes identical)"""
        root_cfg = {"alpha": 0.001, "beta": 0.9, "kappa": 25}
        tree = build_fractal(root_cfg, depth=2, branching=3)

        coherence = fractal_coherence(tree)
        assert coherence == 1.0, "Perfect coherence should be 1.0"

    def test_partial_coherence(self):
        """Test partial coherence after selective updates"""
        root_cfg = {"alpha": 0.001, "beta": 0.9, "kappa": 25}
        tree = build_fractal(root_cfg, depth=2, branching=2)

        # Modify only some nodes
        if tree.children:
            tree.children[0].config["alpha"] = 0.002  # Change one child

        coherence = fractal_coherence(tree)
        # Should be less than 1.0 but greater than 0
        assert 0.0 < coherence < 1.0, f"Partial coherence should be between 0 and 1, got {coherence}"

    def test_zero_coherence(self):
        """Test zero coherence (completely different configs)"""
        root_cfg = {"alpha": 0.001}
        tree = build_fractal(root_cfg, depth=1, branching=2)

        # Replace all child configs with completely different keys
        for child in tree.children:
            child.config = {"gamma": 0.5, "delta": 0.7}

        coherence = fractal_coherence(tree)
        assert coherence == 0.0, "Zero overlap should give 0.0 coherence"

    def test_coherence_ranges(self):
        """Test coherence interpretation ranges"""
        # Excellent range: FC >= 0.95
        root_cfg = {"a": 1, "b": 2, "c": 3}
        tree_excellent = build_fractal(root_cfg, depth=1, branching=1)
        fc_excellent = fractal_coherence(tree_excellent)
        assert fc_excellent >= 0.95, "Should be in excellent range"

        # Test with some divergence
        tree_partial = build_fractal(root_cfg, depth=1, branching=2)
        if tree_partial.children:
            # Change 1 of 3 values in first child
            tree_partial.children[0].config["a"] = 999
        fc_partial = fractal_coherence(tree_partial)
        assert 0.0 <= fc_partial < 1.0, "Should show partial coherence"

    def test_propagate_maintains_coherence(self):
        """Test that propagate_update maintains perfect coherence"""
        root_cfg = {"alpha": 0.001, "beta": 0.9}
        tree = build_fractal(root_cfg, depth=2, branching=2)

        # Update all nodes
        propagate_update(tree, {"alpha": 0.002, "beta": 0.95})

        coherence = fractal_coherence(tree)
        assert coherence == 1.0, "Propagate should maintain perfect coherence"

    def test_deep_tree_coherence(self):
        """Test coherence in deeper trees"""
        root_cfg = {"param": 1.0}
        tree = build_fractal(root_cfg, depth=4, branching=2)

        coherence = fractal_coherence(tree)
        assert coherence == 1.0, "Deep tree with same config should have perfect coherence"

        # Count nodes to verify tree structure
        node_count = sum(1 for _ in _traverse_tree(tree))
        # depth=4, branching=2 should give: 1 + 2 + 4 + 8 + 16 = 31 nodes
        assert node_count == 31, f"Expected 31 nodes, got {node_count}"

    def test_empty_config_coherence(self):
        """Test coherence with empty configurations"""
        root_cfg = {}
        tree = build_fractal(root_cfg, depth=1, branching=2)

        coherence = fractal_coherence(tree)
        # Empty configs should still be coherent (all empty)
        assert coherence == 1.0, "Empty configs should be coherent"

    def test_single_node_tree(self):
        """Test coherence with single node (no children)"""
        root_cfg = {"value": 42}
        tree = build_fractal(root_cfg, depth=0, branching=0)

        coherence = fractal_coherence(tree)
        assert coherence == 1.0, "Single node should have perfect coherence"


def _traverse_tree(root):
    """Helper to traverse all nodes"""
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(node.children)


class TestFractalCoherenceService:
    """Test SR-Ω∞ Service fractal coherence endpoint"""

    def test_fractal_endpoint_exists(self):
        """Test that fractal coherence endpoint exists"""
        from fastapi.testclient import TestClient

        from penin.sr.sr_service import app

        client = TestClient(app)

        # Test with simple request
        response = client.post(
            "/sr/fractal_coherence",
            json={"root_config": {"alpha": 0.001}, "depth": 1, "branching": 2},
        )

        assert response.status_code == 200, f"Endpoint should exist, got {response.status_code}"
        data = response.json()
        assert "fractal_coherence" in data
        assert "tree_depth" in data
        assert "branching_factor" in data
        assert "total_nodes" in data
        assert "metric_name" in data

    def test_fractal_endpoint_coherence_value(self):
        """Test that endpoint returns correct coherence value"""
        from fastapi.testclient import TestClient

        from penin.sr.sr_service import app

        client = TestClient(app)

        response = client.post(
            "/sr/fractal_coherence",
            json={"root_config": {"a": 1, "b": 2}, "depth": 2, "branching": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["fractal_coherence"] == 1.0, "Perfect coherence expected"
        assert data["tree_depth"] == 2
        assert data["branching_factor"] == 2
        assert data["metric_name"] == "penin_fractal_coherence"

    def test_fractal_endpoint_custom_depth(self):
        """Test endpoint with custom depth and branching"""
        from fastapi.testclient import TestClient

        from penin.sr.sr_service import app

        client = TestClient(app)

        response = client.post(
            "/sr/fractal_coherence",
            json={"root_config": {"x": 100}, "depth": 3, "branching": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["fractal_coherence"] <= 1.0
        # depth=3, branching=3: 1 + 3 + 9 + 27 = 40 nodes
        assert data["total_nodes"] == 40

    def test_metrics_endpoint_exists(self):
        """Test that Prometheus metrics endpoint exists"""
        from fastapi.testclient import TestClient

        from penin.sr.sr_service import app

        client = TestClient(app)

        # First compute a fractal coherence to populate the metric
        client.post(
            "/sr/fractal_coherence",
            json={"root_config": {"test": 1}, "depth": 1, "branching": 1},
        )

        # Check metrics endpoint
        response = client.get("/metrics")
        assert response.status_code == 200
        content = response.text
        assert "penin_fractal_coherence" in content, "Metric should be exposed in /metrics"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
