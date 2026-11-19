"""Export the SQLite database to the static JSON files the frontend reads.

Usage: cd backend && uv run python -m app.export [--out DIR] [--db PATH] [--i18n FILE]

The zh files are written to DIR; an English mirror with the same layout goes to DIR/en,
with names and text taken from the translation file (seed/i18n/en.json by default).
"""

import argparse
import copy
import json
import re
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from app import db

DEFAULT_OUT = db.BACKEND_DIR.parent / "frontend" / "public" / "data"
DEFAULT_I18N = db.BACKEND_DIR.parent / "seed" / "i18n" / "en.json"
EN_DIR = "en"
# The graph label is laid out for this many characters.
MAX_SKILL_NAME = 28
# Han, kana, CJK punctuation (《》、。) and full-width forms.
CJK = re.compile(r"[\u3000-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")


LEGACY_FILES = ("clusters.json", "companies.json", "sources.json", "edges.json")
LEGACY_DIRS = ("roles", "roadmaps")


def _roles(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT r.slug, r.name_zh, r.root_label FROM role r"
        " WHERE EXISTS (SELECT 1 FROM role_skill rs JOIN skill s ON s.id = rs.skill_id"
        "               WHERE rs.role_family = r.slug AND s.status = 'active')"
        " ORDER BY r.sort"
    ).fetchall()


def _edges(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT f.slug AS frm, t.slug AS dst, e.type FROM skill_edge e"
        " JOIN skill f ON f.id = e.from_skill AND f.status = 'active'"
        " JOIN skill t ON t.id = e.to_skill AND t.status = 'active'"
        " ORDER BY e.rowid"
    )
    return [{"from": r["frm"], "to": r["dst"], "type": r["type"]} for r in rows]


def _skills(conn: sqlite3.Connection, edges: list[dict]) -> list[dict]:
    resources: dict[int, list[dict]] = {}
    for r in conn.execute(
        "SELECT sr.skill_id, r.title, r.url, r.type FROM skill_resource sr"
        " JOIN resource r ON r.id = sr.resource_id ORDER BY sr.skill_id, sr.rank, r.id"
    ):
        resources.setdefault(r["skill_id"], []).append(
            {"title": r["title"], "url": r["url"], "type": r["type"]})

    prereqs: dict[str, list[str]] = {}
    unlocks: dict[str, list[str]] = {}
    for e in edges:
        if e["type"] == "prereq":
            prereqs.setdefault(e["to"], []).append(e["from"])
            unlocks.setdefault(e["from"], []).append(e["to"])

    # Global order: first appearance in the role switcher order, then anything role-less.
    rows = conn.execute(
        "SELECT s.* FROM skill s"
        " LEFT JOIN (SELECT rs.skill_id, MIN(r.sort * 100000 + rs.sort) AS pos FROM role_skill rs"
        "            JOIN role r ON r.slug = rs.role_family GROUP BY rs.skill_id) p ON p.skill_id = s.id"
        " WHERE s.status = 'active' ORDER BY p.pos IS NULL, p.pos, s.id"
    )
    return [{
        "slug": r["slug"],
        "name": r["name_zh"],
        "description": r["description"],
        "concepts": json.loads(r["concepts"]),
        "practice": r["practice"],
        "resources": resources.get(r["id"], []),
        "prereqs": prereqs.get(r["slug"], []),
        "unlocks": unlocks.get(r["slug"], []),
    } for r in rows]


def _role_files(conn: sqlite3.Connection, role: str, edges: list[dict]) -> dict[str, object]:
    clusters = [{"slug": r["slug"], "name": r["name_zh"], "color": r["color"]} for r in conn.execute(
        "SELECT slug, name_zh, color FROM cluster WHERE role_family = ? ORDER BY sort, slug", (role,))]

    companies = conn.execute(
        "SELECT s.id, s.code, s.name FROM role_company rc JOIN source s ON s.id = rc.source_id"
        " WHERE rc.role_family = ? ORDER BY rc.sort", (role,)).fetchall()
    jobs: dict[int, list[dict]] = {}
    for r in conn.execute(
        "SELECT source_id, title, url FROM job_posting WHERE role_family = ? ORDER BY id", (role,)
    ):
        jobs.setdefault(r["source_id"], []).append({"title": r["title"], "url": r["url"]})

    skills = []
    for r in conn.execute(
        "SELECT s.slug, rs.cluster_slug, rs.reference_companies FROM role_skill rs"
        " JOIN skill s ON s.id = rs.skill_id AND s.status = 'active'"
        " WHERE rs.role_family = ? ORDER BY rs.sort, s.id", (role,)
    ):
        # No extracted postings yet, so heat comes from the hand-curated companies.
        cos = json.loads(r["reference_companies"])
        skills.append({"slug": r["slug"], "cluster": r["cluster_slug"], "companies": cos, "heat": len(cos)})
    members = {s["slug"] for s in skills}

    latest = conn.execute("SELECT MAX(id) FROM roadmap WHERE role_family = ?", (role,)).fetchone()[0]
    phases: list[dict] = []
    current = None
    for r in conn.execute(
        "SELECT rs.phase, rs.phase_title, s.slug FROM roadmap_step rs"
        " JOIN skill s ON s.id = rs.skill_id"
        " WHERE rs.roadmap_id = ? ORDER BY rs.phase, rs.step_order",
        (latest,),
    ):
        if r["phase"] != current:
            current = r["phase"]
            phases.append({"title": r["phase_title"], "skills": []})
        phases[-1]["skills"].append(r["slug"])

    return {
        "clusters.json": clusters,
        "companies.json": [{"code": c["code"], "name": c["name"]} for c in companies],
        "sources.json": [{"code": c["code"], "name": c["name"], "jobs": jobs.get(c["id"], [])}
                         for c in companies],
        "skills.json": skills,
        "edges.json": [e for e in edges if e["from"] in members and e["to"] in members],
        "roadmap.json": {"phases": phases},
    }


