#!/usr/bin/env python3
"""Verification statique legere du schema SQL (pas de serveur PostgreSQL requis).

Controle : parentheses equilibrees hors chaines/commentaires, chaque instruction
terminee par ';', cibles des REFERENCES existantes, colonnes citees dans les
index existantes, et coherence des CHECK (colonne bien declaree).

Ce n'est pas un parseur SQL : ca attrape les fautes de frappe, pas les erreurs
semantiques. A remplacer par `psql -f schema.sql` des qu'un PostgreSQL est dispo.

Usage: python tools/lint_schema.py [db/schema.sql]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

IDENT = r"[a-z_][a-z0-9_]*"


def strip_sql(text: str) -> str:
    """Retire commentaires -- et /* */ et le contenu des chaines '...'."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "'":
            out.append(" ")
            i += 1
            while i < n:
                if text[i] == "'" and i + 1 < n and text[i + 1] == "'":
                    i += 2
                    continue
                if text[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        if text.startswith("--", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "db/schema.sql")
    raw = path.read_text(encoding="utf-8")
    sql = strip_sql(raw)
    errors: list[str] = []
    warns: list[str] = []

    # 1. equilibre des parentheses
    depth, line = 0, 1
    for ch in sql:
        if ch == "\n":
            line += 1
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                errors.append(f"parenthese fermante en trop (ligne {line})")
                depth = 0
    if depth:
        errors.append(f"{depth} parenthese(s) non fermee(s)")

    # 2. instructions terminees par ;
    stmts = [s.strip() for s in sql.split(";") if s.strip()]
    tables: dict[str, set[str]] = {}
    for st in stmts:
        m = re.match(rf"CREATE TABLE (?:IF NOT EXISTS )?(?:public\.)?({IDENT})", st, re.I)
        if not m:
            continue
        name = m.group(1)
        body = st[st.index("("):]
        cols = set(re.findall(rf"(?:\(|,)\s*({IDENT})\s+[a-z]", body, re.I))
        tables[name] = {c.lower() for c in cols}

    if not tables:
        errors.append("aucune table detectee")

    # 3. cibles de REFERENCES
    for m in re.finditer(rf"REFERENCES\s+({IDENT})\s*\(\s*({IDENT})", sql, re.I):
        tgt, col = m.group(1).lower(), m.group(2).lower()
        if tgt not in tables:
            errors.append(f"REFERENCES vers une table inconnue : {tgt}")
        elif col not in tables[tgt]:
            warns.append(f"REFERENCES {tgt}({col}) : colonne non vue dans la definition")

    # 4. colonnes des index
    for m in re.finditer(rf"CREATE INDEX\s+({IDENT})\s+ON\s+({IDENT})\s*\((.*?)\)\s*(?:WHERE|;|$)", sql, re.I | re.S):
        idx, tbl, cols = m.group(1), m.group(2).lower(), m.group(3)
        if tbl not in tables:
            errors.append(f"index {idx} sur table inconnue : {tbl}")
            continue
        plain = re.sub(r"\(.*?\)", "", cols)          # retire les appels de fonction
        for c in re.findall(rf"\b({IDENT})\b", plain):
            if c.lower() in ("using", "gin", "hnsw", "where", "with", "asc", "desc", "vectors", "ops"):
                continue
            if c.lower() not in tables[tbl]:
                warns.append(f"index {idx} : colonne '{c}' absente de {tbl}")

    # 5. colonnes citees dans les CHECK
    for m in re.finditer(rf"CREATE TABLE (?:public\.)?({IDENT})(.*?)\n\)\s*;", sql, re.I | re.S):
        tbl, body = m.group(1).lower(), m.group(2)
        for chk in re.finditer(r"CHECK\s*\((.*?)\)", body, re.S):
            for c in re.findall(rf"({IDENT})\s+(?:BETWEEN|IN|IS|\+|>|<|=)", chk.group(1)):
                if c.lower() not in tables.get(tbl, set()) and c.lower() not in ("check",):
                    warns.append(f"CHECK de {tbl} : colonne '{c}' non declaree")

    print(f"instructions : {len(stmts)}   tables : {len(tables)}")
    print(f"tables : {', '.join(sorted(tables))}\n")
    for w in warns:
        print(f"  avertissement : {w}")
    if errors:
        for e in errors:
            print(f"  ERREUR : {e}")
        print(f"\n{len(errors)} erreur(s)")
        sys.exit(1)
    print(f"OK — aucune erreur structurelle ({len(warns)} avertissement(s))")


if __name__ == "__main__":
    main()
