"""Build the animated profile banner in Retec's brand style (retec.vn/static/style.css).

Edit LINES below, then run from the repo root:

    python3 scripts/make-banner.py            # writes assets/banner.svg

Fonts are fetched from Google Fonts as subsets containing only the glyphs used,
then embedded, so the SVG renders in the brand fonts without external requests.
"""
import base64
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "assets" / "banner.svg"

BG, INK, INK2 = "#F7F6F2", "#14171F", "#4B4F58"
CORAL, TEAL = "#FF6B47", "#21C7A8"

# Each line is a list of (text, highlight) segments; highlights use the coral accent.
LINES = [
    [("Building ", False), ("Retec", True), (": smart tools for everyday work", False)],
    [("OCR", True), (": Vietnamese text from images & PDFs", False)],
    [("Reads handwriting and formulas too", False)],
    [("PHOTO", True), (": edit text in photos, coming soon", False)],
]
SLOT, TYPE, ERASE = 5.0, 1.6, 0.8
T = SLOT * len(LINES) + TYPE            # extra TYPE so line 0 re-types after the last erase
FS = 22
CW = 0.6 * FS                           # IBM Plex Mono advance width is 600/1000 em
X0, Y = 80, 244


HELLO, NAME, SITE = "Hi, I'm", "Nam", "retec.vn"

# A browser user agent makes Google Fonts serve woff2.
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def font(name, weight, text):
    query = urllib.parse.urlencode({"family": f"{name}:wght@{weight}", "text": "".join(sorted(set(text)))})
    css = fetch(f"https://fonts.googleapis.com/css2?{query}").decode()
    url = re.search(r"url\((https://[^)]+)\)", css).group(1)
    data = base64.b64encode(fetch(url)).decode()
    return (f"@font-face{{font-family:'{name}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")


def esc(s):
    return s.replace("&", "&amp;")


def pct(v):
    return f"{v / T * 100:.3f}%"


def frames(stops):
    """stops: (time, value, timing) -> keyframe body; timing applies to the segment after the stop."""
    out = []
    for t, v, timing in stops:
        tf = f";animation-timing-function:{timing}" if timing else ""
        out.append(f"{pct(t)}{{{v}{tf}}}")
    return "".join(out)


css = [
    font("Space Grotesk", 700, NAME),
    font("Space Grotesk", 500, HELLO),
    font("IBM Plex Mono", 400, "".join(t for segs in LINES for t, _ in segs) + SITE),
]
body = []
for i, segs in enumerate(LINES):
    n = sum(len(t) for t, _ in segs)
    w = n * CW
    st = f"steps({n})"
    s = i * SLOT
    hold_end, erase_end = s + SLOT - ERASE, s + SLOT
    if i == 0:   # visible at t=0 so non-animating viewers still see a full line
        reveal = [(0, "transform:scaleX(1)", "linear"), (hold_end, "transform:scaleX(1)", st),
                  (erase_end, "transform:scaleX(0)", "linear"), (T - TYPE, "transform:scaleX(0)", st),
                  (T, "transform:scaleX(1)", None)]
        move = [(0, f"transform:translateX({w:.1f}px)", "linear"),
                (hold_end, f"transform:translateX({w:.1f}px)", st),
                (erase_end, "transform:translateX(0)", "linear"),
                (T - TYPE, "transform:translateX(0)", st), (T, f"transform:translateX({w:.1f}px)", None)]
        show = [(0, "opacity:1", None), (erase_end - 0.01, "opacity:1", None), (erase_end, "opacity:0", None),
                (T - TYPE - 0.01, "opacity:0", None), (T - TYPE, "opacity:1", None), (T, "opacity:1", None)]
    else:
        reveal = [(0, "transform:scaleX(0)", "linear"), (s, "transform:scaleX(0)", st),
                  (s + TYPE, "transform:scaleX(1)", "linear"), (hold_end, "transform:scaleX(1)", st),
                  (erase_end, "transform:scaleX(0)", None), (T, "transform:scaleX(0)", None)]
        move = [(0, "transform:translateX(0)", "linear"), (s, "transform:translateX(0)", st),
                (s + TYPE, f"transform:translateX({w:.1f}px)", "linear"),
                (hold_end, f"transform:translateX({w:.1f}px)", st),
                (erase_end, "transform:translateX(0)", None), (T, "transform:translateX(0)", None)]
        show = [(0, "opacity:0", None), (s - 0.01, "opacity:0", None), (s, "opacity:1", None),
                (erase_end - 0.01, "opacity:1", None), (erase_end, "opacity:0", None), (T, "opacity:0", None)]
    css += [
        f"@keyframes r{i}{{{frames(reveal)}}}",
        f"@keyframes m{i}{{{frames(move)}}}",
        f"@keyframes s{i}{{{frames(show)}}}",
        f"#r{i}{{transform-box:fill-box;transform-origin:0 50%;animation:r{i} {T}s infinite}}",
        f"#k{i}{{animation:m{i} {T}s infinite,s{i} {T}s infinite}}",
    ]
    # static fallback for renderers without CSS animation: only line 0 shows, cursor at its end
    clip_attr = "" if i == 0 else f' transform="matrix(0 0 0 1 {X0} 0)"'
    cur_attr = f' transform="translate({w:.1f} 0)"' if i == 0 else ' opacity="0"'
    spans = "".join(f'<tspan fill="{CORAL}">{esc(t)}</tspan>' if hi else esc(t) for t, hi in segs)
    body.append(
        f'    <clipPath id="c{i}"><rect id="r{i}" x="{X0}" y="{Y - 26}" width="{w + 10:.1f}" height="36"{clip_attr}/></clipPath>\n'
        f'    <text x="{X0}" y="{Y}" clip-path="url(#c{i})">{spans}</text>\n'
        f'    <rect id="k{i}" x="{X0 + 2}" y="{Y - 19}" width="2.5" height="25" rx="1" fill="{CORAL}"{cur_attr}/>'
    )

