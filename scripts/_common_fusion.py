
from __future__ import annotations
import os, re, math
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

LEDGER_DIR_DEFAULT = Path("penin/ledger/fusion")
EPS = 1e-12

def _norm_url(url: str) -> str:
    s = url.strip().replace("git@github.com:", "https://github.com/")
    return s[:-4] if s.endswith(".git") else s

def repo_slug(url: str) -> str:
    u = _norm_url(url)
    m = re.match(r"https?://([^/]+)/([^/]+)/([^/]+)$", u)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}".lower() if m else re.sub(r"\W+","-",u.lower()).strip("-")

def latest_for_slug(slug: str, ledger_dir: Union[str, Path] = LEDGER_DIR_DEFAULT) -> Optional[Path]:
    d = Path(ledger_dir)
    if not d.exists():
        return None
    patt = f"fusion_{slug}_*.json"
    fs = sorted(d.glob(patt), key=lambda p: p.stat().st_mtime, reverse=True)
    if not fs and not slug.startswith("fusion_"):
        fs = sorted(d.glob(f"fusion_{slug}_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return fs[0] if fs else None

def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b: return 0.0
    n = min(len(a), len(b))
    da = sum(x*x for x in a[:n]); db = sum(x*x for x in b[:n])
    if da <= 1e-12 or db <= 1e-12: return 0.0
    dot = sum(a[i]*b[i] for i in range(n))
    return float(dot / ((da**0.5)*(db**0.5)))

def _plan_candidates(base: Path) -> list[Path]:
    policy = os.getenv("FUSE_POLICY","").strip()
    c: list[Path] = []
    if base.suffix in (".yaml",".yml"):
        if policy: c.append(base.with_name(base.stem + f".{policy}" + base.suffix))
        c.append(base)
        return c
    if policy:
        c += [base.with_suffix(f".{policy}.yaml"), base.with_suffix(f".{policy}.yml")]
    c += [base.with_suffix(".yaml"), base.with_suffix(".yml")]
    return c

def load_plan(path: Union[str, Path]) -> Dict[str, Any]:
    p = Path(path)
    if yaml is None:
        raise RuntimeError("PyYAML não instalado; pip install pyyaml")
    for cand in _plan_candidates(p):
        if cand.exists():
            data = yaml.safe_load(cand.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                raise ValueError(f"Plano malformado: {cand}")
            data["_policy_file"] = str(cand)
            data["_policy"] = os.getenv("FUSE_POLICY","") or "default"
            return data
    raise FileNotFoundError(f"Plano não encontrado: {p}")
