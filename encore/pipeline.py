"""Discovery sweep: fetch the Austin show list and extract it, fast and cached.

Days are independent, so they are extracted concurrently. Each extracted day
is cached to disk, which is the app's biggest cost lever: a warm cache serves
a run for free, and across many users one sweep is shared by everyone.
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from . import config, llm
from .agents import scout, showlist

DAY_CACHE = config.CACHE_DIR / "days"
MAX_WORKERS = 8

# Near-term listings change (shows sell out, times move); far-out ones don't.
NEAR_TERM_DAYS = 7
NEAR_TTL = 12 * 60 * 60
FAR_TTL = 7 * 24 * 60 * 60


def _cache_file(day: date) -> Path:
    return DAY_CACHE / f"{day.isoformat()}.json"


def _ttl_for(day: date, today: date) -> int:
    return NEAR_TTL if (day - today).days <= NEAR_TERM_DAYS else FAR_TTL


def _read_cache(day: date, today: date) -> dict | None:
    path = _cache_file(day)
    if not path.is_file():
        return None
    if time.time() - path.stat().st_mtime > _ttl_for(day, today):
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(day: date, payload: dict):
    path = _cache_file(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def load_blocks(window: int, today: date, force: bool = False) -> list[dict]:
    """Fetch the listing page and group it into day blocks."""
    html = scout.fetch(showlist.SOURCE_URL, force=force)
    if html is None:
        return []
    records = showlist.within_window(showlist.load_records(html), window, today=today)
    return showlist.group_by_day(records)


def sweep(meter: llm.Meter | None = None, force: bool = False,
          window_days: int | None = None) -> dict:
    """Return {"shows": [...], "days": int, "cached_days": int, "injections": [...]}"""
    today = date.today()
    window = window_days or config.DISCOVERY_WINDOW_DAYS
    blocks = load_blocks(window, today, force=force)

    shows: list[dict] = []
    injections: list[dict] = []
    cached_days = 0
    pending: list[dict] = []

    for block in blocks:
        hit = None if force else _read_cache(block["date"], today)
        if hit is not None:
            cached_days += 1
            shows.extend(hit.get("shows", []))
            if hit.get("injection_suspected"):
                injections.append({"date": block["date"].isoformat(),
                                   "note": hit.get("injection_note", "")})
            if meter is not None:
                meter.record("showlist", None, 0.0, cached=True)
        else:
            pending.append(block)

    if pending:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            for res in pool.map(lambda b: showlist.extract_day(b, meter=meter), pending):
                if res["error"]:
                    continue
                payload = {
                    "shows": res["shows"],
                    "injection_suspected": res["injection_suspected"],
                    "injection_note": res["injection_note"],
                }
                _write_cache(res["date"], payload)
                shows.extend(res["shows"])
                if res["injection_suspected"]:
                    injections.append({"date": res["date"].isoformat(),
                                       "note": res["injection_note"]})

    shows.sort(key=lambda s: (s.get("date", ""), s.get("artist", "")))
    return {
        "shows": shows,
        "days": len(blocks),
        "cached_days": cached_days,
        "injections": injections,
    }
