from typing import Dict, Any


def propose_with_nextpy(prompt: str) -> Dict[str, Any]:
    try:
        import nextpy  # type: ignore  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "NextPy não instalado. Instale com `pip install nextpy`."
        ) from e

    diff = f"# NextPy AMS Patch\n# Prompt:\n{prompt}\n# TODO: gerar patch real via NextPy."
    return {"diff": diff, "expected_gain": 0.02, "cost": 1.0}

