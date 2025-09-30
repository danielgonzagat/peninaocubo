from pathlib import Path
import datetime


def update_readme():
    root = Path(".")
    now = datetime.datetime.utcnow().isoformat() + "Z"
    txt = (
        f"# PENIN-Ω — Docs Autoatualizadas\n\n_Gerado em {now}_\n\n"
        "Módulos Vida+ ativos: life_eq, fractal, swarm, kratos, market, neural_chain, self_rag, api_metabolizer, immunity, checkpoint, game, darwin_audit, zero_consciousness.\n"
    )
    (root / "README_AUTO.md").write_text(txt, encoding="utf-8")

