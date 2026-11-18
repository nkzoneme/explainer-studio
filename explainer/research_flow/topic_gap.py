#!/usr/bin/env python3
"""Gap check for candidate video topics: is there already a strong long-form video on it?

Usage: .venv/bin/python topic_gap.py candidates.json out.csv [--per-query 15]
candidates.json: [{"id": "t1", "title": "Why Everyone Pays ARM?", "queries": ["arm royalties explained", ...]}, ...]

For each candidate, searches YouTube (yt-dlp, no API key) and records the strongest existing long-form
videos. gap_score is high when demand exists in the niche but nobody has a strong, recent video on it.
"""
from __future__ import annotations

import csv
import json
import sys
import time

import yt_dlp

MIN_DURATION = 6 * 60
OPTS = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist", "skip_download": True}


def search(q: str, n: int) -> list[dict]:
    with yt_dlp.YoutubeDL(OPTS) as y:
        d = y.extract_info(f"ytsearch{n}:{q}", download=False) or {}
    return [e for e in d.get("entries") or [] if e and (e.get("duration") or 0) >= MIN_DURATION]


def main() -> None:
    cands = json.load(open(sys.argv[1]))
    per_q = int(sys.argv[sys.argv.index("--per-query") + 1]) if "--per-query" in sys.argv else 15
    rows = []
    for c in cands:
        seen = {}
        for q in c.get("queries") or [c["title"]]:
            for e in search(q, per_q):
                seen[e["id"]] = e
            time.sleep(1)
        vids = sorted(seen.values(), key=lambda e: e.get("view_count") or 0, reverse=True)
        top = vids[0] if vids else {}
        top_views = top.get("view_count") or 0
        strong = sum((v.get("view_count") or 0) >= 100_000 for v in vids)
        # crude: no strong video -> big gap; one huge video -> proven demand but crowded
        gap = 1.0 if strong == 0 else 0.6 if strong == 1 else 0.3 if strong <= 3 else 0.1
        rows.append({
            "id": c["id"], "title": c["title"], "longform_results": len(vids),
            "videos_100k_plus": strong, "top_views": top_views,
            "top_video": f'{top.get("title", "")} — {top.get("channel", "")} (https://youtu.be/{top.get("id", "")})' if top else "",
            "gap_score": gap,
        })
        print(f'[{c["id"]}] {c["title"][:60]} -> {len(vids)} long-form, {strong} ≥100k, top {top_views:,}', flush=True)
    with open(sys.argv[2], "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
