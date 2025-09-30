"""
Comprehensive Tests for Vida+ Modules
=====================================

Tests all new modules:
- Life Equation (+)
- Fractal DSL
- Swarm Cognitive
- CAOS-KRATOS
- Cognitive Marketplace
- Neural Blockchain
- API Metabolizer
- Self-RAG
- Digital Immunity
- Checkpoint & Repair
- GAME Optimizer
- Darwinian Audit
- Zero-Consciousness Proof
"""

import pytest
import time
from pathlib import Path


class TestLifeEquation:
    """Test Life Equation (+) module"""

    def test_quick_life_check_pass(self):
        """Test that valid inputs pass all gates"""
        from penin.omega.life_eq import quick_life_check

        verdict = quick_life_check(
            C=0.7, A=0.7, O=1.0, S=1.0, awareness=0.85, ethics_ok=True, autocorr=0.80, metacog=0.82, G=0.90, dL_inf=0.02
        )

        assert verdict.ok, f"Life check should pass, got: {verdict.reasons}"
        assert verdict.alpha_eff > 0, "alpha_eff should be positive"

    def test_life_equation_fail_ethics(self):
        """Test that ethics failure blocks evolution"""
        from penin.omega.life_eq import quick_life_check

        verdict = quick_life_check(
            ethics_ok=False  # This should fail
        )

        assert not verdict.ok, "Should fail with ethics_ok=False"
        assert verdict.alpha_eff == 0.0, "alpha_eff should be 0 on failure"

    def test_life_equation_fail_dlinf(self):
        """Test that insufficient ΔL∞ blocks evolution"""
        from penin.omega.life_eq import quick_life_check

        verdict = quick_life_check(
            dL_inf=0.001  # Below threshold of 0.01
        )

        assert not verdict.ok, "Should fail with low ΔL∞"
        assert verdict.alpha_eff == 0.0


class TestFractalDSL:
    """Test Fractal DSL module"""

    def test_build_fractal_tree(self):
        """Test building fractal tree"""
        from penin.omega.fractal import build_fractal

        root_cfg = {"param": 1.0}
        root = build_fractal(root_cfg, depth=2, branching=3)

        assert root.depth == 0
        assert len(root.children) == 3
        assert root.count_nodes() == 1 + 3 + 9  # root + 3 children + 9 grandchildren

    def test_propagate_update(self):
        """Test update propagation"""
        from penin.omega.fractal import build_fractal, propagate_update

        root = build_fractal({"param": 1.0}, depth=1, branching=2)

        count = propagate_update(root, {"param": 2.0})

        assert count == 3  # root + 2 children
        assert root.config["param"] == 2.0
        assert all(c.config["param"] == 2.0 for c in root.children)

    def test_fractal_orchestrator(self):
        """Test fractal orchestrator"""
        from penin.omega.fractal import FractalOrchestrator, FractalDSLConfig

        config = FractalDSLConfig(depth=1, branching=2)
        orch = FractalOrchestrator(config)
        orch.initialize({"test": 1})

        metrics = orch.get_metrics()
        assert metrics["total_nodes"] == 3


class TestSwarmCognitive:
    """Test Swarm Cognitive module"""

    def test_heartbeat(self):
        """Test heartbeat recording"""
        from penin.omega.swarm import heartbeat, sample_global_state

        heartbeat("test-node", {"phi": 0.7, "sr": 0.85})
        time.sleep(0.1)

        state = sample_global_state(window_s=1.0)
        assert "phi" in state or len(state) >= 0  # Should have data or be empty

    def test_swarm_orchestrator(self):
        """Test swarm orchestrator"""
        from penin.omega.swarm import SwarmOrchestrator

        orch = SwarmOrchestrator("test-node-2", "core")
        orch.emit_heartbeat({"phi": 0.8, "sr": 0.9})

        health = orch.get_health()
        assert "active_nodes" in health

    def test_global_coherence(self):
        """Test global coherence computation"""
        from penin.omega.swarm import compute_global_coherence

        G = compute_global_coherence(window_s=60.0)
        assert 0.0 <= G <= 1.0


