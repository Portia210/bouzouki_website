import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from logger import logger

DEFAULT_DB = Path(__file__).parent / "instance" / "music.db"
REQUIRED_VERSION = 2  # see migrations/; run `uv run python db_migrate.py up`


def db_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", DEFAULT_DB))


@dataclass
class Artist:
    artist_id: int
    slug: str
    en_name: str
    gr_name: str
    has_image: bool
    songs: list["Song"] = field(default_factory=list)

    @property
    def number_of_songs(self) -> int:
        return len(self.songs)


@dataclass
class Song:
    song_id: int
    slug: str
    en_name: str
    gr_name: str
    video_id: str  # original recording on YouTube
    demo_id: str  # sheet-music / bouzouki demo on YouTube
    artist: Artist


class Catalog:
    """All artists and songs, loaded once. Image bytes stay in the DB."""

    def __init__(self, artists: list[Artist]):
        self.artists = artists
        self.songs = [s for a in artists for s in a.songs]
        self.artist_by_slug = {a.slug: a for a in artists}
        self.song_by_slug = {s.slug: s for s in self.songs}
        # Old URLs used the English name; first match wins for the few duplicate titles.
        self.artist_by_name = {a.en_name: a for a in artists}
        self.song_by_name: dict[str, Song] = {}
        for s in self.songs:
            self.song_by_name.setdefault(s.en_name, s)


def load_catalog(path: Path | None = None) -> Catalog:
    path = Path(path or db_path())
    # Read-only: the app never writes, and a missing file must not create an empty DB.
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10.0)
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version < REQUIRED_VERSION:
            raise RuntimeError(
                f"{path} is at schema version {version}, need {REQUIRED_VERSION}: "
                "run `uv run python db_migrate.py up`"
            )
        artists = {
            row[0]: Artist(row[0], row[1], row[2], row[3], bool(row[4]))
            for row in conn.execute(
                "SELECT artist_id, slug, en_name, gr_name, artist_img IS NOT NULL FROM artists ORDER BY artist_id"
            )
        }
        for row in conn.execute(
            "SELECT song_id, artist_id, slug, en_name, gr_name, video_id, demo_id FROM songs ORDER BY song_id"
        ):
            artist = artists[row[1]]
            artist.songs.append(Song(row[0], row[2], row[3], row[4], row[5], row[6], artist))
    finally:
        conn.close()
    catalog = Catalog(list(artists.values()))
    logger.info(f"Loaded {len(catalog.artists)} artists and {len(catalog.songs)} songs")
    return catalog


def load_artist_image(artist_id: int, path: Path | None = None) -> bytes | None:
    conn = sqlite3.connect(f"file:{Path(path or db_path())}?mode=ro", uri=True, timeout=10.0)
    try:
        row = conn.execute("SELECT artist_img FROM artists WHERE artist_id = ?", (artist_id,)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None
