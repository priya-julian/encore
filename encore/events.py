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


def load() -> list[dict]:
    if not EVENTS_PATH.is_file():
        return []
    rows = []
    for line in EVENTS_PATH.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def summary() -> dict:
    rows = load()
    sessions = {r["session"] for r in rows if r.get("session")}
    kinds: dict = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    runs = kinds.get("run", 0)
    new_to_me = kinds.get("new_to_me", 0)
    return {
        "sessions": len(sessions),
        "runs": runs,
        "shows_surfaced": sum(r.get("count", 0) for r in rows if r["kind"] == "run"),
        "new_to_me": new_to_me,
        "saved": kinds.get("save", 0),
        "ticket_clicks": kinds.get("ticket_click", 0),
        "by_kind": kinds,
    }
