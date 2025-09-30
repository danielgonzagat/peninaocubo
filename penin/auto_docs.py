from pathlib import Path
import datetime


def update_readme():
    root = Path(".")
    now = datetime.datetime.utcnow().isoformat()
    txt = f"# PENIN-Ω — Auto Docs\n\nGenerated at {now}Z\n\n- Services: 8010/8011/8012/8013 running.\n- Gates: ΔL∞≥0.01, CAOS+≥1.0, SR≥0.80, Σ-Guard allow==true.\n- Ledger: WORM + Merkle root via CLI.\n"
    (root / "README_AUTO.md").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    update_readme()

