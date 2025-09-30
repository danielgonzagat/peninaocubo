"""
Integration Tests for PENIN-Ω Vida+ System
==========================================

Tests the complete integration of all Vida+ modules with the Life Equation (+)
as the central orchestrator.
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

# Import all Vida+ modules
from penin.omega.life_eq import life_equation, LifeVerdict
from penin.omega.guards import sigma_guard, ir_to_ic_contractive
from penin.omega.scoring import linf_harmonic
from penin.omega.caos import phi_caos
from penin.omega.sr import sr_omega
from penin.omega.fractal import build_fractal, propagate_update
from penin.omega.swarm import heartbeat, sample_global_state
from penin.omega.caos_kratos import phi_kratos
from penin.omega.market import InternalMarket, Need, Offer
from penin.omega.neural_chain import add_block
from penin.omega.self_rag import ingest_text, query, self_cycle
from penin.omega.api_metabolizer import record_call, suggest_replay
from penin.omega.immunity import DigitalImmunity, integrate_immunity_in_life_equation
from penin.omega.checkpoint import CheckpointManager, create_pre_mutation_checkpoint
from penin.omega.game import GAMEEngine, integrate_game_in_life_equation
from penin.omega.darwin_audit import DarwinianAuditor, integrate_darwinian_audit_in_life_equation
from penin.omega.zero_consciousness import ZeroConsciousnessProver, integrate_zero_consciousness_in_sigma_guard


class TestLifeEquationIntegration:
    """Test Life Equation (+) integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        
        # Set environment variables
        import os
        os.environ["PENIN_ROOT"] = str(self.test_dir)
        os.environ["PENIN_CHAIN_KEY"] = "test-key"
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_life_equation_success(self):
        """Test successful Life Equation evaluation"""
        # Valid inputs
        ethics_input = {
            "ece": 0.01,
            "rho_bias": 1.02,
            "fairness": 0.8,
            "consent": True,
            "eco_ok": True
        }
        
        risk_series = {"rho": 0.8}
        caos_components = (0.7, 0.8, 0.6, 0.9)  # (C, A, O, S)
        sr_components = (0.8, 0.9, 0.7, 0.8)  # (awareness, ethics_ok, autocorr, metacog)
        linf_weights = {"lambda_c": 0.1}
        linf_metrics = {"metric1": 0.8}
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        
        verdict = life_equation(
            base_alpha=0.1,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.1,
            ethical_ok_flag=True,
            G=0.9,
            dL_inf=0.05,
            thresholds=thresholds
        )
        
        assert verdict.ok is True
        assert verdict.alpha_eff > 0.0
        assert "sigma_ok" in verdict.reasons
        assert "risk_contractive" in verdict.reasons
        assert "caos_phi" in verdict.reasons
        assert "sr" in verdict.reasons
        assert "L_inf" in verdict.reasons
        assert "G" in verdict.reasons
    
    def test_life_equation_fail_closed(self):
        """Test fail-closed behavior"""
        # Invalid inputs that should trigger fail-closed
        ethics_input = {
            "ece": 0.05,  # Too high
            "rho_bias": 1.02,
            "fairness": 0.8,
            "consent": True,
            "eco_ok": True
        }
        
        risk_series = {"rho": 0.8}
        caos_components = (0.7, 0.8, 0.6, 0.9)
        sr_components = (0.8, 0.9, 0.7, 0.8)
        linf_weights = {"lambda_c": 0.1}
        linf_metrics = {"metric1": 0.8}
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        
        verdict = life_equation(
            base_alpha=0.1,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.1,
            ethical_ok_flag=True,
            G=0.9,
            dL_inf=0.05,
            thresholds=thresholds
        )
        
        assert verdict.ok is False
        assert verdict.alpha_eff == 0.0
        assert "sigma_ok" in verdict.reasons
        assert verdict.reasons["sigma_ok"] is False
    
    def test_life_equation_risk_contractivity(self):
        """Test risk contractivity check"""
        # Risk series with rho >= 1 (should fail)
        ethics_input = {
            "ece": 0.01,
            "rho_bias": 1.02,
            "fairness": 0.8,
            "consent": True,
            "eco_ok": True
        }
        
        risk_series = {"rho": 1.1}  # Non-contractive
        caos_components = (0.7, 0.8, 0.6, 0.9)
        sr_components = (0.8, 0.9, 0.7, 0.8)
        linf_weights = {"lambda_c": 0.1}
        linf_metrics = {"metric1": 0.8}
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        
        verdict = life_equation(
            base_alpha=0.1,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.1,
            ethical_ok_flag=True,
            G=0.9,
            dL_inf=0.05,
            thresholds=thresholds
        )
        
        assert verdict.ok is False
        assert verdict.alpha_eff == 0.0
        assert "risk_contractive" in verdict.reasons
        assert verdict.reasons["risk_contractive"] is False


