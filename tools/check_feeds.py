#!/usr/bin/env python3
"""Audite un catalogue de sources (RSS / Atom / RDF / Google News).

Sortie :
  docs/feeds-check.json        mesures brutes (statut, items, latence, format)
  docs/sources-catalogue.md    tableau lisible, groupe par region

Aucune dependance externe. Test concurrent, timeout dur, User-Agent identifiable.

Usage: python tools/check_feeds.py [sources/catalog.json]
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ATOM = "{http://www.w3.org/2005/Atom}"
DC = "{http://purl.org/dc/elements/1.1/}"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36 WorldNewsBot/0.1 (+https://example.org/bot)")
TIMEOUT = 15
WORKERS = 10


def parse(raw: bytes) -> tuple[str, int, str | None, str | None]:
    root = ET.fromstring(raw)
    tag = root.tag
    if tag == "rss" or tag.endswith("}rss"):
        fmt, items = "RSS 2.0", root.findall("./channel/item")
    elif tag.startswith(ATOM):
        fmt, items = "Atom", root.findall(f"{ATOM}entry")
    elif tag.endswith("RDF"):
        fmt, items = "RSS 1.0 (RDF)", root.findall(".//{http://purl.org/rss/1.0/}item")
    else:
        fmt, items = tag.split("}")[-1], root.findall(".//item")
    if not items:
        items = root.findall(".//item") or root.findall(f".//{ATOM}entry")

    link = None
    if items:
        first = items[0]
        for path in ("link", f"{ATOM}link", f"{DC}link"):
            node = first.find(path)
            if node is None:
                continue
            link = (node.get("href") or node.text or "").strip() or None
            if link:
                break
    return fmt, len(items), link, None


def check(entry: dict) -> dict:
    out = dict(entry, ok=False, status=None, items=0, format=None, ms=None,
               sample_link=None, error=None, note_system=None)
    if entry.get("type") == "api":
        out["error"] = "API : cle requise, non testee"
        return out

    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(entry["url"], headers={
            "User-Agent": UA,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
            "Accept-Language": "fr,en;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read(4_000_000)
            ctype = r.headers.get("Content-Type", "").split(";")[0].strip()
            out["status"] = r.status
        out["ms"] = round((time.perf_counter() - t0) * 1000)
        fmt, n, link, _ = parse(raw)
        out.update(format=f"{fmt} [{ctype}]" if ctype else fmt, items=n, sample_link=link, ok=n > 0)
        if n == 0:
            out["error"] = "XML valide mais 0 item"
        elif link and "news.google.com" in link:
            out["note_system"] = "liens de redirection Google"
    except urllib.error.HTTPError as e:
        out["ms"] = round((time.perf_counter() - t0) * 1000)
        out["status"] = e.code
        out["error"] = f"HTTP {e.code}"
    except urllib.error.URLError as e:
        out["ms"] = round((time.perf_counter() - t0) * 1000)
        reason = str(e.reason)
        if "CERTIFICATE" in reason.upper():
            out["error"] = "certificat TLS invalide"
        elif "timed out" in reason.lower():
            out["error"] = "timeout"
        else:
            out["error"] = f"reseau : {reason[:60]}"
    except ET.ParseError as e:
        out["ms"] = round((time.perf_counter() - t0) * 1000)
        out["error"] = f"XML invalide : {str(e)[:50]}"
    except Exception as e:  # noqa: BLE001
        out["ms"] = round((time.perf_counter() - t0) * 1000)
        out["error"] = f"{type(e).__name__} : {str(e)[:60]}"
    return out


def md_table(results: list[dict]) -> str:
    order = ["Europe", "Allemagne", "Italie", "Espagne", "Amerique du Nord", "Amerique du Sud",
             "Afrique", "Maghreb", "Monde arabe", "Asie", "Moyen-Orient", "Monde", "API"]
    head = ("| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |\n"
            "|---|---|---|---|---|---|---|---|")
    out = ["# Catalogue de sources — mesures réelles\n",
           "Test automatisé (`tools/check_feeds.py`), effectué le "
           + time.strftime("%d/%m/%Y à %H:%M") + ".\n",
           "« Statut » = le flux répond et contient des articles au moment du test. "
           "Un flux peut casser demain : c'est précisément pour cela que le poller "
           "surveille les flux muets et désactive automatiquement ceux qui échouent.\n",
           "> Les latences sont mesurées avec 10 requêtes en parallèle : elles sont "
           "gonflées par la concurrence et ne doivent pas servir au dimensionnement. "
           "Un poller réel interroge les flux de façon étalée.\n"]
    for region in order:
        rows = [r for r in results if r["region"] == region]
        if not rows:
            continue
        out.append(f"\n## {region}\n")
        ok = sum(1 for r in rows if r["ok"])
        out.append(f"{ok}/{len(rows)} exploitables.\n")
        out.append(head)
        for r in rows:
            statut = "OK" if r["ok"] else "**KO**"
            rem = r.get("note_system") or r.get("note") or r.get("error") or ""
            lat = f"{r['ms']} ms" if r.get("ms") is not None else "—"
            out.append(f"| {r['name']} | {r['country']} | {r['lang']} | {statut} | "
                       f"{r['items']} | {lat} | {r['format'] or '—'} | {rem} |")
    return "\n".join(out) + "\n"


def main() -> None:
    cat_path = Path(sys.argv[1] if len(sys.argv) > 1 else "sources/catalog.json")

    # --render-only : regenere le tableau markdown depuis le JSON deja mesure,
    # sans re-solliciter les serveurs (les chiffres du document restent stables).
    if "--render-only" in sys.argv:
        results = json.loads(Path("docs/feeds-check.json").read_text(encoding="utf-8"))
        Path("docs/sources-catalogue.md").write_text(md_table(results), encoding="utf-8")
        print("docs/sources-catalogue.md regenere depuis docs/feeds-check.json")
        return

    entries = json.loads(cat_path.read_text(encoding="utf-8"))["entries"]
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        results = list(ex.map(check, entries))

    Path("docs").mkdir(exist_ok=True)
    Path("docs/feeds-check.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    Path("docs/sources-catalogue.md").write_text(md_table(results), encoding="utf-8")

    rss = [r for r in results if r["type"] != "api"]
    ok = [r for r in rss if r["ok"]]
    print(f"\n{len(ok)}/{len(rss)} flux exploitables "
          f"({sum(r['items'] for r in ok)} articles vus au premier chargement)\n")

    width = max(len(r["name"]) for r in results) + 2
    for region in ["Europe", "Allemagne", "Italie", "Espagne", "Amerique du Nord", "Amerique du Sud",
                   "Afrique", "Maghreb", "Monde arabe", "Asie", "Moyen-Orient", "Monde", "API"]:
        rows = [r for r in results if r["region"] == region]
        if not rows:
            continue
        print(f"-- {region} " + "-" * (width + 46))
        for r in rows:
            flag = "OK " if r["ok"] else "KO "
            err = "" if r["ok"] else (r.get("error") or "")
            print(f"  {flag}{r['name']:<{width}}{r['items']:>4} items  {str(r['ms'] or '-'):>6} ms  {err}")
    print()


if __name__ == "__main__":
    main()
