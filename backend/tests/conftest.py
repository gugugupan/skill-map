import importlib.util
import sys
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[2] / "seed"
FIXTURE_ROLES = Path(__file__).resolve().parent / "fixtures" / "roles"


def load_seed_module(name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SEED_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
