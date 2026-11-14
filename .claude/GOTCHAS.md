# GOTCHAS — standing traps and known gaps

Read when something behaves oddly, **before** calling it a bug. Each entry is one
row; add one whenever a trap bites twice or costs real time. Delete rows that stop
being true.

## Traps
| Trap | Symptom | What to do |
|---|---|---|
| `.gitignore` doesn't hide files from Claude | Claude could read an ignored `.env` | Reads are blocked by `deny` rules in `.claude/settings.json`, not by `.gitignore` |
| English names use the site's own transliteration (`υ`→`y`: `Moy`, `Mayra`) | Raw substring search misses `mou`/`mavra` | Always search via `textkeys.phonetic_key`; extend `_DIGRAPHS` there and run `tests/test_textkeys.py` |
| `video_id` is the original recording, `demo_id` the lesson | The old desktop template had the two labels swapped | Original = `video_id`, lesson = `demo_id` (`test_pages_render` guards it) |
| CSP forbids inline `<script>` and `style=` | New inline code silently does nothing | Put JS in `static/js/`, styling in `styles.css` (`test_no_inline_script_or_style_in_pages`) |
| `.gitignore` contains `*.db` | A new `.db` file is ignored | `!instance/music.db` keeps the main DB tracked; use `git add -f` for others |
| `pkill -f <text>` in a Bash tool call matches the call itself | Shell exits 144 | Kill by port: `fuser -k 5055/tcp` |
| Some videos can't be embedded for the viewer | Two causes seen: (1) a few play on an https origin but not on `http://localhost`; (2) region block / embedding disabled → player error 150 even on https (oEmbed still says 200) | (2) is YouTube-side and stays after deploy. `artist.js` detects the error via the iframe API and shows a card with "Watch on YouTube" / "Find another recording". `main.py --https` was tried and removed: slow (a TLS handshake per request) |
| `app.py` / gunicorn don't reload; templates are cached | Edited templates don't show, or a half-updated server returns 500 | Develop with `uv run python main.py` (debug + reloader); `main.py` is never for production |
| `artist_thumb` (WebP) is made by migration 0003 with Pillow (dev dependency) | A new artist image added later has no thumbnail | App falls back to `artist_img`; re-run a thumbnail step for new images |
| Migrations rebuild tables | DB file doubles in size | `db_migrate.py` runs `VACUUM` afterwards |

## Known gaps
| Gap | Impact | Tracked in |
|---|---|---|
| Rate-limit counters are per gunicorn worker (memory storage) | Effective limit = limit × workers | set `RATELIMIT_STORAGE_URI` if it matters |
| `images.db`, `instance/music`, `main.py`, `test.py` look unused | Clutter | — |
| No browser/E2E tests; JS verified by hand in headless Chrome | JS regressions not caught by pytest | — |
| `guard-bash.sh` matches the command text with regex | A command hidden in a script or alias isn't caught — it's a seatbelt, not a sandbox | — |

## Deliberate non-fixes
Looks wrong, is intentional. Don't "fix" these.
| What | Why it stays |
|---|---|
| Phonetic key merges b/v/f, d/t, g/k | Recall over precision for autocomplete; exact spelling still ranks higher |
| Greek names in the DB are lowercase and accent-free | Source data; search folds accents anyway |
