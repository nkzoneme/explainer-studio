#!/usr/bin/env python3
"""Hook QA for chapter 1. Usage:
  python3 qa_hook.py <chapter-1 dir | ch01_raw.mp4 | final.mp4> --channel <slug> [--title "..."] [--script SCRIPT.md]
                     [--words ch01_w.words.json] [--thumb thumb.png] [--out report.json] [--no-video]
Thresholds come from channels/<slug>/style.json "hook" (first_sentence_by_s, promise_by_s, story_by_s).
Checks (FAIL exits 1; THUMB is a heuristic and only ever WARNs):
  voice_start      first word starts by 1.5 s
  first_sentence   <= 15 words, ends by first_sentence_by_s
  promise          the SCRIPT's marked promise line (a line tagged [promise] / "Promise:", else the section headed
                   "Promise") is spoken by promise_by_s, found in words.json by fuzzy match. Without a script: the first
                   question sentence, or with --title a sentence with >= 2 content words of the title.
  title_sentence   (with --title) a sentence with >= 2 title content words is spoken by promise_by_s
  banned_60s       none of welcome / in this video / subscribe / sponsor / channel or host name in the first 60 s
  pace_30s         >= 8 full-frame changes in the first 30 s, first by 3 s, none held over 5 s (qa_pace.measure)
  frame0_clean     no logo / title card / host in the first sentence: OCR of frames at 0.0, 0.5 s and mid first sentence
                   (channel name, title words, "welcome") and host calls in index.html before the first sentence ends
  thumb_object     frame 0 vs the thumbnail(s): perceptual hash + colour histogram; heuristic, WARN only
Importable: run(target, channel, ...) -> dict with "overall"."""
import argparse, difflib, json, pathlib, re, subprocess, sys, tempfile
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

STOP = set("a an the of to in on at for and or but is are was were be been it its this that these those with by as from than then so not no".split())
BANNED = [r"\bwelcome\b", r"\bin this video\b", r"\bsubscribe\b", r"\bsponsor(ed)?\b"]


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def content(words):
    return {norm(w) for w in words if norm(w) and norm(w) not in STOP and len(norm(w)) > 2}


def sentences(words):
    """words: [{word,start,end}] -> [{text, tokens, start, end, n}]"""
    out, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.!?][\"')\]]*$", w["word"].strip()):
            out.append(cur); cur = []
    if cur: out.append(cur)
    return [{"text": " ".join(x["word"] for x in s), "start": s[0]["start"], "end": s[-1]["end"], "n": len(s), "ws": s} for s in out]


def find_script(slug_name, explicit):
    if explicit: return pathlib.Path(explicit)
    for p in (ROOT / "research" / "remake" / slug_name / "SCRIPT.md", ROOT / "research" / slug_name / "SCRIPT.md"):
        if p.exists(): return p
    return None


def promise_line(script):
    """Marked promise line: a '>' line (or plain line) containing [promise] / 'Promise:'; else the > line(s) of the heading containing 'Promise'."""
    txt = script.read_text(errors="ignore").splitlines()
    for i, l in enumerate(txt):
        if re.search(r"\[promise\]|\bpromise:", l, re.I) and not l.lstrip().startswith("- ["):
            m = re.sub(r"\[promise\]|promise:", "", l, flags=re.I).strip(" >*")
            if len(m.split()) >= 4: return m
            for l2 in txt[i + 1:i + 6]:
                if l2.startswith(">"): return l2.lstrip("> ").strip()
    for i, l in enumerate(txt):
        if l.startswith("#") and re.search(r"promise", l, re.I):
            out = []
            for l2 in txt[i + 1:i + 12]:
                if l2.startswith("#"): break
                if l2.startswith(">"): out.append(l2.lstrip("> ").strip())
            if out: return " ".join(out)
    return None


def locate(line, words):
    """Best window of words matching the script line -> (start, end, ratio)."""
    tgt = [norm(w) for w in line.split() if norm(w)]
    seq = [norm(w["word"]) for w in words]
    n, best = len(tgt), (0, 0, 0.0)
    for i in range(0, max(1, len(seq) - n + 1)):
        for L in (n, n - 1, n + 1):
            if L < 1 or i + L > len(seq): continue
            r = difflib.SequenceMatcher(None, tgt, seq[i:i + L]).ratio()
            if r > best[2]: best = (i, i + L - 1, r)
    i, j, r = best
    return words[i]["start"], words[j]["end"], r


