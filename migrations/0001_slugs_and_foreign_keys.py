"""Short URL slugs, a real artist foreign key, unique names and indexes.

up:   artists gets `slug` (unique) and a unique `en_name`; the redundant
      `number_of_songs` is dropped. songs gets `slug` (unique) and `artist_id`
      (FK, replaces the `artist_name` text join).
down: restores the original schema; `number_of_songs` is recomputed, slugs are lost.
"""

from textkeys import make_slug

DESCRIPTION = "slugs, artist_id foreign key, unique names, indexes"


def _unique_slug(base: str, taken: set[str]) -> str:
    slug, n = base, 2
    while slug in taken:
        slug = f"{base}-{n}"
        n += 1
    taken.add(slug)
    return slug


def up(conn):
    artists = conn.execute("SELECT artist_id, en_name, gr_name, artist_img FROM artists ORDER BY artist_id").fetchall()
    songs = conn.execute("SELECT song_id, artist_name, en_name, gr_name, video_id, demo_id FROM songs ORDER BY song_id").fetchall()
    artist_ids = {a[1]: a[0] for a in artists}
    orphans = [s[0] for s in songs if s[1] not in artist_ids]
    if orphans:
        raise RuntimeError(f"songs without a matching artist: {orphans[:10]}")

    taken: set[str] = set()
    conn.execute("""CREATE TABLE artists_new (
        artist_id INTEGER PRIMARY KEY,
        slug TEXT NOT NULL UNIQUE,
        en_name TEXT NOT NULL UNIQUE,
        gr_name TEXT NOT NULL,
        artist_img BLOB)""")
    conn.executemany("INSERT INTO artists_new VALUES (?, ?, ?, ?, ?)",
                     [(a[0], _unique_slug(make_slug(a[1]), taken), a[1], a[2], a[3]) for a in artists])

    taken = set()
    conn.execute("""CREATE TABLE songs_new (
        song_id INTEGER PRIMARY KEY,
        artist_id INTEGER NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
        slug TEXT NOT NULL UNIQUE,
        en_name TEXT NOT NULL,
        gr_name TEXT NOT NULL,
        video_id TEXT NOT NULL,
        demo_id TEXT NOT NULL)""")
    conn.executemany("INSERT INTO songs_new VALUES (?, ?, ?, ?, ?, ?, ?)",
                     [(s[0], artist_ids[s[1]], _unique_slug(make_slug(s[2]), taken), s[2], s[3], s[4], s[5]) for s in songs])

    conn.execute("DROP TABLE songs")
    conn.execute("DROP TABLE artists")
    conn.execute("ALTER TABLE artists_new RENAME TO artists")
    conn.execute("ALTER TABLE songs_new RENAME TO songs")
    conn.execute("CREATE INDEX idx_songs_artist ON songs(artist_id)")


def down(conn):
    conn.execute("""CREATE TABLE artists_old (
        artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        en_name TEXT NOT NULL,
        gr_name TEXT NOT NULL,
        number_of_songs INTEGER NOT NULL,
        artist_img BLOB)""")
    conn.execute("""INSERT INTO artists_old
        SELECT a.artist_id, a.en_name, a.gr_name,
               (SELECT COUNT(*) FROM songs s WHERE s.artist_id = a.artist_id), a.artist_img
        FROM artists a ORDER BY a.artist_id""")
    conn.execute("""CREATE TABLE songs_old (
        song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist_name TEXT NOT NULL,
        en_name TEXT NOT NULL,
        gr_name TEXT NOT NULL,
        video_id TEXT NOT NULL,
        demo_id TEXT NOT NULL)""")
    conn.execute("""INSERT INTO songs_old
        SELECT s.song_id, a.en_name, s.en_name, s.gr_name, s.video_id, s.demo_id
        FROM songs s JOIN artists a ON a.artist_id = s.artist_id ORDER BY s.song_id""")
    conn.execute("DROP TABLE songs")
    conn.execute("DROP TABLE artists")
    conn.execute("ALTER TABLE artists_old RENAME TO artists")
    conn.execute("ALTER TABLE songs_old RENAME TO songs")
