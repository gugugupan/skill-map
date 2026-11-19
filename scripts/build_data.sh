#!/usr/bin/env bash
# Rebuild the site data from scratch: fresh DB -> migrate -> seed -> export.
# Extra arguments are passed to app.export (e.g. --out DIR).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export SKILLMAP_DB="$ROOT/data/skillmap.db"

rm -f "$SKILLMAP_DB" "$SKILLMAP_DB-journal" "$SKILLMAP_DB-wal" "$SKILLMAP_DB-shm"

cd "$ROOT/backend"
uv run python -m app.db migrate
uv run python ../seed/import_reference.py "$SKILLMAP_DB"
uv run python -m app.export "$@"
