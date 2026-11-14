---
description: Run the build gate and report
---
Run the build gate exactly as defined in `CLAUDE.md` → Project Facts, plus the tests
relevant to the current change. If this change adds a migration, also run the
upgrade → downgrade → upgrade round trip.

Report: pass/fail per step, and for failures only the relevant error lines.
Do not fix anything unless I ask — just report.
