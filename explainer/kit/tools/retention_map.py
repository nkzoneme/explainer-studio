#!/usr/bin/env python3
"""Map retention drops to the sentence and the picture they land on (IMPROVE_PLAN section 6). Usage:
  python3 retention_map.py --project <slug> --chapters film/<slug>/final/chapters.json (--csv studio.csv | --drops 83,2:10,412)
        [--duration S] [--script research/remake/<slug>/SCRIPT.md] [--video film/<slug>/final/<slug>_final.mp4] [--out DIR]
        [--window 15] [--min-drop 5] [--top 3]
Input: a YouTube Studio retention CSV (time or % position column plus an audience-retention column; ratio or percent) or a manual
list of drop times (seconds or m:ss). From a CSV the drops are the largest losses over --window seconds (default 15) of at least
--min-drop points (default 5), non-overlapping, top --top (default 3). Chapter start times come from chapters.json
([{ch,start}] or {"starts":[..]}); words from explainer/vo/<project>/chNN_w.words.json.
Output (printed, and DIR/retention_map.md + .json): per drop the time, chapter, the sentence spoken (and the one before), the
SCRIPT beat found by text match with its [visual] line and picture type (real media, document, chart, map, drawn, host, card), a
frame grab at the drop when --video is given, and a cause tag guess: list, card-only, number-chain, host, or untagged
(the operator confirms the tag; it feeds the rule 'change a rule only when three videos agree')."""
import argparse, csv, difflib, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def tsec(s):
    s = str(s).strip()
    if ":" in s:
        p = [float(x) for x in s.split(":")]
        return sum(v * 60 ** i for i, v in enumerate(reversed(p)))
    return float(s)


def fmt(t): return f"{int(t // 60)}:{t % 60:04.1f}"


def read_curve(path, duration):
    rows = list(csv.reader(open(path, newline="", encoding="utf-8-sig")))
    hdr = [h.lower() for h in rows[0]]
    ti = next((i for i, h in enumerate(hdr) if "elapsed" in h or "time" in h or "position" in h), 0)
    ri = next((i for i, h in enumerate(hdr) if "watch ratio" in h or "absolute" in h or "retention" in h), 1)
    pts = []
    for r in rows[1:]:
        try: pts.append((tsec(r[ti].replace("%", "")), float(r[ri].replace("%", ""))))
        except (ValueError, IndexError): continue
    if not pts: raise SystemExit("no numeric rows in the CSV")
    if "%" in hdr[ti] or (max(p[0] for p in pts) <= 1.0001 and duration):
        k = 100 if "%" in hdr[ti] else 1
        if not duration: raise SystemExit("position is a share of the video: pass --duration seconds")
        pts = [(t / k * duration, v) for t, v in pts]
    if max(v for _, v in pts) <= 1.5: pts = [(t, v * 100) for t, v in pts]
    return sorted(pts)


def find_drops(pts, window, min_drop, top):
    cand = []
    for i, (t, v) in enumerate(pts):
        j = max((k for k, p in enumerate(pts) if p[0] <= t + window), default=i)
        loss = v - pts[j][1]
        if loss >= min_drop: cand.append((loss, t, pts[j][0]))
    cand.sort(reverse=True); out = []
    for loss, t0, t1 in cand:
        if all(abs(t0 - o["t"]) > window for o in out): out.append({"t": (t0 + t1) / 2, "from": t0, "to": t1, "loss_points": round(loss, 1)})
        if len(out) >= top: break
    return sorted(out, key=lambda d: d["t"])


def load_chapters(path):
    j = json.loads(pathlib.Path(path).read_text())
    if isinstance(j, dict): j = [{"ch": f"ch{i + 1:02d}", "start": s} for i, s in enumerate(j["starts"])]
    return j


def load_words(project, chs):
    allw = []
    for i, c in enumerate(chs):
        p = ROOT / "vo" / project / f"{c['ch']}_w.words.json"
        if not p.exists(): continue
        for w in json.loads(p.read_text()): allw.append({"t": c["start"] + w["start"], "e": c["start"] + w["end"], "w": w["word"], "ch": c["ch"]})
    return allw


def sentence_at(allw, t):
    idx = next((i for i, w in enumerate(allw) if w["t"] <= t <= w["e"] + 0.3), None)
    if idx is None: idx = min(range(len(allw)), key=lambda i: abs(allw[i]["t"] - t))
    a = idx
    while a > 0 and not re.search(r"[.!?][\"')]*$", allw[a - 1]["w"]): a -= 1
    b = idx
    while b < len(allw) - 1 and not re.search(r"[.!?][\"')]*$", allw[b]["w"]): b += 1
    pa = a - 1
    while pa > 0 and not re.search(r"[.!?][\"')]*$", allw[pa - 1]["w"]): pa -= 1
    txt = lambda x, y: " ".join(w["w"] for w in allw[x:y + 1])
    return {"text": txt(a, b), "start": allw[a]["t"], "end": allw[b]["e"], "prev": txt(pa, a - 1) if a > 0 else "", "ch": allw[idx]["ch"]}


