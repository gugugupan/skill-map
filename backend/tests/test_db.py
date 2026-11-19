import sqlite3

import pytest

from app import db

TABLES = {
    "cluster", "source", "job_posting", "skill", "posting_skill", "skill_edge",
    "resource", "skill_resource", "roadmap", "roadmap_step", "progress",
}


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    yield c
    c.close()


def tables(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    return {r[0] for r in rows}


def test_migrate_empty_db(conn):
    assert db.migrate(conn) == ["0001_init.sql"]
    assert tables(conn) == TABLES | {"schema_migrations"}
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_migrate_idempotent(conn):
    db.migrate(conn)
    assert db.migrate(conn) == []
    assert [r[0] for r in conn.execute("SELECT version FROM schema_migrations")] == [1]


def test_failed_migration_rolls_back(conn, tmp_path):
    mdir = tmp_path / "migrations"
    mdir.mkdir()
    (mdir / "0001_ok.sql").write_text("CREATE TABLE a (x INTEGER);")
    (mdir / "0002_bad.sql").write_text("CREATE TABLE b (x INTEGER); SELECT * FROM nope;")
    with pytest.raises(sqlite3.OperationalError):
        db.migrate(conn, mdir)
    assert "a" in tables(conn) and "b" not in tables(conn)
    assert [r[0] for r in conn.execute("SELECT version FROM schema_migrations")] == [1]


def test_foreign_keys_enforced(conn):
    db.migrate(conn)
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO job_posting (source_id, title) VALUES (999, 'x')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO skill (slug, name_zh, merged_into) VALUES ('a', 'A', 999)")


def test_constraints(conn):
    db.migrate(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO source (name, type) VALUES ('s', 'rss')")
    conn.execute("INSERT INTO source (id, code, name, type) VALUES (1, 'O', 'OpenAI', 'manual')")
    conn.execute("INSERT INTO job_posting (source_id, title) VALUES (1, 'Eng')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO job_posting (source_id, title) VALUES (1, 'Eng')")
    conn.execute("INSERT INTO skill (id, slug, name_zh) VALUES (1, 'a', 'A'), (2, 'b', 'B')")
    conn.execute("INSERT INTO skill_edge VALUES (1, 2, 'prereq')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO skill_edge VALUES (1, 2, 'prereq')")
    conn.execute("INSERT INTO job_posting (source_id, title, role_family) VALUES (1, 'New', 'ai-app')")


def test_cli_uses_env_path(tmp_path, monkeypatch, capsys):
    target = tmp_path / "sub" / "cli.db"
    monkeypatch.setenv("SKILLMAP_DB", str(target))
    assert db.main(["migrate"]) == 0
    assert db.main(["migrate"]) == 0
    with db.connect(target) as c:
        assert TABLES <= tables(c)
    assert "applied 0 migration(s)" in capsys.readouterr().out
