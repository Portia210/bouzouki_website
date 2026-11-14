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
| D2 | Songs with extra PDFs (3 folders): base file only, or upload the alternates too? | P1 | default: base only |
| D3 | Also upload the mp3 / mid / sib files? | P1 | default: no |

Settled 2026-11-14: bucket is private (D1), no custom domain (D4), PDFs only for the signed-in admin.

---

## Part P — Sheet-music PDFs on R2 (plan: `.claude/plans/pdf-upload.md`)

- [ ] **P1** — `scripts/pdf_sync.py` (plan / apply / verify) and the real upload
  - Goal: map the 1048 song folders to `song_id`s and upload their PDFs idempotently; write keys only for verified objects.
  - Done when: `plan` shows 0 unmatched songs; `verify` reports 0 missing and 0 orphans.
  - Depends on: R2 token in the developer's `.env`.
- [ ] **P2** — Go live
  - Goal: R2 + `ADMIN_PASSWORD` variables on Railway, DB with keys pushed.
  - Done when: the admin opens five random PDFs on the live site; visitors see locks.
  - Depends on: P1.

---

## Done

Ticked tasks move here as one line each: `**ID** — title (YYYY-MM-DD, <commit sha>)`.
Detail lives in git, not here.

- **P0** — Admin sign-in, `/pdf` presigned redirect, schema v4, lock/document buttons (2026-11-14).
- Phonetic search, short slug URLs, schema v2/v3 migrations, modern UI, favicon set, Railway deploy (2026-11-14, see NEXTSESSION).
