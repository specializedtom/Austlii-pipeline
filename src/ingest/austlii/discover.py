from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.ingest.austlii.client import AustliiClient
from src.models.legislation import Jurisdiction


SEED_INDEXES: dict[Jurisdiction, list[str]] = {
    Jurisdiction.CTH: ["https://www.austlii.edu.au/au/legis/cth/consol_act/"],
    Jurisdiction.NSW: ["https://www.austlii.edu.au/au/legis/nsw/consol_act/"],
    Jurisdiction.VIC: ["https://www.austlii.edu.au/au/legis/vic/consol_act/"],
    Jurisdiction.QLD: ["https://www.austlii.edu.au/au/legis/qld/consol_act/"],
    Jurisdiction.WA: ["https://www.austlii.edu.au/au/legis/wa/consol_act/"],
    Jurisdiction.SA: ["https://www.austlii.edu.au/au/legis/sa/consol_act/"],
    Jurisdiction.TAS: ["https://www.austlii.edu.au/au/legis/tas/consol_act/"],
    Jurisdiction.ACT: ["https://www.austlii.edu.au/au/legis/act/consol_act/"],
    Jurisdiction.NT: ["https://www.austlii.edu.au/au/legis/nt/consol_act/"],
}


def discover_seed_urls(jurisdiction: Jurisdiction) -> list[str]:
    return SEED_INDEXES.get(jurisdiction, [])


def discover_legislation_urls(
    jurisdiction: Jurisdiction,
    client: AustliiClient,
    max_docs: int = 100,
) -> list[str]:
    """Discover legislation document URLs from AustLII consolidated index pages."""
    discovered: list[str] = []

    for seed in discover_seed_urls(jurisdiction):
        html = client.fetch(seed)
        soup = BeautifulSoup(html, "html.parser")

        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "").strip()
            if not href or href.startswith("#"):
                continue

            candidate = urljoin(seed, href)

            # Keep links inside the same consolidated acts tree.
            if f"/{jurisdiction.value.lower()}/consol_act/" not in candidate.lower():
                continue

            if candidate.endswith("/") or candidate.endswith(".html"):
                discovered.append(candidate)

            if len(discovered) >= max_docs:
                return list(dict.fromkeys(discovered))

    return list(dict.fromkeys(discovered))
