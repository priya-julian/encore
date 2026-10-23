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

## Data

- `data/concert_log.csv` — your own shows. Encore uses this as soon as it has
  rows.
- `data/sample_log.csv` — a 27-show sample, used when your log is empty, so
  the app works on a fresh clone.

Columns: `artist, date, venue, city, openers, gut_rating, notes`. Dates can be
rough (`2024-05`, `2022 fall`). `gut_rating` is `loved`, `liked`, `fine` or
`meh`. The `notes` column is the strongest taste signal — one line on why a
show landed is worth more than a precise date.

To use a different city, replace the venue metadata in `encore/venues.py` and
point `encore/agents/showlist.py` at that city's listing source. Nothing else
in the app is Austin-specific.

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
