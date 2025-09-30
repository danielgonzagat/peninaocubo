# penin/omega/checkpoint.py
"""
Checkpoint & Reparo
===================

Sistema de snapshots e restauração de estado.
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import orjson as json
except ImportError:
    import json

SNAP_PATH = Path.home() / ".penin_omega" / "snapshots"
SNAP_PATH.mkdir(parents=True, exist_ok=True)


def save_snapshot(state: Dict[str, Any], name: Optional[str] = None) -> str:
    """Salva snapshot do estado"""
    timestamp = int(time.time())
    filename = name or f"snap_{timestamp}.json"
    filepath = SNAP_PATH / filename
    
    snapshot = {
        "timestamp": timestamp,
        "state": state,
        "metadata": {
            "created_at": time.time(),
            "version": "1.0"
        }
    }
    
    if hasattr(json, 'dumps'):
        content = json.dumps(snapshot)
        if isinstance(content, bytes):
            content = content.decode('utf-8')
    else:
        content = str(snapshot)
    
    filepath.write_text(content, encoding="utf-8")
    
    return str(filepath)


def restore_last() -> Optional[Dict[str, Any]]:
    """Restaura último snapshot"""
    snapshots = sorted(SNAP_PATH.glob("snap_*.json"))
    if not snapshots:
        return None
    
    try:
        latest = snapshots[-1]
        content = latest.read_text(encoding="utf-8")
        snapshot = json.loads(content) if hasattr(json, 'loads') else eval(content)
        return snapshot.get("state")
    except Exception:
        return None


def list_snapshots() -> list:
    """Lista snapshots disponíveis"""
    snapshots = []
    for snap_file in SNAP_PATH.glob("snap_*.json"):
        try:
            content = snap_file.read_text(encoding="utf-8")
            snapshot = json.loads(content) if hasattr(json, 'loads') else eval(content)
            snapshots.append({
                "filename": snap_file.name,
                "timestamp": snapshot.get("timestamp"),
                "size_bytes": snap_file.stat().st_size
            })
        except Exception:
            continue
    
    return sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)