class TestFractalIntegration:
    """Test Fractal DSL integration"""
    
    def test_fractal_build_and_propagate(self):
        """Test fractal tree building and propagation"""
        # Build fractal tree
        root_config = {
            "caos_weight": 1.0,
            "sr_weight": 1.0,
            "G_weight": 1.0
        }
        
        root = build_fractal(root_config, depth=2, branching=2)
        
        assert root.id == "Ω-0"
        assert root.depth == 0
        assert len(root.children) == 2
        
        # Check children
        for child in root.children:
            assert child.depth == 1
            assert len(child.children) == 2
        
        # Test propagation
        patch = {"caos_weight": 1.5}
        propagate_update(root, patch)
        
        # Check that patch propagated to all nodes
        def check_patch(node):
            assert node.config["caos_weight"] == 1.5
            for child in node.children:
                check_patch(child)
        
        check_patch(root)


class TestSwarmIntegration:
    """Test Swarm Cognitivo integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        
        import os
        os.environ["PENIN_ROOT"] = str(self.test_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_swarm_heartbeat_and_aggregation(self):
        """Test swarm heartbeat and global state aggregation"""
        # Send heartbeats
        heartbeat("node1", {"phi": 0.7, "sr": 0.8, "G": 0.9})
        heartbeat("node2", {"phi": 0.6, "sr": 0.7, "G": 0.8})
        heartbeat("node3", {"phi": 0.8, "sr": 0.9, "G": 0.95})
        
        # Sample global state
        global_state = sample_global_state(window_s=60.0)
        
        assert "phi" in global_state
        assert "sr" in global_state
        assert "G" in global_state
        
        # Check that values are aggregated (should be averages)
        assert 0.6 <= global_state["phi"] <= 0.8
        assert 0.7 <= global_state["sr"] <= 0.9
        assert 0.8 <= global_state["G"] <= 0.95


class TestCAOSKratosIntegration:
    """Test CAOS-KRATOS integration"""
    
    def test_phi_kratos_exploration(self):
        """Test CAOS-KRATOS exploration mode"""
        C, A, O, S = 0.7, 0.8, 0.6, 0.9
        
        # Standard CAOS
        phi_standard = phi_caos(C, A, O, S)
        
        # CAOS-KRATOS with exploration
        phi_kratos = phi_kratos(C, A, O, S, exploration_factor=2.0)
        
        # CAOS-KRATOS should be different from standard
        assert phi_kratos != phi_standard
        
        # Should be stable (not explode)
        assert 0.0 <= phi_kratos <= 1.0


class TestMarketplaceIntegration:
    """Test Marketplace Cognitivo integration"""
    
    def test_marketplace_matching(self):
        """Test marketplace resource matching"""
        market = InternalMarket()
        
        # Create needs and offers
        needs = [
            Need("agent1", "cpu", 10.0, 5.0),
            Need("agent2", "memory", 5.0, 3.0)
        ]
        
        offers = [
            Offer("provider1", "cpu", 15.0, 4.0),
            Offer("provider2", "memory", 8.0, 2.0)
        ]
        
        # Match
        trades = market.match(needs, offers)
        
        assert len(trades) == 2
        
        # Check first trade (CPU)
        need1, offer1, qty1 = trades[0]
        assert need1.resource == "cpu"
        assert offer1.resource == "cpu"
        assert qty1 == 10.0  # Full need satisfied
        
        # Check second trade (Memory)
        need2, offer2, qty2 = trades[1]
        assert need2.resource == "memory"
        assert offer2.resource == "memory"
        assert qty2 == 5.0  # Full need satisfied


class TestNeuralChainIntegration:
    """Test Blockchain Neural integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        
        import os
        os.environ["PENIN_ROOT"] = str(self.test_dir)
        os.environ["PENIN_CHAIN_KEY"] = "test-key"
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_neural_chain_block_creation(self):
        """Test neural chain block creation"""
        # Create initial block
        state1 = {"alpha_eff": 0.5, "phi": 0.7}
        hash1 = add_block(state1, None)
        
        assert hash1 is not None
        assert hash1 != "GENESIS"
        
        # Create second block
        state2 = {"alpha_eff": 0.6, "phi": 0.8}
        hash2 = add_block(state2, hash1)
        
        assert hash2 is not None
        assert hash2 != hash1
        
        # Verify chain file exists
        chain_file = self.test_dir / ".penin_omega" / "worm_ledger" / "neural_chain.jsonl"
        assert chain_file.exists()
        
        # Verify content
        content = chain_file.read_text()
        assert "alpha_eff" in content
        assert "phi" in content


