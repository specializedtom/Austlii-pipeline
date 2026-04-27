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
    title = raw_title.strip()
    for pattern in noise_patterns:
        title = re.sub(pattern, "", title, flags=re.IGNORECASE)
    title = re.sub(r"^(?:the)\s+", "", title, flags=re.IGNORECASE)
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


def _fallback_legislation_lookup(
    legislation_name: str,
    year: str | None = None,
    jurisdiction: str | None = None,
    max_docs: int = 200,
) -> dict[str, Any]:
    """Fallback verifier when sinosrch endpoint is blocked (e.g. 403)."""
    try:
        from urllib.parse import urljoin

        from bs4 import BeautifulSoup
        from src.ingest.austlii.client import AustliiClient
        from src.ingest.austlii.parse import parse_html
    except Exception as exc:  # noqa: BLE001
        return {"found": False, "error": f"fallback unavailable: {exc}"}

    code = (jurisdiction or "Cth").lower()
    code = {"qld": "qld", "vic": "vic", "tas": "tas", "cth": "cth", "nsw": "nsw", "nt": "nt", "wa": "wa", "sa": "sa", "act": "act"}.get(code, "cth")
    seed = f"https://www.austlii.edu.au/au/legis/{code}/consol_act/"

    client = AustliiClient()
    try:
        index_html = client.fetch(seed)
    except Exception as exc:  # noqa: BLE001
        return {"found": False, "error": f"fallback index fetch failed: {exc}"}

    soup = BeautifulSoup(index_html, "html.parser")
    candidates: list[str] = []
    for anchor in soup.select("a[href]"):
        href = (anchor.get("href") or "").strip()
        if not href:
            continue
        link = urljoin(seed, href)
        if f"/{code}/consol_act/" in link.lower():
            candidates.append(link)
        if len(candidates) >= max_docs:
            break

    query_title = legislation_name.lower().strip()
    query_year = (year or "").strip()

    for url in candidates:
        try:
            html = client.fetch(url)
            parsed = parse_html(html)
            title_text = parsed.get("title", "")
            title_lower = title_text.lower()
            if query_title not in title_lower:
                continue
            if query_year and query_year not in title_text:
                continue
            return {
                "found": True,
                "title": title_text,
                "url": url,
                "meta": "fallback-live-lookup",
                "jurisdiction": code.upper() if code != "cth" else "Cth",
            }
        except Exception:
            continue

    return {
        "found": False,
        "query": f"{legislation_name} {year or ''}".strip(),
        "error": "No matching legislation found via fallback live lookup",
    }


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
        from bs4 import BeautifulSoup
        from src.ingest.austlii.client import AustliiClient

        client = AustliiClient()
        html = client.fetch(url)

        soup = BeautifulSoup(html, "html.parser")
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

        return _fallback_legislation_lookup(legislation_name, year, jurisdiction)
    except Exception as exc:  # noqa: BLE001
        fallback = _fallback_legislation_lookup(legislation_name, year, jurisdiction)
        if fallback.get("found"):
            return fallback
        return {"found": False, "query": search_terms, "error": str(exc)}


def verify_text_citations(text: str, limit: int = 5, default_jurisdiction: str | None = None) -> dict[str, Any]:
    citations = extract_legislation_citations(text, limit=limit)
    verified: list[dict[str, Any]] = []
    unverified: list[dict[str, Any]] = []

    for item in citations:
        jurisdiction = item["jurisdiction"] or default_jurisdiction
        result = austlii_legislation_search(item["title"] or "", item["year"], jurisdiction)
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
