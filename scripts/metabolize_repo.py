from __future__ import annotations
import argparse, json, time, random
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="auto")
    ap.add_argument("--src", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--population", type=int, default=1)
    ap.add_argument("--generations", type=int, default=1)
    ap.add_argument("--jitter", type=float, default=0.0)
    args = ap.parse_args()

    random.seed(args.seed)
    slug = args.src.replace("https://","").replace("/","-")
    ts = time.strftime("%Y%m%d_%H%M%S")
    outdir = Path("penin/ledger/fusion"); outdir.mkdir(parents=True, exist_ok=True)
    fn = outdir / f"fusion_{slug}_{ts}_{random.randint(100000,999999)}.json"
    payload = {
        "source": args.src, "slug": slug, "timestamp": ts,
        "novelty": {"vs_global": max(0.0, min(1.0, 0.5 + random.uniform(-args.jitter, args.jitter)))},
        "population": args.population, "generations": args.generations, "mode": args.mode,
    }
    fn.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"✔ WORM salvo: {fn}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
