# DDPS Seminar Series Concept Research

Local transcript-backed concept lab for the YouTube playlist:

https://www.youtube.com/playlist?list=PLy9rIbGDXrG2Ly0LPYNuNn1ohQTqO6mmp

## Current State

- Playlist: Data-driven Physical Simulations (DDPS) Seminar Series
- Visible videos: 141
- Usable transcripts: 139
- Transcript words: 1,397,488
- First-pass concepts: 9
- Detailed deep dives: 5
- Evidence anchors: 27
- Static HTML pages: 161

## End-to-End Goal

Turn the full 141-video DDPS Seminar Series playlist into a transcript-backed first-principles study system:

- Preserve transcripts and metadata for every available video.
- Write detailed lecture-by-lecture primers and deep dives for all usable talks.
- Extract the core concepts, assumptions, equations, failure modes, and practical cautions discussed in each lecture.
- Connect recurring ideas across the series, including PINNs, ROMs, differentiable simulation, operator learning, inverse problems, uncertainty, and hybrid physics-ML systems.
- Keep the generated HTML site valid, browsable, and tied back to transcript evidence.
- Commit and push progress in focused batches so the work can be reviewed incrementally.

## Entry Points

- `site/index.html`
- `site/concepts.html`
- `site/talks.html`
- `site/transcripts.html`

## Gaps

- Talk 37 has an unusably short caption.
- Talk 123 has no usable caption.

## Workflow

```bash
python3 scripts/download_youtube_transcripts.py
python3 scripts/generate_analysis.py
python3 scripts/build_site.py
python3 scripts/validate_all.py
```
