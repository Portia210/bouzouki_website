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
- `GET /artist/<slug>`, `/song/<slug>` → dict lookup in `Catalog`; old `/…/<en_name>` URLs 301 to the slug
- `GET /search?term=&artist=&limit=` → `SearchIndex.search` → JSON list (artists then songs)
- `GET /find?q=` → same index, HTML results page
- `GET /images/<artist slug>` → BLOB from DB on demand, `lru_cache`d, ETag + 7-day cache
- `/healthz`, `/robots.txt`, `/sitemap.xml`

## Data model (schema version 2, `PRAGMA user_version`)
| Entity | Table | Key relations | Owner module |
|---|---|---|---|
| Artist | `artists` (artist_id, slug UNIQUE, en_name UNIQUE, gr_name, artist_img BLOB) | 79 rows | `classes.py` |
| Song | `songs` (song_id, artist_id FK, slug UNIQUE, en_name, gr_name, video_id, demo_id) | 1048 rows; `idx_songs_artist` | `classes.py` |

`video_id` = original recording, `demo_id` = bouzouki sheet-music lesson (both YouTube ids).
Slugs: `textkeys.make_slug` (≤3 significant words, ≤26 chars), duplicates get `-2`.

## Key modules
| Path | Responsibility |
|---|---|
| `app.py` | `create_app`: routes, CSP/security headers, rate limits, error handlers |
| `classes.py` | `Artist`, `Song`, `Catalog`, `load_catalog`, `load_artist_image` |
| `textkeys.py` | `phonetic_key` (Greek/Latin spelling → one key), `make_slug` |
| `search.py` | `SearchIndex`: word/prefix/substring scoring, typo fallback (difflib) |
| `db_migrate.py`, `migrations/` | Versioned, reversible schema changes |
| `templates/`, `static/` | `static/fonts/` = Inter (OFL); `base.html` + `_macros.html`; `css/styles.css`; `js/search.js`, `artist.js`, `theme.js` |
| `tests/` | pytest suite (runs against the real catalog and temp legacy DBs) |
| `crawling_scripts/`, `db_games.py`, `automation.py`, `images.ipynb`, `jsons/`, `artists.csv`, `images/` | Offline data collection (Selenium); not imported by the app. `images/` is git-ignored |

## API surface
5 routes + health/robots/sitemap in `app.py`. Limits: 600/hour default per IP, `/search`
90/min, `/images` 300/min; static and `/healthz` exempt. In-memory storage unless
`RATELIMIT_STORAGE_URI` is set (counts are per gunicorn worker).

## External services
| Service | Used for | Config (env var names only — never values) |
|---|---|---|
| YouTube (nocookie embeds) | Both videos on song pages | — |

Env: `FLASK_SECRET_KEY`, `PORT`, `LOG_LEVEL`, `TRUST_PROXY_HOPS`, `DATABASE_PATH`, `RATELIMIT_STORAGE_URI`.

## Environments & deploy
| Env | Branch | DB | Notes |
|---|---|---|---|
| local | — | `instance/music.db` (tracked) | `uv run python app.py` |
| production | `master` (Railway planned, not connected) | same file, shipped with the code | `railway.json`: gunicorn `app:app`, health `/healthz`; set `TRUST_PROXY_HOPS=1` |

## Verification commands
`uv run pytest -q`. UI: run the app and check pages in a browser (headless Chrome
screenshots were used; no browser test suite).
