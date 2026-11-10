import sqlite3
import sys
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

con = sqlite3.connect("data/news.db")
since = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()

print("articles par region de flux (72 h) :")
total = 0
for region, n in con.execute(
        "SELECT region, COUNT(*) FROM articles WHERE published_at >= ? "
        "GROUP BY region ORDER BY 2 DESC", (since,)):
    total += n
    print("  {:<18}{:>6}  {:>5.1f} %".format(str(region or "?"), n, 100.0 * n / 4567))

print("\narticles par langue (72 h) :")
for lang, n in con.execute(
        "SELECT lang, COUNT(*) FROM articles WHERE published_at >= ? "
        "GROUP BY lang ORDER BY 2 DESC", (since,)):
    print("  {:<8}{:>6}".format(str(lang or "?"), n))

print("\nflux par region :")
for region, n in con.execute(
        "SELECT region, COUNT(*) FROM feeds GROUP BY region ORDER BY 2 DESC"):
    print("  {:<18}{:>4}".format(str(region or "?"), n))
