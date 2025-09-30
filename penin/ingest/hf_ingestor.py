from typing import Any

from huggingface_hub import HfApi

from penin.config import settings

api = HfApi(token=settings.HUGGINGFACE_TOKEN)


async def hf_search(query: str, limit: int = 10) -> dict[str, Any]:
    models = api.list_models(search=query, limit=limit)
    data = [{"id": m.id, "likes": m.likes, "downloads": m.downloads} for m in models]
    return {"results": data}
