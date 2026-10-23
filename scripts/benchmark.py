"""Measure Encore's real token use and cost, for the report's tokenomics.

Runs a genuinely cold pipeline (cache cleared), then a warm one, and writes
the measurements to data/tokenomics.json so the report quotes numbers that
were actually observed rather than estimated.

Run:  python scripts/benchmark.py
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from encore import config, llm, log, pipeline, pricing  # noqa: E402
from encore.agents import profiler, ranker, verifier  # noqa: E402

# A user who opens the app, looks at their picks, and comes back later.
RUNS_PER_USER_PER_MONTH = 8


def cost_of(totals: dict) -> float:
    return pricing.cost_usd(config.MODEL, totals["prompt_tokens"],
                            totals["completion_tokens"])


def full_run(force_sweep: bool) -> dict:
    meter = llm.Meter()
    started = time.time()
    rows = log.read()
    profile = profiler.build(rows, meter=meter)
    swept = pipeline.sweep(meter=meter, force=force_sweep)
    picks = verifier.verify_all(
        ranker.rank(swept["shows"], profile, meter=meter), meter=meter
    )
    totals = meter.totals()
    return {
        "seconds": round(time.time() - started, 1),
        "shows_considered": len(swept["shows"]),
        "picks": len(picks),
        "tokens_in": totals["prompt_tokens"],
        "tokens_out": totals["completion_tokens"],
        "model_calls": totals["calls"],
        "cache_hits": totals["cache_hits"],
        "cost_usd": round(cost_of(totals), 6),
        "by_agent": totals["by_agent"],
    }


def main():
    config.load_env()
    cache = config.CACHE_DIR

    print("clearing cache for a genuinely cold run...")
    shutil.rmtree(cache, ignore_errors=True)

    print("cold run (nothing cached)...")
    cold = full_run(force_sweep=True)
    print(f"  {cold['seconds']}s  ${cold['cost_usd']:.4f}  "
          f"{cold['tokens_in']}in/{cold['tokens_out']}out")

    print("warm run (everything cached)...")
    warm = full_run(force_sweep=False)
    print(f"  {warm['seconds']}s  ${warm['cost_usd']:.4f}")

    # A second user in Austin shares the listing sweep and most artist
    # research, so they pay only for their own screening and ranking.
    shared = cold["cost_usd"] - warm["cost_usd"]
    marginal = warm["cost_usd"] if warm["cost_usd"] > 0 else 0.0
    per_user_month = marginal * RUNS_PER_USER_PER_MONTH

    scale = {}
    for users in (1, 100, 10_000):
        # One shared cold sweep per day, plus each user's own runs.
        monthly_shared = shared * 30
        scale[str(users)] = {
            "users": users,
            "shared_monthly_usd": round(monthly_shared, 2),
            "per_user_monthly_usd": round(per_user_month, 4),
            "total_monthly_usd": round(monthly_shared + per_user_month * users, 2),
        }

    payload = {
        "model": config.MODEL,
        "rate_card_usd_per_1m": pricing.RATE_CARD[config.MODEL],
        "measured_at": time.strftime("%Y-%m-%d %H:%M"),
        "runs_per_user_per_month": RUNS_PER_USER_PER_MONTH,
        "cold": cold,
        "warm": warm,
        "shared_cost_usd": round(shared, 6),
        "scale": scale,
    }
    out = config.DATA_DIR / "tokenomics.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {out}")
    for k, v in scale.items():
        print(f"  {k:>6} users: ${v['total_monthly_usd']}/month")


if __name__ == "__main__":
    main()
