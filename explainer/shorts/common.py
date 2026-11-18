"""Shared loaders for the Shorts tools: film-time words, sentences, script beats, style configs.

Film time = chapter offset + word time. Chapter offsets are the cumulative sums of the trimmed chapter
lengths in trim_v2.json (the join script trims each chapter at that length and concatenates)."""
import json, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # explainer/


def load_style(name_or_path):
    p = name_or_path if name_or_path.endswith(".json") else os.path.join(HERE, "styles", name_or_path + ".json")
    return json.load(open(p))


def chapter_offsets(trim_json):
    tr = json.load(open(trim_json))
    off, out = 0.0, {}
    for k in sorted(tr):
        out[k] = off
        off += tr[k] or 0.0
    return out


def film_words(words_dir, trim_json, pattern="ch{}_w.words.json"):
    """All words of the film in film time: [{word,start,end,ch}]"""
    out = []
    for ch, off in chapter_offsets(trim_json).items():
        p = os.path.join(words_dir, pattern.format(ch))
        if not os.path.exists(p):
            continue
        for w in json.load(open(p)):
            out.append({"word": w["word"], "start": round(off + w["start"], 3), "end": round(off + w["end"], 3), "ch": ch})
    return out


END_RE = re.compile(r"[.?!][\"')\]]*$")


def sentences(words):
    """Split words into sentences at . ? ! (abbreviation-free VO text, numbers are spelled out)."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if END_RE.search(w["word"]) or i == len(words) - 1 or words[i + 1]["ch"] != w["ch"]:
            ws = [words[j] for j in cur]
            out.append({"i0": cur[0], "i1": cur[-1], "start": ws[0]["start"], "end": ws[-1]["end"], "ch": ws[0]["ch"],
                        "text": " ".join(x["word"] for x in ws)})
            cur = []
    return out


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower().replace("-", " ")).split()


def script_beats(script_md):
    """Beats from a SCRIPT.md: '### 1.3 Title (...)' followed by '> spoken text' lines."""
    beats, cur = [], None
    for line in open(script_md):
        m = re.match(r"^###\s+(\d+)\.(\d+)\s+(.+?)\s*(\(.*)?$", line)
        if m:
            cur = {"id": f"{m.group(1)}.{m.group(2)}", "title": m.group(3).strip(), "text": ""}
            beats.append(cur)
        elif cur is not None and line.startswith(">"):
            cur["text"] += " " + line[1:].strip()
    return [b for b in beats if b["text"].strip()]


def locate_beats(beats, words):
    """Find the word index where each beat's spoken text starts (first 4 normalised words, in order)."""
    toks = [" ".join(norm(w["word"])) for w in words]
    pos = 0
    for b in beats:
        key = norm(b["text"])[:4]
        b["i0"] = None
        for i in range(pos, len(words) - len(key)):
            seq = " ".join(toks[i:i + 8]).split()[:len(key)]
            if seq == key:
                b["i0"] = i; pos = i + 1; break
    return [b for b in beats if b["i0"] is not None]


def fmt_ts(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"
