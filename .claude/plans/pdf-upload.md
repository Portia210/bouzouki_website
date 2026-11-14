# Plan — P1–P3: sheet-music PDFs on Cloudflare R2, linked from every song

**Goal:** each song on the site gets "Sheet music" and "Tablature" download buttons whose files live in the developer's existing Cloudflare R2 bucket, in perfect sync with the database.
**Done when:** every song with PDFs has verified objects in R2 and matching DB columns; the artist-page player shows the buttons only for songs that have them; `verify` reports zero missing and zero orphan objects.
**Approved by developer:** pending — decisions D1–D4 in ROADMAP are open. Nothing was uploaded, copied or changed yet.

## Where the files are
- `D:\מסמכים\python-downloads` (Windows D: drive). **D: is not mounted in WSL** (`/mnt/d` is empty); reach it with `powershell.exe` (see `scripts/pdf_audit/manifest.ps1`). Mounting needs sudo: `sudo mount -t drvfs D: /mnt/d`.
- Origin: the old Patreon crawler (`C:\Users\hp\Documents\Python_Projects\patreon\crawling_scripts\crawler.py`, which still points at `C:\Users\yybar\Downloads\python-downloads`, a path that no longer exists). The `patreon` folder itself is only the old copy of this website (no PDFs).
- Layout: `python-downloads\<ARTIST, Greek capitals>\<SONG, Greek capitals>\` containing
  `<song> video link.txt` (2 lines: song name, `Video Link: https://www.youtube.com/watch?v=<demo_id>`),
  `<song> - <artist>.pdf` (sheet music), `<song> - <artist> ΤΑΜΠΛΑΤΟΥΡΑ.pdf` (tablature), plus `.mp3`, `.mid`, `.sib` files.

## Audit results (2026-11-14, `scripts/pdf_audit/audit.py`, read-only)
| Fact | Number |
|---|---|
| Artist folders / song folders | 79 / 1048 (= 1048 songs in the DB) |
| PDFs / size | 1976 / ~740 MB |
| Folders matched to a DB song by `demo_id` from `video link.txt` | 1046 |
| Cross-check: phonetic key of folder names vs `gr_name` | 1045 agree, 0 differ |
| Folders with exactly 1 sheet + 1 tab PDF | 977 |
| Folders with no PDF at all | 56 (those songs get no buttons) |
| Tab only / sheet only | 6 / 5 |
| Extra PDFs (alternates) | 2 folders with 2 sheets; Nikolopoulos "ΦΙΛΕ ΜΟΥ ΚΑΛΕ" has 4 (also `ΠΑΡΤΙΤΟΥΡΑ`-named copies); Panou "ΑΣΦΑΛΩΣ ΚΑΙ ΔΕΝ ΠΡΕΠΕΙ" has 3 |
| Other files | 1597 mp3, 990 mid, 994 sib (Sibelius) — not part of this plan unless D3 says so |
| Encoding hygiene | all folder names NFC; no stray/trailing/double spaces; 6 song folders mix a Latin letter into Greek (`ΑΔIΚΑ…`, `ΛΑΪΚΟ CHA CHA`, `NΑ ' ΤΑΝΕ ΤΟ '21`, `LATIN ΟΡΓΑΝΙΚΟ`, `CASINO`) — harmless when matching by `demo_id` |

Three exceptions to resolve by name (no guessing): folder `ΜΕΛΩΔΙΑ ΣΕ 5` (no link txt) ↔ song `melodia-5`; the other Lemonopoulos song `melodia-58-organiko` shares its `demo_id` with it in the DB; folder `ΤΑ ΦΡΑΓΚΑ ΜΟΥ ΧΑΛΑΩ` (no link txt) ↔ DB song `fragka-chalao`, the only song whose `demo_id` has no folder.

## Design
1. **Keys are ASCII, derived from the DB slug:** `pdf/<song-slug>.pdf` and `pdf/<song-slug>-tab.pdf`. Greek never appears in object keys. The Greek download name goes in the object's `Content-Disposition: attachment; filename*=UTF-8''…` metadata.
2. **Matching rule:** accept a folder only if `demo_id` (from the txt) and the phonetic name key agree; the three exceptions above by name; everything else goes to a report, never guessed.
3. **Classifying PDFs:** name contains `ΤΑΜΠΛΑΤΟΥΡΑ` → tab, else sheet. With several candidates take the base name `<song> - <artist>.pdf` (D2).
4. **Idempotent upload script** (runs on the developer's Windows machine because of D:, uses boto3/rclone against R2's S3 API): upload only missing/changed objects (compare size + sha256 stored in a local manifest), then `HEAD` to confirm size; write DB columns **only** for confirmed objects.
5. **DB:** migration `0004` adds nullable `songs.score_key` and `songs.tab_key` (reversible, via `db_migrate.py`; follow the `db-migration` skill). The app builds links as `PDF_BASE_URL + key`; no key → no button.
6. **`verify` command:** every DB key must exist in the bucket and every `pdf/*` object must be referenced by a song → zero missing, zero orphans = "perfect sync". Run it before each deploy that touches PDFs.
7. **Secrets:** R2 credentials only as environment variables on the developer's machine (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`); never pasted into chat, never committed; list them in `.env.example` with dummy values.
8. **CSP:** download links are plain navigations (no change). Embedding a PDF viewer would need `frame-src`.

## Steps
- [ ] 1. Developer answers D1–D4 (ROADMAP) and gives the bucket name — verify by: answers recorded here.
- [ ] 2. `scripts/pdf_audit/upload_to_r2.py` with `plan` (dry run, prints what would upload), `upload`, `verify` — verify by: dry run on the real manifest lists 1046+3 songs, 0 unmatched; unit tests for classification/keys with fake folders.
- [ ] 3. Migration `0004` + `classes.py` fields + template buttons + tests — verify by: `uv run pytest -q`, migration round trip, screenshot of the player with and without buttons.
- [ ] 4. Upload for real (developer runs it), then `verify` — verify by: zero missing / zero orphans; open 5 random songs' PDFs.
- [ ] 5. Set `PDF_BASE_URL` on Railway, deploy, spot-check on the live site.

## Open questions
- D1 public vs private bucket → **copyright risk:** the PDFs came from the creator's Patreon (members only). A public bucket exposes them to anyone with a link. Get the creator's permission or keep them private (presigned URLs, needs `boto3` and probably a login).
- D2 songs with extra PDFs: base file only, or also upload alternates.
- D3 upload mp3/mid/sib too? (default: no)
- D4 custom domain for R2 (public bucket) or `r2.dev`.
