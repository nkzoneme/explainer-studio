#!/usr/bin/env python3
"""Measure competitor channels for a channel style (skill: explainer-channel-style).

Usage (system python3: needs numpy and ffmpeg; yt-dlp is called from research_flow/.venv):
  python3 channel_style_scan.py competitors.json OUT_DIR [--per 2] [--list-only] [--only <name substring>]

competitors.json:
  {"channel": "My Channel", "niche": "how famous brands make money",
   "competitors": [{"name": "Wendover Productions", "url": "https://www.youtube.com/@Wendoverproductions",
                    "size": "large", "filter": "(?i)brand|company|money", "videos": ["optional ids"], "min_minutes": 6,
                    "skip": false, "note": "why it is in or out"}]}

Per competitor it writes OUT_DIR/<slug>/:
  channel.json   last 30 long uploads (title, views, minutes, title family), median views, subscribers,
                 uploads per 30 days (from the channel RSS feed), the picked videos' metrics
  <id>.json      per picked video: qa_pace numbers, words per minute, contrast turns and questions per minute,
                 words in the first 30 s, hook text (first 60 s of captions), chapters, music-bed level
  <id>_sheet.jpg 30 evenly spaced frames (6x5), for host/presenter share and media mix by eye
  <id>_thumb.jpg the video's thumbnail; thumbs.jpg = the six most-viewed recent thumbnails
The downloaded video (240p) and caption files are deleted after measuring. OUT_DIR/table.md sums it up.
Picks: the `per` most-viewed long uploads among the last 30 (after `filter`), unless `videos` is given.
Requests are sequential with sleeps; YouTube rate-limits captions (HTTP 429) after about a dozen in a row. Captions are\nfetched in a second call, so a 429 only costs the caption numbers (words per minute, contrast, hook text); re-run later.
Never reads .env; sends nothing but public video URLs to YouTube."""
import json, pathlib, re, statistics, subprocess, sys, time, urllib.request, xml.etree.ElementTree as ET
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
YTDLP = [str(HERE / ".venv/bin/python"), "-m", "yt_dlp"]
QA_PACE = HERE.parent / "kit/tools/qa_pace.py"
CONTRAST = re.compile(r"\b(but|except|until|instead|however|yet)\b", re.I)

FAMILIES = [  # first match wins; rough, for counting a channel's title habits
    ("versus/impossible", re.compile(r"\b(vs\.?|versus|can'?t|cannot|impossible|no one|nobody|never)\b", re.I)),
    ("why/how", re.compile(r"^(why|how)\b|\b(why|how)\b.*\b(is|are|did|do|does|was|were|can)\b", re.I)),
    ("number", re.compile(r"[$£€]?\d")),
    ("story/hidden", re.compile(r"\b(inside|secret|hidden|story|truth|real reason|what happened|rise|fall|collapse|downfall|hack|hacked)\b", re.I)),
]


def family(title):
    for name, rx in FAMILIES:
        if rx.search(title):
            return name
    return "statement/other"


def run(cmd, text=True):
    return subprocess.run(cmd, capture_output=True, text=text)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def list_channel(url):
    r = run(YTDLP + ["--flat-playlist", "-J", "--playlist-end", "30", url.rstrip("/") + "/videos"])
    if r.returncode:
        raise RuntimeError(r.stderr[-400:])
    return json.loads(r.stdout)


def rss_dates(cid):
    try:
        x = urllib.request.urlopen(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", timeout=30).read()
    except Exception:
        return {}
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    out = {}
    for e in ET.fromstring(x).findall("a:entry", ns):
        out[e.find("yt:videoId", ns).text] = e.find("a:published", ns).text[:10]
    return out


def captions(base):
    for f in sorted(base.parent.glob(base.name + ".*.json3")):
        d = json.loads(f.read_text())
        words = []
        for ev in d.get("events", []):
            t0 = ev.get("tStartMs", 0)
            segs = ev.get("segs") or []
            for s in segs:
                txt = (s.get("utf8") or "").strip()
                if not txt:
                    continue
                for w in txt.split():
                    words.append(((t0 + s.get("tOffsetMs", 0)) / 1000, w))
        if words:
            return words, f.name
    return [], None


def audio_bed(path, words):
    """Median level in speech gaps minus median level during speech (dB). About -35 or lower: no bed.
    About -20 to -10: a music bed or ambience runs under the voice. Rough: caption timings are approximate."""
    if len(words) < 50:
        return None
    raw = run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], text=False).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    hop = 400  # 50 ms
    n = len(a) // hop
    if n < 100:
        return None
    rms = 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-6)
    speech = np.zeros(n, bool)
    ts = [t for t, _ in words]
    for i, t in enumerate(ts):
        end = min(ts[i + 1] if i + 1 < len(ts) else t + 0.5, t + 0.7)
        speech[int(t * 20): int(end * 20) + 3] = True
    gap = ~speech
    # keep gaps of 0.4 s or more inside the speaking span
    first, last = int(ts[0] * 20), int(ts[-1] * 20)
    gm = np.zeros(n, bool)
    i = first
    while i < last:
        if gap[i]:
            j = i
            while j < last and gap[j]:
                j += 1
            if j - i >= 8:
                gm[i + 2: j - 2] = True
            i = j
        else:
            i += 1
    if gm.sum() < 20:
        return None
    return round(float(np.median(rms[gm]) - np.median(rms[speech[:n]])), 1)


