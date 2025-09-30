from typing import Any

from penin.ingest.hf_ingestor import hf_search
from penin.ingest.kaggle_ingestor import kaggle_search_datasets


async def execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "kaggle_search":
        return await kaggle_search_datasets(args["query"], args.get("max_results", 10))
    if name == "hf_search":
        return await hf_search(args["query"], args.get("limit", 10))
    raise ValueError(f"Tool '{name}' not registered")
