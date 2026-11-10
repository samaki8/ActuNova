# Avant le déploiement

## Faut-il une application locale ?

**Non.** Rien de ce que fait le produit ne doit tourner sur un ordinateur personnel : ni le site,
ni la collecte, ni la publication. Une machine éteinte, en veille ou derrière une connexion
domestique, c'est un site qui tombe et un bulletin qui ne part pas — sans que personne ne le voie.

Ce qu'il faut, ce sont **cinq briques hébergées** :

| Brique | Où elle tourne | Pourquoi pas en local |
|---|---|---|
| Site web (Next.js) | Serveur ou hébergeur managé, derrière un CDN | Il doit répondre 24 h/24, et vite, partout |
| Base PostgreSQL | Managé (Neon, Supabase, Railway) | Sauvegardes et disponibilité ne sont pas un travail d'amateur |
| Collecte (poller) | Le même serveur, en tâche planifiée | Toutes les 10 minutes, sans intervention |
| Pipeline vidéo | Le même serveur, ou GitHub Actions | Rendu quotidien, sans laptop allumé |
| Stockage médias | Cloudflare R2 ou S3 | Les vidéos doivent être servies par un CDN |
| **Interface d'administration** | **Une page du site**, protégée par mot de passe | C'est là qu'on choisit la une et qu'on valide les vidéos — pas une application de bureau |

Autrement dit : **une application de bureau n'a aucune raison d'exister**. Ce qui ressemble à un
« outil local » est en réalité une page d'administration hébergée avec le site.

### Et les réseaux sociaux ?

Ce sont des appels HTTP à des API, depuis le serveur, avec des jetons stockés côté serveur :

- **YouTube** : OAuth 2.0, `videos.insert`, plus les pistes de sous-titres par langue.
- **TikTok** : Content Posting API — **l'application doit être auditée par TikTok**, sinon les
  publications restent en brouillon privé.
- **Instagram** : Graph API, vidéo accessible par URL publique, compte Business obligatoire.
- **X** : API v2 payante, upload média séparé.

Aucune de ces intégrations ne demande d'application installée. Toutes demandent des **comptes
développeur et des validations**, et c'est là que se trouve le vrai délai.

## La checklist, dans l'ordre

### 1. Bloquant juridique — à faire avant toute mise en ligne

- [ ] **Statut juridique** (micro-entreprise suffit pour démarrer) et mentions légales complètes.
- [ ] **CGU et politique de confidentialité** rédigées, pas copiées d'un modèle générique.
- [ ] **Validation par un avocat** du dispositif d'extraits (≤ 150 caractères, lien sortant) et de
      la **reformulation** des sources arabophones. C'est le point le plus exposé du projet.
- [ ] **Procédure de retrait** : adresse dédiée, engagement de 48 h, journal des demandes.
- [ ] **RGPD** : registre des traitements, base légale de la newsletter, sous-traitants listés,
      durée de conservation des e-mails.
- [ ] **Transparence du financement** : page « comment nous sommes financés », `ads.txt` si régie.

### 2. Bloquant technique

- [ ] **Nom de domaine** et certificat HTTPS (Let's Encrypt suffit).
- [ ] **Sauvegardes quotidiennes** de la base, chiffrées, hors du serveur — **et un test de
      restauration**. Une sauvegarde jamais restaurée n'est pas une sauvegarde.
- [ ] **Supervision** : alerte si un flux échoue 3 fois, si le pipeline a plus de 30 minutes de
      retard, si un rendu vidéo échoue. Sans alerte, on découvre la panne par un lecteur.
- [ ] **Secrets hors du dépôt** : jetons OAuth, clés API, mot de passe base en variables
      d'environnement. Un `.env` commité est la fuite la plus banale qui existe.
- [ ] **Limitation de débit** sur `/v1/search` et sur le formulaire de contact.
- [ ] `robots.txt`, `sitemap.xml`, `llms.txt` déployés à la racine (déjà écrits dans `seo/`).

### 3. Bloquant plateformes — le chemin critique

Ces validations prennent des **semaines**. À lancer en premier, même si le site n'est pas prêt :

- [ ] **Compte développeur TikTok** + demande d'audit de l'application.
- [ ] **Projet Google Cloud** + OAuth + demande d'extension de quota YouTube (10 000 unités/jour
      par défaut, un upload en coûte 1 600).
- [ ] **Compte Instagram Business** relié à une page Facebook, application Meta en revue.
- [ ] **Accès API X** (offre payante) et vérification du tier.
- [ ] **Compte développeur OpenAI/Anthropic** (ou autre) pour la génération de scripts et de
      reformulations — avec un plafond de dépense configuré dès le départ.

### 4. Peut attendre les premières semaines

- Comptes utilisateurs, newsletter, personnalisation.
- Carte 3D et clustering avancé.
- Toutes les locales : FR seul au lancement est un choix défendable.
- Thème sombre, s'il n'est pas déjà fait.

## Le piège à éviter

**Ne pas déployer la vidéo et le site en même temps.** Le site peut vivre avec un contenu imparfait ;
une vidéo publiée avec une erreur factuelle reste en ligne, et sur un compte neuf elle coûte la
crédibilité de la chaîne. Le site d'abord, la vidéo ensuite, une fois le regroupement fiable.

Et une règle de sécurité : **les vingt premières vidéos passent par une validation humaine**
(cf. `ARCHITECTURE.md` § ADR-06). Automatiser avant d'avoir mesuré le taux d'erreur revient à
publier à l'aveugle.
