import argparse
import json
import sqlite3

import pytest
from botocore.exceptions import ClientError

import pdf_sync
import storage

TAB = "ΤΑΜΠΛΑΤΟΥΡΑ"


class FakeS3:
    """Just enough of the S3 client that pdf_sync uses."""

    def __init__(self):
        self.objects = {}
        self.puts = 0
        self.copies = 0
        self.fail_put = set()  # (song-id, kind) whose upload raises
        self.corrupt = set()  # (song-id, kind) whose stored copy does not match what was sent
        self.fail_copy = set()  # old keys whose copy raises
        self.corrupt_copy = False
        self.crash_on_put = None  # the n-th put kills the whole run
        self.delete_errors = []

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        o = self.objects[Key]
        return {"ContentLength": len(o["Body"]), "Metadata": o["Metadata"], "ContentType": o["ContentType"]}

    def put_object(self, Bucket, Key, Body, ContentType, Metadata):
        tag = (Metadata.get("song-id"), Metadata.get("kind"))
        if tag in self.fail_put:
            raise RuntimeError("network down")
        if self.crash_on_put is not None and self.puts + 1 >= self.crash_on_put:
            raise SystemExit("the process died")
        self.puts += 1
        meta = dict(Metadata, sha256="corrupt") if tag in self.corrupt else Metadata
        self.objects[Key] = {"Body": Body, "ContentType": ContentType, "Metadata": meta}

    def copy_object(self, Bucket, Key, CopySource, MetadataDirective, ContentType, Metadata):
        if CopySource["Key"] in self.fail_copy:
            raise RuntimeError("copy refused")
        self.copies += 1
        source = self.objects[CopySource["Key"]]
        meta = dict(Metadata, sha256="corrupt") if self.corrupt_copy else dict(Metadata)
        self.objects[Key] = {"Body": source["Body"], "ContentType": ContentType, "Metadata": meta}

    def get_paginator(self, name):
        fake = self

        class Pages:
            def paginate(self, Bucket, Prefix):
                return [{"Contents": [{"Key": k, "Size": len(o["Body"])} for k, o in fake.objects.items() if k.startswith(Prefix)]}]

        return Pages()

    def delete_objects(self, Bucket, Delete):
        if self.delete_errors:
            return {"Errors": self.delete_errors}
        for entry in Delete["Objects"]:
            self.objects.pop(entry["Key"], None)
        return {}


SONGS = [  # song_id, artist_id, slug, gr_name, demo_id
    (1, 1, "alaniaris", "αλανιαρης", "AAAAAAAAAAA"),
    (2, 2, "pyretos", "πυρετος", "BBBBBBBBBBB"),
    (3, 1, "melodia-5", "μελωδια σε 5", "CCCCCCCCCCC"),  # shares its video id with the next one, like in the real DB
    (4, 1, "melodia-58", "μελωδια 58", "CCCCCCCCCCC"),
    (5, 2, "xoris", "χωρις", "EEEEEEEEEEE"),
]
ORPHAN = "pdf/zzzzzzzzzzzz.pdf"


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = tmp_path / "music.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE artists (artist_id INTEGER PRIMARY KEY, gr_name TEXT);"
        "CREATE TABLE songs (song_id INTEGER PRIMARY KEY, artist_id INTEGER, slug TEXT, en_name TEXT, gr_name TEXT,"
        " video_id TEXT, demo_id TEXT, score_key TEXT, tab_key TEXT);"
        "INSERT INTO artists VALUES (1, 'βαμβακαρης μαρκος'), (2, 'πανου ακης');"
    )
    conn.executemany("INSERT INTO songs VALUES (?, ?, ?, ?, ?, 'v', ?, NULL, NULL)", [(i, a, s, s, g, d) for i, a, s, g, d in SONGS])
    conn.commit()
    conn.close()
    monkeypatch.setattr(pdf_sync, "db_path", lambda: path)
    return path


