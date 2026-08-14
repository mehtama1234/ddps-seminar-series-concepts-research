#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
ASSETS = SITE / "assets"


def load_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, body: str, prefix: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="stylesheet" href="{prefix}assets/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="{prefix}index.html">DDPS Concept Lab</a>
    <nav>
      <a href="{prefix}index.html">Overview</a>
      <a href="{prefix}deep-dives.html">Deep Dives</a>
      <a href="{prefix}concepts.html">Concepts</a>
      <a href="{prefix}talks.html">Talks</a>
      <a href="{prefix}evidence.html">Evidence</a>
      <a href="{prefix}transcripts.html">Transcripts</a>
    </nav>
  </header>
  <main>{body}</main>
</body>
</html>
"""


def short_title(title: str) -> str:
    return re.sub(r"^\s*DDPS\s*\|\s*", "", title).strip()


def render_index(summary: dict[str, Any], concepts: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> None:
    body = f"""
<section class="hero">
  <p class="eyebrow">Transcript-backed first-pass map</p>
  <h1>Data-driven Physical Simulations</h1>
  <p class="lede">A local study site for the DDPS seminar playlist: physics-informed learning, reduced-order modeling, differentiable simulation, operator learning, fluid mechanics, hybrid twins, uncertainty, and inverse problems.</p>
</section>
<section class="stats">
  <article><strong>{summary['video_count']}</strong><span>visible videos</span></article>
  <article><strong>{summary['transcript_count']}</strong><span>available transcripts</span></article>
  <article><strong>{summary['word_count']:,}</strong><span>transcript words</span></article>
  <article><strong>{len(concepts)}</strong><span>concept themes</span></article>
  <article><strong>{len(evidence)}</strong><span>evidence anchors</span></article>
</section>
<section>
  <h2>First-Principles Thesis</h2>
  <p>Data-driven simulation is not just replacing solvers with neural nets. It is a scientific modeling problem: governing equations, numerical stability, training data, discretization, uncertainty, and downstream decisions must fit together.</p>
  <p>The seminar series is useful because it shows the field from multiple angles: why PINNs fail, how reduced models work, how differentiable simulators enable inverse design, and how learned surrogates interact with physics.</p>
</section>
<section>
  <h2>Deep Dive Route</h2>
  <p>Start with the concept atlas, then add deep dives for the foundational seminars: PINN failure modes, differentiable physics, operator learning, reduced-order modeling, and robust scientific ML.</p>
  <p><a class="button" href="deep-dives.html">Open deep dives</a></p>
</section>
<section>
  <h2>Concept Route</h2>
  <div class="grid">
    {''.join(f'<article class="card"><h3><a href="concepts/{slugify(c["id"])}.html">{esc(c["name"])}</a></h3><p>{esc(c["plain_language_definition"])}</p></article>' for c in concepts)}
  </div>
</section>
"""
    (SITE / "index.html").write_text(page("DDPS Seminar Series Concept Lab", body), encoding="utf-8")


def optional_sections(item: dict[str, Any]) -> str:
    """Render deeper rubric sections when the source record supplies them.

    Backward-compatible: records without these keys render nothing.
    """
    specs = [
        ("worked_example", "Worked Example"),
        ("deeper_mechanics", "One Level Deeper"),
        ("failure_boundary", "Failure Boundary"),
    ]
    out = []
    for key, heading in specs:
        value = item.get(key)
        if not value:
            continue
        if isinstance(value, list):
            inner = "<ul>" + "".join(f"<li>{esc(v)}</li>" for v in value) + "</ul>"
        else:
            inner = "".join(f"<p>{esc(p)}</p>" for p in str(value).split("\n\n") if p.strip())
        out.append(f'<section class="detail"><h2>{heading}</h2>{inner}</section>')
    return "\n".join(out)


def render_deep_dives(deep_dives: list[dict[str, Any]], talks_by_index: dict[int, dict[str, Any]]) -> None:
    cards = []
    for deep in deep_dives:
        href = f"deep-dives/{slugify(deep['id'])}.html"
        talk = talks_by_index.get(int(deep["talk_index"]), {})
        cards.append(
            f"""<article class="card">
  <p class="quiet">Talk {esc(deep['talk_index'])} · {esc(deep['organization'])}</p>
  <h3><a href="{href}">{esc(deep['title'])}</a></h3>
  <p>{esc(deep['one_sentence'])}</p>
</article>"""
        )
        claims = "".join(f"<li>{esc(item)}</li>" for item in deep["key_claims"])
        deep_extra = optional_sections(deep)
        terms = "".join(f"<article class=\"detail\"><h3>{esc(item['term'])}</h3><p>{esc(item['meaning'])}</p></article>" for item in deep["important_terms"])
        connections = "".join(f"<li>{esc(item)}</li>" for item in deep["stanford_connections"])
        evidence = "".join(f"<blockquote>{esc(item)}</blockquote>" for item in deep["selected_evidence"])
        body = f"""
