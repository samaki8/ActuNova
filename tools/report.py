#!/usr/bin/env python3
"""Rapport de clustering, lu depuis la base du poller.

Ne fait aucun appel reseau : il travaille sur data/news.db. On peut donc le
relancer autant de fois qu'on veut sans solliciter les redactions.

    python tools/report.py --hours 72 --min-sources 2

Sorties : docs/clusters.html + un resume sur la console.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cluster as cl

DB = Path("data/news.db")
NOISE = re.compile(
    r"meteo|weather|horoscope|programme tv|bourse de|taux de change|"
    r"cours du|resultats du jour|loterie|sudoku|mots fleches", re.I)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=72)
    ap.add_argument("--min-sources", type=int, default=2)
    ap.add_argument("--out", default="docs/clusters.html")
    args = ap.parse_args()

    if not DB.exists():
        raise SystemExit("base absente : lancer d'abord python tools/poller.py --once")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    since = (datetime.now(timezone.utc) - timedelta(hours=args.hours)).isoformat()

    rows = con.execute(
        "SELECT title, url, source, lang, region, published_at FROM articles "
        "WHERE published_at >= ? ORDER BY published_at", (since,)).fetchall()

    articles, bruit = [], 0
    for r in rows:
        if NOISE.search(cl.norm(r["title"])):
            bruit += 1
            continue
        articles.append(dict(r))

    total_db = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    feeds_ok = con.execute("SELECT COUNT(*) FROM feeds WHERE active = 1").fetchone()[0]
    feeds_ko = con.execute("SELECT COUNT(*) FROM feeds WHERE active = 0").fetchone()[0]

    print(f"base : {total_db} articles · periode {args.hours} h : {len(articles)} "
          f"({bruit} rubriques ecartees)")
    if not articles:
        raise SystemExit("aucun article sur la periode")

    groups = cl.cluster([a["title"] for a in articles])
    clusters = []
    for g in groups:
        srcs = {articles[i]["source"] for i in g}
        clusters.append((len(srcs), len(g), g))
    clusters.sort(key=lambda c: (-c[0], -c[1]))

    multi = [c for c in clusters if c[0] >= args.min_sources]
    print(f"{len(clusters)} evenements · {len(multi)} couverts par {args.min_sources}+ redactions")

    langs = Counter(a["lang"] for a in articles if a["lang"])
    print("langues :", ", ".join(f"{k} {v}" for k, v in langs.most_common(6)))

    def esc(s):
        return html.escape(s or "")

    cards = []
    for ns, na, g in multi:
        g = sorted(g, key=lambda i: articles[i]["published_at"] or "")
        lead = articles[g[0]]
        items = "".join(
            f'<li><span class="src">{esc(articles[i]["source"])}</span> '
            f'<a href="{esc(articles[i]["url"])}" target="_blank" rel="noopener">'
            f'{esc(articles[i]["title"])}</a></li>' for i in g[:8])
        when = (lead["published_at"] or "")[11:16]
        cards.append(
            f'<article class="ev"><header><span class="n">{ns} rédactions · {na} articles</span>'
            f'<time>{when} UTC</time></header><h2>{esc(lead["title"])}</h2>'
            f'<ul>{items}</ul></article>')

    page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Événements — {len(articles)} articles sur {args.hours} h</title>
<style>
 body{{margin:0;background:#FBFAF7;color:#17181A;font:15px/1.5 -apple-system,"Segoe UI",sans-serif}}
 .wrap{{max-width:920px;margin:0 auto;padding:44px 24px 80px}}
 h1{{font:600 27px/1.2 Georgia,serif;margin:0 0 6px}}
 .sub{{color:#6B6F76;font-size:13px;margin:0 0 26px}}
 .kpi{{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 26px}}
 .kpi div{{border:1px solid #E6E3DD;border-radius:10px;padding:10px 14px;background:#fff}}
 .kpi b{{display:block;font-size:20px}}
 .kpi span{{font-size:11px;color:#6B6F76;text-transform:uppercase;letter-spacing:.08em}}
 .note{{background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:14px 16px;
   font-size:13px;color:#713F12;margin:0 0 28px}}
 .note b{{color:#92400E}}
 .ev{{border:1px solid #E6E3DD;border-radius:12px;background:#fff;padding:16px 18px;margin:0 0 14px}}
 .ev header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}}
 .n{{font-size:11px;font-weight:600;color:#9F1239;text-transform:uppercase;letter-spacing:.06em}}
 time{{font-size:11px;color:#6B6F76}}
 .ev h2{{font:600 17px/1.3 Georgia,serif;margin:0 0 10px}}
 .ev ul{{margin:0;padding-left:18px}}
 .ev li{{margin:0 0 4px;font-size:13.5px}}
 .src{{display:inline-block;min-width:104px;color:#6B6F76;font-size:11.5px;font-weight:600}}
 a{{color:#17181A;text-decoration:none;border-bottom:1px solid #E6E3DD}}
 a:hover{{border-color:#9F1239}}
</style></head><body><div class="wrap">
<h1>Événements des {args.hours} dernières heures</h1>
<p class="sub">Lu depuis <code>data/news.db</code> — aucun appel réseau. Regroupement lexical
(TF-IDF sur les titres) : les langues différentes ne fusionnent pas encore.</p>
<div class="kpi">
 <div><b>{len(articles)}</b><span>articles</span></div>
 <div><b>{len(clusters)}</b><span>événements</span></div>
 <div><b>{len(multi)}</b><span>multi-sources</span></div>
 <div><b>{len({a["source"] for a in articles})}</b><span>rédactions</span></div>
 <div><b>{feeds_ok}</b><span>flux actifs</span></div>
{f'<div style="border-color:#FCA5A5"><b>{feeds_ko}</b><span>flux désactivés</span></div>' if feeds_ko else ''}
</div>
<p class="note"><b>Ce que ce prototype ne sait pas faire.</b> Un même fait couvert en anglais et en
allemand compte pour deux événements tant que les embeddings multilingues ne sont pas branchés.
{bruit} rubriques récurrentes (météo, bourse) ont été écartées en amont.</p>
{''.join(cards)}
</div></body></html>"""

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(page, encoding="utf-8")
    print(f"ecrit: {args.out}")

    print("\n-- les 10 événements les mieux couverts --")
    for ns, na, g in multi[:10]:
        print(f"  [{ns} red.] {articles[g[0]]['title'][:74]}")


if __name__ == "__main__":
    main()
