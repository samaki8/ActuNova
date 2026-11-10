# Catalogue de sources — mesures réelles

Test automatisé (`tools/check_feeds.py`), effectué le 05/11/2026 à 22:32.

« Statut » = le flux répond et contient des articles au moment du test. Un flux peut casser demain : c'est précisément pour cela que le poller surveille les flux muets et désactive automatiquement ceux qui échouent.

> Les latences sont mesurées avec 10 requêtes en parallèle : elles sont gonflées par la concurrence et ne doivent pas servir au dimensionnement. Un poller réel interroge les flux de façon étalée.


## Europe

5/6 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| Euronews | EU | en | OK | 50 | 887 ms | RSS 2.0 [text/xml] |  |
| Politico Europe | BE | en | OK | 10 | 2742 ms | RSS 2.0 [application/rss+xml] |  |
| Reuters (monde) | GB | en | **KO** | 0 | 446 ms | — | reseau : [Errno 11001] getaddrinfo failed |
| BBC World | GB | en | OK | 20 | 4359 ms | RSS 2.0 [text/xml] |  |
| Deutsche Welle (all) | DE | en | OK | 124 | 4932 ms | RSS 2.0 [application/xml] |  |
| France 24 | FR | fr | OK | 24 | 1288 ms | RSS 2.0 [application/rss+xml] |  |

## Allemagne

9/9 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| Deutsche Welle (de) | DE | de | OK | 79 | 401 ms | RSS 1.0 (RDF) [text/xml] |  |
| Tagesschau (ARD) | DE | de | OK | 40 | 772 ms | RSS 2.0 [application/xml] |  |
| Der Spiegel | DE | de | OK | 30 | 347 ms | RSS 2.0 [application/rss+xml] |  |
| FAZ | DE | de | OK | 160 | 40913 ms | RSS 2.0 [application/xml] |  |
| Süddeutsche Zeitung | DE | de | OK | 15 | 169 ms | RSS 2.0 [application/xml] |  |
| Die Zeit | DE | de | OK | 15 | 178 ms | RSS 2.0 [application/rss+xml] |  |
| Handelsblatt | DE | de | OK | 50 | 538 ms | RSS 2.0 [application/rss+xml] |  |
| n-tv | DE | de | OK | 50 | 2161 ms | RSS 2.0 [text/xml] |  |
| Deutschlandfunk | DE | de | OK | 44 | 439 ms | RSS 2.0 [application/rss+xml] |  |

## Italie

6/6 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| ANSA | IT | it | OK | 28 | 356 ms | RSS 2.0 [text/xml] |  |
| Corriere della Sera | IT | it | OK | 69 | 189 ms | RSS 2.0 [text/xml] |  |
| La Repubblica | IT | it | OK | 30 | 222 ms | RSS 2.0 [application/xml] |  |
| Il Sole 24 Ore | IT | it | OK | 9 | 310 ms | RSS 2.0 [text/xml] |  |
| Il Post | IT | it | OK | 80 | 383 ms | RSS 2.0 [application/rss+xml] |  |
| Sky TG24 | IT | it | OK | 100 | 301 ms | RSS 2.0 [application/xml] |  |

## Espagne

5/5 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| El Mundo | ES | es | OK | 21 | 251 ms | RSS 2.0 [text/xml] |  |
| ABC (Espana) | ES | es | OK | 20 | 292 ms | RSS 2.0 [text/xml] |  |
| elDiario.es | ES | es | OK | 115 | 1315 ms | RSS 2.0 [text/xml] |  |
| La Vanguardia | ES | es | OK | 156 | 830 ms | RSS 2.0 [application/xml] |  |
| Europa Press | ES | es | OK | 10 | 224 ms | RSS 2.0 [text/xml] |  |

## Amerique du Nord

6/9 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| CBC News | CA | en | OK | 20 | 6092 ms | RSS 2.0 [application/xml] |  |
| Global News | CA | en | OK | 10 | 2706 ms | RSS 2.0 [application/rss+xml] |  |
| CTV News | CA | en | **KO** | 0 | 3105 ms | — | HTTP 404 |
| Radio-Canada | CA | fr | OK | 34 | 5360 ms | RSS 2.0 [text/xml] |  |
| CNN (top stories) | US | en | OK | 69 | 6482 ms | RSS 2.0 [text/xml] |  |
| Fox News | US | en | OK | 25 | 8151 ms | RSS 2.0 [text/xml] |  |
| Associated Press | US | en | **KO** | 0 | 4139 ms | — | HTTP 403 |
| New York Times (home) | US | en | OK | 23 | 3842 ms | RSS 2.0 [application/xml] |  |
| Washington Post (world) | US | en | **KO** | 0 | 13458 ms | — | HTTP 502 |

## Amerique du Sud

3/5 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| Clarin | AR | es | OK | 10 | 3061 ms | RSS 2.0 [text/xml] |  |
| La Nacion | AR | es | OK | 84 | 4350 ms | RSS 2.0 [application/xml] |  |
| El Tiempo | CO | es | **KO** | 0 | 3332 ms | — | XML invalide : not well-formed (invalid token): line 72, column 4 |
| Folha de S.Paulo | BR | pt | OK | 100 | 5024 ms | RSS 2.0 [text/xml] |  |
| Emol (El Mercurio) | CL | es | **KO** | 0 | 3929 ms | — | ConnectionResetError : [WinError 10054] Une connexion existante a dû être fermée pa |

## Afrique

