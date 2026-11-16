# ARCHITECTURE

**Derived from source on 2026-11-14.** Source code outranks this file; if they disagree,
report it and re-derive the section. Facts only — no history, no plans (those go in ROADMAP).

## Overview
Flask app built by `create_app()` in `app.py` (`app:app` for gunicorn). At startup
`classes.load_catalog()` reads artists and songs from SQLite into memory (read-only
connection, image BLOBs stay in the DB) and `search.SearchIndex` builds a phonetic index.
Pages are Jinja2 + Bootstrap 5.3 (served locally, no CDN) + small vanilla JS files.

## Request / data flow
- `GET /` → artists sorted by song count → `index.html`
- `GET /artist/<slug>` → dict lookup in `Catalog`; `artist_songs.html` with the list and one shared player (`static/js/artist.js`); nothing open on phones, first song in the side player on wide screens. Old `/artist/<en_name>` 301 to the slug
- `GET /song/<slug>` → the same template with `song` set: that row is `aria-current`, and title, description, canonical and `og:*` are the song's. Clicking another row swaps the player and rewrites the URL with `replaceState` (no reload, no extra Back steps); folding the player on a phone restores `/artist/<slug>`. Old `/artist/x#<song slug>` links are upgraded to `/song/<slug>` by `artist.js`; old `/song/<English name>` 301 to `/song/<slug>`. The Share button copies (phones: shares) the `/song/<slug>` URL
- `GET /search?term=&artist=&limit=` → `SearchIndex.search` → JSON list (artists then songs)
- `GET /find?q=` → same index, HTML results page (no-JS / no-match fallback; the search box opens the best match directly)
- `GET /images/<artist slug>` → BLOB from DB on demand, `lru_cache`d, ETag + 7-day cache
- `GET/POST /admin` (password-only sign-in, `?next=` same-site paths only), `POST /admin/logout`, `GET /admin/session` → `{admin: bool}` (no-store). Session = signed cookie, 7 days since the last visit. No `ADMIN_PASSWORD` → all admin/PDF routes 404 and no PDF buttons are rendered
- `GET /pdf/<song_id>/<sheet|tab>` → not admin: 302 to `/admin?next=…` (before any lookup); admin: 302 to a 5-minute R2 presigned URL (inline, filename from the *current* names); no key → 404; R2 env missing → 503. The artist page shows it inside the player (iframe `#pdf-frame` replaces the video; "Open in new tab" beside it), so CSP `frame-src` allows `'self'` (the `/pdf` hop) and `https://<R2_ACCOUNT_ID>.r2.cloudflarestorage.com` (added only when that env var is a 32-hex id)
- `/healthz`, `/robots.txt`, `/sitemap.xml` (home + every artist + every song)

## Data model (schema version 4, `PRAGMA user_version`)
| Entity | Table | Key relations | Owner module |
|---|---|---|---|
| Artist | `artists` (artist_id, slug UNIQUE, en_name UNIQUE, gr_name, artist_img BLOB) | 79 rows | `classes.py` |
| Song | `songs` (song_id, artist_id FK, slug UNIQUE, en_name, gr_name, video_id, demo_id, score_key, tab_key) | 1048 rows; `idx_songs_artist` | `classes.py` |

`video_id` = original recording, `demo_id` = bouzouki sheet-music lesson (both YouTube ids).
`score_key`/`tab_key` = R2 object keys of the sheet/tab PDF: random `pdf/<12 chars a-z2-7>.pdf`, made once by `pdf_sync.py` and kept in the DB, unrelated to names and ids; NULL = no PDF. The page HTML never contains a key.
Slugs: `textkeys.make_slug` (≤3 significant words, ≤26 chars), duplicates get `-2`.

