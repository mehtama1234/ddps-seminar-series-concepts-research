#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COURSE_SLUG = "ddps-seminar-series"
COURSE_TITLE = "Data-driven Physical Simulations (DDPS) Seminar Series"
SOURCE_URL = "https://www.youtube.com/playlist?list=PLy9rIbGDXrG2Ly0LPYNuNn1ohQTqO6mmp"

RAW = ROOT / "raw-material" / "youtube"
PLAYLIST_MANIFEST = RAW / "playlist.json"
BASE = RAW / "transcripts" / COURSE_SLUG
RAW_VTT = BASE / "raw-vtt"
CLEAN = BASE / "clean"
CUES = BASE / "cues"
META = RAW / "metadata" / COURSE_SLUG
SUMMARY = RAW / "summary.json"
INDEX = RAW / "transcript-index.json"


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check)


def slugify(value: str) -> str:
    value = value.replace("|", " ")
    value = re.sub(r"[^\w .:()&,'-]+", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:130]


def parse_seconds(value: str) -> float:
    parts = value.split(":")
    if len(parts) == 2:
        minutes, rest = parts
        return int(minutes) * 60 + float(rest)
    hours, minutes, rest = parts
    return int(hours) * 3600 + int(minutes) * 60 + float(rest)


def clean_caption_line(line: str) -> str:
    line = re.sub(r"<[^>]+>", "", line)
    line = (
        line.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    return re.sub(r"\s+", " ", line).strip()


def parse_vtt(path: Path) -> tuple[str, list[dict[str, Any]]]:
    cues: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    text_lines: list[str] = []

    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE")):
            continue
        if "-->" in line:
            start, end = [part.strip().split(" ")[0] for part in line.split("-->", 1)]
            current = {
                "start": start,
                "end": end,
                "start_seconds": parse_seconds(start),
                "end_seconds": parse_seconds(end),
                "text": [],
            }
            cues.append(current)
            continue
        if re.match(r"^\d+$", line):
            continue
        cleaned = clean_caption_line(line)
        if not cleaned:
            continue
        if current is not None and (not current["text"] or current["text"][-1] != cleaned):
            current["text"].append(cleaned)
        text_lines.append(cleaned)

    compact_cues: list[dict[str, Any]] = []
    for cue in cues:
        joined = " ".join(cue["text"]).strip()
        if joined:
            compact_cues.append({**cue, "text": joined})

    deduped: list[str] = []
    for line in text_lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return "\n".join(deduped).strip() + "\n", compact_cues


def choose_vtt(video_id: str) -> Path | None:
    candidates = sorted(RAW_VTT.glob(f"*{video_id}*.vtt"))
    if not candidates:
        return None
    ranked: list[tuple[int, Path]] = []
    for path in candidates:
        name = path.name
        if ".en-j3PyPqV-e1s." in name or ".en." in name:
            rank = 0
        elif ".en-orig." in name or ".en-US." in name:
            rank = 1
        else:
            rank = 5
        ranked.append((rank, path))
    return sorted(ranked, key=lambda item: (item[0], item[1].name))[0][1]


def capture_playlist() -> dict[str, Any]:
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--dump-single-json", SOURCE_URL],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    manifest = json.loads(result.stdout)
    manifest.pop("epoch", None)
    PLAYLIST_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    PLAYLIST_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def playlist_videos() -> list[dict[str, Any]]:
    if not PLAYLIST_MANIFEST.exists():
        return []
    manifest = json.loads(PLAYLIST_MANIFEST.read_text(encoding="utf-8"))
    videos: list[dict[str, Any]] = []
    for index, entry in enumerate(manifest.get("entries", []), 1):
        video_id = entry["id"]
        videos.append(
            {
                "index": entry.get("playlist_index") or index,
                "id": video_id,
                "title": entry.get("title") or f"Video {index}",
                "url": entry.get("url") or f"https://www.youtube.com/watch?v={video_id}",
                "duration": entry.get("duration"),
                "view_count": entry.get("view_count"),
            }
        )
    return videos


def download() -> None:
    for path in [RAW_VTT, CLEAN, CUES, META]:
        path.mkdir(parents=True, exist_ok=True)
    capture_playlist()
    output = str(RAW_VTT / "%(playlist_index|001)03d-%(id)s-%(title).130B.%(ext)s")
    cmd = [
        "yt-dlp",
        "--ignore-errors",
        "--skip-download",
        "--write-info-json",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        "en,en-US,en-orig,en.*",
        "--sub-format",
        "vtt",
        "-o",
        output,
        SOURCE_URL,
    ]
    print(run(cmd, check=False).stdout)
    for info in RAW_VTT.glob("*.info.json"):
        target = META / info.name
        if target.exists():
            target.unlink()
        info.replace(target)


def rebuild_index() -> None:
    records: list[dict[str, Any]] = []
    for video in playlist_videos():
        video_id = video["id"]
        vtt = choose_vtt(video_id)
        transcript_status = "missing"
        clean_path = None
        cue_path = None
        word_count = 0
        cue_count = 0
        if vtt is not None:
            text, cues = parse_vtt(vtt)
            clean_path = CLEAN / f"{video['index']:03d}-{video_id}-{slugify(video['title'])}.txt"
            cue_path = CUES / f"{video['index']:03d}-{video_id}.json"
            clean_path.write_text(text, encoding="utf-8")
            cue_path.write_text(json.dumps(cues, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            word_count = len(re.findall(r"\b\w+\b", text))
            cue_count = len(cues)
            transcript_status = "available" if word_count >= 50 else "unusable"

        meta_files = sorted(META.glob(f"*{video_id}*.info.json"))
        records.append(
            {
                "course_slug": COURSE_SLUG,
                "source_url": SOURCE_URL,
                "index": video["index"],
                "id": video_id,
                "title": video["title"],
                "url": video["url"],
                "duration": video.get("duration"),
                "view_count": video.get("view_count"),
                "transcript_status": transcript_status,
                "source_tier": "youtube-caption" if transcript_status == "available" else "missing",
                "raw_vtt": str(vtt.relative_to(ROOT)) if vtt else None,
                "clean_txt": str(clean_path.relative_to(ROOT)) if clean_path else None,
                "cues_json": str(cue_path.relative_to(ROOT)) if cue_path else None,
                "metadata_json": str(meta_files[0].relative_to(ROOT)) if meta_files else None,
                "word_count": word_count,
                "cue_count": cue_count,
            }
        )

    summary = {
        "course_slug": COURSE_SLUG,
        "course_title": COURSE_TITLE,
        "source_url": SOURCE_URL,
        "video_count": len(records),
        "transcript_count": sum(1 for row in records if row["transcript_status"] == "available"),
        "word_count": sum(row["word_count"] for row in records),
        "videos": records,
    }
    INDEX.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {INDEX.relative_to(ROOT)} with {summary['transcript_count']}/"
        f"{summary['video_count']} transcripts and {summary['word_count']} words"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    if not args.summary_only:
        download()
    rebuild_index()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