@pytest.fixture
def s3(monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(storage, "client", lambda: fake)
    monkeypatch.setattr(storage, "bucket", lambda: "test-bucket")
    return fake


def folder(artist, song, video_id, pdfs):
    link = {"value": f"{song}\nVideo Link: https://www.youtube.com/watch?v={video_id}"} if video_id else None
    return {"artist": artist, "song": song, "link": link,
            "files": [{"name": n, "size": len(b)} for n, b in pdfs.items()] + [{"name": "x.mp3", "size": 3}]}


@pytest.fixture
def world(tmp_path):
    """A manifest and matching files on disk, in the shape of the Patreon download folder."""
    root = tmp_path / "downloads"
    folders = [
        folder("ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ", "ΑΛΑΝΙΑΡΗΣ", "AAAAAAAAAAA",
               {"ΑΛΑΝΙΑΡΗΣ - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ.pdf": b"%PDF-sheet-1", f"ΑΛΑΝΙΑΡΗΣ - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ {TAB}.pdf": b"%PDF-tab-1"}),
        folder("ΠΑΝΟΥ ΑΚΗΣ", "ΠΥΡΕΤΟΣ", "BBBBBBBBBBB", {"ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf": b"%PDF-sheet-2"}),  # sheet only
        folder("ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ", "ΜΕΛΩΔΙΑ ΣΕ 5", None, {"ΜΕΛΩΔΙΑ ΣΕ 5 - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ.pdf": b"%PDF-sheet-3"}),  # no link file
        folder("ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ", "ΜΕΛΩΔΙΑ 58", "CCCCCCCCCCC", {"ΜΕΛΩΔΙΑ 58 - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ.pdf": b"%PDF-sheet-4"}),
        folder("ΠΑΝΟΥ ΑΚΗΣ", "ΧΩΡΙΣ", "EEEEEEEEEEE", {}),  # no PDF at all
    ]
    contents = {
        ("ΑΛΑΝΙΑΡΗΣ", "ΑΛΑΝΙΑΡΗΣ - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ.pdf"): b"%PDF-sheet-1",
        ("ΑΛΑΝΙΑΡΗΣ", f"ΑΛΑΝΙΑΡΗΣ - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ {TAB}.pdf"): b"%PDF-tab-1",
        ("ΠΥΡΕΤΟΣ", "ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf"): b"%PDF-sheet-2",
        ("ΜΕΛΩΔΙΑ ΣΕ 5", "ΜΕΛΩΔΙΑ ΣΕ 5 - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ.pdf"): b"%PDF-sheet-3",
        ("ΜΕΛΩΔΙΑ 58", "ΜΕΛΩΔΙΑ 58 - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ.pdf"): b"%PDF-sheet-4",
    }
    for f in folders:
        d = root / f["artist"] / f["song"]
        d.mkdir(parents=True)
        for (song, name), data in contents.items():
            if f["song"] == song:
                (d / name).write_bytes(data)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"songs": folders}), encoding="utf-8")
    return root, manifest, folders


def apply(world, **extra):
    root, manifest, _ = world
    return pdf_sync.cmd_apply(argparse.Namespace(manifest=str(manifest), root=str(root), dry_run=False, workers=2, **extra))


def keys_in_db(db):
    return {r[0]: (r[1], r[2]) for r in sqlite3.connect(db).execute("SELECT song_id, score_key, tab_key FROM songs")}


def key_of(db, song_id, kind):
    return keys_in_db(db)[song_id][0 if kind == "sheet" else 1]


def all_keys(db):
    return sorted(k for pair in keys_in_db(db).values() for k in pair if k)


def go_back_to_old_style_keys(db, s3):
    """The state the first upload left: objects under pdf/<song_id>/sheet.pdf, without the `kind` tag."""
    conn = sqlite3.connect(db)
    for song_id, (sheet, tab) in keys_in_db(db).items():
        for kind, key, column in (("sheet", sheet, "score_key"), ("tab", tab, "tab_key")):
            if key:
                old = f"pdf/{song_id}/{kind}.pdf"
                s3.objects[old] = s3.objects.pop(key)
                s3.objects[old]["Metadata"].pop("kind")
                conn.execute(f"UPDATE songs SET {column} = ? WHERE song_id = ?", (old, song_id))
    conn.commit()
    conn.close()


