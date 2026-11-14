"""R2 object keys of each song's sheet-music and tablature PDFs.

The keys are opaque random strings (`pdf/<12 random chars>.pdf`, see pdf_sync.py), never derived from
names, so renaming a song or artist leaves the bucket untouched. NULL = the song has no such PDF
(no button). Meant to be filled by a sync script (planned), only after the object is verified in the bucket.

up:   adds `score_key` and `tab_key` (TEXT, NULL).
down: drops both columns (the PDFs in the bucket stay untouched).
"""

DESCRIPTION = "songs.score_key / songs.tab_key"


def up(conn):
    conn.execute("ALTER TABLE songs ADD COLUMN score_key TEXT")
    conn.execute("ALTER TABLE songs ADD COLUMN tab_key TEXT")


def down(conn):
    conn.execute("ALTER TABLE songs DROP COLUMN tab_key")
    conn.execute("ALTER TABLE songs DROP COLUMN score_key")