def resolve(target):
    t = pathlib.Path(target).resolve()
    info = {"dir": None, "video": None, "name": None}
    if t.is_dir():
        info["dir"] = t
        info["name"] = t.parent.name
        raw = t / "out" / (t.name + "_raw.mp4")
        info["video"] = raw if raw.exists() else None
    else:
        info["video"] = t
        parts = t.parts
        if "film" in parts:
            info["name"] = parts[parts.index("film") + 1]
            d = t.parents[1] if t.parent.name == "out" else None
            info["dir"] = d if d and d.name.startswith("ch") else None
    return info


def frame(video, t, path):
    sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1", str(path)])
    return path if pathlib.Path(path).exists() else None


def dhash(path, n=8):
    import cv2
    im = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    im = cv2.resize(im, (n + 1, n), interpolation=cv2.INTER_AREA)
    return (im[:, 1:] > im[:, :-1]).flatten()


def hist(path):
    import cv2
    im = cv2.imread(str(path)); im = cv2.resize(im, (320, 180))
    h = cv2.calcHist([cv2.cvtColor(im, cv2.COLOR_BGR2HSV)], [0, 1], None, [16, 8], [0, 180, 0, 256])
    return cv2.normalize(h, h).flatten()


def ocr(path):
    r = sh(["tesseract", str(path), "-", "--psm", "11"])
    return re.sub(r"\s+", " ", r.stdout).strip().lower()


