import time
from pathlib import Path
from typing import Any

import orjson

LOG = Path.home() / ".penin_omega" / "knowledge" / "api_io.jsonl"
LOG.parent.mkdir(parents=True, exist_ok=True)


def record_call(
    provider: str, endpoint: str, req: dict[str, Any], resp: dict[str, Any]
) -> None:
    item = {"t": time.time(), "p": provider, "e": endpoint, "req": req, "resp": resp}
    with LOG.open("ab") as f:
        f.write(orjson.dumps(item) + b"\n")


def suggest_replay(prompt: str) -> dict[str, Any]:
    best = None
    best_len = 10**12
    if not LOG.exists():
        return {"note": "no-log"}
    with LOG.open("rb") as f:
        for line in f:
            it = orjson.loads(line)
            try:
                reqp = it.get("req", {}).get("prompt")
            except Exception:
                reqp = None
            if isinstance(reqp, str):
                diff = abs(len(reqp) - len(prompt))
                if diff < best_len:
                    best_len = diff
                    best = it
    return (
        best.get("resp", {"note": "no-similar-found"})
        if best
        else {"note": "no-similar-found"}
    )


def get_provider_stats(provider: str | None = None) -> dict[str, Any]:
    """
    Get statistics about API provider usage.

    Args:
        provider: Optional provider name to filter stats (e.g., "openai", "anthropic")

    Returns:
        Dict with stats: total_calls, providers, recent_calls, etc.
    """
    if not LOG.exists():
        return {
            "total_calls": 0,
            "providers": {},
            "note": "no-log",
        }

    stats = {
        "total_calls": 0,
        "providers": {},
        "recent_calls": [],
    }

    try:
        with LOG.open("rb") as f:
            for line in f:
                try:
                    it = orjson.loads(line)
                    p = it.get("p", "unknown")

                    # Filter by provider if specified
                    if provider and p != provider:
                        continue

                    stats["total_calls"] += 1

                    if p not in stats["providers"]:
                        stats["providers"][p] = {
                            "calls": 0,
                            "endpoints": set(),
                            "first_call": it.get("t"),
                            "last_call": it.get("t"),
                        }

                    stats["providers"][p]["calls"] += 1
                    stats["providers"][p]["last_call"] = it.get("t")

                    endpoint = it.get("e")
                    if endpoint:
                        stats["providers"][p]["endpoints"].add(endpoint)

                    # Keep last 10 calls
                    if len(stats["recent_calls"]) < 10:
                        stats["recent_calls"].append(
                            {
                                "provider": p,
                                "endpoint": endpoint,
                                "timestamp": it.get("t"),
                            }
                        )

                except orjson.JSONDecodeError:
                    # Skip malformed JSON lines
                    continue
                except Exception as e:
                    # Log unexpected errors but continue processing
                    print(f"Warning: Error processing log line: {e}")
                    continue

    except OSError as e:
        return {
            "total_calls": 0,
            "providers": {},
            "error": f"Failed to read log file: {e}",
        }

    # Convert sets to lists for JSON serialization
    for p in stats["providers"]:
        stats["providers"][p]["endpoints"] = list(stats["providers"][p]["endpoints"])

    return stats
