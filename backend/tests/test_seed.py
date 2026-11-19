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
        assert json.loads(rs[0]["reference_companies"]) == ["A", "B", "X", "AN"]
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
