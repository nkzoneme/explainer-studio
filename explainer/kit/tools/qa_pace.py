#!/usr/bin/env python3
"""Shot-rate check for a rendered chapter, a joined film, or any reference video. Usage:
  python3 qa_pace.py <video.mp4> [max_gap_seconds] [--style explainer/channels/<slug>/style.json] [--json]
  python3 qa_pace.py <video.mp4> --channel <slug>          (same as --style explainer/channels/<slug>/style.json)

Counts FULL-FRAME CHANGES: moments where more than 20 % of the picture changes within 0.2 s (a cut, a
punch-in, a whip/wipe, a full-frame insert). A prop popping in or a label does not count; a slow camera
push does not count. Also prints the share of runtime that is near-still for 1 s or more (a talking mouth or a small float counts as still; this is a style measure, qa_freeze.sh is the dead-picture test).

Targets come from the channel's style.json, key "pace" (see explainer/channels/README.md):
  shot_changes_per_min.{min,max}, first_60s_per_min_min, median_gap_max_s, long_gap_s, max_gap_s, still_share_max
Without a style the house DEFAULTS below are used and the output says so. They are defaults only: each
channel's style sets its own range from its competitors (skill explainer-channel-style).
--json prints one JSON object (used by research_flow/channel_style_scan.py).
Needs ffmpeg and numpy (system python3)."""
import json, pathlib, subprocess, sys
import numpy as np

W, H, FPS = 96, 54, 5
ROOT = pathlib.Path(__file__).resolve().parents[2]          # .../explainer
DEFAULTS = {"min_per_min": 10.0, "first_60s_min": 14.0, "median_gap_max_s": 6.0, "long_gap_s": 12.0, "max_gap_s": 20.0}


def measure(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={FPS},scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    f = np.frombuffer(raw, dtype=np.uint8).reshape(-1, H, W).astype(np.int16)
    dur = len(f) / FPS
    changed = (np.abs(f[1:] - f[:-1]) > 24).mean(axis=(1, 2))  # share of pixels that moved by > 24 levels in one 0.2 s step

    def events(mask, refractory=0.8):
        out, last = [], -1e9
        for i in np.nonzero(mask)[0]:
            t = (i + 1) / FPS
            if t - last >= refractory:
                out.append(t)
            last = t
        return out

    shots = events(changed > 0.20)
    cuts = events(changed > 0.45)
    # frozen: runs of >= 1 s where under 0.3 % of pixels change per step
    still = changed < 0.003
    frozen_steps, run = 0, 0
    for s in list(still) + [False]:
        if s:
            run += 1
        else:
            if run >= FPS:
                frozen_steps += run
            run = 0
    edges = [0.0] + shots + [dur]
    gaps = np.diff(edges)
    first = min(dur, 60.0)
    return {
        "file": str(path), "duration_s": round(dur, 1),
        "changes": len(shots), "per_min": round(len(shots) / dur * 60, 1),
        "hard_cuts_per_min": round(len(cuts) / dur * 60, 1),
        "first_60s_per_min": round(len([t for t in shots if t < first]) / first * 60, 1),
        "median_gap_s": round(float(np.median(gaps)), 1), "p90_gap_s": round(float(np.percentile(gaps, 90)), 1),
        "longest_gap_s": round(float(gaps.max()), 1), "still_share": round(frozen_steps / max(1, len(changed)), 3),
        "gaps": [(round(edges[i], 1), round(float(gaps[i]), 1)) for i in range(len(gaps))],
    }


def targets(style_path):
    if not style_path:
        return dict(DEFAULTS), "house defaults (no channel style given)"
    s = json.loads(pathlib.Path(style_path).read_text())
    p = s.get("pace", {})
    t = dict(DEFAULTS)
    rng = p.get("shot_changes_per_min", {})
    if "min" in rng: t["min_per_min"] = rng["min"]
    if "max" in rng: t["max_per_min"] = rng["max"]
    for k in ("first_60s_per_min_min", "median_gap_max_s", "long_gap_s", "max_gap_s", "still_share_max"):
        if k in p: t[k.replace("_per_min_min", "_min")] = p[k]
    return t, f"channel style {s.get('channel', style_path)} ({style_path})"


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    style = None
    if "--style" in args:
        style = args[args.index("--style") + 1]
    if "--channel" in args:
        style = str(ROOT / "channels" / args[args.index("--channel") + 1] / "style.json")
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] not in ("--style", "--channel"))]
    path = pos[0]
    m = measure(path)
    t, src = targets(style)
    if len(pos) > 1:
        t["long_gap_s"] = float(pos[1])
    if as_json:
        m["targets"], m["targets_from"] = t, src
        print(json.dumps(m))
        return
    fmt = lambda s: f"{int(s // 60)}:{s % 60:04.1f}"
    dur = m["duration_s"]
    print(f"{path}: {dur:.1f} s")
    print(f"full-frame changes: {m['changes']} = {m['per_min']:.1f} per minute (hard cuts >45 % of picture: {m['hard_cuts_per_min']:.1f} per minute)")
    print(f"first {min(dur, 60):.0f} s: {m['first_60s_per_min']:.1f} per minute | near-still >= 1 s: {m['still_share'] * 100:.0f} % of runtime")
    print(f"gap between changes: median {m['median_gap_s']:.1f} s, 90th percentile {m['p90_gap_s']:.1f} s, longest {m['longest_gap_s']:.1f} s")
    long_gaps = [(t0, g) for t0, g in m["gaps"] if g > t["long_gap_s"]]
    for t0, g in long_gaps:
        print(f"  same framing for {g:.1f} s from {fmt(t0)}")
    print(f"targets from {src}:")
    ok_rate = m["per_min"] >= t["min_per_min"]
    hi = t.get("max_per_min")
    rate = f">= {t['min_per_min']:g}" + (f" and <= {hi:g}" if hi else "") + " per minute "
    rate += "ok" if ok_rate and (not hi or m["per_min"] <= hi) else ("LOW" if not ok_rate else "HIGH (busier than the channel style)")
    too_long = len([g for _, g in long_gaps if g > t["max_gap_s"]])
    print(f"  {rate} | median gap <= {t['median_gap_max_s']:g} s {'ok' if m['median_gap_s'] <= t['median_gap_max_s'] else 'LONG'}"
          f" | gaps over {t['long_gap_s']:g} s: {len(long_gaps)} (each needs a reason in the plan) | over {t['max_gap_s']:g} s: {too_long if too_long else 'none'}"
          + (f" | first 60 s >= {t['first_60s_min']:g} per minute {'ok' if m['first_60s_per_min'] >= t['first_60s_min'] else 'LOW'} (films and chapter 1 only)" if dur >= 30 else "")
          + (f" | near-still <= {t['still_share_max'] * 100:.0f} % {'ok' if m['still_share'] <= t['still_share_max'] else 'HIGH'}" if "still_share_max" in t else ""))


if __name__ == "__main__":
    main()
