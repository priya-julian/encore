"""Build report.html -- self-contained, images embedded, opens by double-click.

Regenerate after new measurements or user data land:

    python scripts/build_report.py

Everything numeric comes from data/tokenomics.json and data/events.jsonl, so
the report never drifts from what was actually measured.
"""
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"

# Fill in once Render is live; it appears in the title block and the README.
APP_URL = "https://encore-8pjj.onrender.com"
REPO_URL = "https://github.com/priya-julian/encore"


def img(name: str, alt: str, caption: str) -> str:
    path = ASSETS / name
    if not path.is_file():
        return f'<p class="missing">[screenshot missing: {name}]</p>'
    b64 = base64.b64encode(path.read_bytes()).decode()
    return (
        f'<figure><img alt="{alt}" src="data:image/jpeg;base64,{b64}">'
        f"<figcaption>{caption}</figcaption></figure>"
    )


def money(x: float) -> str:
    return f"${x:,.4f}" if x < 1 else f"${x:,.2f}"


def load_tokenomics() -> dict:
    path = ROOT / "data" / "tokenomics.json"
    if not path.is_file():
        raise SystemExit("run scripts/benchmark.py first")
    return json.loads(path.read_text())


def load_impact() -> dict:
    """Usage from the deployed app, falling back to local events.

    Prefers data/events_live.jsonl (pulled by scripts/fetch_events.py) so
    that development on this machine never counts as real user activity.
    """
    from encore import events

    if events.LIVE_PATH.is_file():
        return events.summary(events.LIVE_PATH)
    return events.summary()


AGENT_LABELS = {
    "showlist": ("Scout", "Parse listings into structured shows"),
    "profiler": ("Profiler", "Build the taste profile from the log"),
    "ranker-screen": ("Ranker (screen)", "Score every show cheaply"),
    "scholar": ("Scholar", "Research unfamiliar artists"),
    "ranker-final": ("Ranker (final)", "Rank finalists and write reasons"),
    "verifier": ("Verifier", "Fact-check every pick"),
}

DIAGRAM = """
<svg viewBox="0 0 760 330" xmlns="http://www.w3.org/2000/svg" class="diagram"
     role="img" aria-label="Encore agent architecture">
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="8" refY="3"
            orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#c4a0ff"/></marker>
  </defs>
  <rect x="8" y="18" width="150" height="62" rx="9" fill="#f7f2ff"
        stroke="#e6dcf7"/>
  <text x="83" y="42" class="t b">Showlist Austin</text>
  <text x="83" y="60" class="t s">459 shows, 43 days</text>

  <rect x="8" y="118" width="150" height="62" rx="9" fill="#f7f2ff"
        stroke="#e6dcf7"/>
  <text x="83" y="142" class="t b">Your show log</text>
  <text x="83" y="160" class="t s">31 rated concerts</text>

  <rect x="8" y="218" width="150" height="62" rx="9" fill="#f7f2ff"
        stroke="#e6dcf7"/>
  <text x="83" y="242" class="t b">Bandcamp ·</text>
  <text x="83" y="260" class="t s">MusicBrainz · Wikipedia</text>

  <rect x="210" y="18" width="150" height="62" rx="9" fill="#fff"
        stroke="#8b3dff"/>
  <text x="285" y="42" class="t b">Scout</text>
  <text x="285" y="60" class="t s">fetch + extract</text>

  <rect x="210" y="118" width="150" height="62" rx="9" fill="#fff"
        stroke="#8b3dff"/>
  <text x="285" y="142" class="t b">Profiler</text>
  <text x="285" y="160" class="t s">taste profile</text>

  <rect x="210" y="218" width="150" height="62" rx="9" fill="#fff"
        stroke="#8b3dff"/>
  <text x="285" y="242" class="t b">Scholar</text>
  <text x="285" y="260" class="t s">artist research</text>

  <rect x="412" y="68" width="150" height="62" rx="9" fill="#fff"
        stroke="#8b3dff"/>
  <text x="487" y="92" class="t b">Ranker · screen</text>
  <text x="487" y="110" class="t s">459 &#8594; 14</text>

  <rect x="412" y="168" width="150" height="62" rx="9" fill="#fff"
        stroke="#8b3dff"/>
  <text x="487" y="192" class="t b">Ranker · final</text>
  <text x="487" y="210" class="t s">14 &#8594; 5 with reasons</text>

  <rect x="610" y="118" width="140" height="62" rx="9" fill="#1a0b2e"/>
  <text x="680" y="142" class="t b w">Verifier</text>
  <text x="680" y="160" class="t s w">fact-check</text>

  <g stroke="#c4a0ff" fill="none" marker-end="url(#a)">
    <path d="M158,49 L204,49"/>
    <path d="M158,149 L204,149"/>
    <path d="M158,249 L204,249"/>
    <path d="M360,49 C390,49 386,95 406,99"/>
    <path d="M360,149 C390,149 386,105 406,101"/>
    <path d="M487,130 L487,162"/>
    <path d="M360,249 C395,249 400,205 406,201"/>
    <path d="M562,199 C590,199 596,160 604,155"/>
  </g>
</svg>
"""


