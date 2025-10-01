from typing import Dict, Any, Callable

_REGISTRY: Dict[str, Callable[..., Any]] = {}

def register(name: str, factory: Callable[..., Any]) -> None:
    _REGISTRY[name] = factory

def get(name: str) -> Callable[..., Any]:
    return _REGISTRY[name]

# Registrar o híbrido sem hard-fail
try:
    from penin.integrations.evolution import neuroevo_evox_ray as _hyb
    register("neuroevo_evox_ray", _hyb.instantiate)
except Exception:
    pass
