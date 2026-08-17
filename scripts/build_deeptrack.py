#!/usr/bin/env python3
"""Build site/deep-track.html (index of the deep dives) and inject a
'Read the deep dive' callout into each original concept page. Idempotent."""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "analysis" / "deep"
SITE = ROOT / "site"
CONC = SITE / "concepts"

# logical reading order (locally-flat geometry -> up to cosmology)
ORDER = [
    "physics-informed-learning", "operator-learning", "reduced-order-modeling",
    "scientific-machine-learning", "differentiable-simulation",
    "inverse-problems-and-control", "fluid-mechanics-simulation",
    "hybrid-twins", "uncertainty-and-robustness",
]

def esc(s): return html.escape(str(s), quote=False)

def load():
    specs = {}
    for p in SPECS.glob("*.json"):
        if p.stem.startswith("_"):
            continue
        specs[p.stem] = json.loads(p.read_text())
    return specs

INDEX = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Deep Track · DDPS Concept Lab</title>
<link rel="stylesheet" href="assets/styles.css">
<style>
.dt-hero{{max-width:820px;margin:6px 0 26px}}
.dt-hero .kick{{font-size:12px;color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.07em;margin:6px 0}}
.dt-hero h1{{margin:6px 0 12px}}
.dt-hero p{{font-size:18px;color:#2c2c2c;line-height:1.5}}
.dt-grid{{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(340px,1fr))}}
.dt-card{{border:1px solid var(--line,#dcdcdc);border-radius:10px;background:#fff;padding:16px 18px;text-decoration:none;color:inherit;display:block;transition:border-color .12s}}
.dt-card:hover{{border-color:var(--accent)}}
.dt-card .n{{font-size:12px;color:#7a7a7a;font-family:ui-monospace,Menlo,monospace}}
.dt-card h3{{margin:5px 0 8px;font-size:17px;color:var(--accent)}}
.dt-card p{{margin:0;font-size:14px;color:#3a3a3a;line-height:1.45}}
.dt-card .go{{margin-top:10px;font-size:13px;font-weight:700;color:var(--accent)}}
</style></head><body>
<header class="topbar"><a class="brand" href="index.html">DDPS Concept Lab</a>
<nav><a href="index.html">Overview</a><a href="concepts.html">Concepts</a><a class="active" href="deep-track.html">Deep Track</a></nav></header>
<main>
<div class="dt-hero">
  <div class="kick">the deep track · every number computed</div>
  <h1>Deep Track — data-driven physical simulation, actually run</h1>
  <p>Nine ideas at the heart of scientific machine learning, each rebuilt as a first-principles deep dive in plain language: a real problem, the reframe that cracks it, and <strong>a result we actually computed and ran</strong> — a network solving a differential equation with no data (error 0.9 to 0.002), SINDy reading an equation back off raw trajectories, a hybrid model cutting simulation error 122-fold, an ensemble whose error bars grow 8x exactly where it has no data. Every quantity is produced by a short program (<code>scripts/experiments/ddps_run.py</code>); nothing is asserted.</p>
</div>
<div class="dt-grid">
{cards}
</div>
<footer style="color:#5a5a5a;font-size:13px;border-top:1px solid var(--line,#dcdcdc);padding:22px 0 60px;margin-top:26px">Gravity &amp; Light · deep track · {count} computed deep dives.</footer>
</main></body></html>
"""

CARD = """  <a class="dt-card" href="concepts/{id}-deep.html">
    <div class="n">{n:02d}</div>
    <h3>{title}</h3>
    <p>{blurb}</p>
    <div class="go">Read the deep dive &rarr;</div>
  </a>"""

def first_sentence(lede):
    # strip tags, take up to first 2 sentences, cap length
    t = re.sub("<[^>]+>", "", lede)
    parts = re.split(r"(?<=[.?!])\s+", t)
    out = " ".join(parts[:2])
    return out[:240].rstrip()

def build_index(specs):
    ids = [i for i in ORDER if i in specs] + [i for i in specs if i not in ORDER]
    cards = []
    for n, cid in enumerate(ids, 1):
        s = specs[cid]
        cards.append(CARD.format(id=esc(cid), n=n, title=esc(s["title"]),
                                 blurb=esc(first_sentence(s["lede"]))))
    (SITE / "deep-track.html").write_text(
        INDEX.format(cards="\n".join(cards), count=len(ids)))
    print(f"wrote deep-track.html ({len(ids)} cards)")

CALLOUT = ('<div class="deepdive-callout" style="border:1px solid var(--accent,#255f85);'
           'background:#eef3f7;border-radius:10px;padding:14px 18px;margin:16px 0">'
           '<strong>Go deeper:</strong> this concept has a first-principles <a href="{id}-deep.html">'
           'deep dive with a result we actually computed</a> &mdash; the real run, an honest limit, '
           'and a surprising connection. <a href="../deep-track.html">See the whole deep track &rarr;</a></div>')

def inject_buttons(specs):
    n = 0
    for cid in specs:
        page = CONC / f"{cid}.html"
        if not page.exists():
            print(f"  no original for {cid}, skip")
            continue
        htmltxt = page.read_text()
        if "deepdive-callout" in htmltxt:
            # refresh existing callout
            htmltxt = re.sub(r'<div class="deepdive-callout".*?</div>\s*</div>',
                             CALLOUT.format(id=cid), htmltxt, flags=re.S)
            page.write_text(htmltxt)
            n += 1
            continue
        anchor = '<p><a href="../concepts.html">Back to concepts</a></p>'
        if anchor in htmltxt:
            htmltxt = htmltxt.replace(anchor, anchor + "\n        " + CALLOUT.format(id=cid), 1)
            page.write_text(htmltxt)
            n += 1
        else:
            print(f"  anchor not found in {cid}, skip")
    print(f"injected/updated callout in {n} concept pages")

def main():
    specs = load()
    build_index(specs)
    inject_buttons(specs)

if __name__ == "__main__":
    main()
