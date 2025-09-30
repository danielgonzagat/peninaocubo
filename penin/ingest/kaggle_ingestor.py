import asyncio
import re
import re as _re
from typing import Any

SAFE_QUERY_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,-]+$")


async def kaggle_search_datasets(query: str, max_results: int = 10) -> dict[str, Any]:
    if not query or not SAFE_QUERY_PATTERN.fullmatch(query):
        return {"error": "Invalid query format", "code": 1}

    try:
        limit = int(max_results)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 50))

    cmd = [
        "kaggle",
        "datasets",
        "list",
        "-s",
        query,
        "-v",
        "--page-size",
        str(limit),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, err = await proc.communicate()
        return {"stdout": out.decode(), "stderr": err.decode(), "code": proc.returncode}
    except Exception as e:
        return {"error": str(e), "code": 1}


# --- Safe query guard (added by fix/kaggle-safe-query) ---

# Formatos aceitos: "owner/dataset" ou "dataset" (letras, números, ponto, underscore e hífen)
SAFE_QUERY_PATTERN = _re.compile(r"^[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)?$")


def is_safe_kaggle_query(q: str) -> bool:
    """True se a consulta Kaggle for segura (sem espaços, sem '../', sem caracteres estranhos)."""
    if q is None:
        return False
    return bool(SAFE_QUERY_PATTERN.fullmatch(q))


__all__ = ["SAFE_QUERY_PATTERN", "is_safe_kaggle_query"]