# ------------------------------------------------------------------ matching and choosing
def test_every_folder_is_matched_to_its_own_song_including_shared_video_ids_and_missing_link_files(db, world):
    songs = pdf_sync.load_songs(sqlite3.connect(db))
    matches, items, problems = pdf_sync.build_plan(world[2], songs)
    assert problems == []
    assert {m[1].slug: m[2] for m in matches} == {
        "alaniaris": "demo_id + names", "pyretos": "demo_id + names", "melodia-5": "names only (no link file)",
        "melodia-58": "demo_id + names", "xoris": "demo_id + names"}
    assert sorted((i.song.slug, i.kind) for i in items) == [
        ("alaniaris", "sheet"), ("alaniaris", "tab"), ("melodia-5", "sheet"), ("melodia-58", "sheet"), ("pyretos", "sheet")]


def test_a_folder_is_never_guessed(db, world):
    songs = pdf_sync.load_songs(sqlite3.connect(db))
    wrong_names = folder("ΠΑΝΟΥ ΑΚΗΣ", "ΑΛΛΟ ΤΡΑΓΟΥΔΙ", "AAAAAAAAAAA", {})  # right video id, other names
    unknown = folder("ΠΑΝΟΥ ΑΚΗΣ", "ΑΓΝΩΣΤΟ", None, {})
    duplicate = folder("ΠΑΝΟΥ ΑΚΗΣ", "ΠΥΡΕΤΟΣ", "BBBBBBBBBBB", {})  # a second folder for the same song
    matches, problems = pdf_sync.match_folders([wrong_names, unknown, duplicate, world[2][1]], songs)
    assert matches == []
    assert len(problems) == 3 and sum("conflict" in p for p in problems) == 1 and sum("unmatched" in p for p in problems) == 2  # one message per conflict


def test_tab_typo_partitura_copies_double_spaces_and_swapped_names(db):
    sheet, tab = "ΑΣΦΑΛΩΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf", f"ΑΣΦΑΛΩΣ - ΠΑΝΟΥ ΑΚΗΣ {TAB}.pdf"
    f = folder("ΠΑΝΟΥ ΑΚΗΣ", "ΑΣΦΑΛΩΣ", "X", {
        "ΑΣΦΑΛΩΣ  - ΠΑΝΟΥ ΑΚΗΣ.pdf": b"a", sheet: b"b", tab: b"c", "ΑΣΦΑΛΩΣ - ΑΚΗΣ ΠΑΝΟΥ ΠΑΡΤΙΤΟΥΡΑ.pdf": b"d", "ΑΣΦΑΛΩΣ - ΑΚΗΣ ΠΑΝΟΥ.pdf": b"e"})
    picked, problems = pdf_sync.pick_pdfs(f)
    assert (picked["sheet"]["name"], picked["tab"]["name"], problems) == (sheet, tab, [])
    typo = folder("ΘΕΟΔΩΡΑΚΗΣ ΜΙΚΗΣ", "ΤΗΣ ΞΕΝΙΤΙΑΣ (ΦΕΓΓΑΡΙ)", "X", {
        "ΤΗΣ ΞΕΝΙΤΙΑΣ - ΘΕΟΔΩΡΑΚΗΣ ΜΙΚΗΣ ΤΑΜΠΑΛΑΤΟΥΡΑ.pdf": b"t", "ΤΗΣ ΞΕΝΙΤΙΑΣ - ΘΕΟΔΩΡΑΚΗΣ ΜΙΚΗΣ.pdf": b"s"})
    picked, _ = pdf_sync.pick_pdfs(typo)
    assert set(picked) == {"sheet", "tab"}  # a lone candidate is taken even if its name is shorter than the folder's
    partitura = folder("Α", "Β", "X", {"Β - Α ΠΑΡΤΙΤΟΥΡΑ.pdf": b"p", "Β - Α.pdf": b"s"})
    assert pdf_sync.pick_pdfs(partitura)[0]["sheet"]["name"] == "Β - Α.pdf"


