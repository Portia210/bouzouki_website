"""Keep the Patreon sheet-music PDFs, the private R2 bucket and `songs.score_key/tab_key` in sync.

    uv run python pdf_sync.py plan   --manifest M.json              # matches + picked files, no network, no writes
    uv run python pdf_sync.py apply  --manifest M.json --root DIR   # upload what is missing/changed, then write keys
    uv run python pdf_sync.py verify [--deep]                       # DB <-> bucket: 0 missing and 0 orphans
    uv run python pdf_sync.py prune  [--yes]                        # delete orphans (dry run without --yes)

Full logic, the manifest format and how to add other file types (mp3, mid, sib):
scripts/pdf_audit/UPLOAD_LOGIC.md
"""

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from classes import db_path
from textkeys import phonetic_key


@dataclass(frozen=True)
class Kind:
    column: str  # `songs` column that stores the object key
    filename: str  # last part of the object key


# To upload another file type, add its Kind here (plus a migration for the column) — see UPLOAD_LOGIC.md.
KINDS = {"sheet": Kind("score_key", "sheet.pdf"), "tab": Kind("tab_key", "tab.pdf")}
KEY_PREFIX = "pdf/"
CONTENT_TYPE = "application/pdf"

TAB_RE = re.compile(r"ΤΑΜΠ\S*ΤΟΥΡΑ")  # "ΤΑΜΠΛΑΤΟΥΡΑ" and the typo "ΤΑΜΠΑΛΑΤΟΥΡΑ" seen in the folders
SCORE_WORD = "ΠΑΡΤΙΤΟΥΡΑ"  # an alternate full score next to the plain sheet; never preferred


class DbSong(NamedTuple):
    song_id: int
    slug: str
    song_gr: str
    demo_id: str
    artist_gr: str
    score_key: str | None
    tab_key: str | None


@dataclass
class Item:
    song: DbSong
    kind: str
    folder: dict
    file: dict  # {"name", "size"} from the manifest

    @property
    def key(self) -> str:
        return object_key(self.song.song_id, self.kind)


def object_key(song_id: int, kind: str) -> str:
    """Derived from the immutable song_id only: renaming a song or artist never changes it."""
    return f"{KEY_PREFIX}{song_id}/{KINDS[kind].filename}"


def demo_id(link) -> str | None:
    text = link.get("value") if isinstance(link, dict) else link
    match = re.search(r"v=([\w-]{11})", text or "")
    return match.group(1) if match else None


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text).upper()


def name_key(text: str) -> tuple:
    """Phonetic key plus the numbers: the key alone drops digits, so "ΜΕΛΩΔΙΑ 5" would equal "ΜΕΛΩΔΙΑ 58"."""
    return (phonetic_key(text), tuple(re.findall(r"\d+", text)))


def _label(folder: dict) -> str:
    return f"{folder['artist']} / {folder['song']}"


# ------------------------------------------------------------------ matching
def match_folders(folders: list[dict], songs: list[DbSong]):
    """Folder -> DB song. A folder is accepted only when its Greek names (phonetic key) agree with the
    song, and its `video link.txt` agrees too when there is one. Everything else is a problem, never a guess."""
    by_demo, by_names = defaultdict(list), defaultdict(list)
    for s in songs:
        by_demo[s.demo_id].append(s)
        by_names[(name_key(s.artist_gr), name_key(s.song_gr))].append(s)

    claims, problems = defaultdict(list), []
    for f in folders:
        names = (name_key(f["artist"]), name_key(f["song"]))
        did = demo_id(f.get("link"))
        if did:
            pool = [s for s in by_demo.get(did, []) if (name_key(s.artist_gr), name_key(s.song_gr)) == names]
            how = "demo_id + names"
        else:
            # No usable video id: the names (and numbers) must agree exactly, and `plan` lists it as a NOTE.
            pool, how = by_names.get(names, []), "names only (" + ("link file has no video id" if f.get("link") else "no link file") + ")"
        if len(pool) != 1:
            why = "no song with these names" if not pool else "several songs fit"
            problems.append(f"unmatched: {_label(f)} (video id {did}): {why}")
            continue
        claims[pool[0].song_id].append((f, how, pool[0]))

    matches = []
    for song_id, found in claims.items():
        if len(found) > 1:
            problems.append(f"conflict: song {found[0][2].slug} claimed by " + " | ".join(_label(f) for f, _, _ in found))
        else:
            matches.append((found[0][0], found[0][2], found[0][1]))
    return matches, problems


