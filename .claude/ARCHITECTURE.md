# ARCHITECTURE

**Derived from source on 2026-11-14 at `0e861f1`.** Source code outranks this
file; if they disagree, report it and re-derive the section. Facts only — no history,
no plans (those go in ROADMAP).

## Overview
Single-process Flask app (`app.py`). At import time `classes.import_db()` loads every
artist and song from SQLite into memory (`all_artists`); all routes read that list and
never touch the DB again. Pages are Jinja2 + Bootstrap 5; search is jQuery UI autocomplete
calling `/search`. Content is Greek/English sheet-music videos hosted on YouTube.

## Request / data flow
- `GET /` → `app.home` → sorts `all_artists` by `number_of_songs` → `index.html`
- `GET /artist/<en_name>` → linear scan of `all_artists` → `artist_songs.html`
- `GET /song/<en_name>` → linear scan over all songs → `song_details.html`
- `GET /search?term=` → `validate_search_term` → substring match on lowercased `en_name`/`gr_name` → JSON (max 50)
- `GET /images/<en_name>` → `artist.artist_img` bytes (PNG) → cached 30 days (SimpleCache, per process)

## Data model
| Entity | Table | Key relations | Owner module |
|---|---|---|---|
| Artist | `artists` (artist_id, en_name, gr_name, number_of_songs, artist_img BLOB) | 79 rows | `classes.py` |
| Song | `songs` (song_id, artist_name, en_name, gr_name, video_id, demo_id) | 1048 rows; joined to artists by `artist_name = en_name` text, no FK, no indexes | `classes.py` |

`instance/images.db` and the empty file `instance/music` are not used by the app.

## Key modules
| Path | Responsibility |
|---|---|
| `app.py` | Routes, input sanitizing, rate limits, cache, error handlers |
| `classes.py` | `Artist`, `Song`, `import_db()` |
| `logger.py` | Logger; level from `LOG_LEVEL` |
| `templates/` | `base.html` (header + search JS), `index.html`, `artist_songs.html`, `song_details.html`, `error.html` |
| `static/` | `css/styles.css` (empty), `js/artist_songs.js` (unused), `img/` logos |
| `crawling_scripts/`, `db_games.py`, `automation.py`, `images.ipynb`, `jsons/`, `artists.csv`, `images/` | Offline data collection (Selenium, Patreon, YouTube); not imported by the app |

## API surface
5 routes + 3 error handlers, all in `app.py`. `/search` 30/min, `/images` 100/min,
default 200/day and 50/hour per IP (in-memory limiter).

## External services
| Service | Used for | Config (env var names only — never values) |
|---|---|---|
| YouTube embeds | Song + sheet-music iframes | — |
| jQuery / jQuery UI CDNs | Autocomplete | — |

## Environments & deploy
| Env | Branch | DB | Notes |
|---|---|---|---|
| local | — | `instance/music.db` (tracked in git) | `FLASK_SECRET_KEY`, `PORT`, `LOG_LEVEL` |
| production | none yet (Railway planned) | same file, shipped with the code | `Procfile` runs `gunicorn server:app`; `server.py` does not exist |

## Verification commands
No automated checks. Smoke test: Flask `test_client()` GET `/`, `/artist/<name>`,
`/song/<name>`, `/search?term=...`, `/images/<name>` → expect 200.