## Key modules
| Path | Responsibility |
|---|---|
| `app.py` | `create_app`: routes, CSP/security headers, rate limits, error handlers |
| `classes.py` | `Artist`, `Song`, `Catalog`, `load_catalog`, `load_artist_image` |
| `storage.py` | R2 client (boto3, lazy import), `presigned_url`, `content_disposition` |
| `pdf_sync.py` | CLI `plan / apply / verify / prune`: Patreon folders → R2 + `songs.*_key`; logic and how to add mp3/mid/sib in `scripts/pdf_audit/UPLOAD_LOGIC.md` |
| `textkeys.py` | `phonetic_key` (Greek/Latin spelling → one key), `make_slug` |
| `search.py` | `SearchIndex`: word/prefix/substring scoring, typo fallback (difflib) |
| `db_migrate.py`, `migrations/` | Versioned, reversible schema changes |
| `templates/`, `static/` | `static/fonts/` = Inter (OFL); `base.html` + `_macros.html`; `css/styles.css`; `js/search.js`, `artist.js`, `theme.js`; icons: `img/logo.svg` (hero bouzouki), `favicon.ico` + `img/favicon-32.png`, `icon-192/512.png`, `apple-touch-icon.png` (an orange guitar pick, shaped like the developer's photo, on a deep-blue tile; sources and attempts in `design/favicon/`), `site.webmanifest` |
| `tests/` | pytest suite (runs against the real catalog and temp legacy DBs) |
| `crawling_scripts/`, `db_games.py`, `automation.py`, `images.ipynb`, `jsons/`, `artists.csv`, `images/` | Offline data collection (Selenium); not imported by the app. `images/` is git-ignored |

## API surface
6 routes + favicon/health/robots/sitemap in `app.py`. Limits: 600/hour default per IP, `/search`
90/min, `/images` 300/min; static and `/healthz` exempt. In-memory storage unless
`RATELIMIT_STORAGE_URI` is set (counts are per gunicorn worker).

## External services
| Service | Used for | Config (env var names only — never values) |
|---|---|---|
| YouTube (nocookie embeds) | Both videos on song pages | — |
| Cloudflare R2 (private bucket `bouzouki-rebetiko`) | Sheet-music/tab PDFs, served only via presigned URLs to the admin | `R2_ACCOUNT_ID`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` |

Env: `ADMIN_PASSWORD`, `FLASK_SECRET_KEY`, `PORT`, `LOG_LEVEL`, `TRUST_PROXY_HOPS`, `DATABASE_PATH`, `RATELIMIT_STORAGE_URI`.

## Environments & deploy
| Env | Branch | DB | Notes |
|---|---|---|---|
| local | — | `instance/music.db` (tracked) | `uv run python app.py` |
| production | `master` auto-deploys to Railway | same file, shipped with the code | `railway.json`: gunicorn `app:app`, health `/healthz`; set `TRUST_PROXY_HOPS=1` |

## Verification commands
`uv run pytest -q`. UI: run the app and check pages in a browser (headless Chrome
screenshots were used; no browser test suite).

## Railway (production) — facts
Project `bouzouki-website` id `75ef6876-6dc5-40e0-9f00-445cc86137b1`, environment `production` `0b99f4ed-88e8-4c03-8ce9-12bbd6b7a466`, service `web` `6f318ef4-dd9c-4b20-939e-41cbc31b6e74`. Builder RAILPACK, start `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`, health `/healthz`, region `europe-west4-drams3a`, edge CDN on. Variables: `FLASK_SECRET_KEY`, `TRUST_PROXY_HOPS=1`. Settings live in Railway, not in git (`railway.json`/`Procfile` mirror them). Every push to `master` redeploys; expect a short "Application not found" while it swaps.

## Sheet-music PDFs on Cloudflare R2
Built: schema, admin sign-in, `/pdf`, buttons (lock until signed in; `artist.js` asks `/admin/session`, so the cached HTML is identical for everyone), `pdf_sync.py` (tested against a fake S3). Not done: the real upload (needs D: mounted in WSL) — plan in `.claude/plans/pdf-upload.md`.
