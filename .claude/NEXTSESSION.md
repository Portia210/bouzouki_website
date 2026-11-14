# NEXTSESSION — hand-off log

Newest entry first; the SessionStart hook shows the top entry automatically.
A hand-off, not an archive: ≤ ~120 lines, delete entries that stopped mattering (git
keeps them). Standing rules go in CLAUDE.md or GOTCHAS.md, not here.

Entry template (copy it, keep the "NOT verified" line — write "nothing" if so):

    ## YYYY-MM-DD — <task id>: <title>
    - Changed: <what, a line or two>
    - Verified: <gate, tests, click-through, migration round trip>
    - NOT verified: <what and why>
    - Traps / decisions: <what the next session must know>
    - Next: <what's owed, open questions for the developer>

## 2026-11-14 — Header, favicon emblem, quiet dev log, "unavailable" videos
- Changed: site name **Bouzouki Rebetico** everywhere (spelling as requested; hero copy still says "Rebetiko"); header is one big line, no icon; favicon/PNG/ICO = body-only bouzouki emblem (`static/img/favicon.svg`; hero keeps the full tilted `logo.svg`); `main.py` dev log shows pages and errors only, gunicorn access log removed.
- Verified: pytest (39); screenshots desktop/mobile; dev log content; embeds that say "unavailable" on http://localhost DO play from an https origin.
- NOT verified: videos on the real Railway https domain; browser tabs showing the new favicon (cache).
- Also: `cryptography` (dev dep) + `main.py --https`; verified the previously "unavailable" original plays on https://localhost. Phone artist page: list first, player opens under the tapped song (tap again/Close folds it, stops playback); desktop unchanged.
- Next: after the Railway deploy, confirm the embeds play there.

## 2026-11-14 — Icon, artist-page layout, songs open in the artist page
- Changed: Greek-bouzouki logo/favicon set (SVG source `static/img/logo.svg`; ICO/PNGs rendered from it with headless Chrome); no song pages any more — `/song/<slug>` and search results go to `/artist/<slug>#<song>`, Enter opens the best match; artist page list scrolls with the page, player panel sticky (phone: player above the list); "Open on YouTube" link per player.
- Verified: pytest (39), headless-Chrome screenshots + DOM checks (hash select, search → hash, header position).
- NOT verified: the reported home-page 500 — not reproducible; most likely the dev server briefly ran new templates with old `app.py` while I was editing (restart the server). Real devices/Safari; why some videos say "unavailable" for the developer (likely region).
- Also: new ornate bouzouki logo (`logo.svg` upright, `favicon.svg`/PNG/ICO cropped tile), hero illustration, artist cards ~320px, larger sticky player (cols 4/8, capped to viewport).
- Next: if the 500 comes back, send the traceback.

## 2026-11-14 — Search, DB, redesign, Railway prep
- Changed: phonetic search (`textkeys.py`, `search.py`), schema v2 via `db_migrate.py` (slugs, artist FK, indexes), `create_app` refactor with CSP/ETag/health/sitemap, new Bootstrap-based UI with vanilla JS (jQuery removed), Procfile/`railway.json`, `images/` untracked, pytest suite.
- Verified: `uv run pytest -q` (37 pass); migration round trip on the real DB copy; gunicorn start + `/healthz`; headless-Chrome screenshots (desktop, mobile, dark) and scripted search/filter/player checks.
- NOT verified: real Railway deploy; real YouTube playback (embeds were blank in headless); Safari/Firefox; keyboard/screen-reader pass.
- Traps / decisions: slugs are short (≤3 words), old name URLs 301 to them; `number_of_songs` and `artist_name` columns dropped (derivable); `.claude/settings.json` allow-list not extended (blocked by the auto-mode classifier).
- Next: connect Railway (`TRUST_PROXY_HOPS=1`, `FLASK_SECRET_KEY`); decide if `images/` should be deleted from disk.

## 2026-11-14 — Project bootstrap
- Changed: added the .claude/ scaffold, merged CLAUDE.md (facts filled, old text moved to ARCHITECTURE.md), .gitignore, .editorconfig, .gitattributes, .env.example.
- Verified: —
- NOT verified: branches, build gate, code conventions are still placeholders; no lint/tests exist.
- Traps / decisions: —
- Next: run the `bootstrap-project` skill; developer defines the first ROADMAP tasks.