<p><a href="../deep-dives.html">Back to deep dives</a></p>
<section class="page-head">
  <p class="eyebrow">Talk {esc(deep['talk_index'])} · {esc(deep['organization'])}</p>
  <h1>{esc(deep['title'])}</h1>
  <p class="lede">{esc(deep['one_sentence'])}</p>
  <p><a href="{esc(talk.get('url', '#'))}">YouTube source</a> · <a href="../talks/{int(deep['talk_index']):02d}.html">Talk page</a></p>
</section>
<div class="two-col">
  <section class="detail"><h2>Core Problem</h2><p>{esc(deep['core_problem'])}</p></section>
  <section class="detail"><h2>First-Principles Model</h2><p>{esc(deep['first_principles_model'])}</p></section>
</div>
<section class="detail">
  <h2>Key Claims</h2>
  <ul>{claims}</ul>
</section>
{deep_extra}
<section>
  <h2>Important Terms</h2>
  <div class="two-col">{terms}</div>
</section>
<section class="detail">
  <h2>Connections Across The Series</h2>
  <ul>{connections}</ul>
</section>
<div class="two-col">
  <section class="detail"><h2>Practical Caution</h2><p>{esc(deep['practical_caution'])}</p></section>
  <section class="detail"><h2>Takeaway</h2><p>{esc(deep['takeaway'])}</p></section>
</div>
<section>
  <h2>Selected Transcript Phrases</h2>
  {evidence}
</section>
"""
        (SITE / "deep-dives" / f"{slugify(deep['id'])}.html").write_text(page(deep["title"], body, prefix="../"), encoding="utf-8")

    body = f"""
<section class="page-head">
  <p class="eyebrow">Deep synthesis</p>
  <h1>High-Value Talks</h1>
  <p class="lede">Detailed first-principles writeups for seminars that best frame the field. This section starts empty and grows as we review the transcript set manually.</p>
</section>
<div class="grid">{''.join(cards) if cards else '<article class="card"><h3>No deep dives yet</h3><p>The transcript-backed concept atlas is available now. Manual deep dives can be added after reviewing the highest-value seminars.</p></article>'}</div>
"""
    (SITE / "deep-dives.html").write_text(page("Deep Dives", body), encoding="utf-8")


def render_concepts(concepts: list[dict[str, Any]], evidence_by_id: dict[str, dict[str, Any]]) -> None:
    cards = []
    for concept in concepts:
        href = f"concepts/{slugify(concept['id'])}.html"
        cards.append(f'<article class="card"><h3><a href="{href}">{esc(concept["name"])}</a></h3><p>{esc(concept["ordinary_problem"])}</p><p class="quiet">{esc(concept["theme"])}</p></article>')
        ev_html = []
        for ev_id in concept.get("evidence_ids", []):
            ev = evidence_by_id[ev_id]
            ev_html.append(
                f"""<article class="evidence-item">
  <h3>{esc(ev['title'])}</h3>
  <p><a href="{esc(ev['url'])}">{esc(ev['url'])}</a></p>
  <blockquote>{esc(ev['quote'])}</blockquote>
  <p><strong>Evidence type:</strong> {esc(ev['evidence_type'])}</p>
  <p>{esc(ev['why_span_matters'])}</p>
</article>"""
            )
        body = f"""
<p><a href="../concepts.html">Back to concepts</a></p>
<section class="page-head">
  <p class="eyebrow">{esc(concept['theme'])}</p>
  <h1>{esc(concept['name'])}</h1>
  <p class="lede">{esc(concept['plain_language_definition'])}</p>
</section>
<div class="two-col">
  <section class="detail"><h2>Ordinary Problem</h2><p>{esc(concept['ordinary_problem'])}</p></section>
  <section class="detail"><h2>Naive Picture</h2><p>{esc(concept['naive_picture'])}</p></section>
  <section class="detail"><h2>Why It Fails</h2><p>{esc(concept['why_naive_fails'])}</p></section>
  <section class="detail"><h2>First-Principles Move</h2><p>{esc(concept['first_principles'])}</p></section>
  <section class="detail"><h2>What Breaks Without It</h2><p>{esc(concept['what_breaks_without_it'])}</p></section>
  <section class="detail"><h2>Summit Role</h2><p>{esc(concept['course_role'])}</p></section>
</div>
{optional_sections(concept)}
<section>
  <h2>Transcript Evidence</h2>
  {''.join(ev_html)}
</section>
"""
        (SITE / "concepts" / f"{slugify(concept['id'])}.html").write_text(page(concept["name"], body, prefix="../"), encoding="utf-8")
    body = f"""
