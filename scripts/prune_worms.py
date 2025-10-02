from pathlib import Path
from collections import defaultdict
import json, sys

d = Path("penin/ledger/fusion")
keep_per_slug = int(sys.argv[1]) if len(sys.argv) > 1 else 5

buckets = defaultdict(list)
for p in sorted(d.glob("fusion_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        p.unlink(missing_ok=True)
        continue
    slug = j.get("_slug") or j.get("fusion") or "unknown"
    buckets[slug].append(p)

removed = 0
for slug, files in buckets.items():
    for p in files[keep_per_slug:]:
        p.unlink(missing_ok=True)
        removed += 1

print(f"✔ prune: removidos {removed} WORM(s); slugs={len(buckets)}; keep={keep_per_slug}")
