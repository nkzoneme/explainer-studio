#!/usr/bin/env python3
"""Script lint, run before any voice is paid for. Usage:
  python3 qa_script.py <SCRIPT.md> [--channel <slug>] [--wpm 160] [--no-card] [--json] [--spoken out.txt]

Reads the spoken lines (lines that start with "> ") under each "## Chapter ..." heading, and the
"## Story card" block (slots listed in research_flow/STORY_SHAPES.md). Counts only; whether the story
is any good is the cold read's job (STORY_SHAPES.md "Cold read"); --spoken writes the narration alone for it,
one blank line between chapters.

FAIL (exit 1), the measurable script rules of skill explainer-research:
  sentence over 30 words; first sentence over 15 words; contrast turns per minute under the minimum;
  more questions in a chapter than allowed, or two questions in a row; welcome / "in this video" /
  subscribe / sponsor in the first 60 s; a missing or empty Story card slot (skip with --no-card
  for scripts written before 18/11/2026).
WARN (exit 0), things to look at:
  sentence-length mix; a stretch over 75 s with no turn; "and then" links; a chapter that ends on a
  summary line; a chapter with fewer than 2 numbers or dates; the peak outside 55-90 % of the
  runtime; fewer re-hooks than one per 3.5 minutes or a gap over 4 minutes between them.
Limits come from the channel's style.json "script" key when --channel is given (contrast_per_min_min,
questions_per_chapter_max, wpm), else the defaults below.
"""
import argparse, json, pathlib, re, statistics, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]          # .../explainer
TURNS = r"\b(but|except|until|instead|however|yet)\b"
BANNED = [r"\bwelcome\b", r"\bin this video\b", r"\bsubscribe\b", r"(?<![-\w])sponsor(ed)?\b(?! hackers| groups?| attack)"]   # "state-sponsored" is not an ad read
SUMMARY = r"^(so that'?s|that'?s how|that is how|in short|in other words|to sum|in summary|as we('ve| have)? seen|and that'?s (how|why))\b"
NUMWORD = r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|trillion|half|quarter|dozen|first|second|third|january|february|march|april|may|june|july|august|september|october|november|december)\b"
CARD = ["promise", "first 10 s", "person", "peak", "shape", "stakes ladder", "re-hooks"]


def words(t):
    return re.findall(r"[A-Za-z0-9$%][A-Za-z0-9$%'’.,:-]*[A-Za-z0-9%]|[A-Za-z0-9$%]", t)


def sentences(t):
    t = re.sub(r"\s+", " ", t.replace("*", "")).strip()
    parts = re.split(r"(?<=[.!?…])[\"'’)\]]*\s+(?=[\"'‘“(\[]?[A-Z0-9$])", t)
    return [p.strip() for p in parts if words(p)]