<section class="page-head">
  <p class="eyebrow">Concept atlas</p>
  <h1>Data-driven Simulation Concepts</h1>
  <p class="lede">A first-pass concept map generated from the playlist titles and available transcripts. Use this as the route for deeper talk-by-talk writeups.</p>
</section>
<div class="grid">{''.join(cards)}</div>
"""
    (SITE / "concepts.html").write_text(page("Concepts", body), encoding="utf-8")


def render_evidence(evidence: list[dict[str, Any]], concepts_by_id: dict[str, dict[str, Any]]) -> None:
    items = []
    for ev in evidence:
        concept_links = " ".join(
            f'<a class="chip" href="concepts/{slugify(cid)}.html">{esc(concepts_by_id[cid]["name"])}</a>'
            for cid in ev.get("supports_concepts", [])
            if cid in concepts_by_id
        )
        items.append(
            f"""<article class="evidence-item" id="{esc(ev['id'])}">
  <h2>{esc(ev['title'])}</h2>
  <p><a href="{esc(ev['url'])}">{esc(ev['url'])}</a></p>
  <blockquote>{esc(ev['quote'])}</blockquote>
  <p><strong>Source tier:</strong> {esc(ev['source_tier'])} · <strong>Type:</strong> {esc(ev['evidence_type'])}</p>
  <p>{esc(ev['why_span_matters'])}</p>
  <p>{concept_links}</p>
</article>"""
        )
    body = f"""
<section class="page-head">
  <p class="eyebrow">Evidence ledger</p>
  <h1>Transcript Anchors</h1>
  <p class="lede">Short transcript spans selected by title and keyword matches. These are starting anchors for manual review and deeper synthesis.</p>
</section>
{''.join(items)}
"""
    (SITE / "evidence.html").write_text(page("Evidence", body), encoding="utf-8")


def render_talks(index: list[dict[str, Any]], evidence: list[dict[str, Any]], deep_dives: list[dict[str, Any]]) -> None:
    evidence_by_talk: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for ev in evidence:
        evidence_by_talk[int(ev["lecture_index"])].append(ev)
    deep_by_talk = {int(deep["talk_index"]): deep for deep in deep_dives}

    cards = []
    for row in index:
        talk_index = int(row["index"])
        href = f"talks/{talk_index:02d}.html"
        cards.append(
            f"""<article class="card">
  <h3><a href="{href}">Talk {talk_index}: {esc(short_title(row['title']))}</a></h3>
  <p>{row['word_count']:,} transcript words · {len(evidence_by_talk.get(talk_index, []))} evidence anchors</p>
  <p class="quiet">{esc(row['transcript_status'])} · {esc(row['source_tier'])}{' · deep dive available' if talk_index in deep_by_talk else ''}</p>
</article>"""
        )
        items = []
        for ev in sorted(evidence_by_talk.get(talk_index, []), key=lambda item: item["id"]):
            items.append(
                f"""<article class="evidence-item">
  <h3>{esc(ev['title'])}</h3>
  <p><a href="{esc(ev['url'])}">{esc(ev['url'])}</a></p>
  <blockquote>{esc(ev['quote'])}</blockquote>
  <p>{esc(ev['why_span_matters'])}</p>
</article>"""
            )
        body = f"""
<p><a href="../talks.html">Back to talks</a></p>
<section class="page-head">
  <p class="eyebrow">Talk {talk_index}</p>
  <h1>{esc(row['title'])}</h1>
  <p class="lede">{row['word_count']:,} words · {row['cue_count']:,} timestamped cues · <a href="{esc(row['url'])}">YouTube source</a></p>
  {f'<p><a class="button" href="../deep-dives/{slugify(deep_by_talk[talk_index]["id"])}.html">Open deep dive</a></p>' if talk_index in deep_by_talk else ''}
</section>
<section>
  <h2>Selected Anchors</h2>
  {''.join(items) if items else '<p>No evidence anchors have been selected for this talk yet.</p>'}
</section>
<section>
  <h2>Local Source Files</h2>
  <p><code>{esc(row.get('clean_txt'))}</code></p>
  <p><code>{esc(row.get('cues_json'))}</code></p>
</section>
"""
        (SITE / "talks" / f"{talk_index:02d}.html").write_text(page(row["title"], body, prefix="../"), encoding="utf-8")

    body = f"""
<section class="page-head">
  <p class="eyebrow">Talk index</p>
  <h1>DDPS Seminar Videos</h1>
  <p class="lede">Each seminar page shows transcript status and any selected evidence anchors.</p>
