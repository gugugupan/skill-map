"""Write the English mirror of the hand-written frontend fixtures.

frontend/fixtures/data/ is a hand-written zh sample (not exported from a DB). This applies
scripts/fixtures/en.json with the same validation and substitution as app.export and writes
frontend/fixtures/data/en/, replacing whatever is there.

Usage: cd backend && uv run python ../scripts/build_fixture_en.py
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import export  # noqa: E402

DATA = ROOT / "frontend" / "fixtures" / "data"
I18N = ROOT / "scripts" / "fixtures" / "en.json"


def main() -> int:
    files = {
        str(p.relative_to(DATA)): json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(DATA.rglob("*.json"))
        if p.relative_to(DATA).parts[0] != export.EN_DIR
    }
    try:
        en = export.translate(files, export.load_translations(I18N), I18N)
    except export.TranslationError as e:
        print(e, file=sys.stderr)
        return 1
    out = DATA / export.EN_DIR
    shutil.rmtree(out, ignore_errors=True)
    for name, payload in en.items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # Same formatting as the hand-written zh fixtures.
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(en)} file(s) to {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
