from __future__ import annotations
import json, os, sys, time, subprocess, math
from pathlib import Path
sys.path.append("scripts")
from _common_fusion import _norm_url, repo_slug, latest_for_slug

PYEXE = os.environ.get("VENV_PY") or sys.executable

def load_inventory() -> list[dict]:
    p = Path("scripts/_repos.all.json")
    if not p.exists():
        raise SystemExit("❌ inventory não encontrado: scripts/_repos.all.json (gere com gh repo list ...)")
    return json.loads(p.read_text(encoding="utf-8"))

def rank_repo(r: dict) -> float:
    stars = float(r.get("stars",0))
    du = float(r.get("diskUsage",0))
    is_fork = 1.0 if r.get("isFork") else 0.0
    return stars*2.0 + du/1000.0 - is_fork*0.5

def should_skip(slug: str, novelty_min: float) -> bool:
    last = latest_for_slug(slug)
    if not last: return False
    nov = ((last.get("novelty") or {}).get("vs_global"))
    if nov is None: return False
    return nov < novelty_min

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=int(os.environ.get("FUSE_TOP","50")))
    ap.add_argument("--mode", default=os.environ.get("FUSE_MODE","auto"))
    ap.add_argument("--workers", type=int, default=1)  # este runner é sequencial; parâmetro mantido por compat
    ap.add_argument("--seed", type=int, default=int(time.time()))
    ap.add_argument("--jitter", type=float, default=float(os.environ.get("FUSE_JITTER","0.001")))
    ap.add_argument("--pop", type=int, default=int(os.environ.get("FUSE_POP","16")))
    ap.add_argument("--gen", type=int, default=int(os.environ.get("FUSE_GEN","2")))
    ap.add_argument("--novelty-min", type=float, default=0.01)
    ap.add_argument("--stop-eps", type=float, default=0.005)
    ap.add_argument("--stop-window", type=int, default=30)
    ap.add_argument("--stop-streak", type=int, default=2)
    args = ap.parse_args()

    inv = load_inventory()
    inv = sorted(inv, key=rank_repo, reverse=True)
    selected = inv[:args.top]

    roll = []
    cold_streak = 0
    ok=0; sk=0

    for i,r in enumerate(selected,1):
        url = _norm_url(r["url"])
        slug = repo_slug(url)
        if should_skip(slug, args.novelty_min):
            sk += 1
            print(f"[{i}/{len(selected)}] skip (nov<min) :: {url}")
            continue
        seed = args.seed + i
        print(f"[{i}/{len(selected)}] smart :: {url} | seed={seed} jitter={args.jitter}")
        cmd = [
            PYEXE, "scripts/metabolize_repo.py",
            "--mode", args.mode, "--src", url,
            "--seed", str(seed),
            "--population", str(args.pop),
            "--generations", str(args.gen),
            "--jitter", str(args.jitter),
        ]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error processing {url}: {e}")
            print(f"   stderr: {e.stderr}")
            continue
        # ler novidade do último WORM do slug
        nov = None
        # Try to parse novelty value from subprocess output
        try:
            # Assume output is JSON with a 'novelty' field
            out_json = json.loads(result.stdout)
            nov = out_json.get("novelty")
        except Exception:
            # Fallback: try to parse a line like 'novelty: <value>'
            for line in result.stdout.splitlines():
                if line.lower().startswith("novelty:"):
                    try:
                        nov = float(line.split(":",1)[1].strip())
                    except Exception:
                        nov = None
                    break
        if nov is not None:
            roll.append(nov)
            if len(roll) > args.stop_window:
                roll.pop(0)
            mean = sum(roll)/len(roll)
            print(f"   → novelty_global_mean(last {len(roll)}): {mean:.6f}")
            if mean < args.stop_eps:
                cold_streak += 1
                if cold_streak >= args.stop_streak:
                    print(f"🛑 critério de parada: média<{args.stop_eps} por {cold_streak} janelas")
                    break
            else:
                cold_streak = 0
        ok += 1

    print(f"\nResumo smart-run: run={ok} skip={sk} stop_streak={cold_streak}")

if __name__ == "__main__":
    main()
