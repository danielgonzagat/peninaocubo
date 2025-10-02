from __future__ import annotations
import os, sys, time, json, random, subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

sys.path.append("scripts")
from _common_fusion import (
    WORM_DIR, OMEGA_DIR, load_worms, score, load_champion, save_champion,
    auto_calibrate_policies, _norm_url
)

PYEXE = os.environ.get("VENV_PY") or sys.executable

STATE_F = Path("fusion_results/omega_state.json")
STATE_F.parent.mkdir(exist_ok=True, parents=True)

def shell(cmd: List[str]) -> Tuple[int,str,str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def ensure_inventory() -> None:
    inv = Path("scripts/_repos.all.json")
    if inv.exists(): return
    # tenta descobrir owner pela origem do git
    rc,out,_ = shell(["git","remote","get-url","origin"])
    owner = None
    if rc==0 and "github.com" in out:
        try:
            owner = out.rsplit("/",2)[-2].split(":")[-1]
        except Exception:
            owner=None
    owner = os.environ.get("GITHUB_USER") or owner
    if not owner:
        print("⚠️  Could not infer GITHUB_USER; inventory not generated")
        return
    cmd = ["gh","repo","list", owner, "--limit","1200",
           "--json","name,nameWithOwner,url,sshUrl,visibility,isFork,isArchived,isEmpty,licenseInfo,updatedAt,primaryLanguage,diskUsage,stargazerCount"]
    rc,out,err = shell(cmd)
    if rc!=0:
        print("⚠️  gh falhou, siga manualmente:", " ".join(cmd), "\n", err)
        return
    # normaliza esquema esperado pelos runners
    import json as _json
    data = _json.loads(out)
    outv=[]
    for r in data:
        if r["name"]=="peninaocubo": continue
        outv.append({
            "name": r.get("name"),
            "nwo": r.get("nameWithOwner"),
            "url": _norm_url(r.get("url") or ""),
            "ssh": r.get("sshUrl"),
            "visibility": r.get("visibility"),
            "isFork": r.get("isFork") or False,
            "isArchived": r.get("isArchived") or False,
            "isEmpty": r.get("isEmpty") or False,
            "license": (r.get("licenseInfo") or {}).get("spdxId") or "UNKNOWN",
            "updatedAt": r.get("updatedAt"),
            "primaryLanguage": (r.get("primaryLanguage") or {}).get("name"),
            "diskUsage": r.get("diskUsage") or 0,
            "stars": r.get("stargazerCount") or 0,
        })
    inv.write_text(_json.dumps(outv, indent=2), encoding="utf-8")
    print(f"✔ Inventory created: {inv} ({len(outv)} repos)")

def load_state() -> dict:
    if STATE_F.exists():
        try:
            return json.loads(STATE_F.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "cycle": 0,
        "last_seen": [],      # nomes de arquivos WORM já vistos
        "history": [],        # [(cycle, new_n, mean_score, mean_nov)]
        "params": { "mode":"auto","top":60, "pop":16, "gen":2, "jitter":0.001, "novelty_min":0.01 },
    }

def save_state(st: dict) -> None:
    STATE_F.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")

def list_worm_files() -> List[str]:
    return sorted([p.name for p in WORM_DIR.glob("fusion_*.json")])

def new_worms_since(snapshot: List[str]) -> List[str]:
    cur = set(list_worm_files())
    prev = set(snapshot)
    return sorted(cur - prev)

def stats_from_files(files: List[str]) -> Tuple[float,float,int]:
    # retorna (mean_score, mean_nov_global, n)
    import json
    scores=[]; novs=[]
        try:
            s = p.read_text(encoding="utf-8", errors="replace")
            # leitura leniente (arquivos WORM podem ter "lixo" após JSON)
            i=s.find("{"); k=s.rfind("}")
            if i==-1 or k==-1 or k<=i: 
                print(f"Warning: Invalid JSON structure in {p.name}", file=sys.stderr)
                continue
            j=json.loads(s[i:k+1])
            m=j.get("metrics") or {}
            scores.append(float(score(m)))
            novs.append(float(((j.get("novelty") or {}).get("vs_global")) or 0.0))
        except Exception as e:
            print(f"Warning: Failed to parse {p.name}: {e}", file=sys.stderr)
            continue
    n=len(scores)
    if n==0: return (0.0, 0.0, 0)
    return (sum(scores)/n, sum(novs)/n, n)

def run_smart(params: dict) -> None:
    cmd = [
        PYEXE,"scripts/run_smart.py",
        "--top", str(params["top"]),
        "--mode", params["mode"],
        "--seed", str(int(time.time())%10**9),
        "--jitter", str(params["jitter"]),
        "--pop", str(params["pop"]),
        "--gen", str(params["gen"]),
        "--novelty-min", str(params["novelty_min"]),
    ]
    try:
        timeout_val = int(os.environ.get("FUSE_SUBPROC_TIMEOUT", "180"))
        # Clamp timeout to reasonable bounds (30 seconds to 30 minutes)
        timeout_val = max(30, min(1800, timeout_val))
        subprocess.run(cmd, check=False, timeout=timeout_val)
    except subprocess.TimeoutExpired:
        print("⏱ run_smart: subprocess timeout — continuing to next.")

def autotune_once(base: dict) -> dict:
    # tenta Optuna; senão faz três vizinhos do ponto atual
    try:
        import optuna
    except Exception:
        candidates = []
        for jf in (base["jitter"]*0.5, base["jitter"], base["jitter"]*1.6):
            c = dict(base); c["jitter"]=max(1e-6, min(0.01, jf))
            candidates.append(c)
        return max(candidates, key=lambda x: random.random())
    study = optuna.create_study(direction="maximize", study_name="fusion_autotune",
                                storage="sqlite:///fusion_results/optuna_study.db",
                                load_if_exists=True)
    snapshot = list_worm_files()
    def objective(trial: "optuna.trial.Trial") -> float:
        params = {
            "mode": base["mode"],
            "top":  trial.suggest_categorical("top",[40,60,80]),
            "pop":  trial.suggest_categorical("pop",[8,16,32]),
            "gen":  trial.suggest_categorical("gen",[1,2,3]),
            "jitter": trial.suggest_float("jitter", 1e-6, 5e-3, log=True),
            "novelty_min": trial.suggest_float("novelty_min", 0.0, 0.02),
        }
        run_smart(params)
        new = new_worms_since(snapshot)
        mscore, mnov, n = stats_from_files(new)
        # objetivo: score médio *e* novidade média, com leve peso de cardinalidade
        val = mscore + 0.05*mnov + 0.0001*n
        trial.set_user_attr("n_new", n)
        return float(val)
    try:
        study.optimize(objective, n_trials=3, timeout=None, gc_after_trial=True)
    except Exception as e:
        print("⚠️  autotune falhou:", e)
        return base
    bt = study.best_trial
    tuned = dict(base)
    tuned.update({
        "top": bt.params["top"],
        "pop": bt.params["pop"],
        "gen": bt.params["gen"],
        "jitter": bt.params["jitter"],
        "novelty_min": bt.params["novelty_min"],
    })
    print(f"★ autotune → {tuned} | n_new={bt.user_attrs.get('n_new')}")
    return tuned

def cycle_once(st: dict, patience: int=2, min_improve: float=1e-4) -> dict:
    ensure_inventory()
    champ = load_champion()
    base = st.get("params") or {"mode":"auto","top":60, "pop":16, "gen":2, "jitter":0.001, "novelty_min":0.01}

    snap = list_worm_files()
    # 1) exploração/exploração: autotune local
    params = autotune_once(base)
    # 2) executa com params escolhidos
    before = list_worm_files()
    run_smart(params)
    new = new_worms_since(before)
    mscore, mnov, n = stats_from_files(new)
    print(f"   ciclo: novos={n} | mean_score={mscore:.5f} | mean_novelty={mnov:.6f}")

    st["cycle"] = int(st.get("cycle",0)) + 1
    st["history"].append([st["cycle"], int(n), float(mscore), float(mnov)])
    st["params"] = params
    st["last_seen"] = list(set(snap + new))[:20000]  # truncagem simples

    # 3) melhoria? -> atualiza campeão
    improved = (mscore > champ.get("best_score", -1e9) + min_improve)
    if improved:
        champ = {"best_score": float(mscore), "params": params, "ts": time.time()}
        save_champion(champ)
        print(f"✓ novo campeão: score={mscore:.5f} → {champ['params']}")
    else:
        # 4) sem melhora: escala entropia de forma segura (aumenta jitter levemente)
        params["jitter"] = min(params["jitter"]*1.618, 0.01)
        st["params"] = params
        print(f"↻ sem melhora; escala jitter p/ {params['jitter']:.6f}")

    # 5) calibração ética (aperta thresholds com dados recentes)
    cal = auto_calibrate_policies()  # silencioso se nada mudar
    if cal:
        print(f"Σ-Guard recalibrado: {cal}")

    # 6) artefatos do ciclo
    cycdir = Path(f"fusion_results/omega_cycle_{st['cycle']:04d}")
    cycdir.mkdir(parents=True, exist_ok=True)
    (cycdir/"new_worms.txt").write_text("\n".join(new), encoding="utf-8")
    (cycdir/"cycle_summary.json").write_text(json.dumps({
        "params": params, "new": len(new), "mean_score": mscore, "mean_novelty": mnov
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    return st

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-cycles", type=int, default=-1, help="-1 = infinito")
    ap.add_argument("--sleep", type=int, default=60, help="segundos entre ciclos")
    ap.add_argument("--patience", type=int, default=2)
    ap.add_argument("--min-improve", type=float, default=1e-4)
    st = load_state()
    args = ap.parse_args()

    i=0
    while True:
        i+=1
        st = cycle_once(st, patience=args.patience, min_improve=args.min_improve)
        save_state(st)
        if args.max_cycles>0 and i>=args.max_cycles:
            break
        time.sleep(max(1, args.sleep))

if __name__=="__main__":
    main()
