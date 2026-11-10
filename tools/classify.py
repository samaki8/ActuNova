#!/usr/bin/env python3
"""Classement des articles par theme, par regles lexicales.

On mesure d'abord la couverture : si 60 % des articles restent sans theme, ce
n'est pas la peine de construire les pages de rubrique. Les regles suffisent
pour trancher vite ; un classifieur zero-shot viendra pour les cas ambigus.

    python tools/classify.py            # mesure sur la base
    python tools/classify.py --apply    # ecrit la colonne topic
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, "tools")
import cluster as cl  # noqa: E402

DB = Path("data/news.db")

# Les mots-cles sont compares en forme normalisee (sans accents, minuscules).
# FR et EN portent l'essentiel du volume ; les autres langues completes au fil
# de l'eau, mais le mecanisme est identique.
RULES: dict[str, list[str]] = {
    "economie": [
        "economie", "inflation", "bourse", "pib", "budget", "banque", "bancaire",
        "euro", "taux", "chomage", "croissance", "fiscal", "impot", "commerce",
        "economy", "market", "growth", "banking", "trade", "tariff", "stocks",
        "wirtschaft", "inflacion", "economia", "banca", "economia",
    ],
    "sciences": [
        "science", "recherche", "etude", "chercheurs", "nasa", "espace", "fusee",
        "decouverte", "physique", "biologie", "adn", "fossile", "telescope",
        "research", "study", "scientists", "space", "discovery", "genome",
        "wissenschaft", "forschung", "ciencia", "investigacion", "scienza",
    ],
    "tech": [
        "informatique", "numerique", "intelligence artificielle", "logiciel",
        "cyber", "hacker", "google", "apple", "openai", "microsoft", "algorithme",
        "smartphone", "donnees personnelles", "tech", "software", "ai", "chip",
        "semiconductor", "kuenstliche intelligenz", "inteligencia artificial",
        "intelligenza artificiale", "technologie",
    ],
    "environnement": [
        "climat", "climatique", "rechauffement", "carbone", "pollution", "energie",
        "biodiversite", "cop31", "cop30", "secheresse", "inondation", "ecologie",
        "climate", "emissions", "carbon", "renewable", "biodiversity", "flood",
        "klima", "clima", "ambiente", "energia",
    ],
    "sport": [
        "football", "match", "coupe", "ligue", "championnat", "tennis", "rugby",
        "olympique", "jo ", "mondial", "transfert", "entraineur", "buts",
        "sport", "league", "cup", "coach", "fifa", "uefa", "nba", "formule 1",
        "fussball", "futbol", "calcio", "partita",
    ],
    "culture": [
        "cinema", "film", "musique", "album", "livre", "roman", "exposition",
        "festival", "serie", "acteur", "actrice", "peinture", "theatre",
        "movie", "music", "book", "novel", "exhibition", "actor", "award",
        "kino", "musik", "pelicula", "musica", "film",
    ],
    "sante": [
        "sante", "hopital", "vaccin", "maladie", "epidemie", "medecine", "cancer",
        "medicament", "grippe", "sante publique", "health", "hospital", "vaccine",
        "disease", "outbreak", "who", "medizin", "salud", "salute", "malattia",
    ],
    "societe": [
        "education", "ecole", "universite", "logement", "immigration", "police",
        "greve", "manifestation", "femmes", "famille", "religion", "justice",
        "society", "school", "housing", "protest", "strike", "court", "women",
        "gesellschaft", "sociedad", "societa", "scuola",
    ],
    "politique": [
        "election", "gouvernement", "president", "ministre", "parlement", "vote",
        "senat", "assemblee", "premier ministre", "midterms", "coalition",
        "election", "government", "minister", "parliament", "senate", "vote",
        "regierung", "wahl", "gobierno", "elecciones", "governo", "elezioni",
    ],
}

PRIORITY = ["tech", "sciences", "environnement", "sante", "economie",
            "politique", "sport", "culture", "societe"]


def score(title: str, words: list[str]) -> int:
    t = " " + cl.norm(title) + " "
    return sum(1 for w in words if f" {cl.norm(w)}" in t)


def best_topic(title: str) -> tuple[str | None, int]:
    scores = {k: score(title, v) for k, v in RULES.items()}
    top = max(scores.values())
    if top == 0:
        return None, 0
    for slug in PRIORITY:
        if scores[slug] == top:
            return slug, top
    return None, 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--hours", type=int, default=72)
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cols = {r[1] for r in con.execute("PRAGMA table_info(articles)")}
    if "topic" not in cols:
        con.execute("ALTER TABLE articles ADD COLUMN topic TEXT")
        con.commit()

    since = (datetime.now(timezone.utc) - timedelta(hours=args.hours)).isoformat()
    rows = con.execute("SELECT id, title FROM articles WHERE published_at >= ?",
                       (since,)).fetchall()

    counts: Counter = Counter()
    assigned: Counter = Counter()
    updates = []
    for r in rows:
        slug, sc = best_topic(r["title"])
        counts["total"] += 1
        if slug:
            assigned[slug] += 1
            counts["classés"] += 1
            updates.append((slug, r["id"]))
        else:
            counts["sans thème"] += 1

    total = counts["total"]
    print(f"{total} articles sur {args.hours} h")
    print(f"classés : {counts['classés']} ({100 * counts['classés'] / total:.0f} %), "
          f"sans thème : {counts['sans thème']}")
    print("\nrépartition :")
    for slug, n in assigned.most_common():
        print(f"  {slug:<14}{n:>5}  ({100 * n / total:.1f} %)")

    if args.apply:
        con.executemany("UPDATE articles SET topic = ? WHERE id = ?", updates)
        con.commit()
        print(f"\n{len(updates)} articles étiquetés en base")


if __name__ == "__main__":
    main()
