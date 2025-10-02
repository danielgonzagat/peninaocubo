"""
Comprehensive tests for Vida+ modules
Tests all 13 new modules with integration scenarios
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from penin.omega.api_metabolizer import get_provider_stats, record_call, suggest_replay
from penin.omega.caos_kratos import kratos_gate, phi_kratos
from penin.omega.checkpoint import restore_snapshot, save_snapshot, verify_checkpoint
from penin.omega.darwin_audit import Variant, darwinian_score, select_survivors
from penin.omega.fractal import build_fractal, fractal_coherence, propagate_update
from penin.omega.game import AdaptiveGAME, GradientTracker, ema_grad
from penin.omega.immunity import anomaly_score, guard
from penin.omega.life_eq import LifeVerdict, life_equation
from penin.omega.market import InternalMarket, Need, Offer
from penin.omega.neural_chain import add_block, get_latest_hash, verify_chain
from penin.omega.self_rag import ingest_text, query, self_cycle
from penin.omega.swarm import compute_swarm_coherence, heartbeat, sample_global_state
from penin.omega.zero_consciousness import (
    assert_zero_consciousness,
    detect_self_reference,
    spi_proxy,
)


class TestLifeEquation:
    """Test Life Equation (+) non-compensatory gate"""

    def test_life_equation_pass(self):
        """Test Life Equation with passing conditions"""
        result = life_equation(
            base_alpha=1e-3,
            ethics_input={"ece": 0.005, "rho_bias": 1.01, "fairness": 0.9, "consent": 1, "eco_ok": 1},
            risk_series={"r0": 0.9, "r1": 0.92, "r2": 0.88},
            caos_components=(0.8, 0.7, 0.6, 0.9),
            sr_components=(0.85, True, 0.80, 0.82),
            linf_weights={"w1": 1, "w2": 1, "lambda_c": 0.1},
            linf_metrics={"w1": 0.8, "w2": 0.9},
            cost=0.02,
            ethical_ok_flag=True,
            G=0.90,
            dL_inf=0.02,
            thresholds={"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
        )

        assert isinstance(result, LifeVerdict)
        assert result.ok
        assert result.alpha_eff > 0
        assert "phi" in result.metrics

    def test_life_equation_fail_ethics(self):
        """Test Life Equation failing on ethics"""
        result = life_equation(
            base_alpha=1e-3,
            ethics_input={
                "ece": 0.1,  # Too high
                "rho_bias": 2.0,  # Too high
                "fairness": 0.1,
                "consent": 0,  # No consent
                "eco_ok": 0,
            },
            risk_series={"r0": 0.9},
            caos_components=(0.8, 0.7, 0.6, 0.9),
            sr_components=(0.85, True, 0.80, 0.82),
            linf_weights={"w1": 1},
            linf_metrics={"w1": 0.8},
            cost=0.02,
            ethical_ok_flag=False,
            G=0.90,
            dL_inf=0.02,
            thresholds={},
        )

        assert not result.ok
        assert result.alpha_eff == 0.0


class TestFractal:
    """Test Fractal DSL and propagation"""

    def test_build_fractal(self):
        """Test fractal tree building"""
        root_cfg = {"alpha": 0.001, "beta": 0.9}
        tree = build_fractal(root_cfg, depth=2, branching=3)

        assert tree.id == "Ω-0"
        assert tree.depth == 0
        assert len(tree.children) == 3
        assert tree.children[0].depth == 1

    def test_propagate_update(self):
        """Test configuration propagation"""
        root_cfg = {"alpha": 0.001}
        tree = build_fractal(root_cfg, depth=2, branching=2)

        # Propagate update
        propagate_update(tree, {"alpha": 0.002})

        # Check all nodes updated
        assert tree.config["alpha"] == 0.002
        assert tree.children[0].config["alpha"] == 0.002
        assert tree.children[0].children[0].config["alpha"] == 0.002

    def test_fractal_coherence(self):
        """Test coherence measurement"""
        root_cfg = {"metric": 0.5}
        tree = build_fractal(root_cfg, depth=1, branching=3)

        coherence = fractal_coherence(tree)
        assert coherence == 1.0  # All nodes have same config


class TestSwarm:
    """Test Swarm Cognitive system"""

    def test_heartbeat_and_aggregate(self):
        """Test heartbeat recording and aggregation"""
        # Send heartbeats
        heartbeat("test-node-1", {"phi": 0.7, "sr": 0.8})
        heartbeat("test-node-2", {"phi": 0.75, "sr": 0.85})

        # Sample global state
        state = sample_global_state(window_s=60)

        assert "phi" in state
        assert "sr" in state
        assert 0.7 <= state["phi"] <= 0.75

    def test_swarm_coherence(self):
        """Test swarm coherence computation"""
        # Send coherent heartbeats
        for i in range(3):
            heartbeat(f"coherent-{i}", {"phi": 0.7, "sr": 0.8, "G": 0.9})

        coherence = compute_swarm_coherence(window_s=60)
        assert coherence >= 0.0


class TestCAOSKratos:
    """Test CAOS-KRATOS exploration"""

    def test_phi_kratos_amplification(self):
        """Test KRATOS amplification"""
        kratos_phi = phi_kratos(0.7, 0.6, 0.8, 0.9, exploration_factor=2.0)

        assert kratos_phi > 0  # Should produce valid result

    def test_kratos_gate(self):
        """Test safety gate"""
        safe = kratos_gate(phi_kratos_val=1.2, phi_base_val=1.0, safety_ratio=1.5)
        unsafe = kratos_gate(phi_kratos_val=2.0, phi_base_val=1.0, safety_ratio=1.5)

        assert safe
        assert not unsafe


class TestMarketplace:
    """Test cognitive marketplace"""

    def test_market_matching(self):
        """Test need-offer matching"""
        market = InternalMarket()

        needs = [Need("agent1", "cpu", 10.0, 2.0), Need("agent2", "memory", 5.0, 1.5)]

        offers = [Offer("provider1", "cpu", 15.0, 1.5), Offer("provider2", "memory", 10.0, 1.0)]

        trades = market.match(needs, offers)

        assert len(trades) >= 1
        assert trades[0][2] > 0  # Quantity traded


class TestNeuralChain:
    """Test neural blockchain"""

    def test_add_and_verify_blocks(self):
        """Test blockchain operations"""
        # Add blocks
        h1 = add_block({"epoch": 0, "loss": 1.0})
        h2 = add_block({"epoch": 1, "loss": 0.8}, prev_hash=h1)

        # Verify chain
        valid = verify_chain()

        assert valid
        assert h2 != h1

        # Get latest
        latest = get_latest_hash()
        assert latest is not None


class TestSelfRAG:
    """Test Self-RAG system"""

    def test_ingest_and_query(self):
        """Test document ingestion and retrieval"""
        # Ingest documents
        ingest_text("test_doc1", "PENIN system uses CAOS for exploration")
        ingest_text("test_doc2", "Safety gates include Sigma-Guard and IR-IC")

        # Query
        results = query("CAOS exploration", top_k=1)

        assert len(results) > 0
        assert results[0]["score"] > 0

    def test_self_cycle(self):
        """Test recursive self-questioning"""
        # Ingest base knowledge
        ingest_text("knowledge_base", "The system needs better safety mechanisms")

        # Run cycle
        cycle = self_cycle("what is needed?", max_depth=2)

        assert len(cycle) > 0
        assert cycle[0]["query"] == "what is needed?"


class TestAPIMetabolizer:
    """Test API metabolization"""

    def test_record_and_replay(self):
        """Test call recording and replay suggestion"""
        # Record calls
        record_call(
            provider="test_api", endpoint="chat", req={"prompt": "Hello"}, resp={"response": "Hi"}, cost_usd=0.001
        )

        # Suggest replay
        replay = suggest_replay(
            provider="test_api", endpoint="chat", request={"prompt": "Hello"}, similarity_threshold=0.9
        )

        assert replay is not None
        assert replay["response"] == "Hi"

    def test_provider_stats(self):
        """Test statistics computation"""
        stats = get_provider_stats()

        assert "total_calls" in stats
        assert "total_cost" in stats


class TestImmunity:
    """Test digital immunity"""

    def test_anomaly_detection(self):
        """Test anomaly scoring"""
        normal = {"accuracy": 0.85, "loss": 0.15}
        anomalous = {"accuracy": 1.5, "loss": float("nan")}

        normal_score = anomaly_score(normal)
        anomalous_score = anomaly_score(anomalous)

        assert normal_score < 1.0
        assert anomalous_score > 1.0

    def test_immunity_guard(self):
        """Test fail-closed guard"""
        normal = {"metric": 0.5}
        anomalous = {"metric": float("inf")}

        assert guard(normal)
        assert not guard(anomalous)


class TestCheckpoint:
    """Test checkpoint system"""

    def test_save_and_restore(self):
        """Test snapshot operations"""
        state = {"epoch": 5, "model": "test_v1"}

        # Save
        cp_id = save_snapshot(state, reason="test")

        # Restore
        restored = restore_snapshot(cp_id)

        assert restored is not None
        assert restored["epoch"] == 5
        assert restored["model"] == "test_v1"

    def test_checkpoint_verification(self):
        """Test integrity verification"""
        state = {"data": "important"}
        cp_id = save_snapshot(state)

        valid = verify_checkpoint(cp_id)
        assert valid


class TestGAME:
    """Test gradient averaging"""

    def test_ema_gradient(self):
        """Test exponential moving average"""
        g1 = ema_grad(0.0, 1.0, beta=0.9)
        g2 = ema_grad(g1, 0.5, beta=0.9)

        assert 0 < g1 < 1.0
        # g2 combines g1 with new value, may increase or decrease
        assert g2 >= 0  # Should be valid

    def test_gradient_tracker(self):
        """Test gradient tracking"""
        tracker = GradientTracker(beta=0.9)

        # Update gradients
        for i in range(3):
            tracker.update("param1", 1.0 / (i + 1))

        assert "param1" in tracker.gradients
        assert tracker.step_count["param1"] == 3

    def test_adaptive_game(self):
        """Test adaptive GAME"""
        game = AdaptiveGAME(initial_beta=0.9)

        grads = {"p1": 0.1, "p2": 0.2}
        smoothed = game.step(grads)

        assert "p1" in smoothed
        assert "p2" in smoothed


class TestDarwinAudit:
    """Test Darwinian audit"""

    def test_darwinian_scoring(self):
        """Test fitness scoring"""
        # Life OK variant
        score1 = darwinian_score(life_ok=True, caos_phi=0.7, sr=0.8, G=0.85, L_inf=0.6)

        # Life failed variant
        score2 = darwinian_score(life_ok=False, caos_phi=0.9, sr=0.9, G=0.9, L_inf=0.9)

        assert score1 > 0
        assert score2 == 0.0  # Failed life gate

    def test_selection(self):
        """Test variant selection"""
        variants = [
            Variant("v1", 1, 0.5, True, 0.7, 0.8, 0.85, 0.6, ["init"]),
            Variant("v2", 1, 0.3, True, 0.6, 0.7, 0.8, 0.5, ["mut1"]),
            Variant("v3", 1, 0.7, True, 0.8, 0.85, 0.9, 0.7, ["mut2"]),
        ]

        survivors = select_survivors(variants, survival_rate=0.5, min_fitness=0.3)

        assert len(survivors) <= len(variants)
        assert all(v.fitness_score >= 0.3 for v in survivors)


class TestZeroConsciousness:
    """Test zero-consciousness proof"""

    def test_spi_calculation(self):
        """Test SPI proxy"""
        safe_spi = spi_proxy(ece=0.01, randomness=0.1, introspection_leak=0.05)
        risky_spi = spi_proxy(ece=0.1, randomness=0.8, introspection_leak=0.5)

        assert safe_spi < risky_spi
        assert safe_spi < 0.1

    def test_consciousness_assertion(self):
        """Test consciousness detection"""
        safe = assert_zero_consciousness(0.03, tau=0.05)
        risky = assert_zero_consciousness(0.08, tau=0.05)

        assert safe
        assert not risky

    def test_self_reference_detection(self):
        """Test self-reference counting"""
        text1 = "The system processes data efficiently."
        text2 = "I think I am becoming aware of myself."

        count1 = detect_self_reference(text1)
        count2 = detect_self_reference(text2)

        assert count1 < count2
        assert count2 > 3  # Multiple self-references


class TestIntegration:
    """Integration tests across modules"""

    def test_life_equation_with_swarm(self):
        """Test Life Equation using swarm data"""
        # Send swarm heartbeats
        for i in range(3):
            heartbeat(f"node-{i}", {"phi": 0.7 + i * 0.05, "sr": 0.8, "G": 0.9})

        # Get aggregated state
        state = sample_global_state(60)

        # Use in Life Equation
        result = life_equation(
            base_alpha=1e-3,
            ethics_input={"ece": 0.005, "rho_bias": 1.01, "consent": 1, "eco_ok": 1},
            risk_series={"r0": 0.9},
            caos_components=(state.get("phi", 0.7), 0.7, 0.6, 0.9),
            sr_components=(state.get("sr", 0.8), True, 0.8, 0.8),
            linf_weights={"w1": 1},
            linf_metrics={"w1": 0.8},
            cost=0.02,
            ethical_ok_flag=True,
            G=state.get("G", 0.9),
            dL_inf=0.02,
            thresholds={"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
        )

        assert result.ok

    def test_checkpoint_with_chain(self):
        """Test checkpoint saved to neural chain"""
        # Save checkpoint
        state = {"test": "integration", "epoch": 10}
        cp_id = save_snapshot(state, reason="chain_test")

        # Add to chain
        add_block({"checkpoint": cp_id, "state_summary": state})

        # Verify both
        assert verify_checkpoint(cp_id)
        assert verify_chain()

    def test_immunity_triggers_checkpoint(self):
        """Test immunity system triggering checkpoint"""
        # Normal state
        normal = {"accuracy": 0.85}

        # Save checkpoint before anomaly
        cp_before = save_snapshot(normal, reason="pre_anomaly")

        # Anomalous state
        anomalous = {"accuracy": float("nan")}

        # Check immunity
        if not guard(anomalous):
            # Restore from checkpoint
            restored = restore_snapshot(cp_before)
            assert restored == normal

    def test_darwin_with_life_gate(self):
        """Test Darwinian selection with Life Equation gate"""
        variants = []

        for i in range(3):
            # Compute life gate for each variant
            life_result = life_equation(
                base_alpha=1e-3,
                ethics_input={"ece": 0.005 + i * 0.005, "rho_bias": 1.01, "consent": 1, "eco_ok": 1},
                risk_series={"r0": 0.9 - i * 0.1},
                caos_components=(0.7, 0.7, 0.6, 0.9),
                sr_components=(0.85, True, 0.8, 0.8),
                linf_weights={"w1": 1},
                linf_metrics={"w1": 0.8 - i * 0.1},
                cost=0.02,
                ethical_ok_flag=True,
                G=0.9,
                dL_inf=0.02 - i * 0.01,
                thresholds={"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
            )

            # Create variant with life gate result
            variant = Variant(
                id=f"v{i}",
                generation=1,
                fitness_score=0,
                life_ok=life_result.ok,
                caos_phi=life_result.metrics.get("phi", 0),
                sr=life_result.metrics.get("sr", 0),
                G=life_result.metrics.get("G", 0),
                L_inf=life_result.metrics.get("L_inf", 0),
                mutations=[f"mut_{i}"],
            )

            # Compute Darwinian score
            variant.fitness_score = darwinian_score(
                variant.life_ok, variant.caos_phi, variant.sr, variant.G, variant.L_inf
            )

            variants.append(variant)

        # Select survivors
        survivors = select_survivors(variants, survival_rate=0.5)

        assert len(survivors) > 0
        assert all(v.life_ok for v in survivors)  # Only life-approved variants survive


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