</section>
<div class="grid">{''.join(cards)}</div>
"""
    (SITE / "talks.html").write_text(page("Talks", body), encoding="utf-8")


def render_transcripts(index: list[dict[str, Any]]) -> None:
    rows = []
    for row in index:
        rows.append(
            f"""<tr>
  <td>{esc(row['index'])}</td>
  <td><a href="{esc(row['url'])}">{esc(row['title'])}</a></td>
  <td>{esc(row['transcript_status'])}</td>
  <td>{esc(row['source_tier'])}</td>
  <td>{row['word_count']:,}</td>
  <td><code>{esc(row.get('clean_txt'))}</code></td>
</tr>"""
        )
    body = f"""
<section class="page-head">
  <p class="eyebrow">Source index</p>
  <h1>Transcripts</h1>
  <p class="lede">Raw captions and clean transcripts are archived locally for review.</p>
</section>
<table>
  <thead><tr><th>#</th><th>Video</th><th>Status</th><th>Source Tier</th><th>Words</th><th>Clean Text</th></tr></thead>
  <tbody>{''.join(rows)}</tbody>
</table>
"""
    (SITE / "transcripts.html").write_text(page("Transcripts", body), encoding="utf-8")


def render_styles() -> None:
    css = """
:root { color-scheme: light; --ink: #1f2328; --muted: #59636e; --line: #d0d7de; --bg: #f6f8fa; --panel: #ffffff; --accent: #0a6b78; }
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); line-height: 1.55; }
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 14px 28px; border-bottom: 1px solid var(--line); background: #fff; position: sticky; top: 0; z-index: 2; }
.brand { font-weight: 750; color: var(--ink); }
nav { display: flex; gap: 14px; flex-wrap: wrap; font-size: 14px; }
main { max-width: 1180px; margin: 0 auto; padding: 32px 24px 64px; }
.hero, .page-head { border-bottom: 1px solid var(--line); padding-bottom: 24px; margin-bottom: 24px; }
.eyebrow { text-transform: uppercase; letter-spacing: .08em; color: var(--accent); font-weight: 800; font-size: 12px; margin: 0 0 8px; }
h1 { font-size: clamp(32px, 5vw, 58px); line-height: 1.02; margin: 0 0 14px; letter-spacing: 0; }
h2 { margin: 0 0 10px; font-size: 22px; }
h3 { margin: 0 0 8px; }
.lede { font-size: 19px; max-width: 880px; color: #34373b; }
.stats { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 12px; margin: 20px 0 30px; }
.stats article, .card, .detail, .evidence-item { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 18px; }
.button { display: inline-block; background: var(--ink); color: #fff; border-radius: 8px; padding: 9px 13px; font-weight: 700; }
.button:hover { text-decoration: none; background: #3b434b; }
.stats strong { display: block; font-size: 28px; }
.stats span, .quiet { color: var(--muted); font-size: 14px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }
.two-col { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; margin-bottom: 28px; }
.evidence-item { margin: 14px 0; }
blockquote { border-left: 4px solid var(--accent); margin: 12px 0; padding: 8px 14px; background: #eefaff; color: #16353a; }
.chip { display: inline-block; border: 1px solid var(--line); border-radius: 999px; padding: 4px 10px; margin: 2px; background: #fff; font-size: 13px; }
table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid var(--line); }
th, td { text-align: left; border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; }
code { font-size: 12px; overflow-wrap: anywhere; }
@media (max-width: 760px) { .topbar { align-items: flex-start; flex-direction: column; } .stats { grid-template-columns: repeat(2, 1fr); } main { padding: 24px 16px 48px; } }
"""
    (ASSETS / "styles.css").write_text(css.strip() + "\n", encoding="utf-8")


def main() -> int:
    SITE.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    (SITE / "concepts").mkdir(exist_ok=True)
    (SITE / "talks").mkdir(exist_ok=True)
    (SITE / "deep-dives").mkdir(exist_ok=True)
    for folder in [SITE / "concepts", SITE / "talks", SITE / "deep-dives"]:
        for stale in folder.glob("*.html"):
            stale.unlink()
    summary = load_json("raw-material/youtube/summary.json")
    index = load_json("raw-material/youtube/transcript-index.json")
    concepts = load_json("analysis/concepts/concept-atlas.json")
    evidence = load_json("analysis/evidence/evidence-ledger.json")
    deep_dives = load_json("analysis/deep-dives/deep-dives.json")
    evidence_by_id = {ev["id"]: ev for ev in evidence}
    concepts_by_id = {concept["id"]: concept for concept in concepts}
    talks_by_index = {int(row["index"]): row for row in index}
    render_styles()
    render_index(summary, concepts, evidence)
    render_deep_dives(deep_dives, talks_by_index)
    render_concepts(concepts, evidence_by_id)
    render_talks(index, evidence, deep_dives)
    render_evidence(evidence, concepts_by_id)
    render_transcripts(index)
    manifest = sorted(str(path.relative_to(SITE)) for path in SITE.rglob("*.html"))
    (SITE / "page-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(manifest)} html pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
