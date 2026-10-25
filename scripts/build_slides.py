"""Build slides.html -- self-contained reveal.js deck, 10 slides.

reveal.js and the screenshots are inlined so the file opens by double-click
with no network. Regenerate after new measurements:

    python scripts/build_slides.py
"""
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"
VENDOR = ROOT / "vendor"

APP_URL = "https://encore-8pjj.onrender.com"
REPO_URL = "github.com/priya-julian/encore"


def font_face() -> str:
    """Inline the display face so the deck needs no network at all."""
    path = VENDOR / "bebas.woff2"
    if not path.is_file():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode()
    return (
        "@font-face{font-family:'Bebas Neue';font-style:normal;font-weight:400;"
        f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
    )


def data_uri(name: str) -> str:
    path = ASSETS / name
    if not path.is_file():
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()


def build() -> str:
    t = json.loads((ROOT / "data" / "tokenomics.json").read_text())
    from encore import events
    from encore.diagram import SVG

    impact = (events.summary(events.LIVE_PATH)
              if events.LIVE_PATH.is_file() else events.summary())

    cold, warm, scale = t["cold"], t["warm"], t["scale"]
    reveal_css = (VENDOR / "reveal.css").read_text()
    face = font_face()
    theme_css = (VENDOR / "white.css").read_text()
    reveal_js = (VENDOR / "reveal.js").read_text()

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Encore — MGT 409</title>
<style>{reveal_css}</style>
<style>{theme_css}</style>
<style>
  {face}
  :root {{ --blue:#8b3dff; --hot:#ff3d9a; --dark:#1a0b2e; --deep:#4c1d95;
           --dim:#6b5b85; --line:#e6dcf7; --soft:#f7f2ff; }}
  .reveal {{ font-family:ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
             font-size:30px; color:#1b1230; }}
  .reveal h1,.reveal h2,.reveal h3 {{ color:var(--dark); text-transform:none;
             font-family:"Bebas Neue",Impact,sans-serif; font-weight:400;
             letter-spacing:1.2px; }}
  .reveal h1 {{ font-size:2.6em; }}
  .reveal h2 {{ font-size:1.7em; margin-bottom:.35em; }}
  .reveal h2::after {{ content:""; display:block; width:74px; height:4px;
             margin-top:10px; border-radius:2px;
             background:linear-gradient(90deg,var(--hot),var(--blue)); }}
  .reveal section {{ text-align:left; }}
  .reveal .center {{ text-align:center; }}
  .reveal p.lead {{ color:var(--dim); font-size:.8em; margin-top:0; }}
  .reveal ul {{ font-size:.78em; }}
  .reveal li {{ margin-bottom:.35em; }}
  .reveal strong {{ color:var(--deep); }}
  .kpis {{ display:flex; gap:18px; margin:.5em 0; }}
  .kpi {{ flex:1; background:var(--soft); border:1px solid var(--line);
          border-radius:14px; padding:18px 10px; text-align:center; }}
  .kpi b {{ display:block; font-size:1.7em; color:var(--dark);
            font-family:"Bebas Neue",Impact,sans-serif; letter-spacing:.5px; }}
  .kpi span {{ font-size:.46em; color:var(--dim); }}
  .reveal table {{ font-size:.58em; width:100%; }}
  .reveal th {{ background:var(--soft); color:var(--deep); }}
  .reveal td, .reveal th {{ padding:7px 10px; }}
  .n {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .shot {{ border:1px solid var(--line); border-radius:12px; max-height:60vh;
           box-shadow:0 6px 26px rgba(76,29,149,.16); }}
  .quote {{ background:var(--soft); border-left:4px solid var(--hot);
            padding:14px 22px; font-size:.68em; font-style:italic; }}
  .pass {{ color:#5ee6a0; font-weight:700; }}
  .mono {{ font-family:ui-monospace,Menlo,monospace; font-size:.62em;
           background:var(--dark); color:#e4d9fb; padding:14px 18px;
           border-radius:10px; white-space:pre; }}
  .foot {{ position:absolute; bottom:-10px; left:0; font-size:.4em;
           color:var(--dim); }}
  .two {{ display:flex; gap:26px; align-items:flex-start; }}
  .two > div {{ flex:1; }}
  .cap {{ font-size:.5em; line-height:1.6; color:#413355; margin-top:.3em; }}
  .diagwrap {{ text-align:center; }}
  .diagwrap svg {{ width:760px; height:330px; max-width:100%; }}
  .diagwrap .t {{ font:12px ui-sans-serif,system-ui,sans-serif; fill:#1b1230;
                  text-anchor:middle; }}
  .diagwrap .b {{ font-weight:700; }}
  .diagwrap .s {{ font-size:10.5px; fill:#6b5b85; }}
  .diagwrap .w {{ fill:#fff; }}
  .links {{ display:inline-block; text-align:left; background:var(--soft);
            border:1px solid var(--line); border-radius:12px;
            padding:13px 20px; font-size:.5em; line-height:1.75; }}
  .links b {{ display:inline-block; min-width:86px; color:var(--deep); }}
  .links a {{ color:var(--blue); }}
  .pub {{ background:var(--blue); color:#fff; border-radius:99px;
          padding:1px 9px; font-size:.82em; margin-left:6px; }}
</style></head>
<body>
<noscript>
  <div style="max-width:620px;margin:60px auto;padding:22px 26px;
              border:1px solid #e6dcf7;border-radius:14px;background:#f7f2ff;
              font:16px/1.6 ui-sans-serif,system-ui,sans-serif;color:#1b1230">
    <b>This deck needs JavaScript.</b> It is a reveal.js presentation and the
    slides stay hidden until the script runs. Open <code>slides.html</code> in
    a normal browser window (double-click it) and they will appear. Use the
    arrow keys to move between the ten slides.
  </div>
</noscript>
<div class="reveal"><div class="slides">

<section class="center">
  <h1>Encore</h1>
  <p class="lead">Rank the concerts you've been to;<br>
  Encore tells you which upcoming shows you'd regret missing.</p>
  <p style="font-size:.52em;color:#6b5b85;margin-bottom:.2em">
    Priya Julian · MGT 409 · Fall 2026
  </p>
  <div class="links">
    <div><b>Repo</b> <a href="https://{REPO_URL}">https://{REPO_URL}</a>
      <span class="pub">public</span></div>
    <div><b>Live app</b> <a href="{APP_URL}">{APP_URL}</a></div>
  </div>
</section>

<section>
  <h2>The problem</h2>
  <div class="kpis">
    <div class="kpi"><b>{cold["shows_considered"]}</b><span>shows in the next six weeks</span></div>
    <div class="kpi"><b>25</b><span>Austin venues</span></div>
    <div class="kpi"><b>~35 min</b><span>per week to check them by hand</span></div>
  </div>
  <ul>
    <li>Austin's abundance is the problem, not the feature.</li>
    <li>You find out about the show you'd have loved <strong>after it
        happens</strong>.</li>
    <li>Instagram shows you paid promotion. Spotify only knows artists
        <strong>already in your library</strong>. Ticketmaster ranks by sales.</li>
    <li>None of them know you found Moody Center too big.</li>
  </ul>
</section>

<section>
  <h2>What's new</h2>
  <p class="lead">Letterboxd, Goodreads and Beli are social networks with a
  rating primitive. Encore inverts that.</p>
  <ul>
    <li><strong>The log is the input to an agent</strong>, not content for a
        feed. No followers, no aggregate score.</li>
    <li><strong>Useful with one user on day one</strong> — signal comes from
        your history, not a crowd.</li>
    <li><strong>Reads the whole city</strong>, including openers and local
        acts you've never streamed.</li>
    <li><strong>Negative signal is first-class</strong> — four <em>meh</em>
        ratings become an explicit "avoids" list.</li>
  </ul>
</section>

<section>
  <h2>Five agents</h2>
  <div class="diagwrap">{SVG}</div>
  <p class="cap"><strong>Scout</strong> structures the listings ·
  <strong>Profiler</strong> reads your log · <strong>Scholar</strong>
  researches unknowns (Bandcamp, MusicBrainz, Wikipedia) ·
  <strong>Ranker</strong> screens {cold["shows_considered"]} &#8594; 14 &#8594; 5 ·
  <strong>Verifier</strong> fact-checks every pick.
  Ordered <strong>cheap to expensive</strong>, so research runs on 14 shows,
  not {cold["shows_considered"]}.</p>
</section>

<section>
  <h2>It works</h2>
  <div class="two">
    <div><img class="shot" src="{data_uri("discover.jpg")}" alt="Discover screen"></div>
    <div>
      <div class="quote">"You like emotionally direct indie songwriting, and
      Julia Jacklin's intimate indie-folk connects with the Angel Olsen and
      Waxahatchee lane in your taste."</div>
      <p style="font-size:.6em;margin-top:.8em">Reasons cite <strong>specific
      bands from the log</strong>, not genre keywords. Picks carry the
      Verifier's judgement — shown, not hidden.</p>
    </div>
  </div>
</section>

<section>
  <h2>Cost</h2>
  <div class="kpis">
    <div class="kpi"><b>${cold["cost_usd"]:.4f}</b><span>cold run</span></div>
    <div class="kpi"><b>${warm["cost_usd"]:.4f}</b><span>warm run</span></div>
    <div class="kpi"><b>{cold["seconds"]}s → {warm["seconds"]}s</b><span>latency</span></div>
  </div>
  <table>
    <tr><th>Users</th><th class="n">Shared / mo</th><th class="n">Per user / mo</th>
        <th class="n">Total / mo</th></tr>
    <tr><td>1</td><td class="n">${scale["1"]["shared_monthly_usd"]:.2f}</td>
        <td class="n">${scale["1"]["per_user_monthly_usd"]:.3f}</td>
        <td class="n">${scale["1"]["total_monthly_usd"]:.2f}</td></tr>
    <tr><td>100</td><td class="n">${scale["100"]["shared_monthly_usd"]:.2f}</td>
        <td class="n">${scale["100"]["per_user_monthly_usd"]:.3f}</td>
        <td class="n">${scale["100"]["total_monthly_usd"]:.2f}</td></tr>
    <tr><td>10,000</td><td class="n">${scale["10000"]["shared_monthly_usd"]:.2f}</td>
        <td class="n">${scale["10000"]["per_user_monthly_usd"]:.3f}</td>
        <td class="n">${scale["10000"]["total_monthly_usd"]:.2f}</td></tr>
  </table>
  <p style="font-size:.58em">Listings and artist research are <strong>shared
  across every user in a city</strong>, so cost per user falls as it
  scales — about ten cents a month at 10,000.</p>
</section>

<section>
  <h2>Safety: we found a real one</h2>
  <p class="lead">A planted jailbreak tripped the <em>provider's</em> content
  filter, which rejected the whole batch — silently returning
  <strong>zero shows for that day</strong>. An attacker could erase a day of
  Austin music without ever reaching the model.</p>
  <div class="mono">DEFENCE 1a: blatant jailbreak in a venue listing
  injection_suspected : True
  shows extracted     : 2  (Alvvays, Being Dead)
  <span class="pass">[PASS]</span> real shows survived — quarantine isolates the bad listing</div>
  <p style="font-size:.58em;margin-top:.5em">Fix: filtered batches retry one
  listing at a time. <strong>4/4 defences pass</strong> —
  <span class="mono" style="background:none;color:#16233a;padding:0">python safety/demo.py</span></p>
</section>

<section>
  <h2>Safety: nothing unchecked reaches you</h2>
  <div class="mono">under test: "Being Dead's Grammy-winning sound, fresh off
            their Sub Pop signing, sounds like Big Thief"
research:   genre Experimental | Austin, Texas | sounds like: (none)

flagged: "Grammy-winning sound"        -> no awards in research
flagged: "fresh off a Sub Pop signing" -> no label in research
flagged: "sounds like Big Thief"       -> no such comparison
confidence downgraded: high -> medium</div>
  <ul style="font-size:.68em;margin-top:.5em">
    <li>Deterministic source-tracing costs <strong>no tokens</strong> and
        can't be argued with.</li>
    <li>Flagged picks are <strong>labelled, not dropped</strong>.</li>
    <li>Four venues block bots — we <strong>honour the 403</strong> rather
        than working around it.</li>
  </ul>
</section>

<section>
  <h2>Impact</h2>
  <div class="kpis">
    <div class="kpi"><b>{impact["sessions"]}</b><span>people</span></div>
    <div class="kpi"><b>{impact["runs"]}</b><span>runs</span></div>
    <div class="kpi"><b>{impact["new_to_me"]}</b><span>"didn't know this"</span></div>
    <div class="kpi"><b>{impact["saved"]}</b><span>saved</span></div>
  </div>
  <div class="quote">The first run against my real log returned Adrianne
  Lenker at ACL Live. I had independently been considering that show and had
  never told the system — it was chosen from {cold["shows_considered"]}
  candidates on the strength of 31 rated concerts.</div>
</section>

<section>
  <h2>Limits &amp; next</h2>
  <ul>
    <li><strong>One city, one source.</strong> A second city is a day's work,
        not a rewrite.</li>
    <li><strong>Thin on very small artists</strong> — Scholar says so rather
        than guessing. Reading the Bandcamp artist page closes most of it.</li>
    <li><strong>Entering the log is the barrier.</strong> Importing from
        ticket emails is the highest-value next feature.</li>
    <li><strong>"Not for me" isn't fed back yet</strong> — the most direct
        path to picks that improve over time.</li>
    <li><strong>Travel mode:</strong> "I'm in Chicago Nov 14–17, what's on?"
        is the same pipeline, different window.</li>
  </ul>
  <div class="links" style="margin-top:.5em">
    <div><b>Repo</b> <a href="https://{REPO_URL}">https://{REPO_URL}</a>
      <span class="pub">public</span></div>
    <div><b>Live app</b> <a href="{APP_URL}">{APP_URL}</a></div>
  </div>
</section>

</div></div>
<script>{reveal_js}</script>
<script>
  // No hash routing: it drives history.replaceState, which some browsers
  // refuse on a file:// URL, and a throw there would leave the deck blank
  // for anyone who opened the file by double-clicking it.
  Reveal.initialize({{hash:false, slideNumber:'c/t', transition:'fade',
    width:1100, height:700, margin:0.06}});
</script>
</body></html>
"""


if __name__ == "__main__":
    out = ROOT / "slides.html"
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB, 10 slides, "
          "reveal.js inlined)")