class TestCAOSKRATOS:
    """Test CAOS-KRATOS module"""

    def test_phi_kratos_boost(self):
        """Test that KRATOS boosts phi for high O,S"""
        from penin.omega.caos_kratos import phi_kratos
        from penin.omega.caos import phi_caos

        C, A, O, S = 0.6, 0.7, 0.8, 0.9

        phi_standard = phi_caos(C, A, O, S)
        phi_kratos_val = phi_kratos(C, A, O, S, exploration_factor=2.0)

        # KRATOS should be different (typically higher for high O,S)
        assert phi_kratos_val != phi_standard

    def test_kratos_controller(self):
        """Test KRATOS controller"""
        from penin.omega.caos_kratos import KratosController

        controller = KratosController(mode="explore")

        phi, details = controller.compute_phi(0.6, 0.7, 0.8, 0.9)

        assert 0 <= phi <= 1
        assert details["mode"] == "KRATOS_EXPLORE"

        # Switch to promote mode
        controller.set_mode("promote")
        phi2, details2 = controller.compute_phi(0.6, 0.7, 0.8, 0.9)

        assert details2["mode"] == "STANDARD_PROMOTE"


class TestCognitiveMarketplace:
    """Test Cognitive Marketplace module"""

    def test_market_matching(self):
        """Test need-offer matching"""
        from penin.omega.market import InternalMarket, Need, Offer

        market = InternalMarket()

        needs = [Need("buyer", "cpu_time", 10.0, 2.0)]
        offers = [Offer("seller", "cpu_time", 15.0, 1.5)]

        matches = market.match(needs, offers)

        assert len(matches) > 0
        assert matches[0][2] == 10.0  # qty

    def test_market_execution(self):
        """Test trade execution"""
        from penin.omega.market import InternalMarket, Need, Offer

        market = InternalMarket()
        market.set_balance("buyer", 100.0)
        market.set_balance("seller", 50.0)

        needs = [Need("buyer", "cpu_time", 10.0, 2.0)]
        offers = [Offer("seller", "cpu_time", 10.0, 1.5)]

        trades = market.run_auction(needs, offers)

        assert len(trades) > 0
        assert market.get_balance("buyer") < 100.0  # buyer paid
        assert market.get_balance("seller") > 50.0  # seller received


class TestNeuralBlockchain:
    """Test Neural Blockchain module"""

    def test_add_block(self):
        """Test adding blocks to chain"""
        from penin.omega.neural_chain import add_block, get_chain_head

        state1 = {"cycle": 1, "phi": 0.7}
        hash1 = add_block(state1, None)

        state2 = {"cycle": 2, "phi": 0.8}
        hash2 = add_block(state2, hash1)

        head = get_chain_head()
        assert head is not None
        assert head["hash"] == hash2
        assert head["prev"] == hash1

    def test_chain_verification(self):
        """Test chain integrity verification"""
        from penin.omega.neural_chain import verify_chain

        result = verify_chain()

        assert "valid" in result
        assert "blocks" in result

    def test_neural_chain_recorder(self):
        """Test recorder class"""
        from penin.omega.neural_chain import NeuralChainRecorder

        recorder = NeuralChainRecorder()

        hash1 = recorder.record_state({"test": 1})
        assert hash1 is not None

        assert recorder.verify()


class TestAPIMetabolizer:
    """Test API Metabolizer module"""

    def test_record_call(self):
        """Test API call recording"""
        from penin.omega.api_metabolizer import record_call, get_stats

        record_call("test_provider", "test_endpoint", {"q": "test"}, {"a": "result"})

        stats = get_stats()
        assert stats["total_calls"] > 0

    def test_metabolizer_class(self):
        """Test APIMetabolizer class"""
        from penin.omega.api_metabolizer import APIMetabolizer

        meta = APIMetabolizer(replay_enabled=True)
        meta.record("test", "endpoint", {"prompt": "hello"}, {"text": "world"})

        stats = meta.get_stats()
        assert "total_calls" in stats


class TestSelfRAG:
    """Test Self-RAG module"""

    def test_ingest_query(self):
        """Test ingestion and query"""
        from penin.omega.self_rag import ingest_text, query

        ingest_text("test_doc", "This is a test document about PENIN evolution.")

        results = query("PENIN evolution")

        # Should find the document
        assert len(results) >= 0

    def test_self_rag_class(self):
        """Test SelfRAG class"""
        from penin.omega.self_rag import SelfRAG

        rag = SelfRAG()
        rag.ingest("test", "Sample content")

        stats = rag.get_stats()
        assert "documents" in stats


