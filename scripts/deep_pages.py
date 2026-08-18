#!/usr/bin/env python3
"""Deep-page builder for the DDPS (data-driven physical simulation) Concept Lab.
Specs in analysis/deep/<id>.json -> site/concepts/<id>-deep.html."""
import html, json, re, sys
from pathlib import Path
def slugify(v): return re.sub(r"[^a-z0-9]+","-",v.lower()).strip("-")
ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "analysis" / "deep"
OUT = ROOT / "site"
HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_tab} · DDPS Concept Lab</title>
<link rel="stylesheet" href="../assets/styles.css">
<style>
.arc{{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0}}
.arc a{{font-size:12.5px;color:var(--accent);text-decoration:none;border:1px solid var(--line,#dcdcdc);border-radius:20px;padding:3px 10px;background:#fff}}
.fp{{border-top:1px solid var(--line,#dcdcdc);padding:22px 0 4px;margin-top:10px}}
.fp h2{{margin:6px 0 10px}}
.kick{{font-size:12px;color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.07em;margin:6px 0}}
.lede{{font-size:20px;color:#2c2c2c;max-width:820px}}
.essay p{{max-width:74ch;font-size:16.5px;margin:11px 0;color:#232323}}
.barrow{{display:flex;align-items:center;gap:10px;margin:5px 0;font-size:13px}}
.barrow .lab{{width:160px;font-family:ui-monospace,Menlo,monospace;font-size:12px;color:#5a5a5a;text-align:right}}
.bar{{height:16px;border-radius:3px;background:var(--accent);min-width:2px}}.bar.alt{{background:var(--accent-2,#7a3f2a)}}
.barrow .val{{font-family:ui-monospace,Menlo,monospace;font-size:12px}}
.eq{{font-family:ui-monospace,Menlo,monospace;font-size:13.5px;background:#eef3f7;border:1px solid var(--line,#dcdcdc);border-radius:6px;padding:12px 14px;margin:12px 0;overflow-x:auto;white-space:pre-wrap}}
.insight{{border-left:4px solid var(--accent);background:#eef3f7;padding:12px 16px;border-radius:0 8px 8px 0;margin:16px 0;font-size:16px}}
details.math{{border:1px solid var(--line,#dcdcdc);border-radius:8px;background:#fff;margin:14px 0}}
details.math summary{{cursor:pointer;padding:10px 13px;color:var(--accent);font-weight:750}}
details.math > div{{border-top:1px solid var(--line,#dcdcdc);padding:4px 14px 12px}}
figure{{margin:16px 0}}figcaption{{font-size:13px;color:#5a5a5a;margin-top:6px}}
table{{border-collapse:collapse;width:100%;background:#fff;border:1px solid var(--line,#dcdcdc)}}
th,td{{border:1px solid var(--line,#dcdcdc);padding:8px 11px;text-align:left;font-size:14.5px}}th{{background:#eef3f7}}
.tw{{overflow-x:auto}}
</style></head><body>
<header class="topbar"><a class="brand" href="../index.html">DDPS Concept Lab</a>
<nav><a href="../index.html">Overview</a><a href="../concepts.html">Concepts</a><a class="active" href="../deep-track.html">Deep Track</a><a href="{id}.html">This concept</a></nav></header>
<main>
<div class="kick">{kick}</div>
<h1>{h1}</h1>
<p class="lede">{lede}</p>
<div class="arc">{arc}</div>
"""
FOOT = """<footer style="color:#5a5a5a;font-size:13px;border-top:1px solid var(--line,#dcdcdc);padding:22px 0 60px;margin-top:24px">DDPS Concept Lab · {name} deep dive · every quantity here is computed. Experiments in scripts/experiments/ddps_run.py.</footer>
</main></body></html>
"""
def esc(s: str) -> str:
    return html.escape(str(s), quote=False)


def render_block(b: dict) -> str:
    t = b["t"]
    if t == "para":
        return f'      <p>{b["html"]}</p>'
    if t == "eq":
        return f'      <div class="eq">{esc(b["text"])}</div>'
    if t == "insight":
        return f'      <div class="insight">{b["html"]}</div>'
    if t == "table":
        head = "".join(f"<th>{esc(h)}</th>" for h in b["headers"])
        rows = ""
        for r in b["rows"]:
            rows += "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>"
        cap = f'<figcaption>{esc(b["caption"])}</figcaption>' if b.get("caption") else ""
        return f'      <div class="tw"><table><tr>{head}</tr>{rows}</table></div>{cap}'
    if t == "bars":
        rows = ""
        for row in b["rows"]:
            lab, val = row[0], row[2]
            try:
                frac = float(row[1])
            except (TypeError, ValueError):
                frac = 0.0            # informational row, no bar
            alt = " alt" if (len(row) > 3 and row[3]) else ""
            w = max(2, round(frac * 150))
            rows += (f'<div class="barrow"><span class="lab">{esc(lab)}</span>'
                     f'<div class="bar{alt}" style="width:{w}px"></div>'
                     f'<span class="val">{esc(val)}</span></div>')
        cap = f'<figcaption>{esc(b["caption"])}</figcaption>' if b.get("caption") else ""
        return f'      <figure>{rows}{cap}</figure>'
    raise ValueError(f"unknown block type {t}")


def render(spec: dict) -> str:
    arc = "".join(f'<a href="#{aid}">{esc(lbl)}</a>' for aid, lbl in spec.get("arc", []))
    arc += f'<a href="{spec["id"]}.html">Atlas card</a>'
    out = [HEAD.format(
        title_tab=esc(spec["name"]) + " (deep)",
        id=esc(spec["id"]),
        kick=esc(spec.get("kick", spec["name"] + " · first principles")),
        h1=esc(spec["title"]),
        lede=spec["lede"],
        arc=arc,
        name=esc(spec["name"]),
    )]
    for s in spec["sections"]:
        out.append(f'    <section class="fp" id="{esc(s["id"])}">')
        out.append(f'      <h2>{esc(s["h2"])}</h2>')
        out.append('      <div class="essay">')
        for b in s["blocks"]:
            out.append(render_block(b))
        out.append("      </div>")
        out.append("    </section>")
    if spec.get("connects"):
        BASES = {"aa203": "https://mehtama1234.github.io/stanford-aa203-optimal-learning-control-concepts-research/concepts/", "brunton": "https://mehtama1234.github.io/eigensteve-concepts-research/", "piml": "https://mehtama1234.github.io/physics-informed-machine-learning-concepts-research/topics/", "ddps": "https://mehtama1234.github.io/ddps-seminar-series-concepts-research/concepts/"}
        CLABEL = {"aa203": "AA203 · control", "brunton": "Brunton · data-driven", "piml": "physics-informed ML", "ddps": "DDPS · data-driven physics"}
        items = ""
        for c in spec["connects"]:
            course = c.get("course", "brunton")
            href = BASES[course] + esc(c["id"]) + "-deep.html"
            items += (f'<li style="margin:9px 0;padding-left:14px;border-left:3px solid #8b3f18">'
                      f'<a href="{href}" style="font-weight:700">{esc(c["label"])}</a>'
                      f' <span class="muted" style="font-size:13px">· {esc(CLABEL[course])}</span>'
                      f'<div style="font-size:14.5px;margin-top:3px">{c["note"]}</div></li>')
        out.append(
            '    <section class="fp" id="connects"><h2>Where this connects — across the machine</h2>'
            '<p class="muted">DDPS is the &ldquo;use the model&rdquo; layer &mdash; several of these ideas are the same object taught in a sister course. '
            'Links open the concept it mirrors, feeds, or is fed by, in the wider data&rarr;model&rarr;control pipeline.</p>'
            f'<ul style="list-style:none;padding:14px 16px;margin:12px 0;border:1px solid var(--line,#d7ddd9);border-radius:10px;background:#fff">{items}</ul></section>')
    if spec.get("related"):
        rel = " · ".join(f'<a href="{esc(h)}">{esc(l)}</a>' for h, l in spec["related"])
        out.append(f'    <section class="fp"><p class="muted">Related: {rel}</p></section>')
    if spec.get("recipe"):
        rc = spec["recipe"]
        out.append('    <details class="math"><summary>the run recipe — reproduce every number above</summary><div>')
        out.append(f'      <p class="muted">{esc(rc.get("summary",""))}</p>')
        if rc.get("eq"):
            out.append(f'      <div class="eq">{esc(rc["eq"])}</div>')
        if rc.get("note"):
            out.append(f'      <p class="muted">{esc(rc["note"])}</p>')
        out.append("    </div></details>")
    out.append(FOOT.format(name=esc(spec["name"])))
    return "\n".join(out)


def main():
    ids = sys.argv[1:] or [p.stem for p in SPECS.glob("*.json") if not p.stem.startswith("_")]
    n = 0
    for cid in ids:
        spec = json.loads((SPECS / f"{cid}.json").read_text())
        (OUT / "concepts" / f"{cid}-deep.html").write_text(render(spec))
        n += 1
    print(f"built {n} deep pages -> {OUT}")


if __name__ == "__main__":
    main()
