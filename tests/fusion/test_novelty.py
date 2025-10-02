import sys
from pathlib import Path
sys.path.append("scripts")
from _common_fusion import vectorize, novelty

def test_vectorize_and_novelty():
    m = {"delta_linf":0.012,"caos_pre":0.72,"caos_pos":0.75,"sr":0.86,"G":0.88,"ece":0.006,"rho_bias":1.01,"fp":0.02}
    v = vectorize(m)
    assert len(v)==7
    # same metric => novelty ~ 0
    assert (novelty(v, v) or 0.0) < 1e-8
    
    # Test edge cases
    v2 = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    nov = novelty(v2, v3)
    assert nov is not None and 0.0 <= nov <= 1.0
    
    # Test with None reference
    assert novelty(v, None) is None
