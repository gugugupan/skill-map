import importlib.util
import json
from pathlib import Path

import pytest

from app import db

SEED_DIR = Path(__file__).resolve().parents[2] / "seed"

_spec = importlib.util.spec_from_file_location("import_reference", SEED_DIR / "import_reference.py")
seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)

EXPECTED = {
    "cluster": 8,
    "source": 10,
    "job_posting": 23,
    "skill": 50,
    "roadmap": 1,
    "roadmap_step": 32,
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
        assert s["cluster"] == "found" and s["status"] == "active" and s["sort"] == 0
        assert json.loads(s["reference_companies"]) == ["A", "B", "X", "AN"]
        assert len(json.loads(s["concepts"])) == 4
        assert [r[0] for r in conn.execute("SELECT slug FROM cluster ORDER BY sort")][:2] == ["found", "core"]
        src = conn.execute("SELECT * FROM source WHERE code = 'AN'").fetchone()
        assert (src["name"], src["company"], src["type"], src["url"]) == ("Anthropic", "Anthropic", "manual", None)
        screenshot = conn.execute(
            "SELECT url, status, role_family FROM job_posting WHERE title = '大模型基建部 AgentSphere（截图）'"
        ).fetchone()
        assert tuple(screenshot) == (None, "open", "agent-infra")
        rm = conn.execute("SELECT params FROM roadmap").fetchone()
        assert json.loads(rm[0]) == {"origin": "reference"}
        first = conn.execute(
            "SELECT rs.phase, rs.phase_title, rs.step_order, s.slug FROM roadmap_step rs"
            " JOIN skill s ON s.id = rs.skill_id ORDER BY rs.phase, rs.step_order LIMIT 1"
        ).fetchone()
        assert tuple(first) == (1, "Agent 核心", 0, "llm")
    finally:
        conn.close()


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
