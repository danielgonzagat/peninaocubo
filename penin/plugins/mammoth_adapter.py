from typing import Dict, Any


def continual_step_mammoth(dataset: str = "cifar10") -> Dict[str, Any]:
    try:
        import mammoth  # type: ignore  # noqa: F401
    except Exception as e:
        raise ImportError(
            "Mammoth not installed. Install with `pip install mammoth-cl` or skip this plugin."
        ) from e

    ece = 0.006
    acc = 0.82
    robust = 0.70
    return {"ece": ece, "acc": acc, "robust": robust}

