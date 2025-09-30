from typing import Dict, Any


def propose_with_naslib(space: str = "ResNet") -> Dict[str, Any]:
    try:
        import naslib  # type: ignore
    except Exception as e:
        raise ImportError(
            "NASLib não instalado. Instale com `pip install naslib` ou desative este plugin."
        ) from e

    arch_repr = f"NASLib::{space}::candidate_A"
    expected_gain = 0.015
    cost = 0.8
    return {"arch": arch_repr, "expected_gain": expected_gain, "cost": cost}