class TranslationError(ValueError):
    def __init__(self, source: object, problems: list[str]):
        self.problems = problems
        super().__init__(f"{source}: {len(problems)} translation problem(s):\n"
                         + "\n".join(f"  - {p}" for p in problems))


def _role_slugs(files: dict[str, object]) -> list[str]:
    return [r["slug"] for r in files["roles.json"]]


def _check_keys(problems: list[str], section: str, got: object, expected: list[str]) -> bool:
    if not isinstance(got, dict):
        problems.append(f"{section}: must be an object")
        return False
    for key in expected:
        if key not in got:
            problems.append(f"{section}: missing {key!r}")
    for key in got:
        if key not in expected:
            problems.append(f"{section}: unknown key {key!r}")
    return True


def _is_text(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _check_text(problems: list[str], where: str, value: object) -> None:
    if not _is_text(value):
        problems.append(f"{where}: must be a non-empty string")
    elif CJK.search(value):
        problems.append(f"{where}: contains CJK characters: {value!r}")


def _check_list(problems: list[str], where: str, value: object, length: int, item: str) -> None:
    if not isinstance(value, list) or not all(_is_text(v) for v in value):
        problems.append(f"{where}: must be a list of non-empty strings")
    elif len(value) != length:
        problems.append(f"{where}: has {len(value)} item(s), expected {length}")
    elif any(CJK.search(v) for v in value):
        problems.append(f"{where}: contains CJK characters: {[v for v in value if CJK.search(v)]}")
    elif len(set(value)) != len(value):
        dupes = sorted({v for v in value if value.count(v) > 1})
        problems.append(f"{where}: duplicate {item}(s) {dupes}")


def _validate(files: dict[str, object], tr: object) -> list[str]:
    problems: list[str] = []
    sections = ("roles", "clusters", "companies", "phases", "resources", "skills")
    if not _check_keys(problems, "top level", tr, list(sections)):
        return problems
    roles = _role_slugs(files)
    clusters: list[str] = []
    companies: list[str] = []
    for role in roles:
        for c in files[f"roles/{role}/clusters.json"]:
            if c["slug"] not in clusters:
                clusters.append(c["slug"])
        for c in files[f"roles/{role}/companies.json"]:
            if c["code"] not in companies:
                companies.append(c["code"])
    skills = files["skills.json"]
    titles = list(dict.fromkeys(r["title"] for s in skills for r in s["resources"]))
    cjk_titles = [t for t in titles if CJK.search(t)]

    if _check_keys(problems, "roles", tr.get("roles"), roles):
        for slug, entry in tr["roles"].items():
            if not isinstance(entry, dict):
                problems.append(f"roles.{slug}: must be an object")
                continue
            _check_keys(problems, f"roles.{slug}", entry, ["name", "root_label"])
            for field in ("name", "root_label"):
                if field in entry:
                    _check_text(problems, f"roles.{slug}.{field}", entry[field])
    for section, expected in (("clusters", clusters), ("companies", companies)):
        if _check_keys(problems, section, tr.get(section), expected):
            for key, value in tr[section].items():
                _check_text(problems, f"{section}.{key}", value)
    if _check_keys(problems, "phases", tr.get("phases"), roles):
        for role, value in tr["phases"].items():
            if role in roles:
                count = len(files[f"roles/{role}/roadmap.json"]["phases"])
                _check_list(problems, f"phases.{role}", value, count, "phase title")
    if _check_keys(problems, "resources", tr.get("resources"), cjk_titles):
        before = len(problems)
        for key, value in tr["resources"].items():
            _check_text(problems, f"resources.{key}", value)
        if len(problems) == before:
            seen: dict[str, str] = {}
            for title in titles:
                en = tr["resources"].get(title, title)
                if en in seen:
                    problems.append(f"resources: {title!r} and {seen[en]!r} both become {en!r}")
                else:
                    seen[en] = title
    by_slug = {s["slug"]: s for s in skills}
    if _check_keys(problems, "skills", tr.get("skills"), list(by_slug)):
        for slug, entry in tr["skills"].items():
            where = f"skills.{slug}"
            if not isinstance(entry, dict):
                problems.append(f"{where}: must be an object")
                continue
            _check_keys(problems, where, entry, ["name", "description", "concepts", "practice"])
            for field in ("name", "description", "practice"):
                if field in entry:
                    _check_text(problems, f"{where}.{field}", entry[field])
            name = entry.get("name")
            if isinstance(name, str) and len(name) > MAX_SKILL_NAME:
                problems.append(f"{where}.name: {len(name)} characters, at most {MAX_SKILL_NAME}")
            if slug in by_slug and "concepts" in entry:
                _check_list(problems, f"{where}.concepts", entry["concepts"],
                            len(by_slug[slug]["concepts"]), "concept")
    return problems


def translate(files: dict[str, object], tr: object, source: object = "translations") -> dict[str, object]:
    """Return the English mirror of the zh files built by build(), keyed by the same names.

    Raises TranslationError listing every problem when tr does not match the data exactly.
    """
    problems = _validate(files, tr)
    if problems:
        raise TranslationError(source, problems)
    en = copy.deepcopy(files)
    for r in en["roles.json"]:
        r["name"] = tr["roles"][r["slug"]]["name"]
        r["root_label"] = tr["roles"][r["slug"]]["root_label"]
    for s in en["skills.json"]:
        t = tr["skills"][s["slug"]]
        s.update(name=t["name"], description=t["description"],
                 concepts=list(t["concepts"]), practice=t["practice"])
        for r in s["resources"]:
            r["title"] = tr["resources"].get(r["title"], r["title"])
    for role in _role_slugs(en):
        for c in en[f"roles/{role}/clusters.json"]:
            c["name"] = tr["clusters"][c["slug"]]
        for name in ("companies.json", "sources.json"):
            for c in en[f"roles/{role}/{name}"]:
                c["name"] = tr["companies"][c["code"]]
        for phase, title in zip(en[f"roles/{role}/roadmap.json"]["phases"], tr["phases"][role]):
            phase["title"] = title
    return en


def load_translations(path: Path) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise TranslationError(path, ["file not found"]) from None
    except json.JSONDecodeError as e:
        raise TranslationError(path, [f"not valid JSON: {e}"]) from None


def build(conn: sqlite3.Connection, i18n: Path | None = None) -> dict[str, object]:
    """Build every output file; with i18n, also the English mirror under en/."""
    edges = _edges(conn)
    files: dict[str, object] = {
        "meta.json": {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        "skills.json": _skills(conn, edges),
    }
    roles = []
    for role in _roles(conn):
        per_role = _role_files(conn, role["slug"], edges)
        roles.append({
            "slug": role["slug"],
            "name": role["name_zh"],
            "root_label": role["root_label"],
            "counts": {
                "companies": len(per_role["companies.json"]),
                "postings": sum(len(s["jobs"]) for s in per_role["sources.json"]),
                "skills": len(per_role["skills.json"]),
                "edges": len(per_role["edges.json"]),
            },
        })
        for name, payload in per_role.items():
            files[f"roles/{role['slug']}/{name}"] = payload
    files["roles.json"] = roles
    if i18n is not None:
        en = translate(files, load_translations(i18n), i18n)
        files.update({f"{EN_DIR}/{name}": payload for name, payload in en.items()})
    return files


def export(conn: sqlite3.Connection, out_dir: Path, i18n: Path | None = None) -> list[Path]:
    """Write the zh files to out_dir and, with i18n, the English mirror to out_dir/en.

    Nothing is written when the translations do not validate. Without i18n a stale out_dir/en
    is removed so it cannot drift from the zh files.
    """
    files = build(conn, i18n)
    out_dir = Path(out_dir)
    if i18n is None:
        shutil.rmtree(out_dir / EN_DIR, ignore_errors=True)
    for base in (out_dir, out_dir / EN_DIR):
        for d in LEGACY_DIRS:
            shutil.rmtree(base / d, ignore_errors=True)
        for f in LEGACY_FILES:
            (base / f).unlink(missing_ok=True)
    written = []
    for name, payload in files.items():
        path = out_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.export")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--db", type=Path, default=None, help="default: $SKILLMAP_DB or data/skillmap.db")
    parser.add_argument("--i18n", type=Path, default=DEFAULT_I18N, help="default: seed/i18n/en.json")
    args = parser.parse_args(argv)
    path = args.db or db.db_path()
    if not path.exists():
        print(f"{path}: database not found", file=sys.stderr)
        return 1
    conn = db.connect(path)
    try:
        written = export(conn, args.out, args.i18n)
    except TranslationError as e:
        print(e, file=sys.stderr)
        return 1
    finally:
        conn.close()
    print(f"{path} -> {args.out}: wrote {len(written)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
