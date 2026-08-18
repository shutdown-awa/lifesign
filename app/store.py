"""Thread-safe in-memory store for the latest status snapshot.

Not persisted — on restart the store is empty until the next ingest.
"""

from __future__ import annotations

import threading
from typing import Any, Optional

_lock = threading.Lock()
_store: dict[str, Any] = {}


def put(payload: dict[str, Any]) -> None:
    """Replace the entire stored snapshot with *payload*."""
    with _lock:
        _store.clear()
        _store.update(payload)


def get_all() -> dict[str, Any]:
    """Return a shallow copy of the entire store."""
    with _lock:
        return dict(_store)


def get_fields(paths: list[str]) -> dict[str, Any]:
    """Return a subset dictated by dot-separated *paths*.

    Example paths:
        ["device_stage.battery", "health.body.heart_beat"]
    """
    with _lock:
        result: dict[str, Any] = {}
        for path in paths:
            if not path:
                continue
            parts = path.split(".")
            node: Any = _store
            for part in parts:
                if isinstance(node, dict):
                    node = node.get(part)
                else:
                    node = None
                    break
            if node is not None:
                _set_nested(result, parts, node)
        return result


def _set_nested(d: dict[str, Any], parts: list[str], value: Any) -> None:
    """Write *value* at the dotted path inside *d*, creating nested dicts."""
    for part in parts[:-1]:
        d = d.setdefault(part, {})
    d[parts[-1]] = value