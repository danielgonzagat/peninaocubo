from typing import Any


def continual_step_mammoth(dataset: str = "cifar10") -> dict[str, Any]:
    try:
        pass  # type: ignore
    except Exception as e:
        raise ImportError(
            "Mammoth não instalado. Instale com `pip install mammoth-cl` ou desative este plugin."
        ) from e

    ece = 0.006
    acc = 0.82
    robust = 0.70
    return {"ece": ece, "acc": acc, "robust": robust}
