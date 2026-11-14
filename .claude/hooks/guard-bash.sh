#!/usr/bin/env bash
# PreToolUse hook for Bash. Blocks commands that must never run without the developer.
# Exit 2 = block the call; stderr is shown to Claude. Exit 0 = allow.
# Edit PROD_BRANCH to match your project.

PROD_BRANCH="prod"

input="$(cat)"

block() {
  echo "BLOCKED by .claude/hooks/guard-bash.sh: $1 — this needs the developer. Explain what you wanted to run and why, then wait." >&2
  exit 2
}

# Push to the production branch (git push origin prod, HEAD:prod, master:prod, ...)
if echo "$input" | grep -Eq "git push[^\"]*[ :]${PROD_BRANCH}([^A-Za-z0-9_./-]|$)"; then
  block "push to '${PROD_BRANCH}' (release)"
fi

# Force push of any kind (--force, --force-with-lease, -f, +refspec)
if echo "$input" | grep -Eq 'git push[^"]*(--force|[ ]-f([ "]|$)|[ ]\+[A-Za-z])'; then
  block "force push"
fi

# Staging a real env file (.env.example is fine)
if echo "$input" | grep -Eq 'git add[^"]*\.env' && ! echo "$input" | grep -Eq '\.env\.example'; then
  block "staging an .env file — secrets must never be committed"
fi

# Bypassing git hooks / checks
if echo "$input" | grep -Eq -- '--no-verify'; then
  block "--no-verify bypasses safety checks"
fi

exit 0
