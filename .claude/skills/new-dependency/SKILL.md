---
name: new-dependency
description: Decide whether to add a library or external service, or build it ourselves. Use before adding any package/dependency, before building a peripheral feature (analytics, error tracking, email, uptime, file storage, auth, search, payments), and before integrating any third-party API or script.
---
# Adding a dependency or service

**Never add one silently — and never build silently either. The developer decides.**

## Buy before build
Before hand-writing a peripheral feature, check for a free or cheap ready-made option.
If one exists, stop and present:
- **Price:** free / free tier (limits) / paid.
- **Build instead:** what we'd write, concretely (files, tables, endpoints, tests).
- **Tradeoff:** data leaves the project, another account to maintain, lock-in, a free
  tier that may start charging.
- **Integration cost:** env vars, CSP `script-src`/`connect-src`, CORS — a third-party
  script that isn't allowed by the CSP loads and silently does nothing.
- **Recommendation**, with the reason.

## Before adding a package
- Can the standard library or an existing dependency do it?
- Exact name verified against the official source (typosquats are common).
- Maintained: recent releases, open-issue health, real usage. License compatible.
- Size and transitive dependencies proportionate to the need.

## When approved
- Use the project's package manager only; pin per project convention; commit the
  lockfile in the same commit.
- Run the dependency audit (Project facts). Report findings; don't auto-upgrade majors.
- Note it in ARCHITECTURE (external services) if it's a service.
