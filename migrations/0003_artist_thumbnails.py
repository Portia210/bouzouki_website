"""WebP thumbnails for artist images.

The original portraits are 360 px PNG screenshots (up to 250 KB, 9 MB for the home page).
A WebP copy is ~10x smaller; the app serves it and falls back to the original when it is
missing. Needs Pillow (dev dependency), only when this migration is applied.

up:   adds `artist_thumb BLOB` and fills it. Images that can't be decoded are left NULL.
down: drops the column (the originals stay untouched).
"""

import io

DESCRIPTION = "artist_thumb WebP column"


def up(conn):
    from PIL import Image  # dev-only dependency, imported here so `down` and `status` work without it

    conn.execute("ALTER TABLE artists ADD COLUMN artist_thumb BLOB")
    for artist_id, data in conn.execute("SELECT artist_id, artist_img FROM artists WHERE artist_img IS NOT NULL").fetchall():
        try:
            out = io.BytesIO()
            Image.open(io.BytesIO(data)).convert("RGB").save(out, "WEBP", quality=82, method=6)
        except Exception as error:  # noqa: BLE001 - corrupt source image: keep the original only
            print(f"  artist {artist_id}: no thumbnail ({error})")
            continue
        conn.execute("UPDATE artists SET artist_thumb = ? WHERE artist_id = ?", (out.getvalue(), artist_id))


def down(conn):
    conn.execute("ALTER TABLE artists DROP COLUMN artist_thumb")