# Retec wordmark, copied from retec.vn/shared/retec-wordmark.svg
WORDMARK = f'''<svg x="858" y="92" width="262" height="75" viewBox="8 0 230 66" fill="none">
    <g stroke="{INK}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 60V38A18 18 0 0 1 32 20"/><path d="M48.0 40H89.0A20.5 20.5 0 1 0 83.73 53.72"/>
      <path d="M115 6V50A10 10 0 0 0 125 60M105 20H126"/><path d="M132.0 40H173.0A20.5 20.5 0 1 0 167.73 53.72"/>
      <path d="M223.22 24.77A20.5 20.5 0 1 0 223.22 55.23"/>
    </g>
    <circle cx="41.5" cy="19" r="5.5" fill="{CORAL}"/><circle cx="230" cy="40" r="5.5" fill="{TEAL}"/>
  </svg>'''

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-labelledby="t">
  <title id="t">Hi, I'm Nam, building Retec: smart tools for everyday work</title>
  <style>
{chr(10).join("    " + c for c in css)}
  </style>
  <defs>
    <pattern id="grid" width="22" height="22" patternUnits="userSpaceOnUse">
      <circle cx="11" cy="11" r="1" fill="{INK}" fill-opacity="0.10"/>
    </pattern>
    <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="50"/></filter>
    <clipPath id="frame"><rect width="1200" height="300" rx="18"/></clipPath>
  </defs>

  <g clip-path="url(#frame)">
    <rect width="1200" height="300" fill="{BG}"/>
    <rect width="1200" height="300" fill="url(#grid)"/>
    <ellipse cx="80" cy="10" rx="320" ry="190" fill="{CORAL}" fill-opacity="0.13" filter="url(#blur)"/>
    <ellipse cx="1150" cy="300" rx="340" ry="220" fill="{TEAL}" fill-opacity="0.12" filter="url(#blur)"/>
    <circle cx="1185" cy="-15" r="120" fill="none" stroke="{TEAL}" stroke-opacity="0.16" stroke-width="22"/>
    <path d="M -60 330 A 230 230 0 0 1 150 330" fill="none" stroke="{CORAL}" stroke-opacity="0.16" stroke-width="22" transform="rotate(-8 45 330)"/>
    <circle cx="44" cy="262" r="7" fill="{TEAL}"/>
    <circle cx="800" cy="54" r="7" fill="{CORAL}"/>
  </g>
  <rect x="0.75" y="0.75" width="1198.5" height="298.5" rx="18" fill="none" stroke="{INK}" stroke-opacity="0.14" stroke-width="1.5"/>

  <text x="80" y="96" font-family="'Space Grotesk',system-ui,sans-serif" font-size="28" font-weight="500" fill="{INK2}">{esc(HELLO)}</text>
  <text x="74" y="194" font-family="'Space Grotesk',system-ui,sans-serif" font-size="112" font-weight="700" fill="{INK}" letter-spacing="-3">{esc(NAME)}</text>

  <g font-family="'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace" font-size="{FS}" fill="{INK2}">
{chr(10).join(body)}
  </g>

  {WORDMARK}
  <g font-family="'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace" font-size="17" fill="{INK2}">
    <rect x="900" y="199" width="36" height="2" rx="1" fill="{CORAL}"/>
    <text x="989" y="206" text-anchor="middle">{esc(SITE)}</text>
    <rect x="1042" y="199" width="36" height="2" rx="1" fill="{TEAL}"/>
  </g>
</svg>
'''
OUT.write_text(svg)
print(f"wrote {OUT}")