def pick_pdfs(folder: dict):
    """One sheet and one tab per folder. With several candidates the plain `<song> - <artist>` name wins,
    a ΠΑΡΤΙΤΟΥΡΑ copy never does; a tie is reported, not decided."""
    expected = f"{_nfc(folder['song'])} - {_nfc(folder['artist'])}"
    groups = {"sheet": [], "tab": []}
    for x in folder["files"]:
        if x["name"].lower().endswith(".pdf"):
            stem = _nfc(x["name"][:-4])
            groups["tab" if TAB_RE.search(stem) else "sheet"].append((x, stem))

    def rank(entry):
        base = TAB_RE.sub("", entry[1])
        return (SCORE_WORD in entry[1], " ".join(base.split()) != " ".join(expected.split()), base.strip() != expected)

    picked, problems = {}, []
    for kind, entries in groups.items():
        entries.sort(key=rank)
        if len(entries) > 1 and rank(entries[0]) == rank(entries[1]):
            problems.append(f"ambiguous {kind}: {_label(folder)}: " + " | ".join(e[0]["name"] for e in entries))
        elif entries:
            picked[kind] = entries[0][0]
    return picked, problems


def needs_review(folder: dict, file: dict) -> bool:
    """A picked name that does not look like "<song> - <artist>" (any word order), or is only a ΠΑΡΤΙΤΟΥΡΑ copy."""
    def words(text):  # phonetic_key joins its input into one string, so key every word separately
        return sorted(k for w in re.split(r"[\s\-]+", TAB_RE.sub("", text)) if (k := phonetic_key(w)))

    stem = _nfc(file["name"][:-4])
    return SCORE_WORD in stem or words(stem) != words(f"{folder['song']} {folder['artist']}")


def build_plan(folders: list[dict], songs: list[DbSong]):
    matches, problems = match_folders(folders, songs)
    items = []
    for folder, song, _ in matches:
        picked, issues = pick_pdfs(folder)
        problems += issues
        items += [Item(song, kind, folder, file) for kind, file in picked.items()]
    return matches, items, problems


# ------------------------------------------------------------------ bucket
def head(s3, bucket: str, key: str):
    from botocore.exceptions import ClientError

    try:
        return s3.head_object(Bucket=bucket, Key=key)
    except ClientError as error:
        if error.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
            return None
        raise


def sync_one(s3, bucket: str, item: Item, root: Path, dry_run: bool) -> str:
    path = root / item.folder["artist"] / item.folder["song"] / item.file["name"]
    if not path.resolve().is_relative_to(root.resolve()):  # a manifest with ".." must not read outside the folder
        raise ValueError(f"{path} is outside {root}")
    data = path.read_bytes()
    if not data.startswith(b"%PDF"):  # empty, truncated, or an error page saved as .pdf
        raise ValueError(f"{path.name} is not a PDF ({len(data)} bytes)")
    if len(data) != item.file["size"]:
        raise ValueError(f"{path.name}: {len(data)} bytes on disk, {item.file['size']} in the manifest (stale manifest?)")
    digest = hashlib.sha256(data).hexdigest()
    current = head(s3, bucket, item.key)
    if current and current["ContentLength"] == len(data) and current.get("Metadata", {}).get("sha256") == digest:
        return "unchanged"
    if dry_run:
        return "would upload"
    s3.put_object(
        Bucket=bucket, Key=item.key, Body=data, ContentType=CONTENT_TYPE,
        # lets the DB links be rebuilt from the bucket alone, whatever happens to the DB
        Metadata={"song-id": str(item.song.song_id), "demo-id": item.song.demo_id, "sha256": digest},
    )
    after = head(s3, bucket, item.key)
    if not after or after["ContentLength"] != len(data) or after.get("Metadata", {}).get("sha256") != digest:
        raise RuntimeError("the object is not in the bucket as uploaded")
    return "uploaded"


