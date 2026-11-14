#!/usr/bin/env bash
# Self-test for guard-bash.sh. Run after editing it:  bash .claude/hooks/test-hooks.sh
cd "$(dirname "$0")" || exit 1
PROD="$(grep -m1 '^PROD_BRANCH=' guard-bash.sh | cut -d'"' -f2)"
fail=0

check() { # expected_exit command
  printf '{"tool_input":{"command":"%s"}}' "$2" | ./guard-bash.sh >/dev/null 2>&1
  got=$?
  if [ "$got" = "$1" ]; then echo "PASS ($got) $2"; else echo "FAIL (want $1, got $got) $2"; fail=1; fi
}

check 2 "git push origin $PROD"
check 2 "git push origin HEAD:$PROD"
check 2 "git push origin main:$PROD"
check 2 "git push --force origin feature"
check 2 "git push -f origin feature"
check 2 "git push origin +feature"
check 2 "git commit --no-verify -m x"
check 2 "git add .env"
check 2 "git add backend/.env.local"
check 0 "git push origin ${PROD}-docs"
check 0 "git push origin feature"
check 0 "git add .env.example"
check 0 "git add src/env.ts"
check 0 "git status"

[ "$fail" = 0 ] && echo "All hook checks passed." || { echo "Hook checks FAILED."; exit 1; }
