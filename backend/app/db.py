import os
import re
import sqlite3
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BACKEND_DIR / "migrations"
DEFAULT_DB_PATH = BACKEND_DIR.parent / "data" / "skillmap.db"

_MIGRATION_NAME = re.compile(r"^(\d{4})_[a-z0-9_]+\.sql$")


def db_path() -> Path:
    env = os.environ.get("SKILLMAP_DB")
    return Path(env) if env else DEFAULT_DB_PATH


def connect(path: str | os.PathLike | None = None) -> sqlite3.Connection:
    target = Path(path) if path is not None else db_path()
    if str(target) != ":memory:":
        target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrations(directory: Path) -> list[tuple[int, Path]]:
    found = []
    for f in directory.iterdir():
        m = _MIGRATION_NAME.match(f.name)
        if m:
            found.append((int(m.group(1)), f))
    found.sort()
    versions = [v for v, _ in found]
    if len(versions) != len(set(versions)):
        raise RuntimeError(f"duplicate migration version in {directory}")
    return found


def migrate(conn: sqlite3.Connection, directory: Path = MIGRATIONS_DIR) -> list[str]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " version INTEGER PRIMARY KEY,"
        " name TEXT NOT NULL,"
        " applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    applied = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
    done = []
    for version, f in _migrations(directory):
        if version in applied:
            continue
        # executescript() auto-commits, so the transaction must live inside the script.
        script = (
            "BEGIN;\n"
            + f.read_text(encoding="utf-8")
            + f"\n;INSERT INTO schema_migrations (version, name) VALUES ({version}, '{f.name}');\n"
            + "COMMIT;\n"
        )
        try:
            conn.executescript(script)
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        done.append(f.name)
    return done


def main(argv: list[str]) -> int:
    if argv != ["migrate"]:
        print("usage: python -m app.db migrate", file=sys.stderr)
        return 2
    path = db_path()
    with connect(path) as conn:
        done = migrate(conn)
    conn.close()
    print(f"{path}: applied {len(done)} migration(s)" + (f": {', '.join(done)}" if done else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