def test_a_tie_is_reported_not_decided(db):
    tie = folder("Α", "Β", "X", {"Β - ΑΛΛΟ ΟΝΟΜΑ.pdf": b"2", "Β - ΑΛΛΟ.pdf": b"3"})  # neither is the plain "<song> - <artist>"
    picked, problems = pdf_sync.pick_pdfs(tie)
    assert "sheet" not in picked and "ambiguous sheet" in problems[0]


# ------------------------------------------------------------------ keys and renames
def test_keys_are_random_unique_unrelated_to_ids_and_never_change(db, world, s3):
    assert apply(world) == 0
    keys = all_keys(db)
    assert len(keys) == 5 and len(set(keys)) == 5
    assert all(pdf_sync.KEY_RE.fullmatch(k) for k in keys) and all(len(k) == len("pdf/") + 12 + len(".pdf") for k in keys)
    assert key_of(db, 1, "sheet") != key_of(db, 1, "tab")  # the two files of one song can't be derived from each other
    assert not any(f"/{n}/" in k for k in keys for n in range(1, 6))
    before = keys_in_db(db)
    assert apply(world) == 0 and keys_in_db(db) == before  # a second run keeps every key


def test_renaming_songs_and_artists_leaves_keys_and_bucket_untouched(db, world, s3):
    assert apply(world) == 0
    before, puts = keys_in_db(db), s3.puts
    conn = sqlite3.connect(db)
    conn.execute("UPDATE songs SET gr_name = 'νεο ονομα', slug = 'new-slug'")
    conn.execute("UPDATE artists SET gr_name = 'αλλος καλλιτεχνης'")
    conn.commit()
    assert keys_in_db(db) == before
    assert pdf_sync.verify(s3, "test-bucket", conn, deep=True) == []  # still perfectly in sync
    assert s3.puts == puts


# ------------------------------------------------------------------ apply
def test_apply_uploads_verifies_and_writes_keys_then_does_nothing_the_second_time(db, world, s3):
    assert apply(world) == 0
    keys = keys_in_db(db)
    assert sorted(s3.objects) == all_keys(db) and len(s3.objects) == 5
    assert [(k[0] is not None, k[1] is not None) for _, k in sorted(keys.items())] == [(True, True), (True, False), (True, False), (True, False), (False, False)]
    obj = s3.objects[key_of(db, 1, "tab")]
    assert obj["ContentType"] == "application/pdf" and obj["Body"] == b"%PDF-tab-1"
    assert obj["Metadata"]["song-id"] == "1" and obj["Metadata"]["kind"] == "tab" and obj["Metadata"]["demo-id"] == "AAAAAAAAAAA"
    puts = s3.puts
    assert apply(world) == 0 and s3.puts == puts  # idempotent


def test_only_changed_files_are_uploaded_again(db, world, s3):
    root = world[0]
    apply(world)
    puts = s3.puts
    path = root / "ΠΑΝΟΥ ΑΚΗΣ" / "ΠΥΡΕΤΟΣ" / "ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf"
    path.write_bytes(b"%PDF-sheet-X")  # same size, different content
    assert apply(world) == 0 and s3.puts == puts + 1 and s3.objects[key_of(db, 2, "sheet")]["Body"] == b"%PDF-sheet-X"


def test_a_failed_upload_gets_no_key_and_the_rest_still_goes_through(db, world, s3):
    s3.fail_put.add(("1", "tab"))
    assert apply(world) == 1
    keys = keys_in_db(db)
    assert keys[1][0] and keys[1][1] is None and keys[2][0]  # no key without an object
    assert len(s3.objects) == 4


