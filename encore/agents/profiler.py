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

Voice: write with conviction, in second person. State what is true of them
rather than hedging about it. No "seems to", "appears to", "moderate to high",
"you may", "somewhat". If the log is too thin to support a claim, leave the
claim out instead of qualifying it.

- "summary": 2-3 sentences. Specific and recognisable, never horoscope-vague.
- "loves" and "avoids": 4-5 short phrases each, describing SOUNDS, SCENES,
  ERAS and KINDS OF SHOW. Never name an artist, band or venue in these lists --
  the reader already knows who they have seen; what they want back is the
  pattern underneath. "Arena pop built on spectacle" not "shows like Kesha".
- "avoids" comes from their lowest-rated shows and anything they turned down.
  Describe what did not land, not who.
- "venue_preference": room size and setting, in one sentence.
- "discovery_appetite": one sentence on whether they turn out for unfamiliar
  acts or stick to artists they already know.
- "confidence": "low", "medium" or "high", from how many shows and how much
  variety the log has.
- Base everything on the log. Never invent a show they did not attend.
- Turned-down recommendations are real negative signal, but weaker than a
  show they attended and rated. Do not let one rejection outweigh the log.
"""


def build(rows: list[dict], rejected: list[str] | None = None, meter=None) -> dict:
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
    if rejected:
        user += (
            "\n\nRECOMMENDATIONS THEY TURNED DOWN (they were offered these "
            "upcoming shows and said 'not for me'; weigh this as negative "
            "signal alongside the MEH list):\n"
            + "\n".join(f"- {a}" for a in rejected)
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
