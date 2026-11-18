#!/usr/bin/env python3
"""G2 remake gate. Usage:
  python3 remake_diff.py REMAKE_MAP.md OUR_chapters.json [--script SCRIPT.md] [--transcript src_transcript.txt]
        [--title "our title"] [--src-title "source title"] [--entity "Acme"]
        [--thumb-text "OUR WORDS"] [--src-thumb-text "THEIR WORDS"] [--thumb-img ours.png --src-thumb-img theirs.png]
        [--tol 10] [--json out.json]
OUR_chapters.json: film/<slug>/final/chapters.json ([{ch,name,start,len}]) or {"starts":[...]} (older format) or a list of numbers.
Source chapter starts come from the REMAKE_MAP "Chapters, lengths, pace" table (first time of the Time/Range column).
Rules (FAIL exits 1):
  chapter_timing   % of our chapter starts (excluding 0:00) within +-tol s (default 10) of a source start: limit 30 %
  beat_order       sections of --script mapped to the source beat table by word overlap; longest in-order run / our sections: limit 60 %
  angle            REMAKE_MAP has an 'Angle:' line "They asked X. We ask Y." and Y's content words appear in our title
  title            our title shares <= 1 content word with the source title beyond --entity words
  thumb_text       thumbnail words share nothing but the entity with the source thumbnail text (when both given)
  thumb_hash       dHash distance >= 20 of 64 bits (when both images given; calibrate on unrelated pairs first)
  wording          (with --script and --transcript) zero shared 6-word runs, <= 3 shared 4-word runs per 1,000 words
Checks whose inputs are missing are reported as SKIP, never as PASS."""
import argparse, json, pathlib, re, sys

STOP = set("a an the of to in on at for and or but is are was were be been it its this that these those with by as from than then so not no how why what who did does do you your we our they their he she his her".split())


