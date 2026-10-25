"""Did the cost cutting hurt the picks?

The biggest saving in Encore is screening every show cheaply and paying for
research only on a short shortlist. That is only a good trade if widening the
shortlist would not have changed the answer. This measures exactly that:
the same run at the production shortlist of 14, and at 40.

Run:  python scripts/quality_check.py
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from encore import config, llm, log, pipeline, pricing  # noqa: E402
from encore.agents import profiler, ranker  # noqa: E402


def run(shortlist: int, shows, profile) -> dict:
    meter = llm.Meter()
    started = time.time()
    picks = ranker.rank(shows, profile, meter=meter, shortlist=shortlist)
    totals = meter.totals()
    return {
        "shortlist": shortlist,
        "picks": [p["artist"] for p in picks],
        "seconds": round(time.time() - started, 1),
        "cost_usd": round(pricing.cost_usd(config.MODEL, totals["prompt_tokens"],
                                           totals["completion_tokens"]), 5),
    }


def main():
    config.load_env()
    rows = log.read(log.OWNER_LOG)
    meter = llm.Meter()
    profile = profiler.build(rows, meter=meter)
    shows = pipeline.sweep(meter=meter)["shows"]
    print(f"{len(shows)} shows considered\n")

    results = [run(14, shows, profile), run(40, shows, profile)]
    for r in results:
        print(f"shortlist {r['shortlist']:>2}: ${r['cost_usd']:.5f}  "
              f"{r['seconds']:>5}s")
        for i, a in enumerate(r["picks"], 1):
            print(f"      {i}. {a}")
        print()

    a, b = (set(r["picks"]) for r in results)
    overlap = len(a & b)
    extra = results[1]["cost_usd"] - results[0]["cost_usd"]
    print(f"overlap: {overlap}/5 picks identical")
    print(f"researching 40 instead of 14 costs "
          f"${extra:.5f} more per run "
          f"({results[1]['cost_usd'] / max(results[0]['cost_usd'], 1e-9):.1f}x)")

    out = config.DATA_DIR / "quality_check.json"
    out.write_text(json.dumps({
        "measured_at": time.strftime("%Y-%m-%d %H:%M"),
        "shows_considered": len(shows),
        "results": results,
        "overlap": overlap,
        "extra_cost_usd": round(extra, 5),
    }, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
