from __future__ import annotations

from bs4 import BeautifulSoup


def parse_html(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.text if soup.title else "").strip()
    body_text = soup.get_text("\n", strip=True)
    return {
        "title": title,
        "text": body_text,
    }