def norm(w): return re.sub(r"[^a-z0-9']", "", w.lower())
def cw(text): return {norm(w) for w in text.split() if norm(w) and norm(w) not in STOP and len(norm(w)) > 2}
def tsec(s):
    p = [int(x) for x in s.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def parse_map(text):
    d = {"title": None, "starts": [], "beats": []}
    m = re.search(r'"([^"]{8,})"', text.split("\n", 1)[0])
    d["title"] = m.group(1) if m else None
    sec = None
    for l in text.splitlines():
        if l.startswith("## "): sec = l.lower()
        if not l.startswith("|") or not sec: continue
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if "chapters" in sec:
            m = re.search(r"(\d+:\d{2})(?:\s*-\s*\d+:\d{2})?", " ".join(cells[1:3]))
            if m and not l.startswith("|--") and not l.startswith("| ---"): d["starts"].append(tsec(m.group(1)))
        if "beat table" in sec and len(cells) >= 4:
            m = re.match(r"(\d+:\d{2})", cells[1])
            if m: d["beats"].append({"t": tsec(m.group(1)), "text": " ".join(cells[3:])})
    am = re.search(r"^\W*\**angle\**\s*:\**\s*(.+)$", text, re.I | re.M)
    d["angle"] = am.group(1).strip() if am else None
    tm = re.search(r'Title:\s*"([^"]+)"', text)
    if not d["title"] and tm: d["title"] = tm.group(1)
    thm = re.search(r'headline\s+"([^"]+)"', text, re.I) or re.search(r'thumbnail[^"\n]*"([^"]{3,40})"', text, re.I)
    d["thumb_text"] = thm.group(1) if thm else None
    return d


def load_ours(path):
    j = json.loads(pathlib.Path(path).read_text())
    if isinstance(j, dict): j = j.get("starts") or j.get("chapters") or []
    return [float(x["start"] if isinstance(x, dict) else x) for x in j]


def sections(script):
    out, cur = [], None
    for l in pathlib.Path(script).read_text(errors="ignore").splitlines():
        if l.startswith("### "): cur = {"h": l, "t": ""}; out.append(cur)
        elif cur is not None and l.startswith(">"): cur["t"] += " " + l.lstrip("> ")
    return out


def lis(a):
    best = [1] * len(a)
    for i in range(len(a)):
        for j in range(i):
            if a[j] < a[i]: best[i] = max(best[i], best[j] + 1)
    return max(best, default=0)


def ngrams(tokens, n): return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map"); ap.add_argument("chapters")
    ap.add_argument("--script"); ap.add_argument("--transcript"); ap.add_argument("--title"); ap.add_argument("--src-title"); ap.add_argument("--entity", default="")
    ap.add_argument("--thumb-text"); ap.add_argument("--src-thumb-text"); ap.add_argument("--thumb-img"); ap.add_argument("--src-thumb-img")
    ap.add_argument("--tol", type=float, default=10.0); ap.add_argument("--json")
    a = ap.parse_args()
    mp = pathlib.Path(a.map); mtxt = mp.read_text(errors="ignore")
    src = parse_map(mtxt)
    ours = load_ours(a.chapters)
    script = a.script or (str(mp.parent / "SCRIPT.md") if (mp.parent / "SCRIPT.md").exists() else None)
    transcript = a.transcript or (str(mp.parent / "transcript.txt") if (mp.parent / "transcript.txt").exists() else None)
    title = a.title
    if not title and script:
        m = re.match(r"#\s*SCRIPT:\s*(.+)", pathlib.Path(script).read_text(errors="ignore").splitlines()[0])
        title = m.group(1).strip() if m else None
    src_title = a.src_title or src["title"]
    ent = cw(a.entity)
    R = {}
    def rec(k, st, d, **x): R[k] = {"status": st, **{"detail": d}, **x}

    # 1 chapter timing
    ss = [s for s in src["starts"] if s > 0]; os_ = [o for o in ours if o > 0]
    if ss and os_:
        near = [o for o in os_ if any(abs(o - s) <= a.tol for s in ss)]
        pct = 100 * len(near) / len(os_)
        rec("chapter_timing", "PASS" if pct <= 30 else "FAIL", f"{len(near)} of {len(os_)} of our chapter starts within +-{a.tol:g} s of a source start = {pct:.0f} % (limit 30 %); source starts {ss}", pct=round(pct, 1))
    else:
        rec("chapter_timing", "FAIL", "could not read chapter starts from the map table or chapters.json")

    # 2 beat order
    if script and src["beats"]:
        secs = sections(script); idx = []
        for s in secs:
            sc = cw(s["h"] + " " + s["t"])
            best = max(range(len(src["beats"])), key=lambda i: len(sc & cw(src["beats"][i]["text"])) / (1 + len(cw(src["beats"][i]["text"])) ** 0.5))
            ov = len(sc & cw(src["beats"][best]["text"]))
            if ov >= 3: idx.append(best)
        run = lis(idx); pct = 100 * run / max(1, len(secs))
        rec("beat_order", "PASS" if pct <= 60 else "FAIL", f"{run} of {len(secs)} sections ({pct:.0f} %) follow the source beat order (limit 60 %); {len(idx)} sections matched a beat by word overlap (>=3 shared content words; a proxy for topic tags)", pct=round(pct, 1))
    else:
        rec("beat_order", "SKIP", "needs --script (or SCRIPT.md beside the map) and a beat table")

    # 3 angle
    ang = src["angle"]
    if not ang:
        rec("angle", "FAIL", "REMAKE_MAP has no 'Angle:' line. Add: Angle: They asked X. We ask Y. (Y goes in our title)")
    else:
        m = re.search(r"we ask\s*:?\s*(.+)$", ang, re.I)
        if not (re.search(r"they asked", ang, re.I) and m): rec("angle", "FAIL", f"angle line is not 'They asked X. We ask Y.': {ang[:100]}")
        elif title and not (cw(m.group(1)) & cw(title)): rec("angle", "FAIL", f"Y ('{m.group(1)[:60]}') shares no content word with our title '{title}'")
        else: rec("angle", "PASS", f"angle present: {ang[:120]}")

    # 4 title
    if title and src_title:
        sh = (cw(title) & cw(src_title)) - ent
        rec("title", "PASS" if len(sh) <= 1 else "FAIL", f"shared content words beyond the entity: {sorted(sh) or 'none'} (limit 1); ours '{title}' vs source '{src_title}'")
    else:
        rec("title", "SKIP", "need both titles (--title / SCRIPT.md heading, and a quoted source title in the map)")

    # 5 thumbnail text and hash
    st = a.src_thumb_text or src["thumb_text"]
    if a.thumb_text and st:
        sh = (cw(a.thumb_text) & cw(st)) - ent
        rec("thumb_text", "PASS" if not sh else "FAIL", f"shared thumbnail words beyond the entity: {sorted(sh) or 'none'}; ours '{a.thumb_text}' vs source '{st}'")
    else:
        rec("thumb_text", "SKIP", "need --thumb-text (ours) and source thumbnail text (--src-thumb-text or a quoted headline in the map)")
    if a.thumb_img and a.src_thumb_img:
        import cv2, numpy as np
        def dh(p):
            im = cv2.resize(cv2.imread(p, cv2.IMREAD_GRAYSCALE), (9, 8), interpolation=cv2.INTER_AREA)
            return (im[:, 1:] > im[:, :-1]).flatten()
        dist = int((dh(a.thumb_img) != dh(a.src_thumb_img)).sum())
        rec("thumb_hash", "PASS" if dist >= 20 else "FAIL", f"dHash distance {dist}/64 (need >= 20; calibrate on unrelated pairs)", distance=dist)
    else:
        rec("thumb_hash", "SKIP", "need --thumb-img and --src-thumb-img")

    # 6 wording
    if script and transcript:
        tt = pathlib.Path(transcript).read_text(errors="ignore")
        tt = re.sub(r"\[\d+:\d{2}(?::\d{2})?\]", " ", tt)
        st_tok = [norm(w) for w in tt.split() if norm(w)]
        ot = [norm(w) for s in sections(script) for w in s["t"].split() if norm(w)]
        n6 = ngrams(ot, 6) & ngrams(st_tok, 6); n4 = ngrams(ot, 4) & ngrams(st_tok, 4)
        per = 1000 * len(n4) / max(1, len(ot))
        ok = not n6 and per <= 3
        rec("wording", "PASS" if ok else "FAIL", f"{len(n6)} shared 6-word runs (limit 0), {len(n4)} shared 4-word runs = {per:.1f} per 1,000 words (limit 3); {len(ot)} words compared", examples=[" ".join(x) for x in list(n6)[:3]])
    else:
        rec("wording", "SKIP", "needs --script and --transcript")

    fails = [k for k, v in R.items() if v["status"] == "FAIL"]
    for k, v in R.items(): print(f"{v['status']:5} {k:15} {v['detail']}")
    print("REMAKE_DIFF", "FAIL" if fails else "PASS", "| failing:", ", ".join(fails) or "none")
    if a.json: pathlib.Path(a.json).write_text(json.dumps({"overall": "FAIL" if fails else "PASS", "checks": R}, indent=1))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
