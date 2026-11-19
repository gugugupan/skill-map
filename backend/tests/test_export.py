import json

import pytest

from app import db, export
from conftest import FIXTURE_ROLES, SEED_DIR, load_seed_module

ref = load_seed_module("import_reference")
roles = load_seed_module("import_roles")

ROLE_FILES = ["clusters.json", "companies.json", "sources.json", "skills.json", "edges.json", "roadmap.json"]
GLOBAL_SKILL_KEYS = {"slug", "name", "description", "concepts", "practice", "resources", "prereqs", "unlocks"}


def load(out, name):
    return json.loads((out / name).read_text(encoding="utf-8"))


def run_export(db_file, out):
    conn = db.connect(db_file)
    try:
        return export.export(conn, out)
    finally:
        conn.close()


@pytest.fixture(scope="module")
def ref_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("ref") / "ref.db"
    ref.import_reference(path, SEED_DIR / "reference.html")
    return path


@pytest.fixture(scope="module")
def ref_out(ref_db, tmp_path_factory):
    out = tmp_path_factory.mktemp("ref_out")
    run_export(ref_db, out)
    return out


@pytest.fixture(scope="module")
def multi_db(ref_db, tmp_path_factory):
    path = tmp_path_factory.mktemp("multi") / "multi.db"
    path.write_bytes(ref_db.read_bytes())
    roles.import_roles(path, FIXTURE_ROLES)
    return path


@pytest.fixture(scope="module")
def out(multi_db, tmp_path_factory):
    out = tmp_path_factory.mktemp("out")
    # Stale files from the single-role layout and a role that no longer has data.
    for name in export.LEGACY_FILES:
        (out / name).write_text("[]")
    (out / "roadmaps").mkdir()
    (out / "roadmaps" / "agent-infra.json").write_text("{}")
    (out / "roles" / "data-eng").mkdir(parents=True)
    (out / "roles" / "data-eng" / "skills.json").write_text("[]")
    (out / "keep.txt").write_text("x")
    run_export(multi_db, out)
    return out


def test_reference_only(ref_out):
    assert load(ref_out, "roles.json") == [{
        "slug": "agent-infra", "name": "Agent Infra 工程师", "root_label": "Agent Infra 工程师",
        "counts": {"companies": 10, "postings": 23, "skills": 50, "edges": 52}}]
    role = ref_out / "roles" / "agent-infra"
    assert len(load(role, "skills.json")) == 50
    assert len(load(role, "edges.json")) == 52
    assert sum(len(s["jobs"]) for s in load(role, "sources.json")) == 23
    assert len(load(role, "companies.json")) == 10
    assert len(load(role, "clusters.json")) == 8
    phases = load(role, "roadmap.json")["phases"]
    assert len(phases) == 7
    assert phases[0]["title"] == "Agent 核心" and phases[0]["skills"][0] == "llm"
    assert len(load(ref_out, "skills.json")) == 50


def test_layout(out):
    assert set(load(out, "meta.json")) == {"generated_at"}
    for name in export.LEGACY_FILES:
        assert not (out / name).exists(), name
    assert not (out / "roadmaps").exists()
    assert not (out / "roles" / "data-eng").exists()
    assert (out / "keep.txt").exists()
    assert sorted(p.name for p in (out / "roles").iterdir()) == ["agent-infra", "backend", "frontend"]
    for role in ("agent-infra", "backend", "frontend"):
        assert sorted(p.name for p in (out / "roles" / role).iterdir()) == sorted(ROLE_FILES)
    assert "\\u" not in (out / "skills.json").read_text(encoding="utf-8")


def test_roles_json(out):
    got = load(out, "roles.json")
    assert [r["slug"] for r in got] == ["agent-infra", "backend", "frontend"]
    assert all(set(r) == {"slug", "name", "root_label", "counts"} for r in got)
    assert got[0]["counts"] == {"companies": 10, "postings": 23, "skills": 50, "edges": 52}
    assert got[1] == {"slug": "backend", "name": "后端工程师", "root_label": "后端工程师",
                      "counts": {"companies": 2, "postings": 2, "skills": 3, "edges": 2}}
    # dist -> cache and net -> conc touch frontend skills but have one end outside the role.
    assert got[2]["counts"] == {"companies": 2, "postings": 2, "skills": 4, "edges": 2}


