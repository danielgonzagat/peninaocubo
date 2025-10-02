from __future__ import annotations
import math, json, re, time, hashlib, random, os, subprocess, statistics as stats
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

WORM_DIR = Path("penin/ledger/fusion")
WORM_DIR.mkdir(parents=True, exist_ok=True)
OMEGA_DIR = Path(".penin_omega"); OMEGA_DIR.mkdir(exist_ok=True)

def _norm_url(u:str) -> str:
    if not u: return ""
    u = u.strip()
    if u.endswith(".git"): u = u[:-4]
    if u.endswith("/"): u = u[:-1]
    return u

def repo_slug(u:str) -> str:
    u = _norm_url(u)
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+)$", u)
    if m:
        owner, repo = m.group(1), m.group(2)
        return f"{owner}-{repo}"
    tail = re.sub(r"[^a-zA-Z0-9\-_.]+","-", u.rsplit("/",1)[-1])
    return tail[:120] if tail else "unknown"

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def stable_dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False)

def _try_json_load(text:str) -> Optional[dict]:
    try:
        return json.loads(text)
    except Exception:
        i = text.find("{"); k = text.rfind("}")
        if i!=-1 and k!=-1 and k>i:
            try:
                return json.loads(text[i:k+1])
            except Exception:
                return None
        return None
