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
        self.fail_put = set()
        self.corrupt = set()  # keys whose stored copy does not match what was sent
        self.delete_errors = []

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        o = self.objects[Key]
        return {"ContentLength": len(o["Body"]), "Metadata": o["Metadata"], "ContentType": o["ContentType"]}

    def put_object(self, Bucket, Key, Body, ContentType, Metadata):
        if Key in self.fail_put:
            raise RuntimeError("network down")
        self.puts += 1
        meta = dict(Metadata, sha256="corrupt") if Key in self.corrupt else Metadata
        self.objects[Key] = {"Body": Body, "ContentType": ContentType, "Metadata": meta}

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
    for f in folders:
        d = root / f["artist"] / f["song"]
        d.mkdir(parents=True)
        for name in (x["name"] for x in f["files"]):
            (d / name).write_bytes(b"?" * next(x["size"] for x in f["files"] if x["name"] == name))
    contents = {  # real bytes for the PDFs
        ("ΑΛΑΝΙΑΡΗΣ", f"ΑΛΑΝΙΑΡΗΣ - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ.pdf"): b"%PDF-sheet-1",
        ("ΑΛΑΝΙΑΡΗΣ", f"ΑΛΑΝΙΑΡΗΣ - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ {TAB}.pdf"): b"%PDF-tab-1",
        ("ΠΥΡΕΤΟΣ", "ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf"): b"%PDF-sheet-2",
        ("ΜΕΛΩΔΙΑ ΣΕ 5", "ΜΕΛΩΔΙΑ ΣΕ 5 - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ.pdf"): b"%PDF-sheet-3",
        ("ΜΕΛΩΔΙΑ 58", "ΜΕΛΩΔΙΑ 58 - ΒΑΜΒΑΚΑΡΗΣ ΜΑΡΚΟΣ.pdf"): b"%PDF-sheet-4",
    }
    for f in folders:
        for (song, name), data in contents.items():
            if f["song"] == song:
                (root / f["artist"] / f["song"] / name).write_bytes(data)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"songs": folders}), encoding="utf-8")
    return root, manifest, folders


def apply(world, **extra):
    root, manifest, _ = world
    return pdf_sync.cmd_apply(argparse.Namespace(manifest=str(manifest), root=str(root), dry_run=False, workers=2, **extra))


def keys_in_db(db):
    return dict(((r[0]), (r[1], r[2])) for r in sqlite3.connect(db).execute("SELECT song_id, score_key, tab_key FROM songs"))


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
def test_keys_depend_only_on_song_id():
    assert pdf_sync.object_key(7, "sheet") == "pdf/7/sheet.pdf" and pdf_sync.object_key(7, "tab") == "pdf/7/tab.pdf"


def test_renaming_songs_and_artists_leaves_keys_and_bucket_untouched(db, world, s3):
    assert apply(world) == 0
    before, puts = keys_in_db(db), s3.puts
    conn = sqlite3.connect(db)
    conn.execute("UPDATE songs SET gr_name = 'νεο ονομα', slug = 'new-slug'")
    conn.execute("UPDATE artists SET gr_name = 'αλλος καλλιτεχνης'")
    conn.commit()
    assert keys_in_db(db) == before
    assert pdf_sync.verify(s3, "test-bucket", conn) == []  # still perfectly in sync
    assert s3.puts == puts


# ------------------------------------------------------------------ apply
def test_apply_uploads_verifies_and_writes_keys_then_does_nothing_the_second_time(db, world, s3):
    assert apply(world) == 0
    assert sorted(s3.objects) == ["pdf/1/sheet.pdf", "pdf/1/tab.pdf", "pdf/2/sheet.pdf", "pdf/3/sheet.pdf", "pdf/4/sheet.pdf"]
    meta = s3.objects["pdf/1/tab.pdf"]
    assert meta["ContentType"] == "application/pdf" and meta["Metadata"]["song-id"] == "1" and meta["Metadata"]["demo-id"] == "AAAAAAAAAAA"
    assert keys_in_db(db) == {1: ("pdf/1/sheet.pdf", "pdf/1/tab.pdf"), 2: ("pdf/2/sheet.pdf", None),
                              3: ("pdf/3/sheet.pdf", None), 4: ("pdf/4/sheet.pdf", None), 5: (None, None)}
    puts = s3.puts
    assert apply(world) == 0 and s3.puts == puts  # idempotent


def test_only_changed_files_are_uploaded_again(db, world, s3):
    root = world[0]
    apply(world)
    puts = s3.puts
    path = root / "ΠΑΝΟΥ ΑΚΗΣ" / "ΠΥΡΕΤΟΣ" / "ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf"
    path.write_bytes(b"%PDF-sheet-X")  # same size, different content
    assert apply(world) == 0 and s3.puts == puts + 1 and s3.objects["pdf/2/sheet.pdf"]["Body"] == b"%PDF-sheet-X"


def test_a_failed_upload_gets_no_key_and_the_rest_still_goes_through(db, world, s3):
    s3.fail_put.add("pdf/1/tab.pdf")
    assert apply(world) == 1
    keys = keys_in_db(db)
    assert keys[1] == ("pdf/1/sheet.pdf", None) and keys[2] == ("pdf/2/sheet.pdf", None)  # no key without an object


def test_a_stale_manifest_is_refused_for_that_file_only(db, world, s3):
    root, manifest, folders = world
    folders[1]["files"][0]["size"] += 1
    manifest.write_text(json.dumps({"songs": folders}), encoding="utf-8")
    assert apply(world) == 1
    assert "pdf/2/sheet.pdf" not in s3.objects and keys_in_db(db)[2] == (None, None)
    assert keys_in_db(db)[1] == ("pdf/1/sheet.pdf", "pdf/1/tab.pdf")  # the other files still went through