def measure_video(vid, d, sleep):
    url = f"https://www.youtube.com/watch?v={vid}"
    base = d / vid
    have = [p for p in d.glob(vid + ".*") if p.suffix in (".mkv", ".mp4", ".webm")] and pathlib.Path(str(base) + ".info.json").exists()
    r = None if have else run(YTDLP + ["-f", "bv*[height<=240]+ba[abr<=80]/bv*[height<=240]+ba/b[height<=360]", "--merge-output-format", "mkv",
                     "--write-info-json", "-o", str(base) + ".%(ext)s", url])
    if not list(d.glob(vid + ".*.json3")):  # captions separately: a 429 here must not cost the video
        time.sleep(sleep)
        run(YTDLP + ["--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "en,en-orig", "--sub-format", "json3",
                     "-o", str(base) + ".%(ext)s", url])
    info_f = pathlib.Path(str(base) + ".info.json")
    vids = [p for p in d.glob(vid + ".*") if p.suffix in (".mkv", ".mp4", ".webm")]
    if not vids or not info_f.exists():
        return {"id": vid, "error": (r.stderr if r else "no file")[-300:]}
    v = vids[0]
    info = json.loads(info_f.read_text())
    m = {"id": vid, "title": info.get("title"), "views": info.get("view_count"), "upload_date": info.get("upload_date"),
         "minutes": round((info.get("duration") or 0) / 60, 1), "chapters": [(round(c["start_time"]), c["title"]) for c in info.get("chapters") or []]}
    q = run(["python3", str(QA_PACE), str(v), "--json"])
    if q.returncode == 0:
        p = json.loads(q.stdout)
        p.pop("gaps", None); p.pop("targets", None); p.pop("targets_from", None); p.pop("file", None)
        m["pace"] = p
    words, cap = captions(base)
    if words:
        span = max(1.0, words[-1][0] - words[0][0])
        text = " ".join(w for _, w in words)
        m["captions"] = cap
        m["wpm"] = round(len(words) / span * 60)
        m["contrast_per_min"] = round(len(CONTRAST.findall(text)) / span * 60, 2)
        m["questions_per_min"] = round(text.count("?") / span * 60, 2)  # ASR captions often lack "?": treat as a floor
        m["words_first_30s"] = len([1 for t, _ in words if t < 30])
        m["first_speech_s"] = round(words[0][0], 1)
        m["hook_text"] = " ".join(w for t, w in words if t < 60)
        m["last_text"] = " ".join(w for t, w in words if t > words[-1][0] - 30)
        try:
            m["music_bed_db"] = audio_bed(v, words)
        except Exception as e:
            m["music_bed_db"] = None; m["music_bed_error"] = str(e)[:120]
    dur = info.get("duration") or 1
    run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-vf", f"fps=30/{dur},scale=320:-2,tile=6x5", "-frames:v", "1", str(d / f"{vid}_sheet.jpg")])
    if info.get("thumbnail"):
        try:
            urllib.request.urlretrieve(f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg", d / f"{vid}_thumb.jpg")
        except Exception:
            pass
    for p in d.glob(vid + ".*"):  # delete video, captions, info json
        if not p.name.endswith((".jpg",)) and not p.name.endswith(f"{vid}.json"):
            p.unlink()
    (d / f"{vid}.json").write_text(json.dumps(m, indent=1))
    return m


def thumbs_montage(ids, d):
    fs = []
    for i in ids[:6]:
        f = d / f"t_{i}.jpg"
        try:
            urllib.request.urlretrieve(f"https://i.ytimg.com/vi/{i}/mqdefault.jpg", f)
            fs.append(f)
        except Exception:
            pass
    if fs:
        args = []
        for f in fs:
            args += ["-i", str(f)]
        n = len(fs)
        run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex",
             "".join(f"[{k}:v]scale=320:180[v{k}];" for k in range(n)) + "".join(f"[v{k}]" for k in range(n)) + f"xstack=inputs={n}:layout="
             + "|".join(f"{(k % 3) * 320}_{(k // 3) * 180}" for k in range(n)) + ":fill=black" if n > 1 else "[0:v]scale=320:180",
             "-frames:v", "1", str(d / "thumbs.jpg")])
        for f in fs:
            f.unlink()


