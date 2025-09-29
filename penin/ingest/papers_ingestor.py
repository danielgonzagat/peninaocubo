import os
import glob
from typing import List


def list_pdfs(folder: str) -> List[str]:
    return glob.glob(os.path.join(folder, "*.pdf"))

