"""Phonetic, typo-tolerant search over songs and artists."""

import difflib
from dataclasses import dataclass

from classes import Artist, Catalog, Song
from textkeys import fold, phonetic_words

MAX_QUERY_LEN = 100
MAX_TOKENS = 8


@dataclass
class _Entry:
    item: Artist | Song
    words: list[str]  # phonetic keys of the title words
    joined: str  # words concatenated, so "mavramatia" still matches "mavra matia"
    extra: list[str]  # phonetic keys of the artist words (songs only)
    raw: str  # folded English + Greek name, for exact-spelling bonus


def _score_token(token: str, entry: _Entry) -> float:
    best = 0.0
    for w in entry.words:
        if w == token:
            best = max(best, 3)
        elif w.startswith(token):
            best = max(best, 2)
        elif token in w:
            best = max(best, 1)
    if best < 1 and token in entry.joined:
        best = 0.6
    for w in entry.extra:
        if w == token:
            best = max(best, 1.5)
        elif w.startswith(token):
            best = max(best, 1)
    return best


class SearchIndex:
    def __init__(self, catalog: Catalog):
        self.songs = [self._entry(s, s.en_name, s.gr_name, phonetic_words(s.artist.en_name)) for s in catalog.songs]
        self.artists = [self._entry(a, a.en_name, a.gr_name, []) for a in catalog.artists]
        vocab = {w for e in self.songs + self.artists for w in e.words + e.extra}
        self.vocab = sorted(vocab)

    @staticmethod
    def _entry(item, en: str, gr: str, extra: list[str]) -> _Entry:
        words = phonetic_words(en) or phonetic_words(gr)
        return _Entry(item, words, "".join(words), extra, f"{fold(en)} {fold(gr)}")

    def _tokens(self, term: str) -> list[str]:
        return phonetic_words(term[:MAX_QUERY_LEN])[:MAX_TOKENS]

    def _fuzzy(self, token: str) -> str | None:
        if len(token) < 4:
            return None
        close = difflib.get_close_matches(token, self.vocab, n=1, cutoff=0.78)
        return close[0] if close else None

    def _rank(self, entries: list[_Entry], tokens: list[str], raw_query: str, limit: int, artist_bonus: float = 0):
        scored = []
        for e in entries:
            total = 0.0
            for t in tokens:
                s = _score_token(t, e)
                if s == 0:
                    total = 0
                    break
                total += s
            if not total:
                continue
            if raw_query and raw_query in e.raw:
                total += 2
            if e.joined.startswith("".join(tokens)):
                total += 2
            scored.append((total + artist_bonus, e.item))
        scored.sort(key=lambda p: (-p[0], p[1].en_name))
        return [item for _, item in scored[:limit]]

    def search(self, term: str, *, song_limit: int = 8, artist_limit: int = 4, artist: Artist | None = None):
        """Return (artists, songs) best matches. ``artist`` restricts songs to one artist."""
        tokens = self._tokens(term or "")
        if not tokens:
            return [], []
        raw_query = fold(term[:MAX_QUERY_LEN]).strip()
        songs = [e for e in self.songs if artist is None or e.item.artist is artist]
        artists = [] if artist else self.artists

        found_a = self._rank(artists, tokens, raw_query, artist_limit, artist_bonus=1)
        found_s = self._rank(songs, tokens, raw_query, song_limit)
        if not found_s and not found_a:  # typo fallback: swap unknown tokens for the closest known word
            fixed = [t if any(t in w for w in self.vocab) else (self._fuzzy(t) or t) for t in tokens]
            if fixed != tokens:
                found_a = self._rank(artists, fixed, "", artist_limit, artist_bonus=1)
                found_s = self._rank(songs, fixed, "", song_limit)
        return found_a, found_s