def main():
    a = sys.argv[1:]
    cfg = json.loads(pathlib.Path(a[0]).read_text())
    out = pathlib.Path(a[1]); out.mkdir(parents=True, exist_ok=True)
    per = int(a[a.index("--per") + 1]) if "--per" in a else 2
    only = a[a.index("--only") + 1].lower() if "--only" in a else None
    list_only = "--list-only" in a
    for c in cfg["competitors"]:
        if (only and only not in c["name"].lower()) or c.get("skip"):
            continue
        d = out / slug(c["name"]); d.mkdir(exist_ok=True)
        try:
            pl = list_channel(c["url"])
        except Exception as e:
            print(f"{c['name']}: listing failed {e}", flush=True)
            continue
        ents = [e for e in pl.get("entries") or [] if e and (e.get("duration") or 0) >= c.get("min_minutes", 6) * 60]
        cid = pl.get("channel_id") or (ents[0].get("channel_id") if ents else None)
        dates = rss_dates(cid) if cid else {}
        long_dates = sorted(dates[e["id"]] for e in ents if e["id"] in dates)
        cadence = None
        if len(long_dates) >= 2:
            span = (time.mktime(time.strptime(long_dates[-1], "%Y-%m-%d")) - time.mktime(time.strptime(long_dates[0], "%Y-%m-%d"))) / 86400
            cadence = round((len(long_dates) - 1) / max(span, 1) * 30, 1)
        rows = [{"id": e["id"], "title": e.get("title"), "views": e.get("view_count") or 0, "minutes": round((e.get("duration") or 0) / 60, 1),
                 "family": family(e.get("title") or ""), "published": dates.get(e["id"])} for e in ents]
        views = [r["views"] for r in rows]
        ch = {"name": c["name"], "url": c["url"], "size": c.get("size"), "subs": pl.get("channel_follower_count"), "channel_id": cid,
              "long_uploads_listed": len(rows), "median_views": int(statistics.median(views)) if views else 0,
              "newest_long_upload": long_dates[-1] if long_dates else None, "long_uploads_per_30_days": cadence,
              "rss_window": [long_dates[0], long_dates[-1]] if long_dates else None,
              "families": {f: sum(1 for r in rows if r["family"] == f) for f in {r["family"] for r in rows}},
              "median_minutes": statistics.median([r["minutes"] for r in rows]) if rows else None, "uploads": rows}
        flt = re.compile(c["filter"]) if c.get("filter") else None
        cand = [r for r in rows if not flt or flt.search(r["title"] or "")] or rows   # filter matched nothing: use all
        picks = c.get("videos") or [r["id"] for r in sorted(cand, key=lambda r: -r["views"])[:per]]
        ch["picked"] = picks
        print(f"{c['name']}: subs {ch['subs']}, {len(rows)} long uploads, median {ch['median_views']}, newest {ch['newest_long_upload']}, "
              f"{cadence} per 30 d; picks {picks}", flush=True)
        for r in sorted(rows, key=lambda r: -r["views"])[:8]:
            print(f"   {r['views']:>10}  {r['minutes']:>5}  {r['family']:<18} {r['title']}", flush=True)
        thumbs_montage([r["id"] for r in sorted(rows, key=lambda r: -r["views"])], d)
        if not list_only:
            ch["videos"] = []
            for vid in picks:
                if (d / f"{vid}.json").exists():
                    ch["videos"].append(json.loads((d / f"{vid}.json").read_text()))
                    continue
                m = measure_video(vid, d, 4)
                ch["videos"].append(m)
                p = m.get("pace", {})
                print(f"   measured {vid}: {p.get('per_min')} /min, median gap {p.get('median_gap_s')}, still {p.get('still_share')}, "
                      f"wpm {m.get('wpm')}, contrast {m.get('contrast_per_min')}, bed {m.get('music_bed_db')} {m.get('error', '')[:120]}", flush=True)
                time.sleep(8)
        (d / "channel.json").write_text(json.dumps(ch, indent=1))
        time.sleep(3)
    table(out)


def table(out):
    lines = ["| Competitor | Subs | Median views | Long uploads / 30 d | Median length | Video | Views | Changes / min | First 60 s | Median gap | Near-still | WPM | Contrast / min | Words first 30 s | Music bed dB |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in sorted(out.glob("*/channel.json")):
        ch = json.loads(f.read_text())
        for v in ch.get("videos") or [{}]:
            p = v.get("pace", {})
            lines.append(f"| {ch['name']} | {ch.get('subs')} | {ch.get('median_views')} | {ch.get('long_uploads_per_30_days')} | {ch.get('median_minutes')} | "
                         f"{(v.get('title') or '')[:48]} | {v.get('views')} | {p.get('per_min')} | {p.get('first_60s_per_min')} | {p.get('median_gap_s')} | "
                         f"{p.get('still_share')} | {v.get('wpm')} | {v.get('contrast_per_min')} | {v.get('words_first_30s')} | {v.get('music_bed_db')} |")
    (out / "table.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
