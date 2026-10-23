"""Profiler: turn a ranked concert log into a structured taste profile.

This runs rarely -- only when the log changes -- and its output is cached and
reused by every discovery run, so its cost amortises to near zero per run.
"""
import json

from .. import llm
from ..log import by_tier

SYSTEM = """You build a concertgoer's taste profile from the shows they have
been to and how much they liked each one.

Return JSON:
{
  "summary": str,
  "loves": [str],
  "avoids": [str],
  "venue_preference": str,
  "discovery_appetite": str,
  "confidence": str
}

- "summary" is 2-3 sentences in second person ("You go out for..."). Specific
  and recognisable, not horoscope-vague.
- "loves" and "avoids" are 4-6 short phrases each: scenes, sounds, eras,
  kinds of show. Ground them in the actual log.
- "venue_preference" covers room size and setting, inferred from the venues.
- "discovery_appetite": do they turn up for unknown local acts, or mostly
  established touring artists?
- "confidence": "low", "medium" or "high", based on how many shows and how
  much variety the log has. Say low if the log is thin.
- Never invent an artist that is not in the log.
"""


def build(rows: list[dict], meter=None) -> dict:
    if not rows:
        return {"summary": "", "loves": [], "avoids": [], "venue_preference": "",
                "discovery_appetite": "", "confidence": "low", "shows": 0}

    tiers = by_tier(rows)

    def fmt(key: str) -> str:
        items = tiers.get(key) or []
        return "\n".join(
            f"- {r['artist']}"
            + (f" (with {r['openers']})" if r.get("openers") else "")
            + f" at {r['venue']}, {r['date']}"
            + (f" -- {r['notes']}" if r.get("notes") else "")
            for r in items
        ) or "(none)"

    user = (
        f"LOVED ({len(tiers.get('loved') or [])} shows):\n{fmt('loved')}\n\n"
        f"LIKED ({len(tiers.get('liked') or [])} shows):\n{fmt('liked')}\n\n"
        f"FINE ({len(tiers.get('fine') or [])} shows):\n{fmt('fine')}\n\n"
        f"MEH ({len(tiers.get('meh') or [])} shows):\n{fmt('meh')}"
    )
    try:
        profile = json.loads(llm.complete("profiler", SYSTEM, user, meter=meter,
                                          json_mode=True))
    except Exception as exc:
        return {"summary": "", "loves": [], "avoids": [], "venue_preference": "",
                "discovery_appetite": "", "confidence": "low", "shows": len(rows),
                "error": type(exc).__name__}
    profile["shows"] = len(rows)
    return profile
