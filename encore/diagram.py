"""The agent architecture diagram, shared by the report and the deck."""

SVG = """
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
