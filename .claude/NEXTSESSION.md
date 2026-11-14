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

## 2026-11-14 — Project bootstrap
- Changed: added the .claude/ scaffold, merged CLAUDE.md (facts filled, old text moved to ARCHITECTURE.md), .gitignore, .editorconfig, .gitattributes, .env.example.
- Verified: —
- NOT verified: branches, build gate, code conventions are still placeholders; no lint/tests exist.
- Traps / decisions: —
- Next: run the `bootstrap-project` skill; developer defines the first ROADMAP tasks.