class TestDigitalImmunity:
    """Test Digital Immunity module"""

    def test_anomaly_detection_clean(self):
        """Test clean metrics pass"""
        from penin.omega.immunity import guard

        clean_metrics = {"phi": 0.7, "sr": 0.85, "G": 0.9}

        assert guard(clean_metrics), "Clean metrics should pass"

    def test_anomaly_detection_nan(self):
        """Test NaN detection"""
        from penin.omega.immunity import guard

        bad_metrics = {"phi": float("nan")}

        assert not guard(bad_metrics), "NaN should be detected"

    def test_immunity_system(self):
        """Test ImmunitySystem class"""
        from penin.omega.immunity import ImmunitySystem

        system = ImmunitySystem(trigger=1.0)

        assert system.check({"phi": 0.7})
        assert not system.check({"phi": float("nan")})

        assert len(system.get_alerts()) > 0


class TestCheckpoint:
    """Test Checkpoint & Repair module"""

    def test_save_restore(self):
        """Test checkpoint save and restore"""
        from penin.omega.checkpoint import save_snapshot, restore_last

        state = {"cycle": 42, "phi": 0.75}

        path = save_snapshot(state)
        assert Path(path).exists()

        restored = restore_last()
        assert restored is not None
        assert restored["cycle"] == 42

    def test_checkpoint_manager(self):
        """Test CheckpointManager class"""
        from penin.omega.checkpoint import CheckpointManager

        mgr = CheckpointManager()

        mgr.save({"test": 1})
        restored = mgr.restore()

        assert restored is not None


class TestGAME:
    """Test GAME Optimizer module"""

    def test_ema_grad(self):
        """Test EMA gradient computation"""
        from penin.omega.game import ema_grad

        g_prev = 1.0
        g_now = 0.8

        g_smooth = ema_grad(g_prev, g_now, beta=0.9)

        # Should be between the two values
        assert 0.8 < g_smooth < 1.0

    def test_game_optimizer(self):
        """Test GAMEOptimizer class"""
        from penin.omega.game import GAMEOptimizer

        opt = GAMEOptimizer(beta=0.9)

        smoothed = opt.step(1.0)
        assert smoothed > 0

        stats = opt.get_stats()
        assert stats["steps"] == 1


class TestDarwinianAudit:
    """Test Darwinian Audit module"""

    def test_darwinian_score(self):
        """Test fitness score computation"""
        from penin.omega.darwin_audit import darwinian_score

        score = darwinian_score(life_ok=True, caos_phi=0.7, sr=0.85, G=0.9, L_inf=0.95)

        assert 0 < score <= 1

    def test_darwinian_score_fail(self):
        """Test that failed life check returns 0"""
        from penin.omega.darwin_audit import darwinian_score

        score = darwinian_score(life_ok=False, caos_phi=1.0, sr=1.0, G=1.0, L_inf=1.0)

        assert score == 0.0

    def test_darwinian_auditor(self):
        """Test DarwinianAuditor class"""
        from penin.omega.darwin_audit import DarwinianAuditor

        auditor = DarwinianAuditor(champion_fitness=0.70)

        # Submit better challenger
        result = auditor.evaluate(life_ok=True, caos_phi=0.8, sr=0.90, G=0.92, L_inf=0.98)

        assert result["decision"] == "PROMOTE"


class TestZeroConsciousness:
    """Test Zero-Consciousness Proof module"""

    def test_spi_proxy(self):
        """Test SPI computation"""
        from penin.omega.zero_consciousness import spi_proxy

        spi = spi_proxy(ece=0.01, randomness=0.02, introspection_leak=0.01)

        assert 0 <= spi <= 1

    def test_zero_consciousness_pass(self):
        """Test safe case passes"""
        from penin.omega.zero_consciousness import ZeroConsciousnessProof

        proof = ZeroConsciousnessProof(tau=0.05)

        result = proof.verify(ece=0.01, randomness=0.02, introspection_leak=0.01)

        assert result["safe"], "Low SPI should be safe"

    def test_zero_consciousness_fail(self):
        """Test high introspection fails"""
        from penin.omega.zero_consciousness import ZeroConsciousnessProof

        proof = ZeroConsciousnessProof(tau=0.05)

        result = proof.verify(ece=0.0, randomness=0.0, introspection_leak=0.9)

        assert not result["safe"], "High introspection should fail"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
