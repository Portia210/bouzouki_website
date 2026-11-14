"""Match the Patreon PDF folders to the site's songs (read-only).

    powershell.exe ... manifest.ps1 > manifest.json
    uv run python scripts/pdf_audit/audit.py manifest.json

Primary key = the YouTube id inside each folder's "<song> video link.txt" (== songs.demo_id).
Cross-check = phonetic key of the Greek folder names vs songs.gr_name / artists.gr_name.
"""

import collections
import json
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from textkeys import phonetic_key  # noqa: E402

TAB_WORD = "ΤΑΜΠΛΑΤΟΥΡΑ"  # tablature PDFs are named "<song> - <artist> ΤΑΜΠΛΑΤΟΥΡΑ.pdf"


def demo_id(link):
    text = link.get("value") if isinstance(link, dict) else link
    match = re.search(r"v=([\w-]{11})", text or "")
    return match.group(1) if match else None


def main(manifest_path: str) -> None:
    songs = json.loads(Path(manifest_path).read_text(encoding="utf-8-sig"))["songs"]
    db = sqlite3.connect(Path(__file__).resolve().parents[2] / "instance" / "music.db")
    rows = db.execute(
        "SELECT s.song_id, s.slug, s.en_name, s.gr_name, s.demo_id, a.slug, a.gr_name "
        "FROM songs s JOIN artists a USING(artist_id)"
    ).fetchall()
    by_demo = collections.defaultdict(list)
    for r in rows:
        by_demo[r[4]].append(r)

    folders_by_demo = collections.defaultdict(list)
    no_link, agree, disagree = [], 0, 0
    for f in songs:
        d = demo_id(f["link"])
        if not d:
            no_link.append(f"{f['artist']} / {f['song']}")
            continue
        folders_by_demo[d].append(f)
        cand = by_demo.get(d, [])
        if len(cand) == 1:
            same = phonetic_key(f["song"]) == phonetic_key(cand[0][3]) and phonetic_key(f["artist"]) == phonetic_key(cand[0][6])
            agree, disagree = agree + same, disagree + (not same)

    shapes = collections.Counter()
    extras = collections.Counter()
    for f in songs:
        pdfs = [x["name"] for x in f["files"] if x["name"].lower().endswith(".pdf")]
        tab = [n for n in pdfs if TAB_WORD in unicodedata.normalize("NFC", n).upper()]
        shapes[(len(pdfs) - len(tab), len(tab))] += 1
        for x in f["files"]:
            ext = os.path.splitext(x["name"])[1].lower()
            if ext != ".pdf" and not x["name"].endswith("video link.txt"):
                extras[ext] += 1

    print(f"folders: {len(songs)} | DB songs: {len(rows)}")
    print(f"matched by demo_id: {sum(1 for d in folders_by_demo if d in by_demo)} | folders without link txt: {no_link}")
    print(f"DB songs without a folder: {[r[1] for r in rows if r[4] not in folders_by_demo]}")
    print(f"demo_ids shared by several DB songs: {[[x[1] for x in v] for v in by_demo.values() if len(v) > 1]}")
    print(f"phonetic-name cross-check: {agree} agree, {disagree} differ")
    print(f"(score pdfs, tab pdfs) per folder: {dict(shapes.most_common())}")
    print(f"other file types: {dict(extras)}")


if __name__ == "__main__":
    main(sys.argv[1])
