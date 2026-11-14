---
name: debugging
description: Systematic debugging procedure. Use when fixing a bug, a failing test, a crash, an error message, or unexpected behavior.
---
# Debugging

1. **Reproduce first.** Get a reliable reproduction — ideally a failing test. No repro,
   no fix; if you can't reproduce, report what you tried.
2. **Read everything.** The full error and stack trace, relevant logs, recent changes
   (`git log -p` on the affected files). Check `.claude/GOTCHAS.md`.
3. **Form one hypothesis and test it** with the smallest experiment (a log line, a
   narrowed test, a bisect). Remove temporary instrumentation afterwards.
4. **Fix the root cause,** not the symptom. A try/except that hides the error, a
   retry that masks a race, or a special case for the failing input is not a fix.
5. **Regression test:** fails before the fix, passes after.
6. **Check siblings:** the same mistake elsewhere? Report it; don't fix out of scope.
7. **Two failed attempts → stop.** Report what you tried, what you learned, and your
   current hypothesis instead of looping on variations.
8. Worth remembering for next time? Propose a one-line GOTCHAS entry.
