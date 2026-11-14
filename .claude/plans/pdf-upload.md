# Plan — sheet-music PDFs on private Cloudflare R2, admin-only

**Goal:** each song gets "Sheet music" / "Tablature" buttons; the files live in a **private** R2 bucket (`bouzouki-rebetiko`), only the signed-in admin can open them, and bucket and DB stay in perfect sync even when song/artist names change.
**Done when:** every song with PDFs has a verified object in R2 and matching DB keys; `pdf_sync.py verify` reports 0 missing and 0 orphans; the live site opens a PDF for the admin and shows a lock to everyone else.
**Approved by developer (2026-11-14):** private bucket + admin login (D1/D4 settled: no public URL, no custom domain); push to `master` freely (no users yet); DB changes are made on the local DB first, then shipped by committing it.

## Design (decided)
- **Keys from `song_id`:** `pdf/<song_id>/sheet.pdf`, `pdf/<song_id>/tab.pdf`. Names never enter keys, so renames touch nothing in R2. The download name is built per request from the current DB names.
- **DB = source of truth:** `songs.score_key` / `tab_key` (migration 0004, done). A key is written only after the object is HEAD-verified.
- **Access:** `/admin` (one password, `ADMIN_PASSWORD`), 7-day session renewed on every visit, `/pdf/...` redirects to a 5-minute presigned URL. Public HTML is identical for everyone (Railway edge cache); lock → document icon is swapped by JS after `/admin/session`.
- **Dependency:** `boto3` (approved by proceeding; used by `storage.py` and the sync script).
- **Object metadata** (set by the sync script): `song-id`, `demo-id`, `sha256` — lets the DB links be rebuilt from the bucket.

## Where the files are
`D:\מסמכים\python-downloads\<ARTIST>\<SONG>\` on Windows. D: is not mounted in WSL: use `powershell.exe -File scripts/pdf_audit/manifest.ps1` or `sudo mount -t drvfs D: /mnt/d`.
Per folder: `<song> video link.txt` (YouTube `demo_id`), `<song> - <artist>.pdf` (sheet), `<song> - <artist> ΤΑΜΠΛΑΤΟΥΡΑ.pdf` (tab), plus mp3/mid/sib (not uploaded).

## Audit (2026-11-14, read-only)
79 artist folders = 79 DB artists (0 missing either side, song counts equal). 1048 song folders = 1048 songs; 1046 matched by `demo_id` (+ phonetic name cross-check 1045/1045); 1976 PDFs, ~740 MB. 977 folders have exactly 1 sheet + 1 tab, 56 none, 6 tab only, 5 sheet only; extras: 2 folders with 2 sheets, Nikolopoulos "ΦΙΛΕ ΜΟΥ ΚΑΛΕ" 4, Panou "ΑΣΦΑΛΩΣ ΚΑΙ ΔΕΝ ΠΡΕΠΕΙ" 3. Exceptions by name: `ΜΕΛΩΔΙΑ ΣΕ 5` ↔ `melodia-5`, `ΤΑ ΦΡΑΓΚΑ ΜΟΥ ΧΑΛΑΩ` ↔ `fragka-chalao`.

## Steps
- [x] 1. Migration 0004 + `classes.py` (`score_key`, `tab_key`, `song_by_id`) — round trip proven on a copy of the real DB.
- [x] 2. `/admin`, session, `/pdf`, `storage.py`, buttons + lock, `tests/test_admin.py` — verified in a browser on a scratch DB with fake keys.
- [ ] 3. `scripts/pdf_sync.py` `plan` / `apply` / `verify`: match folders (rule above; anything unmatched goes to a report, never guessed), classify tab by `ΤΑΜΠΛΑΤΟΥΡΑ`, base file `<song> - <artist>.pdf` when several (D2), upload only missing/changed (sha256), HEAD-verify, then write keys. Tests with fake folders and a fake S3.
- [x] 4a. Bucket-scoped R2 token (Object Read & Write) created; `R2_*` in the local `.env`; round trip incl. presigned GET and refused anonymous GET verified.
- [ ] 4b. Developer adds `ADMIN_PASSWORD` to `.env`; run `plan`, then `apply`, then `verify`.
- [ ] 5. Set the same variables on Railway, commit + push the DB, check a PDF on the live site (R2 honouring `response-content-disposition` is already verified).

## Open
- D2 extra PDFs: default = base file only; alternates listed in the report.
- D3 mp3/mid/sib: default = not uploaded.
