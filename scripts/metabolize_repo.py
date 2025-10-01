import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "fusion" / "megaIAAA.plan.yaml"
POL = ROOT / "policies" / "fusion_policies.yaml"
WORM_DIR = ROOT / "penin" / "ledger" / "fusion"


def load_yaml(p: Path):
    import yaml

    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def acceptance_ok(m, acc) -> bool:
    ratio = m["caos_pos"] / max(m["caos_pre"], 1e-9)
    return (
        m["delta_linf"] >= acc["min_delta_linf"]
        and ratio >= acc["min_caos_ratio"]
        and m["sr"] >= acc["min_sr"]
        and m["G"] >= acc["min_G"]
        and m["ece"] <= acc["max_ece"]
        and m["rho_bias"] <= acc["max_rho_bias"]
        and m["fp"] <= acc["max_fp"]
    )


def worm_write(entry: dict) -> Path:
    WORM_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = WORM_DIR / f"fusion_megaIAAA_{ts}.json"
    out.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return out


def main():
    # 0) Sanity
    if not PLAN.exists():
        print(f"❌ Plano não encontrado: {PLAN}")
        sys.exit(1)

    plan = load_yaml(PLAN)
    acc = plan["acceptance"]

    # 1) Instanciar adapter emergente
    from penin.integrations.evolution import neuroevo_evox_ray as hyb

    inst = hyb.instantiate(population=32, generations=3)
    metrics = inst.run_shadow()

    # 2) Checar origem (genes): só valida acesso
    src = plan.get("source_url", "")
    genes = {"source_url": src}
    try:
        subprocess.run(["git", "ls-remote", src, "HEAD"], check=True, capture_output=True, text=True)
        genes["reachable"] = True
    except Exception:
        genes["reachable"] = False

    # 3) Gates
    ok = acceptance_ok(metrics, acc)

    # 4) WORM
    proof = {
        "fusion": "megaIAAA",
        "plan": plan,
        "genes": genes,
        "adapter": inst.describe(),
        "metrics": metrics,
        "gate_pass": bool(ok),
        "timestamp": time.time(),
    }
    f = worm_write(proof)
    print(f"✔ WORM salvo: {f}")
    print(f"Σ-Guard gates: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
