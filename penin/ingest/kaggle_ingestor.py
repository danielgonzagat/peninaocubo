import asyncio
import re
from typing import Any, Dict


# Allow common dataset queries that include spaces, slashes, commas, periods and dashes
# while continuing to block attempts to traverse directories (".." sequences).
SAFE_QUERY_PATTERN = re.compile(r"^(?!.*\.\.)[a-zA-Z0-9\s./,-]+$")


async def kaggle_search_datasets(query: str, max_results: int = 10) -> Dict[str, Any]:
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
