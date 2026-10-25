"""Capture one real run, stage by stage, for the report's agent section.

Writes data/trace.txt: what each agent received, what it returned, what it
cost. The report embeds it verbatim.

Run:  python scripts/trace_run.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from encore import config, llm, log, pipeline, pricing  # noqa: E402
from encore.agents import profiler, ranker, scholar, verifier  # noqa: E402

LINES: list[str] = []


def say(text: str = ""):
    print(text)
    LINES.append(text)


def spend(meter: llm.Meter) -> str:
    t = meter.totals()
    cost = pricing.cost_usd(config.MODEL, t["prompt_tokens"], t["completion_tokens"])
    return (f"{t['calls']} calls, {t['cache_hits']} cache hits, "
            f"{t['prompt_tokens']} in / {t['completion_tokens']} out, "
            f"${cost:.5f}")


def main():
    config.load_env()
    meter = llm.Meter()
    started = time.time()
    say("ENCORE — traced run")
    say(f"model {config.MODEL} · {time.strftime('%Y-%m-%d %H:%M')}")
    say("=" * 66)

    say("\n[1] SCOUT — fetch and structure the city's listings")
    swept = pipeline.sweep(meter=meter)
    shows = swept["shows"]
    venues = {s["venue"] for s in shows if s["venue"]}
    say(f"    source      austin.showlists.net (one request)")
    say(f"    in          {swept['days']} days of raw listings")
    say(f"    out         {len(shows)} shows across {len(venues)} venues")
    say(f"    injections  {swept['injections'] or 'none flagged'}")
    say(f"    example     {shows[0]['artist']} @ {shows[0]['venue'] or 'TBA'}"
        f" ({shows[0]['date']})")
    say(f"    from source \"{shows[0]['source_title'][:58]}\"")

    say("\n[2] PROFILER — read the user's log into a taste profile")
    rows = log.read(log.OWNER_LOG)
    before = len(meter.calls)
    profile = profiler.build(rows, meter=meter)
    say(f"    in          {len(rows)} rated concerts")
    say(f"    out         confidence: {profile['confidence']}")
    say(f"    loves       {'; '.join(profile['loves'][:3])}")
    say(f"    avoids      {'; '.join(profile['avoids'][:3])}")
    say(f"    calls       {len(meter.calls) - before}")

    say("\n[3] RANKER (screen) — score every show, cheaply")
    screen_meter = llm.Meter()
    scored = ranker.screen(shows, profile, meter=screen_meter)
    top = scored[:ranker.SHORTLIST]
    say(f"    in          {len(shows)} shows, batched {ranker.BATCH_SIZE} per call")
    say(f"    out         {len(scored)} scored; keeping top {len(top)}")
    say(f"    spend       {spend(screen_meter)}")
    for s in top[:4]:
        say(f"      {s['score']:>3}  {s['artist'][:28]:30} {s['screen_why'][:30]}")
    say(f"      ...  cut-off at {top[-1]['score']} "
        f"(median of all {len(scored)}: {scored[len(scored)//2]['score']})")

    say("\n[4] SCHOLAR — research only the shortlist")
    sch_meter = llm.Meter()
    for s in top[:3]:
        r = scholar.research(s["artist"], meter=sch_meter)
        say(f"    {s['artist'][:26]:28} known={str(r['known']):5} "
            f"{(r['genre'] or '-')[:30]}")
        if r.get("sounds_like"):
            say(f"      sounds like {r['sounds_like'][:48]}")
    say(f"    spend       {spend(sch_meter)} (for 3 of {len(top)})")

    say("\n[5] RANKER (final) + [6] VERIFIER")
    final_meter = llm.Meter()
    picks = verifier.verify_all(
        ranker.rank(shows, profile, meter=final_meter), meter=final_meter)
    for p in picks:
        say(f"    #{p['rank']} {p['artist'][:30]:32} {p['date']} @ "
            f"{(p['venue'] or 'TBA')[:20]}")
        say(f"       why        {p['why'][:70]}")
        flags = [u['claim'][:34] for u in p['unsupported']] + p['listing_problems']
        say(f"       verified   {p['verified']} · confidence {p['confidence']}"
            + (f" · flagged: {flags}" if flags else ""))

    say("\n" + "=" * 66)
    say(f"TOTAL  {round(time.time() - started, 1)}s · {spend(meter)}")

    out = config.DATA_DIR / "trace.txt"
    out.write_text("\n".join(LINES), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