def test_a_stale_manifest_is_refused_for_that_file_only(db, world, s3):
    root, manifest, folders = world
    folders[1]["files"][0]["size"] += 1
    manifest.write_text(json.dumps({"songs": folders}), encoding="utf-8")
    assert apply(world) == 1
    assert keys_in_db(db)[2] == (None, None) and len(s3.objects) == 4
    assert all(keys_in_db(db)[1])  # the other files still went through


def test_dry_run_changes_nothing(db, world, s3):
    root, manifest, _ = world
    assert pdf_sync.cmd_apply(argparse.Namespace(manifest=str(manifest), root=str(root), dry_run=True, workers=2)) == 0
    assert s3.objects == {} and keys_in_db(db)[1] == (None, None)


def test_keys_are_saved_chunk_by_chunk_so_a_dying_run_loses_no_uploaded_object(db, world, s3, monkeypatch):
    monkeypatch.setattr(pdf_sync, "CHUNK", 2)
    s3.crash_on_put = 3  # the third upload kills the process
    with pytest.raises(SystemExit):
        apply(world)
    saved = all_keys(db)
    assert len(saved) == 2 and sorted(s3.objects) == saved  # everything uploaded so far is referenced
    s3.crash_on_put = None
    assert apply(world) == 0
    assert len(s3.objects) == 5 and sorted(s3.objects) == all_keys(db) and pdf_sync.verify(s3, "test-bucket", sqlite3.connect(db)) == []


# ------------------------------------------------------------------ verify / prune
def test_verify_reports_missing_orphans_wrong_metadata_and_shared_keys(db, world, s3):
    apply(world)
    conn = sqlite3.connect(db)
    assert pdf_sync.verify(s3, "test-bucket", conn, deep=True) == []
    gone, tagged = key_of(db, 2, "sheet"), key_of(db, 3, "sheet")
    del s3.objects[gone]
    s3.objects[ORPHAN] = {"Body": b"x", "ContentType": "application/pdf", "Metadata": {}}
    s3.objects[tagged]["Metadata"]["song-id"] = "8"
    conn.execute("UPDATE songs SET tab_key = ? WHERE song_id = 4", (key_of(db, 4, "sheet"),))  # two columns, one object
    problems = pdf_sync.verify(s3, "test-bucket", conn, deep=True)
    assert f"missing in bucket: {gone}" in problems
    assert f"orphan in bucket: {ORPHAN}" in problems
    assert f"wrong metadata: {tagged}" in problems
    assert f"key used twice: {key_of(db, 4, 'sheet')}" in problems


def test_verify_flags_keys_that_do_not_follow_the_scheme(db, world, s3):
    apply(world)
    conn = sqlite3.connect(db)
    conn.execute("UPDATE songs SET score_key = 'pdf/1/sheet.pdf' WHERE song_id = 1")
    assert any(p.startswith("unexpected key") for p in pdf_sync.verify(s3, "test-bucket", conn))


def test_prune_is_a_dry_run_unless_told_otherwise(db, world, s3):
    apply(world)
    s3.objects[ORPHAN] = {"Body": b"x", "ContentType": "application/pdf", "Metadata": {}}
    pdf_sync.cmd_prune(argparse.Namespace(yes=False, force=False))
    assert ORPHAN in s3.objects
    pdf_sync.cmd_prune(argparse.Namespace(yes=True, force=False))
    assert ORPHAN not in s3.objects and key_of(db, 1, "sheet") in s3.objects


