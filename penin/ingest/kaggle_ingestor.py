import asyncio
from typing import Dict, Any


async def kaggle_search_datasets(query: str, max_results: int = 10) -> Dict[str, Any]:
    cmd = [
        "kaggle",
        "datasets",
        "list",
        "-s",
        query,
        "-v",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    return {"stdout": out.decode(), "stderr": err.decode(), "code": proc.returncode}

