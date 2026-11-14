# Rebetiko Music

Flask catalog of Greek rebetiko songs: for each song, the original recording and a
bouzouki sheet-music lesson (YouTube embeds). Songs open inside their artist's page. Search works in Greek and in any spelling of
the Latin transliteration (`mou` / `moy` / `μου`).

## Run locally

```bash
uv sync
cp .env.example .env        # then set FLASK_SECRET_KEY
uv run python app.py        # http://localhost:5000
uv run pytest -q            # tests
```

## Database

`instance/music.db` (SQLite) is committed and shipped with the app; the app opens it
read-only. Schema changes are numbered scripts in `migrations/`:

```bash
uv run python db_migrate.py status
uv run python db_migrate.py up      # backs up the file first
uv run python db_migrate.py down    # revert one step
```

## Deploy on Railway

Start command and health check are in `railway.json` (`Procfile` mirrors it). Set the
variables from `.env.example` in the service: `FLASK_SECRET_KEY` (required) and
`TRUST_PROXY_HOPS=1`. The database file is part of the repo, so no volume is needed.
