import datetime
from pathlib import Path


def update_readme():
    now = datetime.datetime.utcnow().isoformat() + "Z"
    txt = [
        "# PENIN-Ω — VIDA+",
        f"_Gerado em {now}_",
        "",
        "## Equação de Vida (+) — Gate não-compensatório",
        "- Implementada em `penin/omega/life_eq.py`.",
        "- Hook automático via `sitecustomize.py` (ligue com `PENIN_ENABLE_VIDA_HOOK=1`).",
        "- Fail-closed real: se qualquer critério falhar, promoção é bloqueada.",
        "",
        "## Próximos passos (roadmap curto)",
        "1. Fractal DSL + propagate core.",
        "2. Swarm heartbeat → G global.",
        "3. Marketplace cognitivo (Ω-tokens).",
        "4. Neural-Chain com co-assinatura (swarm).",
        "5. Self-RAG com FAISS/HNSW + reranker leve.",
        "6. API metabolizer → distillation por endpoint.",
        "7. NAS online + Continual Learning (Mammoth/zero-cost) com VIDA+.",
    ]
    Path("README_AUTO.md").write_text("\n".join(txt), encoding="utf-8")
