# GOTCHAS — standing traps and known gaps

Read when something behaves oddly, **before** calling it a bug. Each entry is one
row; add one whenever a trap bites twice or costs real time. Delete rows that stop
being true.

## Traps
| Trap | Symptom | What to do |
|---|---|---|
| `.gitignore` doesn't hide files from Claude | Claude could read an ignored `.env` | Reads are blocked by `deny` rules in `.claude/settings.json`, not by `.gitignore` |
| English song names use the site's own transliteration (`υ`→`y`: `Moy`, `Mayra`, `Aytos`) | Searching `mou` / `mavra` finds nothing | Search must normalize phonetically, not substring-match raw text |
| Songs are addressed by `en_name` in URLs | 5 duplicate names (`Pyretos`, `O Trelos`, ...): the second song is unreachable | Needs a unique slug/id (see ROADMAP once created) |
| `.gitignore` now contains `*.db` | New `.db` files are ignored; `instance/music.db` stays tracked because it was added earlier | `git add -f` for a deliberate new DB |

## Known gaps
Things that are incomplete on purpose or not yet handled.
| Gap | Impact | Tracked in |
|---|---|---|
| `Procfile` points to `server:app`, no `server.py` | Heroku start fails unless a Heroku-side override exists | — |
| Old CLAUDE.md mentioned `requirements.txt`, SQLAlchemy, Selenium as app deps | Stale: deps are in `pyproject.toml` (uv); Selenium only used by offline scripts | — |
| `guard-bash.sh` matches the command text with regex | A command hidden in a script or alias isn't caught — it's a seatbelt, not a sandbox | — |

## Deliberate non-fixes
Looks wrong, is intentional. Don't "fix" these.
| What | Why it stays |
|---|---|
| — | — |
