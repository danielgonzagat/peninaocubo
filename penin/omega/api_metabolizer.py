"""API Metabolizer - I/O Recorder + Replayer"""
import orjson, time
from pathlib import Path

LOG = Path.home()/".penin_omega"/"knowledge"/"api_io.jsonl"
LOG.parent.mkdir(parents=True, exist_ok=True)

def record_call(provider:str, endpoint:str, req:dict, resp:dict):
    item={"t":time.time(),"p":provider,"e":endpoint,"req":req,"resp":resp}
    LOG.open("ab").write(orjson.dumps(item)+b"\n")

def suggest_replay(prompt:str)->dict:
    best=None; best_len=10**9
    if not LOG.exists(): return {"note":"no-data"}
    for line in LOG.open("rb"):
        it=orjson.loads(line)
        if it["p"]=="openai" and isinstance(it["req"].get("prompt"), str):
            diff = abs(len(it["req"]["prompt"])-len(prompt))
            if diff<best_len: best_len, best = diff, it
    return best["resp"] if best else {"note":"no-similar-found"}