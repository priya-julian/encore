"""Warm the listing cache at build time.

Render's filesystem is rebuilt on every deploy, so without this the first
visitor after a deploy pays a full cold sweep -- about a minute of waiting.
Running it here means the cache is already warm when the service starts.

Never fails the build: a cold cache is a slow app, not a broken one.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from encore import config  # noqa: E402


def main() -> int:
    config.load_env()
    try:
        config.api_key()
    except RuntimeError:
        print("warm_cache: no PORTKEY_API_KEY at build time, skipping")
        return 0

    from encore import service

    try:
        result = service.get_picks()
    except Exception as exc:  # noqa: BLE001 - never break the build
        print(f"warm_cache: skipped ({type(exc).__name__}: {exc})")
        return 0

    if result.get("error"):
        print(f"warm_cache: {result['error']}")
        return 0
    print(f"warm_cache: {result.get('considered', 0)} shows cached, "
          f"{len(result.get('picks', []))} picks, "
          f"${result.get('cost', 0):.4f}, {result.get('seconds', 0)}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
