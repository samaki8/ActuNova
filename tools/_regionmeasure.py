import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "tools")
import gazetteer  # noqa: E402

g = gazetteer.gazetteer()
con = sqlite3.connect("data/news.db")
since = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
rows = con.execute("SELECT title, region FROM articles WHERE published_at >= ?",
                   (since,)).fetchall()

tagged = 0
by_region = Counter()
by_feed_region = Counter()
difference = 0
for title, feed_region in rows:
    hits = g.tag(title)
    if hits:
        tagged += 1
        reg = hits[0]["region"]
        by_region[reg] += 1
        if reg and feed_region and reg != feed_region:
            difference += 1
    by_feed_region[feed_region] += 1

total = len(rows)
print(f"{total} articles (72 h)")
print(f"taggés par pays : {tagged} ({100 * tagged / total:.0f} %)")
print(f"région du sujet ≠ région du flux : {difference} "
      f"({100 * difference / max(1, tagged):.0f} % des articles taggés)")

print("\nrépartition par région du SUJET :")
for reg, n in by_region.most_common():
    print("  {:<20}{:>6}  {:>5.1f} %".format(str(reg), n, 100 * n / total))

print("\nrépartition par région du FLUX (pour comparaison) :")
for reg, n in by_feed_region.most_common(6):
    print("  {:<20}{:>6}".format(str(reg), n))
