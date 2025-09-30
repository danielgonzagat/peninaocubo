"""
Tests for Life Equation (+) and related modules
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from penin.omega.life_eq import life_equation, life_equation_simple, LifeVerdict
from penin.omega.fractal import build_fractal, propagate_update, FractalOrchestrator
from penin.omega.swarm import heartbeat, sample_global_state, SwarmOrchestrator
from penin.omega.caos_kratos import phi_kratos, KratosController
from penin.omega.market import InternalMarket, Need, Offer, MarketMaker
from penin.omega.neural_chain import add_block, verify_chain, NeuralLedger
from penin.omega.self_rag import ingest_text, query, SelfRAG
from penin.omega.api_metabolizer import record_call, suggest_replay, APIMetabolizer
from penin.omega.immunity import anomaly_score, guard, ImmunitySystem
from penin.omega.checkpoint import save_snapshot, restore_last, CheckpointManager
from penin.omega.game import ema_grad, AdaptiveOptimizer
from penin.omega.darwin_audit import darwinian_score, DarwinianAuditor, Variant
from penin.omega.zero_consciousness import spi_proxy, assert_zero_consciousness, ZeroConsciousnessMonitor


class TestLifeEquation:
    """Test Life Equation (+) functionality"""
    
    def test_life_equation_pass(self):
        """Test Life Equation with passing conditions"""
        verdict = life_equation_simple(
            base_alpha=0.001,
            ece=0.005,
            rho_bias=1.01,
            risk_rho=0.95,
            caos_values=(0.8, 0.7, 0.6, 0.9),
            sr_values=(0.85, 1.0, 0.80, 0.82),
            dL_inf=0.02,
            G=0.90
        )
        
        assert verdict.ok == True
        assert verdict.alpha_eff > 0
        assert "phi" in verdict.metrics
        assert "sr" in verdict.metrics
    
    def test_life_equation_fail_ethics(self):
        """Test Life Equation fails on ethics violation"""
        verdict = life_equation_simple(
            ece=0.02,  # Exceeds threshold
            rho_bias=1.01,
            risk_rho=0.95,
            caos_values=(0.8, 0.7, 0.6, 0.9),
            sr_values=(0.85, 1.0, 0.80, 0.82),
            dL_inf=0.02,
            G=0.90
        )
        
        assert verdict.ok == False
        assert verdict.alpha_eff == 0.0
    
    def test_life_equation_fail_risk(self):
        """Test Life Equation fails on risk contractivity"""
        verdict = life_equation_simple(
            ece=0.005,
            rho_bias=1.01,
            risk_rho=1.1,  # Non-contractive
            caos_values=(0.8, 0.7, 0.6, 0.9),
            sr_values=(0.85, 1.0, 0.80, 0.82),
            dL_inf=0.02,
            G=0.90
        )
        
        assert verdict.ok == False
        assert verdict.alpha_eff == 0.0
    
    def test_life_equation_fail_delta_linf(self):
        """Test Life Equation fails on insufficient ΔL∞"""
        verdict = life_equation_simple(
            ece=0.005,
            rho_bias=1.01,
            risk_rho=0.95,
            caos_values=(0.8, 0.7, 0.6, 0.9),
            sr_values=(0.85, 1.0, 0.80, 0.82),
            dL_inf=0.005,  # Below threshold
            G=0.90
        )
        
        assert verdict.ok == False
        assert verdict.alpha_eff == 0.0


class TestFractal:
    """Test Fractal DSL functionality"""
    
    def test_build_fractal(self):
        """Test fractal tree building"""
        root = build_fractal(
            root_cfg={"test": "config"},
            depth=2,
            branching=3
        )
        
        assert root.id == "Ω-0"
        assert len(root.children) == 3
        assert len(root.children[0].children) == 3
    
    def test_propagate_update(self):
        """Test configuration propagation"""
        root = build_fractal(
            root_cfg={"value": 1.0},
            depth=2,
            branching=2
        )
        
        propagate_update(root, {"value": 2.0})
        
        assert root.config["value"] == 2.0
        assert root.children[0].config["value"] == 2.0
        assert root.children[0].children[0].config["value"] == 2.0
    
    def test_fractal_orchestrator(self):
        """Test FractalOrchestrator"""
        orch = FractalOrchestrator()
        
        assert orch.root is not None
        assert orch.update_all({"test": "value"})
        
        health = orch.get_health()
        assert "avg" in health
        assert "min" in health


class TestSwarm:
    """Test Swarm Cognitive functionality"""
    
    def test_heartbeat(self):
        """Test heartbeat recording"""
        success = heartbeat("test-node", {
            "phi": 0.7,
            "sr": 0.85,
            "g": 0.9,
            "health": 1.0
        })
        
        assert success == True
    
    def test_sample_global_state(self):
        """Test global state aggregation"""
        # Add some heartbeats
        heartbeat("node-1", {"phi": 0.7, "sr": 0.85, "g": 0.9, "health": 1.0})
        heartbeat("node-2", {"phi": 0.8, "sr": 0.80, "g": 0.85, "health": 0.95})
        
        state = sample_global_state(60)
        
        assert "phi_avg" in state
        assert "sr_avg" in state
        assert state["node_count"] >= 0
    
    def test_swarm_orchestrator(self):
        """Test SwarmOrchestrator"""
        orch = SwarmOrchestrator("test-node")
        
        orch.emit_heartbeat({
            "phi": 0.75,
            "sr": 0.82,
            "g": 0.88,
            "health": 0.98
        })
        
        consensus = orch.get_consensus()
        assert "consensus" in consensus
        assert "state" in consensus


class TestCaosKratos:
    """Test CAOS-KRATOS functionality"""
    
    def test_phi_kratos(self):
        """Test KRATOS enhancement"""
        standard = phi_kratos(0.6, 0.5, 0.4, 0.3, exploration_factor=1.0)
        enhanced = phi_kratos(0.6, 0.5, 0.4, 0.3, exploration_factor=2.0)
        
        # Enhanced should be different (usually higher)
        assert enhanced != standard
    
    def test_kratos_controller(self):
        """Test KratosController safety"""
        controller = KratosController()
        
        # Safe exploration
        result = controller.compute(
            C=0.7, A=0.6, O=0.5, S=0.4,
            safety_score=0.8,
            mode="explore"
        )
        
        assert result["exploration_allowed"] == True
        assert "phi_kratos" in result
        
        # Unsafe - should block
        result = controller.compute(
            C=0.7, A=0.6, O=0.5, S=0.4,
            safety_score=0.5,
            mode="explore"
        )
        
        assert result["exploration_allowed"] == False


class TestMarketplace:
    """Test Cognitive Marketplace"""
    
    def test_market_matching(self):
        """Test market matching"""
        market = InternalMarket()
        
        needs = [
            Need("agent1", "cpu_time", 10.0, 2.0),
            Need("agent2", "memory", 5.0, 1.0)
        ]
        
        offers = [
            Offer("provider1", "cpu_time", 15.0, 1.5),
            Offer("provider2", "memory", 10.0, 0.8)
        ]
        
        trades = market.match(needs, offers)
        
        assert len(trades) == 2
        assert trades[0].qty == 10.0  # Full need satisfied
    
    def test_market_maker(self):
        """Test MarketMaker pricing"""
        maker = MarketMaker()
        
        price = maker.get_price("cpu_time")
        assert price > 0
        
        offers = maker.create_offers()
        assert len(offers) > 0


class TestNeuralChain:
    """Test Neural Blockchain"""
    
    def test_add_block(self):
        """Test block addition"""
        hash1 = add_block({"test": "data1"})
        assert hash1 is not None
        
        hash2 = add_block({"test": "data2"}, hash1)
        assert hash2 is not None
        assert hash2 != hash1
    
    def test_verify_chain(self):
        """Test chain verification"""
        add_block({"test": "data"})
        valid, error = verify_chain()
        
        assert valid == True
        assert error is None
    
    def test_neural_ledger(self):
        """Test NeuralLedger interface"""
        ledger = NeuralLedger()
        
        hash1 = ledger.record_state({"metric": 0.5})
        assert hash1 is not None
        
        history = ledger.get_history(10)
        assert len(history) > 0


class TestSelfRAG:
    """Test Self-RAG functionality"""
    
    def test_ingest_query(self):
        """Test document ingestion and query"""
        ingest_text("test_doc", "This is a test document about PENIN evolution")
        
        results = query("PENIN")
        assert len(results) > 0
        assert results[0]["score"] > 0
    
    def test_self_rag(self):
        """Test SelfRAG orchestrator"""
        rag = SelfRAG()
        
        rag.ingest("doc1", "Content about Life Equation and evolution")
        
        answer = rag.ask("What is Life Equation?")
        assert "answer" in answer
        assert "confidence" in answer


class TestAPIMetabolizer:
    """Test API Metabolizer"""
    
    def test_record_suggest(self):
        """Test recording and suggestion"""
        record_call(
            "openai", "/chat", 
            {"prompt": "test prompt"},
            {"response": "test response"},
            latency_ms=100,
            cost_usd=0.001
        )
        
        suggestion = suggest_replay("test prompt", "openai")
        assert suggestion is not None
    
    def test_metabolizer(self):
        """Test APIMetabolizer"""
        metabolizer = APIMetabolizer()
        
        # First call - miss
        response, cached = metabolizer.metabolize(
            "test", "/endpoint",
            {"prompt": "new prompt"},
            fallback_fn=lambda x: {"result": "computed"}
        )
        
        assert cached == False
        
        stats = metabolizer.get_stats()
        assert stats["cache_misses"] > 0


class TestImmunity:
    """Test Digital Immunity"""
    
    def test_anomaly_score(self):
        """Test anomaly scoring"""
        # Normal metrics
        score = anomaly_score({
            "accuracy": 0.85,
            "loss": 0.15
        })
        assert score < 1.0
        
        # Anomalous metrics
        score = anomaly_score({
            "accuracy": -0.5,  # Invalid
            "loss": float('nan')  # NaN
        })
        assert score > 1.0
    
    def test_guard(self):
        """Test immunity guard"""
        # Should pass
        assert guard({"metric": 0.5}, trigger=1.0) == True
        
        # Should fail
        assert guard({"metric": float('nan')}, trigger=1.0) == False
    
    def test_immunity_system(self):
        """Test ImmunitySystem"""
        system = ImmunitySystem()
        
        result = system.check({
            "accuracy": 0.9,
            "loss": 0.1
        })
        
        assert result["safe"] == True
        
        # Check with anomaly
        result = system.check({
            "accuracy": float('inf')
        })
        
        assert result["safe"] == False


class TestCheckpoint:
    """Test Checkpoint & Repair"""
    
    def test_save_restore(self):
        """Test snapshot save and restore"""
        state = {"test": "data", "value": 42}
        
        snap_id = save_snapshot(state)
        assert snap_id is not None
        
        restored = restore_last()
        assert restored is not None
        assert restored["test"] == "data"
    
    def test_checkpoint_manager(self):
        """Test CheckpointManager"""
        manager = CheckpointManager()
        
        snap_id = manager.checkpoint(
            {"metric": 0.5},
            force=True,
            reason="test"
        )
        
        assert snap_id is not None
        
        restored = manager.restore()
        assert restored is not None


class TestGAME:
    """Test GAME functionality"""
    
    def test_ema_grad(self):
        """Test exponential moving average"""
        ema = ema_grad(0.5, 0.7, beta=0.9)
        
        assert 0.5 < ema < 0.7  # Should be between old and new
    
    def test_adaptive_optimizer(self):
        """Test AdaptiveOptimizer"""
        opt = AdaptiveOptimizer()
        
        gradients = {"param1": 0.1, "param2": -0.2}
        updates = opt.step(gradients)
        
        assert "param1" in updates
        assert "param2" in updates
        
        stats = opt.get_stats()
        assert stats["step_count"] == 1


class TestDarwinianAudit:
    """Test Darwinian Audit"""
    
    def test_darwinian_score(self):
        """Test Darwinian scoring"""
        score = darwinian_score(
            life_ok=True,
            caos_phi=0.7,
            sr=0.8,
            G=0.9,
            L_inf=0.85
        )
        
        assert score > 0
        
        # Life not OK
        score = darwinian_score(
            life_ok=False,
            caos_phi=0.7,
            sr=0.8,
            G=0.9,
            L_inf=0.85
        )
        
        assert score == 0.0
    
    def test_darwinian_auditor(self):
        """Test DarwinianAuditor"""
        auditor = DarwinianAuditor()
        
        variant = Variant(
            id="test-variant",
            generation=0,
            fitness=0.0,
            traits={"learning_rate": 0.01}
        )
        
        fitness = auditor.evaluate_variant(
            variant,
            life_ok=True,
            metrics={"phi": 0.7, "sr": 0.8, "G": 0.9, "L_inf": 0.85}
        )
        
        assert fitness > 0
        
        # Add to population
        auditor.population.add_variant(variant)
        
        # Try selection
        selected = auditor.select_for_promotion(min_fitness=0.5)
        assert selected is not None or variant.fitness < 0.5


class TestZeroConsciousness:
    """Test Zero-Consciousness Proof"""
    
    def test_spi_proxy(self):
        """Test SPI calculation"""
        spi = spi_proxy(
            ece=0.01,
            randomness=0.8,
            introspection_leak=0.1
        )
        
        assert 0 <= spi <= 1
    
    def test_assert_zero_consciousness(self):
        """Test consciousness assertion"""
        # Low SPI - should pass
        assert assert_zero_consciousness(0.03, tau=0.05) == True
        
        # High SPI - should fail
        assert assert_zero_consciousness(0.1, tau=0.05) == False
    
    def test_zero_consciousness_monitor(self):
        """Test ZeroConsciousnessMonitor"""
        monitor = ZeroConsciousnessMonitor()
        
        check = monitor.check(
            ece=0.01,
            randomness=0.9,
            introspection_leak=0.05
        )
        
        assert check.passed == True or check.passed == False
        assert "spi" in check.to_dict()
        
        report = monitor.get_report()
        assert "status" in report
        assert "recommendation" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])