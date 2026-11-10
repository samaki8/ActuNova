#!/usr/bin/env python3
"""Verifie les artefacts SEO / GEO : JSON-LD, robots.txt, llms.txt, entete HTML.

Ne remplace pas le test des outils (Rich Results, Search Console) : il attrape les
erreurs betes et les champs manquants avant la mise en ligne.

Usage: python tools/seo_check.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

errors: list[str] = []
warnings: list[str] = []

REQUIRED = {
    "Article": ["headline", "datePublished", "dateModified", "inLanguage", "citation", "publisher"],
    "VideoObject": ["name", "uploadDate", "thumbnailUrl", "duration", "description"],
    "CollectionPage": ["name", "url", "about"],
    "WebSite": ["url", "name"],
    "NewsMediaOrganization": ["name", "url", "logo"],
}


def check_jsonld() -> int:
    files = sorted(Path("seo/jsonld").glob("*.json"))
    if not files:
        errors.append("seo/jsonld/ : aucun fichier")
        return 0
    count = 0
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{f.name} : JSON invalide ({e})")
            continue

        nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
        for node in nodes:
            count += 1
            t = node.get("@type")
            if not t:
                errors.append(f"{f.name} : nœud sans @type")
                continue
            for field in REQUIRED.get(t, []):
                if field not in node or not node[field]:
                    errors.append(f"{f.name} : {t} sans « {field} »")
            if t in ("Article", "WebPage", "CollectionPage", "VideoObject"):
                for k in ("datePublished", "dateModified", "uploadDate"):
                    v = node.get(k)
                    if isinstance(v, str) and not re.match(r"^\d{4}-\d{2}-\d{2}T", v):
                        errors.append(f"{f.name} : {k} n'est pas au format ISO 8601")
            if t == "Article" and node.get("citation") and not isinstance(node["citation"], list):
                warnings.append(f"{f.name} : citation devrait être un tableau")
    return count


def check_robots() -> None:
    p = Path("seo/robots.txt")
    if not p.exists():
        errors.append("seo/robots.txt manquant")
        return
    allowed = {"user-agent", "allow", "disallow", "sitemap", "crawl-delay", "host"}
    current_ua = None
    for i, raw in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            errors.append(f"robots.txt ligne {i} : pas de « : » — {line!r}")
            continue
        key, _, val = line.partition(":")
        if key.strip().lower() not in allowed:
            errors.append(f"robots.txt ligne {i} : directive inconnue « {key.strip()} »")
        if key.strip().lower() == "user-agent":
            current_ua = val.strip()
        if key.strip().lower() == "sitemap" and not val.strip().startswith("https://"):
            errors.append(f"robots.txt ligne {i} : sitemap non absolu en https")
    for ua in ("OAI-SearchBot", "PerplexityBot", "ClaudeBot", "GPTBot", "Googlebot"):
        if ua not in p.read_text(encoding="utf-8"):
            warnings.append(f"robots.txt : {ua} non mentionné explicitement")
    if current_ua is None:
        errors.append("robots.txt : aucun User-agent")


def check_llms() -> None:
    p = Path("seo/llms.txt")
    if not p.exists():
        errors.append("seo/llms.txt manquant")
        return
    txt = p.read_text(encoding="utf-8")
    if not txt.startswith("# "):
        errors.append("llms.txt : doit commencer par un titre « # »")
    if "> " not in txt:
        errors.append("llms.txt : résumé « > » absent")
    if len(re.findall(r"(?m)^## ", txt)) < 2:
        warnings.append("llms.txt : moins de deux sections « ## »")
    if len(txt) > 20_000:
        warnings.append("llms.txt : plus de 20 000 caractères, il sera tronqué")


def check_head() -> None:
    p = Path("seo/head.html")
    if not p.exists():
        errors.append("seo/head.html manquant")
        return
    h = p.read_text(encoding="utf-8")
    for needle, label in [
        ('rel="canonical"', "canonical"),
        ('hreflang="fr"', "hreflang fr"),
        ('hreflang="en"', "hreflang en"),
        ('hreflang="x-default"', "hreflang x-default"),
        ('name="robots"', "meta robots"),
        ('property="og:image"', "og:image"),
        ('application/ld+json', "JSON-LD"),
    ]:
        if needle not in h:
            errors.append(f"head.html : {label} absent")
    if "max-snippet:-1" not in h:
        warnings.append("head.html : max-snippet:-1 absent — limite la taille des extraits citables")


def main() -> None:
    n = check_jsonld()
    check_robots()
    check_llms()
    check_head()

    print(f"JSON-LD : {n} nœud(s) vérifié(s)")
    for w in warnings:
        print(f"  avertissement : {w}")
    for e in errors:
        print(f"  ERREUR : {e}")
    if errors:
        print(f"\n{len(errors)} erreur(s)")
        sys.exit(1)
    print(f"OK — {len(warnings)} avertissement(s), aucune erreur")


if __name__ == "__main__":
    main()
