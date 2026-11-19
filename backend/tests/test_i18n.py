import copy
import json
from pathlib import Path

import pytest

from app import db, export
from conftest import SEED_DIR, load_seed_module
from test_export import FIXTURE_I18N, ROLE_FILES, load, multi_db, out, ref_db, rel_files, run_export  # noqa: F401

ref = load_seed_module("import_reference")
roles = load_seed_module("import_roles")

REAL_I18N = SEED_DIR / "i18n" / "en.json"


@pytest.fixture(scope="module")
def zh_files(multi_db):
    conn = db.connect(multi_db)
    try:
        return export.build(conn)
    finally:
        conn.close()


@pytest.fixture
def tr():
    return json.loads(FIXTURE_I18N.read_text(encoding="utf-8"))


def problems(zh_files, tr):
    with pytest.raises(export.TranslationError) as e:
        export.translate(zh_files, tr)
    return e.value.problems


# --- output -------------------------------------------------------------------------------------

def test_zh_unchanged_by_i18n(multi_db, out, tmp_path):
    run_export(multi_db, tmp_path)
    assert not (tmp_path / "en").exists()
    for name in rel_files(tmp_path):
        if name != "meta.json":
            assert (tmp_path / name).read_bytes() == (out / name).read_bytes(), name


def test_en_meta(out):
    assert load(out, "en/meta.json") == load(out, "meta.json")


def test_en_roles(out):
    zh, en = load(out, "roles.json"), load(out, "en/roles.json")
    assert en[1] == {"slug": "backend", "name": "Backend Engineer", "root_label": "Backend Engineer",
                     "counts": zh[1]["counts"]}
    assert [r["slug"] for r in en] == [r["slug"] for r in zh]


def test_en_skills(out):
    zh, en = load(out, "skills.json"), load(out, "en/skills.json")
    assert [s["slug"] for s in en] == [s["slug"] for s in zh]
    cache = next(s for s in en if s["slug"] == "cache")
    assert cache["name"] == "Caching"
    assert cache["concepts"] == ["Redis", "Cache penetration", "Eviction policies", "Consistency"]
    assert cache["practice"] == "Put a read cache in front of an endpoint."
    assert cache["resources"] == [
        {"title": "Redis official documentation", "url": "https://redis.io/docs/", "type": "doc"},
        {"title": "Kleppmann Designing Data-Intensive Applications", "url": "https://dataintensive.net/",
         "type": "doc"}]
    web = next(s for s in en if s["slug"] == "web-basics")
    # Titles already in English stay as they are.
    assert web["resources"][0]["title"] == "MDN Web Docs"
    for a, b in zip(zh, en):
        assert (a["prereqs"], a["unlocks"]) == (b["prereqs"], b["unlocks"])
        assert [(r["url"], r["type"]) for r in a["resources"]] == [(r["url"], r["type"]) for r in b["resources"]]


def test_en_role_files(out):
    role = out / "en" / "roles" / "agent-infra"
    assert [c["name"] for c in load(role, "clusters.json")][:2] == ["Engineering Foundations", "Agent Core"]
    assert {"code": "A", "name": "Alibaba"} in load(role, "companies.json")
    zh_sources = load(out, "roles/agent-infra/sources.json")
    en_sources = load(role, "sources.json")
    assert [s["name"] for s in en_sources] == [c["name"] for c in load(role, "companies.json")]
    # Job titles are real posting titles and are never translated.
    assert [s["jobs"] for s in en_sources] == [s["jobs"] for s in zh_sources]
    assert load(out, "en/roles/frontend/roadmap.json") == {"phases": [
        {"title": "Foundations", "skills": ["net", "web-basics"]},
        {"title": "Engineering Tooling", "skills": ["ts", "cache"]}]}
    for r in ("agent-infra", "backend", "frontend"):
        for name in ("skills.json", "edges.json"):
            assert (out / "roles" / r / name).read_bytes() == (out / "en" / "roles" / r / name).read_bytes()


def test_without_i18n_removes_stale_en(multi_db, tmp_path):
    (tmp_path / "en" / "roles" / "x").mkdir(parents=True)
    (tmp_path / "en" / "skills.json").write_text("[]")
    run_export(multi_db, tmp_path)
    assert not (tmp_path / "en").exists()


# --- validation -----------------------------------------------------------------------------------

