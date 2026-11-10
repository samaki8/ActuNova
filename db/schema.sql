-- ============================================================================
--  Plateforme d'actualite mondiale -- schema de reference (PostgreSQL 16+)
--  Dependances : pgvector, pg_trgm, unaccent
-- ----------------------------------------------------------------------------
--  Principes de conception :
--   1. Le brut (raw_items) est immuable : on peut rejouer les parseurs corriges
--      sans re-solliciter les serveurs des redactions.
--   2. La provenance d'une information est stockee, pas devinee : chaque pays
--      associe a un article porte sa methode et son niveau de confiance.
--   3. Tout contenu non distribuable est filtrable en SQL (colonne `licence`),
--      jamais par convention humaine.
--   4. Les identifiants publics (stories) sont stables et ne derivent jamais
--      du contenu, sinon chaque mise a jour casse les liens partages.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;   -- embeddings + recherche semantique
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- recherche floue sur les titres
CREATE EXTENSION IF NOT EXISTS citext;   -- e-mails insensibles a la casse
CREATE EXTENSION IF NOT EXISTS btree_gist; -- exclusion des chevauchements (une editoriale)

-- ---------------------------------------------------------------------------
-- 1. REFERENTIELS GEOGRAPHIQUES
-- ---------------------------------------------------------------------------

CREATE TABLE regions (
    code        text PRIMARY KEY,              -- M49 : '001','150','002','019','142'
    name_fr     text NOT NULL,
    name_en     text NOT NULL,
    parent_code text REFERENCES regions(code),
    level       text NOT NULL CHECK (level IN ('continent', 'subregion'))
);

COMMENT ON TABLE regions IS 'Decoupage ONU M49 : 5 continents + 22 sous-regions';

CREATE TABLE countries (
    iso2        char(2) PRIMARY KEY,
    iso3        char(3) NOT NULL UNIQUE,
    name_fr     text NOT NULL,
    name_en     text NOT NULL,
    region_code text NOT NULL REFERENCES regions(code),
    latitude    numeric(8, 5),
    longitude   numeric(8, 5),
    -- compteurs denormalises : evite un COUNT(*) jointure a chaque rendu de carte
    story_count     integer NOT NULL DEFAULT 0,
    story_count_24h integer NOT NULL DEFAULT 0
);

CREATE INDEX idx_countries_region ON countries(region_code);

-- ---------------------------------------------------------------------------
-- 2. SOURCES ET FLUX
-- ---------------------------------------------------------------------------

