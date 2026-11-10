#!/usr/bin/env python3
"""Convertit ARCHITECTURE.md en HTML autonome, pret a imprimer en PDF.

Sous-ensemble Markdown supporte (celui utilise dans le document) :
titres #/##/###, paragraphes (saut de ligne = <br>), listes - et 1.,
tableaux a pipes, blocs de code ```, regles ---, inline **gras**, `code`,
[liens](url).

Usage: python tools/md2html.py [src.md] [out.html]
"""
from __future__ import annotations

import html
import re
import sys
import unicodedata
from pathlib import Path

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
IMG = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
TABLE_SEP = re.compile(r"^\|[\s:\-|]+\|$")
OL = re.compile(r"^\d+\.\s+")


def slug(text: str, seen: dict) -> str:
    base = unicodedata.normalize("NFKD", text.replace("’", "'"))
    base = "".join(c for c in base if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    s = s or "section"
    if s in seen:
        seen[s] += 1
        s = f"{s}-{seen[s]}"
    else:
        seen[s] = 0
    return s


def inline(text: str) -> str:
    stash: list[str] = []

    def keep(m: re.Match) -> str:
        stash.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x00{len(stash) - 1}\x00"

    text = INLINE_CODE.sub(keep, text)
    text = html.escape(text)
    # les images avant les liens, sinon le "!" reste orphelin
    text = IMG.sub(r'<img src="\2" alt="\1" loading="lazy">', text)
    text = LINK.sub(r'<a href="\2">\1</a>', text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = ITALIC.sub(r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)


def cells(row: str) -> list[str]:
    r = row.strip()
    if r.startswith("|"):
        r = r[1:]
    if r.endswith("|") and not r.endswith("\\|"):
        r = r[:-1]
    # un pipe echappe (\|) appartient a la cellule, il ne la separe pas
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", r)]


def convert(md: str) -> tuple[str, list[tuple[str, str]]]:
    lines = md.split("\n")
    out: list[str] = []
    toc: list[tuple[str, str]] = []
    seen: dict = {}
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # --- bloc de code -------------------------------------------------
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            body = []
            while i < n and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{lang}"' if lang else ""
            code = html.escape("\n".join(body))
            out.append(f"<pre><code{cls}>{code}</code></pre>")
            continue

        # --- titres -------------------------------------------------------
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            sid = slug(text, seen)
            if level == 1:
                # le titre du document est deja rendu par la couverture HTML
                if not any(out):
                    i += 1
                    continue
                out.append(f'<h1 id="{sid}">{inline(text)}</h1>')
            elif level == 2:
                toc.append((sid, text))
                out.append(f'<h2 id="{sid}">{inline(text)}</h2>')
            elif level == 3:
                out.append(f'<h3 id="{sid}">{inline(text)}</h3>')
            else:
                out.append(f'<h4 id="{sid}">{inline(text)}</h4>')
            i += 1
            continue

        # --- regle horizontale -------------------------------------------
        if re.fullmatch(r"-{3,}|\*{3,}", stripped):
            out.append("<hr>")
            i += 1
            continue

        # --- tableau ------------------------------------------------------
        if stripped.startswith("|") and i + 1 < n and TABLE_SEP.match(lines[i + 1].strip()):
            head = cells(stripped)
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i].strip()))
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            body = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows
            )
            out.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>')
            continue

        # --- listes -------------------------------------------------------
        if stripped.startswith("- ") or OL.match(stripped):
            ordered = bool(OL.match(stripped))
            items = []
            while i < n:
                cur = lines[i].strip()
                if ordered and OL.match(cur):
                    items.append(OL.sub("", cur))
                elif not ordered and cur.startswith("- "):
                    items.append(cur[2:])
                elif cur and not cur.startswith(("#", "|", "```")) and items and lines[i].startswith("  "):
                    items[-1] += " " + cur
                else:
                    break
                i += 1
            tag = "ol" if ordered else "ul"
            body = "".join(f"<li>{inline(x)}</li>" for x in items)
            out.append(f"<{tag}>{body}</{tag}>")
            continue

        # --- paragraphe ---------------------------------------------------
        para = []
        while i < n:
            cur = lines[i].strip()
            if (not cur or cur.startswith(("#", "|", "```")) or cur.startswith("- ")
                    or OL.match(cur) or re.fullmatch(r"-{3,}", cur)):
                break
            para.append(cur)
            i += 1
        # un saut de ligne simple vaut une espace (Markdown) ; on joint AVANT
        # le rendu inline, sinon un **gras** coupe par un retour a la ligne
        # laisse ses deux marqueurs non apparies
        out.append("<p>" + inline(" ".join(para)) + "</p>")

    return "\n".join(out), toc


