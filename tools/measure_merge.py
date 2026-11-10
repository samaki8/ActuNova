"""Mesure l'apport du pont interlangues sur la base reelle. Script d'experience."""
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "tools")
import cluster as cl  # noqa: E402

NOISE = re.compile(
    r"meteo|weather|horoscope|programme tv|bourse de|taux de change|"
    r"cours du|resultats du jour|loterie|sudoku|mots fleches", re.I)

con = sqlite3.connect("data/news.db")
con.row_factory = sqlite3.Row
since = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
rows = [dict(r) for r in con.execute(
    "SELECT title, source, lang, published_at FROM articles WHERE published_at >= ?",
    (since,))]
arts = [a for a in rows if not NOISE.search(cl.norm(a["title"]))]
titles = [a["title"] for a in arts]
print(f"{len(arts)} articles, {len({a['lang'] for a in arts})} langues")

base = cl.cluster(titles)
print(f"avant : {len(base)} evenements, "
      f"{sum(1 for g in base if len({arts[i]['source'] for i in g}) >= 2)} multi-sources")

for shared in (1, 2, 3):
    merged = cl.merge_by_signature(base, titles, min_shared=shared)
    multi = sum(1 for g in merged if len({arts[i]["source"] for i in g}) >= 2)
    print(f"  fusion >= {shared} tokens rares : {len(merged)} evenements, {multi} multi-sources")

merged = cl.merge_by_signature(base, titles, min_shared=2)

print("\n-- le cas Paraguay --")
for g in merged:
    if any("paraguay" in cl.norm(arts[i]["title"]) for i in g):
        langs = Counter(arts[i]["lang"] for i in g)
        print(f"  groupe de {len(g)} articles, langues {dict(langs)}")
        for i in g[:4]:
            print(f"    [{arts[i]['lang']}] {arts[i]['title'][:72]}")

print("\n-- verifier les fusions douteuses (titre le plus long du groupe) --")
douteux = 0
for g in merged:
    if len(g) < 3:
        continue
    langs = {arts[i]["lang"] for i in g}
    if len(langs) >= 3:
        douteux += 1
        if douteux <= 5:
            print(f"  {len(g)} articles, langues {sorted(langs)} : {arts[g[0]]['title'][:60]}")
print(f"  {douteux} groupes melangent 3 langues ou plus")