CREATE TABLE sources (
    id          bigserial PRIMARY KEY,
    slug        text NOT NULL UNIQUE,           -- 'lemonde', 'aljazeera'
    name        text NOT NULL,
    homepage    text,
    country_iso2 char(2) REFERENCES countries(iso2),
    lang        char(2) NOT NULL,               -- langue principale de publication
    tier        smallint NOT NULL DEFAULT 2 CHECK (tier BETWEEN 1 AND 3),
    -- 'rss_excerpt' : titre + extrait court autorises
    -- 'licensed'    : contrat de redistribution signe
    -- 'blocked_eu'  : distribution interdite dans l'UE (ex. RT)
    -- 'internal'    : lecture seule, jamais publie
    licence     text NOT NULL DEFAULT 'rss_excerpt'
                CHECK (licence IN ('rss_excerpt', 'licensed', 'blocked_eu', 'internal')),
    state_owned boolean NOT NULL DEFAULT false, -- transparence : media d'Etat
    active      boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON COLUMN sources.licence IS
  'Conditionne l affichage public et la publication video. Toute vue publique '
  'doit filtrer sur licence <> ''blocked_eu'' AND licence <> ''internal''.';

CREATE TABLE feeds (
    id              bigserial PRIMARY KEY,
    source_id       bigint NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    url             text NOT NULL UNIQUE,
    format          text NOT NULL DEFAULT 'auto'
                    CHECK (format IN ('auto', 'rss2', 'atom', 'rdf', 'json')),
    lang            char(2) NOT NULL,
    -- etat du poller : en base, pas en memoire (survit aux redemarrages)
    poll_interval_s integer NOT NULL DEFAULT 300,
    etag            text,
    last_modified   text,
    last_poll_at    timestamptz,
    last_ok_at      timestamptz,
    consecutive_errors smallint NOT NULL DEFAULT 0,
    last_error      text,
    -- geo par defaut du flux (un flux /world/europe -> '150')
    default_region  text REFERENCES regions(code),
    default_country char(2) REFERENCES countries(iso2),
    active          boolean NOT NULL DEFAULT true
);

CREATE INDEX idx_feeds_due ON feeds(active, last_poll_at) WHERE active;
CREATE INDEX idx_feeds_source ON feeds(source_id);

-- ---------------------------------------------------------------------------
-- 3. INGESTION : LE BRUT
-- ---------------------------------------------------------------------------

CREATE TABLE raw_items (
    id          bigserial PRIMARY KEY,
    feed_id     bigint NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    guid        text,                            -- <guid> ou <id> du flux
    payload     jsonb NOT NULL,                  -- item brut, champs texte preserves
    payload_hash char(64) NOT NULL,              -- sha256 : evite de retraiter 2 fois
    fetched_at  timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz,
    UNIQUE (feed_id, payload_hash)
);

CREATE INDEX idx_raw_pending ON raw_items(fetched_at) WHERE processed_at IS NULL;

CREATE TABLE ingest_runs (
    id          bigserial PRIMARY KEY,
    feed_id     bigint REFERENCES feeds(id) ON DELETE SET NULL,
    started_at  timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    http_status integer,
    items_seen  integer NOT NULL DEFAULT 0,
    items_new   integer NOT NULL DEFAULT 0,
    error       text
);

-- ---------------------------------------------------------------------------
-- 4. ARTICLES NORMALISES
-- ---------------------------------------------------------------------------

CREATE TABLE topics (
    id      smallserial PRIMARY KEY,
    slug    text NOT NULL UNIQUE,
    name_fr text NOT NULL,
    name_en text NOT NULL
);

CREATE TABLE articles (
    id           bigserial PRIMARY KEY,
    feed_id      bigint REFERENCES feeds(id) ON DELETE SET NULL,
    source_id    bigint NOT NULL REFERENCES sources(id),
    url          text NOT NULL,
    canonical_url text NOT NULL UNIQUE,          -- nettoyee des utm_*, fbclid, ancres
    title        text NOT NULL,
    excerpt      text,                           -- <= 150 caracteres, jamais plus
    lang         char(2) NOT NULL,
    published_at timestamptz,
    date_inferred boolean NOT NULL DEFAULT false, -- published_at absent du flux
    fetched_at   timestamptz NOT NULL DEFAULT now(),
    image_url    text,                           -- URL d'origine, jamais hebergee
    content_hash char(64) NOT NULL,              -- sha256(titre normalise + url)
    simhash      bigint,                         -- detection de quasi-doublons
    embedding    vector(1024),                   -- bge-m3 / e5-base
    topic_id     smallint REFERENCES topics(id),
    country_iso2 char(2) REFERENCES countries(iso2), -- pays principal (denormalise)
    status       text NOT NULL DEFAULT 'live'
                 CHECK (status IN ('live', 'blocked', 'error')),
    CONSTRAINT excerpt_len CHECK (excerpt IS NULL OR char_length(excerpt) <= 150)
);

CREATE INDEX idx_articles_recent ON articles(published_at DESC) WHERE status = 'live';
CREATE INDEX idx_articles_source ON articles(source_id, published_at DESC);
CREATE INDEX idx_articles_country ON articles(country_iso2, published_at DESC);
CREATE INDEX idx_articles_topic ON articles(topic_id, published_at DESC);
CREATE INDEX idx_articles_hash ON articles(content_hash);
CREATE INDEX idx_articles_title_trgm ON articles USING gin (title gin_trgm_ops);

-- recherche plein texte bilingue : on indexe les deux configurations
ALTER TABLE articles
  ADD COLUMN search_tsv tsvector
  GENERATED ALWAYS AS (
      setweight(to_tsvector('french', coalesce(title, '') || ' ' || coalesce(excerpt, '')), 'A') ||
      setweight(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(excerpt, '')), 'B')
  ) STORED;

CREATE INDEX idx_articles_fts ON articles USING gin (search_tsv);

