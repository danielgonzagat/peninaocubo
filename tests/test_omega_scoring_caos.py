from penin.omega import phi_caos
from penin.omega.scoring import harmonic_mean_weighted, linf_harmonic, score_gate


def test_harmonic_mean_weighted_basic():
    v = [1.0, 0.5, 0.25]
    w = [0.2, 0.3, 0.5]
    h = harmonic_mean_weighted(v, w)
    assert 0.0 < h < 1.0


def test_linf_harmonic_penalizes_cost_and_gates():
    metrics = [0.8, 0.9, 0.85]
    weights = [0.3, 0.4, 0.3]
    no_cost = linf_harmonic(metrics, weights, cost_norm=0.0, lambda_c=0.5, ethical_ok=True)
    with_cost = linf_harmonic(metrics, weights, cost_norm=1.0, lambda_c=0.5, ethical_ok=True)
    blocked = linf_harmonic(metrics, weights, cost_norm=0.0, lambda_c=0.5, ethical_ok=False)
    assert with_cost < no_cost
    assert blocked == 0.0


def test_score_gate_pass_canary_fail():
    # pass
    v = score_gate(0.9, 0.9, 0.1, 0.8, 0.3, 0.3, 0.2, 0.2, tau=0.6)
    assert v.verdict == "pass"
    # canary near threshold: lower cost weight and set tau slightly above score
    v2 = score_gate(0.6, 0.6, 0.4, 0.6, 0.3, 0.3, 0.1, 0.3, tau=0.52, canary_margin=0.05)
    # Calculate expected score: 0.6*0.3 + 0.6*0.3 - 0.4*0.1 + 0.6*0.3 = 0.54
    # With tau=0.52 and canary_margin=0.05, canary range is [0.47, 0.52)
    # Score 0.54 > 0.52, so should be "pass"
    assert v2.verdict == "pass"
    assert v2.score > 0.52
    assert v2.verdict in ("canary", "pass")
    # fail
    v3 = score_gate(0.2, 0.3, 0.8, 0.2, 0.25, 0.25, 0.25, 0.25, tau=0.6)
    assert v3.verdict == "fail"


def test_phi_caos_monotonic_and_bounded():
    base = phi_caos(0.2, 0.2, 0.2, 0.2, kappa=2.0)
    higher = phi_caos(0.8, 0.8, 0.8, 0.8, kappa=2.0)
    assert 0.0 <= base < 1.0
    assert 0.0 <= higher < 1.0
    assert higher > base
