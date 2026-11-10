# Plateforme d'actualité mondiale — plan d'architecture

Agrégation d'actualité mondiale multi-sources, filtre par pays / région / thème, interface en
**cinq langues (FR, EN, DE, ES, IT)**, sources arabophones **reformulées** vers la langue du
lecteur, puis usine vidéo quotidienne pour YouTube, TikTok, Instagram et X.

## Livrables

| Fichier | Contenu |
|---|---|
| [`architecture.html`](architecture.html) | **Le document à lire.** Mise en page éditoriale, sommaire, prêt à imprimer en PDF (Ctrl+P) |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | La source du document, en Markdown (versionnable, éditable) |
| [`seo.html`](seo.html) | **Playbook de positionnement** : moteurs de recherche et moteurs IA |
| [`SEO.md`](SEO.md) | La source du playbook |
| [`DEPLOIEMENT.md`](DEPLOIEMENT.md) | **Checklist avant mise en ligne** et réponse à « faut-il une application locale ? » |
| [`seo/`](seo/) | Fichiers prêts à déployer : `robots.txt`, `llms.txt`, `head.html`, 4 schémas JSON-LD |
| [`db/schema.sql`](db/schema.sql) | Schéma PostgreSQL complet (pgvector, 21 tables), exécutable |
| [`sources/catalog.json`](sources/catalog.json) | Le catalogue des 81 sources (68 flux de rédaction, 7 Google News, 6 API) |
| [`docs/sources-catalogue.md`](docs/sources-catalogue.md) | Le catalogue mesuré, zone par zone |
| [`docs/feeds-check.json`](docs/feeds-check.json) | Mesures brutes du test, le 5 novembre 2026 |
| [`docs/pipeline.png`](docs/pipeline.png) / [`docs/pipeline.svg`](docs/pipeline.svg) | Schéma d'architecture en une image |
| [`docs/ad-slots.png`](docs/ad-slots.png) | Carte des emplacements publicitaires réservés (desktop + mobile) |
| [`docs/subtitles.png`](docs/subtitles.png) | Une voix, cinq sous-titres : l'alignement se fait au segment |
| [`docs/home.png`](docs/home.png) | Composition de la page d'accueil : une manuelle, Résumé, fil, carte |
| [`docs/card.png`](docs/card.png) | Anatomie d'une carte vidéo : zones interdites, typographie, rythme |
| [`docs/site.png`](docs/site.png) | **Le site, rendu** : accueil complet 1440 px avec les dépêches du 5 novembre |
| [`docs/site-dark.png`](docs/site-dark.png) | Le même écran en thème sombre |
| [`docs/globe.png`](docs/globe.png) | La page Carte : un globe, un point par événement, taille = nombre de rédactions |
| [`docs/demo/bulletin.mp4`](docs/demo/bulletin.mp4) | **Démo réelle** : 10 cartes, 62 s, 1080×1920, sous-titres — sur des dépêches du 5 novembre |
| [`docs/demo/contact.png`](docs/demo/contact.png) | Les 10 cartes en planche contact |
| [`docs/demo/`](docs/demo/) | Le dossier de production : `backgrounds/` pour les images, `music/` pour le son, `audio/` pour la voix |

## Ouvrir dans VS Code

Ce dépôt contient un **plan** et ses outils de rendu — pas encore une application
web. Ouvrir le dossier et lancer un script fonctionne ; « lancer le site »
n'existe pas encore (voir la section suivante).

```powershell
code .
python -m pip install -r requirements.txt     # Pillow, et numpy pour le globe
```

Ensuite : `Ctrl+Maj+B` exécute la tâche par défaut (régénération des deux documents
HTML). Le reste est dans `Terminal → Run Task` : figures, démo vidéo, audit des
flux, vérification du schéma et des artefacts SEO.

Deux points de configuration, si vous préférez ne pas utiliser les tâches :

- `python.analysis.extraPaths` contient `tools`, parce que les scripts s'importent
  entre eux (`geo_silhouette`) ;
