import sys
from pathlib import Path
sys.path.append("scripts")
from _common_fusion import vectorize, novelty

def test_vectorize_and_novelty():
    m = {"delta_linf":0.012,"caos_pre":0.72,"caos_pos":0.75,"sr":0.86,"G":0.88,"ece":0.006,"rho_bias":1.01,"fp":0.02}
    v = vectorize(m)
    assert len(v)==7
    # mesma métrica => novelty ~ 0
    assert (novelty(v, v) or 0.0) < 1e-8
