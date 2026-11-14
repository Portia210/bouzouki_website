---
name: db-migration
description: How to change the database schema safely. Use for any change to models, tables, columns, indexes, constraints or enums, and before writing or reviewing any migration.
---
# Database migrations

**Never change the schema by hand. Migrations only. Every migration is reversible.**

## Steps
1. Change the models.
2. Generate the migration with the project's tool (see Project facts).
3. **Read the generated file**, especially the downgrade — autogenerate is often wrong
   for constraint changes, type changes, server defaults and enum changes.
4. Data migrations: make them idempotent; batch large updates; never lock big tables
   for long.
5. Prove the round trip **locally**: upgrade → downgrade one step → upgrade. Part of
   the gate for this task.
6. Update `.claude/ARCHITECTURE.md` (data model) in the same commit.

## Destroying data
Dropping a column/table or lossy type changes are irreversible in practice — downgrade
restores schema, not data. **Ask first**, say so explicitly in the plan and the
hand-off, and recommend a dump before release.

## Safe rollout
- Prefer expand → migrate → contract: add the new column, deploy code that writes
  both, backfill, switch reads, remove the old column in a later release.
- Migrations reach test/staging first; a clean apply there comes before any release.
- Rollback is two steps: revert the code **and** run the downgrade. Redeploying old
  code doesn't un-run a migration; neither does a feature flag.
- If migrations run automatically on deploy, check that the test environment can never
  resolve to the production database.
