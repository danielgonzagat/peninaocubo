from __future__ import annotations
import math, os, re, json
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # será verificado em load_plan

LEDGER_DIR_DEFAULT = Path("penin/ledger/fusion")
EPS = 1e-12

def _norm_url(url: str) -> str:
    s = url.strip()
    s = s.replace("git@github.com:", "https://github.com/")
    if s.endswith(".git"):
        s = s[:-4]
    return s

def repo_slug(url: str) -> str:
    """Ex.: https://github.com/user/repo -> github.com-user-repo (lower)"""
    u = _norm_url(url)
    m = re.match(r"https?://([^/]+)/([^/]+)/([^/]+)$", u)
    if not m:
        # fallback robusto
        return re.sub(r"\W+", "-", u.lower()).strip("-")
    host, owner, repo = m.groups()
    return f"{host}-{owner}-{repo}".lower()

def latest_for_slug(slug: str, ledger_dir: Union[str, Path] = LEDGER_DIR_DEFAULT) -> Optional[Path]:
    d = Path(ledger_dir)
    if not d.exists():
        return None
    patt = f"fusion_{slug}_*.json"
    files = sorted(d.glob(patt), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files and not slug.startswith("fusion_"):
        # compat: às vezes o slug já vem com github.com-...
        files = sorted(d.glob(f"fusion_{slug}_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    da = sum(x * x for x in a[:n])
    db = sum(x * x for x in b[:n])
    if da <= EPS or db <= EPS:
        return 0.0
    dot = sum(a[i] * b[i] for i in range(n))
    return float(dot / (math.sqrt(da) * math.sqrt(db)))

def load_plan(path: Union[str, Path]) -> Dict[str, Any]:
    """Carrega um .yaml de plano (ex.: fusion/megaIAAA.plan.yaml)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Plano não encontrado: {p}")
    if yaml is None:
        raise RuntimeError("PyYAML não instalado; pip install pyyaml")
    with p.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Plano malformado: {p}")
    return data