4/5 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| Africanews | AF | en | OK | 50 | 1765 ms | RSS 2.0 [application/xhtml+xml] |  |
| AllAfrica | AF | en | OK | 33 | 2299 ms | RSS 2.0 [application/rss+xml] |  |
| The Africa Report | AF | en | OK | 10 | 1862 ms | RSS 2.0 [application/xml] |  |
| Africa.com | AF | en | **KO** | 0 | 2027 ms | — | certificat TLS invalide |
| Jeune Afrique | AF | fr | OK | 30 | 1768 ms | RSS 2.0 [text/xml] |  |

## Maghreb

7/8 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| Hespress FR | MA | fr | OK | 10 | 1806 ms | RSS 2.0 [application/rss+xml] |  |
| Hespress AR | MA | ar | OK | 12 | 2071 ms | RSS 2.0 [application/rss+xml] |  |
| Aujourd'hui le Maroc | MA | fr | OK | 10 | 3178 ms | RSS 2.0 [application/rss+xml] |  |
| La Vie Eco | MA | fr | OK | 30 | 5346 ms | RSS 2.0 [application/rss+xml] |  |
| TSA Algerie | DZ | fr | OK | 10 | 2378 ms | RSS 2.0 [application/rss+xml] |  |
| El Watan | DZ | fr | **KO** | 0 | 4417 ms | — | ConnectionResetError : [WinError 10054] Une connexion existante a dû être fermée pa |
| Business News | TN | fr | OK | 10 | 6323 ms | RSS 2.0 [application/rss+xml] |  |
| Mosaique FM | TN | fr | OK | 40 | 1551 ms | RSS 2.0 [text/xml] |  |

## Monde arabe

6/7 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| Al Jazeera (arabe) | QA | ar | OK | 25 | 199 ms | RSS 2.0 [application/rss+xml] |  |
| Al Arabiya | AE | ar | **KO** | 0 | 99 ms | — | HTTP 403 |
| Asharq Al-Awsat | GB | ar | OK | 300 | 379 ms | RSS 2.0 [application/rss+xml] |  |
| France 24 (arabe) | FR | ar | OK | 24 | 356 ms | RSS 2.0 [application/rss+xml] |  |
| BBC Arabic | GB | ar | OK | 24 | 216 ms | RSS 2.0 [text/xml] |  |
| DW (arabe) | DE | ar | OK | 45 | 288 ms | RSS 1.0 (RDF) [text/xml] |  |
| Sky News Arabia | AE | ar | OK | 79 | 229 ms | RSS 2.0 [application/rss+xml] |  |

## Asie

5/5 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| Nikkei Asia | JP | en | OK | 50 | 1512 ms | RSS 1.0 (RDF) [application/rss+xml] |  |
| South China Morning Post | HK | en | OK | 50 | 3913 ms | RSS 2.0 [text/xml] |  |
| The Japan Times | JP | en | OK | 30 | 1816 ms | RSS 2.0 [application/rss+xml] |  |
| The Straits Times | SG | en | OK | 50 | 2197 ms | RSS 2.0 [application/rss+xml] |  |
| Channel News Asia | SG | en | OK | 20 | 3124 ms | RSS 2.0 [application/rss+xml] |  |

## Moyen-Orient

2/3 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| Al Jazeera | QA | en | OK | 25 | 1466 ms | RSS 2.0 [application/rss+xml] |  |
| Arab News | SA | en | **KO** | 0 | 1756 ms | — | HTTP 403 |
| Middle East Eye | GB | en | OK | 20 | 2699 ms | RSS 2.0 [application/rss+xml] |  |

## Monde

7/7 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| Google News (monde FR) | FR | fr | OK | 34 | 3239 ms | RSS 2.0 [application/xml] | liens de redirection Google |
| Google News (Afrique) | AF | fr | OK | 102 | 3030 ms | RSS 2.0 [application/xml] | liens de redirection Google |
| Google News (Maroc) | MA | fr | OK | 99 | 3066 ms | RSS 2.0 [application/xml] | liens de redirection Google |
| Google News (Algerie) | DZ | fr | OK | 92 | 2882 ms | RSS 2.0 [application/xml] | liens de redirection Google |
| Google News (Tunisie) | TN | fr | OK | 102 | 2668 ms | RSS 2.0 [application/xml] | liens de redirection Google |
| Google News (Canada) | CA | fr | OK | 100 | 2631 ms | RSS 2.0 [application/xml] | liens de redirection Google |
| Google News (Asie) | AS | fr | OK | 100 | 2602 ms | RSS 2.0 [application/xml] | liens de redirection Google |

## API

0/6 exploitables.

| Source | Pays | Langue | Statut | Items | Latence | Format | Remarque |
|---|---|---|---|---|---|---|---|
| GNews API | XX | multi | **KO** | 0 | — | — | Cle requise. 100 req/jour gratuit, 10 articles/requete. |
| NewsAPI.org | XX | multi | **KO** | 0 | — | — | Gratuit = developpement seulement, production interdite sans plan payant. |
| NewsData.io | XX | multi | **KO** | 0 | — | — | Bon sur Afrique / Moyen-Orient. 200 credits/jour gratuit. |
| Mediastack | XX | multi | **KO** | 0 | — | — | 500 req/mois gratuit, pas de production serieuse a ce prix. |
| Currents API | XX | multi | **KO** | 0 | — | — | 600 req/jour gratuit. |
| SerpApi (Google News) | XX | multi | **KO** | 0 | — | — | Payant. Contourne le ToS de Google News : risque juridique. |
