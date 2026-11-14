#!/usr/bin/env bash
# SessionStart hook: stdout is added to Claude's context at session start / resume /
# after /clear. Read-only. Never fails the session.

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

echo "=== SESSION CONTEXT (.claude/hooks/session-context.sh) ==="

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Branch: $(git branch --show-current 2>/dev/null)"
  status="$(git status --short 2>/dev/null | head -30)"
  echo "--- git status ---"
  if [ -n "$status" ]; then echo "$status"; else echo "(clean)"; fi
  echo "--- recent commits ---"
  git log --oneline -5 2>/dev/null || echo "(no commits yet)"
fi

if [ -f .claude/NEXTSESSION.md ]; then
  echo "--- top NEXTSESSION entry ---"
  awk '/^## /{n++} n==1' .claude/NEXTSESSION.md | head -40
fi

plans="$(ls .claude/plans/*.md 2>/dev/null | grep -v '_TEMPLATE.md')"
if [ -n "$plans" ]; then
  echo "--- open plans ---"
  echo "$plans"
fi

if grep -q '<PLACEHOLDER' CLAUDE.md 2>/dev/null; then
  echo "!!! CLAUDE.md has unfilled <PLACEHOLDER> values -> use the bootstrap-project skill first."
fi

echo "=== Wait for the developer to name the task. ==="
exit 0
