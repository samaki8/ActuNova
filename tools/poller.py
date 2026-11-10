#!/usr/bin/env python3
"""Collecte continue des flux dans une base SQLite.

Un cycle = une requete conditionnelle par flux (ETag / If-Modified-Since), les
nouveaux articles inseres, l'etat du flux mis a jour. On peut le laisser tourner
des jours : les flux qui echouent sont comptes puis desactives.

    python tools/poller.py --once                 # un cycle, puis sortie
    python tools/poller.py --loop --interval 600  # toutes les 10 minutes

Base : data/news.db (creee au premier lancement, amorcee depuis le catalogue).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

DB = Path("data/news.db")
CATALOG = Path("sources/catalog.json")
UA = "Mozilla/5.0 (compatible; FilMonde/0.1; +https://filmonde.example/bot)"
ATOM = "{http://www.w3.org/2005/Atom}"

SCHEMA = """
CREATE TABLE IF NOT EXISTS feeds (
    id            INTEGER PRIMARY KEY,
    slug          TEXT UNIQUE,
    name          TEXT NOT NULL,
    url           TEXT UNIQUE NOT NULL,
    lang          TEXT,
    region        TEXT,
    etag          TEXT,
    last_modified TEXT,
    last_poll     TEXT,
    last_ok       TEXT,
    errors        INTEGER NOT NULL DEFAULT 0,
    active        INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS articles (
    id           INTEGER PRIMARY KEY,
    feed_id      INTEGER REFERENCES feeds(id),
    url          TEXT UNIQUE NOT NULL,
    title        TEXT NOT NULL,
    summary      TEXT,
    published_at TEXT,
    fetched_at   TEXT NOT NULL,
    lang         TEXT,
    source       TEXT,
    region       TEXT,
    feed_category TEXT
);
CREATE INDEX IF NOT EXISTS idx_articles_pub ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_feed ON articles(feed_id);CREATE TABLE IF NOT EXISTS runs (
    id         INTEGER PRIMARY KEY,
    started_at TEXT, ended_at TEXT,
    fetched    INTEGER, new INTEGER, failed INTEGER
);
"""

TRACKING = re.compile(r"^(utm_|fbclid|gclid|at_|ref=|mc_)", re.I)


def canonical(url: str) -> str:
    if not url:
        return ""
    url = url.split("#", 1)[0]
    base, _, query = url.partition("?")
    base = base.rstrip("/")
    keep = [p for p in query.split("&") if p and not TRACKING.match(p)]
    return base + ("?" + "&".join(keep) if keep else "")


def iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def parse_date(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        d = parsedate_to_datetime(raw)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:  # noqa: BLE001
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
            try:
                d = datetime.strptime(raw[:26], fmt)
                return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
            except Exception:  # noqa: BLE001
                continue
    return None


def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " "))
    return re.sub(r"\s+", " ", s).strip()


def get(url: str, etag: str | None, modified: str | None):
    headers = {"User-Agent": UA, "Accept": "application/rss+xml, application/xml, */*"}
    if etag:
        headers["If-None-Match"] = etag
    if modified:
        headers["If-Modified-Since"] = modified
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read(), r.headers
    except urllib.error.HTTPError as e:
        return e.code, b"", e.headers
    except Exception:  # noqa: BLE001  (DNS, TLS, timeout : un flux ne doit pas tuer le cycle)
        return 0, b"", None


def items_from(raw: bytes):
    root = ET.fromstring(raw)
    nodes = root.findall(".//item") or root.findall(f".//{ATOM}entry")
    for it in nodes:
        title = (it.findtext("title") or it.findtext(f"{ATOM}title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not link:
            n = it.find(f"{ATOM}link")
            if n is not None:
                link = n.get("href", "")
        summary = (it.findtext("description") or it.findtext("summary")
                   or it.findtext(f"{ATOM}summary") or "")
        date = parse_date(it.findtext("pubDate") or it.findtext("published")
                          or it.findtext(f"{ATOM}updated")
                          or it.findtext("{http://purl.org/dc/elements/1.1/}date") or "")
        if title and link:
            yield {
                "title": title[:400],
                "category": (it.findtext("category") or "").strip()[:80],
                "url": canonical(link),
                "summary": strip_html(summary)[:200],
                "published_at": iso(date),
            }


def poll_one(feed: dict) -> dict:
    status, body, headers = get(feed["url"], feed.get("etag"), feed.get("last_modified"))
    if status == 304:
        return {"slug": feed["slug"], "status": 304, "items": [], "ok": True}
    if status != 200 or not body:
        return {"slug": feed["slug"], "status": status, "items": [], "ok": False}
    try:
        items = list(items_from(body))
    except ET.ParseError:
        return {"slug": feed["slug"], "status": status, "items": [], "ok": False}
    return {
        "slug": feed["slug"], "status": status, "items": items, "ok": True,
        "etag": headers.get("ETag"), "modified": headers.get("Last-Modified"),
    }


def cycle(con: sqlite3.Connection, workers: int = 12) -> tuple[int, int, int]:
    feeds = [dict(r) for r in con.execute(
        "SELECT slug, name, url, lang, region, etag, last_modified FROM feeds WHERE active = 1")]
    started = datetime.now(timezone.utc).isoformat()
    now = started
    fetched = new = failed = 0

    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(poll_one, feeds))

    for r in results:
        if not r["ok"]:
            con.execute("UPDATE feeds SET errors = errors + 1, last_poll = ?, "
                        "active = CASE WHEN errors >= 8 THEN 0 ELSE active END WHERE slug = ?",
                        (now, r["slug"]))
            failed += 1
            continue
        fetched += len(r["items"])
        for it in r["items"]:
            cur = con.execute(
                "INSERT OR IGNORE INTO articles "
                "(feed_id, url, title, summary, published_at, fetched_at, lang, source, region, "
                " feed_category) "
                "SELECT id, ?, ?, ?, ?, ?, ?, ?, ?, ? FROM feeds WHERE slug = ?",
                (it["url"], it["title"], it["summary"], it["published_at"], now,
                 None, None, None, it.get("category"), r["slug"]))
            if cur.rowcount:
                new += 1
            # rattrapage : les articles deja en base au premier passage n'avaient
            # pas de categorie (colonne ajoutee apres coup)
            if it.get("category"):
                con.execute(
                    "UPDATE articles SET feed_category = ? "
                    "WHERE url = ? AND (feed_category IS NULL OR feed_category = '')",
                    (it["category"], it["url"]))
        con.execute(
            "UPDATE feeds SET last_poll = ?, last_ok = ?, errors = 0, etag = COALESCE(?, etag), "
            "last_modified = COALESCE(?, last_modified) WHERE slug = ?",
            (now, now, r.get("etag"), r.get("modified"), r["slug"]))

    # on remplit lang / source / region depuis le flux, pour les lignes inserees
    con.execute("""
        UPDATE articles SET
            lang   = COALESCE(lang,  (SELECT lang   FROM feeds WHERE feeds.id = articles.feed_id)),
            source = COALESCE(source,(SELECT name   FROM feeds WHERE feeds.id = articles.feed_id)),
            region = COALESCE(region,(SELECT region FROM feeds WHERE feeds.id = articles.feed_id))
        WHERE lang IS NULL OR source IS NULL OR region IS NULL
    """)
    con.execute("INSERT INTO runs (started_at, ended_at, fetched, new, failed) VALUES (?,?,?,?,?)",
                (started, datetime.now(timezone.utc).isoformat(), fetched, new, failed))
    con.commit()
    return fetched, new, failed


def seed(con: sqlite3.Connection) -> None:
    entries = json.loads(CATALOG.read_text(encoding="utf-8"))["entries"]
    for e in entries:
        if e.get("type") == "api":
            continue
        con.execute("INSERT OR IGNORE INTO feeds (slug, name, url, lang, region) VALUES (?,?,?,?,?)",
                    (e["id"], e["name"], e["url"], e["lang"], e["region"]))
    con.commit()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=600)
    args = ap.parse_args()

    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)

    # migration legere : CREATE TABLE IF NOT EXISTS ne modifie pas une base
    # existante, donc les colonnes ajoutees apres coup se creent ici
    cols = {r[1] for r in con.execute("PRAGMA table_info(articles)")}
    if "feed_category" not in cols:
        con.execute("ALTER TABLE articles ADD COLUMN feed_category TEXT")
        con.commit()
        print("migration : colonne feed_category ajoutee")
    seed(con)

    total = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    print(f"base {DB} — {total} articles deja stockes")

    while True:
        t0 = time.time()
        fetched, new, failed = cycle(con)
        total = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        stamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{stamp}] {fetched} lus · {new} nouveaux · {failed} flux en echec · "
              f"total {total} · {time.time() - t0:.0f}s", flush=True)
        if args.once or not args.loop:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