-- index vectoriel : HNSW cosine, parametres adaptes a < 500k vecteurs
CREATE INDEX idx_articles_embedding ON articles
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE TABLE article_countries (
    article_id   bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    country_iso2 char(2) NOT NULL REFERENCES countries(iso2),
    confidence   real NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    -- 'source_default' | 'gazetteer' | 'feed_metadata' | 'editor'
    method       text NOT NULL,
    PRIMARY KEY (article_id, country_iso2)
);

CREATE INDEX idx_article_countries_lookup ON article_countries(country_iso2, article_id);

-- ---------------------------------------------------------------------------
-- 4 bis. MEDIAS DES SOURCES (video, audio)
-- ---------------------------------------------------------------------------
-- Quand une depeche arrive avec une video, on la GARDE — mais on integre le
-- lecteur du fournisseur, on ne telecharge jamais le fichier.
--
-- Re-heberger une video de presse est une contrefacon : AFP et Reuters vendent
-- leurs videos separement, sous contrat distinct. L'inclure dans notre MP4
-- revient a la re-heberger, donc c'est interdit aussi dans nos propres videos.
-- Seul usage autorise : <iframe> vers le lecteur officiel, sur la page
-- evenement, chargee au clic.

CREATE TABLE article_media (
    id            bigserial PRIMARY KEY,
    article_id    bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    kind          text NOT NULL DEFAULT 'video' CHECK (kind IN ('video', 'audio')),
    provider      text NOT NULL
                  CHECK (provider IN ('youtube', 'vimeo', 'dailymotion', 'x', 'instagram', 'facebook', 'self')),
    external_id   text NOT NULL,
    page_url      text NOT NULL,                  -- page publique du media
    embed_url     text NOT NULL,                  -- URL de lecteur, jamais un fichier
    thumbnail_url text,
    duration_s    integer,
    audio_locale  char(2),                        -- langue de la piste audio, affichee a l ecran
    -- 'embed_only' : lecteur du fournisseur. 'licensed' : contrat signe (rare).
    -- 'blocked' : ne pas afficher (retrait demande, source non distribuable).
    rights        text NOT NULL DEFAULT 'embed_only'
                  CHECK (rights IN ('embed_only', 'licensed', 'blocked')),
    created_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (article_id, provider, external_id)
);

CREATE INDEX idx_article_media_article ON article_media(article_id);

COMMENT ON TABLE article_media IS
  'Medias tiers integres par embed. Aucune colonne de stockage de fichier : si '
  'un chemin de fichier apparait un jour ici, c est une violation de la regle '
  '"jamais re-heberger". La page evenement charge l iframe au clic seulement.';

-- ---------------------------------------------------------------------------
-- 5. EVENEMENTS (CLUSTERS)
-- ---------------------------------------------------------------------------

CREATE TABLE stories (
    id           bigserial PRIMARY KEY,
    slug         text NOT NULL UNIQUE,           -- stable, lisible : "greve-sncf-2026-11"
    title_fr     text,
    title_en     text,
    title_de     text,
    title_es     text,
    title_it     text,
    summary_fr   text,
    summary_en   text,
    summary_de   text,
    summary_es   text,
    summary_it   text,
    first_seen   timestamptz NOT NULL DEFAULT now(),
    last_seen    timestamptz NOT NULL DEFAULT now(),
    article_count integer NOT NULL DEFAULT 0,
    source_count  integer NOT NULL DEFAULT 0,
    country_iso2 char(2) REFERENCES countries(iso2),
    topic_id     smallint REFERENCES topics(id),
    centroid     vector(1024),
    score        real NOT NULL DEFAULT 0,        -- rafraichi par worker (fenetre 48 h)
    status       text NOT NULL DEFAULT 'live'
                 CHECK (status IN ('live', 'archived', 'split'))
);

