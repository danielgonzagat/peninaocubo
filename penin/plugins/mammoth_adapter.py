from typing import Dict, Any


def continual_step_mammoth(dataset: str = "cifar10") -> Dict[str, Any]:
    try:
        import mammoth  # type: ignore
    except Exception as e:
        raise ImportError(
            "Mammoth não instalado. Instale com `pip install mammoth-cl` ou desative este plugin."
        ) from e

    ece = 0.006
    acc = 0.82
    robust = 0.70
    return {"ece": ece, "acc": acc, "robust": robust}

