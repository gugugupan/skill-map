import importlib.util
import json
from pathlib import Path

import pytest

from app import db, export

SEED_DIR = Path(__file__).resolve().parents[2] / "seed"

_spec = importlib.util.spec_from_file_location("import_reference", SEED_DIR / "import_reference.py")
seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)

FILES = [
    "meta.json", "clusters.json", "companies.json", "sources.json",
    "skills.json", "edges.json", "roadmaps/agent-infra.json",
]


def load(out, name):
    return json.loads((out / name).read_text(encoding="utf-8"))


def run_export(db_file, out):
    conn = db.connect(db_file)
    try:
        export.export(conn, out)
    finally:
        conn.close()


@pytest.fixture(scope="module")
def db_file(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "seed.db"
    seed.import_reference(path, SEED_DIR / "reference.html")
    return path


@pytest.fixture(scope="module")
def out(db_file, tmp_path_factory):
    out = tmp_path_factory.mktemp("data")
    run_export(db_file, out)
    return out


def test_files_written(out):
    for name in FILES:
        assert (out / name).is_file(), name
    assert "\\u" not in (out / "skills.json").read_text(encoding="utf-8")


def test_meta(out):
    meta = load(out, "meta.json")
    assert set(meta) == {"generated_at", "counts"}
    assert meta["counts"] == {"companies": 10, "postings": 23, "skills": 50, "edges": 52}


def test_clusters_and_companies(out):
    clusters = load(out, "clusters.json")
    assert len(clusters) == 8
    assert all(set(c) == {"slug", "name", "color"} for c in clusters)
    assert [c["slug"] for c in clusters][:2] == ["found", "core"]

    companies = load(out, "companies.json")
    assert len(companies) == 10
    assert all(set(c) == {"code", "name"} for c in companies)
    assert {"code": "AN", "name": "Anthropic"} in companies


def test_sources(out):
    sources = load(out, "sources.json")
    assert [s["code"] for s in sources] == [c["code"] for c in load(out, "companies.json")]
    jobs = [j for s in sources for j in s["jobs"]]
    assert len(jobs) == 23
    assert all(set(j) == {"title", "url"} for j in jobs)
    assert any(j["url"] is None for j in jobs)


def test_skills(out):
    skills = load(out, "skills.json")
    assert len(skills) == 50
    keys = {"slug", "name", "cluster", "description", "concepts", "practice", "resources",
            "companies", "heat", "prereqs", "unlocks"}
    assert all(set(s) == keys for s in skills)
    clusters = {c["slug"] for c in load(out, "clusters.json")}
    codes = {c["code"] for c in load(out, "companies.json")}
    for s in skills:
        assert s["cluster"] in clusters
        assert s["heat"] == len(s["companies"])
        assert set(s["companies"]) <= codes
        assert all(set(r) == {"title", "url", "type"} for r in s["resources"])
    os_ = skills[0]
    assert os_["slug"] == "os" and os_["companies"] == ["A", "B", "X", "AN"] and os_["heat"] == 4


def test_slugs_resolve(out):
    skills = load(out, "skills.json")
    slugs = {s["slug"] for s in skills}
    edges = load(out, "edges.json")
    assert len(edges) == 52
    assert all(set(e) == {"from", "to", "type"} for e in edges)
    for e in edges:
        assert e["from"] in slugs and e["to"] in slugs
    for s in skills:
        assert set(s["prereqs"]) <= slugs and set(s["unlocks"]) <= slugs
    prereq_pairs = {(e["from"], e["to"]) for e in edges if e["type"] == "prereq"}
    assert {(p, s["slug"]) for s in skills for p in s["prereqs"]} == prereq_pairs
    assert {(s["slug"], u) for s in skills for u in s["unlocks"]} == prereq_pairs

    phases = load(out, "roadmaps/agent-infra.json")["phases"]
    assert len(phases) == 7
    assert phases[0]["title"] == "Agent 核心" and phases[0]["skills"][0] == "llm"
    assert all(slug in slugs for p in phases for slug in p["skills"])


def test_deterministic(db_file, out, tmp_path):
    run_export(db_file, tmp_path)
    for name in FILES:
        if name == "meta.json":
            a, b = load(out, name), load(tmp_path, name)
            a.pop("generated_at"), b.pop("generated_at")
            assert a == b
        else:
            assert (out / name).read_bytes() == (tmp_path / name).read_bytes(), name
