"""
Checkpoint & Reparo
===================

Salvamento de snapshots e restauração de estado.
"""

from pathlib import Path
import time
from typing import Dict, Any, Optional

try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    import json
    HAS_ORJSON = False


SNAP = Path.home() / ".penin_omega" / "snapshots"
SNAP.mkdir(parents=True, exist_ok=True)


def save_snapshot(state: Dict[str, Any]) -> str:
    """
    Salva snapshot do estado.
    
    Args:
        state: Estado do sistema
        
    Returns:
        Path do snapshot salvo
    """
    fn = SNAP / f"snap_{int(time.time())}.json"
    
    if HAS_ORJSON:
        fn.write_bytes(orjson.dumps(state, option=orjson.OPT_INDENT_2))
    else:
        fn.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    
    return str(fn)


def restore_last() -> Optional[Dict[str, Any]]:
    """
    Restaura último snapshot.
    
    Returns:
        Estado restaurado ou None se não houver snapshots
    """
    snaps = sorted(SNAP.glob("snap_*.json"))
    
    if not snaps:
        return None
    
    last = snaps[-1]
    
    if HAS_ORJSON:
        return orjson.loads(last.read_bytes())
    else:
        return json.loads(last.read_text(encoding="utf-8"))


def restore_specific(timestamp: int) -> Optional[Dict[str, Any]]:
    """
    Restaura snapshot específico.
    
    Args:
        timestamp: Timestamp do snapshot
        
    Returns:
        Estado restaurado ou None se não encontrar
    """
    fn = SNAP / f"snap_{timestamp}.json"
    
    if not fn.exists():
        return None
    
    if HAS_ORJSON:
        return orjson.loads(fn.read_bytes())
    else:
        return json.loads(fn.read_text(encoding="utf-8"))


def list_snapshots() -> list:
    """
    Lista todos os snapshots disponíveis.
    
    Returns:
        Lista de timestamps
    """
    snaps = sorted(SNAP.glob("snap_*.json"))
    return [int(s.stem.split("_")[1]) for s in snaps]


def cleanup_old_snapshots(keep_last: int = 10) -> int:
    """
    Remove snapshots antigos, mantendo apenas os N mais recentes.
    
    Args:
        keep_last: Número de snapshots a manter
        
    Returns:
        Número de snapshots removidos
    """
    snaps = sorted(SNAP.glob("snap_*.json"))
    
    if len(snaps) <= keep_last:
        return 0
    
    to_remove = snaps[:-keep_last]
    
    for snap in to_remove:
        snap.unlink()
    
    return len(to_remove)