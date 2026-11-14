"""Latin letters typed inside Greek song names (e.g. 'αδiκα' with a Latin i)."""

DESCRIPTION = "replace stray Latin letters in three Greek song names"

FIXES = [
    (4, "αδiκα με κατακρινουν", "αδικα με κατακρινουν"),
    (361, "nα ' τανε το '21", "να ' τανε το '21"),
    (1036, "ακου βρε φιλe", "ακου βρε φιλε"),
]


def up(conn):
    for song_id, old, new in FIXES:
        conn.execute("UPDATE songs SET gr_name = ? WHERE song_id = ? AND gr_name = ?", (new, song_id, old))


def down(conn):
    for song_id, old, new in FIXES:
        conn.execute("UPDATE songs SET gr_name = ? WHERE song_id = ? AND gr_name = ?", (old, song_id, new))
