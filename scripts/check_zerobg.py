#!/usr/bin/env python3
"""Flag raw math / assumed-background symbols left in the MAIN FLOW of a deep spec.
Body = para/insight html, h2, lede. Equations are allowed ONLY in 'eq' blocks and 'recipe'."""
import json, re, sys

DEEP="/home/manishmehta/projects/ddps-seminar-series-concepts-research/analysis/deep"
# symbols/patterns that should NOT appear in body prose
BAD = [
    ("ᵀ", "transpose superscript"),
    ("⁻¹", "inverse superscript"),
    ("[[", "raw matrix literal"),
    ("]]", "raw matrix literal"),
    ("·P·", "quadratic form x·P·x"),
    ("Bᵀ", "matrix transpose"),
    ("Aᵀ", "matrix transpose"),
    ("γ", "raw gamma symbol"),
    ("λ", "raw lambda symbol"),
    ("∑", "sigma"),
    ("√", "sqrt"),
    ("θ", "theta"),
]
# term used with no nearby gloss is only a soft warning; hard-fail on symbols above
def body_texts(spec):
    out=[]
    out.append(("lede", spec.get("lede","")))
    for s in spec.get("sections",[]):
        out.append(("h2", s.get("h2","")))
        for b in s.get("blocks",[]):
            if b.get("t") in ("para","insight"):
                out.append((b["t"], b.get("html","")))
    return out

def main():
    ids = sys.argv[1:]
    total=0
    for cid in ids:
        spec=json.load(open(f"{DEEP}/{cid}.json"))
        hits=[]
        for where,txt in body_texts(spec):
            for sym,desc in BAD:
                if sym in txt:
                    snip=txt[max(0,txt.find(sym)-25):txt.find(sym)+25]
                    hits.append(f"    [{where}] {desc}: …{snip}…")
        if hits:
            total+=len(hits)
            print(f"✗ {cid}: {len(hits)} raw-symbol hits")
            for h in hits: print(h)
        else:
            print(f"✓ {cid}: no raw math in body")
    print(f"\nTOTAL raw-symbol hits in body: {total}")
    sys.exit(1 if total else 0)

if __name__=="__main__":
    main()