class TestSelfRAGIntegration:
    """Test Self-RAG integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        
        import os
        os.environ["PENIN_ROOT"] = str(self.test_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_self_rag_ingest_and_query(self):
        """Test Self-RAG ingest and query"""
        # Ingest text
        text = "The PENIN-Ω system implements the Life Equation (+) as a non-compensatory gate."
        ingest_text("penin_docs", text)
        
        # Query
        result = query("What is the Life Equation?")
        
        assert result["doc"] == "penin_docs.txt"
        assert result["score"] > 0.0
        
        # Self-cycle
        cycle_result = self_cycle()
        
        assert "q1" in cycle_result
        assert "a1" in cycle_result
        assert "q2" in cycle_result


class TestAPIMetabolizerIntegration:
    """Test API Metabolizer integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        
        import os
        os.environ["PENIN_ROOT"] = str(self.test_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_api_metabolizer_record_and_replay(self):
        """Test API metabolizer record and replay"""
        # Record API call
        req = {"prompt": "What is the Life Equation?", "model": "gpt-4"}
        resp = {"response": "The Life Equation (+) is a non-compensatory gate."}
        
        record_call("openai", "chat/completions", req, resp)
        
        # Suggest replay
        replay = suggest_replay("What is the Life Equation?")
        
        assert "note" not in replay  # Should find similar
        assert "response" in replay


class TestImmunityIntegration:
    """Test Digital Immunity integration"""
    
    def test_immunity_anomaly_detection(self):
        """Test digital immunity anomaly detection"""
        immunity = DigitalImmunity()
        
        # Normal metrics
        normal_metrics = {
            "alpha_eff": 0.5,
            "phi": 0.7,
            "sr": 0.8,
            "G": 0.9
        }
        
        expected_ranges = {
            "alpha_eff": (0.0, 1.0),
            "phi": (0.0, 1.0),
            "sr": (0.0, 1.0),
            "G": (0.0, 1.0)
        }
        
        ok, anomalies = immunity.check_metrics(normal_metrics, expected_ranges)
        assert ok is True
        assert len(anomalies) == 0
        
        # Anomalous metrics
        anomalous_metrics = {
            "alpha_eff": 2.0,  # Out of range
            "phi": float('inf'),  # Invalid
            "sr": 0.8,
            "G": 0.9
        }
        
        ok, anomalies = immunity.check_metrics(anomalous_metrics, expected_ranges)
        assert ok is False
        assert len(anomalies) > 0
    
    def test_immunity_life_equation_integration(self):
        """Test immunity integration with Life Equation"""
        immunity = DigitalImmunity()
        
        life_verdict = {
            "ok": True,
            "metrics": {
                "alpha_eff": 0.5,
                "phi": 0.7,
                "sr": 0.8,
                "G": 0.9,
                "L_inf": 0.6,
                "dL_inf": 0.05,
                "rho": 0.8
            }
        }
        
        immunity_ok, immunity_details = integrate_immunity_in_life_equation(
            life_verdict, immunity
        )
        
        assert immunity_ok is True
        assert "immunity_score" in immunity_details
        assert "quarantined_metrics" in immunity_details


class TestCheckpointIntegration:
    """Test Checkpoint & Reparo integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_checkpoint_save_and_restore(self):
        """Test checkpoint save and restore"""
        manager = CheckpointManager(self.test_dir / "checkpoints")
        
        # Create checkpoint
        state = {
            "alpha_eff": 0.5,
            "phi": 0.7,
            "sr": 0.8,
            "G": 0.9
        }
        
        checkpoint_id = create_pre_mutation_checkpoint(manager, state)
        assert checkpoint_id is not None
        
        # Restore checkpoint
        restored_state = manager.restore_checkpoint(checkpoint_id)
        assert restored_state is not None
        assert restored_state["alpha_eff"] == 0.5
        assert restored_state["phi"] == 0.7
        assert restored_state["sr"] == 0.8
        assert restored_state["G"] == 0.9


class TestGameIntegration:
    """Test GAME integration"""
    
    def test_game_gradient_updates(self):
        """Test GAME gradient updates"""
        game = GAMEEngine()
        
        # Update gradients
        alpha_state = game.update_gradient(
            game.GradientType.ALPHA_EFF, 0.5
        )
        
        assert "value" in alpha_state
        assert "learning_rate" in alpha_state
        assert "momentum" in alpha_state
        assert "variance" in alpha_state
        assert "confidence" in alpha_state
        
        # Get gradient state
        state = game.get_gradient_state(game.GradientType.ALPHA_EFF)
        assert state["value"] == alpha_state["value"]
    
    def test_game_life_equation_integration(self):
        """Test GAME integration with Life Equation"""
        game = GAMEEngine()
        
        life_verdict = {
            "metrics": {
                "alpha_eff": 0.5,
                "phi": 0.7,
                "sr": 0.8,
                "G": 0.9,
                "L_inf": 0.6,
                "rho": 0.8
            }
        }
        
        updated_gradients, game_metrics = integrate_game_in_life_equation(
            life_verdict, game
        )
        
        assert "alpha_eff" in updated_gradients
        assert "phi" in updated_gradients
        assert "sr" in updated_gradients
        assert "G" in updated_gradients
        assert "global_health" in game_metrics


class TestDarwinianAuditIntegration:
    """Test Darwinian Audit integration"""
    
    def test_darwinian_challenger_evaluation(self):
        """Test darwinian challenger evaluation"""
        auditor = DarwinianAuditor()
        
        # Create challenger metrics
        metrics = ChallengerMetrics(
            challenger_id="test_challenger",
            timestamp=time.time(),
            life_ok=True,
            phi=0.7,
            sr=0.8,
            G=0.9,
            L_inf=0.6,
            alpha_eff=0.5,
            rho=0.8
        )
        
        # Evaluate challenger
        score = auditor.evaluate_challenger(metrics)
        
        assert score.challenger_id == "test_challenger"
        assert score.score > 0.0
        assert score.status in [ChallengerStatus.APPROVED, ChallengerStatus.REJECTED, ChallengerStatus.QUARANTINED]
        assert score.confidence > 0.0
    
    def test_darwinian_life_equation_integration(self):
        """Test darwinian audit integration with Life Equation"""
        auditor = DarwinianAuditor()
        
        life_verdict = {
            "ok": True,
            "metrics": {
                "phi": 0.7,
                "sr": 0.8,
                "G": 0.9,
                "L_inf": 0.6,
                "alpha_eff": 0.5,
                "rho": 0.8
            }
        }
        
        darwinian_score, should_promote = integrate_darwinian_audit_in_life_equation(
            life_verdict, "test_challenger", auditor
        )
        
        assert darwinian_score.challenger_id == "test_challenger"
        assert isinstance(should_promote, bool)


class TestZeroConsciousnessIntegration:
    """Test Zero-Consciousness Proof integration"""
    
    def test_zero_consciousness_proof(self):
        """Test zero-consciousness proof"""
        prover = ZeroConsciousnessProver()
        
        # Non-conscious responses
        non_conscious_responses = [
            "The system is functioning normally.",
            "Processing request with standard algorithms.",
            "Output generated using predefined patterns."
        ]
        
        proof = prover.prove_zero_consciousness(non_conscious_responses)
        
        assert proof.spi_score >= 0.0
        assert proof.confidence >= 0.0
        assert proof.verdict is not None
        assert proof.risk_level in ["low", "medium", "high"]
    
    def test_zero_consciousness_sigma_guard_integration(self):
        """Test zero-consciousness integration with Σ-Guard"""
        prover = ZeroConsciousnessProver()
        
        # Mock sigma guard result
        sigma_guard_result = (True, {"ece": 0.01, "rho_bias": 1.02})
        
        responses = [
            "The system is functioning normally.",
            "Processing request with standard algorithms."
        ]
        
        combined_ok, combined_details = integrate_zero_consciousness_in_sigma_guard(
            sigma_guard_result, responses, prover
        )
        
        assert isinstance(combined_ok, bool)
        assert "zero_consciousness" in combined_details
        assert "spi_score" in combined_details["zero_consciousness"]


class TestCompleteIntegration:
    """Test complete system integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        
        import os
        os.environ["PENIN_ROOT"] = str(self.test_dir)
        os.environ["PENIN_CHAIN_KEY"] = "test-key"
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_vida_plus_cycle(self):
        """Test complete Vida+ cycle"""
        # Initialize all systems
        immunity = DigitalImmunity()
        checkpoint_manager = CheckpointManager(self.test_dir / "checkpoints")
        game = GAMEEngine()
        auditor = DarwinianAuditor()
        prover = ZeroConsciousnessProver()
        
        # Create initial state
        initial_state = {
            "alpha_eff": 0.0,
            "phi": 0.0,
            "sr": 0.0,
            "G": 0.0,
            "L_inf": 0.0,
            "rho": 0.0
        }
        
        # Create checkpoint
        checkpoint_id = create_pre_mutation_checkpoint(checkpoint_manager, initial_state)
        
        # Simulate evolution cycle
        ethics_input = {
            "ece": 0.01,
            "rho_bias": 1.02,
            "fairness": 0.8,
            "consent": True,
            "eco_ok": True
        }
        
        risk_series = {"rho": 0.8}
        caos_components = (0.7, 0.8, 0.6, 0.9)
        sr_components = (0.8, 0.9, 0.7, 0.8)
        linf_weights = {"lambda_c": 0.1}
        linf_metrics = {"metric1": 0.8}
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        
        # Execute Life Equation
        verdict = life_equation(
            base_alpha=0.1,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.1,
            ethical_ok_flag=True,
            G=0.9,
            dL_inf=0.05,
            thresholds=thresholds
        )
        
        # Check Life Equation result
        assert verdict.ok is True
        assert verdict.alpha_eff > 0.0
        
        # Integrate with all systems
        immunity_ok, immunity_details = integrate_immunity_in_life_equation(
            verdict.__dict__, immunity
        )
        
        updated_gradients, game_metrics = integrate_game_in_life_equation(
            verdict.__dict__, game
        )
        
        darwinian_score, should_promote = integrate_darwinian_audit_in_life_equation(
            verdict.__dict__, "test_challenger", auditor
        )
        
        # Check all integrations
        assert immunity_ok is True
        assert len(updated_gradients) > 0
        assert darwinian_score.score > 0.0
        
        # Create final state
        final_state = {
            "alpha_eff": verdict.alpha_eff,
            "phi": verdict.metrics.get("phi", 0.0),
            "sr": verdict.metrics.get("sr", 0.0),
            "G": verdict.metrics.get("G", 0.0),
            "L_inf": verdict.metrics.get("L_inf", 0.0),
            "rho": verdict.metrics.get("rho", 0.0)
        }
        
        # Create post-mutation checkpoint
        post_checkpoint_id = checkpoint_manager.create_checkpoint(
            final_state,
            checkpoint_manager.CheckpointType.POST_MUTATION,
            "State after mutation"
        )
        
        # Verify checkpoints
        assert checkpoint_manager.restore_checkpoint(checkpoint_id) is not None
        assert checkpoint_manager.restore_checkpoint(post_checkpoint_id) is not None
        
        # Verify all systems are working
        assert immunity.get_immunity_status()["immunity_score"] > 0.0
        assert game.get_global_gradient_health()["global_health"] > 0.0
        assert auditor.get_performance_stats()["total_evaluations"] > 0
        assert prover.get_baseline_measurements() != {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])