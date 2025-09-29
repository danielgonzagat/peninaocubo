import asyncio
from typing import Dict, Any


async def kaggle_search_datasets(query: str, max_results: int = 10) -> Dict[str, Any]:
    # Sanitize query to prevent command injection
    import re
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', query):
        return {"error": "Invalid query format", "code": 1}
    
    cmd = [
        "kaggle",
        "datasets",
        "list",
        "-s",
        query,
        "-v",
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, err = await proc.communicate()
        return {"stdout": out.decode(), "stderr": err.decode(), "code": proc.returncode}
    except Exception as e:
        return {"error": str(e), "code": 1}
