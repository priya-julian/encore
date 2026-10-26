"""Pull the latest usage, rebuild both deliverables, and check them over.

Run this immediately before submitting:

    python scripts/finalize.py

It fetches events from the deployed app, regenerates report.html and
slides.html from measured data, and audits both against the project
requirements so nothing is submitted on an assumption.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PY_BIN = str(ROOT / ".venv" / "bin" / "python")


def run(label: str, *args: str) -> bool:
    print(f"\n--- {label} ---")
    done = subprocess.run([PY_BIN, *args], cwd=ROOT,
                          capture_output=True, text=True)
    out = (done.stdout + done.stderr).strip()
    if out:
        print("  " + out.replace("\n", "\n  "))
    return done.returncode == 0


def audit() -> list[tuple[bool, str]]:
    from encore import events

    checks: list[tuple[bool, str]] = []
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT,
                             capture_output=True, text=True).stdout.split()
    checks.append((".env" not in tracked
                   and not any(t.endswith("/.env") for t in tracked),
                   "no real .env committed"))

    envex = (ROOT / ".env.example").read_text()
    checks.append(("PORTKEY_API_KEY" in envex
                   and not re.search(r"PORTKEY_API_KEY=\S", envex),
                   ".env.example has key names, no values"))

    for name in ("report.html", "slides.html"):
        html = (ROOT / name).read_text()
        remote = [u for u in re.findall(r'(?:src|href)="([^"]+)"', html)
                  if not u.startswith(("data:", "#"))
                  and re.search(r"\.(css|js|jpg|png|svg|woff2?)$", u)]
        checks.append((not remote, f"{name} is self-contained"))
        checks.append(("github.com/priya-julian/encore" in html,
                       f"{name} carries the repo URL"))

    slides = (ROOT / "slides.html").read_text()
    n = slides.count("<section")
    checks.append((n <= 10, f"slides.html has {n} slides (max 10)"))

    words = len(re.sub(r"<[^>]+>", " ",
                       (ROOT / "report.html").read_text()).split())
    checks.append((words > 2800, f"report is substantial ({words} words)"))

    clean = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    checks.append((not clean, "working tree clean / everything pushed"))

    quotes = ROOT / "data" / "quotes.json"
    checks.append((quotes.is_file(),
                   "tester quote collected (data/quotes.json) — "
                   "the impact row's named evidence"))

    stats = events.summary(events.LIVE_PATH)
    checks.append((stats["sessions"] > 0,
                   f"real usage recorded ({stats['sessions']} people, "
                   f"{stats['runs']} runs)"))
    return checks


def main() -> int:
    print("=" * 62)
    print("  FINALISE — fetch usage, rebuild deliverables, audit")
    print("=" * 62)

    run("pulling usage from the deployed app", "scripts/fetch_events.py")
    run("rebuilding report.html", "scripts/build_report.py")
    run("rebuilding slides.html", "scripts/build_slides.py")

    print("\n--- audit ---")
    results = audit()
    for passed, label in results:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")

    failed = [l for ok, l in results if not ok]
    print("\n" + "=" * 62)
    if failed:
        print(f"  {len(failed)} issue(s) to fix before submitting:")
        for label in failed:
            print(f"    - {label}")
    else:
        print("  Ready to submit. Upload to Canvas, nothing else:")
        print("    report.html")
        print("    slides.html")
    print("=" * 62)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
