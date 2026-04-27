from __future__ import annotations

import re
from html import unescape
from typing import Any
from urllib.parse import quote


JURISDICTIONS = {
    "Cth": "Commonwealth",
    "ACT": "Australian Capital Territory",
    "NSW": "New South Wales",
    "NT": "Northern Territory",
    "Qld": "Queensland",
    "SA": "South Australia",
    "Tas": "Tasmania",
    "Vic": "Victoria",
    "WA": "Western Australia",
}

LEGISLATION_RE = re.compile(
    r"\b(?:the\s+)?([A-Z][a-zA-Z0-9\.\-'&]+(?:\s+[a-zA-Z0-9\.\-'&]+)*?\s+(?:Act|Regulations?|Rules?|Bill|Order|Ordinance|Code|Statute))\s+"
    r"((?:\(No\s+\d+\)\s+)?\d{4}(?:-\d{2,4})?)(?:\s*\(("
    + "|".join(JURISDICTIONS.keys())
    + r")\))?",
    re.IGNORECASE,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.austlii.edu.au/forms/search1.html",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}


def clean_title(raw_title: str) -> str:
    noise_patterns = [
        r"^Mentions\s+",
        r"^References\s+",
        r"^and\s+",
        r"^or\s+",
        r"^the\s+",
        r"^section\s+\d+\s+of\s+",
        r"^of\s+",
        r"^under\s+",
        r"^in\s+",
        r"^for\s+",
    ]
    title = raw_title
    for pattern in noise_patterns:
        title = re.sub(pattern, "", title, flags=re.IGNORECASE)
    return title.strip()


def extract_legislation_citations(text: str, limit: int = 5) -> list[dict[str, str | None]]:
    seen: set[str] = set()
    results: list[dict[str, str | None]] = []

    for match in LEGISLATION_RE.finditer(text):
        title = clean_title(match.group(1).strip())
        year = match.group(2)
        jurisdiction = match.group(3) if match.group(3) else None

        key = f"{title}|{year}|{jurisdiction or ''}"
        if key in seen:
            continue
        seen.add(key)

        results.append(
            {
                "citation": f"{title} {year}" + (f" ({jurisdiction})" if jurisdiction else ""),
                "title": title,
                "year": year,
                "jurisdiction": jurisdiction,
            }
        )
        if len(results) >= limit:
            break

    return results


def austlii_legislation_search(
    legislation_name: str,
    year: str | None = None,
    jurisdiction: str | None = None,
    max_results: int = 3,
) -> dict[str, Any]:
    search_terms = legislation_name + (f" {year}" if year else "")
    query_string = (
        f"query={quote(search_terms)}"
        f";method=title"
        f";results={max_results}"
        f";meta={quote('/au')}"
        f";mask_path="
    )
    url = f"https://www.austlii.edu.au/cgi-bin/sinosrch.cgi?{query_string}"

    try:
        import httpx
        from bs4 import BeautifulSoup

        response = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for card in soup.select("div.card"):
            for li in card.select("li.multi"):
                anchor = li.find("a")
                if not anchor:
                    continue

                title = unescape(anchor.get_text(strip=True))
                link = unescape(anchor.get("href", ""))
                if not link:
                    continue
                if "?" in link:
                    link = link.split("?", 1)[0]
                if not link.startswith("http"):
                    link = "https://www.austlii.edu.au" + link

                if "/legis/" not in link.lower():
                    continue

                meta_tag = li.find("p", class_="meta")
                meta_text = meta_tag.get_text(strip=True) if meta_tag else ""

                return {
                    "found": True,
                    "title": title,
                    "url": link,
                    "meta": meta_text,
                    "jurisdiction": jurisdiction,
                }

        return {"found": False, "query": search_terms}
    except httpx.TimeoutException:
        return {"found": False, "query": search_terms, "error": "Request timed out"}
    except httpx.HTTPStatusError as exc:
        return {
            "found": False,
            "query": search_terms,
            "error": f"HTTP {exc.response.status_code}: {str(exc)}",
        }
    except Exception as exc:  # noqa: BLE001
        return {"found": False, "query": search_terms, "error": str(exc)}


def verify_text_citations(text: str, limit: int = 5) -> dict[str, Any]:
    citations = extract_legislation_citations(text, limit=limit)
    verified: list[dict[str, Any]] = []
    unverified: list[dict[str, Any]] = []

    for item in citations:
        result = austlii_legislation_search(item["title"] or "", item["year"], item["jurisdiction"])
        payload = {**item, "result": result}
        if result.get("found"):
            verified.append(payload)
        else:
            unverified.append(payload)

    return {
        "citations_found": len(citations),
        "verified": verified,
        "unverified": unverified,
    }
