"""Configuration and secret loading for Encore.

Per the course requirements, the app looks for a .env file in its own repo
folder first, then in the folder one level above it.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "cache"
DATA_DIR = REPO_ROOT / "data"

# The course model, per the posted project requirements.
MODEL = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

# Shows further out than this are ignored.
DISCOVERY_WINDOW_DAYS = 42
CITY = "Austin, TX"


def load_env() -> Path | None:
    """Load .env from the repo folder, else from one level above."""
    for candidate in (REPO_ROOT / ".env", REPO_ROOT.parent / ".env"):
        if candidate.is_file():
            load_dotenv(candidate)
            return candidate
    return None


def api_key() -> str:
    key = os.environ.get("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError(
            "PORTKEY_API_KEY not found. Put a .env file in this folder or one "
            "level above it. See .env.example."
        )
    return key
