from typing import Dict, Any


def propose_with_naslib(space: str = "ResNet") -> Dict[str, Any]:
    try:
        import naslib  # type: ignore  # noqa: F401
    except Exception as e:
        raise ImportError(
            "NASLib not installed. Install with `pip install naslib` or skip this plugin."
        ) from e

    arch_repr = f"NASLib::{space}::candidate_A"
    return {"arch": arch_repr, "expected_gain": 0.015, "cost": 0.8}