# ------------------------------------------------------------------ rekey
def test_rekey_moves_old_style_keys_to_random_ones_without_uploading(db, world, s3):
    apply(world)
    go_back_to_old_style_keys(db, s3)
    bodies = {k: o["Body"] for k, o in s3.objects.items()}
    assert any(p.startswith("unexpected key") for p in pdf_sync.verify(s3, "test-bucket", sqlite3.connect(db)))
    puts = s3.puts
    assert pdf_sync.cmd_rekey(argparse.Namespace(dry_run=False, keep_old=False)) == 0
    keys = all_keys(db)
    assert len(keys) == 5 and all(pdf_sync.KEY_RE.fullmatch(k) for k in keys)
    assert sorted(s3.objects) == keys  # the old objects are gone
    assert s3.puts == puts and s3.copies == 5  # copied inside the bucket, nothing uploaded
    assert sorted(o["Body"] for o in s3.objects.values()) == sorted(bodies.values())
    assert pdf_sync.verify(s3, "test-bucket", sqlite3.connect(db), deep=True) == []  # incl. the new `kind` tag
    assert list(db.parent.glob("music.db.pre-pdfsync-*.bak"))
    assert pdf_sync.cmd_rekey(argparse.Namespace(dry_run=False, keep_old=False)) == 0 and s3.copies == 5  # nothing left to do


def test_rekey_dry_run_and_keep_old(db, world, s3):
    apply(world)
    go_back_to_old_style_keys(db, s3)
    old = keys_in_db(db)
    assert pdf_sync.rekey(s3, "test-bucket", sqlite3.connect(db), dry_run=True)["to move"] == 5
    assert keys_in_db(db) == old and s3.copies == 0
    pdf_sync.rekey(s3, "test-bucket", sqlite3.connect(db), keep_old=True)
    assert len(s3.objects) == 10 and old[1][0] in s3.objects  # old and new side by side, DB on the new


@pytest.mark.parametrize("what", ["copy_fails", "copy_differs", "old_missing"])
def test_rekey_keeps_the_old_key_and_object_when_a_copy_cannot_be_trusted(db, world, s3, what):
    apply(world)
    go_back_to_old_style_keys(db, s3)
    if what == "copy_fails":
        s3.fail_copy.add("pdf/1/sheet.pdf")
    elif what == "copy_differs":
        s3.corrupt_copy = True
    else:
        del s3.objects["pdf/1/sheet.pdf"]
    result = pdf_sync.rekey(s3, "test-bucket", sqlite3.connect(db))
    assert result["failed"] >= 1
    if what == "copy_differs":
        assert result["moved"] == 0 and all(not pdf_sync.KEY_RE.fullmatch(k) for k in all_keys(db))
        assert all(k in s3.objects for k in all_keys(db))  # the old objects were never deleted
    else:
        assert key_of(db, 1, "sheet") == "pdf/1/sheet.pdf"
        assert result["moved"] == 4 and (what == "old_missing" or "pdf/1/sheet.pdf" in s3.objects)


def test_rekey_reports_objects_that_could_not_be_deleted(db, world, s3):
    apply(world)
    go_back_to_old_style_keys(db, s3)
    s3.delete_errors = [{"Key": "pdf/1/sheet.pdf", "Message": "denied"}]
    result = pdf_sync.rekey(s3, "test-bucket", sqlite3.connect(db))
    assert result["moved"] == 5 and result["old deleted"] == 4 and "pdf/1/sheet.pdf" in s3.objects


# ------------------------------------------------------------------ review findings
def test_empty_and_non_pdf_files_are_never_uploaded(db, world, s3):
    root = world[0]
    for content in (b"", b"<html>404 not found</html>"):
        (root / "ΠΑΝΟΥ ΑΚΗΣ" / "ΠΥΡΕΤΟΣ" / "ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf").write_bytes(content)
        assert apply(world) == 1
        assert keys_in_db(db)[2] == (None, None) and len(s3.objects) == 4


def test_a_key_is_not_written_when_the_stored_object_does_not_match_what_was_sent(db, world, s3):
    s3.corrupt.add(("1", "sheet"))
    assert apply(world) == 1
    keys = keys_in_db(db)
    assert keys[1][0] is None and keys[1][1] is not None


def test_a_run_that_lost_its_keys_uploads_again_under_new_keys_and_the_old_objects_are_orphans(db, world, s3):
    apply(world)
    first = set(s3.objects)
    conn = sqlite3.connect(db)
    conn.execute("UPDATE songs SET score_key = NULL, tab_key = NULL")  # e.g. the DB was restored from an older copy
    conn.commit()
    assert apply(world) == 0
    problems = pdf_sync.verify(s3, "test-bucket", conn)
    assert sorted(p.removeprefix("orphan in bucket: ") for p in problems) == sorted(first)  # the report finds them


