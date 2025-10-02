#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone, timedelta
import argparse

p = argparse.ArgumentParser()
p.add_argument("--hours", type=int, default=168)
p.add_argument("--out-md", default="docs/FUSION_AUDIT.md")
p.add_argument("--out-csv", default="fusion_results/audit_summary.csv")
args = p.parse_args()

root = Path("penin/ledger/fusion")
now = datetime.now(timezone.utc)
cutoff = now - timedelta(hours=args.hours)

total=0; pass_total=0
by_policy = Counter(); by_policy_n = Counter()
by_slug_total = Counter(); by_slug_pass = Counter()
last_ts = {}

def policy_label(j):
    pf = j.get("_policy_file") or ""
    if pf.endswith(".staging.yaml"): return "staging"
    if pf.endswith(".strict.yaml"):  return "strict"
    if pf.endswith(".plan.yaml"):    return "default"
    return "unknown"

def to_dt(ts):
    try: return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except: return None

events_recent = []
for fp in sorted(root.glob("fusion_*.json")):
    try:
        j = json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        continue
    total += 1
    slug = j.get("_slug") or j.get("fusion") or "unknown"
    ok   = bool(j.get("gate_pass"))
    ts   = to_dt(j.get("timestamp"))
    pol  = policy_label(j)

    by_slug_total[slug]+=1
    if ok:
        pass_total += 1
        by_slug_pass[slug]+=1
        by_policy[pol]+=1
    by_policy_n[pol]+=1

    if ts:
        last_ts[slug] = max(last_ts.get(slug, ts), ts)
        if ts >= cutoff:
            events_recent.append((ts, slug, ok, pol))

rate = (pass_total/total*100) if total else 0.0
top = sorted(by_slug_pass.items(),
             key=lambda kv:(kv[1], last_ts.get(kv[0], datetime.fromtimestamp(0, tz=timezone.utc))),
             reverse=True)[:50]

Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
with open(args.out_csv, "w", encoding="utf-8") as fh:
    fh.write("slug,total,pass,pass_rate,last_ts\n")
    for slug,_ in top:
        t = by_slug_total[slug]; p = by_slug_pass[slug]
        r = (p/t*100) if t else 0.0
        lt = last_ts.get(slug)
        fh.write(f"{slug},{t},{p},{r:.1f},{lt.isoformat() if lt else ''}\n")

Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
def fmt_policy():
    lines = ["| policy | pass/total | rate |","|---|---:|---:|"]
    for pol in ("staging","strict","default","unknown"):
        if by_policy_n[pol]==0: continue
        a = by_policy[pol]; b= by_policy_n[pol]
        lines.append(f"| {pol} | {a}/{b} | {a/b*100:.1f}% |")
    return "\n".join(lines)

def fmt_recent():
    lines = ["| when (UTC) | slug | policy | pass |","|---|---|---|:--:|"]
    for ts,slug,ok,pol in sorted(events_recent, reverse=True)[:80]:
        lines.append(f"| {ts.isoformat()} | `{slug}` | {pol} | {'✅' if ok else '❌'} |")
    return "\n".join(lines)

with open(args.out_md, "w", encoding="utf-8") as fh:
    fh.write(f"""# FUSION — Auditoria

**Gerado em:** {now.isoformat()}  
**WORMs totais:** {total}  
**PASS:** {pass_total}  (**{rate:.1f}%**)

## Taxa por policy
{fmt_policy()}

## TOP 50 por PASS
| rank | slug | total | pass | rate | last |
|---:|---|---:|---:|---:|---|
""")
    for i,(slug,p) in enumerate(top,1):
        t = by_slug_total[slug]; r = (p/t*100) if t else 0.0
        lt = last_ts.get(slug); lt_s = lt.isoformat() if lt else ""
        fh.write(f"| {i} | `{slug}` | {t} | {p} | {r:.1f}% | {lt_s} |\n")
    fh.write(f"""

## Últimos eventos (últimas {args.hours}h)
{fmt_recent()}

---
_Gerado por `scripts/audit_fusion.py`._
""")

print(f"✔ Audit: total={total} pass={pass_total} rate={rate:.1f}% -> {args.out_md} & {args.out_csv}")
