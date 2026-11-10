# Positionnement — moteurs de recherche et moteurs IA

**Version 1.0 · 5 novembre 2026** · Complète [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## 0. La thèse en dix lignes

Un agrégateur d'actualité ne se positionne pas comme un journal. Il ne peut pas gagner sur
« l'info », il peut gagner sur **la comparaison** : personne d'autre ne montre, sur la même page,
ce que disent quatorze rédactions du même fait, avec les chiffres et les dates alignés.

C'est aussi exactement ce qu'un moteur de réponse IA a besoin de citer : une page qui **répond
directement**, avec des **faits datés**, des **entités nommées** et une **synthèse originale**.
Un mur de liens ne se cite pas ; une page qui répond, oui.

Trois convictions qui structurent tout ce document :

1. **Le trafic de recherche informationnel va baisser**, mécaniquement, à cause des réponses
   générées. Le bon objectif n'est donc pas « plus de clics », c'est **être la source citée** —
   et convertir la visite en retour direct (newsletter, marque).
2. **La page événement est l'actif SEO**, pas la page d'accueil. C'est la seule qui contienne de
   l'information que personne d'autre ne publie.
3. **L'indexation est un problème de qualité, pas de volume.** 2 000 pages pays vides détruisent
   un site plus sûrement qu'elles ne le font décoller.

---

## 1. Ce que le site peut espérer — et ce qu'il ne peut pas

### Ce à quoi il n'a pas droit

| Espoir courant | Réalité |
|---|---|
| Apparaître dans **Google News** | Le Publisher Center est réservé aux éditeurs de contenu original. Un agrégateur n'y est pas éligible. Ne pas bâtir de plan dessus. |
| Apparaître dans **Discover** | Même condition : contenu original, politique éditoriale, entité identifiée. Possible plus tard, via le bulletin vidéo et les synthèses, pas au lancement. |
| Battre Le Monde sur « Maroc » | Aucune chance. Les requêtes de marque et les gros mots-clés pays sont verrouillés par les éditeurs historiques. |
| Vivre du clic de recherche | En baisse structurelle sur l'information. C'est un canal d'acquisition, pas un modèle. |

### Ce qui est réellement atteignable

| Gisement | Exemple de requête | Pourquoi ça marche |
|---|---|---|
| **Longue traîne datée** | « ce qui s'est passé au Soudan cette semaine » | Personne ne structure l'actualité par fenêtre temporelle et par pays. |
| **Comparaison de sources** | « ce que disent les médias sur la réforme des retraites » | C'est littéralement le produit. Aucun concurrent direct. |
| **Citations IA** | « résume l'actualité au Maghreb aujourd'hui » | Les moteurs de réponse cherchent des pages synthétiques et fraîches. |
| **Requêtes d'entité** | « situation politique au Mali novembre 2026 » | Une page pays bien construite devient la référence de fait. |
| **YouTube** | « actualité Maroc du 5 novembre » | Le bulletin vidéo est indexé, et les Shorts apparaissent dans Google. |

Le positionnement réaliste : **devenir la page que Google et les IA citent quand la question porte
sur « qui dit quoi » et « quoi de neuf » sur une zone donnée.**

---

## 2. La thèse de contenu : une page qui ajoute quelque chose

C'est le point de survie. La politique anti-spam de Google vise explicitement le **contenu
aspiré** (« scraped content ») : du contenu copié d'autres sites sans valeur ajoutée. Un
agrégateur est, par définition, dans le collimateur. La seule défense est que chaque page
contienne **quelque chose qui n'existe nulle part ailleurs**.

### Ce que chaque page événement doit contenir

| Bloc | Contenu | Pourquoi |
|---|---|---|
| **Réponse en 3 phrases** | Synthèse écrite par nous, 40-60 mots, en tête de page | C'est le bloc que les moteurs de réponse extraient |
| **Chronologie** | 4 à 8 entrées horodatées, multi-sources | N'existe nulle part ailleurs : elle est le produit de notre regroupement |
| **Qui dit quoi** | Tableau : rédaction, angle, ce qu'elle affirme, lien | Le bloc le plus cité par les IA, et le plus utile au lecteur |
| **Chiffres clés** | 2 à 4 chiffres, chacun attribué à sa source | Les LLM citent les pages qui contiennent des nombres datés |
| **Angles divergents** | Une phrase quand deux sources se contredisent | C'est la valeur éditoriale, et un signal d'originalité fort |

**Interdit structurel** : une page événement qui ne serait qu'une liste de titres et de liens.
Elle sera filtrée comme contenu aspiré, et elle ne sera jamais citée. Si le pipeline n'a pas assez
de matière pour remplir ces blocs, la page ne doit pas être indexée.

### La règle des 150 caractères

On ne republie jamais l'article (cf. `ARCHITECTURE.md` § 4.1). Mais attention : un extrait de
150 caractères **par source**, multiplié par quatorze sources, c'est 2 100 caractères de texte
d'autrui sur la page. La règle doit être : **un extrait court par événement**, pas par source.
Les autres sources sont représentées par leur titre, leur angle en trois mots, et un lien.

---

## 3. Architecture des URL et de l'indexation

### Arborescence

```
/fr/                                   accueil (carte + fil)
/fr/evenement/{slug}-{id}              LA page qui compte (stable, jamais réécrite)
/fr/pays/{iso2}                        page pays
/fr/pays/{iso2}/{theme}                page pays + thème (indexée sous condition)
/fr/region/{code-m49}                  continent / sous-région
/fr/videos                             la rubrique vidéo
/fr/videos/{slug}                      une vidéo
/fr/sources                            le catalogue de sources (page de transparence)
/en/...  /de/...  /es/...  /it/...      miroirs des quatre autres locales
```

Règles :

- **L'identifiant de l'événement est stable.** Le slug peut changer, l'URL redirige en 301.
  Un événement qui vit trois jours ne doit pas changer d'adresse trois fois.
- **Les filtres ne sont pas des pages.** `?country=FR&sort=recent` : `noindex, follow` et
  `rel=canonical` vers la page propre. On ne les bloque **pas** dans `robots.txt` — un moteur qui
  ne peut pas explorer une URL ne peut pas voir son canonical. C'est l'erreur la plus fréquente.
- **Les pages pays ne sont indexées que si elles ont de la matière** : au moins 10 événements sur
  30 jours. En dessous, `noindex, follow`. Sans ce garde-fou, on crée 2 340 pages vides
  (195 pays × 12 thèmes) et on ressemble à un annuaire spam — ce que Google appelle une *doorway
  page*.
- **hreflang obligatoire** : `fr`, `en`, `de`, `es`, `it` et `x-default` sur chaque page, en
  entête et dans le sitemap, avec des liens de retour réciproques — chaque page déclare toutes
  les autres, y compris elle-même. Un hreflang sans retour est ignoré.

### Cinq langues : ce qui change pour l'indexation

C'est la partie qui se rate le plus souvent, parce qu'elle a l'air simple.

- **Jamais de redirection par IP.** Googlebot explore depuis les États-Unis : une redirection
  géographique lui sert la version anglaise à la place de la française, et la page n'est jamais
  indexée. On détecte `Accept-Language` **côté client**, on propose un bandeau, et on laisse
  l'utilisateur choisir. L'URL reste la source de vérité.
- **Slugs en ASCII, toujours.** `…/es/evento/huelga-transportes-marruecos-20261105` — jamais de
  caractère non latin brut dans l'URL. L'encodage pourcent-encodé casse le partage, les
  statistiques et la lecture des journaux serveur. On garde le slug latin, éventuellement
  localisé par le segment de section, pas par le titre.
- **Une traduction non produite ne s'indexe pas.** Si `/it/` sert du contenu français faute de
  reformulation, la page passe en `noindex, follow` et propose la version d'origine. Servir du
  français sous une balise `lang="it"` est du contenu dupliqué mal étiqueté : le pire des deux.
- **`lang` doit dire la vérité, y compris en ligne.** Une page française qui affiche un titre
  arabe original garde `lang="fr"` sur la page, et l'encadre de `<bdi lang="ar" dir="rtl">`.
  L'attribut global ne ment jamais, le fragment est déclaré pour ce qu'il est.
- **Un titre reformulé n'est pas un titre original.** La page doit afficher « reformulé
  automatiquement » près du titre traduit. Ce n'est pas seulement une question d'honnêteté : c'est
  ce qui évite qu'un contenu généré soit évalué comme du contenu de presse original, et ce qui
  protège l'attribution.
- **La qualité prime sur la couverture.** La politique anti-spam de Google vise l'abus de contenu
  à l'échelle (« scaled content abuse ») : des centaines de reformulations automatiques par jour,
  relues par personne, en relèvent. On reformule peu, on relit les événements les plus vus, et on
  n'indexe que ce qui a été relu.

C'est aussi une raison de plus de ne pas générer de pages pays vides : multiplier par cinq
locales un contenu mince, c'est multiplier le problème par cinq.

### Sitemaps

Quatre fichiers, un index :

| Fichier | Contenu | Fréquence |
|---|---|---|
| `sitemap-evenements.xml` | événements des 7 derniers jours + les 500 plus consultés | régénéré toutes les 10 min |
| `sitemap-pays.xml` | pages pays indexables uniquement | quotidien |
| `sitemap-videos.xml` | vidéos publiées, avec `video:thumbnail_loc` | à chaque publication |
| `sitemap-pages.xml` | accueil, sources, à propos, mentions | mensuel |

`lastmod` doit être **réel** (date de dernière modification du contenu), pas la date de
génération. Un `lastmod` qui ment est ignoré, et fait perdre la confiance sur tout le fichier.

---

## 4. Technique : ce qui se code une fois

### Rendu et performance

- **Rendu serveur** pour tout le contenu (RSC / ISR). Un fil d'actualité rendu côté client n'est
  pas indexé de façon fiable.
- **Core Web Vitals** : LCP < 2,5 s, CLS < 0,1, INP < 200 ms. Le CLS est directement lié aux
  emplacements publicitaires (`ARCHITECTURE.md` § 10.5) : un slot non réservé casse la page.
- **Pas d'AMP.** Le format est mort, la vitesse suffit.

### Données structurées

Quatre schémas, un par type de page. Les fichiers prêts à l'emploi sont dans
[`seo/jsonld/`](seo/jsonld/) et l'entête complète dans [`seo/head.html`](seo/head.html).

| Page | Type schema.org | Point d'attention |
|---|---|---|
| Accueil | `WebSite` + `SearchAction` + `NewsMediaOrganization` | La `SearchAction` fait apparaître la recherche dans Google |
| Événement | `Article` + `citation[]` | `citation` pointe les sources : c'est honnête, et ça documente l'agrégation |
| Vidéo | `VideoObject` + `transcript` | Le transcript est ce qui fait indexer le contenu parlé |
| Pays / région | `CollectionPage` + `about: Country` | Rattache la page à une entité, pas à un mot-clé |

Ce qu'on **ne** fait pas : baliser chaque article source en `NewsArticle`. Ce n'est pas notre
contenu, et un balisage mensonger expose à une action manuelle.

### Liens sortants : en `follow`

Réflexe répandu chez les agrégateurs : mettre `nofollow` sur tout ce qui sort, « pour ne pas
perdre de jus ». C'est une erreur. Un lien éditorial vers la source d'une information est un
signal de confiance (E-E-A-T), pas du spam de liens. On garde `rel="noopener"` pour la sécurité,
on ne met **pas** `nofollow`.

### Indexation accélérée

- **IndexNow** : un ping à Bing (et Yandex) à chaque publication. C'est gratuit, instantané, et
  c'est important ici pour une raison précise : **ChatGPT Search s'appuie sur l'index de Bing**.
  Être indexé vite chez Bing, c'est être citable vite dans ChatGPT.
- **Google Indexing API** : ne concerne que les offres d'emploi et les diffusions en direct.
  Inutile ici. La Search Console suffit (soumission de sitemap + inspection d'URL).

---

## 5. Moteurs IA : comment on se fait citer

### Les trois tuyaux

| Moteur | D'où vient sa réponse | Ce qu'il faut faire |
|---|---|---|
| **AI Overviews** (Google) | L'index Google classique | Le SEO classique s'applique : c'est la même bataille |
| **ChatGPT Search / Copilot** | Index Bing + crawl direct | Bing Webmaster Tools + IndexNow + `OAI-SearchBot` autorisé |
| **Perplexity / Claude** | Crawl direct + index partenaires | `PerplexityBot` et `ClaudeBot` autorisés, pages stables |

### Les sept propriétés d'une page citée

1. **Une réponse directe en tête.** 40 à 60 mots qui répondent à la question, avant tout le
   reste. Un moteur de réponse extrait ce paragraphe ; s'il n'existe pas, il prend celui du
   concurrent.
2. **Des faits datés et chiffrés.** « 14 rédactions », « depuis le 3 novembre », « 240 morts
   selon X ». Les nombres et les dates sont ce qui distingue une source citable d'un commentaire.
3. **Des entités nommées.** Écrire « le Mali », « Bamako », « l'ONU », pas « le pays » ni « la
   capitale ». Une IA doit pouvoir rattacher la page à une entité.
4. **Une structure extractible.** Des `h2` qui sont des questions, des tableaux, des listes.
   Un pavé de prose ne se cite pas.
5. **Une fraîcheur visible.** `dateModified` juste, et à l'écran « mis à jour il y a 12 minutes ».
6. **De l'unicité.** Si douze sites disent la même chose, l'IA cite celui qui ajoute la synthèse,
   la chronologie ou la contradiction.
7. **Une autorité externe.** Être cité par d'autres augmente la probabilité d'être cité. C'est
   lent, et ça ne s'achète pas.

### Le gabarit à imposer dans le CMS

Chaque page événement commence par :

```
H1  {Titre de l'événement}
    Résumé en 3 phrases …                       <- 40-60 mots, écrit par nous
    Mis à jour il y a 12 min · 14 rédactions · Maroc

H2  Ce qu'il faut retenir
    - 3 à 5 puces, chacune avec un fait daté
H2  Chronologie
    - liste horodatée
H2  Qui dit quoi
    - tableau : rédaction | angle | affirmation | lien
H2  Les chiffres
    - 2 à 4 chiffres sourcés
```

### `llms.txt` : à faire, sans en attendre de miracle

Le fichier [`seo/llms.txt`](seo/llms.txt) est proposé à la racine. Il décrit le site et ses pages
clés aux modèles. **Soyons honnêtes : ce n'est pas un standard reconnu**, aucun moteur majeur n'a
confirmé l'exploiter, et son effet mesurable est probablement nul aujourd'hui. Il coûte dix
minutes, il ne nuit pas, et il documente le site pour les humains qui le liront. C'est un
pari à faible coût, pas une stratégie.

Ce qui marche vraiment pour les IA, c'est le contenu ci-dessus. Pas un fichier magique.

### Autoriser ou bloquer les crawlers IA ?

**Autoriser.** Sur un agrégateur, la citation *est* le produit : être la source d'une réponse
générée vaut plus que le clic perdu. Bloquer `GPTBot` revient à disparaître des réponses sans
rien protéger, puisqu'on ne publie aucun texte intégral.

La distinction utile, si le choix se discute plus tard :

| Crawler | Rôle | Recommandation |
|---|---|---|
| `OAI-SearchBot` | Index de ChatGPT Search | **Autoriser** — c'est la citation |
| `ChatGPT-User` | Requête déclenchée par l'utilisateur | Autoriser |
| `GPTBot` | Entraînement des modèles | Autoriser (aucun coût, visibilité d'entité) |
| `PerplexityBot`, `ClaudeBot` | Index / réponse | Autoriser |
| `Google-Extended` | Gemini (entraînement et grounding) | Autoriser — n'affecte pas le référencement Google |
| `CCBot` (Common Crawl) | Jeux de données ouverts | Autoriser, neutre |

---

## 6. YouTube : le deuxième moteur de recherche

Le bulletin vidéo est un actif SEO à part entière, et souvent plus rapide à faire décoller que le
site.

- **Titre = question.** « Ce qui s'est passé au Sahel cette semaine » plutôt que « Bulletin du
  5 novembre ». Les gens cherchent des questions.
- **Description = synthèse + sources + chapitres.** Les trois premières lignes sont indexées et
  affichées.
- **Sous-titres FR et EN** déposés (on les a déjà : ce sont les `.vtt` du pipeline).
- **Chapitres** (horodatages) : ils apparaissent dans les résultats Google.
- **Shorts** : indexés dans Google, format découverte. Un Short par événement majeur, avec un
  lien vers la page événement.

---

## 7. Mesure

| Outil | Ce qu'on y regarde |
|---|---|
| Search Console | impressions, CTR par type de page, requêtes émergentes, couverture |
| Bing Webmaster Tools | indispensable : c'est l'index de ChatGPT |
| Analytics | sessions avec `referrer` = `chatgpt.com`, `perplexity.ai`, `gemini.google.com`, `copilot.microsoft.com`, `claude.ai` |
| Panel de prompts | 20 questions types posées chaque mois à ChatGPT et Perplexity, en relevant si le site est cité |
| Journaux serveur | passages de `OAI-SearchBot`, `PerplexityBot` : est-on crawlé ? |

### Les cinq indicateurs qui comptent

1. **Pages citées par une IA** (panel mensuel) — l'indicateur directeur.
2. **Part de citations** sur les 20 prompts suivis.
3. **Clics de recherche** sur les requêtes événementielles (pas le total).
4. **Taux de retour direct** — la seule protection contre la baisse du clic de recherche.
5. **Inscriptions newsletter issues de la recherche** — la conversion qui rend le canal rentable.

---

## 8. Plan 90 jours

| Semaine | Action | Résultat attendu |
|---|---|---|
| 1-2 | Gabarit de page événement (résumé, chronologie, qui dit quoi) + JSON-LD | Les pages sont citables avant d'être nombreuses |
| 2-3 | `robots.txt`, sitemaps, hreflang, IndexNow, Search Console + Bing | Indexation propre |
| 3-4 | Garde-fou `noindex` sur pages pays vides et filtres | Zéro page mince dans l'index |
| 4-6 | 200 premières pages événement de qualité, maillage interne depuis la carte | Le socle indexable existe |
| 6-8 | Publication YouTube quotidienne + chapitres + sous-titres | Deuxième canal actif |
| 8-10 | Panel de prompts, première mesure de citations IA | On sait où on en est |
| 10-12 | Itération sur les 20 pages les plus citées / les plus vues | Le gabarit s'affine sur des données réelles |

---

## 9. Les pièges qui tuent

| Piège | Ce qui se passe | Parade |
|---|---|---|
| Page événement = liste de liens | Filtrage « scraped content » | Les cinq blocs du § 2, ou pas d'indexation |
| 2 340 pages pays générées d'un coup | *Doorway pages*, site dévalué | Seuil de 10 événements / 30 jours |
| `nofollow` sur tous les liens sortants | Perte de signal de confiance | `follow` + `noopener` |
| Bloquer les filtres dans `robots.txt` | Le canonical n'est jamais lu | `noindex` + canonical, pas de blocage |
| Contenu FR et EN identiques | Duplication | Vraie traduction + hreflang |
| `lastmod` = date de génération | Sitemap ignoré | Date de modification réelle |
| Publier 50 vidéos par jour | Signal de spam, aucune rétention | 3 à 5, choisies |
| Croire que `llms.txt` fait le travail | Déception | Le contenu fait le travail |

---

## 10. Ce qu'il ne faut pas attendre

- **Pas de trafic massif la première année.** Une page événement met des mois à se positionner,
  et l'actualité est le domaine le plus concurrentiel du web.
- **Pas de Google News.** L'éligibilité n'existe pas pour un agrégateur.
- **Pas de revenus publicitaires significatifs avant un an** de trafic qualifié.
- **Pas de protection contre les réponses IA.** Elles vont capter une partie du clic. La seule
  réponse est d'être cité, et de faire revenir par la newsletter et par la vidéo.

---

## Annexes

- [`seo/robots.txt`](seo/robots.txt) — politique de crawl, moteurs de recherche et crawlers IA.
- [`seo/llms.txt`](seo/llms.txt) — description du site pour les modèles.
- [`seo/head.html`](seo/head.html) — entête HTML complète : hreflang, canonical, Open Graph, JSON-LD.
- [`seo/jsonld/`](seo/jsonld/) — les quatre schémas, prêts à adapter.