def test_dry_run_changes_nothing(db, world, s3):
    root, manifest, _ = world
    assert pdf_sync.cmd_apply(argparse.Namespace(manifest=str(manifest), root=str(root), dry_run=True, workers=2)) == 0
    assert s3.objects == {} and keys_in_db(db)[1] == (None, None)


# ------------------------------------------------------------------ verify / prune
def test_verify_reports_missing_orphans_and_wrong_metadata(db, world, s3):
    apply(world)
    conn = sqlite3.connect(db)
    assert pdf_sync.verify(s3, "test-bucket", conn, deep=True) == []
    del s3.objects["pdf/2/sheet.pdf"]
    s3.objects["pdf/99/sheet.pdf"] = {"Body": b"x", "ContentType": "application/pdf", "Metadata": {}}
    s3.objects["pdf/3/sheet.pdf"]["Metadata"]["song-id"] = "8"
    problems = pdf_sync.verify(s3, "test-bucket", conn, deep=True)
    assert "missing in bucket: pdf/2/sheet.pdf" in problems
    assert "orphan in bucket: pdf/99/sheet.pdf" in problems
    assert "wrong metadata: pdf/3/sheet.pdf" in problems


def test_verify_flags_keys_that_do_not_follow_the_convention(db, world, s3):
    apply(world)
    conn = sqlite3.connect(db)
    conn.execute("UPDATE songs SET score_key = 'pdf/elsewhere.pdf' WHERE song_id = 1")
    assert any(p.startswith("unexpected key") for p in pdf_sync.verify(s3, "test-bucket", conn))


def test_prune_is_a_dry_run_unless_told_otherwise(db, world, s3):
    apply(world)
    s3.objects["pdf/99/sheet.pdf"] = {"Body": b"x", "ContentType": "application/pdf", "Metadata": {}}
    pdf_sync.cmd_prune(argparse.Namespace(yes=False, force=False))
    assert "pdf/99/sheet.pdf" in s3.objects
    pdf_sync.cmd_prune(argparse.Namespace(yes=True, force=False))
    assert "pdf/99/sheet.pdf" not in s3.objects and "pdf/1/sheet.pdf" in s3.objects


def test_a_manifest_cannot_make_the_script_read_outside_the_download_folder(db, world, s3):
    root, manifest, folders = world
    folders[1]["files"][0]["name"] = "../../../outside.pdf"
    manifest.write_text(json.dumps({"songs": folders}), encoding="utf-8")
    assert apply(world) == 1 and "pdf/2/sheet.pdf" not in s3.objects


# ------------------------------------------------------------------ review findings
def test_empty_and_non_pdf_files_are_never_uploaded(db, world, s3):
    root = world[0]
    for content in (b"", b"<html>404 not found</html>"):
        (root / "ΠΑΝΟΥ ΑΚΗΣ" / "ΠΥΡΕΤΟΣ" / "ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf").write_bytes(content)
        assert apply(world) == 1
        assert "pdf/2/sheet.pdf" not in s3.objects and keys_in_db(db)[2] == (None, None)


def test_a_key_is_not_written_when_the_stored_object_does_not_match_what_was_sent(db, world, s3):
    s3.corrupt.add("pdf/1/sheet.pdf")
    assert apply(world) == 1
    assert keys_in_db(db)[1] == (None, "pdf/1/tab.pdf")


def test_a_crashed_run_is_repaired_by_the_next_one_without_uploading_again(db, world, s3):
    apply(world)
    conn = sqlite3.connect(db)
    conn.execute("UPDATE songs SET score_key = NULL, tab_key = NULL")  # objects uploaded, keys lost
    conn.commit()
    puts = s3.puts
    assert apply(world) == 0 and s3.puts == puts
    assert keys_in_db(db)[1] == ("pdf/1/sheet.pdf", "pdf/1/tab.pdf")


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
    for n in range(100, 112):
        s3.objects[f"pdf/{n}/sheet.pdf"] = {"Body": b"x", "ContentType": "application/pdf", "Metadata": {}}
    assert pdf_sync.cmd_prune(argparse.Namespace(yes=True, force=False)) == 1 and len(s3.objects) == 17
    assert pdf_sync.cmd_prune(argparse.Namespace(yes=True, force=True)) == 0 and len(s3.objects) == 5


def test_prune_reports_objects_the_bucket_refused_to_delete(db, world, s3):
    apply(world)
    s3.objects["pdf/99/sheet.pdf"] = {"Body": b"x", "ContentType": "application/pdf", "Metadata": {}}
    s3.delete_errors = [{"Key": "pdf/99/sheet.pdf", "Message": "denied"}]
    assert pdf_sync.cmd_prune(argparse.Namespace(yes=True, force=False)) == 1


def test_a_symlink_pointing_outside_the_download_folder_is_refused(db, world, s3, tmp_path):
    root, manifest, folders = world
    secret = tmp_path / "outside.pdf"
    secret.write_bytes(b"%PDF-sheet-2")
    (root / "ΠΑΝΟΥ ΑΚΗΣ" / "ΠΥΡΕΤΟΣ" / "ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf").unlink()
    (root / "ΠΑΝΟΥ ΑΚΗΣ" / "ΠΥΡΕΤΟΣ" / "ΠΥΡΕΤΟΣ - ΠΑΝΟΥ ΑΚΗΣ.pdf").symlink_to(secret)
    assert apply(world) == 1 and "pdf/2/sheet.pdf" not in s3.objects


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