def script_beats(path):
    beats, cur = [], None
    for l in pathlib.Path(path).read_text(errors="ignore").splitlines():
        if l.startswith("###") or l.startswith("## "):
            cur = {"h": l.lstrip("# ").strip(), "say": "", "vis": ""}; beats.append(cur)
        elif cur is not None and l.startswith(">"): cur["say"] += " " + l.lstrip("> ")
        elif cur is not None and l.lstrip().startswith("- [visual]"): cur["vis"] += l.split("]", 1)[1].strip()
    return [b for b in beats if b["say"].strip()]


def norm(s): return re.sub(r"[^a-z0-9 ]", " ", s.lower())


def match_beat(beats, sent):
    best, br = None, 0
    ts = norm(sent)
    for b in beats:
        r = difflib.SequenceMatcher(None, ts, norm(b["say"])).find_longest_match(0, len(ts), 0, len(norm(b["say"]))).size / max(1, len(ts))
        if r > br: best, br = b, r
    return (best, br) if br >= 0.5 else (None, br)


def picture_type(vis):
    v = vis or ""
    kinds = []
    for tag, name in (("[M]", "real media"), ("[DOC]", "document"), ("[CHART]", "chart"), ("[MAP]", "map"), ("[HDL]", "headline"), ("[CARD]", "card")):
        if tag in v: kinds.append(name)
    if re.search(r"\bHOST\b|host", v): kinds.append("host")
    return kinds or (["drawn / unspecified"] if v else ["unknown (no script match)"])


def cause(sent, vis, kinds):
    tags = []
    if len(re.findall(r"\b(?:first|second|third|fourth|next|finally|number \w+)\b", sent.lower())) >= 2 or sent.count(",") >= 3: tags.append("list")
    nums = re.findall(r"\b(?:\d[\d,.]*|(?:one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion)\b)", sent.lower())
    if len(nums) >= 4: tags.append("number-chain")
    if "host" in kinds: tags.append("host")
    if set(kinds) <= {"document", "card", "headline"} and kinds and "unknown" not in kinds[0]: tags.append("card-only")
    return tags or ["untagged"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--chapters", required=True)
    ap.add_argument("--csv"); ap.add_argument("--drops"); ap.add_argument("--duration", type=float)
    ap.add_argument("--script"); ap.add_argument("--video"); ap.add_argument("--out"); ap.add_argument("--window", type=float, default=15); ap.add_argument("--min-drop", type=float, default=5); ap.add_argument("--top", type=int, default=3)
    a = ap.parse_args()
    chs = load_chapters(a.chapters); allw = load_words(a.project, chs)
    if not allw: sys.exit(f"no words.json found under {ROOT / 'vo' / a.project}")
    if a.csv: drops = find_drops(read_curve(a.csv, a.duration), a.window, a.min_drop, a.top)
    elif a.drops: drops = [{"t": tsec(x), "loss_points": None} for x in a.drops.split(",")]
    else: sys.exit("give --csv or --drops")
    sp = a.script or next((str(p) for p in (ROOT / "research" / "remake" / a.project / "SCRIPT.md", ROOT / "research" / a.project / "SCRIPT.md") if p.exists()), None)
    beats = script_beats(sp) if sp else []
    out = pathlib.Path(a.out) if a.out else ROOT / "film" / a.project / "final" / "retention"
    out.mkdir(parents=True, exist_ok=True)
    res, md = [], [f"# Retention map: {a.project}", "", "| Drop | Chapter | Sentence at the drop | Beat / picture | Cause tag |", "|---|---|---|---|---|"]
    for n, d in enumerate(drops, 1):
        t = d["t"]; ch = max((c for c in chs if c["start"] <= t), key=lambda c: c["start"])
        s = sentence_at(allw, t); b, r = match_beat(beats, s["text"])
        kinds = picture_type(b["vis"] if b else ""); ct = cause(s["text"], b["vis"] if b else "", kinds)
        frame = None
        if a.video:
            frame = out / f"drop{n}_{int(t)}s.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", a.video, "-frames:v", "1", "-vf", "scale=640:-1", str(frame)])
        rec = {"t": round(t, 1), "loss_points": d.get("loss_points"), "chapter": ch["ch"], "sentence": s["text"], "sentence_start": round(s["start"], 1), "previous": s["prev"],
               "beat": b["h"] if b else None, "match": round(r, 2), "visual": b["vis"] if b else None, "picture_type": kinds, "cause_tags": ct, "frame": str(frame) if frame else None}
        res.append(rec)
        md.append(f"| {fmt(t)}{' (-' + str(d['loss_points']) + ' pts)' if d.get('loss_points') else ''} | {ch['ch']} | \"{s['text'][:140]}\" | {(b['h'] + ': ' + b['vis'][:110]) if b else 'no script match'} [{', '.join(kinds)}] | {', '.join(ct)} |")
        print(f"drop {n} at {fmt(t)} ({ch['ch']}): \"{s['text'][:110]}\" | picture: {', '.join(kinds)} | tags: {', '.join(ct)}")
    (out / "retention_map.json").write_text(json.dumps(res, indent=1)); (out / "retention_map.md").write_text("\n".join(md) + "\n")
    print(f"-> {out}/retention_map.md")


if __name__ == "__main__":
    main()