CSS = """
:root{
  --ink:#1c1917; --muted:#57534e; --line:#e7e5e4; --soft:#fafaf9;
  --accent:#9f1239; --accent-soft:#fff1f2;
  --sans:"Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  --mono:"Cascadia Code",Consolas,"SF Mono",Menlo,monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#fff;color:var(--ink);font:16.5px/1.62 var(--serif);
  font-feature-settings:"onum" 1,"kern" 1;text-rendering:optimizeLegibility}
.wrap{max-width:1180px;margin:0 auto;padding:0 28px;display:grid;
  grid-template-columns:238px minmax(0,1fr);gap:56px;align-items:start}
nav.toc{position:sticky;top:0;max-height:100vh;overflow:auto;padding:56px 0 40px;
  font-family:var(--sans);font-size:12.5px;line-height:1.45;border-right:1px solid var(--line)}
nav.toc .kicker{display:block;text-transform:uppercase;letter-spacing:.12em;font-size:10px;
  color:var(--muted);margin-bottom:14px}
nav.toc a{display:block;color:var(--muted);text-decoration:none;padding:5px 16px 5px 0;border-left:0}
nav.toc a:hover{color:var(--accent)}
main{padding:56px 0 96px;min-width:0}

header.cover{border-bottom:2px solid var(--ink);padding-bottom:26px;margin-bottom:38px}
header.cover .eyebrow{font-family:var(--sans);font-size:10.5px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--accent);font-weight:600}
header.cover h1{font-family:var(--sans);font-size:39px;line-height:1.1;letter-spacing:-.02em;
  margin:12px 0 0;font-weight:700;border:0;padding:0}
header.cover .sub{font-family:var(--sans);font-size:15px;color:var(--muted);margin-top:12px;max-width:60ch}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px;font-family:var(--sans)}
.meta span{font-size:11.5px;color:var(--muted);border:1px solid var(--line);
  border-radius:999px;padding:4px 11px;background:var(--soft)}

h1,h2,h3,h4{font-family:var(--sans);color:var(--ink);line-height:1.25}
h2{font-size:25px;letter-spacing:-.01em;margin:64px 0 18px;padding-top:22px;
  border-top:1px solid var(--line);font-weight:650;scroll-margin-top:20px}
h2:first-of-type{margin-top:44px}
h3{font-size:17px;margin:32px 0 10px;font-weight:650;scroll-margin-top:20px}
h4{font-size:14px;margin:24px 0 8px;color:var(--muted);text-transform:uppercase;
  letter-spacing:.08em;font-weight:650}
p{margin:0 0 15px}
strong{font-weight:650}
em{font-style:italic}
a{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(159,18,57,.25)}
a:hover{border-bottom-color:var(--accent)}
hr{border:0;border-top:1px solid var(--line);margin:34px 0}

ul,ol{margin:0 0 17px;padding-left:22px}
li{margin:0 0 8px;padding-left:3px}
li::marker{color:var(--muted)}
code{font-family:var(--mono);font-size:.86em;background:var(--soft);
  border:1px solid var(--line);border-radius:4px;padding:1px 5px;white-space:nowrap}
pre{background:#1c1917;color:#f5f5f4;border-radius:8px;padding:18px 20px;overflow:auto;
  font-size:11.5px;line-height:1.5;margin:0 0 20px}
pre code{background:none;border:0;padding:0;color:inherit;font-size:inherit;white-space:pre}

.tw{overflow-x:auto;margin:0 0 22px;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:13px;line-height:1.45}
thead th{background:var(--soft);text-align:left;font-weight:650;font-size:11.5px;
  text-transform:uppercase;letter-spacing:.05em;color:var(--muted);
  padding:10px 13px;border-bottom:1px solid var(--line);white-space:nowrap}
tbody td{padding:10px 13px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:last-child td{border-bottom:0}
tbody tr:nth-child(even){background:#fcfcfb}
td code,th code{white-space:normal;word-break:break-word}
img{max-width:100%;height:auto;display:block;margin:8px 0 22px;
  border:1px solid var(--line);border-radius:8px}

footer{margin-top:70px;padding-top:18px;border-top:1px solid var(--line);
  font-family:var(--sans);font-size:12px;color:var(--muted)}

@media (max-width:980px){
  .wrap{grid-template-columns:1fr;gap:0;padding:0 20px}
  nav.toc{display:none}
  main{padding:34px 0 60px}
  header.cover h1{font-size:30px}
}

@media print{
  @page{size:A4;margin:17mm 15mm}
  .wrap{display:block;max-width:none;padding:0}
  nav.toc{display:none}
  main{padding:0}
  body{font-size:10.4pt;line-height:1.5}
  header.cover h1{font-size:25pt}
  h2{font-size:15pt;margin:26pt 0 9pt;break-after:avoid;page-break-after:avoid}
  h3{font-size:11.5pt;margin:16pt 0 6pt;break-after:avoid;page-break-after:avoid}
  p,li{orphans:3;widows:3}
  pre{font-size:7.6pt;break-inside:avoid;page-break-inside:avoid;background:#f5f5f4;color:#1c1917;border:1px solid #d6d3d1;white-space:pre-wrap;word-break:break-word}
  .tw,table{break-inside:avoid;page-break-inside:avoid}
  img{max-height:150mm;width:auto;max-width:100%;break-inside:avoid}
  table{font-size:8.6pt}
  thead{display:table-header-group}
  a{color:inherit;border:0}
  a[href^="http"]::after{content:" (" attr(href) ")";font-size:7.5pt;color:#78716c}
  footer{break-before:avoid}
}
"""


