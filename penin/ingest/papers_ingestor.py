import glob
import os


def list_pdfs(folder: str) -> list[str]:
    return glob.glob(os.path.join(folder, "*.pdf"))