- les `.ps1` sont bloqués par défaut sous Windows : passer par
  `powershell -ExecutionPolicy Bypass -File tools/demo_build.ps1`, ou autoriser
  l'exécution pour l'utilisateur courant.

## Ce qui manque pour « lancer le site »

Il n'y a ni serveur, ni `package.json`, ni page web : le HTML produit est un
document de lecture, pas une application. Pour avoir quelque chose qui tourne, la
première étape est la Phase 0 du plan — les 24 flux, une base, une page qui liste
les événements avec `?country=FR`.

## Collecter et regrouper (Phase 0)

```bash
python tools/poller.py --once                 # un cycle de collecte -> data/news.db
python tools/poller.py --loop --interval 600  # en continu, toutes les 10 minutes
python tools/report.py --hours 72             # lit la base, écrit docs/clusters.html
```

Le poller utilise les requêtes conditionnelles (`ETag`, `If-Modified-Since`) : un flux qui
n'a pas bougé coûte une requête et zéro traitement. Un flux qui échoue huit fois de suite est
désactivé automatiquement.

Le rapport ne fait **aucun appel réseau** : il travaille sur `data/news.db`, qu'on peut donc
régénérer autant de fois qu'on veut. Le regroupement est encore lexical (TF-IDF sur les titres) —
les langues différentes ne fusionnent pas tant que les embeddings ne sont pas branchés.

**Pour une vraie fenêtre de 72 h**, il faut laisser tourner le poller trois jours : un flux RSS
n'expose qu'une vingtaine à une centaine de titres, soit ~24 h d'historique au mieux. Sous Windows,
une tâche planifiée toutes les 10 minutes fait l'affaire (`schtasks /create /sc minute /mo 10 ...`).
`data/` est ignoré par git.

## Outils

Aucune dépendance à installer pour les documents ; les figures demandent Pillow.

```bash
python tools/check_feeds.py               # audite le catalogue (65/75 flux OK au dernier passage)
python tools/check_feeds.py --render-only # regenere le tableau markdown sans re-tester
python tools/md2html.py                   # ARCHITECTURE.md -> architecture.html
python tools/md2html.py SEO.md seo.html   # SEO.md -> seo.html
python tools/seo_check.py                 # valide robots/llms/JSON-LD avant mise en ligne
python tools/make_diagram.py              # docs/pipeline.png + .svg
python tools/make_admap.py                # docs/ad-slots.png (emplacements pub)
python tools/make_subtitle_figure.py      # docs/subtitles.png (alignement des sous-titres)
python tools/make_home_figure.py          # docs/home.png (composition de l'accueil)
python tools/make_card_figure.py          # docs/card.png (anatomie d'une carte vidéo)
python tools/make_site_preview.py         # docs/site.png (rendu de la page d'accueil)
python tools/make_site_preview.py --theme=dark   # docs/site-dark.png
python tools/make_globe.py                 # docs/globe.png (page Carte, projection orthographique)
python tools/demo_deck.py --render        # docs/demo : cartes, timing, sous-titres
powershell tools/demo_build.ps1           # assemble tout : images, musique, voix, sous-titres
python tools/lint_schema.py               # contrôle statique de db/schema.sql
python tools/size_estimate.py             # volume de stockage selon le trafic
python tools/poller.py --once             # collecte les flux dans data/news.db
python tools/report.py --hours 72         # événements regroupés -> docs/clusters.html
```

## Les quatre points à retenir

1. **On ne republie jamais un article** : titre + extrait ≤ 150 caractères + lien sortant.
   C'est ce qui rend le projet tenable sans contrat de licence.
2. **Le regroupement en événements est le cœur du produit**, pas un module annexe.
3. **La vidéo est un produit séparé** qui consomme la base une fois celle-ci fiable — et elle
   bute sur des contraintes de plateforme avant des contraintes techniques.
4. **L'arabe n'est pas une langue d'interface, c'est un corpus.** On reformule les titres vers la
   langue du lecteur, jamais une traduction littérale — et le titre original reste visible. Le
   raisonnement juridique est en section 10.2 du document.

Les décisions encore ouvertes sont listées en section 16.
