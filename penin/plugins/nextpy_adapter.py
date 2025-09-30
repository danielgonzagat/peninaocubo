from typing import Dict, Any


def propose_with_nextpy(prompt: str) -> Dict[str, Any]:
    try:
        import nextpy  # type: ignore  # noqa: F401
    except Exception as e:
        raise ImportError(
            "NextPy not installed. Install with `pip install nextpy` or skip this plugin."
        ) from e

    diff = f"# NextPy AMS Patch\n# Prompt:\n{prompt}\n# TODO: generate real patch via NextPy APIs."
    return {"diff": diff, "expected_gain": 0.02, "cost": 1.0}

