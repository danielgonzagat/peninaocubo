import importlib


def test_emergent_adapter_shadow_ok():
    mod = importlib.import_module("penin.integrations.evolution.neuroevo_evox_ray")
    inst = mod.instantiate(population=8, generations=1)
    m = inst.run_shadow()
    assert m["caos_pos"] >= m["caos_pre"]
    assert m["sr"] >= 0.80 and m["G"] >= 0.85
    assert m["ece"] <= 0.01 and m["rho_bias"] <= 1.05 and m["fp"] <= 0.05
