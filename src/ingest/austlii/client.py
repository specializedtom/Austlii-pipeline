from __future__ import annotations

import time
from dataclasses import dataclass

import httpx


@dataclass
class AustliiClient:
    timeout_seconds: float = 20.0
    max_retries: int = 3
    backoff_seconds: float = 1.5
    user_agent: str = "austlii-pipeline/0.1"

    def fetch(self, url: str) -> str:
        headers = {"User-Agent": self.user_agent}
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = httpx.get(url, timeout=self.timeout_seconds, headers=headers)
                response.raise_for_status()
                return response.text
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * attempt)
        raise RuntimeError(f"Failed to fetch {url}") from last_error
