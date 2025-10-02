from typing import Any


def propose_with_nextpy(prompt: str) -> dict[str, Any]:
    try:
        pass  # type: ignore
    except Exception as e:
        raise ImportError(
            "NextPy não instalado. Instale com `pip install nextpy` ou desative este plugin."
        ) from e

    diff = f"# NextPy AMS Patch\n# Prompt:\n{prompt}\n# TODO: gerar patch real via API NextPy."
    return {"diff": diff, "expected_gain": 0.02, "cost": 1.0}
