"""Import the reference implementation (seed/reference.html) into the SQLite database.

Usage: cd backend && uv run python ../seed/import_reference.py [db_path] [html_path]
"""

import json
import re
import subprocess
import sys
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SEED_DIR.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import db  # noqa: E402

DEFAULT_HTML = SEED_DIR / "reference.html"
ROLE_FAMILY = "agent-infra"
ROADMAP_ORIGIN = "reference"
CONSTANTS = ("JD", "SOURCES", "CLUSTERS", "N", "PRE", "PATH")

_TOP_LEVEL_DECL = re.compile(r"^(?:const|let|var|function)\s+([A-Za-z_$][\w$]*)", re.M)

# First match wins; order matters (e.g. "Codex CLI 源码（GitHub）" must hit repo, not doc).
_RESOURCE_TYPE_RULES = (
    ("paper", ("论文",)),
    ("course", ("课程",)),
    ("repo", ("源码", "代码", "GitHub")),
    ("doc", ("文档", "规范", "手册", "RFC", "《")),
)


def resource_type(title: str) -> str:
    for rtype, needles in _RESOURCE_TYPE_RULES:
        if any(n in title for n in needles):
            return rtype
    return "blog"


def extract_constants(html: str) -> dict:
    decls = [(m.start(), m.group(1)) for m in _TOP_LEVEL_DECL.finditer(html)]
    snippets = []
    for name in CONSTANTS:
        idx = next((i for i, (_, n) in enumerate(decls) if n == name), None)
        if idx is None:
            raise ValueError(f"const {name} not found in reference html")
        start = decls[idx][0]
        end = decls[idx + 1][0] if idx + 1 < len(decls) else len(html)
        snippets.append(html[start:end])
    program = "\n".join(snippets) + f"\nprocess.stdout.write(JSON.stringify({{{', '.join(CONSTANTS)}}}));\n"
    out = subprocess.run(["node", "-e", program], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def _dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _id(conn, sql: str, params: tuple) -> int:
    return conn.execute(sql, params).fetchone()[0]


def _import(conn, data: dict) -> None:
    for sort, (slug, c) in enumerate(data["CLUSTERS"].items()):
        conn.execute(
            "INSERT INTO cluster (slug, name_zh, color, sort) VALUES (?, ?, ?, ?)"
            " ON CONFLICT (slug) DO UPDATE SET name_zh = excluded.name_zh,"
            " color = excluded.color, sort = excluded.sort",
            (slug, c["name"], c["color"], sort),
        )

    jd = data["JD"]
    source_ids = {}
    for code, company in jd.items():
        conn.execute(
            "INSERT INTO source (code, name, type, url, company) VALUES (?, ?, 'manual', NULL, ?)"
            " ON CONFLICT (code) DO UPDATE SET name = excluded.name,"
            " type = excluded.type, company = excluded.company",
            (code, company, company),
        )
        source_ids[code] = _id(conn, "SELECT id FROM source WHERE code = ?", (code,))

    for src in data["SOURCES"]:
        code = src["k"]
        for title, url in src["jobs"]:
            conn.execute(
                "INSERT INTO job_posting (source_id, company, title, url, role_family, raw_text)"
                " VALUES (?, ?, ?, ?, ?, NULL)"
                " ON CONFLICT (source_id, title) DO UPDATE SET company = excluded.company,"
                " url = excluded.url, role_family = excluded.role_family",
                (source_ids[code], jd[code], title, url or None, ROLE_FAMILY),
            )

    skill_ids = {}
    for sort, n in enumerate(data["N"]):
        conn.execute(
            "INSERT INTO skill (slug, name_zh, cluster, description, concepts, practice,"
            " reference_companies, sort, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')"
            " ON CONFLICT (slug) DO UPDATE SET name_zh = excluded.name_zh,"
            " cluster = excluded.cluster, description = excluded.description,"
            " concepts = excluded.concepts, practice = excluded.practice,"
            " reference_companies = excluded.reference_companies, sort = excluded.sort",
            (n["id"], n["n"], n["c"], n["d"], _dumps(n["k"]), n["p"], _dumps(n["jd"].split()), sort),
        )
        skill_ids[n["id"]] = _id(conn, "SELECT id FROM skill WHERE slug = ?", (n["id"],))

    for n in data["N"]:
        for rank, title in enumerate(n["r"]):
            conn.execute(
                "INSERT INTO resource (title, url, type, added_by) VALUES (?, NULL, ?, 'seed')"
                " ON CONFLICT (title) DO UPDATE SET type = excluded.type",
                (title, resource_type(title)),
            )
            rid = _id(conn, "SELECT id FROM resource WHERE title = ?", (title,))
            conn.execute(
                "INSERT INTO skill_resource (skill_id, resource_id, rank) VALUES (?, ?, ?)"
                " ON CONFLICT (skill_id, resource_id) DO UPDATE SET rank = excluded.rank",
                (skill_ids[n["id"]], rid, rank),
            )

    for frm, to in data["PRE"]:
        conn.execute(
            "INSERT OR IGNORE INTO skill_edge (from_skill, to_skill, type) VALUES (?, ?, 'prereq')",
            (skill_ids[frm], skill_ids[to]),
        )

    row = conn.execute(
        "SELECT id FROM roadmap WHERE role_family = ? AND json_extract(params, '$.origin') = ?",
        (ROLE_FAMILY, ROADMAP_ORIGIN),
    ).fetchone()
    if row:
        roadmap_id = row[0]
    else:
        roadmap_id = conn.execute(
            "INSERT INTO roadmap (role_family, params) VALUES (?, ?)",
            (ROLE_FAMILY, _dumps({"origin": ROADMAP_ORIGIN})),
        ).lastrowid
    conn.execute("DELETE FROM roadmap_step WHERE roadmap_id = ?", (roadmap_id,))
    for phase, stage in enumerate(data["PATH"], start=1):
        for order, slug in enumerate(stage["ids"]):
            conn.execute(
                "INSERT INTO roadmap_step (roadmap_id, phase, phase_title, step_order, skill_id)"
                " VALUES (?, ?, ?, ?, ?)",
                (roadmap_id, phase, stage["t"], order, skill_ids[slug]),
            )


def import_reference(db_path=None, html_path=DEFAULT_HTML) -> None:
    data = extract_constants(Path(html_path).read_text(encoding="utf-8"))
    conn = db.connect(db_path)
    try:
        db.migrate(conn)
        with conn:
            _import(conn, data)
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print("usage: import_reference.py [db_path] [html_path]", file=sys.stderr)
        return 2
    db_path = argv[0] if argv else db.db_path()
    html_path = argv[1] if len(argv) > 1 else DEFAULT_HTML
    import_reference(db_path, html_path)
    print(f"{db_path}: imported {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
