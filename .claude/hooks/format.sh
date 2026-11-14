#!/usr/bin/env bash
# PostToolUse hook (Edit/Write): format the file Claude just changed.
# Uncomment the lines for your stack. Unconfigured file types are skipped.
# Formatter failures never block Claude.

input="$(cat)"
file="$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"

if [ -z "$file" ] || [ ! -f "$file" ]; then
  exit 0
fi

case "$file" in
  # *.ts|*.tsx|*.js|*.jsx|*.mjs|*.css|*.scss|*.json|*.md|*.html)
  #   npx --no-install prettier --write "$file" >/dev/null 2>&1 ;;
  # *.py)
  #   uv run ruff format "$file" >/dev/null 2>&1 && uv run ruff check --fix "$file" >/dev/null 2>&1 ;;
  # *.go)
  #   gofmt -w "$file" >/dev/null 2>&1 ;;
  # *.rs)
  #   rustfmt "$file" >/dev/null 2>&1 ;;
  *) ;;
esac

exit 0
