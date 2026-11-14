---
name: bootstrap-project
description: Onboard Claude to this repository — fill in CLAUDE.md Project facts and configure the .claude/ scaffold. Use when CLAUDE.md still contains <PLACEHOLDER> values, or when the developer asks to set up, onboard or re-derive project facts.
---
# Bootstrap the project

Goal: replace every `<PLACEHOLDER>` with facts derived from the repo, and configure
the scaffold. **Read-only until the developer approves the proposal.**

## 1. Explore (read-only)
- Manifests and lockfiles (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`…),
  CI config, `Makefile`/scripts, Dockerfiles, README, directory layout, existing tests,
  `git log --oneline -20`, `git branch -a`.
- Derive real commands — don't guess from the stack. Unknown → mark `?`.
- If safe and quick, run the lint/type-check/test commands to confirm they work on a
  clean checkout. Note failures; don't fix them.

## 2. Security sweep (report only)
- `git ls-files | grep -iE '\.env($|\.)|\.pem$|\.key$|id_rsa|credentials|\.tfstate'`
  — anything tracked that shouldn't be? Remember: deleting it doesn't remove it from
  history; the fix is rotation (developer decides).
- Env vars the code reads vs. what `.env.example` lists.
- Paths that should be in `.gitignore` but aren't (build output, caches, dumps).

## 3. Propose — then wait
Present, in one message:
1. Filled-in **Project facts** for CLAUDE.md (incl. the build gate and branch names).
2. Project-specific **Code** conventions you observed (one line each).
3. Config changes:
   - `PROD_BRANCH` in `.claude/hooks/guard-bash.sh`
   - lint/test/build commands to add to `permissions.allow` in `.claude/settings.json`
   - formatter lines to enable in `.claude/hooks/format.sh`
   - `.gitignore` project-specific additions; `.env.example` contents
4. A first draft of `.claude/ARCHITECTURE.md` (short; facts only).
5. Everything suspicious from steps 1–2.
6. Sections of CLAUDE.md that don't apply here (e.g. no DB) — propose deleting them.

**Wait for approval.** Then write the files, run `bash .claude/hooks/test-hooks.sh`,
update the bootstrap entry in NEXTSESSION, and commit.
