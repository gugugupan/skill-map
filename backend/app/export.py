"""Export the SQLite database to the static JSON files the frontend reads.

Usage: cd backend && uv run python -m app.export [--out DIR] [--db PATH]
"""

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from app import db

DEFAULT_OUT = db.BACKEND_DIR.parent / "frontend" / "public" / "data"


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


def build(conn: sqlite3.Connection) -> dict[str, object]:
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
    return files


def export(conn: sqlite3.Connection, out_dir: Path) -> list[Path]:
    files = build(conn)
    out_dir = Path(out_dir)
    for d in LEGACY_DIRS:
        shutil.rmtree(out_dir / d, ignore_errors=True)
    for f in LEGACY_FILES:
        (out_dir / f).unlink(missing_ok=True)
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
    args = parser.parse_args(argv)
    path = args.db or db.db_path()
    if not path.exists():
        print(f"{path}: database not found", file=sys.stderr)
        return 1
    conn = db.connect(path)
    try:
        written = export(conn, args.out)
    finally:
        conn.close()
    print(f"{path} -> {args.out}: wrote {len(written)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