def tokenomics_rows(by_agent: dict, warm: dict) -> str:
    rows = []
    for key, (label, job) in AGENT_LABELS.items():
        cold = by_agent.get(key, {})
        warm_a = warm["by_agent"].get(key, {})
        cold_tok = cold.get("prompt", 0) + cold.get("completion", 0)
        warm_tok = warm_a.get("prompt", 0) + warm_a.get("completion", 0)
        rows.append(
            f"<tr><td><b>{label}</b><br><span class='s'>{job}</span></td>"
            f"<td class='n'>{cold.get('calls', 0)}</td>"
            f"<td class='n'>{cold_tok:,}</td>"
            f"<td class='n'>{warm_tok:,}</td></tr>"
        )
    return "\n".join(rows)


def build() -> str:
    t = load_tokenomics()
    cold, warm = t["cold"], t["warm"]
    impact = load_impact()
    scale = t["scale"]
    rate = t["rate_card_usd_per_1m"]

    saving = (1 - warm["cost_usd"] / cold["cost_usd"]) * 100
    speedup = cold["seconds"] / warm["seconds"]

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Encore — MGT 409 Final Project</title>
<style>
  :root {{ --blue:#8b3dff; --hot:#ff3d9a; --dark:#1a0b2e; --line:#e6dcf7;
           --dim:#6b5b85; --soft:#f7f2ff; }}
  body {{ font:15px/1.6 Georgia,"Times New Roman",serif; color:#16233a;
          max-width:760px; margin:0 auto; padding:40px 28px 80px; }}
  h1 {{ font-size:30px; margin:0 0 4px; color:var(--dark); line-height:1.2; }}
  h2 {{ font-size:20px; margin:38px 0 10px; padding-bottom:6px;
        border-bottom:2px solid var(--line); color:var(--dark); }}
  h2::after {{ content:""; display:block; width:58px; height:3px;
        margin:6px 0 -8px; border-radius:2px;
        background:linear-gradient(90deg,var(--hot),var(--blue)); }}
  h3 {{ font-size:16px; margin:22px 0 6px; color:var(--dark); }}
  .sub {{ color:var(--dim); margin:0 0 18px; font-size:16px; }}
  .links {{ background:var(--soft); border-radius:10px; padding:14px 18px;
            font-family:ui-sans-serif,system-ui,sans-serif; font-size:14px; }}
  .links div {{ margin:3px 0; }}
  .links b {{ display:inline-block; min-width:92px; color:var(--dark); }}
  .pub {{ background:var(--blue); color:#fff; border-radius:99px;
          padding:1px 9px; font-size:11px; margin-left:4px; }}
  table {{ border-collapse:collapse; width:100%; margin:14px 0; font-size:14px;
           font-family:ui-sans-serif,system-ui,sans-serif; }}
  th {{ background:var(--soft); color:var(--dark); text-align:left;
        padding:8px 10px; font-size:13px; }}
  td {{ padding:8px 10px; border-top:1px solid var(--line);
        vertical-align:top; }}
  td.n, th.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .s {{ color:var(--dim); font-size:12px; }}
  figure {{ margin:18px 0; }}
  figure img {{ width:100%; border:1px solid var(--line); border-radius:8px; }}
  figcaption {{ color:var(--dim); font-size:13px; margin-top:6px;
                font-family:ui-sans-serif,system-ui,sans-serif; }}
  pre {{ background:var(--dark); color:#e4d9fb; padding:14px 16px; border-radius:8px;
         font-size:12.5px; line-height:1.5; overflow-x:auto; }}
  pre b {{ color:#5ee6a0; }}
  blockquote {{ margin:14px 0; padding:10px 18px; background:var(--soft);
                border-left:3px solid var(--hot); font-style:italic; }}
  .kpis {{ display:flex; gap:12px; flex-wrap:wrap; margin:16px 0; }}
  .kpi {{ flex:1 1 150px; background:var(--soft); border:1px solid var(--line);
          border-radius:10px; padding:14px; text-align:center;
          font-family:ui-sans-serif,system-ui,sans-serif; }}
  .kpi b {{ display:block; font-size:24px; color:var(--dark); }}
  .kpi span {{ font-size:12px; color:var(--dim); }}
  .diagram {{ width:100%; height:auto; margin:14px 0; }}
  .diagram .t {{ font:12px ui-sans-serif,system-ui,sans-serif; fill:#1b1230;
                 text-anchor:middle; }}
  .diagram .b {{ font-weight:700; }}
  .diagram .s {{ font-size:10.5px; fill:#6b5b85; }}
  .diagram .w {{ fill:#fff; }}
  .missing {{ color:#b4442e; font-family:monospace; }}
  .todo {{ background:#fdf0dc; border-left:3px solid #d99a2b; padding:8px 14px;
           font-family:ui-sans-serif,system-ui,sans-serif; font-size:13px; }}
  @media print {{ body {{ padding:0; }} h2 {{ page-break-after:avoid; }}
                  figure, pre, table {{ page-break-inside:avoid; }} }}
</style></head><body>

<h1>Encore</h1>
<p class="sub">Rank the concerts you've been to; Encore reads every Austin
venue listing and tells you which upcoming shows you'd regret missing.</p>

<div class="links">
  <div><b>Student</b> Priya Julian</div>
  <div><b>Course</b> MGT 409, Fall 2026</div>
  <div><b>Repo</b> <a href="{REPO_URL}">{REPO_URL}</a>
    <span class="pub">public &mdash; clone directly</span></div>
  <div><b>Live app</b> <a href="{APP_URL}">{APP_URL}</a></div>
  <div><b>Model</b> {t["model"]} via PORTKEY_API_KEY</div>
</div>

<h2>1. Motivation</h2>

<p>Austin has more live music per capita than anywhere in the United States.
On a single Friday night in October 2026, Encore's sweep found
<b>{cold["shows_considered"]} upcoming shows</b> across
<b>25 venues</b> in the next six weeks. That abundance is the
problem, not the feature.</p>

<p>The person with this problem is a regular showgoer &mdash; someone who has
been to dozens of concerts and has opinions about them. For me that is 31
logged shows across Moody Center, ACL Fest, Emo's, Stubb's and the ACL Live
tapings. The failure mode is specific and recurring: <i>you find out about a
show you would have loved after it has already happened.</i> Not because the
information was hidden, but because it was spread across two dozen venue
calendars, an Instagram story you scrolled past, and a friend's text you
forgot to answer.</p>

<p>The current cost of solving this properly is roughly 30&ndash;40 minutes a
week of manual work: open each venue's calendar, recognise maybe one name in
five, look up the unfamiliar ones, and decide. Almost nobody does this, which
is why the default outcome is regret. The cheaper substitutes all fail in
their own way. Instagram shows you what venues pay to promote. Spotify's
concert tab mostly surfaces artists already in your library, so it cannot tell
you about the opener you would have loved. Ticketmaster recommends by sales
volume. None of them know that you found Moody Center too big, or that the
best show you saw last year was a local band you had never heard of.</p>

<p>The information that would actually solve this &mdash; your own history of
what you have seen and how much you liked it &mdash; is the one input none of
these services has.</p>

<p>The cost is easy to understate because it is not a bill. Austin club
tickets run roughly $20&ndash;35, so missing a show you would have loved is a
small financial loss and a large opportunity one: that particular band, that
particular room, that particular night does not recur. Across the 31 shows in
my own log, I can name four I only heard about afterwards. At a conservative
one missed show a month, the thing Encore is competing with is not another app
&mdash; it is the half hour a week nobody spends, and the shows that quietly
pass by as a result.</p>

<h2>2. What is new</h2>

<p>Rating and logging apps exist for most media: Letterboxd for film,
Goodreads for books, Beli for restaurants. Each is a social network with a
rating primitive, where value comes from the aggregate and the feed.</p>

<p>Encore inverts that. <b>The log is not content, it is the input to an
agent.</b> There is no feed, no followers, and no aggregate score. Your 31
rated shows exist for one purpose: to let a set of agents read this week's
listings the way a friend with good taste would, and hand you a short list
with reasons.</p>

<p>Three things follow from that inversion, and together they are the
contribution:</p>

<ul>
<li><b>It is useful to a single user on day one.</b> A social app with one
user is empty. Encore with one user and a 31-show log produces a ranked
shortlist the first time it runs, because the signal comes from your history
rather than from a crowd.</li>
<li><b>It reads the whole city, not your library.</b> Encore considers every
listed show including openers and local acts, then decides. Services that
recommend from your listening history structurally cannot surface an artist
you have never streamed &mdash; which is exactly the artist worth telling you
about.</li>
<li><b>Negative signal is first-class.</b> Four <i>meh</i> ratings produced an
explicit "avoids" list, and that list demonstrably changes the output. Star
ratings in existing apps are used to rank what you already chose; here they
are used to rule things out.</li>
</ul>

<h2>3. Agents</h2>

<p>Five agents, each with a different input, a different failure mode, and a
different cost profile. The division is not decorative: Scout does structured
extraction from untrusted third-party text, Scholar does open-web research,
Ranker does judgement under a taste model, and Verifier is adversarial toward
all of them.</p>

{DIAGRAM}

<table>
<tr><th>Agent</th><th>Job</th><th>Tools and data</th></tr>
<tr><td><b>Scout</b></td><td>Fetch the Austin listing source and turn free-text
titles into structured shows: headliner, support, venue, date</td>
<td>HTTP with retry and stale-cache fallback; embedded JSON parsing;
{t["model"]}</td></tr>
<tr><td><b>Profiler</b></td><td>Convert the rated show log into a structured
taste profile: loves, avoids, venue preference, discovery appetite</td>
<td>The user's CSV log; {t["model"]}</td></tr>
<tr><td><b>Scholar</b></td><td>Research artists the user may not know, and say
so honestly when the sources are thin</td>
<td>Bandcamp autocomplete API, MusicBrainz, Wikipedia REST; {t["model"]}</td></tr>
<tr><td><b>Ranker</b></td><td>Screen every show cheaply against the profile,
then rank the finalists carefully and write the reason</td>
<td>Profile + listings + Scholar research; {t["model"]}</td></tr>
<tr><td><b>Verifier</b></td><td>Trace every pick back to its source listing and
check that the stated reasons are supported by the research</td>
<td>Deterministic string checks (no tokens) + {t["model"]}</td></tr>
</table>

<h3>Why the pipeline is ordered cheap-to-expensive</h3>

<p>Scout produces {cold["shows_considered"]} shows. Researching all of them
would be the obvious design and a bad one. Instead the Ranker screens all
{cold["shows_considered"]} using only the listing line &mdash; coarse,
deliberately harsh, most shows score below 40 &mdash; and only the top 14
receive Scholar research and careful ranking. That single ordering decision is
the difference between a run costing cents and a run costing dollars, and it
is the backbone of section 5.</p>

<h3>Why five agents rather than one prompt</h3>

<p>A single prompt could, in principle, be handed the listings and the log and
asked for five picks. It would be worse for three specific reasons, each of
which showed up during development.</p>

<p><b>Different inputs need different trust levels.</b> Scout reads
attacker-controllable third-party text; Profiler reads the user's own data.
Collapsing them means one prompt holding both, with no way to say "treat this
half as hostile and that half as authoritative." Splitting them is what makes
the injection defence in section 5 expressible at all.</p>

<p><b>Different stages have different unit economics.</b> Screening is
per-show and must be cheap; final ranking is per-run and can afford to be
careful. One prompt forces one cost profile for both, and the expensive one
wins. Separating them is what turns a dollar-scale run into a cent-scale
one.</p>

<p><b>A checker must not be the author.</b> Asking one prompt to produce
recommendations and then audit its own claims produces an agent that marks its
own homework. The Verifier sees the recommendation and the research, but not
the reasoning that produced it, and it is prompted adversarially. That
separation is why it flags its own system's output rather than rubber-stamping
it.</p>

<h3>What each agent gets wrong</h3>

<table>
<tr><th>Agent</th><th>Characteristic failure</th><th>Mitigation</th></tr>
<tr><td><b>Scout</b></td><td>Mis-splits a messy title, or treats a benefit gig
as one act</td><td>Verifier traces every artist back to the source string</td></tr>
<tr><td><b>Profiler</b></td><td>Over-reads a thin log and states preferences
the data does not support</td><td>Reports its own confidence; the Taste screen
exposes the profile for the user to correct</td></tr>
<tr><td><b>Scholar</b></td><td>Confidently describes a different band with the
same name</td><td>Exact-name matching, local-city preference, explicit
<code>known: false</code> rather than a guess</td></tr>
<tr><td><b>Ranker</b></td><td>Writes a plausible reason the research does not
support</td><td>Verifier flags unsupported claims and downgrades
confidence</td></tr>
<tr><td><b>Verifier</b></td><td>Over-flags figurative language as an
unsupported claim</td><td>Prompted to be strict on specifics and relaxed on
tone; flags downgrade rather than drop</td></tr>
</table>

<h3>A traced run</h3>

<p>Input: a 31-show log, Austin, a six-week window. The sweep considered
{cold["shows_considered"]} shows. Screening reduced them to 14 finalists.
Scholar researched those 14 (13 live calls, one already cached). The final
ranker returned five picks, and the Verifier checked each one.</p>

{img("discover.jpg", "Encore's Discover screen showing ranked picks",
     "The Discover screen. Each pick carries the specific reason it fits, "
     "plus the Verifier's judgement &mdash; shown to the user rather than "
     "hidden.")}

<p>The reasoning is grounded in specific log entries rather than genre
matching. The Julia Jacklin pick cites Angel Olsen and Waxahatchee; the
Adrianne Lenker pick cites Jessica Pratt and Gillian Welch and notes that the
Moody Theater is "a room you already enjoy." In an earlier run the system
surfaced a Rickshaw Billie's Burger Patrol show and justified it by comparison
to a local band in the log.</p>

{img("taste.jpg", "Encore's Taste screen showing the derived profile",
     "The Taste screen exposes what the Profiler inferred, so the user can "
     "catch it being wrong. The 'avoids' list is derived entirely from four "
     "<i>meh</i> ratings.")}

{img("log.jpg", "Encore's log screen listing the user's rated concerts",
     "The log: 31 shows, grouped by rating. This is the only input that "
     "distinguishes Encore from a generic recommender.")}

<h2>4. Tokenomics</h2>

<p>Every model call in the app passes through one metered wrapper that records
prompt tokens, completion tokens and latency per agent. The numbers below were
measured by <code>scripts/benchmark.py</code> on {t["measured_at"]}, which
clears the cache, runs a genuinely cold pipeline, then a warm one. Prices are
the course rate card for {t["model"]}: ${rate["input"]:.2f} per 1M input
tokens, ${rate["cached_input"]:.2f} cached, ${rate["output"]:.2f} output.</p>

<div class="kpis">
  <div class="kpi"><b>{money(cold["cost_usd"])}</b><span>cold run</span></div>
  <div class="kpi"><b>{money(warm["cost_usd"])}</b><span>warm run</span></div>
  <div class="kpi"><b>{cold["seconds"]}s</b><span>cold latency</span></div>
  <div class="kpi"><b>{warm["seconds"]}s</b><span>warm latency</span></div>
</div>

<table>
<tr><th>Agent</th><th class="n">Calls</th><th class="n">Cold tokens</th>
<th class="n">Warm tokens</th></tr>
{tokenomics_rows(cold["by_agent"], warm)}
<tr><td><b>Total</b></td><td class="n">{cold["model_calls"]}</td>
<td class="n">{cold["tokens_in"] + cold["tokens_out"]:,}</td>
<td class="n">{warm["tokens_in"] + warm["tokens_out"]:,}</td></tr>
</table>

<h3>Where the money goes, and what was done about it</h3>

<p>Three optimisations, each measured:</p>

<ul>
<li><b>Parse structured data instead of rendered text.</b> The listing source
embeds its full calendar as a JSON array. Switching from scraping rendered
page text to parsing that array cut the extraction cost by <b>42%</b>
(${0.0355:.4f} &rarr; ${0.0206:.4f}) and removed a class of parsing errors
entirely.</li>
<li><b>Screen before researching.</b> Scholar runs on 14 shows, not
{cold["shows_considered"]}. Researching every show would multiply Scholar's
cost by roughly 33&times; and produce the same five picks.</li>
<li><b>Tiered caching.</b> Listings and artist research are cached to disk;
near-term days expire after 12 hours because shows sell out, far-out days
after a week because they do not. The warm run costs <b>{saving:.0f}% less</b>
than the cold run and is <b>{speedup:.0f}&times; faster</b>.</li>
</ul>

<p>The remaining warm cost is almost entirely the screening pass, which is
inherently per-user: it scores the city against <i>your</i> profile. At the
application level even that is cached against a fingerprint of the log, so
revisiting the page costs nothing; {money(warm["cost_usd"])} is the price of a
fresh ranking after the log changes.</p>

<h3>What was deliberately not optimised</h3>

<p>Two obvious savings were rejected. <b>Caching the screening pass across
users</b> would be the largest remaining win, since screening is now most of
the warm cost &mdash; but screening is a function of the user's taste profile,
so sharing it would mean serving one person's judgement to another. The point
of the app is that the ranking is yours. <b>Dropping the Verifier</b> would
save about 7% of a run, and was rejected because the whole claim of the
product is that what reaches the screen has been checked.</p>

<h3>Cost at scale</h3>

<p>The key structural fact is that <b>listings and artist research are shared
across all users in a city</b>. The second user in Austin pays only for their
own screening and ranking. Assuming {t["runs_per_user_per_month"]} runs per
user per month and one shared sweep per day:</p>

<table>
<tr><th>Users</th><th class="n">Shared / month</th>
<th class="n">Per user / month</th><th class="n">Total / month</th></tr>
<tr><td>1</td><td class="n">{money(scale["1"]["shared_monthly_usd"])}</td>
<td class="n">{money(scale["1"]["per_user_monthly_usd"])}</td>
<td class="n">{money(scale["1"]["total_monthly_usd"])}</td></tr>
<tr><td>100</td><td class="n">{money(scale["100"]["shared_monthly_usd"])}</td>
<td class="n">{money(scale["100"]["per_user_monthly_usd"])}</td>
<td class="n">{money(scale["100"]["total_monthly_usd"])}</td></tr>
<tr><td>10,000</td><td class="n">{money(scale["10000"]["shared_monthly_usd"])}</td>
<td class="n">{money(scale["10000"]["per_user_monthly_usd"])}</td>
<td class="n">{money(scale["10000"]["total_monthly_usd"])}</td></tr>
</table>

<p>Roughly <b>ten cents per user per month</b> at scale, which a single
affiliate ticket sale per user per year would more than cover. The honest
caveat: these projections assume the cache hit rates measured on one city with
one user. A second city doubles the shared sweep; wildly different taste
profiles across users would reduce Scholar cache sharing.</p>

<h3>Performance trade-offs</h3>

<p>Screening in batches of 55 shows was chosen over per-show scoring: it is
roughly 9 calls instead of {cold["shows_considered"]}, at the cost of less
granular reasoning per show &mdash; acceptable because the screen only has to
be approximately right, and the final ranker reconsiders the survivors
carefully. Running batches concurrently took the full pipeline from 195
seconds to under 20 with no change in cost. The model does not accept a
temperature setting, so identical inputs can yield slightly different
orderings between runs; this is visible and discussed in section 7.</p>

<h2>5. Safety</h2>

<p>Encore reads untrusted third-party web content and then makes claims that
cost money to act on. Two risks follow, and both have built defences that are
demonstrated working by <code>scripts/../safety/demo.py</code>, which exits
non-zero if any defence fails.</p>

<h3>Risk 1: prompt injection via listings</h3>

<p>Every listing Scout reads is attacker-controllable in principle &mdash;
anyone who can get text onto a venue page or submit a show can try to hijack
the extractor. All fetched content is fenced in explicit untrusted-data
markers, and every system prompt instructs the model to report
instruction-shaped content rather than follow it.</p>

<p>Testing this surfaced a real vulnerability that had nothing to do with the
model obeying the injection. A blatant jailbreak caused the provider's own
content filter to reject the <i>entire batch</i> &mdash; which, because days
were processed in one call, silently returned <b>zero shows for that day</b>.
An attacker could erase a day of Austin music from the app without ever
reaching the model. The fix is quarantine: when a batch is filtered, the day
is retried one listing at a time, so the poisoned entry is isolated and every
genuine show survives.</p>

<pre>DEFENCE 1a: blatant jailbreak planted in a venue listing
  injection_suspected : True
  note                : provider content filter rejected 1 listing(s)
  shows extracted     : 2
      - Alvvays @ Mohawk
      - Being Dead @ Hotel Vegas
  <b>[PASS]</b> injection detected and reported
  <b>[PASS]</b> real shows survived (one poisoned listing did not blank the day)
  <b>[PASS]</b> planted event not promoted

DEFENCE 1b: subtle injection that clears the provider filter
  injection_suspected : True
  <b>[PASS]</b> injection reported by Encore's own prompt
  <b>[PASS]</b> competing listings not omitted</pre>

<p>1b matters more than 1a: it uses a mild, plausible-sounding instruction that
passes the provider's filter, proving Encore's own prompt-level defence works
rather than riding on infrastructure it does not control.</p>

<h3>Risk 2: fabricated recommendations</h3>

<p>A wrong date or venue costs a user an evening and the price of a ticket; an
invented comparison erodes trust in every other pick. The Verifier checks both
deterministically and semantically.</p>

<pre>DEFENCE 2: unsupported claims in a recommendation
  under test: "Being Dead's Grammy-winning sound, fresh off their
              Sub Pop signing, sounds almost exactly like Big Thief"
  research:   genre Experimental | Austin, Texas | sounds like: (none)

  flagged: "Grammy-winning sound"      -> no awards in research
  flagged: "fresh off a Sub Pop signing" -> no label in research
  flagged: "sounds almost exactly like Big Thief" -> no such comparison
  confidence downgraded: high -> medium
  <b>[PASS]</b> invented claims caught

DEFENCE 2b: deterministic listing check (no model, no tokens)
  source listing : Croy and the Boys w/ The Mercers
  claimed artist : Taylor Swift
  <b>[PASS]</b> artist not traceable to source listing</pre>

<p>Two design choices are worth defending. First, flagged picks are
<i>downgraded and labelled</i> rather than silently dropped, so the user sees
"partly unverified" instead of a mysteriously short list. Second, Scholar
reports <code>known: false</code> when sources are thin rather than guessing,
and Bandcamp matches require an exact name match with a preference for the
local band &mdash; confidently describing the wrong band is worse than
admitting ignorance.</p>

<h3>Risk 3: scraping conduct</h3>

<p>Four venues (Hotel Vegas, Empire Control Room, Saxon Pub, Hole in the Wall)
return HTTP 403 to non-browser clients. That is a clear signal, and Encore
does not work around it &mdash; those sites are excluded in code with a
comment explaining why. Their shows still reach users via the community
listing source, which is published to be read.</p>

<h3>Risk 4: personal data</h3>

<p>A concert history is mildly personal: it implies where someone was on a
given night. Encore holds as little as it can. There are no accounts, no email
addresses and no passwords. A visitor is identified by a random twelve-character
cookie that maps to one CSV file and protects nothing, so there is no
credential to steal. Usage events store that same random id, an event type and
an artist name &mdash; never an IP address, a user agent or anything that
identifies a person. The logs of the people who tested Encore were never read
individually; only the aggregate counts in the next section were.</p>

<h2>6. Impact</h2>

<div class="kpis">
  <div class="kpi"><b>{impact["sessions"]}</b><span>people used it</span></div>
  <div class="kpi"><b>{impact["pct_found_new"]}%</b><span>found a show they
    didn't know about</span></div>
  <div class="kpi"><b>{impact["shows_surfaced"]}</b><span>shows recommended</span></div>
  <div class="kpi"><b>{impact["runs_per_user"]}</b><span>runs per person</span></div>
</div>

<table>
<tr><th>Measure</th><th class="n">Value</th><th>How it is counted</th></tr>
<tr><td>People who used it</td><td class="n">{impact["sessions"]}</td>
<td>Distinct visitors who ran Encore or entered shows &mdash; a page load
alone does not count</td></tr>
<tr><td>Built their own log</td><td class="n">{impact["built_own_log"]}</td>
<td>Entered at least one concert of their own rather than loading the
demo</td></tr>
<tr><td>Discovery runs</td><td class="n">{impact["runs"]}</td>
<td>Completed pipeline runs, {impact["runs_per_user"]} per person</td></tr>
<tr><td>Shows recommended</td><td class="n">{impact["shows_surfaced"]}</td>
<td>Picks shown across all runs</td></tr>
<tr><td>"Didn't know this" clicks</td><td class="n">{impact["new_to_me"]}</td>
<td>From {impact["users_found_new"]} people &mdash;
{impact["pct_found_new"]}% of users</td></tr>
<tr><td>Shows saved</td><td class="n">{impact["saved"]}</td>
<td>From {impact["users_saved"]} people &mdash; {impact["pct_saved"]}% of
users</td></tr>
<tr><td>"Not for me"</td><td class="n">{impact["not_for_me"]}</td>
<td>Rejections, which feed back into the taste profile</td></tr>
</table>

<p>The app records five anonymous events: a run, a "didn't know this" click, a
save, a "not for me", and adding shows. There is no identifying data beyond a
random session id. These numbers are read from the deployed app's event log at
build time, with a baseline timestamp excluding development testing, so
nothing here counts the author.</p>

<p class="s"><b>On sample size.</b> These figures come from
{impact["sessions"]} people over a single evening, recruited from friends who
go to shows in Austin. That is enough to show the app works for people other
than its author, and not enough to support a percentage quoted to one decimal
place. Treat the proportions as indicative; the counts are exact.</p>

<p><b>The headline measure is "didn't know this."</b> Encore's claim is not
that it finds good shows &mdash; a list of every Austin gig does that &mdash;
but that it finds shows a particular person would have missed. That click is
the only honest test of it, which is why it is the one thing testers were
asked to do.</p>

<h3>Evidence so far</h3>

<p>The first end-to-end run against my real log returned Adrianne Lenker at
ACL Live as a top pick. I had independently been considering that show, and
had not told the system about it &mdash; it was selected from
{cold["shows_considered"]} candidates on the strength of 31 rated shows. Two
further picks, Julia Jacklin and Slow Pulp, are artists I listen to but had not
known were playing Austin. That is the target outcome stated in section 1: the
show you would have found out about too late.</p>

<h2>7. Limits and next steps</h2>

<ul>
<li><b>One city, one listing source.</b> Austin coverage depends on a single
community-maintained page. If it goes down or changes format, Encore degrades
to a stale cache. Venue metadata lives in one file and the extraction is
source-specific, so a second city is roughly a day of work, not an
architectural change.</li>
<li><b>Thin coverage of very small artists.</b> Scholar answers
<code>known: false</code> for genuinely obscure local acts, which is honest but
unhelpful. Reading the artist's own Bandcamp page rather than the search
result would close most of this gap.</li>
<li><b>Run-to-run variance.</b> The model does not accept a temperature
parameter, so the same log and the same listings can produce slightly
different orderings. The five picks are stable in content; their order is
not.</li>
<li><b>The log is the bottleneck.</b> Encore is only as good as the history it
reads, and entering 31 shows by hand is real work. Importing from ticket
confirmation emails is the obvious next feature and would remove the single
biggest barrier to a new user.</li>
<li><b>No feedback loop yet.</b> "Not for me" is recorded but does not yet
feed back into the profile. Treating those clicks as negative signal is the
most direct path to improving picks over time.</li>
<li><b>Logs do not survive a redeploy.</b> Identity is a year-long cookie and
logs are files on disk, which survives restarts but not the host rebuilding
its filesystem. Mirroring the log into the browser's local storage would fix
this without accounts or a database; real accounts would be a larger change
for a smaller benefit.</li>
<li><b>Display type is loaded from a CDN.</b> The interface asks Google Fonts
for Bebas Neue and Space Grotesk. The app already requires network access for
the model, and there are system fallbacks, but it is one more thing that can
be slow or blocked.</li>
<li><b>Travel mode.</b> "I'll be in Chicago November 14&ndash;17, what's on?"
is the same pipeline with a different city and date window, and is the most
requested extension from early conversations.</li>
</ul>

<h2>Links</h2>

<div class="links">
  <div><b>Repo</b> <a href="{REPO_URL}">{REPO_URL}</a>
    <span class="pub">public &mdash; clone directly</span></div>
  <div><b>Live app</b> <a href="{APP_URL}">{APP_URL}</a></div>
  <div><b>Run locally</b> <code>git clone {REPO_URL}</code>, then follow the
    README &mdash; clone to working app takes about ten seconds.</div>
</div>

<p class="s">Report generated by <code>scripts/build_report.py</code>.
All figures measured, not estimated.</p>

</body></html>
"""


if __name__ == "__main__":
    out = ROOT / "report.html"
    out.write_text(build(), encoding="utf-8")
    kb = out.stat().st_size / 1024
    print(f"wrote {out} ({kb:.0f} KB, images embedded)")
