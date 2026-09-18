"""
backend/workflow_tools/common.py

Small shared helpers used by the numbered workflow_tools scripts
(1_company_md_to_company_details.py, 2_company_details_to_initial_filter.py,
3_run_filter_for_tenders.py, 4_standardize_tenders.py) now that they're
importable modules as well as CLI scripts.

Currently just: loading GEMINI_API_KEY from backend/.env (falling back to an
already-exported environment variable, e.g. in CI), without requiring the
python-dotenv package.
"""

import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DEFAULT_ENV_PATH = BACKEND_DIR / ".env"


def load_env_file(env_path: Path = DEFAULT_ENV_PATH) -> None:
    """Populate os.environ from a simple KEY=VALUE .env file, without
    overriding any variable that's already set in the environment.

    Tries python-dotenv first if it's installed (handles more edge cases:
    quoted values, export prefixes, etc.); falls back to a minimal manual
    parser so this works with zero extra dependencies.
    """
    if not env_path.exists():
        return

    try:
        from dotenv import dotenv_values

        for key, value in dotenv_values(env_path).items():
            if key and value is not None and key not in os.environ:
                os.environ[key] = value
        return
    except ImportError:
        pass

    # Minimal fallback parser: KEY=VALUE per line, '#' comments, optional
    # surrounding quotes, optional leading "export ".
    with open(env_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value


def get_gemini_api_key(env_path: Path = DEFAULT_ENV_PATH) -> str:
    """Return GEMINI_API_KEY, loading backend/.env first if needed.

    Raises RuntimeError with a clear message if the key still isn't set
    afterward (caller decides whether that's a sys.exit in CLI mode or an
    exception to propagate when used as a library).
    """
    if not os.environ.get("GEMINI_API_KEY"):
        load_env_file(env_path)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. Set it in "
            f"{env_path} (GEMINI_API_KEY=your-key-here) or export it as an "
            "environment variable before running."
        )
    return api_key