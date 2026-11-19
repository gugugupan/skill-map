"""Import per-role seeds (seed/roles/<role>.json) into the SQLite database.

Run after import_reference.py. Every file is validated before anything is written.

Usage: cd backend && uv run python ../seed/import_roles.py [db_path] [roles_dir]
"""

import json
import sys
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SEED_DIR.parent / "backend"
for p in (BACKEND_DIR, SEED_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app import db  # noqa: E402
from import_reference import ROLE_FAMILY as REFERENCE_ROLE, resource_type  # noqa: E402

DEFAULT_ROLES_DIR = SEED_DIR / "roles"
ROADMAP_ORIGIN = "seed"
REUSE_KEYS = {"slug", "cluster", "companies"}
FULL_KEYS = {"name", "description", "concepts", "practice"}


class SeedError(ValueError):
    pass


def _dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _load(roles_dir: Path) -> list[tuple[str, dict]]:
    return [(f.name, json.loads(f.read_text(encoding="utf-8")))
            for f in sorted(Path(roles_dir).glob("*.json"))]


def _has_cycle(edges: set[tuple[str, str]]) -> list[str] | None:
    graph: dict[str, list[str]] = {}
    for a, b in sorted(edges):
        graph.setdefault(a, []).append(b)
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(n: str) -> list[str] | None:
        state[n] = 1
        stack.append(n)
        for m in graph.get(n, []):
            if state.get(m) == 1:
                return stack[stack.index(m):] + [m]
            if m not in state and (found := visit(m)):
                return found
        stack.pop()
        state[n] = 2
        return None

    for n in sorted(graph):
        if n not in state and (found := visit(n)):
            return found
    return None


def validate(conn, files: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
    """Return the files ordered by role sort, or raise SeedError listing every problem."""
    errors: list[str] = []
    roles = {r["slug"]: r["sort"] for r in conn.execute("SELECT slug, sort FROM role")}
    existing_skills = {r[0] for r in conn.execute("SELECT slug FROM skill")}
    reference_skills = {r[0] for r in conn.execute(
        "SELECT s.slug FROM role_skill rs JOIN skill s ON s.id = rs.skill_id WHERE rs.role_family = ?",
        (REFERENCE_ROLE,))}
    # Skills written by an earlier run of this script are not "existing" for collision purposes.
    owned_by_roles = {r[0] for r in conn.execute(
        "SELECT DISTINCT s.slug FROM role_skill rs JOIN skill s ON s.id = rs.skill_id"
        " WHERE rs.role_family != ?", (REFERENCE_ROLE,))} - reference_skills
    known_codes = {r[0] for r in conn.execute("SELECT code FROM source WHERE code IS NOT NULL")}
    cluster_owner = {r[0]: r[1] for r in conn.execute("SELECT slug, role_family FROM cluster")}
    edges = {(r[0], r[1]) for r in conn.execute(
        "SELECT f.slug, t.slug FROM skill_edge e JOIN skill f ON f.id = e.from_skill"
        " JOIN skill t ON t.id = e.to_skill WHERE e.type = 'prereq'")}

    seen_roles: dict[str, str] = {}
    full_defs: dict[str, str] = {}
    for fname, data in files:
        slug = (data.get("role") or {}).get("slug")
        if slug not in roles:
            errors.append(f"{fname}: unknown role {slug!r}")
        elif slug == REFERENCE_ROLE:
            errors.append(f"{fname}: role {slug!r} is imported from reference.html")
        elif slug in seen_roles:
            errors.append(f"{fname}: role {slug!r} already defined in {seen_roles[slug]}")
        else:
            seen_roles[slug] = fname
        for s in data.get("skills", []):
            if not FULL_KEYS & s.keys():
                continue
            sslug = s.get("slug")
            if sslug in full_defs:
                errors.append(f"{fname}: skill {sslug!r} fully defined again (first in {full_defs[sslug]})")
            elif sslug in existing_skills and sslug not in owned_by_roles:
                errors.append(f"{fname}: skill {sslug!r} already exists; reuse it with slug/cluster/companies only")
            else:
                full_defs[sslug] = fname
    known_skills = existing_skills | set(full_defs)

    for fname, data in files:
        role = (data.get("role") or {}).get("slug")
        clusters = [c["slug"] for c in data.get("clusters", [])]
        for c in data.get("clusters", []):
            if not c["slug"].startswith(f"{role}-"):
                errors.append(f"{fname}: cluster {c['slug']!r} must start with '{role}-'")
            owner = cluster_owner.get(c["slug"])
            if owner is not None and owner != role:
                errors.append(f"{fname}: cluster {c['slug']!r} belongs to role {owner!r}")
        if len(set(clusters)) != len(clusters):
            errors.append(f"{fname}: duplicate cluster slug")
        colors = [c.get("color") for c in data.get("clusters", [])]
        if len(set(colors)) != len(colors):
            errors.append(f"{fname}: duplicate cluster color")

        codes = [c["code"] for c in data.get("companies", [])]
        if len(set(codes)) != len(codes):
            errors.append(f"{fname}: duplicate company code")
        for c in data.get("companies", []):
            if not c.get("name") and c["code"] not in known_codes:
                errors.append(f"{fname}: company {c['code']!r} is new and needs a name")
        posted = set()
        for p in data.get("postings", []):
            if p.get("company") not in codes:
                errors.append(f"{fname}: posting {p.get('title')!r} references company "
                              f"{p.get('company')!r} not in this role's companies")
            if not p.get("url"):
                errors.append(f"{fname}: posting {p.get('title')!r} has no url")
            posted.add(p.get("company"))
        for code in codes:
            if code not in posted:
                errors.append(f"{fname}: company {code!r} has no posting")

        role_skills: list[str] = []
        for s in data.get("skills", []):
            sslug = s.get("slug")
            if sslug in role_skills:
                errors.append(f"{fname}: skill {sslug!r} listed twice")
            role_skills.append(sslug)
            if FULL_KEYS & s.keys():
                missing = FULL_KEYS - s.keys()
                if missing:
                    errors.append(f"{fname}: skill {sslug!r} missing {sorted(missing)}")
            else:
                extra = s.keys() - REUSE_KEYS
                if extra:
                    errors.append(f"{fname}: skill {sslug!r} reuse may only set {sorted(REUSE_KEYS)},"
                                  f" got {sorted(extra)}")
                if sslug not in known_skills:
                    errors.append(f"{fname}: skill {sslug!r} does not exist")
            if s.get("cluster") not in clusters:
                errors.append(f"{fname}: skill {sslug!r} uses unknown cluster {s.get('cluster')!r}")
            outside = [c for c in s.get("companies", []) if c not in codes]
            if outside:
                errors.append(f"{fname}: skill {sslug!r} companies {outside} not in this role's companies")

        for pair in data.get("prereqs", []):
            frm, to = pair
            for end in (frm, to):
                if end not in known_skills:
                    errors.append(f"{fname}: prereq [{frm!r}, {to!r}] references unknown skill {end!r}")
            if frm in reference_skills and to in reference_skills and (frm, to) not in edges:
                errors.append(f"{fname}: prereq [{frm!r}, {to!r}] joins two {REFERENCE_ROLE} skills")
            edges.add((frm, to))

        for phase in data.get("path", []):
            for sslug in phase.get("skills", []):
                if sslug not in role_skills:
                    errors.append(f"{fname}: path phase {phase.get('title')!r} lists"
                                  f" {sslug!r}, which is not a skill of this role")

    cycle = _has_cycle(edges)
    if cycle:
        errors.append(f"prereq cycle: {' -> '.join(cycle)}")
    if errors:
        raise SeedError("\n".join(errors))
    return sorted(files, key=lambda f: roles[f[1]["role"]["slug"]])


def _id(conn, sql: str, params: tuple) -> int:
    return conn.execute(sql, params).fetchone()[0]


def _write(conn, files: list[tuple[str, dict]]) -> list[str]:
    warnings: list[str] = []
    skill_ids = {r[0]: r[1] for r in conn.execute("SELECT slug, id FROM skill")}

    for _, data in files:
        for s in data.get("skills", []):
            if not FULL_KEYS & s.keys():
                continue
            conn.execute(
                "INSERT INTO skill (slug, name_zh, description, concepts, practice, status)"
                " VALUES (?, ?, ?, ?, ?, 'active')"
                " ON CONFLICT (slug) DO UPDATE SET name_zh = excluded.name_zh,"
                " description = excluded.description, concepts = excluded.concepts,"
                " practice = excluded.practice",
                (s["slug"], s["name"], s["description"], _dumps(s["concepts"]), s["practice"]),
            )
            sid = skill_ids[s["slug"]] = _id(conn, "SELECT id FROM skill WHERE slug = ?", (s["slug"],))
            conn.execute("DELETE FROM skill_resource WHERE skill_id = ?", (sid,))
            for rank, r in enumerate(s.get("resources", [])):
                url = r.get("url") or None
                row = conn.execute("SELECT id, url FROM resource WHERE title = ?", (r["title"],)).fetchone()
                if row is None:
                    rid = conn.execute(
                        "INSERT INTO resource (title, url, type, added_by) VALUES (?, ?, ?, 'seed')",
                        (r["title"], url, resource_type(r["title"])),
                    ).lastrowid
                else:
                    rid = row["id"]
                    if row["url"] != url:
                        warnings.append(f"resource {r['title']!r}: keeping url {row['url']!r},"
                                        f" ignoring {url!r} from skill {s['slug']!r}")
                conn.execute(
                    "INSERT INTO skill_resource (skill_id, resource_id, rank) VALUES (?, ?, ?)"
                    " ON CONFLICT (skill_id, resource_id) DO UPDATE SET rank = excluded.rank",
                    (sid, rid, rank),
                )

    for _, data in files:
        role = data["role"]["slug"]
        conn.execute("DELETE FROM role_skill WHERE role_family = ?", (role,))
        conn.execute("DELETE FROM role_company WHERE role_family = ?", (role,))

        for sort, c in enumerate(data.get("clusters", [])):
            conn.execute(
                "INSERT INTO cluster (slug, name_zh, color, sort, role_family) VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT (slug) DO UPDATE SET name_zh = excluded.name_zh,"
                " color = excluded.color, sort = excluded.sort",
                (c["slug"], c["name"], c["color"], sort, role),
            )

        source_ids = {}
        names = {}
        for sort, c in enumerate(data.get("companies", [])):
            row = conn.execute("SELECT id, name FROM source WHERE code = ?", (c["code"],)).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO source (code, name, type, url, company) VALUES (?, ?, 'manual', NULL, ?)",
                    (c["code"], c["name"], c["name"]),
                )
                row = conn.execute("SELECT id, name FROM source WHERE code = ?", (c["code"],)).fetchone()
            source_ids[c["code"]], names[c["code"]] = row["id"], row["name"]
            conn.execute(
                "INSERT INTO role_company (role_family, source_id, sort) VALUES (?, ?, ?)",
                (role, row["id"], sort),
            )

        for p in data.get("postings", []):
            conn.execute(
                "INSERT INTO job_posting (source_id, company, title, url, role_family)"
                " VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT (source_id, title, role_family) DO UPDATE SET company = excluded.company,"
                " url = excluded.url",
                (source_ids[p["company"]], names[p["company"]], p["title"], p["url"], role),
            )

        for sort, s in enumerate(data.get("skills", [])):
            conn.execute(
                "INSERT INTO role_skill (role_family, skill_id, cluster_slug, reference_companies, sort)"
                " VALUES (?, ?, ?, ?, ?)",
                (role, skill_ids[s["slug"]], s["cluster"], _dumps(s.get("companies", [])), sort),
            )

        for frm, to in data.get("prereqs", []):
            conn.execute(
                "INSERT OR IGNORE INTO skill_edge (from_skill, to_skill, type) VALUES (?, ?, 'prereq')",
                (skill_ids[frm], skill_ids[to]),
            )

        row = conn.execute(
            "SELECT id FROM roadmap WHERE role_family = ? AND json_extract(params, '$.origin') = ?",
            (role, ROADMAP_ORIGIN),
        ).fetchone()
        roadmap_id = row[0] if row else conn.execute(
            "INSERT INTO roadmap (role_family, params) VALUES (?, ?)",
            (role, _dumps({"origin": ROADMAP_ORIGIN})),
        ).lastrowid
        conn.execute("DELETE FROM roadmap_step WHERE roadmap_id = ?", (roadmap_id,))
        for phase, stage in enumerate(data.get("path", []), start=1):
            for order, sslug in enumerate(stage["skills"]):
                conn.execute(
                    "INSERT INTO roadmap_step (roadmap_id, phase, phase_title, step_order, skill_id)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (roadmap_id, phase, stage["title"], order, skill_ids[sslug]),
                )
    return warnings


def import_roles(db_path=None, roles_dir=DEFAULT_ROLES_DIR) -> list[str]:
    """Import every roles_dir/*.json; return resource warnings. Raises SeedError, writing nothing."""
    files = _load(roles_dir)
    conn = db.connect(db_path)
    try:
        db.migrate(conn)
        ordered = validate(conn, files)
        with conn:
            warnings = _write(conn, ordered)
    finally:
        conn.close()
    return warnings


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print("usage: import_roles.py [db_path] [roles_dir]", file=sys.stderr)
        return 2
    db_path = argv[0] if argv else db.db_path()
    roles_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_ROLES_DIR
    if not roles_dir.is_dir():
        print(f"{roles_dir}: not found, skipping")
        return 0
    try:
        warnings = import_roles(db_path, roles_dir)
    except SeedError as e:
        print(f"{roles_dir}: rejected\n{e}", file=sys.stderr)
        return 1
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(f"{db_path}: imported {roles_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
