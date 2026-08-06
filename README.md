# DDPS Seminar Series Concept Research

Local transcript-backed concept lab for the YouTube playlist:

https://www.youtube.com/playlist?list=PLy9rIbGDXrG2Ly0LPYNuNn1ohQTqO6mmp

## Current State

- Playlist: Data-driven Physical Simulations (DDPS) Seminar Series
- Visible videos: 141
- Usable transcripts: 139
- Transcript words: 1,397,488
- First-pass concepts: 9
- Evidence anchors: 27
- Static HTML pages: 156

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

