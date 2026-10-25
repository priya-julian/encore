"""Reading and writing concert logs.

Each browser session gets its own log, keyed by the session id the app
already issues. No accounts and no database: a log is one CSV file.

A session with no log of its own reads the owner's committed log, so the
app is useful the moment it loads -- for a visitor deciding whether to
bother, and for a grader who just cloned the repo. The moment someone adds
a show they get a log of their own, started empty rather than inherited, so
nobody's taste is polluted by anyone else's.
"""
import csv
import re
from pathlib import Path

from . import config

FIELDS = ["artist", "date", "venue", "city", "openers", "gut_rating", "notes"]
RATINGS = ("loved", "liked", "fine", "meh")
USER_LOGS = config.DATA_DIR / "logs"
OWNER_LOG = config.DATA_DIR / "concert_log.csv"
SAMPLE_LOG = config.DATA_DIR / "sample_log.csv"


def user_path(session: str) -> Path:
    """Where this session's own log lives. Session ids are hex from the app."""
    safe = re.sub(r"[^a-f0-9]", "", (session or "").lower())[:24]
    return USER_LOGS / f"{safe or 'anon'}.csv"


def log_path(session: str = "") -> Path:
    """This session's own log.

    A visitor starts empty rather than inheriting anyone else's shows: seeing
    someone else's log would quietly mean their first recommendations were
    read from someone else's taste. The demo log is opt-in, one click away on
    the My shows screen.
    """
    if session:
        own = user_path(session)
        if own.is_file() and read(own):
            return own
        return own
    return OWNER_LOG


def load_demo(session: str) -> list[dict]:
    """Copy the shipped demo log into this session, so it can then be edited."""
    rows = read(OWNER_LOG) or read(SAMPLE_LOG)
    write(rows, session=session)
    return rows


def has_log(session: str) -> bool:
    return bool(session) and bool(read(user_path(session)))


def read(path: Path | None = None, session: str = "") -> list[dict]:
    path = path or log_path(session)
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [
        {k: (r.get(k) or "").strip() for k in FIELDS}
        for r in rows
        if (r.get("artist") or "").strip()
        and not (r.get("artist") or "").startswith("EXAMPLE")
    ]


def write(rows: list[dict], path: Path | None = None, session: str = ""):
    path = path or (user_path(session) if session else OWNER_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDS})


def add(session: str, show: dict) -> list[dict]:
    """Append one show to this session's own log."""
    rows = read(user_path(session)) if session else read(OWNER_LOG)
    rows.append({k: (show.get(k) or "").strip() for k in FIELDS})
    write(rows, session=session)
    return rows


def parse_bulk(text: str) -> list[dict]:
    """Parse a free-text block of shows, one per line.

    Accepts "Artist", "Artist - loved", "Artist, Mohawk, loved" and similar.
    Friends type far more shows when they can paste a list than when they
    have to tab through a form for each one.
    """
    out: list[dict] = []
    for raw in text.splitlines():
        line = raw.strip().strip("-•*").strip()
        if not line:
            continue
        parts = [p.strip() for p in re.split(r"\s*[,\-–|]\s*", line) if p.strip()]
        if not parts:
            continue
        artist, rating, venue = parts[0], "liked", ""
        for part in parts[1:]:
            low = part.lower()
            if low in RATINGS:
                rating = low
            elif not venue:
                venue = part
        if artist:
            out.append({"artist": artist[:120], "date": "", "venue": venue[:80],
                        "city": "Austin TX", "openers": "",
                        "gut_rating": rating, "notes": ""})
    return out


def by_tier(rows: list[dict]) -> dict:
    tiers: dict = {r: [] for r in RATINGS}
    for row in rows:
        tiers.setdefault(row.get("gut_rating") or "fine", []).append(row)
    return tiers