def list_objects(s3, bucket: str) -> dict[str, int]:
    found = {}
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=KEY_PREFIX):
        for obj in page.get("Contents", []):
            found[obj["Key"]] = obj["Size"]
    return found


def verify(s3, bucket: str, conn, deep: bool = False) -> list[str]:
    """DB <-> bucket. Empty list = perfect sync."""
    in_bucket = list_objects(s3, bucket)
    referenced = {}
    problems = []
    for song_id, *keys in conn.execute("SELECT song_id, " + ", ".join(k.column for k in KINDS.values()) + " FROM songs"):
        for (kind, spec), key in zip(KINDS.items(), keys):
            if not key:
                continue
            referenced[key] = (song_id, kind)
            if key != object_key(song_id, kind):
                problems.append(f"unexpected key: song {song_id} {spec.column} = {key}")
            if key not in in_bucket:
                problems.append(f"missing in bucket: {key}")
            elif in_bucket[key] == 0:
                problems.append(f"empty object: {key}")
    problems += [f"orphan in bucket: {key}" for key in sorted(set(in_bucket) - set(referenced))]
    if deep:
        def check(key):
            meta = head(s3, bucket, key)
            song_id = referenced[key][0]
            if meta and (meta.get("Metadata", {}).get("song-id") != str(song_id) or meta.get("ContentType") != CONTENT_TYPE):
                return f"wrong metadata: {key}"
        with ThreadPoolExecutor(8) as pool:
            problems += [p for p in pool.map(check, [k for k in referenced if k in in_bucket]) if p]
    return problems


# ------------------------------------------------------------------ CLI
def load_songs(conn) -> list[DbSong]:
    return [DbSong(*row) for row in conn.execute(
        "SELECT s.song_id, s.slug, s.gr_name, s.demo_id, a.gr_name, s.score_key, s.tab_key "
        "FROM songs s JOIN artists a USING(artist_id)")]


def read_manifest(path: str) -> list[dict]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))["songs"]
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"cannot read the manifest {path}: {error} (make it with scripts/pdf_audit/manifest.ps1)")


def cmd_plan(args) -> int:
    conn = sqlite3.connect(f"file:{db_path()}?mode=ro", uri=True)
    folders = read_manifest(args.manifest)
    songs = load_songs(conn)
    matches, items, problems = build_plan(folders, songs)
    print(f"folders {len(folders)}, matched {len(matches)}, songs in DB {len(songs)}")
    print("PDFs to sync:", {kind: sum(i.kind == kind for i in items) for kind in KINDS})
    with_pdf = {i.song.song_id for i in items}
    print(f"matched songs without any PDF: {len([m for m in matches if m[1].song_id not in with_pdf])}")
    for folder, song, how in matches:
        if how != "demo_id + names":
            print(f"  NOTE {_label(folder)} -> {song.slug}: {how}")
    for message in problems:
        print("  PROBLEM", message)
    review = [i for i in items if needs_review(i.folder, i.file)]
    print(f"picked files whose name does not look like '<song> - <artist>' (look at them before apply): {len(review)}")
    for i in review:
        print("  REVIEW", i.kind, "|", _label(i.folder), "|", i.file["name"])
    return 1 if problems else 0