def test_each_run_that_changes_the_db_leaves_a_consistent_backup(db, world, s3):
    apply(world)
    backups = list(db.parent.glob("music.db.pre-pdfsync-*.bak"))
    assert len(backups) == 1
    assert sqlite3.connect(backups[0]).execute("SELECT count(*) FROM songs WHERE score_key IS NOT NULL").fetchone()[0] == 0


def test_dry_run_neither_creates_nor_writes_the_db(world, s3, tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_sync, "db_path", lambda: tmp_path / "typo.db")
    with pytest.raises(SystemExit):
        pdf_sync.cmd_apply(argparse.Namespace(manifest=str(world[1]), root=str(world[0]), dry_run=True, workers=1))
    assert not (tmp_path / "typo.db").exists()


def test_prune_refuses_when_the_db_references_nothing(db, world, s3):
    apply(world)
    conn = sqlite3.connect(db)
    conn.execute("UPDATE songs SET score_key = NULL, tab_key = NULL")  # e.g. a wrong or restored DB
    conn.commit()
    assert pdf_sync.cmd_prune(argparse.Namespace(yes=True, force=True)) == 1
    assert len(s3.objects) == 5


def test_prune_refuses_to_delete_a_large_share_of_the_bucket_without_force(db, world, s3):
    apply(world)
    for n in range(12):
        s3.objects[f"pdf/orphan{n:02d}.pdf"] = {"Body": b"x", "ContentType": "application/pdf", "Metadata": {}}
    assert pdf_sync.cmd_prune(argparse.Namespace(yes=True, force=False)) == 1 and len(s3.objects) == 17
    assert pdf_sync.cmd_prune(argparse.Namespace(yes=True, force=True)) == 0 and len(s3.objects) == 5


def test_prune_reports_objects_the_bucket_refused_to_delete(db, world, s3):
    apply(world)
    s3.objects[ORPHAN] = {"Body": b"x", "ContentType": "application/pdf", "Metadata": {}}
    s3.delete_errors = [{"Key": ORPHAN, "Message": "denied"}]
    assert pdf_sync.cmd_prune(argparse.Namespace(yes=True, force=False)) == 1


def test_a_manifest_cannot_make_the_script_read_outside_the_download_folder(db, world, s3):
    root, manifest, folders = world
    folders[1]["files"][0]["name"] = "../../../outside.pdf"
    manifest.write_text(json.dumps({"songs": folders}), encoding="utf-8")
    assert apply(world) == 1 and keys_in_db(db)[2] == (None, None)


def test_a_symlink_pointing_outside_the_download_folder_is_refused(db, world, s3, tmp_path):
    root, manifest, folders = world
    secret = tmp_path / "outside.pdf"
    secret.write_bytes(b"%PDF-sheet-2")
    (root / "ΠΑΝΟΥ ΑΚΗΣ" / "ΠΥΡΕΤΟΣ" / "ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf").unlink()
    (root / "ΠΑΝΟΥ ΑΚΗΣ" / "ΠΥΡΕΤΟΣ" / "ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf").symlink_to(secret)
    assert apply(world) == 1 and keys_in_db(db)[2] == (None, None)


def test_numbers_are_part_of_the_name_and_an_unreadable_link_file_is_only_a_names_match(db, world):
    songs = pdf_sync.load_songs(sqlite3.connect(db))
    five = folder("ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ", "ΜΕΛΩΔΙΑ 5", None, {})  # would equal "μελωδια 58" if digits were dropped
    broken = folder("ΠΑΝΟΥ ΑΚΗΣ", "ΠΥΡΕΤΟΣ", "media.html", {})
    broken["link"] = {"value": "ΠΥΡΕΤΟΣ\nVideo Link: https://www.youtube.com/watch?v=media.html"}
    matches, problems = pdf_sync.match_folders([five, broken], songs)
    assert [(m[1].slug, m[2]) for m in matches] == [("pyretos", "names only (link file has no video id)")]
    assert len(problems) == 1 and "ΜΕΛΩΔΙΑ 5" in problems[0]


