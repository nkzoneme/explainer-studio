#!/usr/bin/env python3
"""Plagiarism guard: shared word n-grams between our script and a source transcript.

Usage: overlap_check.py OUR_SCRIPT.md THEIR_transcript.txt [--n 6] [--allow ALLOW.txt]

Both files are normalised (lowercase, markdown/timestamps/punctuation stripped, numbers kept as words).
Every n-gram of >= n consecutive shared words is reported as a merged run with line locations in both
files. --allow FILE: one word or phrase per line (proper nouns, numbers, e.g. "acme corp", "lazarus group",
"september 10th"); an n-gram made ONLY of allowed words is ignored. Exit 1 if any shared run remains, else 0.
"""
import argparse, re, sys

def norm_words(path, strip_ts):
    out = []  # (word, lineno)
    for i, line in enumerate(open(path, encoding="utf8", errors="replace"), 1):
        if strip_ts:
            line = re.sub(r"^\s*\[\d+:\d+(?::\d+)?\]\s*", "", line)
        line = re.sub(r"&nbsp;|<[^>]+>", " ", line)
        line = line.lower().replace("’", "'").replace("'", "")
        line = re.sub(r"[^a-z0-9]+", " ", line)
        out += [(w, i) for w in line.split()]
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ours"); ap.add_argument("theirs")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--allow")
    a = ap.parse_args()
    allowed = set()
    if a.allow:
        for l in open(a.allow, encoding="utf8"):
            allowed.update(norm_text(l))
    ours, theirs = norm_words(a.ours, False), norm_words(a.theirs, True)
    n = a.n
    idx = {}
    for j in range(len(theirs) - n + 1):
        idx.setdefault(tuple(w for w, _ in theirs[j:j + n]), []).append(j)
    hits = []  # (i, j) start positions
    for i in range(len(ours) - n + 1):
        g = tuple(w for w, _ in ours[i:i + n])
        if all(w in allowed for w in g):
            continue
        for j in idx.get(g, []):
            hits.append((i, j))
    # merge consecutive hits on the same diagonal into runs
    runs = []
    for i, j in sorted(hits):
        if runs and runs[-1][0] + runs[-1][2] - n + 1 == i and runs[-1][1] + runs[-1][2] - n + 1 == j:
            runs[-1][2] += 1
        else:
            runs.append([i, j, n])
    for i, j, ln in runs:
        text = " ".join(w for w, _ in ours[i:i + ln])
        print(f'{ln} words | ours line {ours[i][1]}-{ours[i+ln-1][1]} | theirs line {theirs[j][1]}-{theirs[j+ln-1][1]} | "{text}"')
    print(f"{len(runs)} shared run(s) of >= {n} words", file=sys.stderr)
    sys.exit(1 if runs else 0)

def norm_text(s):
    s = s.lower().replace("’", "'").replace("'", "")
    return re.sub(r"[^a-z0-9]+", " ", s).split()

if __name__ == "__main__":
    main()
