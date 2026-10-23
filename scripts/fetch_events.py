"""Pull usage events down from the deployed app.

Render's free tier wipes the filesystem when the service sleeps or
redeploys, so impact data has to be fetched before that happens. Run this
after a testing round and before rebuilding the report:

    python scripts/fetch_events.py
    python scripts/build_report.py

Events already saved locally are kept, so running it repeatedly accumulates
rather than overwrites.
"""
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from encore import config  # noqa: E402

APP_URL = "https://encore-8pjj.onrender.com"
OUT = config.DATA_DIR / "events_live.jsonl"


def mark_baseline() -> int:
    """Record 'everything up to now is developer testing'."""
    import time

    from encore import events

    events.BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    events.BASELINE_PATH.write_text(json.dumps({"ts": now}))
    print(f"baseline set: events before {time.strftime('%Y-%m-%d %H:%M')} "
          "will not count as real usage")
    return 0


def main() -> int:
    try:
        resp = requests.get(f"{APP_URL}/api/events.jsonl", timeout=180)
    except requests.RequestException as exc:
        print(f"could not reach the app: {exc}")
        return 1
    if resp.status_code != 200:
        print(f"app returned HTTP {resp.status_code}")
        return 1

    def parse(text: str) -> list[dict]:
        out = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    existing = parse(OUT.read_text(encoding="utf-8")) if OUT.is_file() else []
    fetched = parse(resp.text)

    # Events carry no id, so dedupe on their full content.
    seen = {json.dumps(r, sort_keys=True) for r in existing}
    added = [r for r in fetched
             if json.dumps(r, sort_keys=True) not in seen]

    merged = existing + added
    merged.sort(key=lambda r: r.get("ts", 0))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r) + "\n" for r in merged), encoding="utf-8")

    sessions = len({r.get("session") for r in merged if r.get("session")})
    print(f"fetched {len(fetched)}, new {len(added)}, total {len(merged)} "
          f"events from {sessions} sessions -> {OUT}")
    return 0


if __name__ == "__main__":
    if "--mark-baseline" in sys.argv:
        raise SystemExit(mark_baseline())
    raise SystemExit(main())
