import io
import sqlite3

import pytest

import db_migrate

LEGACY = """
CREATE TABLE artists (artist_id INTEGER PRIMARY KEY AUTOINCREMENT, en_name TEXT NOT NULL, gr_name TEXT NOT NULL,
    number_of_songs INTEGER NOT NULL, artist_img BLOB);
CREATE TABLE songs (song_id INTEGER PRIMARY KEY AUTOINCREMENT, artist_name TEXT NOT NULL, en_name TEXT NOT NULL,
    gr_name TEXT NOT NULL, video_id TEXT NOT NULL, demo_id TEXT NOT NULL);
INSERT INTO artists VALUES (1, 'Vamvakaris Markos', 'Βαμβακαρης Μαρκος', 2, x'89504e47'), (2, 'Panoy Akis', 'Πανου Ακης', 1, NULL);
INSERT INTO songs VALUES (1, 'Vamvakaris Markos', 'Pyretos', 'πυρετος', 'v1', 'd1'),
    (2, 'Panoy Akis', 'Pyretos', 'πυρετος', 'v2', 'd2'),
    (4, 'Vamvakaris Markos', 'Adika Me Katakrinoyn', 'αδiκα με κατακρινουν', 'v4', 'd4');
"""


def rows(path, table, order):
    conn = sqlite3.connect(path)
    try:
        return conn.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall()
    finally:
        conn.close()


@pytest.fixture
def legacy_db(tmp_path):
    path = tmp_path / "music.db"
    conn = sqlite3.connect(path)
    conn.executescript(LEGACY)
    conn.close()
    return path


def test_up_adds_slugs_fk_and_fixes_names(legacy_db):
    assert db_migrate.migrate(legacy_db, "up") == 3
    songs = rows(legacy_db, "songs", "song_id")
    assert [s[2] for s in songs] == ["pyretos", "pyretos-2", "adika-katakrinoyn"]
    assert songs[0][1] == 1 and songs[1][1] == 2  # artist_id
    assert songs[2][4] == "αδικα με κατακρινουν"  # Latin 'i' replaced
    conn = sqlite3.connect(legacy_db)
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 3


def test_round_trip_restores_original_data(legacy_db):
    before = (rows(legacy_db, "artists", "artist_id"), rows(legacy_db, "songs", "song_id"))
    db_migrate.migrate(legacy_db, "up")
    assert db_migrate.migrate(legacy_db, "down", 3) == 0
    assert (rows(legacy_db, "artists", "artist_id"), rows(legacy_db, "songs", "song_id")) == before
    assert db_migrate.migrate(legacy_db, "up") == 3


def test_orphan_song_aborts_and_leaves_db_untouched(legacy_db):
    conn = sqlite3.connect(legacy_db)
    conn.execute("INSERT INTO songs VALUES (9, 'Nobody', 'X', 'χ', 'v', 'd')")
    conn.commit()
    conn.close()
    with pytest.raises(RuntimeError):
        db_migrate.migrate(legacy_db, "up")
    assert sqlite3.connect(legacy_db).execute("PRAGMA user_version").fetchone()[0] == 0
    assert len(rows(legacy_db, "songs", "song_id")) == 4


def test_thumbnail_is_created_for_valid_images_and_skipped_for_broken_ones(legacy_db):
    from PIL import Image

    png = io.BytesIO()
    Image.new("RGB", (40, 30), "orange").save(png, "PNG")
    conn = sqlite3.connect(legacy_db)
    conn.execute("UPDATE artists SET artist_img = ? WHERE artist_id = 2", (png.getvalue(),))  # 1 keeps its invalid bytes
    conn.commit()
    conn.close()
    db_migrate.migrate(legacy_db, "up")
    conn = sqlite3.connect(legacy_db)
    thumbs = dict(conn.execute("SELECT artist_id, artist_thumb FROM artists").fetchall())
    assert thumbs[2][:4] == b"RIFF" and thumbs[1] is None
