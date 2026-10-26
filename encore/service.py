"""Caches a user's picks so the web app does not re-run agents on every load."""
import hashlib
import json
import time

from . import config, events, llm, log, pipeline, pricing
from .agents import profiler, ranker, verifier

PICKS_CACHE = config.CACHE_DIR / "picks"
PROFILE_CACHE = config.CACHE_DIR / "profiles"
TTL = 6 * 60 * 60


def log_fingerprint(rows: list[dict], rejected: list[str] | None = None) -> str:
    """Identity of the inputs a profile and its picks depend on.

    Rejections are part of the key: saying 'not for me' should invalidate the
    cached picks, or the feedback would appear to do nothing.
    """
    blob = json.dumps({"rows": rows, "rejected": sorted(rejected or [])},
                      sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _cached(folder, key: str, ttl: int = TTL):
    path = folder / f"{key}.json"
    if path.is_file() and time.time() - path.stat().st_mtime < ttl:
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _store(folder, key: str, payload):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{key}.json").write_text(json.dumps(payload))


def get_profile(rows: list[dict], meter: llm.Meter,
                rejected: list[str] | None = None) -> dict:
    key = log_fingerprint(rows, rejected)
    hit = _cached(PROFILE_CACHE, key, ttl=30 * 24 * 60 * 60)
    if hit is not None:
        return hit
    profile = profiler.build(rows, rejected=rejected, meter=meter)
    # Never cache a failed profile: a missing key or a transient API error
    # would otherwise be frozen in for the life of the cache.
    if profile.get("summary"):
        _store(PROFILE_CACHE, key, profile)
    return profile


def get_picks(force: bool = False, session: str = "") -> dict:
    """Profile -> sweep -> rank -> verify, cached on the log's fingerprint.

    Caches are keyed by log content, not by session, so two users with the
    same shows share a cached result rather than paying twice.
    """
    rows = log.read(session=session)
    rejected = list(events.rejected_artists(session))
    if force:
        # An explicit Re-run is a request for different shows, not the same
        # five again; what they were just shown is treated like a rejection
        # for this run only.
        rejected += [a for a in events.recently_shown(session)
                     if a not in rejected]
    meter = llm.Meter()
    started = time.time()

    if not rows:
        return {"picks": [], "profile": {}, "error": "no shows in your log yet",
                "meter": meter.totals(), "cost": 0.0, "seconds": 0.0}

    key = log_fingerprint(rows, rejected)
    if not force:
        hit = _cached(PICKS_CACHE, key)
        if hit is not None:
            hit["from_cache"] = True
            return hit

    profile = get_profile(rows, meter, rejected=rejected)
    if not profile.get("summary"):
        reason = profile.get("error", "")
        detail = ("the app could not reach the model — check that "
                  "PORTKEY_API_KEY is set"
                  if reason == "RuntimeError" else
                  f"could not build your taste profile ({reason or 'unknown'})")
        return {"picks": [], "profile": profile, "considered": 0,
                "injections": [], "meter": meter.totals(), "cost": 0.0,
                "seconds": round(time.time() - started, 1),
                "from_cache": False, "error": detail}

    swept = pipeline.sweep(meter=meter)
    # Never offer back something already turned down.
    turned_down = {a.lower() for a in rejected}
    swept["shows"] = [s for s in swept["shows"]
                      if s.get("artist", "").lower() not in turned_down]
    if not swept["shows"]:
        return {"picks": [], "profile": profile, "considered": 0,
                "injections": [], "meter": meter.totals(), "cost": 0.0,
                "seconds": round(time.time() - started, 1),
                "from_cache": False,
                "error": "could not read any Austin listings just now"}

    picks = verifier.verify_all(ranker.rank(swept["shows"], profile, meter=meter),
                                meter=meter)

    totals = meter.totals()
    payload = {
        "picks": picks,
        "profile": profile,
        "considered": len(swept["shows"]),
        "injections": swept["injections"],
        "meter": totals,
        "cost": pricing.cost_usd(config.MODEL, totals["prompt_tokens"],
                                 totals["completion_tokens"]),
        "seconds": round(time.time() - started, 1),
        "from_cache": False,
        "error": "",
    }
    # Only a run that actually produced picks is worth remembering.
    if picks:
        _store(PICKS_CACHE, key, payload)
    return payload
