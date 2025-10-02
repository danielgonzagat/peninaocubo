from pathlib import Path
from typing import Dict, Any, Optional

    WORM_DIR.mkdir(parents=True, exist_ok=True)
    ts   = time.strftime("%Y%m%d_%H%M%S")
    uniq = str(int(time.time()*1000) % 1_000_000)
    slug = repo_slug(src_url)
    # garanta consistência
    e = dict(entry or {})
    e["fusion"] = slug
    genes = dict(e.get("genes") or {})
    genes["source_url"] = _norm_url(src_url)
    e["genes"] = genes
    e["_slug"] = slug
    out = WORM_DIR / f"fusion_{slug}_{ts}_{uniq}.json"
    out.write_text(json.dumps(e, indent=2), encoding="utf-8")
    return out

    try:
        subprocess.run(["git","ls-remote", src, "HEAD"], check=True, capture_output=True)
        reachable = True
    except Exception:
        pass
    # tentar checar reachability por git (não quebra se git não estiver disponível)
    reachable = False
    try:
        # Validate URL format before passing to git
        if not src.startswith(('https://', 'git://', 'ssh://')) or any(c in src for c in ['&', '|', ';', '`', '$']):
            reachable = False
        else:
            subprocess.run(["git","ls-remote", src, "HEAD"], check=True, capture_output=True, timeout=30)
            reachable = True
    except Exception:
        pass
            "engine": "Shadow" if args.mode=="shadow" or (args.mode=="auto" and os.environ.get("FUSE_REAL","0") in ("0","")) else "NeuroEvoHybrid",
            "population": int(args.pop or 16),
            "generations": int(args.gen or 1),
            "model": "distilbert-base-uncased",
        },
        "metrics": m,
        "gate_pass": bool(ok),
        "timestamp": time.time(),
        "_slug": slug,
    }

    f = worm_write(proof, src)
    print(f"✔ WORM salvo: {f}")
    print(f"Σ-Guard gates: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