def test_global_skills(out):
    skills = load(out, "skills.json")
    slugs = [s["slug"] for s in skills]
    assert len(slugs) == len(set(slugs)) == 54
    assert all(set(s) == GLOBAL_SKILL_KEYS for s in skills)
    assert slugs[:2] == ["os", "net"]
    assert slugs[50:] == ["sql-db", "cache", "web-basics", "ts"]
    cache = skills[slugs.index("cache")]
    assert cache["prereqs"] == ["sql-db", "dist"] and cache["unlocks"] == []
    net = skills[slugs.index("net")]
    assert "web-basics" in net["unlocks"] and "conc" in net["unlocks"]
    assert all(set(r) == {"title", "url", "type"} for s in skills for r in s["resources"])
    for s in skills:
        assert set(s["prereqs"]) <= set(slugs) and set(s["unlocks"]) <= set(slugs)


def test_role_files(out):
    role = out / "roles" / "frontend"
    assert load(role, "clusters.json") == [
        {"slug": "frontend-web", "name": "Web 基础", "color": "#2A8C82"},
        {"slug": "frontend-eng", "name": "工程化", "color": "#C08A1E"}]
    assert load(role, "companies.json") == [{"code": "MERCARI", "name": "Mercari"},
                                            {"code": "STRIPE", "name": "Stripe"}]
    assert load(role, "sources.json") == [
        {"code": "MERCARI", "name": "Mercari",
         "jobs": [{"title": "Frontend Engineer", "url": "https://example.com/mercari/frontend"}]},
        {"code": "STRIPE", "name": "Stripe",
         "jobs": [{"title": "Software Engineer", "url": "https://example.com/stripe/frontend"}]}]
    assert load(role, "skills.json") == [
        {"slug": "web-basics", "cluster": "frontend-web", "companies": ["MERCARI", "STRIPE"], "heat": 2},
        {"slug": "ts", "cluster": "frontend-eng", "companies": ["MERCARI"], "heat": 1},
        {"slug": "net", "cluster": "frontend-web", "companies": ["STRIPE"], "heat": 1},
        {"slug": "cache", "cluster": "frontend-web", "companies": ["MERCARI", "STRIPE"], "heat": 2}]
    assert load(role, "edges.json") == [{"from": "net", "to": "web-basics", "type": "prereq"},
                                        {"from": "web-basics", "to": "ts", "type": "prereq"}]
    assert load(role, "roadmap.json") == {"phases": [
        {"title": "基础", "skills": ["net", "web-basics"]}, {"title": "工程化", "skills": ["ts", "cache"]}]}


def test_agent_infra_unchanged(ref_out, out):
    for name in ROLE_FILES:
        a = ref_out / "roles" / "agent-infra" / name
        b = out / "roles" / "agent-infra" / name
        assert a.read_bytes() == b.read_bytes(), name
    skills = load(out, "roles/agent-infra/skills.json")
    os_ = skills[0]
    assert os_ == {"slug": "os", "cluster": "found", "companies": ["A", "B", "X", "AN"], "heat": 4}
    clusters = {c["slug"] for c in load(out, "roles/agent-infra/clusters.json")}
    assert all(s["cluster"] in clusters for s in skills)


def test_role_consistency(out):
    global_slugs = {s["slug"] for s in load(out, "skills.json")}
    for r in load(out, "roles.json"):
        role = out / "roles" / r["slug"]
        skills = load(role, "skills.json")
        members = {s["slug"] for s in skills}
        codes = {c["code"] for c in load(role, "companies.json")}
        clusters = {c["slug"] for c in load(role, "clusters.json")}
        assert members <= global_slugs
        for s in skills:
            assert s["cluster"] in clusters and set(s["companies"]) <= codes and s["heat"] == len(s["companies"])
        for e in load(role, "edges.json"):
            assert e["from"] in members and e["to"] in members
        assert all(slug in members for p in load(role, "roadmap.json")["phases"] for slug in p["skills"])


def test_deterministic(multi_db, out, tmp_path):
    written = run_export(multi_db, tmp_path)
    for path in written:
        name = path.relative_to(tmp_path)
        if str(name) == "meta.json":
            continue
        assert path.read_bytes() == (out / name).read_bytes(), name
