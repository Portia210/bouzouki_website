"""Minimal SQLite migration runner.  Usage:

    uv run python db_migrate.py status
    uv run python db_migrate.py up            # apply everything pending
    uv run python db_migrate.py down [N]      # revert the last N (default 1)

The schema version lives in `PRAGMA user_version`. A backup copy of the database is
written next to it before any change. `DATABASE_PATH` overrides the default file.
"""

import importlib
import os
import pkgutil
import shutil
import sqlite3
import sys
from pathlib import Path

import migrations

DEFAULT_DB = Path(__file__).parent / "instance" / "music.db"


def db_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", DEFAULT_DB))


def load_migrations():
    names = sorted(m.name for m in pkgutil.iter_modules(migrations.__path__) if m.name[:4].isdigit())
    return [(int(n[:4]), n, importlib.import_module(f"migrations.{n}")) for n in names]


def version(conn) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _run(conn, step, direction: str, new_version: int):
    # Table rebuilds need foreign keys off, and the pragma is a no-op inside a transaction.
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("BEGIN")
    try:
        getattr(step, direction)(conn)
        problems = conn.execute("PRAGMA foreign_key_check").fetchall()
        if problems:
            raise RuntimeError(f"foreign key violations: {problems[:5]}")
        conn.execute(f"PRAGMA user_version = {int(new_version)}")
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def migrate(path: Path, direction: str = "up", steps: int | None = None) -> int:
    all_steps = load_migrations()
    conn = sqlite3.connect(path, isolation_level=None)
    try:
        current = version(conn)
        if direction == "up":
            todo = [m for m in all_steps if m[0] > current]
        else:
            todo = [m for m in reversed(all_steps) if m[0] <= current][: steps or 1]
        if not todo:
            return current
        shutil.copy2(path, f"{path}.pre-{todo[0][0]:04d}-{direction}.bak")
        for number, name, module in todo:
            target = number if direction == "up" else number - 1
            print(f"{direction} {name}")
            _run(conn, module, direction, target)
        conn.execute("VACUUM")  # table rebuilds leave the old BLOB pages as free space
        return version(conn)
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "status"
    path = db_path()
    if command == "status":
        conn = sqlite3.connect(path)
        print(f"{path}: version {version(conn)} of {load_migrations()[-1][0]}")
    elif command in ("up", "down"):
        steps = int(argv[2]) if len(argv) > 2 else None
        print(f"now at version {migrate(path, command, steps)}")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
