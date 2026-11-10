#!/usr/bin/env python3
"""Regroupement lexical des titres (TF-IDF + cosinus, glouton).

C'est le prototype du clustering, en attendant les embeddings multilingues.
Volontairement isole dans un module : le jour ou un modele entre en jeu, seule
cette fonction change, pas le poller ni le rapport.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

import numpy as np

STOP = set("""
le la les un une des du de d au aux a et ou mais donc or ni car que qui quoi dont
en dans par pour sur sous avec sans chez vers entre depuis pendant apres avant
ce cet cette ces son sa ses leur leurs il elle ils elles on nous vous je tu
est sont etait etaient ete avoir ont avait avaient plus moins tres trop
the a an and or but of to in on at for with from by as is are was were be been
this that these those it its he she they we you i not no than then
says said say after before over under about into new
""".split())

TOKEN = re.compile(r"[a-z0-9]{3,}")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return s


def tokens(s: str) -> list[str]:
    return [t for t in TOKEN.findall(norm(s)) if t not in STOP]


def matrix(titles: list[str]):
    docs = [tokens(t) for t in titles]
    df = Counter(t for d in docs for t in set(d))
    vocab = {t: i for i, t in enumerate(sorted(t for t, c in df.items() if c >= 2))}
    if not vocab:
        return None, {}
    M = np.zeros((len(titles), len(vocab)), dtype=np.float32)
    for i, doc in enumerate(docs):
        for t, c in Counter(t for t in doc if t in vocab).items():
            M[i, vocab[t]] = (1 + math.log(c)) * math.log(len(titles) / df[t])
    n = np.linalg.norm(M, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return M / n, vocab


def cluster(titles: list[str], threshold: float = 0.34) -> list[list[int]]:
    """Retourne des groupes d'indices, du plus couvert au moins couvert."""
    M, vocab = matrix(titles)
    if M is None:
        return [[i] for i in range(len(titles))]

    groups: list[list[int]] = []
    cents: list[np.ndarray] = []
    for i in range(len(titles)):
        v = M[i]
        if not cents:
            groups.append([i])
            cents.append(v.copy())
            continue
        sims = np.vstack(cents) @ v
        best = int(np.argmax(sims))
        if float(sims[best]) >= threshold:
            groups[best].append(i)
            c = (cents[best] * (len(groups[best]) - 1) + v) / len(groups[best])
            cents[best] = c / (np.linalg.norm(c) or 1.0)
        else:
            groups.append([i])
            cents.append(v.copy())
    return groups


# ── pont interlangues ───────────────────────────────────────────────────────
# Sans modele multilingue, le seul ancrage commun entre « Ueno Bank collapse in
# Paraguay » et « Bankenkrise: Paraguays Präsident Peña » est le nom propre.
# On fusionne donc les groupes qui partagent au moins deux tokens rares
# (noms propres, sigles, nombres) — c'est grossier, mais gratuit et mesurable.

RARE_DF = 40          # un token present dans plus de 40 titres n'ancre rien
NUM = re.compile(r"\b\d{3,}\b")


def signature(title: str, df: dict) -> set[str]:
    toks = [t for t in tokens(title) if len(t) >= 4 and 2 <= df.get(t, 0) <= RARE_DF]
    return set(toks) | set(NUM.findall(norm(title)))


def merge_by_signature(groups: list[list[int]], titles: list[str],
                       min_shared: int = 3, max_size: int = 25) -> list[list[int]]:
    """Union-find : deux groupes qui partagent assez de tokens rares n'en font qu'un.

    max_size est indispensable : sans plafond, quelques tokens ponts suffisent a
    chainer des centaines de groupes sans rapport (mesure : un groupe de 881
    articles sur 7 langues). Le seuil seul ne protege pas de la transitivite.
    """
    df: dict = {}
    for t in titles:
        for tok in set(tokens(t)):
            df[tok] = df.get(tok, 0) + 1
    sigs = [signature(t, df) for t in titles]

    parent = list(range(len(groups)))
    size = [len(g) for g in groups]

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    lead = [g[0] for g in groups]
    for a in range(len(groups)):
        for b in range(a + 1, len(groups)):
            ra, rb = find(a), find(b)
            if ra == rb:
                continue
            if size[ra] + size[rb] > max_size:
                continue
            if len(sigs[lead[a]] & sigs[lead[b]]) >= min_shared:
                parent[rb] = ra
                size[ra] += size[rb]

    merged: dict[int, list[int]] = {}
    for i, g in enumerate(groups):
        merged.setdefault(find(i), []).extend(g)
    return list(merged.values())
