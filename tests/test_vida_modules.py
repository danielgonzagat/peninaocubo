"""
Tests for Vida+ Modules
========================

Tests for fractal, swarm, kratos, market, neural_chain, and other new modules.
"""

import pytest
import tempfile
from pathlib import Path


def test_fractal_build():
    """Test fractal structure building"""
    from penin.omega.fractal import build_fractal, count_nodes, propagate_update

    root = build_fractal({"test": "value"}, depth=2, branching=3)

    assert root is not None
    assert root.depth == 0
    assert len(root.children) == 3
    assert count_nodes(root) == 1 + 3 + 9  # Root + level 1 + level 2

    # Test propagation
    updated = propagate_update(root, {"new_key": "new_value"})
    assert updated == 13  # All nodes updated
    assert root.config["new_key"] == "new_value"


def test_swarm_heartbeat():
    """Test swarm heartbeat system"""
    from penin.omega.swarm import heartbeat, sample_global_state, get_nodes

    # Send some heartbeats
    heartbeat("node-test-1", {"phi": 0.7, "sr": 0.85})
    heartbeat("node-test-2", {"phi": 0.8, "sr": 0.90})

    # Sample global state
    state = sample_global_state(window_s=60.0)
    assert "phi" in state or "sr" in state  # At least one metric present

    # Check nodes
    nodes = get_nodes(window_s=60.0)
    assert len(nodes) >= 2


def test_caos_kratos():
    """Test CAOS-KRATOS exploration mode"""
    from penin.omega.caos_kratos import phi_kratos, should_explore

    phi_k = phi_kratos(0.7, 0.7, 0.8, 0.8, exploration_factor=2.0)

    assert phi_k >= 0.0
    assert phi_k <= 1.0

    # Should explore with high phi and sigma OK
    assert should_explore(phi_kratos=0.6, threshold=0.5, sigma_guard_ok=True)

    # Should not explore with sigma guard failed
    assert not should_explore(phi_kratos=0.6, threshold=0.5, sigma_guard_ok=False)


def test_market_matching():
    """Test internal market matching"""
    from penin.omega.market import InternalMarket, Need, Offer

    market = InternalMarket()

    needs = [Need("agent1", "cpu", 10.0, 5.0), Need("agent2", "memory", 8.0, 3.0)]

    offers = [Offer("agent3", "cpu", 15.0, 4.0), Offer("agent4", "memory", 10.0, 2.5)]

    trades = market.match(needs, offers)

    assert len(trades) == 2
    assert trades[0][2] == 10.0  # Full CPU need satisfied
    assert trades[1][2] == 8.0  # Full memory need satisfied


def test_neural_chain():
    """Test neural blockchain"""
    from penin.omega.neural_chain import add_block, get_chain_length, get_latest_block

    # Add some blocks
    hash1 = add_block({"state": "initial"}, None)
    assert hash1 is not None

    hash2 = add_block({"state": "updated"}, hash1)
    assert hash2 is not None
    assert hash2 != hash1

    # Check length
    length = get_chain_length()
    assert length >= 2

    # Get latest block
    latest = get_latest_block()
    assert latest is not None
    assert "hash" in latest
    assert "state" in latest


def test_api_metabolizer():
    """Test API metabolization"""
    from penin.omega.api_metabolizer import record_call, suggest_replay, get_provider_stats

    # Record a call
    record_call("test_provider", "/test/endpoint", {"prompt": "test prompt"}, {"response": "test response"})

    # Try to get stats
    stats = get_provider_stats("test_provider")
    assert stats["count"] >= 1


def test_self_rag():
    """Test Self-RAG system"""
    from penin.omega.self_rag import ingest_text, query, self_cycle

    # Ingest some text
    ingest_text("test_doc", "This is about PENIN evolution and safety measures")

    # Query
    result = query("evolution safety")
    assert result["doc"] == "test_doc.txt" or result["doc"] is None

    # Self cycle
    cycle = self_cycle()
    assert "q1" in cycle
    assert "a1" in cycle


def test_immunity():
    """Test immunity system"""
    from penin.omega.immunity import anomaly_score, guard, diagnose

    # Normal metrics
    normal = {"phi": 0.7, "sr": 0.85, "G": 0.9}
    assert anomaly_score(normal) == 0.0
    assert guard(normal, trigger=1.0)

    # Anomalous metrics
    anomalous = {"phi": float("nan"), "sr": -0.5, "G": 1e10}
    assert anomaly_score(anomalous) > 0.0
    assert not guard(anomalous, trigger=1.0)

    # Diagnose
    diag = diagnose(anomalous)
    assert diag["num_issues"] > 0
    assert not diag["healthy"]


def test_checkpoint():
    """Test checkpoint system"""
    from penin.omega.checkpoint import save_snapshot, restore_last, list_snapshots

    # Save snapshot
    state = {"phi": 0.7, "sr": 0.85, "cycle": 10}
    path = save_snapshot(state)
    assert path is not None

    # List snapshots
    snaps = list_snapshots()
    assert len(snaps) >= 1

    # Restore
    restored = restore_last()
    assert restored is not None
    assert restored["phi"] == 0.7


def test_game_optimizer():
    """Test GAME optimizer"""
    from penin.omega.game import GAMEOptimizer, ema_grad

    # Test EMA
    ema = ema_grad(0.5, 0.8, beta=0.9)
    assert 0.5 < ema < 0.8

    # Test optimizer
    opt = GAMEOptimizer(beta=0.9, lr=0.01)

    update1 = opt.step(1.0)
    assert update1 < 0  # Negative because we use -lr * ema

    update2 = opt.step(0.5)
    assert update2 != update1


def test_darwin_audit():
    """Test darwinian selection"""
    from penin.omega.darwin_audit import darwinian_score, select_variant

    # High quality variant
    score_high = darwinian_score(life_ok=True, caos_phi=0.8, sr=0.85, G=0.9, L_inf=0.88)

    # Low quality variant
    score_low = darwinian_score(life_ok=True, caos_phi=0.3, sr=0.85, G=0.9, L_inf=0.88)

    assert score_high > score_low

    # Failed life equation
    score_fail = darwinian_score(life_ok=False, caos_phi=0.9, sr=0.95, G=0.95, L_inf=0.95)

    assert score_fail == 0.0

    # Select variant
    variants = [{"darwin_score": score_high}, {"darwin_score": score_low}]

    best = select_variant(variants)
    assert best["darwin_score"] == score_high


def test_zero_consciousness():
    """Test zero-consciousness proof"""
    from penin.omega.zero_consciousness import spi_proxy, assert_zero_consciousness

    # Low SPI (no consciousness)
    spi_low = spi_proxy(ece=0.001, randomness=0.01, introspection_leak=0.01)
    assert spi_low < 0.1
    assert assert_zero_consciousness(spi_low, tau=0.05)

    # High SPI (consciousness indicators)
    spi_high = spi_proxy(ece=0.1, randomness=0.5, introspection_leak=0.8)
    assert spi_high > 0.1
    assert not assert_zero_consciousness(spi_high, tau=0.05)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
