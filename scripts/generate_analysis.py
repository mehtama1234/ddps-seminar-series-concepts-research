#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "raw-material" / "youtube" / "transcript-index.json"
CONCEPTS = ROOT / "analysis" / "concepts" / "concept-atlas.json"
EVIDENCE = ROOT / "analysis" / "evidence" / "evidence-ledger.json"

THEMES = [
    {
        "id": "physics-informed-learning",
        "name": "Physics-Informed Learning",
        "keywords": ["physics-informed", "pinn", "pinns", "physics informed", "differential equation", "pde", "ode"],
        "definition": "Physics-informed learning trains models while constraining them with known governing equations, conservation laws, boundary conditions, or residual penalties.",
        "problem": "Pure black-box models can fit data while violating physics, especially when measurements are sparse or extrapolation matters.",
        "first": "If the physical law is known, learning should search among functions that are consistent with that law rather than treating every data point as unconstrained supervision.",
    },
    {
        "id": "reduced-order-modeling",
        "name": "Reduced-Order Modeling",
        "keywords": ["reduced order", "rom", "model reduction", "manifold", "basis", "projection"],
        "definition": "Reduced-order modeling builds lower-dimensional surrogates of expensive physical simulations while preserving the dominant dynamics needed for prediction or control.",
        "problem": "High-fidelity simulations can be too slow for design loops, optimization, uncertainty quantification, or real-time control.",
        "first": "If the system's important states live near a lower-dimensional structure, computation can focus on that structure instead of repeatedly solving the full problem.",
    },
    {
        "id": "differentiable-simulation",
        "name": "Differentiable Simulation",
        "keywords": ["differentiable", "gradient", "adjoint", "backpropagation", "inverse", "optimization"],
        "definition": "Differentiable simulation exposes gradients through a simulator so parameters, controls, shapes, or models can be optimized using gradient-based methods.",
        "problem": "Many scientific and engineering tasks ask not only what happens, but what input would produce a desired outcome.",
        "first": "If a simulator maps causes to effects, differentiating that map tells us how to change the causes to improve the effect.",
    },
    {
        "id": "operator-learning",
        "name": "Operator Learning",
        "keywords": ["operator", "deeponet", "fourier neural operator", "fno", "neural operator", "functionals"],
        "definition": "Operator learning trains models to map between functions, such as from initial conditions or coefficients to full solution fields.",
        "problem": "A simulator often needs to solve a family of related PDE problems, not just predict one fixed vector output.",
        "first": "When inputs and outputs are functions, the learned object should approximate the solution operator that transforms one function into another.",
    },
    {
        "id": "fluid-mechanics-simulation",
        "name": "Fluid Mechanics Simulation",
        "keywords": ["fluid", "fluids", "navier", "stokes", "turbulence", "large eddy", "shock", "conservation law"],
        "definition": "Fluid mechanics simulation models flows, shocks, turbulence, and conservation laws using numerical methods, learned surrogates, or hybrid methods.",
        "problem": "Fluids create multiscale, nonlinear, instability-prone dynamics that are costly to simulate and difficult to learn robustly.",
        "first": "A flow model must respect transport, conservation, stability, and scale interactions; otherwise small errors can propagate into wrong dynamics.",
    },
    {
        "id": "hybrid-twins",
        "name": "Hybrid Twins",
        "keywords": ["hybrid twin", "digital twin", "twin", "hybrid", "physics", "data-driven"],
        "definition": "Hybrid twins combine mechanistic simulation with learned components and live data to represent, predict, and update physical systems.",
        "problem": "Pure simulation may miss unknown effects, while pure data models may fail outside observed regimes.",
        "first": "A useful twin should use physics for structure, data for correction, and online updates to stay aligned with the real system.",
    },
    {
        "id": "scientific-machine-learning",
        "name": "Scientific Machine Learning",
        "keywords": ["scientific machine learning", "sciml", "machine learning", "deep learning", "surrogate", "data-driven"],
        "definition": "Scientific machine learning uses ML to accelerate, infer, control, or augment models of physical, biological, and engineering systems.",
        "problem": "Scientific problems often have limited data, strong priors, expensive simulators, and high penalties for physically invalid predictions.",
        "first": "The learning problem should be designed around the scientific structure: equations, symmetries, measurements, uncertainty, and the decision the model will support.",
    },
    {
        "id": "uncertainty-and-robustness",
        "name": "Uncertainty And Robustness",
        "keywords": ["uncertainty", "robust", "robustness", "error", "stability", "generalization", "failure"],
        "definition": "Uncertainty and robustness address whether learned simulation models remain reliable under sparse data, out-of-distribution parameters, numerical error, and long rollouts.",
        "problem": "A surrogate can be accurate on average yet fail exactly where scientific or engineering decisions are most sensitive.",
        "first": "A model should communicate what it knows, remain stable under perturbations, and be tested where errors would change the conclusion.",
    },
    {
        "id": "inverse-problems-and-control",
        "name": "Inverse Problems And Control",
        "keywords": ["inverse", "control", "optimal control", "parameter estimation", "identification", "pde constrained"],
        "definition": "Inverse problems and control use observations or objectives to infer hidden parameters, states, forces, designs, or interventions.",
        "problem": "In practice we often observe effects and need to recover causes, or choose actions that make a physical system behave a desired way.",
        "first": "Forward simulation predicts consequences; inverse modeling and control use those predictions backward to infer causes or optimize decisions.",
    },
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z-]{2,}", text.lower())


