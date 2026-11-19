import sqlite3

import pytest

from app import db

TABLES = {
    "cluster", "source", "job_posting", "skill", "posting_skill", "skill_edge",
    "resource", "skill_resource", "roadmap", "roadmap_step", "progress",
    "role", "role_skill", "role_company",
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
    assert db.migrate(conn) == ["0001_init.sql", "0002_multi_role.sql"]
    assert tables(conn) == TABLES | {"schema_migrations"}
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_migrate_idempotent(conn):
    db.migrate(conn)
    assert db.migrate(conn) == []
    assert [r[0] for r in conn.execute("SELECT version FROM schema_migrations")] == [1, 2]


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
    conn.execute("INSERT INTO job_posting (source_id, title, role_family) VALUES (1, 'Eng', 'backend')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO job_posting (source_id, title, role_family) VALUES (1, 'Eng', 'backend')")
    conn.execute("INSERT INTO job_posting (source_id, title, role_family) VALUES (1, 'Eng', 'frontend')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO job_posting (source_id, title, role_family) VALUES (1, 'X', 'nope')")
    conn.execute("INSERT INTO skill (id, slug, name_zh) VALUES (1, 'a', 'A'), (2, 'b', 'B')")
    conn.execute("INSERT INTO skill_edge VALUES (1, 2, 'prereq')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO skill_edge VALUES (1, 2, 'prereq')")
    conn.execute("INSERT INTO job_posting (source_id, title, role_family) VALUES (1, 'New', 'ai-app')")


def test_roles_seeded(conn):
    db.migrate(conn)
    rows = conn.execute("SELECT slug, name_zh, root_label FROM role ORDER BY sort").fetchall()
    assert [r[0] for r in rows] == ["agent-infra", "ai-app", "backend", "sre-platform", "frontend", "data-eng"]
    assert tuple(rows[3]) == ("sre-platform", "SRE / 平台工程师", "SRE / 平台工程师")


def test_rebuild_keeps_posting_data(tmp_path):
    c = db.connect(tmp_path / "old.db")
    try:
        db.migrate(c, _only(tmp_path, "0001_init.sql"))
        c.execute("INSERT INTO source (id, code, name, type) VALUES (1, 'O', 'OpenAI', 'manual')")
        c.execute("INSERT INTO job_posting (id, source_id, title, role_family) VALUES (7, 1, 'Eng', 'agent-infra')")
        c.execute("INSERT INTO skill (id, slug, name_zh) VALUES (1, 'a', 'A')")
        c.execute("INSERT INTO posting_skill VALUES (7, 1, NULL, 'required', NULL, 'v1')")
        c.commit()
        assert db.migrate(c) == ["0002_multi_role.sql"]
        assert c.execute("SELECT COUNT(*) FROM posting_skill").fetchone()[0] == 1
        assert [tuple(r) for r in c.execute("SELECT id, title FROM job_posting")] == [(7, "Eng")]
        assert c.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        c.close()


def test_migration_fk_violation_rolls_back(conn, tmp_path):
    mdir = tmp_path / "fkmig"
    mdir.mkdir()
    (mdir / "0001_ok.sql").write_text("CREATE TABLE p (id INTEGER PRIMARY KEY);"
                                      " CREATE TABLE c (p_id INTEGER REFERENCES p(id));")
    (mdir / "0002_bad.sql").write_text("CREATE TABLE d (x INTEGER); INSERT INTO c VALUES (5);")
    with pytest.raises(sqlite3.IntegrityError):
        db.migrate(conn, mdir)
    assert "d" not in tables(conn)
    assert conn.execute("SELECT COUNT(*) FROM c").fetchone()[0] == 0
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def _only(tmp_path, name):
    d = tmp_path / "only"
    d.mkdir()
    (d / name).write_text((db.MIGRATIONS_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")
    return d


def test_cli_uses_env_path(tmp_path, monkeypatch, capsys):
    target = tmp_path / "sub" / "cli.db"
    monkeypatch.setenv("SKILLMAP_DB", str(target))
    assert db.main(["migrate"]) == 0
    assert db.main(["migrate"]) == 0
    with db.connect(target) as c:
        assert TABLES <= tables(c)
    assert "applied 0 migration(s)" in capsys.readouterr().out