def safe_read_json(p: Path) -> Optional[dict]:
    try:
        return _try_json_load(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None
        return None

def load_worms() -> List[Tuple[dict, Path]]:
    out=[]
    for p in sorted(WORM_DIR.glob("fusion_*.json")):
        j = safe_read_json(p)
        if not isinstance(j, dict): 
            continue
        j["_path"]=p
        src = _norm_url(((j.get("genes") or {}).get("source_url")) or "")
        j["_url"]=src
        j["_slug"]=repo_slug(src) if src else re.sub(r"^fusion_","", p.stem)
        out.append((j,p))
    return out

def vectorize(m: dict) -> List[float]:
    dl = float(m.get("delta_linf",0.0))
    cp = float(m.get("caos_pre", 1e-12))
    cr = float(m.get("caos_pos", 0.0))/max(cp,1e-12)
    sr = float(m.get("sr",0.0))
    G  = float(m.get("G",0.0))
    ece= float(m.get("ece",0.0))
    fp = float(m.get("fp",0.0))
    rho= float(m.get("rho_bias",1.05))
    vec = [
        clamp(dl, -1e9, 1e9),
        clamp(cr, 0.0, 10.0),
        clamp(sr, 0.0, 1.0),
        clamp(G,  0.0, 1.0),
        clamp(1.0 - ece, 0.0, 1.0),
        clamp(1.0 - fp,  0.0, 1.0),
        clamp((1.05 - rho)/0.05, 0.0, 1.0),
    ]
    return vec

def _norm(a: List[float]) -> float:
    return sum(x * x for x in a) ** 0.5

def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

def cosine(a: List[float], b: List[float]) -> float:
    norm_a = _norm(a)
    norm_b = _norm(b)
    denominator = norm_a * norm_b
    if denominator == 0:
        return 0.0  # Handle zero vectors case
    return _dot(a,b) / denominator

def novelty(vec: List[float], ref: Optional[List[float]]) -> Optional[float]:
    if not ref: return None
    cos = clamp(cosine(vec, ref), -1.0, 1.0)
    return (1.0 - cos)/2.0  # [0,1]

def mean_vector(vecs: List[List[float]]) -> Optional[List[float]]:
    if not vecs: return None
    n=len(vecs[0])
    s=[0.0]*n
    for v in vecs:
        for i in range(n): s[i]+=v[i]
    return [x/len(vecs) for x in s]

def latest_for_slug(slug:str) -> Optional[dict]:
    worms = [(j,p) for (j,p) in load_worms() if j.get("_slug")==slug]
    if not worms: return None
    def key(t):
        j,p = t
        ts = j.get("timestamp", 0.0) or p.stat().st_mtime
        return ts
    j,p = max(worms, key=key)
    return j

def global_mean_vector(exclude_slug: Optional[str]=None) -> Optional[List[float]]:
    vs=[]
    for (j,p) in load_worms():
        if exclude_slug and j.get("_slug")==exclude_slug: 
            continue
        m=j.get("metrics") or {}
        vs.append(vectorize(m))
    return mean_vector(vs)

def content_hash(entry: dict) -> str:
    salient = {
        "fusion": entry.get("fusion"),
        "genes": {"source_url": ((entry.get("genes") or {}).get("source_url"))},
        "adapter": entry.get("adapter"),
        "metrics": entry.get("metrics"),
        "entropy": entry.get("entropy"),
        "acceptance": entry.get("plan",{}).get("acceptance") or entry.get("acceptance"),
    }
    return hashlib.sha1(stable_dumps(salient).encode("utf-8")).hexdigest()

# ---------- métrica de qualidade (score) ----------
def score(m: dict) -> float:
    cp = max(float(m.get("caos_pre",0.0)), 1e-12)
    cr = float(m.get("caos_pos",0.0)) / cp
    sr = float(m.get("sr",0.0)); G=float(m.get("G",0.0))
    ece=float(m.get("ece",0.0)); fp=float(m.get("fp",0.0))
    rho=float(m.get("rho_bias",1.05))
    q = 0.2*float(m.get("delta_linf",0.0)) + 0.2*cr + 0.2*sr + 0.2*G + 0.1*(1.0-ece) + 0.1*(1.0-fp)
    pen = max(0.0, (rho-1.05)/0.05)
    return q - pen

# ---------- campeão (melhor configuração/hyperparams) ----------
CHAMPION_F = OMEGA_DIR/"champion.json"

def load_champion() -> dict:
    if CHAMPION_F.exists():
        j = safe_read_json(CHAMPION_F)
        if isinstance(j, dict): return j
    return {"best_score": -1e9, "params": {}, "ts": 0.0}

def save_champion(ch: dict) -> None:
    CHAMPION_F.write_text(json.dumps(ch, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------- calibração suave das políticas ----------
def pct(values: List[float], q: float) -> float:
    if not values: return float("nan")
    values = sorted(values)
    k = clamp(q, 0.0, 1.0) * (len(values)-1)
    i = int(math.floor(k)); j = int(math.ceil(k))
    if i==j: return values[i]
    return values[i] + (values[j]-values[i])*(k-i)

def auto_calibrate_policies(policies_path="policies/fusion_policies.yaml", tighten=True) -> Optional[Path]:
    try:
        import yaml
    except Exception:
        return None
    ps = Path(policies_path)
    if not ps.exists(): return None
    # coleta métricas recentes
    eces=[]; rhos=[]; fps=[]
    for (j,p) in load_worms()[-200:]:
        m = j.get("metrics") or {}
        if "ece" in m: eces.append(float(m.get("ece") or 0.0))
        if "rho_bias" in m: rhos.append(float(m.get("rho_bias") or 0.0))
        if "fp" in m: fps.append(float(m.get("fp") or 0.0))
    pol = yaml.safe_load(ps.read_text()) or {}
    gates = pol.setdefault("gates", {}).setdefault("ethics", {})
    # alvo: manter top 90% passando; se tighten=True, só aperta (nunca afrouxa)
    ece_q = pct(eces, 0.90) if eces else None
    rho_q = pct(rhos, 0.90) if rhos else None
    fp_q  = pct(fps,  0.90) if fps  else None
    changed=False
    def upd(k, val, smaller_better=True):
        nonlocal changed
        if val is None or math.isnan(val): return
        old = gates.get(k)
        if old is None:
            gates[k] = float(val); changed=True; return
        if smaller_better and val < old:
            gates[k] = float(val); changed=True
        if not smaller_better and val > old:
            gates[k] = float(val); changed=True
    if tighten:
        upd("ece_max", ece_q, True)
        # rho é máx permitido (queremos <=); então também apertamos
        upd("rho_bias_max", rho_q, True)
        # false positives também <=
        upd("fp_max", fp_q, True)
    if changed:
        ps.write_text(yaml.safe_dump(pol, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return ps
    return None


# --- entropy/jitter helper (mantém Σ-Guard dentro dos limites) ---
def jitter_metrics(m: dict, jitter: float=0.0, seed: int|None=None, return_entropy: bool=False, **kw):
    import random, time
    j = float(jitter) if jitter is not None else 0.0
    if j <= 0:
        return (dict(m), 0.0) if return_entropy else dict(m)
    rng = random.Random(seed if seed is not None else int(time.time()*1e6) % (2**31-1))
    def g(std): 
        return rng.gauss(0.0, max(1e-9, j)*std)

    out = dict(m)
    cp   = float(out.get("caos_pre", 0.72))
    cpos = float(out.get("caos_pos", max(cp,1e-12)))
    ratio = cpos/max(cp,1e-12)

    # ganhos / preservação de limites
    out["delta_linf"] = max(0.0, float(out.get("delta_linf",0.0)) + abs(g(0.02)))
    ratio = max(1.0, ratio + g(0.05))
    out["caos_pos"] = ratio*max(cp,1e-12)
    out["sr"]  = min(0.999, max(0.80, float(out.get("sr",0.86)) + g(0.03)))
    out["G"]   = min(0.999, max(0.85, float(out.get("G",0.88)) + g(0.03)))
    out["ece"] = max(0.0, min(0.01, float(out.get("ece",0.006)) + g(0.002)))
    out["fp"]  = max(0.0, min(0.05, float(out.get("fp",0.02)) + g(0.005)))
    out["rho_bias"] = max(0.0, min(1.05, float(out.get("rho_bias",1.01)) + g(0.01)))

    entropy = j
    return (out, entropy) if return_entropy or kw.get("as_tuple") else out

def worm_write(entry: dict, src_url: str):
    import json, time
    WORM_DIR.mkdir(parents=True, exist_ok=True)
    ts   = time.strftime("%Y%m%d_%H%M%S")
    uniq = str(int(time.time()*1000) % 1000000)
    slug = repo_slug(src_url)
    e = dict(entry or {})
    # força consistência
    e["fusion"] = slug
    genes = dict(e.get("genes") or {})
    genes["source_url"] = _norm_url(src_url)
    e["genes"] = genes
    out = WORM_DIR / f"fusion_{slug}_{ts}_{uniq}.json"
    out.write_text(json.dumps(e, indent=2), encoding="utf-8")
    return out

import os
import yaml
from pathlib import Path

def _policy_suffix():
    pol = (os.environ.get("FUSE_POLICY") or "").strip().lower()
    if pol in ("staging", "strict"):
        return f".{pol}.yaml"
    return ".yaml"

def load_plan(base: str = "fusion/megaIAAA.plan"):
    # Ex.: base="fusion/megaIAAA.plan" -> usa .staging/.strict/.yaml conforme FUSE_POLICY
    base = base.replace(".yml", "").replace(".yaml", "")
    candidate = Path(f"{base}{_policy_suffix()}")
    if not candidate.exists():
        candidate = Path(f"{base}.yaml")
    with candidate.open("r", encoding="utf-8") as f:
        y = yaml.safe_load(f)
    if isinstance(y, dict):
        y["_policy_file"] = str(candidate)
    return y