def run(target, channel, title=None, script=None, words_path=None, thumbs=None, video=True):
    style = json.loads((ROOT / "channels" / channel / "style.json").read_text())
    hk = style.get("hook", {})
    P_FIRST, P_PROM = hk.get("first_sentence_by_s", 6), hk.get("promise_by_s", 20)
    info = resolve(target)
    name = info["name"] or ""
    wp = pathlib.Path(words_path) if words_path else None
    if wp is None:
        for c in (ROOT / "vo" / name / "ch01_w.words.json", ROOT / "vo" / name / "ch01.words.json"):
            if c.exists(): wp = c; break
    if wp is None or not wp.exists():
        return {"overall": "FAIL", "checks": {"words": {"status": "FAIL", "detail": "no words.json found; pass --words"}}}
    words = json.loads(wp.read_text())
    sents = sentences(words)
    C = {}

    def rec(k, status, detail, **data): C[k] = {"status": status, "detail": detail, **data}

    # voice start
    w0 = words[0]["start"]
    rec("voice_start", "PASS" if w0 <= 1.5 else "FAIL", f"first word at {w0:.2f} s (limit 1.5 s)")
    # first sentence
    s1 = sents[0]
    ok = s1["n"] <= 15 and s1["end"] <= P_FIRST
    rec("first_sentence", "PASS" if ok else "FAIL", f"{s1['n']} words, ends {s1['end']:.1f} s (limits 15 words, {P_FIRST} s): \"{s1['text'][:90]}\"")
    # promise
    sp = find_script(name, script)
    pl = promise_line(sp) if sp else None
    if pl:
        a, b, r = locate(pl, words)
        if r < 0.6:
            rec("promise", "FAIL", f"marked promise line not found in the voice (match {r:.2f}); script and voice differ: \"{pl[:80]}\"")
        else:
            rec("promise", "PASS" if a <= P_PROM else "FAIL", f"marked promise line (script {sp.name}) spoken {a:.1f}-{b:.1f} s, limit start by {P_PROM} s (match {r:.2f}): \"{pl[:80]}\"", start=a, end=b)
    else:
        q = next((s for s in sents if s["text"].rstrip().endswith("?")), None)
        if q:
            rec("promise", "PASS" if q["start"] <= P_PROM else "FAIL", f"no marked promise line in a SCRIPT; first question sentence at {q['start']:.1f} s used instead (limit {P_PROM} s): \"{q['text'][:80]}\"", start=q["start"])
        else:
            rec("promise", "FAIL", "no marked promise line and no question sentence in the voice")
    # title sentence
    if title:
        tc = content(title.split())
        hit = next((s for s in sents if len(content(s["text"].split()) & tc) >= 2), None)
        if hit: rec("title_sentence", "PASS" if hit["start"] <= P_PROM else "FAIL", f"sentence with >= 2 title words starts {hit['start']:.1f} s (limit {P_PROM} s)")
        else: rec("title_sentence", "FAIL", f"no sentence in chapter 1 shares 2 content words with the title ({sorted(tc)})")
    # banned first 60 s
    early = " ".join(w["word"] for w in words if w["start"] < 60).lower()
    bad = [p for p in BANNED if re.search(p, early)]
    for nm in (style.get("channel", ""),):
        if nm and nm.lower() in early: bad.append(nm)
    rec("banned_60s", "FAIL" if bad else "PASS", "found " + ", ".join(bad) if bad else "none of welcome / in this video / subscribe / sponsor / channel name in the first 60 s")
    # video checks
    v = info["video"]
    if not video or not v or not v.exists():
        for k in ("pace_30s", "frame0_clean", "thumb_object"):
            rec(k, "SKIP", "no video given (--no-video or no render found)")
    else:
        import qa_pace
        with tempfile.TemporaryDirectory() as td:
            clip = pathlib.Path(td) / "first30.mp4"
            sh(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-t", "30", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(clip)])
            m = qa_pace.measure(clip)
            ch = [round(e, 1) for e, g in m["gaps"][1:]]   # change times (edges after the 0.0 start)
            first = ch[0] if ch else None
            longest = max([g for _, g in m["gaps"]], default=99)
            probs = []
            if len(ch) < 8: probs.append(f"{len(ch)} full-frame changes in 30 s (need 8)")
            if first is None or first > 3.0: probs.append(f"first change at {first} s (need by 3 s)")
            if longest > 5.0: probs.append(f"longest hold {longest} s (max 5 s)")
            rec("pace_30s", "FAIL" if probs else "PASS", "; ".join(probs) if probs else f"{len(ch)} changes, first {first} s, longest hold {longest} s", changes=ch)
            # frame 0 / first sentence: OCR + host log
            tm = [0.0, 0.5, max(0.8, s1["end"] / 2)]
            flags, txts = [], []
            tc = content(title.split()) if title else set()
            chn = (style.get("channel", "") or "").lower()
            f0 = None
            for t in tm:
                p = frame(v, t, pathlib.Path(td) / f"f{t:.1f}.png")
                if not p: continue
                if t == 0.0: f0 = p
                tx = ocr(p); txts.append(tx)
                if "welcome" in tx or (chn and chn in tx): flags.append(f"logo/channel text at {t:.1f} s: '{tx[:50]}'")
                if tc and len(content(tx.split()) & tc) >= 2: flags.append(f"title-card words at {t:.1f} s: '{tx[:50]}'")
            if info["dir"] and (info["dir"] / "index.html").exists():
                html = (info["dir"] / "index.html").read_text(errors="ignore")
                for mm in re.finditer(r"host\w*\.(?:talk|show|enter|in|pose|say)\w*\(\s*([\d.]+)", html):
                    if float(mm.group(1)) < s1["end"]: flags.append(f"host call at {mm.group(1)} s inside the first sentence (ends {s1['end']:.1f} s)")
            rec("frame0_clean", "FAIL" if flags else "PASS", "; ".join(flags[:4]) if flags else "no channel text, title card or host call found in the first sentence (OCR at 0.0/0.5/mid + html host log; detection is partial)")
            # thumbnail object
            th = [pathlib.Path(x) for x in (thumbs or [])]
            if not th:
                for d in filter(None, [ROOT / "film" / name / "thumbs", ROOT / "film" / name / "final"]):
                    th += sorted(d.glob("thumb*.png")) + sorted(d.glob("thumb*.jpg"))
            th = [x for x in th if "test_160" not in x.name]
            if f0 and th:
                h0, g0 = dhash(f0), hist(f0)
                import cv2
                res = []
                for x in th:
                    res.append((int((h0 != dhash(x)).sum()), float(cv2.compareHist(g0, hist(x), cv2.HISTCMP_CORREL)), x.name))
                best = min(res, key=lambda r: (r[0] - 20 * r[1]))
                close = best[0] <= 24 or best[1] >= 0.5
                rec("thumb_object", "PASS" if close else "WARN", f"best thumbnail {best[2]}: dHash distance {best[0]}/64, colour correlation {best[1]:.2f} (heuristic; flag only, check frame 0 by eye)", compared=len(th))
            else:
                rec("thumb_object", "WARN", "no thumbnail found to compare (pass --thumb)")
    fails = [k for k, c in C.items() if c["status"] == "FAIL"]
    return {"target": str(target), "channel": channel, "words": str(wp), "script": str(sp) if sp else None,
            "overall": "FAIL" if fails else "PASS", "fails": fails, "checks": C}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target"); ap.add_argument("--channel", required=True)
    ap.add_argument("--title"); ap.add_argument("--script"); ap.add_argument("--words"); ap.add_argument("--thumb", action="append")
    ap.add_argument("--out"); ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args()
    r = run(a.target, a.channel, a.title, a.script, a.words, a.thumb, not a.no_video)
    for k, c in r["checks"].items(): print(f"{c['status']:5} {k:15} {c['detail']}")
    print(f"QA_HOOK {r['overall']}")
    if a.out: pathlib.Path(a.out).write_text(json.dumps(r, indent=1, default=str))
    sys.exit(1 if r["overall"] == "FAIL" else 0)


if __name__ == "__main__":
    main()
