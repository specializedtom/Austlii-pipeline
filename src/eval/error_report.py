from __future__ import annotations

from collections import Counter


def summarize_errors(items: list[dict], key: str = "error_type") -> dict[str, int]:
    return dict(Counter(item.get(key, "unknown") for item in items))
