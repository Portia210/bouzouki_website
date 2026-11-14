---
description: Close the current task — gate, review, docs, hand-off, commit, push
---
Close the current task, in order. Stop and report at the first failure.

1. Run the build gate (Project facts). Red → stop.
2. Non-trivial change → run the `code-reviewer` agent; fix its "Must fix" findings
   (ask me about anything debatable).
3. `git status` + `git diff --stat`: no debug leftovers, unrelated files, secrets, or
   new files that belong in `.gitignore`. Stage files explicitly.
4. Update affected `.claude/` docs (ARCHITECTURE, GOTCHAS) — replace stale text.
5. Tick the task in ROADMAP and move it to *Done* as one line.
6. Add a NEXTSESSION entry from its template. Be honest in "NOT verified". Prune.
7. Delete the task's plan file in `.claude/plans/` if one exists.
8. Commit (the change and the trap, not the journey) and push to the dev branch.
   Never the production branch.
9. Report in a few lines, then stop. Don't start another task.

Notes from me (may be empty): $ARGUMENTS
