#!/usr/bin/env python3
"""List self-contained Short candidates (20-55 s) from a finished long video.

Usage:
  python3 shorts/pick_segments.py --words vo/<slug> --trim film/<slug>/final/work/trim_v2.json \
      --script research/<slug>/SCRIPT.md --out film/<slug>/shorts/candidates.json [--top 12]

A candidate starts at a sentence start, ends on a sentence end, lasts 20-55 s, and is scored for:
  + a strong opener: a question, a number, a short punchy first sentence, "you"/"imagine"/"here's"
  + starting where a script beat starts (the writer already made it a fresh idea)
  + a payoff: numbers, a named answer ("called", "that's", "it's"), the last sentence closing a beat
  + ending before a natural pause (>= 0.45 s) so the cut does not clip a breath
  - an opener that leans on context ("But", "So", "It", "They", "That", "Which", "Still", "back to")
  - ending on an unanswered question, or a length far from the 30-45 s sweet spot
Overlapping candidates are suppressed (best first). The final pick is a human/LLM judgement: read the top list.
Output JSON: [{rank, score, start, end, dur, chapter, beat, first_line, last_line, hook_title, text, why}]"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import film_words, sentences, script_beats, locate_beats, norm, fmt_ts

NUM = set("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
          "eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion percent half "
          "quarter dozen".split())
DEPENDENT = {"but", "so", "and", "it", "they", "that", "this", "these", "those", "which", "still", "then", "also", "instead",
             "he", "she", "his", "her", "its", "their", "though", "together", "eventually", "except", "by", "for"}
HOOKY = {"imagine", "you", "your", "here's", "think", "why", "what", "how", "who", "nobody", "never", "most", "odd", "twist"}
PAYOFF = {"called", "that's", "it's", "answer", "means", "so", "which", "worth", "more", "than", "yes"}


def has_num(text):
    return any(t in NUM for t in norm(text)) or bool(re.search(r"\d", text))


def score_seg(S, a, b, words, beat_starts, beat_of):
    first, last = S[a], S[b]
    dur = last["end"] - first["start"]
    fw = norm(first["text"]); lw = norm(last["text"])
    why, sc = [], 0.0
    if first["text"].rstrip().endswith("?"): sc += 3; why.append("opens with a question")
    if has_num(first["text"]): sc += 2; why.append("number in first line")
    if len(fw) <= 9: sc += 1.5; why.append("short first line")
    if fw and fw[0] in HOOKY or any(t in HOOKY for t in fw[:3]): sc += 1; why.append("hook word")
    if fw and fw[0] in DEPENDENT: sc -= 3; why.append("opener leans on context")
    if any(p in first["text"].lower() for p in ("back to", "our number", "from the start", "brings back", "that, ")): sc -= 2; why.append("callback opener")
    if first["i0"] in beat_starts: sc += 2; why.append("starts a script beat")
    if b + 1 < len(S) and S[b + 1]["i0"] in beat_starts: sc += 1; why.append("ends a beat")
    nums = sum(1 for k in range(a, b + 1) if has_num(S[k]["text"]))
    sc += min(nums, 4) * 0.6
    if any(t in PAYOFF for t in lw) or has_num(last["text"]): sc += 1; why.append("payoff in last line")
    if last["text"].rstrip().endswith("?"): sc -= 2; why.append("ends on a question")
    nxt = words[last["i1"] + 1]["start"] - last["end"] if last["i1"] + 1 < len(words) else 1.0
    if nxt >= 0.45: sc += 0.5
    sc -= abs(dur - 38) / 12  # sweet spot ~30-45 s
    return sc, dur, why


def hook_title(first, beat_title):
    t = first["text"].strip()
    w = t.split()
    if t.endswith("?") and len(w) <= 6:
        return t.upper()
    return beat_title.upper() if beat_title else " ".join(w[:6]).rstrip(",.").upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", required=True); ap.add_argument("--trim", required=True)
    ap.add_argument("--script", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--top", type=int, default=12); ap.add_argument("--min", type=float, default=20); ap.add_argument("--max", type=float, default=55)
    a = ap.parse_args()
    words = film_words(a.words, a.trim)
    S = sentences(words)
    beats = locate_beats(script_beats(a.script), words)
    beat_starts = {b["i0"] for b in beats}
    def beat_of(i):
        cur = None
        for b in beats:
            if b["i0"] <= i: cur = b
        return cur
    # snap beat starts to sentence starts
    sent_starts = [s["i0"] for s in S]
    beat_starts = {min(sent_starts, key=lambda x: abs(x - i)) for i in beat_starts}
    cands = []
    for i in range(len(S)):
        for j in range(i, len(S)):
            d = S[j]["end"] - S[i]["start"]
            if d > a.max: break
            if d < a.min: continue
            if S[j]["ch"] == "13": continue  # outro
            sc, dur, why = score_seg(S, i, j, words, beat_starts, beat_of)
            bt = beat_of(S[i]["i0"])
            cands.append({"score": round(sc, 2), "start": round(S[i]["start"] - 0.05, 3), "end": round(S[j]["end"] + 0.12, 3),
                          "dur": round(dur + 0.17, 2), "chapter": S[i]["ch"], "beat": f'{bt["id"]} {bt["title"]}' if bt else "",
                          "first_line": S[i]["text"], "last_line": S[j]["text"],
                          "hook_title": hook_title(S[i], bt["title"] if bt else ""),
                          "text": " ".join(S[k]["text"] for k in range(i, j + 1)), "why": why,
                          "long_form_ts": fmt_ts(S[i]["start"])})
    cands.sort(key=lambda c: -c["score"])
    picked = []
    for c in cands:
        if all(min(c["end"], p["end"]) - max(c["start"], p["start"]) < 0.3 * c["dur"] for p in picked):
            picked.append(c)
        if len(picked) >= a.top: break
    for r, c in enumerate(picked, 1): c["rank"] = r
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(picked, open(a.out, "w"), indent=1)
    for c in picked:
        print(f'#{c["rank"]:2d} {c["score"]:5.2f}  {c["long_form_ts"]:>7} +{c["dur"]:4.1f}s  [{c["beat"]}]  "{c["first_line"][:70]}"  -> {c["hook_title"]}')
        print(f'      why: {", ".join(c["why"])}')


if __name__ == "__main__":
    main()
