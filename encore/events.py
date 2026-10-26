"""Usage instrumentation, for the impact section.

One JSON object per line, no personal data beyond an anonymous session id.
"""
import json
import threading
import time
from pathlib import Path

from . import config

EVENTS_PATH = config.DATA_DIR / "events.jsonl"
_lock = threading.Lock()


def record(kind: str, session: str = "", **data):
    row = {"ts": round(time.time(), 1), "kind": kind, "session": session[:12], **data}
    try:
        with _lock:
            EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with EVENTS_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
    except OSError:
        pass


LIVE_PATH = config.DATA_DIR / "events_live.jsonl"
BASELINE_PATH = config.DATA_DIR / "events_baseline.json"


def baseline_ts() -> float:
    """Timestamp before which events are developer testing, not real usage.

    Every curl against the deployed app creates a fresh session, so without
    this the impact numbers would quietly count my own smoke tests as users.
    """
    if not BASELINE_PATH.is_file():
        return 0.0
    try:
        return float(json.loads(BASELINE_PATH.read_text()).get("ts", 0))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 0.0


def load(path: Path | None = None) -> list[dict]:
    path = path or EVENTS_PATH
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def rejected_artists(session: str = "", limit: int = 40) -> list[str]:
    """Artists the user marked 'not for me', newest first.

    This is the one signal the show log cannot provide: the log says what you
    chose to attend, never what you were offered and turned down.
    """
    seen: list[str] = []
    for row in reversed(load()):
        if row.get("kind") != "not_for_me":
            continue
        if session and row.get("session") != session[:12]:
            continue
        artist = (row.get("artist") or "").strip()
        if artist and artist not in seen:
            seen.append(artist)
        if len(seen) >= limit:
            break
    return seen


def recently_shown(session: str, limit: int = 15) -> list[str]:
    """Artists this visitor was shown on their last couple of runs.

    Re-run should mean "show me something else". Without this it returns the
    same five, because the taste profile has not changed.
    """
    out: list[str] = []
    for row in reversed(load()):
        if row.get("kind") != "run" or row.get("session") != session[:12]:
            continue
        for artist in row.get("shown", []):
            if artist and artist not in out:
                out.append(artist)
        if len(out) >= limit:
            break
    return out[:limit]


def summary(path: Path | None = None) -> dict:
    """Usage summary, with the per-user rates the write-up needs.

    Defaults to this machine's events. The report passes the file pulled
    from the deployed app instead, so local development never inflates the
    numbers reported as real usage.
    """
    rows = load(path)
    if path is not None:
        cutoff = baseline_ts()
        rows = [r for r in rows if r.get("ts", 0) > cutoff]

    kinds: dict = {}
    per_session: dict = {}
    for row in rows:
        kind = row.get("kind", "")
        kinds[kind] = kinds.get(kind, 0) + 1
        session = row.get("session")
        if session:
            per_session.setdefault(session, set()).add(kind)

    # Someone who only loaded the page is not a user of the thing.
    engaged = {s for s, ks in per_session.items()
               if ks & {"run", "add_bulk", "add_show", "load_demo"}}
    found_new = {s for s, ks in per_session.items() if "new_to_me" in ks}
    saved = {s for s, ks in per_session.items() if "save" in ks}
    built = {s for s, ks in per_session.items() if ks & {"add_bulk", "add_show"}}

    def pct(part: set) -> float:
        return round(100 * len(part) / len(engaged), 1) if engaged else 0.0

    runs = kinds.get("run", 0)
    return {
        "sessions": len(engaged),
        "built_own_log": len(built),
        "runs": runs,
        "runs_per_user": round(runs / len(engaged), 1) if engaged else 0.0,
        "shows_surfaced": sum(r.get("count", 0) for r in rows if r["kind"] == "run"),
        "new_to_me": kinds.get("new_to_me", 0),
        "users_found_new": len(found_new),
        "pct_found_new": pct(found_new),
        "saved": kinds.get("save", 0),
        "users_saved": len(saved),
        "pct_saved": pct(saved),
        "not_for_me": kinds.get("not_for_me", 0),
        "ticket_clicks": kinds.get("ticket_click", 0),
        "by_kind": kinds,
    }
