#!/usr/bin/env python3
"""Tag des pays et des regions a partir des titres (gazetteer Natural Earth).

Le champ `region` d'un article est aujourd'hui celui du FLUX : un sujet asiatique
publie par la BBC tombe dans « Monde ». Ce module repare ca en cherchant les noms
de pays dans le titre, dans les sept langues de publication — Natural Earth
fournit NAME_AR, NAME_DE, NAME_EN, NAME_ES, NAME_FR, NAME_IT, NAME_PT.

Granularite volontairement grossiere : le pays, pas la ville.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

GEO = Path("sources/geo/ne_110m_countries.geojson")
LANGS = ("FR", "EN", "ES", "DE", "IT", "PT", "AR")

# nos rubriques : continent Natural Earth -> zone
CONTINENT = {
    "Asia": "Asie",
    "Africa": "Afrique",
    "Europe": "Europe",
    "North America": "Amerique du Nord",
    "South America": "Amerique du Sud",
    "Oceania": "Oceanie",
}

# le Maghreb est une sous-region, pas un continent : on le definit par pays
MAGHREB = {"MA", "DZ", "TN", "LY", "MR"}
# le Moyen-Orient = Asie de l'Ouest, plus l'Egypte
MIDDLE_EAST = {"EG"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", s).strip()


class Gazetteer:
    def __init__(self) -> None:
        data = json.loads(GEO.read_text(encoding="utf-8"))
        self.by_name: dict[str, dict] = {}
        for f in data["features"]:
            p = f["properties"]
            iso = p.get("ISO_A2") or p.get("ADM0_A3")
            if not iso or iso == "-99":
                continue
            entry = {
                "iso": iso,
                "continent": CONTINENT.get(p.get("CONTINENT") or "", None),
                "subregion": p.get("SUBREGION") or "",
                "names": {L: p.get(f"NAME_{L}") for L in LANGS},
            }
            for L in LANGS:
                name = p.get(f"NAME_{L}")
                if not name:
                    continue
                key = norm(name)
                if len(key) < 4:
                    continue      # « US », « UK », « UE » : trop ambigus
                self.by_name.setdefault(key, entry)
        # l'alternation doit essayer les noms longs d'abord
        terms = sorted(self.by_name, key=len, reverse=True)
        self.rx = re.compile(r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b")

    def region(self, iso: str, continent: str | None, subregion: str) -> str | None:
        if iso in MAGHREB:
            return "Maghreb"
        if iso in MIDDLE_EAST or subregion == "Western Asia":
            return "Moyen-Orient"
        return continent

    def tag(self, text: str) -> list[dict]:
        found, seen = [], set()
        for m in self.rx.finditer(norm(text)):
            e = self.by_name.get(m.group(1))
            if not e or e["iso"] in seen:
                continue
            seen.add(e["iso"])
            found.append({
                "iso": e["iso"],
                "region": self.region(e["iso"], e["continent"], e["subregion"]),
                "name": e["names"]["FR"] or e["names"]["EN"],
            })
        return found


_gaz: Gazetteer | None = None


def gazetteer() -> Gazetteer:
    global _gaz
    if _gaz is None:
        _gaz = Gazetteer()
    return _gaz


if __name__ == "__main__":
    g = gazetteer()
    print(f"{len(g.by_name)} noms de pays indexés")
    for t in [
        "Mali : reprise des négociations à Bamako",
        "Le Maroc face à la menace terroriste",
        "Germany's economy slows as China exports fall",
        "El presidente de Paraguay dimite",
        "Guerra in Ucraina, nuovi colloqui",
        "ارتفاع أسعار النفط في الجزائر",
    ]:
        print(f"  {t[:52]:<54}{[(x['iso'], x['region']) for x in g.tag(t)]}")