def excerpt(text: str, keywords: list[str]) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    lower = compact.lower()
    hit_positions = [lower.find(keyword) for keyword in keywords if lower.find(keyword) >= 0]
    start = min(hit_positions) if hit_positions else 0
    start = max(0, start - 80)
    snippet = compact[start : start + 190]
    return re.sub(r"\s+", " ", snippet).strip()


def title_case_topic(title: str) -> str:
    clean = re.sub(r"^\s*DDPS\s*\|\s*", "", title)
    clean = re.sub(r"\([^)]*\)", "", clean)
    return re.sub(r"\s+", " ", clean).strip()


def main() -> int:
    rows = load_json(INDEX)
    available = [row for row in rows if row.get("transcript_status") == "available"]
    theme_hits: dict[str, list[dict[str, Any]]] = defaultdict(list)
    evidence: list[dict[str, Any]] = []

    for row in available:
        text = (ROOT / row["clean_txt"]).read_text(encoding="utf-8", errors="ignore")
        haystack = f"{row['title']} {text}".lower()
        for theme in THEMES:
            score = sum(haystack.count(keyword) for keyword in theme["keywords"])
            if score > 0:
                theme_hits[theme["id"]].append({"row": row, "score": score, "text": text})

    concepts: list[dict[str, Any]] = []
    for theme in THEMES:
        hits = sorted(theme_hits.get(theme["id"], []), key=lambda item: item["score"], reverse=True)
        if not hits:
            continue
        ev_ids = []
        for rank, hit in enumerate(hits[:3], start=1):
            row = hit["row"]
            ev_id = f"{theme['id']}-{rank:02d}"
            ev_ids.append(ev_id)
            evidence.append(
                {
                    "id": ev_id,
                    "lecture_index": int(row["index"]),
                    "video_id": row["id"],
                    "title": f"{theme['name']} in {title_case_topic(row['title'])}",
                    "url": row["url"],
                    "quote": excerpt(hit["text"], theme["keywords"]),
                    "source_tier": "youtube-caption",
                    "evidence_type": "title/transcript keyword support",
                    "supports_concepts": [theme["id"]],
                    "why_span_matters": f"This seminar is one of the strongest transcript matches for {theme['name'].lower()} in the DDPS playlist.",
                }
            )
        concepts.append(
            {
                "id": theme["id"],
                "name": theme["name"],
                "theme": "data-driven physical simulation",
                "plain_language_definition": theme["definition"],
                "ordinary_problem": theme["problem"],
                "naive_picture": "The naive view is that a neural network can simply replace a simulator once enough data is available.",
                "why_naive_fails": "Physical simulation problems mix equations, data, discretization, stability, uncertainty, and scientific validity. A generic ML benchmark can hide failures that matter in the real system.",
                "first_principles": theme["first"],
                "what_breaks_without_it": "Without this concept, it is easy to build a model that looks accurate on examples but fails under new parameters, longer time horizons, or scientific constraints.",
                "course_role": f"This theme organizes DDPS seminars related to {theme['name'].lower()} and gives us a first-pass route for later deep dives.",
                "evidence_ids": ev_ids,
            }
        )

    title_words = Counter()
    for row in rows:
        title_words.update(word for word in words(row["title"]) if word not in {"ddps", "seminar", "series", "with", "using", "towards"})

    CONCEPTS.write_text(json.dumps(concepts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    EVIDENCE.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "analysis" / "title-keywords.json").write_text(
        json.dumps(title_words.most_common(80), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(concepts)} concepts, {len(evidence)} evidence anchors from {len(available)} transcripts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