def test_plan_asks_for_a_look_at_picked_names_that_do_not_fit_the_folder(db):
    odd = folder("ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ", "ΨΕΥΤΙΚΟΣ ΝΤΟΥΝΙΑΣ", "X", {})
    assert pdf_sync.needs_review(odd, {"name": "ΨΕΥΤΙΚΟΣ ΝΤΟΥΝΙΑΣ - ΠΑΠΑΪΩΑΝΝΟΥ ΓΙΑΝΝΗΣ.pdf"})
    assert pdf_sync.needs_review(odd, {"name": "ΨΕΥΤΙΚΟΣ ΝΤΟΥΝΙΑΣ - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ ΠΑΡΤΙΤΟΥΡΑ.pdf"})
    assert not pdf_sync.needs_review(odd, {"name": "ΨΕΥΤΙΚΟΣ ΝΤΟΥΝΙΑΣ - ΜΑΡΚΟΣ ΒΑΜΒΑΚΑΡΗΣ ΤΑΜΠΛΑΤΟΥΡΑ.pdf"})  # artist words in another order


# ------------------------------------------------------------------ report
def test_report_lists_what_needs_a_human_look(db, world, s3):
    songs = pdf_sync.load_songs(sqlite3.connect(db))
    r = pdf_sync.build_report(world[2], songs)
    assert r["unmatched_folders"] == [] and r["songs_without_folder"] == []
    assert [s.slug for s in r["no_pdf"]] == ["xoris"]
    assert sorted((s.slug, k) for s, k in r["one_kind"]) == [("melodia-5", "sheet"), ("melodia-58", "sheet"), ("pyretos", "sheet")]
    assert [(s.slug, how) for _, s, how in r["names_only"]] == [("melodia-5", "names only (no link file)")]
    assert len(r["to_upload"]) == 5 and r["stale_keys"] == []


def test_report_suggests_the_closest_songs_for_a_folder_that_matches_nothing(db, world):
    folders = [f for f in world[2] if f["song"] != "ΧΩΡΙΣ"] + [folder("ΠΑΝΟΥ ΑΚΗΣ", "ΧΩΡΙΣΑ", None, {})]  # a typo'd folder
    r = pdf_sync.build_report(folders, pdf_sync.load_songs(sqlite3.connect(db)))
    assert [s.slug for s in r["songs_without_folder"]] == ["xoris"]
    (bad, near, why), = r["unmatched_folders"]
    assert bad["song"] == "ΧΩΡΙΣΑ" and near[0].slug == "xoris" and why


def test_report_after_apply_has_nothing_to_upload_and_flags_stale_keys(db, world, s3):
    apply(world)
    conn = sqlite3.connect(db)
    conn.execute("UPDATE songs SET tab_key = 'pdf/abcdefghijkl.pdf' WHERE song_id = 2")  # a key whose file is not in the folders
    conn.commit()
    r = pdf_sync.build_report(world[2], pdf_sync.load_songs(conn))
    assert r["to_upload"] == [] and [(s.slug, k) for s, k in r["stale_keys"]] == [("pyretos", "tab")]


def test_report_command_exit_code_is_1_only_when_something_needs_action(db, world, capsys):
    root, manifest, folders = world
    assert pdf_sync.cmd_report(argparse.Namespace(manifest=str(manifest))) == 0
    manifest.write_text(json.dumps({"songs": folders + [folder("ΠΑΝΟΥ ΑΚΗΣ", "ΑΓΝΩΣΤΟ", None, {})]}), encoding="utf-8")
    assert pdf_sync.cmd_report(argparse.Namespace(manifest=str(manifest))) == 1
    assert "ΑΓΝΩΣΤΟ" in capsys.readouterr().out
