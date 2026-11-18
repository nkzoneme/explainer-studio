#!/usr/bin/env python3
"""Niche scanner: find long-form outlier videos per niche with yt-dlp (no API key).

Usage:
  .venv/bin/python yt_scan.py niches.json out_dir [--per-query 25] [--max-channels 25]

niches.json: {"niche name": ["search query 1", "search query 2", ...], ...}
Outputs out_dir/<niche>/videos.csv, channels.csv and out_dir/summary.md (+ summary.json).

Outlier score = video views / median views of that channel's last 30 uploads.
Only public metadata is read; requests are sequential with a small delay.
"""
from __future__ import annotations

import csv
import json
import re
import statistics
import sys
import time
from pathlib import Path

import yt_dlp

MIN_DURATION = 6 * 60          # long-form only
OPTS = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist", "skip_download": True}


def ydl_json(url: str, limit: int | None = None) -> dict:
    opts = dict(OPTS, playlistend=limit) if limit else OPTS
    with yt_dlp.YoutubeDL(opts) as y:
        return y.extract_info(url, download=False) or {}


def search(query: str, n: int) -> list[dict]:
    d = ydl_json(f"ytsearch{n}:{query}")
    return [e for e in d.get("entries") or [] if e]


def channel_stats(cid: str) -> dict:
    d = ydl_json(f"https://www.youtube.com/channel/{cid}/videos", limit=30)
    ents = [e for e in (d.get("entries") or [])[:30] if e]
    views = [e.get("view_count") or 0 for e in ents]
    longs = [e for e in ents if (e.get("duration") or 0) >= MIN_DURATION]
    return {
        "channel_id": cid,
        "channel": d.get("channel") or d.get("uploader") or d.get("title"),
        "subs": d.get("channel_follower_count"),
        "recent_videos": len(ents),
        "median_views": int(statistics.median(views)) if views else 0,
        "max_views": max(views) if views else 0,
        "long_share": round(len(longs) / len(ents), 2) if ents else 0,
    }


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def write_summary(out: Path, summary: list[dict]) -> None:
    json.dump(summary, open(out / "summary.json", "w"), indent=1, ensure_ascii=False)
    lines = ["| Niche | Long-form videos | Median views | ≥100k | Small-channel outliers | <1k views share |", "|---|---|---|---|---|---|"]
    for s in sorted(summary, key=lambda s: s["small_channel_outliers"], reverse=True):
        lines.append(f'| {s["niche"]} | {s["longform_videos"]} | {s["median_views"]:,} | {s["videos_100k_plus"]} | {s["small_channel_outliers"]} | {s["zero_traction_share"]:.0%} |')
    for s in summary:
        if s["top_small_hits"]:
            lines += ["", f'**{s["niche"]}** — small channels that broke out:'] + [f"- {h}" for h in s["top_small_hits"]]
    (out / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    niches = json.load(open(sys.argv[1]))
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    per_q = int(sys.argv[sys.argv.index("--per-query") + 1]) if "--per-query" in sys.argv else 25
    max_ch = int(sys.argv[sys.argv.index("--max-channels") + 1]) if "--max-channels" in sys.argv else 25
    cache_p = out / "channel_cache.json"
    cache = json.load(open(cache_p)) if cache_p.exists() else {}
    summary = []
    for niche, queries in niches.items():
        vids: dict[str, dict] = {}
        for q in queries:
            for e in search(q, per_q):
                if (e.get("duration") or 0) >= MIN_DURATION and e.get("id") not in vids:
                    vids[e["id"]] = {"id": e["id"], "title": e.get("title"), "views": e.get("view_count") or 0,
                                     "minutes": round((e.get("duration") or 0) / 60, 1),
                                     "channel": e.get("channel"), "channel_id": e.get("channel_id"), "query": q}
            time.sleep(1)
        # channels ranked by best video views
        best: dict[str, int] = {}
        for v in vids.values():
            if v["channel_id"]:
                best[v["channel_id"]] = max(best.get(v["channel_id"], 0), v["views"])
        for cid in sorted(best, key=best.get, reverse=True)[:max_ch]:
            if cid not in cache:
                try:
                    cache[cid] = channel_stats(cid)
                except Exception as ex:  # private/terminated channels etc.
                    cache[cid] = {"channel_id": cid, "error": str(ex)[:120]}
                json.dump(cache, open(cache_p, "w"))
                time.sleep(1)
        rows = []
        for v in vids.values():
            c = cache.get(v["channel_id"] or "", {})
            med = c.get("median_views") or 0
            v.update(subs=c.get("subs"), ch_median=med, outlier=round(v["views"] / max(med, 1000), 1) if c else None)
            rows.append(v)
        rows.sort(key=lambda r: r["views"], reverse=True)
        d = out / slug(niche); d.mkdir(exist_ok=True)
        with open(d / "videos.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["id"]); w.writeheader(); w.writerows(rows)
        chans = [cache[c] for c in best if c in cache]
        with open(d / "channels.csv", "w", newline="") as fh:
            keys = ["channel", "channel_id", "subs", "recent_videos", "median_views", "max_views", "long_share", "error"]
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(chans)
        scored = [r for r in rows if r["outlier"] is not None]
        small_hits = [r for r in scored if (r["subs"] or 0) < 100_000 and r["outlier"] >= 5 and r["views"] >= 50_000]
        summary.append({
            "niche": niche,
            "longform_videos": len(rows),
            "channels": len(best),
            "median_views": int(statistics.median([r["views"] for r in rows])) if rows else 0,
            "videos_100k_plus": sum(r["views"] >= 100_000 for r in rows),
            "small_channel_outliers": len(small_hits),
            "zero_traction_share": round(sum(r["views"] < 1000 for r in rows) / len(rows), 2) if rows else 0,
            "top_small_hits": [f'{r["title"]} — {r["channel"]} ({r["views"]:,} views, {r["subs"] or "?"} subs, x{r["outlier"]})'
                               for r in sorted(small_hits, key=lambda r: r["outlier"], reverse=True)[:5]],
        })
        write_summary(out, summary)
        print(f"[{niche}] {len(rows)} long-form videos, {len(best)} channels, {len(small_hits)} small-channel outliers", flush=True)
    write_summary(out, summary)
    print((out / "summary.md").read_text())


if __name__ == "__main__":
    main()
