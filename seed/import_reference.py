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
DEFAULT_OVERRIDES = SEED_DIR / "reference_overrides.json"
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


def apply_overrides(sources: list, overrides: dict) -> None:
    """Replace (title, url) of SOURCES jobs matched by (company code, original title), in place."""
    for o in overrides["jobs"]:
        hits = [
            job
            for src in sources if src["k"] == o["code"]
            for job in src["jobs"] if job[0] == o["original_title"]
        ]
        if not hits:
            raise ValueError(f"override not found in SOURCES: {o['code']} {o['original_title']!r}")
        for job in hits:
            job[0], job[1] = o["title"], o["url"]


def apply_skill_companies(nodes: list, codes, spec: dict) -> list[str]:
    """Edit N[].jd in place from {slug: {"add": [...], "remove": [...]}}.

    Returns the slugs whose edit would leave no company; those keep their original jd.
    """
    by_slug = {n["id"]: n for n in nodes}
    kept = []
    for slug, change in spec.items():
        if slug not in by_slug:
            raise ValueError(f"skill_companies: unknown skill {slug!r}")
        unknown = set(change) - {"add", "remove"}
        if unknown:
            raise ValueError(f"skill_companies: {slug}: unknown keys {sorted(unknown)}")
        current = by_slug[slug]["jd"].split()
        add, remove = change.get("add", []), change.get("remove", [])
        for code in add + remove:
            if code not in codes:
                raise ValueError(f"skill_companies: {slug}: unknown company {code!r}")
        for code in remove:
            if code not in current:
                raise ValueError(f"skill_companies: {slug}: remove {code!r} not in {current}")
        for code in add:
            if code in current:
                raise ValueError(f"skill_companies: {slug}: add {code!r} already in {current}")
        result = [c for c in current if c not in remove] + add
        if not result:
            kept.append(slug)
            continue
        by_slug[slug]["jd"] = " ".join(result)
    return kept


def _dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _id(conn, sql: str, params: tuple) -> int:
    return conn.execute(sql, params).fetchone()[0]


def _import(conn, data: dict) -> None:
    for sort, (slug, c) in enumerate(data["CLUSTERS"].items()):
        conn.execute(
            "INSERT INTO cluster (slug, name_zh, color, sort, role_family) VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT (slug) DO UPDATE SET name_zh = excluded.name_zh,"
            " color = excluded.color, sort = excluded.sort, role_family = excluded.role_family",
            (slug, c["name"], c["color"], sort, ROLE_FAMILY),
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

    conn.execute("DELETE FROM role_company WHERE role_family = ?", (ROLE_FAMILY,))
    for sort, code in enumerate(jd):
        conn.execute(
            "INSERT INTO role_company (role_family, source_id, sort) VALUES (?, ?, ?)",
            (ROLE_FAMILY, source_ids[code], sort),
        )

    for src in data["SOURCES"]:
        code = src["k"]
        for title, url in src["jobs"]:
            conn.execute(
                "INSERT INTO job_posting (source_id, company, title, url, role_family, raw_text)"
                " VALUES (?, ?, ?, ?, ?, NULL)"
                " ON CONFLICT (source_id, title, role_family) DO UPDATE SET company = excluded.company,"
                " url = excluded.url",
                (source_ids[code], jd[code], title, url or None, ROLE_FAMILY),
            )

    skill_ids = {}
    conn.execute("DELETE FROM role_skill WHERE role_family = ?", (ROLE_FAMILY,))
    for sort, n in enumerate(data["N"]):
        conn.execute(
            "INSERT INTO skill (slug, name_zh, description, concepts, practice, status)"
            " VALUES (?, ?, ?, ?, ?, 'active')"
            " ON CONFLICT (slug) DO UPDATE SET name_zh = excluded.name_zh,"
            " description = excluded.description,"
            " concepts = excluded.concepts, practice = excluded.practice",
            (n["id"], n["n"], n["d"], _dumps(n["k"]), n["p"]),
        )
        skill_ids[n["id"]] = _id(conn, "SELECT id FROM skill WHERE slug = ?", (n["id"],))
        conn.execute(
            "INSERT INTO role_skill (role_family, skill_id, cluster_slug, reference_companies, sort)"
            " VALUES (?, ?, ?, ?, ?)",
            (ROLE_FAMILY, skill_ids[n["id"]], n["c"], _dumps(n["jd"].split()), sort),
        )

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


def import_reference(db_path=None, html_path=DEFAULT_HTML, overrides_path=DEFAULT_OVERRIDES) -> None:
    data = extract_constants(Path(html_path).read_text(encoding="utf-8"))
    if overrides_path is not None:
        overrides = json.loads(Path(overrides_path).read_text(encoding="utf-8"))
        apply_overrides(data["SOURCES"], overrides)
        kept = apply_skill_companies(data["N"], data["JD"], overrides.get("skill_companies", {}))
        for slug in kept:
            print(f"skill_companies: {slug} would have no company, kept original mapping", file=sys.stderr)
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
