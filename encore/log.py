"""Reading and writing the user's concert log."""
import csv
from pathlib import Path

from . import config

FIELDS = ["artist", "date", "venue", "city", "openers", "gut_rating", "notes"]
RATING_ORDER = {"loved": 3, "liked": 2, "fine": 1, "meh": 0}


def log_path() -> Path:
    """The user's own log if it has rows, else the shipped sample."""
    own = config.DATA_DIR / "concert_log.csv"
    if own.is_file() and len(read(own)) > 0:
        return own
    return config.DATA_DIR / "sample_log.csv"


def read(path: Path | None = None) -> list[dict]:
    path = path or log_path()
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh)]
    return [
        {k: (r.get(k) or "").strip() for k in FIELDS}
        for r in rows
        if (r.get("artist") or "").strip()
        and not (r.get("artist") or "").startswith("EXAMPLE")
    ]


def write(rows: list[dict], path: Path | None = None):
    path = path or (config.DATA_DIR / "concert_log.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def by_tier(rows: list[dict]) -> dict:
    tiers: dict = {"loved": [], "liked": [], "fine": [], "meh": []}
    for r in rows:
        tiers.setdefault(r.get("gut_rating", "fine") or "fine", []).append(r)
    return tiers
