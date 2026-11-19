import copy
import json
import re
import sqlite3

import pytest

from app import db
from conftest import FIXTURE_ROLES, SEED_DIR, load_seed_module

ref = load_seed_module("import_reference")
roles = load_seed_module("import_roles")

TABLES = ("skill", "cluster", "source", "job_posting", "skill_edge", "resource",
          "skill_resource", "role_skill", "role_company", "roadmap", "roadmap_step")


def fixtures():
    return {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(FIXTURE_ROLES.glob("*.json"))}


def write_roles(directory, data):
    directory.mkdir(exist_ok=True)
    for name, payload in data.items():
        (directory / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return directory


def snapshot(path):
    conn = db.connect(path)
    try:
        got = {t: sorted(tuple(r) for r in conn.execute(f"SELECT * FROM {t}")) for t in TABLES}
        # roadmap_step rows are replaced on every import, so their ids are not stable.
        got["roadmap_step"] = sorted(r[1:] for r in got["roadmap_step"])
        return got
    finally:
        conn.close()


@pytest.fixture(scope="module")
def reference_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("ref") / "ref.db"
    ref.import_reference(path, SEED_DIR / "reference.html")
    return path


@pytest.fixture
def ref_db(reference_db, tmp_path):
    path = tmp_path / "work.db"
    path.write_bytes(reference_db.read_bytes())
    return path


@pytest.fixture
def imported(ref_db):
    warnings = roles.import_roles(ref_db, FIXTURE_ROLES)
    return ref_db, warnings


def q(path, sql, params=()):
    conn = db.connect(path)
    try:
        return [tuple(r) for r in conn.execute(sql, params)]
    finally:
        conn.close()


def test_import(imported):
    path, warnings = imported
    assert q(path, "SELECT COUNT(*) FROM skill") == [(54,)]
    assert q(path, "SELECT role_family, COUNT(*) FROM role_skill GROUP BY role_family ORDER BY 1") == [
        ("agent-infra", 50), ("backend", 3), ("frontend", 4)]
    assert q(path, "SELECT s.slug, rs.cluster_slug, rs.reference_companies, rs.sort FROM role_skill rs"
                   " JOIN skill s ON s.id = rs.skill_id WHERE rs.role_family = 'frontend' ORDER BY rs.sort") == [
        ("web-basics", "frontend-web", '["MERCARI", "STRIPE"]', 0),
        ("ts", "frontend-eng", '["MERCARI"]', 1),
        ("net", "frontend-web", '["STRIPE"]', 2),
        ("cache", "frontend-web", '["MERCARI", "STRIPE"]', 3)]
    assert q(path, "SELECT slug, role_family, sort FROM cluster WHERE role_family = 'backend' ORDER BY sort") == [
        ("backend-data", "backend", 0), ("backend-dist", "backend", 1)]
    # Shared companies are one source row each; AN keeps its reference name.
    assert q(path, "SELECT code, name FROM source WHERE code IN ('STRIPE', 'MERCARI', 'AN') ORDER BY code") == [
        ("AN", "Anthropic"), ("MERCARI", "Mercari"), ("STRIPE", "Stripe")]
    assert q(path, "SELECT s.code FROM role_company rc JOIN source s ON s.id = rc.source_id"
                   " WHERE rc.role_family = 'frontend' ORDER BY rc.sort") == [("MERCARI",), ("STRIPE",)]
    # Same company + title in two roles stays two postings.
    assert q(path, "SELECT role_family, url FROM job_posting WHERE title = 'Software Engineer' ORDER BY 1") == [
        ("backend", "https://example.com/stripe/backend"), ("frontend", "https://example.com/stripe/frontend")]
    assert q(path, "SELECT COUNT(*) FROM job_posting") == [(27,)]
    assert q(path, "SELECT COUNT(*) FROM skill_edge") == [(56,)]
    assert q(path, "SELECT name_zh, cluster, sort FROM skill WHERE slug = 'cache'") == [("缓存", None, None)]
    phases = q(path, "SELECT rs.phase, rs.phase_title, s.slug FROM roadmap r"
                     " JOIN roadmap_step rs ON rs.roadmap_id = r.id JOIN skill s ON s.id = rs.skill_id"
                     " WHERE r.role_family = 'backend' ORDER BY rs.phase, rs.step_order")
    assert phases == [(1, "基础", "sql-db"), (1, "基础", "dist"), (2, "进阶", "cache")]


def test_resource_first_come(imported):
    path, warnings = imported
    assert warnings == []
    assert q(path, "SELECT url, type FROM resource WHERE title = 'Redis 官方文档'") == [
        ("https://redis.io/docs/", "doc")]
    assert q(path, "SELECT COUNT(*) FROM skill_resource sr JOIN skill s ON s.id = sr.skill_id"
                   " WHERE s.slug = 'cache'") == [(2,)]


def test_resource_missing_url_is_filled(imported):
    path, _ = imported
    title = "Kleppmann《Designing Data-Intensive Applications》"
    # reference.html imports this title without a url; the backend fixture supplies one.
    assert q(path, "SELECT url, type FROM resource WHERE title = ?", (title,)) == [
        ("https://dataintensive.net/", "doc")]


def test_resource_conflicting_url_keeps_first(ref_db, tmp_path):
    data = fixtures()
    title = "Kleppmann《Designing Data-Intensive Applications》"
    _skill(data, "frontend", "web-basics")["resources"] = [{"title": title, "url": "https://example.com/ddia"}]
    warnings = roles.import_roles(ref_db, write_roles(tmp_path / "r", data))
    assert q(ref_db, "SELECT url FROM resource WHERE title = ?", (title,)) == [("https://dataintensive.net/",)]
    assert len(warnings) == 1 and title in warnings[0]


def test_idempotent(imported):
    path, _ = imported
    before = snapshot(path)
    roles.import_roles(path, FIXTURE_ROLES)
    assert snapshot(path) == before
    ref.import_reference(path, SEED_DIR / "reference.html")
    roles.import_roles(path, FIXTURE_ROLES)
    assert snapshot(path) == before


def test_missing_dir_is_skipped(ref_db, tmp_path, capsys):
    before = snapshot(ref_db)
    assert roles.main([str(ref_db), str(tmp_path / "nope")]) == 0
    assert "skipping" in capsys.readouterr().out
    assert snapshot(ref_db) == before


def test_cli_reports_errors(ref_db, tmp_path, capsys):
    data = fixtures()
    data["backend"]["role"]["slug"] = "devops"
    assert roles.main([str(ref_db), str(write_roles(tmp_path / "r", data))]) == 1
    assert "unknown role 'devops'" in capsys.readouterr().err


def _skill(data, role, slug):
    return next(s for s in data[role]["skills"] if s["slug"] == slug)


def _redefine_existing(d):
    d["backend"]["skills"].append({**copy.deepcopy(_skill(d, "backend", "cache")), "slug": "os"})


def _define_twice(d):
    d["frontend"]["skills"][3] = {**copy.deepcopy(_skill(d, "backend", "cache")), "cluster": "frontend-web"}


def _cycle(d):
    d["frontend"]["prereqs"].append(["cache", "sql-db"])


ERRORS = {
    "full definition hits existing skill": (_redefine_existing, "skill 'os' already exists"),
    "two files define same slug": (_define_twice, "skill 'cache' fully defined again"),
    "unknown reused slug": (
        lambda d: d["frontend"]["skills"].append({"slug": "nope", "cluster": "frontend-web", "companies": []}),
        "skill 'nope' does not exist"),
    "unknown prereq slug": (
        lambda d: d["backend"]["prereqs"].append(["nope", "cache"]), "references unknown skill 'nope'"),
    "unknown path slug": (
        lambda d: d["backend"]["path"][0]["skills"].append("ts"), "'ts', which is not a skill of this role"),
    "unknown posting company": (
        lambda d: d["backend"]["postings"].append({"company": "ZZ", "title": "x", "url": "https://x"}),
        "references company 'ZZ'"),
    "unknown cluster": (
        lambda d: _skill(d, "backend", "dist").update(cluster="backend-nope"),
        "uses unknown cluster 'backend-nope'"),
    "skill companies not subset": (
        lambda d: _skill(d, "frontend", "ts").update(companies=["MERCARI", "AN"]),
        "companies ['AN'] not in this role's companies"),
    "edge between agent-infra skills": (
        lambda d: d["backend"]["prereqs"].append(["os", "dist"]), "joins two agent-infra skills"),
    "prereq cycle": (_cycle, "prereq cycle: "),
    "unknown role": (lambda d: d["frontend"]["role"].update(slug="devops"), "unknown role 'devops'"),
    "agent-infra role file": (
        lambda d: d["frontend"]["role"].update(slug="agent-infra"), "imported from reference.html"),
    "cluster without role prefix": (
        lambda d: d["backend"]["clusters"][0].update(slug="data"), "must start with 'backend-'"),
    "company without posting": (
        lambda d: d["backend"]["postings"].pop(), "company 'AN' has no posting"),
    "reuse rewrites content": (
        lambda d: _skill(d, "backend", "dist").update(resources=[]), "reuse may only set"),
}


@pytest.mark.parametrize("case", list(ERRORS))
def test_errors_write_nothing(ref_db, tmp_path, case):
    mutate, message = ERRORS[case]
    data = fixtures()
    mutate(data)
    before = snapshot(ref_db)
    with pytest.raises(roles.SeedError, match=re.escape(message)):
        roles.import_roles(ref_db, write_roles(tmp_path / "r", data))
    assert snapshot(ref_db) == before


def test_cycle_with_existing_edges(ref_db, tmp_path):
    data = fixtures()
    # sandbox already depends on os (reference); closing the loop through a new skill must fail.
    data["backend"]["skills"].append({"slug": "sandbox", "cluster": "backend-dist", "companies": []})
    data["backend"]["prereqs"] += [["sandbox", "cache"], ["cache", "os"]]
    with pytest.raises(roles.SeedError, match="prereq cycle"):
        roles.import_roles(ref_db, write_roles(tmp_path / "r", data))


def test_unique_posting_key_is_per_role(imported):
    path, _ = imported
    conn = db.connect(path)
    try:
        sid = conn.execute("SELECT id FROM source WHERE code = 'STRIPE'").fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO job_posting (source_id, title, role_family)"
                         " VALUES (?, 'Software Engineer', 'backend')", (sid,))
    finally:
        conn.close()



def test_reimport_drops_postings_no_longer_seeded(imported, reference_db, tmp_path):
    fresh, _ = imported
    old = tmp_path / "old.db"
    old.write_bytes(reference_db.read_bytes())
    data = fixtures()
    data["backend"]["postings"].append({"company": "STRIPE", "title": "Old Title", "url": "https://example.com/old"})
    roles.import_roles(old, write_roles(tmp_path / "r", data))
    conn = db.connect(old)
    try:
        stale = conn.execute("SELECT id FROM job_posting WHERE title = 'Old Title'").fetchone()[0]
        conn.execute("INSERT INTO posting_skill VALUES (?, 1, NULL, 'required', NULL, 'v1')", (stale,))
        conn.commit()
    finally:
        conn.close()
    roles.import_roles(old, FIXTURE_ROLES)
    postings = "SELECT source_id, company, title, url, role_family FROM job_posting ORDER BY 1, 3, 5"
    assert q(old, postings) == q(fresh, postings)
    assert q(old, "SELECT COUNT(*) FROM posting_skill") == [(0,)]
