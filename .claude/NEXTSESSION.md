# NEXTSESSION — hand-off log

Newest entry first; the SessionStart hook shows the top entry automatically.
A hand-off, not an archive: ≤ ~120 lines, delete entries that stopped mattering (git
keeps them). Standing rules go in CLAUDE.md or GOTCHAS.md, not here.

Entry template (copy it, keep the "NOT verified" line — write "nothing" if so):

    ## 2026-11-14 — PDF sheet music: found, audited, plan written (nothing uploaded)
- Changed: only docs + `scripts/pdf_audit/` (`manifest.ps1`, `audit.py`). Full findings and design: `.claude/plans/pdf-upload.md`; tasks P1–P3 and open decisions D1–D4 in ROADMAP.
- Found: the Patreon PDFs are at `D:\מסמכים\python-downloads` (D: is NOT mounted in WSL; use `powershell.exe`). 79 artist folders, 1048 song folders = the 1048 DB songs, 1976 PDFs (~740 MB), 2 per song (sheet + `ΤΑΜΠΛΑΤΟΥΡΑ` tab), plus mp3/mid/sib. 1046 folders match a DB song by `demo_id` (from `video link.txt`), 1045 also by phonetic name; 3 exceptions by name; 56 songs have no PDF.
- Verified: `uv run python scripts/pdf_audit/audit.py <manifest.json>` reproduces every number (manifest made with `manifest.ps1`, ~27 MB, not committed).
- NOT verified: anything on R2 (the developer has a bucket; name, public/private, keys not known). No file was copied, uploaded or changed.
- Traps / decisions: R2 credentials only as env vars on the developer's Windows machine, never in chat; the PDFs are members-only Patreon content (copyright question, D1); object keys ASCII (`pdf/<song-slug>.pdf`), Greek only in `Content-Disposition`.
- Next: developer answers D1–D4, then P1 (upload script with `plan` dry run first).

## 2026-11-14 — Railway: region and edge cache (speed)
- Changed (in Railway, not in git): service `web` moved from us-west2 to `europe-west4-drams3a` (Amsterdam), edge CDN enabled (`htmlCaching auto`, purge all on deploy). Cause of the slowness was distance (~0.45 s per request), not image size (thumbnails ~12 KB).
- Verified: image served with `x-cache: HIT`; 78 home-page images over one HTTP/2 connection 6.5 s → ~2 s; warm-connection TTFB 0.45 s → 0.11 s.
- NOT verified: the region switch finishing on its own — the running deployment still listed both regions; the next deploy applies Europe only.
- Next: —

## 2026-11-14 — Railway deploy fixed and live
- Changed: the Railway project `bouzouki-website` (service `web`, repo `Portia210/bouzouki_website`, branch master, auto-deploy on push) already existed but every deploy failed (Nixpacks `pip install uv==` bug; start command `python app.py` ran without the venv → `No module named 'dotenv'`). Service settings changed in Railway: builder RAILPACK, start `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`, healthcheck `/healthz`, restart ON_FAILURE, variable `TRUST_PROXY_HOPS=1` (`FLASK_SECRET_KEY` was already set).
- Verified: deployment SUCCESS; live https://bouzouki-rebetiko.up.railway.app — pages, search, images (WebP), favicon, sitemap, CSP/HSTS headers, 404 all OK.
- NOT verified: YouTube embeds on the live domain in a real browser; no gzip on responses.
- Next: decide on a custom domain.

## 2026-11-14 — Favicon = orange pick on a deep-blue tile
- Changed: favicon.ico, favicon-32.png, icon-192/512, apple-touch-icon = silhouette traced from the developer's pick photo, flat amber #e0902f (their colour sample), on a rounded deep-blue tile (`deepblue`, darker than the earlier `blue`). Everything about it is kept in `design/favicon/` (originals, earlier attempts, comparison sheets, `make_icons.py` with variants deepblue|pearl|blue|black|night).
- Verified: pytest (42); preview sheets on light and dark.
- NOT verified: real browser tab (icons are cached; hard refresh).
- Next: —

## YYYY-MM-DD — <task id>: <title>
    - Changed: <what, a line or two>
    - Verified: <gate, tests, click-through, migration round trip>
    - NOT verified: <what and why>
    - Traps / decisions: <what the next session must know>
    - Next: <what's owed, open questions for the developer>

## 2026-11-14 — Header, favicon emblem, quiet dev log, "unavailable" videos
- Changed: site name **Bouzouki Rebetico** everywhere (spelling as requested; hero copy still says "Rebetiko"); header is one big line, no icon; favicon set (now the pick photo, see top entry; hero keeps `logo.svg`); `main.py` dev log shows pages and errors only, gunicorn access log removed.
- Verified: pytest (39); screenshots desktop/mobile; dev log content; embeds that say "unavailable" on http://localhost DO play from an https origin.
- NOT verified: videos on the real Railway https domain; browser tabs showing the new favicon (cache).
- Also: `cryptography` (dev dep) + `main.py --https`; verified the previously "unavailable" original plays on https://localhost. Phone artist page: list first, player opens under the tapped song (tap again/Close folds it, stops playback); desktop unchanged.
- Also: local https removed (slow); WebP thumbnails (home 9.9 MB → 1.6 MB); 5 artist cards per row; static URLs versioned + 1-year cache in prod; players use the YouTube iframe API (CSP allows https://www.youtube.com scripts) and show a fallback card on error 150.
- Also: artist page = wide grid (song column + one big tabbed video: lesson default, choice remembered; no inner scrollbar); favicon = flat white bouzouki on the blue tile (alternatives B monogram / C plectrum were offered, not kept).
- Next: after the Railway deploy, check which videos still show the fallback card (those are region/owner blocks).

## 2026-11-14 — Icon, artist-page layout, songs open in the artist page
- Changed: Greek-bouzouki logo/favicon set (SVG source `static/img/logo.svg`; ICO/PNGs rendered from it with headless Chrome); no song pages any more — `/song/<slug>` and search results go to `/artist/<slug>#<song>`, Enter opens the best match; artist page list scrolls with the page, player panel sticky (phone: player above the list); "Open on YouTube" link per player.
- Verified: pytest (39), headless-Chrome screenshots + DOM checks (hash select, search → hash, header position).
- NOT verified: the reported home-page 500 — not reproducible; most likely the dev server briefly ran new templates with old `app.py` while I was editing (restart the server). Real devices/Safari; why some videos say "unavailable" for the developer (likely region).
- Also: new ornate bouzouki logo (`logo.svg` upright, favicon set), hero illustration, artist cards ~320px, larger sticky player (cols 4/8, capped to viewport).
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