COVERS = {
    "architecture.html": {
        "html_title": "Architecture — Plateforme d'actualité mondiale",
        "eyebrow": "Plan d'architecture · v1.0",
        "title": "Plateforme d'actualité mondiale",
        "sub": "Agrégation multi-sources, filtre par pays et région, rubrique vidéo sur le site "
               "et déclinaison quotidienne sur YouTube, TikTok, Instagram et X. "
               "Interface en cinq langues : français, anglais, allemand, espagnol, italien, "
               "avec les sources arabes reformulées.",
        "chips": ["5 novembre 2026", "MVP → production", "FR · EN · DE · ES · IT",
                  "65/75 flux vérifiés"],
    },
    "seo.html": {
        "html_title": "Positionnement — moteurs de recherche et moteurs IA",
        "eyebrow": "Stratégie de visibilité · v1.0",
        "title": "Se faire trouver par Google et par les IA",
        "sub": "Pourquoi la page événement est l'actif, ce qui rend une page citable par un moteur "
               "de réponse, et les garde-fous d'indexation.",
        "chips": ["5 novembre 2026", "SEO + GEO", "Plan 90 jours", "4 schémas JSON-LD prêts"],
    },
}


def build_html(body: str, toc: list[tuple[str, str]], cover: dict) -> str:
    nav = "\n".join(f'<a href="#{sid}">{html.escape(t)}</a>' for sid, t in toc)
    chips = "".join(f"<span>{html.escape(c)}</span>" for c in cover["chips"])
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(cover["html_title"])}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<nav class="toc"><span class="kicker">Sommaire</span>{nav}</nav>
<main>
<header class="cover">
  <div class="eyebrow">{html.escape(cover["eyebrow"])}</div>
  <h1>{html.escape(cover["title"])}</h1>
  <div class="sub">{html.escape(cover["sub"])}</div>
  <div class="meta">{chips}</div>
</header>
{body}
<footer>Document de travail — les chiffres de coût, de quota et de trafic sont des estimations à
revérifier à chaque phase. Les conditions d'utilisation des sources et des plateformes évoluent :
la date de rédaction fait foi.</footer>
</main>
</div>
</body>
</html>
"""


def main() -> None:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "ARCHITECTURE.md")
    dst = Path(sys.argv[2] if len(sys.argv) > 2 else "architecture.html")
    body, toc = convert(src.read_text(encoding="utf-8"))
    # la couverture HTML reprend deja version/date/perimetre : on evite le doublon
    if body.startswith("<p><strong>Version</strong>"):
        body = body.split("</p>", 1)[1].lstrip()
        body = body.removeprefix("<hr>").lstrip()
    cover = COVERS.get(dst.name, COVERS["architecture.html"])
    dst.write_text(build_html(body, toc, cover), encoding="utf-8")
    print(f"ecrit: {dst}  ({len(toc)} sections, {dst.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
