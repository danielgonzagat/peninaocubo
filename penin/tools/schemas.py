# Example tool schema compatible with OpenAI/Anthropic style; for DeepSeek strict

KAGGLE_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "kaggle_search",
        "description": "Search Kaggle datasets by query string.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "search phrase"},
                "max_results": {
                    "type": "integer",
                    "description": "1..50",
                    "minimum": 1,
                    "maximum": 50,
                },
            },
            "required": ["query"],
        },
    },
}