def cmd_apply(args) -> int:
    import storage

    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"{root} is not a directory (is D: mounted? sudo mount -t drvfs D: /mnt/d)")
    if not db_path().exists():
        sys.exit(f"{db_path()} does not exist (DATABASE_PATH?)")
    conn = sqlite3.connect(f"file:{db_path()}?mode=ro", uri=True) if args.dry_run else sqlite3.connect(db_path())
    _, items, problems = build_plan(read_manifest(args.manifest), load_songs(conn))
    for message in problems:
        print("  PROBLEM", message)
    s3, bucket = storage.client(), storage.bucket()

    def run(item):
        try:
            return item, sync_one(s3, bucket, item, root, args.dry_run), None
        except Exception as error:  # noqa: BLE001 - one bad file must not stop the rest; it is reported below
            return item, "failed", f"{type(error).__name__}: {error}"

    with ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(run, items))

    counts = defaultdict(int)
    for item, status, error in results:
        counts[status] += 1
        if error:
            print(f"  FAILED {item.key} ({item.folder['song']}): {error}")
    print(dict(counts))
    if args.dry_run:
        return 1 if counts["failed"] or problems else 0

    # Keys are written only for objects that were verified in the bucket just now (or already matched).
    ok = [i for i, status, _ in results if status in ("uploaded", "unchanged")]
    changes = [i for i in ok if getattr(i.song, KINDS[i.kind].column) != i.key]
    if changes:
        backup = sqlite3.connect(f"{db_path()}.pre-pdfsync-{datetime.now():%Y%m%d-%H%M%S}.bak")
        conn.backup(backup)  # consistent copy; one per run, so an earlier backup is never overwritten
        backup.close()
        with conn:
            for item in changes:
                conn.execute(f"UPDATE songs SET {KINDS[item.kind].column} = ? WHERE song_id = ?", (item.key, item.song.song_id))
    print(f"DB keys written: {len(changes)}")
    return 1 if counts["failed"] or problems else 0


def cmd_verify(args) -> int:
    import storage

    conn = sqlite3.connect(f"file:{db_path()}?mode=ro", uri=True)
    problems = verify(storage.client(), storage.bucket(), conn, args.deep)
    for message in problems:
        print("  PROBLEM", message)
    print("in sync: 0 missing, 0 orphans" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


def cmd_prune(args) -> int:
    import storage

    s3, bucket = storage.client(), storage.bucket()
    conn = sqlite3.connect(f"file:{db_path()}?mode=ro", uri=True)
    keys = {k for row in conn.execute("SELECT " + ", ".join(k.column for k in KINDS.values()) + " FROM songs") for k in row if k}
    in_bucket = set(list_objects(s3, bucket))
    orphans = sorted(in_bucket - keys)
    print(f"bucket {len(in_bucket)} object(s), referenced by this DB {len(keys)}, orphans {len(orphans)}")
    for key in orphans:
        print("  ", key)
    if not orphans:
        return 0
    if not args.yes:
        print("dry run: add --yes to delete them")
        return 0
    # Orphans are computed from the local DB only: a wrong, old or empty DB would make good objects look orphaned.
    if not keys:
        print("REFUSED: this DB references no PDF at all (wrong DATABASE_PATH, or the keys were never written?)")
        return 1
    if len(orphans) > max(10, len(in_bucket) // 10) and not args.force:
        print("REFUSED: that is more than 10% of the bucket; check the DB first, then add --force")
        return 1
    failed = []
    for start in range(0, len(orphans), 1000):
        response = s3.delete_objects(Bucket=bucket, Delete={"Objects": [{"Key": k} for k in orphans[start:start + 1000]]})
        failed += response.get("Errors", [])
    for error in failed:
        print("  NOT DELETED", error.get("Key"), error.get("Message"))
    print(f"deleted {len(orphans) - len(failed)}" + (f", {len(failed)} failed" if failed else ""))
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--manifest", required=True)
    apply = sub.add_parser("apply")
    apply.add_argument("--manifest", required=True)
    apply.add_argument("--root", required=True, help="folder that holds <artist>/<song>/ (e.g. /mnt/d/...)")
    apply.add_argument("--dry-run", action="store_true", help="hash and compare with the bucket, change nothing")
    apply.add_argument("--workers", type=int, default=8, choices=range(1, 33), metavar="1-32")
    check = sub.add_parser("verify")
    check.add_argument("--deep", action="store_true", help="HEAD every object and check its metadata")
    prune = sub.add_parser("prune")
    prune.add_argument("--yes", action="store_true")
    prune.add_argument("--force", action="store_true", help="allow deleting more than 10%% of the bucket")
    args = parser.parse_args(argv)
    return {"plan": cmd_plan, "apply": cmd_apply, "verify": cmd_verify, "prune": cmd_prune}[args.command](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