def test_failure_writes_nothing(multi_db, tr, tmp_path):
    del tr["roles"]["backend"]
    bad = tmp_path / "en.json"
    bad.write_text(json.dumps(tr, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "out"
    (out / "roles" / "old").mkdir(parents=True)
    with pytest.raises(export.TranslationError, match=r"roles: missing 'backend'"):
        run_export(multi_db, out, bad)
    assert rel_files(out) == [] and (out / "roles" / "old").exists()


def test_missing_file(multi_db, tmp_path):
    with pytest.raises(export.TranslationError, match="file not found"):
        run_export(multi_db, tmp_path, tmp_path / "nope.json")
    assert list(tmp_path.iterdir()) == []


def test_invalid_json(multi_db, tmp_path):
    bad = tmp_path / "en.json"
    bad.write_text("{", encoding="utf-8")
    with pytest.raises(export.TranslationError, match="not valid JSON"):
        run_export(multi_db, tmp_path / "out", bad)


def test_cli_reports_problems(multi_db, tr, tmp_path, capsys):
    del tr["companies"]["MERCARI"]
    bad = tmp_path / "en.json"
    bad.write_text(json.dumps(tr), encoding="utf-8")
    assert export.main(["--db", str(multi_db), "--out", str(tmp_path / "out"), "--i18n", str(bad)]) == 1
    assert "companies: missing 'MERCARI'" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_all_problems_listed(zh_files, tr):
    del tr["roles"]["backend"]
    tr["clusters"]["nope"] = "Nope"
    tr["skills"]["os"]["name"] = "x" * 29
    got = problems(zh_files, tr)
    assert got == ["roles: missing 'backend'", "clusters: unknown key 'nope'",
                   "skills.os.name: 29 characters, at most 28"]


def test_top_level_keys(zh_files, tr):
    del tr["phases"]
    tr["extra"] = {}
    got = problems(zh_files, tr)
    assert "top level: missing 'phases'" in got and "top level: unknown key 'extra'" in got


@pytest.mark.parametrize("section,key", [
    ("roles", "frontend"), ("clusters", "frontend-eng"), ("companies", "STRIPE"), ("skills", "ts")])
def test_missing_key(zh_files, tr, section, key):
    del tr[section][key]
    assert problems(zh_files, tr) == [f"{section}: missing {key!r}"]


@pytest.mark.parametrize("section,value", [
    ("roles", {"name": "X", "root_label": "X"}), ("clusters", "X"), ("companies", "X"),
    ("skills", {"name": "X", "description": "X.", "concepts": [], "practice": "X."})])
def test_unknown_key(zh_files, tr, section, value):
    # data-eng has no data in the fixture DB, so it is not an exported role.
    tr[section]["data-eng"] = value
    assert problems(zh_files, tr) == [f"{section}: unknown key 'data-eng'"]


def test_entry_fields(zh_files, tr):
    del tr["roles"]["backend"]["root_label"]
    del tr["skills"]["ts"]["practice"]
    tr["skills"]["ts"]["slug"] = "ts"
    tr["skills"]["cache"]["description"] = ""
    tr["companies"]["A"] = None
    assert sorted(problems(zh_files, tr)) == sorted([
        "roles.backend: missing 'root_label'", "skills.ts: missing 'practice'",
        "skills.ts: unknown key 'slug'", "skills.cache.description: must be a non-empty string",
        "companies.A: must be a non-empty string"])


def test_concepts_length(zh_files, tr):
    tr["skills"]["cache"]["concepts"].pop()
    assert problems(zh_files, tr) == ["skills.cache.concepts: has 3 item(s), expected 4"]


def test_concepts_unique(zh_files, tr):
    tr["skills"]["cache"]["concepts"][1] = "Redis"
    assert problems(zh_files, tr) == ["skills.cache.concepts: duplicate concept(s) ['Redis']"]


def test_phases_length(zh_files, tr):
    tr["phases"]["backend"].append("Extra")
    del tr["phases"]["frontend"]
    assert problems(zh_files, tr) == ["phases: missing 'frontend'",
                                      "phases.backend: has 3 item(s), expected 2"]


def test_phases_unique(zh_files, tr):
    tr["phases"]["frontend"] = ["Foundations", "Foundations"]
    assert problems(zh_files, tr) == ["phases.frontend: duplicate phase title(s) ['Foundations']"]


def test_resources_must_be_cjk_titles(zh_files, tr):
    del tr["resources"]["Redis 官方文档"]
    tr["resources"]["MDN Web Docs"] = "MDN"
    assert problems(zh_files, tr) == ["resources: missing 'Redis 官方文档'",
                                      "resources: unknown key 'MDN Web Docs'"]


def test_cjk_punctuation_counts():
    assert export.CJK.search("Liz Rice《Container Security》")
    assert export.CJK.search("みらい翻訳")
    assert not export.CJK.search("Karpathy’s “Let's build GPT” — 2023")


def test_resource_titles_unique(zh_files, tr):
    tr["resources"]["Redis 官方文档"] = "PostgreSQL official documentation"
    assert problems(zh_files, tr) == [
        "resources: 'Redis 官方文档' and 'PostgreSQL 官方文档' both become 'PostgreSQL official documentation'"]


def test_resource_title_collides_with_english_title(zh_files, tr):
    tr["resources"]["TypeScript 官方文档"] = "MDN Web Docs"
    got = problems(zh_files, tr)
    assert len(got) == 1 and "both become 'MDN Web Docs'" in got[0]


def test_skill_name_length(zh_files, tr):
    tr["skills"]["ts"]["name"] = "x" * 28
    export.translate(zh_files, tr)
    tr["skills"]["ts"]["name"] = "x" * 29
    assert problems(zh_files, tr) == ["skills.ts.name: 29 characters, at most 28"]


# --- real seeds ---------------------------------------------------------------------------------

def test_real_seeds(tmp_path):
    if not REAL_I18N.exists():
        pytest.fail("seed/i18n/en.json is missing: the English translation of the real seeds has not landed yet")
    path = tmp_path / "real.db"
    ref.import_reference(path, SEED_DIR / "reference.html")
    roles.import_roles(path, SEED_DIR / "roles")
    out = tmp_path / "out"
    run_export(path, out, REAL_I18N)
    assert rel_files(out / "en") == [f for f in rel_files(out) if not f.startswith("en/")]
    for r in load(out, "en/roles.json"):
        assert sorted(p.name for p in (out / "en" / "roles" / r["slug"]).iterdir()) == sorted(ROLE_FILES)