def mmss(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"


def parse(path):
    chapters, card, cur, in_card = [], {}, None, False
    for line in pathlib.Path(path).read_text().splitlines():
        if line.startswith("## "):
            in_card = bool(re.match(r"##\s+Story card", line, re.I))
            m = re.match(r"##\s+Chapter\s+(\d+)\s*[—–:-]*\s*(.*)", line)
            cur = None
            if m:
                cur = {"n": int(m.group(1)), "title": re.sub(r"\s*\(.*$", "", m.group(2)).strip(), "text": []}
                chapters.append(cur)
        elif in_card:
            m = re.match(r"\s*[-*]\s*\**([^:*]+?)\**\s*:\s*(.*)", line)
            if m:
                card[m.group(1).strip().lower()] = m.group(2).strip()
        elif cur is not None and line.startswith(">"):
            cur["text"].append(line.lstrip("> ").strip())
    return chapters, card


def limits(channel, wpm):
    lim = {"contrast_per_min_min": 1.0, "questions_per_chapter_max": 1, "wpm": wpm or 160.0, "source": "defaults"}
    if channel:
        p = ROOT / "channels" / channel / "style.json"
        if p.exists():
            s = json.loads(p.read_text()).get("script") or {}
            for k in ("contrast_per_min_min", "questions_per_chapter_max"):
                if isinstance(s.get(k), (int, float)):
                    lim[k] = s[k]; lim["source"] = str(p)
            w = s.get("wpm")
            if not wpm and isinstance(w, dict) and "min" in w and "max" in w:
                lim["wpm"] = (w["min"] + w["max"]) / 2
            elif not wpm and isinstance(w, (list, tuple)) and len(w) == 2:
                lim["wpm"] = sum(w) / 2
    return lim


def run(path, channel=None, wpm=None, need_card=True):
    chapters, card = parse(path)
    lim = limits(channel, wpm)
    fails, warns, rows = [], [], []
    if not chapters or not any(c["text"] for c in chapters):
        return {"fails": ["no '## Chapter N' headings with '> ' spoken lines found"], "warns": [], "rows": [], "limits": lim}
    spw = 60.0 / lim["wpm"]
    t, flat = 0.0, []                                    # flat: (start_s, chapter, sentence)
    for c in chapters:
        ss = sentences(" ".join(c["text"]))
        c["start"], c["sent"] = t, ss
        for s in ss:
            flat.append((t, c["n"], s)); t += len(words(s)) * spw
        c["dur"] = t - c["start"]
    total = t
    # --- hard rules
    for st, ch, s in flat:
        n = len(words(s))
        if n > 30:
            fails.append(f"ch{ch} {mmss(st)}: sentence of {n} words (max 30): \"{s[:70]}...\"")
    n1 = len(words(flat[0][2]))
    if n1 > 15:
        fails.append(f"first sentence has {n1} words (max 15)")
    for st, ch, s in flat:
        if st >= 60: break
        for b in BANNED:
            if re.search(b, s, re.I):
                fails.append(f"ch{ch} {mmss(st)}: '{re.search(b, s, re.I).group(0)}' in the first 60 s")
    turns_all = [(st, ch, s) for st, ch, s in flat if re.search(TURNS, s, re.I)]
    cpm = len(turns_all) / (total / 60)
    if cpm < lim["contrast_per_min_min"]:
        fails.append(f"contrast turns {cpm:.2f} per minute (min {lim['contrast_per_min_min']})")
    prev_q = False
    for st, ch, s in flat:
        q = s.rstrip("\"'’)] ").endswith("?")
        if q and prev_q:
            fails.append(f"ch{ch} {mmss(st)}: two questions in a row")
        prev_q = q
    for c in chapters:
        q = sum(1 for s in c["sent"] if s.rstrip("\"'’)] ").endswith("?"))
        nums = len(re.findall(r"\d[\d,.]*", " ".join(c["sent"]))) + len(re.findall(NUMWORD, " ".join(c["sent"]), re.I))
        tr = sum(1 for s in c["sent"] if re.search(TURNS, s, re.I))
        last = c["sent"][-1] if c["sent"] else ""
        if q > lim["questions_per_chapter_max"]:
            fails.append(f"ch{c['n']}: {q} questions (max {lim['questions_per_chapter_max']} per chapter)")
        if nums < 2:
            warns.append(f"ch{c['n']}: {nums} numbers or dates (want 2 or more)")
        if re.search(SUMMARY, last, re.I):
            warns.append(f"ch{c['n']} ends on a summary line, not a question, reversal or new threat: \"{last[:80]}\"")
        rows.append({"ch": c["n"], "title": c["title"][:28], "start": mmss(c["start"]), "s": round(c["dur"]), "words": sum(len(words(s)) for s in c["sent"]),
                     "turns_per_min": round(tr / max(c["dur"], 1) * 60, 1), "questions": q, "numbers": nums, "last": last[:70]})
    # --- soft rules
    lens = [len(words(s)) for _, _, s in flat]
    med, short = statistics.median(lens), sum(1 for n in lens if n <= 6) / len(lens)
    if not 8 <= med <= 13:
        warns.append(f"median sentence {med:.0f} words (want 8-13)")
    if short < 0.15:
        warns.append(f"only {short * 100:.0f} % of sentences have 6 words or fewer (want 15 % or more)")
    edges = [0.0] + [st for st, _, _ in turns_all] + [total]
    for a, b in zip(edges, edges[1:]):
        if b - a > 75:
            warns.append(f"{mmss(a)}-{mmss(b)}: {b - a:.0f} s with no turn (but / except / until / instead / however / yet)")
    for st, ch, s in flat:
        if re.search(r"^(and then|then,)|\band then\b", s, re.I):
            warns.append(f"ch{ch} {mmss(st)}: 'and then' link (make it BUT or THEREFORE, or cut the beat): \"{s[:70]}\"")
    # --- story card
    if need_card:
        if not card:
            fails.append("no '## Story card' block (slots: " + ", ".join(CARD) + "; see research_flow/STORY_SHAPES.md)")
        else:
            for k in CARD:
                v = next((val for key, val in card.items() if key.startswith(k)), "")
                if not v or set(v) <= set("<>.-_ ?") or re.fullmatch(r"<.*>", v):
                    fails.append(f"Story card: '{k}' is missing or empty")
            pk = next((val for key, val in card.items() if key.startswith("peak")), "")
            m = re.search(r"(\d+):(\d\d)", pk)
            if m:
                p = (int(m.group(1)) * 60 + int(m.group(2))) / total
                if not 0.55 <= p <= 0.90:
                    warns.append(f"peak at {m.group(0)} is {p * 100:.0f} % of the estimated runtime (want 55-90 %)")
            elif pk:
                warns.append("Story card: the peak has no m:ss time")
            rh = next((val for key, val in card.items() if key.startswith("re-hook")), "")
            ts = sorted(int(a) * 60 + int(b) for a, b in re.findall(r"(\d+):(\d\d)", rh))
            want = max(1, int(total / 210))
            if rh and len(ts) < want:
                warns.append(f"{len(ts)} re-hooks for {mmss(total)} (want {want}: one per 3.5 minutes)")
            pts = [0.0] + ts + [total]
            for a, b in zip(pts, pts[1:]):
                if ts and b - a > 240:
                    warns.append(f"{mmss(a)}-{mmss(b)}: {(b - a) / 60:.1f} minutes with no planned re-hook (max 4)")
    return {"file": str(path), "runtime_est": mmss(total), "wpm": lim["wpm"], "limits": lim, "contrast_per_min": round(cpm, 2),
            "median_sentence_words": med, "short_sentence_share": round(short, 2), "rows": rows, "card": card, "fails": fails, "warns": warns}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script"); ap.add_argument("--channel"); ap.add_argument("--wpm", type=float)
    ap.add_argument("--no-card", action="store_true"); ap.add_argument("--json", action="store_true"); ap.add_argument("--spoken")
    a = ap.parse_args()
    if a.spoken:
        pathlib.Path(a.spoken).write_text("\n\n".join(" ".join(c["text"]) for c in parse(a.script)[0] if c["text"]) + "\n")
    r = run(a.script, a.channel, a.wpm, not a.no_card)
    if a.json:
        print(json.dumps(r, indent=1)); sys.exit(1 if r["fails"] else 0)
    if r["rows"]:
        print(f"{r['file']}: about {r['runtime_est']} at {r['wpm']:.0f} wpm | contrast turns {r['contrast_per_min']} per min | median sentence {r['median_sentence_words']:.0f} words | "
              f"{r['short_sentence_share'] * 100:.0f} % short sentences | limits from {r['limits']['source']}")
        print(f"{'ch':>3} {'start':>5} {'s':>4} {'words':>5} {'turns/min':>9} {'q':>2} {'num':>3}  last sentence")
        for x in r["rows"]:
            print(f"{x['ch']:>3} {x['start']:>5} {x['s']:>4} {x['words']:>5} {x['turns_per_min']:>9} {x['questions']:>2} {x['numbers']:>3}  {x['last']}")
    for w in r["warns"]: print("WARN  " + w)
    for f in r["fails"]: print("FAIL  " + f)
    print("qa_script: " + ("FAIL" if r["fails"] else "ok") + f" ({len(r['fails'])} fail, {len(r['warns'])} warn)")
    sys.exit(1 if r["fails"] else 0)


if __name__ == "__main__":
    main()
