# Upload logic: Patreon folders → private R2 bucket → `songs` table

Reference for `pdf_sync.py` (repo root). Read this before changing it or before uploading another
file type (mp3, mid, sib). Facts as of 2026-11-14; the code outranks this file.

## The pipeline
```
D:\מסמכים\python-downloads\<ARTIST>\<SONG>\*   (Windows, not mounted in WSL)
   │ scripts/pdf_audit/manifest.ps1  → manifest.json (names + sizes + the video link; no bytes)
   ▼
pdf_sync.py plan    manifest → match folders to songs → pick files        (no network, no writes)
pdf_sync.py apply   + --root (the folder, mounted) → sha256 → HEAD → PUT → HEAD → write DB key
pdf_sync.py verify  DB ⇄ bucket: 0 missing, 0 orphans (--deep also checks object metadata)
pdf_sync.py prune   delete orphans (dry run unless --yes)
```
Run (WSL): `sudo mount -t drvfs D: /mnt/d` once per boot, then
```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(wslpath -w scripts/pdf_audit/manifest.ps1)" > manifest.json
uv run python pdf_sync.py plan   --manifest manifest.json
uv run python pdf_sync.py apply  --manifest manifest.json --root "/mnt/d/מסמכים/python-downloads" --dry-run
uv run python pdf_sync.py apply  --manifest manifest.json --root "/mnt/d/מסמכים/python-downloads"
uv run python pdf_sync.py verify --deep
```
Needs `R2_ACCOUNT_ID`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` in `.env` (token limited to
the one bucket, Object Read & Write). The DB written is `instance/music.db` (or `DATABASE_PATH`); a
consistent `music.db.pre-pdfsync-<timestamp>.bak` copy is made by every run that changes the DB (git-ignored `*.bak`). `manifest.json` in the repo root is git-ignored too. Commit the DB to ship the keys.

## Rules that make it safe
1. **Keys come from `song_id` only:** `pdf/<song_id>/sheet.pdf`, `pdf/<song_id>/tab.pdf` (`object_key`).
   Names, slugs and Greek never enter a key, so renaming a song/artist changes nothing in the bucket.
   The download name is built per request from the current DB names (`app.py`, `storage.content_disposition`).
2. **The DB is the source of truth.** `songs.score_key` / `tab_key` say which object belongs to a song.
   A key is written **only after** the object was HEAD-verified in the bucket in the same run.
3. **Matching never guesses** (`match_folders`). A folder is accepted only if its Greek artist and song names
   agree with the song's (phonetic key **and** the numbers in the name — the key alone drops digits) and,
   when the folder's `<song> video link.txt` holds a video id, that id equals `songs.demo_id`. With no link
   file, or one without a usable id (one folder has `v=media.html`), the names alone decide and `plan`
   prints a `NOTE` line for it (2 of 1048 today). Several songs share one video id (`melodia-5` /
   `melodia-58`): the names decide. Zero or several candidates, or two folders claiming one song → a PROBLEM,
   nothing uploaded for it.
4. **Choosing the file** (`pick_pdfs`): tab = name contains `ΤΑΜΠ…ΤΟΥΡΑ` (also the typo `ΤΑΜΠΑΛΑΤΟΥΡΑ`);
   everything else is the sheet. With several candidates: a `ΠΑΡΤΙΤΟΥΡΑ` copy never wins, then the exact
   `<song> - <artist>` name wins (whitespace-collapsed, then raw: the Panou folder has a double-space copy).
   A tie is reported, not decided. A lone candidate is taken even if its name differs from the folder's, so `plan`
   prints a `REVIEW` line for every pick whose words don't match `<song> <artist>` (any order) or that is a
   ΠΑΡΤΙΤΟΥΡΑ copy — 208 today, mostly punctuation and typos, a few really different (e.g. another artist's
   name): read them before `apply`.
5. **Idempotent:** each object stores `sha256`, `song-id`, `demo-id` as metadata. A file is uploaded only if
   the object is missing or its size/sha256 differ. A second run uploads nothing.
6. **File checks before upload:** content must start with `%PDF` (no empty files, no error pages saved as .pdf), its
   size must equal the manifest's (stale manifest), and its resolved path must stay inside `--root`
   (no `..`, no symlink out). After the PUT, a HEAD must show the same size **and** sha256 metadata.
7. **One failure doesn't stop the rest;** a failed file gets no key and the exit code is 1.
8. **Bucket stays private;** the site hands out 5-minute presigned URLs to the signed-in admin only.
9. **Recovery (not automated):** each object carries `song-id` and `demo-id`, so the DB links could be rebuilt
   from the bucket; there is no `relink` command yet. If the DB loses its keys, run `apply` again: unchanged
   objects are not re-uploaded, only the keys are written back.
10. **`prune` is guarded:** orphans are computed from the *local* DB only, so it refuses (even with `--yes`) when the DB
   references no object at all, and refuses to delete more than 10% of the bucket without `--force`. It reports
   per-object delete errors. A DB key outside the `pdf/<song_id>/…` convention is flagged by `verify`, and its
   object is never pruned.

## Results of the 2026-11-14 audit (D: folder)
79 artist folders = 79 DB artists (song counts equal); 1048 song folders → all 1048 matched, 0 problems;
986 sheets + 986 tabs picked; 56 songs have no PDF. Other files in the folders: 1597 mp3, 990 mid, 994 sib,
1047 `video link.txt` — **not uploaded** (decision D3, PDF only).

## Adding another file type later (mp3 / mid / sib)
Nothing for them exists yet. The steps, in order:
1. **Decide** the product question first: who may open them (admin only like the PDFs?), and the
   copyright question — the files come from a members-only Patreon.
2. **Audit** their names like `audit.py` did for PDFs: how many per folder, naming patterns, sizes (R2
   cost), duplicates. `manifest.ps1` already lists every file with its size.
3. **Schema:** a migration adding one nullable column per kind to `songs` (`audio_key`, `midi_key`,
   `sib_key`; follow `migrations/0004_song_pdf_keys.py` and the `db-migration` skill) and `classes.py`
   (`Song` fields + the SELECT).
4. **`pdf_sync.py`:** add the kinds to `KINDS` (`Kind(column, filename)`), e.g. `"audio": Kind("audio_key", "audio.mp3")`,
   and make these PDF-only parts per kind:
   - `KEY_PREFIX` / `list_objects`: one prefix per kind (`audio/`, `midi/`, …), and `verify`/`prune`
     must list **every** prefix, or orphans there go unnoticed;
   - `CONTENT_TYPE` (`audio/mpeg`, `audio/midi`, `application/octet-stream` for `.sib`);
   - `pick_pdfs`: classification is by file name and `.pdf` extension — write a picker for the new
     extension (take care when a folder has several mp3: decide which one is "the" recording);
   - rename the module/CLI if it no longer says "pdf".
5. **Serving:** `storage.presigned_url` hard-codes `ResponseContentType: application/pdf` and an `inline`
   disposition — parametrise both (`sib`/`mid` should be `attachment`). `/pdf/<song_id>/<kind>` in `app.py`
   whitelists `("sheet", "tab")`; add the kinds there (or a sibling route) and the buttons in
   `artist_songs.html` / `artist.js` (`data-*` attributes + `pdfButtons`).
6. **Tests:** extend `tests/test_pdf_sync.py` (picker, keys, verify with the new prefix) and
   `tests/test_admin.py` (route, 404 for missing keys).
7. **Run** `plan` → `apply --dry-run` → `apply` → `verify --deep`, commit the DB, set Railway variables.
