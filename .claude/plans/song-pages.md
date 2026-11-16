# Plan — a real page (URL) for every song, same player, instant switching

**Goal:** `/song/<slug>` renders the artist page opened on that song, with song-specific title, description, canonical and OG tags (so link previews and search engines see the song). Clicking another song in the list still swaps the player without a reload.
**Done when:** `/song/<slug>` is a 200 page; the list and the search use it; old `/artist/x#slug` links still open the song; old `/song/<English name>` 301s to `/song/<slug>`; sitemap lists every song; tests and a browser click-through pass.
**Approved by developer (2026-11-17):** "full version" of the proposal.

## Design (decided)
- One template (`artist_songs.html`) for both URLs; `song` is optional. The server marks the row `aria-current` and fills title/player heading, so there is no flash.
- URL while browsing: `history.replaceState` (not `pushState`), so Back leaves the artist instead of stepping through every song played; the URL is always shareable. Folding the player on a phone restores `/artist/<slug>`.
- Old `#slug` links: the server never sees a hash, so `artist.js` upgrades it to the song URL on load (and on `hashchange`).
- Slugs are unique across all songs, so `/song/<slug>` needs no artist in the path.
- HTML stays identical for everyone (admin state still comes from `/admin/session`).
- `og:image` stays the 192px icon (a bigger image makes WhatsApp show a full-width card).

## Steps
- [x] 1. `app.py`: `/song/<slug>` renders; legacy names 301 to it; `/search` and sitemap use song URLs.
- [x] 2. Templates: per-song title/description/canonical/og tags (`base.html` blocks), row links, `aria-current`, `data-artist-url`; search results link to song pages.
- [x] 3. `artist.js`: row URL instead of `#slug`; hash upgrade; fold restores the artist URL; share + admin `next` use the song path.
- [x] 4. Tests (song page content/meta, legacy redirects, search URLs, sitemap) + gate.
- [x] 5. Browser click-through (desktop + phone), docs (ARCHITECTURE, NEXTSESSION), commit, push.
