#!/usr/bin/env python3
"""Estime le volume de stockage en fonction du nombre d'articles par jour.

Le poste dominant n'est pas le texte : ce sont les embeddings (1024 dimensions)
et leur index HNSW. Ajuste les parametres ci-dessous si tes volumes changent.

Usage: python tools/size_estimate.py [articles_par_jour]
"""
from __future__ import annotations

import sys

# ── parametres ──────────────────────────────────────────────────────────────
ARTICLES_JOUR = 2500        # 65 flux : ordre de grandeur mesure
DIM = 1024                  # bge-m3
DTYPE = "float32"           # float32 | float16 | int8
ARTICLES_PAR_EVENT = 3      # regroupement moyen
EVENTS_ACTIFS_HEURES = 72   # au-dela, le centroide n'est plus utile
HNSW_M = 16

# ── couts unitaires (octets) ────────────────────────────────────────────────
VEC = {"float32": DIM * 4, "float16": DIM * 2, "int8": DIM + 8}[DTYPE]
INDEX = VEC + HNSW_M * 2 * 4 + 64          # pgvector HNSW : vecteur + liens

TXT_ARTICLE = 600                          # titre, extrait, URL, hashes, horodatages
RAW_ARTICLE = 1000                         # item brut, compresse par TOAST
TXT_EVENT = 1500                           # titres et syntheses dans 4 langues
VIDEO_MOIS = 130 * 1.2e6                   # 5 shorts/jour + 1 resume : ~1,2 Mo chacun


def mb(octets: float) -> str:
    return f"{octets / 1e6:,.1f}".replace(",", " ") + " Mo"


def postes(jours: float) -> list[tuple[str, float]]:
    articles = ARTICLES_JOUR * jours
    events = articles / ARTICLES_PAR_EVENT
    actifs = ARTICLES_JOUR * (EVENTS_ACTIFS_HEURES / 24) / ARTICLES_PAR_EVENT
    archives = max(0.0, events - actifs)
    return [
        ("Articles : texte et metadonnees", articles * TXT_ARTICLE),
        ("Articles : reponse brute du flux", articles * RAW_ARTICLE),
        ("Articles : embeddings", articles * VEC),
        ("Articles : index HNSW", articles * INDEX),
        ("Evenements : titres et syntheses", events * TXT_EVENT),
        ("Evenements : centroides actifs", actifs * (VEC + INDEX)),
        ("Videos", VIDEO_MOIS * jours / 30),
    ]


def main() -> None:
    global ARTICLES_JOUR
    if len(sys.argv) > 1:
        ARTICLES_JOUR = int(sys.argv[1])

    print(f"{ARTICLES_JOUR} articles/jour · {DIM} dim · {DTYPE} · "
          f"{ARTICLES_PAR_EVENT} articles par evenement\n")

    header = f"{'Poste':<38}{'1 jour':>12}{'1 semaine':>13}{'1 an':>12}"
    print(header)
    print("-" * len(header))

    total_semaine = 0.0
    totaux = {}
    for nom, _ in postes(1):
        totaux[nom] = 0.0

    for nom, _ in postes(1):
        pass

    lignes = {}
    for jours in (1, 7, 365):
        for nom, val in postes(jours):
            lignes.setdefault(nom, {})[jours] = val
            if jours == 7:
                total_semaine += val

    for nom, vals in lignes.items():
        print(f"{nom:<38}{mb(vals[1]):>12}{mb(vals[7]):>13}{mb(vals[365]):>12}")

    print("-" * len(header))
    total_an = sum(v[365] for v in lignes.values())
    print(f"{'TOTAL':<38}{mb(sum(v[1] for v in lignes.values())):>12}"
          f"{mb(total_semaine):>13}{mb(total_an):>12}")

    part_vec = sum(v[7] for k, v in lignes.items() if "embedding" in k or "HNSW" in k or "centroide" in k)
    print(f"\nPart des vecteurs dans la semaine : {100 * part_vec / total_semaine:.0f} %")

    print("\nAvec des vecteurs en halfvec (float16), le total hebdomadaire passe a environ "
          f"{mb(total_semaine - 0.5 * part_vec)}.")
    print(f"Prevoir 1,5x pour les index, le WAL et les sauvegardes : "
          f"{mb(total_semaine * 1.5)} par semaine, {mb(total_an * 1.5)} par an.")


if __name__ == "__main__":
    main()
