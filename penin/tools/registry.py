import asyncio
from typing import Dict, Any
from penin.ingest.kaggle_ingestor import kaggle_search_datasets
from penin.ingest.hf_ingestor import hf_search


async def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "kaggle_search":
        return await kaggle_search_datasets(args["query"], args.get("max_results", 10))
    if name == "hf_search":
        return await hf_search(args["query"], args.get("limit", 10))
    raise ValueError(f"Tool '{name}' not registered")
