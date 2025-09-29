KAGGLE_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "kaggle_search",
        "description": "Search Kaggle datasets by query string.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "search phrase"},
                "max_results": {"type": "integer", "description": "1..50"},
            },
            "required": ["query"],
        },
    },
}

HF_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "hf_search",
        "description": "Search Hugging Face models/datasets by query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "search phrase"},
                "limit": {"type": "integer", "description": "max number of results"},
            },
            "required": ["query"],
        },
    },
}
