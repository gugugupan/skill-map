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


def _clusters(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT slug, name_zh, color FROM cluster ORDER BY sort, slug")
    return [{"slug": r["slug"], "name": r["name_zh"], "color": r["color"]} for r in rows]


def _companies(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT code, name FROM source ORDER BY id")
    return [{"code": r["code"], "name": r["name"]} for r in rows]


def _sources(conn: sqlite3.Connection) -> list[dict]:
    jobs: dict[int, list[dict]] = {}
    for r in conn.execute("SELECT source_id, title, url FROM job_posting ORDER BY id"):
        jobs.setdefault(r["source_id"], []).append({"title": r["title"], "url": r["url"]})
    rows = conn.execute("SELECT id, code, name FROM source ORDER BY id")
    return [{"code": r["code"], "name": r["name"], "jobs": jobs.get(r["id"], [])} for r in rows]


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

    out = []
    for r in conn.execute("SELECT * FROM skill WHERE status = 'active' ORDER BY sort, id"):
        # M0: no extracted postings yet, so heat comes from the hand-curated reference companies.
        companies = json.loads(r["reference_companies"])
        out.append({
            "slug": r["slug"],
            "name": r["name_zh"],
            "cluster": r["cluster"],
            "description": r["description"],
            "concepts": json.loads(r["concepts"]),
            "practice": r["practice"],
            "resources": resources.get(r["id"], []),
            "companies": companies,
            "heat": len(companies),
            "prereqs": prereqs.get(r["slug"], []),
            "unlocks": unlocks.get(r["slug"], []),
        })
    return out


def _roadmaps(conn: sqlite3.Connection) -> dict[str, dict]:
    latest = conn.execute(
        "SELECT role_family, MAX(id) AS id FROM roadmap GROUP BY role_family ORDER BY role_family"
    ).fetchall()
    out = {}
    for rm in latest:
        phases: list[dict] = []
        current = None
        for r in conn.execute(
            "SELECT rs.phase, rs.phase_title, s.slug FROM roadmap_step rs"
            " JOIN skill s ON s.id = rs.skill_id"
            " WHERE rs.roadmap_id = ? ORDER BY rs.phase, rs.step_order",
            (rm["id"],),
        ):
            if r["phase"] != current:
                current = r["phase"]
                phases.append({"title": r["phase_title"], "skills": []})
            phases[-1]["skills"].append(r["slug"])
        out[rm["role_family"]] = {"phases": phases}
    return out


def build(conn: sqlite3.Connection) -> dict[str, object]:
    edges = _edges(conn)
    skills = _skills(conn, edges)
    files: dict[str, object] = {
        "meta.json": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "counts": {
                "companies": conn.execute("SELECT COUNT(*) FROM source").fetchone()[0],
                "postings": conn.execute("SELECT COUNT(*) FROM job_posting").fetchone()[0],
                "skills": len(skills),
                "edges": len(edges),
            },
        },
        "clusters.json": _clusters(conn),
        "companies.json": _companies(conn),
        "sources.json": _sources(conn),
        "skills.json": skills,
        "edges.json": edges,
    }
    for role_family, roadmap in _roadmaps(conn).items():
        files[f"roadmaps/{role_family}.json"] = roadmap
    return files


def export(conn: sqlite3.Connection, out_dir: Path) -> list[Path]:
    files = build(conn)
    out_dir = Path(out_dir)
    # Clear stale roadmaps so a removed role_family does not linger on the site.
    shutil.rmtree(out_dir / "roadmaps", ignore_errors=True)
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
