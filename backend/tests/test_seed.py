import json

import pytest

from app import db
from conftest import SEED_DIR, load_seed_module

seed = load_seed_module("import_reference")

EXPECTED = {
    "cluster": 8,
    "source": 10,
    "job_posting": 23,
    "skill": 50,
    "roadmap": 1,
    "roadmap_step": 32,
    "role_skill": 50,
    "role_company": 10,
}


def counts(path):
    conn = db.connect(path)
    try:
        got = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in EXPECTED}
        got["prereq"] = conn.execute(
            "SELECT COUNT(*) FROM skill_edge WHERE type = 'prereq'").fetchone()[0]
        got["phase"] = conn.execute(
            "SELECT COUNT(DISTINCT phase) FROM roadmap_step").fetchone()[0]
        for t in ("resource", "skill_resource", "posting_skill"):
            got[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        return got
    finally:
        conn.close()


@pytest.fixture
def db_file(tmp_path):
    path = tmp_path / "seed.db"
    seed.import_reference(path, SEED_DIR / "reference.html")
    return path


def test_counts(db_file):
    got = counts(db_file)
    assert {k: got[k] for k in EXPECTED} == EXPECTED
    assert got["prereq"] == 52
    assert got["phase"] == 7
    assert got["resource"] > 0 and got["skill_resource"] >= got["resource"]
    assert got["posting_skill"] == 0


def test_reimport_is_idempotent(db_file):
    before = counts(db_file)
    seed.import_reference(db_file, SEED_DIR / "reference.html")
    assert counts(db_file) == before


def test_field_mapping(db_file):
    conn = db.connect(db_file)
    try:
        s = conn.execute("SELECT * FROM skill WHERE slug = 'os'").fetchone()
        assert s["status"] == "active" and len(json.loads(s["concepts"])) == 4
        rs = conn.execute("SELECT * FROM role_skill WHERE skill_id = ?", (s["id"],)).fetchall()
        assert [(r["role_family"], r["cluster_slug"], r["sort"]) for r in rs] == [("agent-infra", "found", 0)]
        assert json.loads(rs[0]["reference_companies"]) == ["A", "B", "AN"]
        assert [tuple(r) for r in conn.execute(
            "SELECT slug, role_family FROM cluster ORDER BY sort")][:2] == [
            ("found", "agent-infra"), ("core", "agent-infra")]
        assert [r[0] for r in conn.execute(
            "SELECT s.code FROM role_company rc JOIN source s ON s.id = rc.source_id"
            " WHERE rc.role_family = 'agent-infra' ORDER BY rc.sort")][:2] == ["O", "AN"]
        src = conn.execute("SELECT * FROM source WHERE code = 'AN'").fetchone()
        assert (src["name"], src["company"], src["type"], src["url"]) == ("Anthropic", "Anthropic", "manual", None)
        xhs = conn.execute(
            "SELECT url, status, role_family FROM job_posting WHERE title = '【2027校招】AI Agent Infra 工程师'"
        ).fetchone()
        assert tuple(xhs) == ("https://job.xiaohongshu.com/campus/position/22062", "open", "agent-infra")
        rm = conn.execute("SELECT params FROM roadmap").fetchone()
        assert json.loads(rm[0]) == {"origin": "reference"}
        first = conn.execute(
            "SELECT rs.phase, rs.phase_title, rs.step_order, s.slug FROM roadmap_step rs"
            " JOIN skill s ON s.id = rs.skill_id ORDER BY rs.phase, rs.step_order LIMIT 1"
        ).fetchone()
        assert tuple(first) == (1, "Agent 核心", 0, "llm")
    finally:
        conn.close()


def test_overrides_replace_screenshot_jobs(db_file):
    overrides = json.loads((SEED_DIR / "reference_overrides.json").read_text(encoding="utf-8"))["jobs"]
    conn = db.connect(db_file)
    try:
        assert conn.execute("SELECT COUNT(*) FROM job_posting WHERE title LIKE '%截图%'").fetchone()[0] == 0
        rows = {
            (r[0], r[1]): r[2] for r in conn.execute(
                "SELECT s.code, j.title, j.url FROM job_posting j JOIN source s ON s.id = j.source_id")
        }
        for o in overrides:
            assert rows[(o["code"], o["title"])] == o["url"]
    finally:
        conn.close()


def _postings(path):
    conn = db.connect(path)
    try:
        return sorted(tuple(r) for r in conn.execute(
            "SELECT s.code, j.title, j.url, j.role_family FROM job_posting j JOIN source s ON s.id = j.source_id"))
    finally:
        conn.close()


def test_reimport_drops_postings_no_longer_seeded(db_file, tmp_path):
    old = tmp_path / "old.db"
    seed.import_reference(old, SEED_DIR / "reference.html", None)
    conn = db.connect(old)
    try:
        stale = conn.execute("SELECT id FROM job_posting WHERE title LIKE '%截图%'").fetchone()[0]
        conn.execute("INSERT INTO posting_skill VALUES (?, 1, NULL, 'required', NULL, 'v1')", (stale,))
        conn.commit()
    finally:
        conn.close()
    seed.import_reference(old, SEED_DIR / "reference.html")
    assert counts(old) == counts(db_file)
    assert _postings(old) == _postings(db_file)


def test_override_without_match_raises(tmp_path):
    bad = tmp_path / "overrides.json"
    bad.write_text(json.dumps({"jobs": [{
        "code": "O", "original_title": "不存在的岗位（截图）",
        "title": "x", "url": "https://example.com", "fetched": "2026-11-19",
    }]}), encoding="utf-8")
    with pytest.raises(ValueError, match="override not found"):
        seed.import_reference(tmp_path / "seed.db", SEED_DIR / "reference.html", bad)


def test_override_wrong_company_raises():
    sources = [{"k": "A", "jobs": [["Agent 基础设施（截图）", ""]]}]
    with pytest.raises(ValueError, match="override not found"):
        seed.apply_overrides(sources, {"jobs": [{
            "code": "B", "original_title": "Agent 基础设施（截图）", "title": "x", "url": "u"}]})
    assert sources[0]["jobs"][0] == ["Agent 基础设施（截图）", ""]


def _companies(path):
    conn = db.connect(path)
    try:
        return {r[0]: json.loads(r[1]) for r in conn.execute(
            "SELECT s.slug, rs.reference_companies FROM role_skill rs JOIN skill s ON s.id = rs.skill_id"
            " WHERE rs.role_family = 'agent-infra'")}
    finally:
        conn.close()


def test_skill_companies_applied(db_file, tmp_path):
    spec = json.loads((SEED_DIR / "reference_overrides.json").read_text(encoding="utf-8"))["skill_companies"]
    raw = tmp_path / "raw.db"
    seed.import_reference(raw, SEED_DIR / "reference.html", None)
    before, after = _companies(raw), _companies(db_file)
    assert set(before) == set(after)
    for slug in before:
        change = spec.get(slug, {})
        expected = [c for c in before[slug] if c not in change.get("remove", [])] + change.get("add", [])
        assert after[slug] == expected
        assert after[slug]
    assert after["durable"] == ["O", "X", "AN"]
    assert after["cpdp"] == ["X"]
    assert "O" in after["rl"] and "A" in after["cua"]
    assert "O" not in after["rag"] and "A" not in after["dist"]


NODES = [{"id": "a", "jd": "O A"}, {"id": "b", "jd": "A"}]
CODES = {"O": "OpenAI", "A": "阿里", "B": "百度"}


@pytest.mark.parametrize("spec, match", [
    ({"zzz": {"add": ["B"]}}, "unknown skill"),
    ({"a": {"add": ["ZZ"]}}, "unknown company"),
    ({"a": {"remove": ["ZZ"]}}, "unknown company"),
    ({"a": {"remove": ["B"]}}, "not in"),
    ({"a": {"add": ["O"]}}, "already in"),
    ({"a": {"drop": ["O"]}}, "unknown keys"),
])
def test_skill_companies_errors(spec, match):
    nodes = [dict(n) for n in NODES]
    with pytest.raises(ValueError, match=match):
        seed.apply_skill_companies(nodes, CODES, spec)


def test_skill_companies_edit():
    nodes = [dict(n) for n in NODES]
    assert seed.apply_skill_companies(nodes, CODES, {"a": {"remove": ["O"], "add": ["B"]}}) == []
    assert nodes[0]["jd"] == "A B"


def test_skill_companies_never_empty():
    nodes = [dict(n) for n in NODES]
    assert seed.apply_skill_companies(nodes, CODES, {"b": {"remove": ["A"]}, "a": {"remove": ["O"]}}) == ["b"]
    assert nodes[1]["jd"] == "A" and nodes[0]["jd"] == "A"


def test_skill_companies_error_aborts_import(tmp_path):
    bad = tmp_path / "overrides.json"
    bad.write_text(json.dumps({"jobs": [], "skill_companies": {"os": {"remove": ["O"]}}}), encoding="utf-8")
    with pytest.raises(ValueError, match="not in"):
        seed.import_reference(tmp_path / "seed.db", SEED_DIR / "reference.html", bad)


@pytest.mark.parametrize("title, expected", [
    ("Raft 论文", "paper"),
    ("MIT 6.5840 课程", "course"),
    ("Codex CLI 源码（GitHub）", "repo"),
    ("Kubernetes 官方文档", "doc"),
    ("《Rust for Rustaceans》", "doc"),
    ("Saga 模式", "blog"),
])
def test_resource_type(title, expected):
    assert seed.resource_type(title) == expected