CREATE INDEX idx_stories_score ON stories(score DESC) WHERE status = 'live';
CREATE INDEX idx_stories_recent ON stories(last_seen DESC) WHERE status = 'live';
CREATE INDEX idx_stories_country ON stories(country_iso2, score DESC);
CREATE INDEX idx_stories_centroid ON stories USING hnsw (centroid vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

CREATE TABLE story_articles (
    story_id   bigint NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    article_id bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    similarity real,                             -- cosine au moment du rattachement
    is_lead    boolean NOT NULL DEFAULT false,   -- article dont le titre sert de reference
    PRIMARY KEY (story_id, article_id)
);

CREATE INDEX idx_story_articles_article ON story_articles(article_id);

-- ---------------------------------------------------------------------------
-- 5 bis. TRADUCTION DES SOURCES ARABOPHONES
-- ---------------------------------------------------------------------------
-- L'arabe n'est pas une langue d'interface : ce sont les sources arabes
-- (Hespress, Al Jazeera AR, Asharq Al-Awsat, BBC Arabic, Sky News Arabia...)
-- dont le titre est reformule vers la langue du lecteur.
--
-- Regle de conception : on traduit l'EVENEMENT (titre + synthese), pas chaque
-- article. Un evenement produit une reformulation par locale, coherente, au
-- lieu de 14 traductions qui se contredisent.
--
-- La reformulation n'est pas une traduction litterale : c'est une paraphrase
-- factuelle. Le titre original reste affiche et cliquable, avec attribution.

CREATE TABLE article_translations (
    article_id    bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    locale        char(2) NOT NULL CHECK (locale IN ('fr', 'en', 'de', 'es', 'it')),
    title         text NOT NULL,               -- paraphrase, pas traduction mot a mot
    excerpt       text,
    method        text NOT NULL DEFAULT 'llm'
                  CHECK (method IN ('llm', 'human', 'fallback_original')),
    translated_at timestamptz NOT NULL DEFAULT now(),
    reviewed_by   bigint REFERENCES users(id),
    reviewed_at   timestamptz,
    PRIMARY KEY (article_id, locale),
    CONSTRAINT tr_excerpt_len CHECK (excerpt IS NULL OR char_length(excerpt) <= 150)
);

CREATE INDEX idx_article_translations_locale ON article_translations(locale, translated_at DESC);

COMMENT ON TABLE article_translations IS
  'Reformulation des titres de sources non francophones (arabe en priorite). '
  'method = fallback_original signifie qu on affiche le titre d origine sans '
  'traduction : l interface doit alors le signaler, jamais le presenter '
  'comme traduit.';

-- Un evenement dont aucune source n est lisible par le lecteur ne doit pas
-- etre presente comme traduit : la vue publique expose l etat reel.
CREATE OR REPLACE VIEW v_story_locales AS
SELECT s.id AS story_id,
       loc.locale,
       CASE loc.locale
           WHEN 'fr' THEN s.title_fr
           WHEN 'en' THEN s.title_en
           WHEN 'de' THEN s.title_de
           WHEN 'es' THEN s.title_es
           WHEN 'it' THEN s.title_it
       END AS title,
       CASE loc.locale
           WHEN 'fr' THEN s.summary_fr
           WHEN 'en' THEN s.summary_en
           WHEN 'de' THEN s.summary_de
           WHEN 'es' THEN s.summary_es
           WHEN 'it' THEN s.summary_it
       END AS summary
FROM stories s
CROSS JOIN (VALUES ('fr'), ('en'), ('de'), ('es'), ('it')) AS loc(locale);

COMMENT ON VIEW v_story_locales IS
  'Aplatit les colonnes de traduction : l API lit une seule forme, et un titre '
  'manquant se voit immediatement (NULL) au lieu de retomber silencieusement '
  'sur le francais.';

-- ---------------------------------------------------------------------------
-- 5 ter. UNE EDITORIALE (selection manuelle)
-- ---------------------------------------------------------------------------
-- Le fil est algorithmique ; la une ne l'est pas. C'est un choix editorial,
-- assume et trace. Trois emplacements au maximum, et surtout une DATE DE FIN
-- OBLIGATOIRE : une une sans expiration est la facon la plus rapide de laisser
-- une actualite de trois semaines en haut du site un dimanche soir.

CREATE TABLE hero_slots (
    id          bigserial PRIMARY KEY,
    position    smallint NOT NULL CHECK (position BETWEEN 1 AND 3),
    story_id    bigint NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    starts_at   timestamptz NOT NULL DEFAULT now(),
    ends_at     timestamptz NOT NULL,
    pinned_by   bigint REFERENCES users(id),    -- qui a choisi : tracabilite
    note        text,                           -- pourquoi (utile en revue editoriale)
    created_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT hero_window CHECK (ends_at > starts_at),
    -- deux unes ne peuvent pas se chevaucher sur la meme position
    EXCLUDE USING gist (position WITH =, tstzrange(starts_at, ends_at) WITH &&)
);

COMMENT ON TABLE hero_slots IS
  'Selection manuelle de la une. ends_at est obligatoire : le hero expire seul '
  'et l API retombe sur le classement algorithmique. Un emplacement manuel qui '
  'n expire pas est un site qui affiche de la vieille actualite.';

CREATE INDEX idx_hero_window ON hero_slots(ends_at DESC);

CREATE OR REPLACE VIEW v_hero_now AS
SELECT position, story_id, starts_at, ends_at, pinned_by, note
FROM hero_slots
WHERE now() >= starts_at AND now() < ends_at;

-- ---------------------------------------------------------------------------
-- 6. UTILISATEURS ET PERSONNALISATION
-- ---------------------------------------------------------------------------

CREATE TABLE users (
    id            bigserial PRIMARY KEY,
    email         citext NOT NULL UNIQUE,
    password_hash text,                           -- NULL si connexion par lien magique
    locale        char(2) NOT NULL DEFAULT 'fr'
                  CHECK (locale IN ('fr', 'en', 'de', 'es', 'it')),
    digest_opt_in boolean NOT NULL DEFAULT false,
    digest_hour   smallint NOT NULL DEFAULT 7,    -- heure locale d'envoi
    created_at    timestamptz NOT NULL DEFAULT now(),
    last_seen_at  timestamptz,
    deleted_at    timestamptz                     -- suppression logique (RGPD : purge a 30 j)
);

CREATE TABLE user_interests (
    user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind    text NOT NULL CHECK (kind IN ('country', 'region', 'topic', 'source')),
    value   text NOT NULL,                        -- iso2 / code M49 / slug
    PRIMARY KEY (user_id, kind, value)
);

CREATE INDEX idx_interests_value ON user_interests(kind, value);

-- ---------------------------------------------------------------------------
-- 7. USINE VIDEO
-- ---------------------------------------------------------------------------

CREATE TABLE videos (
    id            bigserial PRIMARY KEY,
    -- 'short' : 45-75 s, vertical 9:16, UN evenement, reseaux sociaux
    -- 'brief' : 3-5 min, horizontal 16:9, PLUSIEURS evenements, site + YouTube + podcast
    format        text NOT NULL DEFAULT 'short' CHECK (format IN ('short', 'brief')),
    story_id      bigint REFERENCES stories(id),  -- NULL pour un brief (multi-evenements)
    -- langue de l'AUDIO. Une seule voix au lancement (fr) ; les autres langues
    -- sont des pistes de sous-titres, pas des doublages. Exception : le brief,
    -- produit en fr ET en en (voir commentaire plus bas).
    voice_locale  char(2) NOT NULL DEFAULT 'fr'
                  CHECK (voice_locale IN ('fr', 'en', 'de', 'es', 'it')),
    script_json   jsonb NOT NULL,                 -- plans + article_id de chaque phrase
    voice_id      text,
    duration_s    real,
    master_path   text,                           -- cle objet R2 du MP4 1080x1920
    master_landscape_path text,                   -- 1920x1080, image propre pour le site
    status        text NOT NULL DEFAULT 'draft'
                  CHECK (status IN ('draft', 'qa_failed', 'approved', 'published', 'rejected')),
    qa_report     jsonb,                          -- checks auto : duree, loudness, claims
    created_at    timestamptz NOT NULL DEFAULT now(),
    approved_by   bigint REFERENCES users(id),
    approved_at   timestamptz,
    -- un short porte sur un evenement ; un brief en couvre plusieurs
    CONSTRAINT video_format_story CHECK (
        (format = 'short' AND story_id IS NOT NULL)
        OR (format = 'brief' AND story_id IS NULL)
    )
);

CREATE INDEX idx_videos_story ON videos(story_id);
CREATE INDEX idx_videos_brief ON videos(format, voice_locale, created_at DESC)
  WHERE format = 'brief';

-- Chapitrage d'un brief : quels evenements, dans quel ordre, a quel instant.
-- C'est ce qui alimente les liens « aller a l'evenement » sur la page video,
-- les chapitres YouTube, et le maillage interne vers les pages evenement.
CREATE TABLE video_sources (
    video_id    bigint NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    story_id    bigint NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    position    smallint NOT NULL,                -- ordre dans le resume
    starts_at_s real NOT NULL,                    -- debut du chapitre, en secondes
    PRIMARY KEY (video_id, story_id),
    UNIQUE (video_id, position)
);

COMMENT ON TABLE video_sources IS
  'Chapitres dun brief : un evenement par chapitre, avec son instant de debut. '
  'Un short na pas de lignes ici (son story_id est sur videos).';

-- Le format est un diaporama de cartes : une image fixe, trois a six mots.
-- Une ligne = un plan. Les cartes sont generees par Pillow, assemblees par
-- ffmpeg. Aucune image tierce, donc aucune question de droits sur les visuels.
CREATE TABLE video_cards (
    video_id    bigint NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    position    smallint NOT NULL CHECK (position > 0),
    kicker      text,                             -- pays ou categorie, 2 mots max
    headline    text NOT NULL,                    -- 3 a 6 mots, cesures manuelles
    source_line text,                             -- attribution affichee sur la carte
    image_path  text,                             -- PNG 1080x1920, cle objet R2
    duration_s  real NOT NULL CHECK (duration_s BETWEEN 0.8 AND 6),
    PRIMARY KEY (video_id, position),
    CONSTRAINT card_kicker_len CHECK (kicker IS NULL OR char_length(kicker) <= 24),
    CONSTRAINT card_headline_len CHECK (char_length(headline) <= 64)
);

COMMENT ON COLUMN video_cards.headline IS
  'Trois a six mots, 64 caracteres maximum, coupure des lignes decassee a la '
  'main : un retour a la ligne automatique produit des veuves qui font amateur '
  'sur un ecran de telephone.';

-- Une voix, cinq jeux de sous-titres.
-- 'captions' = transcription fidele de la voix, dans sa langue (accessibilite).
-- 'subtitles' = resume traduit, cale sur les SEGMENTS du script, jamais sur les
--               mots : une traduction ne dure pas le meme temps que l original.
CREATE TABLE video_subtitles (
    video_id      bigint NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    locale        char(2) NOT NULL CHECK (locale IN ('fr', 'en', 'de', 'es', 'it')),
    kind          text NOT NULL CHECK (kind IN ('captions', 'subtitles')),
    vtt_path      text,                           -- cle objet R2 du fichier WebVTT
    segment_map   jsonb,                          -- [{seg, start, end, text}]
    chars_per_sec real,                           -- controle de lisibilite (cible <= 17)
    method        text NOT NULL DEFAULT 'llm' CHECK (method IN ('llm', 'human')),
    reviewed_by   bigint REFERENCES users(id),
    created_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (video_id, locale, kind)
);

COMMENT ON COLUMN video_subtitles.chars_per_sec IS
  'Vitesse de lecture du bloc le plus dense. Au-dela de 17, le spectateur '
  'saute le sous-titre : le bloc doit etre reecrit plus court, pas accelere.';

CREATE INDEX idx_video_subtitles_locale ON video_subtitles(locale, kind);

CREATE TABLE video_posts (
    video_id    bigint NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    platform    text NOT NULL CHECK (platform IN ('youtube', 'tiktok', 'instagram', 'x')),
    -- langue incrustee dans le MP4 publie. TikTok/Reels/Shorts n acceptent pas
    -- de pistes : une langue par post. YouTube accepte toutes les pistes.
    subtitle_locale char(2) CHECK (subtitle_locale IN ('fr', 'en', 'de', 'es', 'it')),
    remote_id   text,
    remote_url  text,
    status      text NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'uploading', 'published', 'failed', 'skipped')),
    attempts    smallint NOT NULL DEFAULT 0,
    last_error  text,
    published_at timestamptz,
    -- idempotence : un retry ne doit jamais creer un doublon public
    PRIMARY KEY (video_id, platform)
);

CREATE OR REPLACE VIEW v_public_stories AS
SELECT s.*
FROM stories s
WHERE s.status = 'live'
  AND EXISTS (
      SELECT 1
      FROM story_articles sa
      JOIN articles a ON a.id = sa.article_id
      JOIN sources src ON src.id = a.source_id
      WHERE sa.story_id = s.id
        AND src.licence IN ('rss_excerpt', 'licensed')
        AND a.status = 'live'
  );

COMMENT ON VIEW v_public_stories IS
  'Point d entree des lectures publiques : materialise la regle "aucun contenu '
  'non distribuable" au lieu de la laisser a la charge de chaque requete. '
  'Une story dont tous les articles viennent d une source bloquee est exclue.';
