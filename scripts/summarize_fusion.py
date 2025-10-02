from __future__ import annotations
import json, csv, time
from pathlib import Path
from typing import Optional
import math

WORM_DIR = Path("penin/ledger/fusion")
OUT_DIR  = Path("fusion_results")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _try_json(p: Path) -> Optional[dict]:
    s = p.read_text(encoding="utf-8", errors="ignore")
    try:
        return json.loads(s)
    except Exception:
        i = s.find("{"); k = s.rfind("}")
        if i!=-1 and k!=-1 and k>i:
            try:
                return json.loads(s[i:k+1])
            except Exception:
                return None
        return None

def score(m: dict) -> float:
    # simples: pondera qualidade e penaliza ECE/FP/ρ
    cp = max(float(m.get("caos_pre",0.0)), 1e-12)
    cr = float(m.get("caos_pos",0.0)) / cp
    sr = float(m.get("sr",0.0)); G=float(m.get("G",0.0))
    ece=float(m.get("ece",0.0)); fp=float(m.get("fp",0.0))
    rho=float(m.get("rho_bias",1.05))
    q = 0.2*float(m.get("delta_linf",0.0)) + 0.2*cr + 0.2*sr + 0.2*G + 0.1*(1.0-ece) + 0.1*(1.0-fp)
    pen = max(0.0, (rho-1.05)/0.05)
    return q - pen

def main():
    rows=[]
    for p in sorted(WORM_DIR.glob("fusion_*.json")):
        j = _try_json(p)
        if not isinstance(j, dict): 
            continue
        m = j.get("metrics") or {}
        ent = j.get("entropy") or {}
        nov = j.get("novelty") or {}
        genes = j.get("genes") or {}
        rows.append({
            "slug": j.get("fusion"),
            "repo": genes.get("source_url"),
            "worm_file": p.name,
            "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(j.get("timestamp", p.stat().st_mtime))),
            "mode": j.get("mode_used","?"),
            "seed": ent.get("seed"),
            "population": ent.get("population"),
            "generations": ent.get("generations"),
            "jitter": ent.get("jitter"),
            "delta_linf": m.get("delta_linf"),
            "caos_ratio": (m.get("caos_pos",0.0)/max(1e-12, m.get("caos_pre",0.0))),
            "sr": m.get("sr"),
            "G": m.get("G"),
            "ece": m.get("ece"),
            "rho_bias": m.get("rho_bias"),
            "fp": m.get("fp"),
            "nov_last": nov.get("vs_last"),
            "nov_global": nov.get("vs_global"),
            "score": score(m),
            "hash": j.get("content_hash"),
            "gate_pass": j.get("gate_pass", True),
        })
    # CSV
    if rows:
        with open(OUT_DIR/"summary.csv","w",newline="",encoding="utf-8") as fo:
            cw = csv.DictWriter(fo, fieldnames=list(rows[0].keys()))
            cw.writeheader(); cw.writerows(rows)
    # Markdown top 50
    rows_sorted = sorted(rows, key=lambda r: (r["score"] or 0.0), reverse=True)
    md = ["# Fusion Report — Top 50\n",
          "|#|Slug|Repo|Score|novG|SR|G|DeltaLInf|CR|ECE|rho|FP|WORM|\n",
          "|-:|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|\n"]
    for i,r in enumerate(rows_sorted[:50],1):
        md.append(f'|{i}|{r["slug"] or ""}|{r["repo"] or ""}|{r["score"]:.5f}|{(r["nov_global"] or 0):.3f}|{(r["sr"] or 0):.3f}|{(r["G"] or 0):.3f}|{(r["delta_linf"] or 0):.4f}|{(r["caos_ratio"] or 0):.3f}|{(r["ece"] or 0):.4f}|{(r["rho_bias"] or 0):.3f}|{(r["fp"] or 0):.3f}|{r["worm_file"] or ""}|')
    (OUT_DIR/"top_50.md").write_text("\\n".join(md), encoding="utf-8")
    print(f"OK: {len(rows)} WORMs → {OUT_DIR/'summary.csv'} & {OUT_DIR/'top_50.md'}")

if __name__ == "__main__":
    main()
