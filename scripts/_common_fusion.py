from __future__ import annotations
import math, json, re, time, hashlib, random, os, subprocess
from pathlib import Path
from typing import List, Tuple, Optional

WORM_DIR = Path("penin/ledger/fusion")
WORM_DIR.mkdir(parents=True, exist_ok=True)

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

def load_worms() -> List[Tuple[dict, Path]]:
    out=[]
    for p in sorted(WORM_DIR.glob("fusion_*.json")):
        j = _try_json_load(p.read_text(encoding="utf-8", errors="ignore"))
        if not isinstance(j, dict): 
            continue
        j["_path"]=p.as_posix()
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

def _dot(a: List[float], b: List[float]) -> float:
    return sum(x*y for x,y in zip(a,b))

def _norm(a: List[float]) -> float:
    return math.sqrt(_dot(a,a)) or 1e-12

def cosine(a: List[float], b: List[float]) -> float:
    return _dot(a,b)/(_norm(a)*_norm(b))

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

def jitter_metrics(m: dict, jitter: float, seed: Optional[int]) -> dict:
    if not jitter or jitter <= 0: 
        return m
    rnd = random.Random(seed if seed is not None else int(time.time()*1000))
    out=dict(m)
    out["caos_pos"]   = clamp(out.get("caos_pos",0.0)   + rnd.gauss(0, jitter), 0.0, 1e9)
    out["delta_linf"] = out.get("delta_linf",0.0) + rnd.gauss(0, jitter*0.5)
    out["sr"]         = clamp(out.get("sr",0.0)         + rnd.gauss(0, jitter*0.3), 0.0, 1.0)
    out["G"]          = clamp(out.get("G",0.0)          + rnd.gauss(0, jitter*0.3), 0.0, 1.0)
    return out

def worm_write(entry: dict, src_url: str) -> Path:
    WORM_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    uniq = str(int(time.time()*1000) % 1000000)
    slug = repo_slug(src_url)
    out = WORM_DIR / f"fusion_{slug}_{ts}_{uniq}.json"
    out.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    return out

def git_reachable(url: str) -> bool:
    url = _norm_url(url)
    try:
        subprocess.run(["git","ls-remote", url, "HEAD"], check=True, capture_output=True, text=True, timeout=20)
        return True
    except Exception:
        return False
