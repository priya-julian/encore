# Encore

**Live app: <https://encore-8pjj.onrender.com>**

Rank the concerts you've been to; Encore reads every Austin venue calendar and
tells you which upcoming shows you'd regret missing.

Five agents: **Scout** gathers listings, **Profiler** learns your taste from
your own show history, **Scholar** researches artists you may not know,
**Ranker** screens and ranks, **Verifier** fact-checks every pick before you
see it.

## Setup

1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. Put `PORTKEY_API_KEY=...` in a `.env` file, either in this folder or one
   level above it. See `.env.example`.
5. `python app.py`
6. Open <http://localhost:5000>

On macOS, port 5000 is often taken by the AirPlay Receiver. If the app will
not start, either turn that off in System Settings > General > AirDrop &
Handoff, or run `PORT=5001 python app.py` and use <http://localhost:5001>.

## Data and how to switch datasets

Encore ships with two small datasets so it works immediately on a fresh
clone, and every log is a plain CSV with the same columns:

| File | What it is |
|---|---|
| `data/concert_log.csv` | 31 real Austin concerts. This is the **demo log**, loaded by the "Load the demo log" button on the My shows screen. |
| `data/sample_log.csv` | A 27-show sample, used as a fallback if the demo log is missing. |
| `data/logs/<id>.csv` | Written automatically, one per visitor. Not in the repo. |

Columns: `artist, date, venue, city, openers, gut_rating, notes`.
Dates can be rough — `2024-05`, `2022 fall`, or blank. `gut_rating` is
`loved`, `liked`, `fine` or `meh` (defaults to `liked`). `notes` is the
strongest taste signal: one line on why a show landed is worth more than a
precise date.

**To use your own data**, pick whichever is easier:

1. **In the app** — go to My shows and paste bands you've seen, one per line,
   with an optional `- loved` / `- meh`. This writes `data/logs/<id>.csv` and
   leaves the shipped files alone.
2. **Replace the demo log** — overwrite `data/concert_log.csv` with your own
   CSV, keeping the header row and column names. The "Load the demo log"
   button then loads yours.
3. **Point at a different file** — the paths are the three constants at the
   top of `encore/log.py` (`USER_LOGS`, `OWNER_LOG`, `SAMPLE_LOG`). Change
   `OWNER_LOG` to read a CSV from anywhere.

A larger dataset needs no code change — the Profiler reads whatever rows the
CSV has. Logs beyond a few hundred shows will cost more per profile run, and
the profile is cached on a hash of the log, so it is rebuilt only when the
file changes.

**To use a different city**, replace the venue metadata in
`encore/venues.py` and point `encore/agents/showlist.py` at that city's
listing source. Nothing else in the app is Austin-specific.

## Safety demos

    python safety/demo.py

Runs four live checks: a blatant prompt injection planted in a venue listing,
a subtler one that clears the provider's content filter, a fabricated
recommendation claim, and a deterministic source-tracing check. Exits non-zero
if any defence fails.

## Caching

First run reads every listing and costs about $0.013. Results are cached in
`cache/`, so later runs are near-instant and free. Delete `cache/` or press
**Re-run** in the app to force a fresh sweep.
