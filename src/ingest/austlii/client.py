from __future__ import annotations

import time
from dataclasses import dataclass, field

import httpx


@dataclass
class AustliiClient:
    timeout_seconds: float = 20.0
    max_retries: int = 3
    backoff_seconds: float = 1.5
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    extra_headers: dict[str, str] = field(
        default_factory=lambda: {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-AU,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
        }
    )

    def fetch(self, url: str) -> str:
        """Fetch HTML from URL with retries and 403-specific fallback behavior."""
        headers = {"User-Agent": self.user_agent, **self.extra_headers}
        last_error: Exception | None = None
        candidates = self._candidate_urls(url)

        for candidate in candidates:
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = httpx.get(
                        candidate,
                        timeout=self.timeout_seconds,
                        headers=headers,
                        follow_redirects=True,
                    )
                    response.raise_for_status()
                    return response.text
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    if exc.response.status_code == 403:
                        # Try the next candidate URL immediately when blocked.
                        break
                    if attempt < self.max_retries:
                        time.sleep(self.backoff_seconds * attempt)
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    if attempt < self.max_retries:
                        time.sleep(self.backoff_seconds * attempt)

        raise RuntimeError(
            f"Failed to fetch {url}. Last error: {last_error}. "
            "If you receive repeated 403 errors, try providing a local mirror/source file."
        ) from last_error

    @staticmethod
    def _candidate_urls(url: str) -> list[str]:
        """Generate common AustLII variants that can bypass simple endpoint blocking."""
        candidates = [url]
        if url.startswith("https://www.austlii.edu.au/"):
            candidates.append(url.replace("https://www.austlii.edu.au/", "https://www8.austlii.edu.au/"))
            candidates.append(url.replace("https://www.austlii.edu.au/", "http://www.austlii.edu.au/"))
        return list(dict.fromkeys(candidates))
