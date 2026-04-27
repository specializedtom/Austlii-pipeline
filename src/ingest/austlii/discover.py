from __future__ import annotations

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
