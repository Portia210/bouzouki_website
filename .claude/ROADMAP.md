# ROADMAP — task list

**Not self-serve.** Work only on a task the developer names in the session.
Before starting: read the task, check *Open decisions*, confirm your understanding.
When done: tick the box, write a hand-off entry, commit. One task per session.

**Task format:** `- [ ] **ID** — title` then indented lines:
`Goal` (one sentence) · `Done when` (checkable criteria) · `Depends on` · `Notes`.
Keep tasks small enough for one session and one commit; split anything bigger.

---

## Open decisions

Questions that block or shape tasks. A task touching one of these waits for an answer.

| # | Question | Blocks | Status |
|---|---|---|---|
| D1 | R2 bucket public or private? The PDFs came from a members-only Patreon: public means anyone with a link can download; private needs `boto3`, presigned URLs and probably a login. Is publishing them allowed? | P1–P3 | open |
| D2 | Songs with extra PDFs (3 folders): base file only, or upload the alternates too? | P1 | open |
| D3 | Also upload the 1597 mp3 / 990 mid / 994 sib files? (default: no) | P1 | open |
| D4 | Custom domain for the R2 bucket or `r2.dev`? Bucket name? | P3 | open |

---

## Part P — Sheet-music PDFs on R2 (plan: `.claude/plans/pdf-upload.md`)

- [ ] **P1** — Upload script (plan / upload / verify)
  - Goal: map the 1048 Patreon song folders to song slugs and upload their PDFs to R2 idempotently.
  - Done when: dry run shows 0 unmatched songs; real upload verified by HEAD checks; `verify` reports 0 missing and 0 orphans.
  - Depends on: D1, D2, D3
- [ ] **P2** — DB columns and download buttons
  - Goal: show "Sheet music" / "Tablature" buttons for songs that have a verified file.
  - Done when: migration `0004` round-trips; buttons only where a key exists; tests green.
  - Depends on: P1
- [ ] **P3** — Go live
  - Goal: set `PDF_BASE_URL` on Railway and deploy.
  - Done when: five random songs' PDFs download from the live site.
  - Depends on: P2, D4

---

## Done

Ticked tasks move here as one line each: `**ID** — title (YYYY-MM-DD, <commit sha>)`.
Detail lives in git, not here.

- Phonetic search, short slug URLs, schema v2/v3 migrations, modern UI, favicon set, Railway deploy (2026-11-14, see NEXTSESSION).
