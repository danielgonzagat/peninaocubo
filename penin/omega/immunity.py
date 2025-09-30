"""Imunidade Digital"""
def anomaly_score(metrics:dict)->float:
    s=0.0
    for k,v in metrics.items():
        try:
            if not (0.0 <= float(v) <= 1e6): s += 1.0
        except: s += 1.0
    return s

def guard(metrics:dict, trigger:float=1.0)->bool:
    return anomaly_score(metrics) < trigger