#!/usr/bin/env python3
"""One-shot machine QA for a finished film (G4 pre-check). Usage:
  python3 kit/tools/qa_film.py <final.mp4> <project_dir> [--channel <slug>] [--out <dir>] [--srt <file>] [--fast] [--jobs N]
    <project_dir> = explainer/film/<name>   (chNN/out/chNN_raw.mp4, chNN/index.html, final/*.srt; voice in explainer/vo/<name>/chNN_w.*)
Writes <out>/QA_FILM.md, <out>/QA_FILM.json, <out>/join_frames.jpg, <out>/contact/chNN_contact_2fps.jpg
(default out = <project_dir>/qa_film/ ; it never touches the final or the chapter renders). Exit code 1 if any check is FAIL.
Thresholds come from explainer/channels/<slug>/style.json (pace, host, sound.sfx_hits_per_min); the channel is guessed from
channels/*/videos/<name> unless --channel is given. Loudness/format limits are constants below (-14 LUFS, TP <= -1.0).
Checks: format, duration vs trimmed chapters, chapter-start frames (trim applied / right build), black flashes, freeze,
silence, loudness + true peak + sample peak after decode, pace, SFX bus/density per chapter, SRT vs words.json,
render freshness (+ stale voice, html duration), host share, render queue / zombie pollers, join sheet, 2 fps contact sheets.
HOST SHARE: pixel measurement was tried (template matching of the host head with OpenCV) and does NOT discriminate
(scores 0.55-0.74 with and without the host). So it reports (a) the share DECLARED in each index.html header comment
('host visible ... N s = N %') and (b) a structural UPPER BOUND = scenes (data-start/duration) that contain a host element.
--fast skips the per-chapter qa_audio runs and the pace decode."""
import argparse, concurrent.futures as cf, difflib, hashlib, importlib.util, json, math, os, pathlib, re, subprocess, sys, time
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
C = dict(lufs_target=-14.0, lufs_tol=1.0, tp_max=-1.0, sample_peak_max=-1.0, dur_tol_s=0.15, black_d=0.03, black_pix=0.10,
         freeze_d=1.0, freeze_fail_s=1.2, silence_noise=-45, silence_d=0.9, silence_fail_s=1.5, tail_s=15.0,
         sfx_bus_db=(10.0, 18.0), srt_drift_s=1.5, srt_max_cue_s=8.0, boundary_mad=14.0, queue_cap=4)
SFX_TOL = 1.15   # qa_audio onset counting is approximate (about +/- 15 %)
R = {}


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def rec(name, status, detail, data=None, thresholds=None):
    R[name] = {"status": status, "detail": detail, "data": data or {}, "thresholds": thresholds or {}}


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def probe(p):
    return json.loads(sh(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(p)]).stdout)


# ---------------------------------------------------------------- project model
def load_project(proj):
    name = proj.name
    chs = []
    for d in sorted(proj.glob("ch[0-9][0-9]")):
        n = d.name[2:]
        voice = d / "assets" / "vo" / f"ch{n}_w.mp3"
        master = ROOT / "vo" / name / f"ch{n}_w.mp3"
        chs.append(dict(ch=f"ch{n}", n=n, dir=d, raw=d / "out" / f"ch{n}_raw.mp4", words=ROOT / "vo" / name / f"ch{n}_w.words.json",
                        voice=voice if voice.exists() else master, master_voice=master, html=d / "index.html"))
    chs = [c for c in chs if c["raw"].exists() or c["html"].exists()]
    for i, c in enumerate(chs):
        last = i == len(chs) - 1
        c["trim"] = None
        if c["raw"].exists():
            c["raw_dur"] = float(probe(c["raw"])["format"]["duration"])
        if c["words"].exists() and not last:   # build_final.py rule: last word + 0.6 s snapped up to a frame
            w = json.load(open(c["words"]))
            c["trim"] = math.ceil((w[-1]["end"] + 0.6) * 30) / 30
        if last and c.get("raw_dur"):          # last chapter untrimmed
            c["trim"] = math.floor(c["raw_dur"] * 30) / 30
    t = 0.0
    for c in chs:
        c["start"] = t
        t += c["trim"] or 0.0
        c["end"] = t
    return chs, t


def guess_channel(name):
    chans = sorted(p.name for p in (ROOT / "channels").iterdir() if p.is_dir() and not p.name.startswith("_"))
    for s in chans:
        if (ROOT / "channels" / s / "videos" / name).exists():
            return s
    return chans[0] if chans else None


def chapter_of(chs, t):
    for c in chs:
        if c["start"] <= t < c["end"] + 1e-6:
            return c["ch"]
    return chs[-1]["ch"] if chs else "?"


# ---------------------------------------------------------------- ffmpeg scans
def video_scan(film, chs, dur):
    e = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(film), "-an", "-vf",
            f"scale=640:360,blackdetect=d={C['black_d']}:pix_th={C['black_pix']},freezedetect=n=-50dB:d={C['freeze_d']}", "-f", "null", "-"]).stderr
    blacks = [(float(a), float(b), float(d)) for a, b, d in re.findall(r"black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)", e)]
    fs = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", e)]
    fd = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", e)]
    if len(fs) > len(fd):
        fd.append(round(dur - fs[-1], 3))
    freezes = list(zip(fs, fd))
    bad = [b for b in blacks if b[0] > 0.2 and b[1] < dur - 0.2]
    if bad:
        rec("blackdetect", "FAIL", f"{len(bad)} black hit(s) not at film start/end: " + "; ".join(f"{fmt(a)} ({chapter_of(chs, a)}, {d:.2f}s)" for a, _, d in bad[:12]),
            {"hits": blacks}, {"d": C["black_d"], "pix_th": C["black_pix"]})
    else:
        rec("blackdetect", "PASS", f"no black frames outside film start/end ({len(blacks)} at the edges)", {"hits": blacks}, {"d": C["black_d"]})
    long = [(a, d) for a, d in freezes if d > C["freeze_fail_s"]]
    last = chs[-1] if chs else None
    def tag(a):
        return f"{chapter_of(chs, a)}" + (", END PLATE" if last and a >= last["end"] - 15 else "")
    if long:
        rec("freeze", "FAIL", f"{len(long)} static stretch(es) > {C['freeze_fail_s']}s: " + "; ".join(f"{fmt(a)} {d:.1f}s ({tag(a)})" for a, d in long[:12]),
            {"freezes": freezes}, {"max_static_s": C["freeze_fail_s"]})
    else:
        rec("freeze", "WARN" if freezes else "PASS", f"no static stretch over {C['freeze_fail_s']}s" + (f"; {len(freezes)} of 1.0-{C['freeze_fail_s']}s: " + "; ".join(f"{fmt(a)} {d:.2f}s ({tag(a)})" for a, d in freezes[:8]) if freezes else ""),
            {"freezes": freezes}, {"max_static_s": C["freeze_fail_s"]})


def audio_scan(film, chs, dur):
    e = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(film), "-vn", "-af",
            f"silencedetect=noise={C['silence_noise']}dB:d={C['silence_d']},volumedetect,ebur128=peak=true", "-f", "null", "-"]).stderr
    starts = [max(0.0, float(x)) for x in re.findall(r"silence_start: (-?[\d.]+)", e)]
    durs = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", e)]
    if len(starts) > len(durs):
        durs.append(dur - starts[-1])
    sil = list(zip(starts, durs))
    bad = [(a, d) for a, d in sil if d >= C["silence_fail_s"] and a < dur - C["tail_s"]]
    warn = [(a, d) for a, d in sil if C["silence_d"] <= d < C["silence_fail_s"] and a < dur - C["tail_s"]]
    msg = ""
    if bad: msg += f"{len(bad)} gap(s) >= {C['silence_fail_s']}s: " + "; ".join(f"{fmt(a)} {d:.1f}s ({chapter_of(chs, a)})" for a, d in bad[:10])
    if warn: msg += f" {len(warn)} gap(s) 0.9-1.5s: " + "; ".join(f"{fmt(a)} {d:.1f}s" for a, d in warn[:10])
    rec("silence", "FAIL" if bad else ("WARN" if warn else "PASS"), msg or "no silence >= 0.9 s before the end tail", {"silences": sil},
        {"noise_db": C["silence_noise"], "fail_s": C["silence_fail_s"]})
    tail = e[e.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
    lra = float(re.search(r"LRA:\s+(-?[\d.]+) LU", tail).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))
    mx = re.findall(r"max_volume: (-?[\d.]+) dB", e)
    rec("loudness", "FAIL" if abs(I - C["lufs_target"]) > C["lufs_tol"] else "PASS", f"integrated {I} LUFS (target {C['lufs_target']} +/- {C['lufs_tol']}), LRA {lra}",
        {"I": I, "LRA": lra}, {"I": C["lufs_target"], "tol": C["lufs_tol"]})
    rec("true_peak", "FAIL" if tp > C["tp_max"] else "PASS", f"true peak {tp} dBTP decoded from the final (limit {C['tp_max']})", {"tp": tp}, {"max_dbtp": C["tp_max"]})
    if mx:
        m = float(mx[-1])
        rec("max_sample", "FAIL" if m > C["sample_peak_max"] else "PASS", f"max sample {m} dBFS (limit {C['sample_peak_max']})", {"max_volume": m}, {"max_db": C["sample_peak_max"]})


# ---------------------------------------------------------------- format, duration, boundaries
def check_format(film, chs, total):
    j = probe(film)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    issues = []
    if v["codec_name"] != "h264": issues.append(f"video codec {v['codec_name']}")
    if (v["width"], v["height"]) != (1920, 1080): issues.append(f"size {v['width']}x{v['height']}")
    num, den = map(int, v["r_frame_rate"].split("/"))
    if abs(num / den - 30) > 0.01: issues.append(f"fps {num / den:.3f}")
    if v.get("pix_fmt") != "yuv420p": issues.append(f"pix_fmt {v.get('pix_fmt')}")
    if a is None: issues.append("no audio")
    else:
        if a["codec_name"] != "aac": issues.append(f"audio codec {a['codec_name']}")
        if int(a["sample_rate"]) != 48000: issues.append(f"audio rate {a['sample_rate']}")
    fd = float(j["format"]["duration"])
    vd = float(v.get("duration") or fd); ad = float(a.get("duration") or fd) if a else vd
    if abs(vd - ad) > 0.1: issues.append(f"A/V duration differ {vd:.2f}/{ad:.2f}")
    head = open(film, "rb").read(65536)
    faststart = head.find(b"moov") != -1 and (head.find(b"mdat") == -1 or head.find(b"moov") < head.find(b"mdat"))
    rec("format", "FAIL" if issues else ("PASS" if faststart else "WARN"),
        (", ".join(issues) if issues else f"h264 1920x1080 30 fps yuv420p, aac {a['sample_rate']} Hz {a.get('channels')} ch, {int(j['format']['bit_rate']) // 1000} kb/s") +
        ("" if faststart else " | moov atom not at the start (no faststart)"), {"video_duration": vd, "audio_duration": ad})
    diff = fd - total
    miss = [c["ch"] for c in chs if not c["trim"]]
    rec("duration", "FAIL" if abs(diff) > C["dur_tol_s"] or miss else "PASS",
        f"film {fd:.2f}s vs sum of trimmed chapters {total:.2f}s (diff {diff:+.2f}s, tol {C['dur_tol_s']}s)" + (f"; no trim data for {miss}" if miss else ""),
        {"film": fd, "expected": total, "trims": {c["ch"]: c["trim"] for c in chs}}, {"tol_s": C["dur_tol_s"]})
    return fd


def frames_at(path, times, size=(64, 36)):
    out = []
    for t in times:
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t):.3f}", "-i", str(path), "-frames:v", "1", "-vf", f"scale={size[0]}:{size[1]},format=gray",
                            "-f", "rawvideo", "-"], capture_output=True).stdout
        out.append(np.frombuffer(r, np.uint8).astype(np.float64).reshape(size[1], size[0]) if len(r) == size[0] * size[1] else None)
    return out


def check_boundaries(film, chs):
    """Frame at start+x in the final must match frame at x in chNN_raw.mp4 (trim applied, right build, right order)."""
    bad, rows = [], {}
    for c in chs:
        if not c["raw"].exists() or not c["trim"]:
            continue
        offs = [1.0, 3.0, max(1.0, min(c["trim"] - 1.0, 10.0))]
        d = [float(np.abs(x - y).mean()) for x, y in zip(frames_at(film, [c["start"] + o for o in offs]), frames_at(c["raw"], offs)) if x is not None and y is not None]
        med = round(float(np.median(d)), 1) if d else 999
        rows[c["ch"]] = med
        if med > C["boundary_mad"]: bad.append(f"{c['ch']} MAD {med}")
    rec("chapter_boundaries", "FAIL" if bad else "PASS",
        ("final does not match the chapter render at the expected offset (trim/order/old build): " + ", ".join(bad)) if bad else
        f"{len(rows)} chapters: frames in the final match chNN_raw.mp4 at the expected offsets (median abs diff <= {C['boundary_mad']}/255)", {"mad": rows}, {"mad_max": C["boundary_mad"]})


def check_pace(film, style_path):
    spec = importlib.util.spec_from_file_location("qa_pace", TOOLS / "qa_pace.py")
    qp = importlib.util.module_from_spec(spec); spec.loader.exec_module(qp)
    m = qp.measure(film); t, _ = qp.targets(style_path)
    p = []
    if m["per_min"] < t["min_per_min"]: p.append(f"{m['per_min']} changes/min < {t['min_per_min']}")
    busy = bool(t.get("max_per_min") and m["per_min"] > t["max_per_min"])   # busier than the style range: WARN, not FAIL
    if m["first_60s_per_min"] < t["first_60s_min"]: p.append(f"first 60 s {m['first_60s_per_min']}/min < {t['first_60s_min']}")
    if m["median_gap_s"] > t["median_gap_max_s"]: p.append(f"median gap {m['median_gap_s']}s > {t['median_gap_max_s']}")
    if m["longest_gap_s"] > t["max_gap_s"]: p.append(f"longest same-framing gap {m['longest_gap_s']}s > {t['max_gap_s']}")
    if "still_share_max" in t and m["still_share"] > t["still_share_max"]: p.append(f"near-still {m['still_share']:.0%} > {t['still_share_max']:.0%}")
    longs = [(a, g) for a, g in m["gaps"] if g > t["long_gap_s"]]
    rec("pace", "FAIL" if p else ("WARN" if busy else "PASS"),
        ("; ".join(p) if p else f"{m['per_min']}/min, first 60 s {m['first_60s_per_min']}/min, median gap {m['median_gap_s']}s, longest {m['longest_gap_s']}s, still {m['still_share']:.0%}") + (f" | HIGH: {m['per_min']}/min > style max {t['max_per_min']}" if busy else "") +
        (f" | {len(longs)} gap(s) > {t['long_gap_s']}s at " + ", ".join(fmt(a) for a, _ in longs[:8]) if longs else ""),
        {k: m[k] for k in m if k != "gaps"}, t)


# ---------------------------------------------------------------- SFX per chapter
def run_qa_audio(c):
    if not (c["raw"].exists() and c["voice"].exists()):
        return c["ch"], None
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")   # numpy BLAS threads pile up on a busy box
    e = subprocess.run([sys.executable, str(TOOLS / "qa_audio.py"), str(c["raw"]), str(c["voice"])], capture_output=True, text=True, env=env)
    o = e.stdout
    m1 = re.search(r"SFX bus is ([\d.-]+) dB under the voice", o); m2 = re.search(r"= (\d+) per minute", o)
    m4 = re.search(r"loudest SFX 20 ms frame (-?[\d.]+) dB vs loudest voice frame (-?[\d.]+) dB", o)
    if not (m1 and m2):
        return c["ch"], {"error": (e.stderr or o)[-200:]}
    return c["ch"], {"bus_db": float(m1.group(1)), "per_min": int(m2.group(1)), "sfx_peak_over_voice": (float(m4.group(1)) > float(m4.group(2))) if m4 else None}


def check_sfx(chs, style, jobs):
    s = style.get("sound", {}).get("sfx_hits_per_min", {})
    body = s.get("body", [0, 999]); hook_max = s.get("hook_max", 999)
    with cf.ThreadPoolExecutor(jobs) as ex:
        res = dict(ex.map(run_qa_audio, chs))
    bad, warn = [], []
    for i, c in enumerate(chs):
        r = res.get(c["ch"])
        if not r or "error" in r: continue
        hi = hook_max if i == 0 else body[1]
        if r["per_min"] > hi * SFX_TOL: bad.append(f"{c['ch']} {r['per_min']}/min > {hi} (+15 % detector tolerance)")
        elif r["per_min"] > hi: warn.append(f"{c['ch']} {r['per_min']}/min slightly over {hi}")
        if r["bus_db"] < C["sfx_bus_db"][0]: bad.append(f"{c['ch']} SFX bus only {r['bus_db']} dB under voice (< {C['sfx_bus_db'][0]})")
        if r.get("sfx_peak_over_voice"): warn.append(f"{c['ch']} an SFX frame is louder than the loudest voice frame")
    ok = [r for r in res.values() if r and "bus_db" in r]
    if not ok:
        rec("sfx_vs_voice", "SKIP", "no chNN/out raw + voice mp3 pairs", res); return
    rec("sfx_vs_voice", "FAIL" if bad else ("WARN" if warn else "PASS"),
        ("; ".join(bad) if bad else f"{len(ok)} chapters: bus {min(r['bus_db'] for r in ok)}-{max(r['bus_db'] for r in ok)} dB under voice, SFX {min(r['per_min'] for r in ok)}-{max(r['per_min'] for r in ok)}/min (body limit {body[1]}, hook {hook_max})") +
        ((" | warn: " + "; ".join(warn)) if warn else ""), res, {"bus_db": C["sfx_bus_db"], "body_per_min": body, "hook_max": hook_max})


# ---------------------------------------------------------------- SRT vs words
_U = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split())}
_T = {w: 10 * i for i, w in enumerate("x x twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "x"}
_O = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12,
      "thirteenth": 13, "fourteenth": 14, "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19, "twentieth": 20, "thirtieth": 30}
_YR = {"nineteen", "eighteen", "seventeen", "sixteen", "twenty"}


def _small(tk, i):
    """parse 0-99 at tk[i:]; returns (value, next_i) or None"""
    if i < len(tk) and tk[i] in _T:
        if i + 1 < len(tk) and tk[i + 1] in _U and 1 <= _U[tk[i + 1]] <= 9: return _T[tk[i]] + _U[tk[i + 1]], i + 2
        return _T[tk[i]], i + 1
    if i < len(tk) and tk[i] in _U: return _U[tk[i]], i + 1
    return None


def numberize(tk):
    """returns [(token, index of its first source token)]. Spoken number words -> digits so '$100 million' and 'a hundred million dollars' compare equal; spelled-out letters -> one token."""
    out, i = [], 0
    while i < len(tk):
        t = tk[i]
        i0 = i
        if t in _O: out.append((str(_O[t]), i0)); i += 1; continue
        if t == "a" and i + 1 < len(tk) and tk[i + 1] in ("hundred", "thousand"): i += 1; t = tk[i]
        sm = _small(tk, i) if t not in ("hundred", "thousand") else None
        if sm is None and t not in ("hundred", "thousand"): out.append((t, i0)); i += 1; continue
        if sm and t in _YR:    # year: 'twenty twenty three', 'nineteen eighty four', 'twenty nineteen'
            sm2 = _small(tk, sm[1]) if sm[1] < len(tk) else None
            if sm[0] in (19, 20, 18, 17, 16) and sm2 and (sm2[0] >= 10 or (tk[sm[1]] in _T)) and tk[sm[1]] not in ("hundred", "thousand"):
                out.append((str(sm[0] * 100 + sm2[0]), i0)); i = sm2[1]; continue
        val, j = (sm if sm else (1, i))
        while j < len(tk) and tk[j] in ("hundred", "thousand"):
            val *= 100 if tk[j] == "hundred" else 1000; j += 1
            k = j + 1 if (j < len(tk) and tk[j] == "and" and _small(tk, j + 1)) else j
            sm3 = _small(tk, k)
            if sm3: val += sm3[0]; j = sm3[1]
        out.append((str(val), i0)); i = j
    # runs of single letters (spelled acronyms: 'c i s a') -> one token
    res, k = [], 0
    while k < len(out):
        j = k
        while j < len(out) and len(out[j][0]) == 1 and out[j][0].isalpha(): j += 1
        if j - k >= 2: res.append(("".join(x for x, _ in out[k:j]), out[k][1])); k = j
        else: res.append(out[k]); k += 1
    return res


def norm_tok(w):
    w = w.lower().replace("’", "'")
    w = re.sub(r"(?<=\d),(?=\d)", "", w)
    w = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", w)
    w = w.replace("%", " percent ").replace("$", " ")
    w = re.sub(r"[-—–/]", " ", w)
    w = re.sub(r"[^\w'. ]", " ", w)
    return [t for t in (x.strip(".'") for x in w.split()) if t and t not in ("dollar", "dollars")]


def parse_srt(p):
    cues = []
    for blk in re.split(r"\n\s*\n", pathlib.Path(p).read_text(encoding="utf-8").strip()):
        ln = blk.strip().splitlines()
        if len(ln) < 3: continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+) --> (\d+):(\d+):(\d+)[,.](\d+)", ln[1])
        if not m: continue
        g = list(map(int, m.groups()))
        cues.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, "\n".join(ln[2:])))
    return cues


def check_srt(srt, chs, dur):
    if not srt or not pathlib.Path(srt).exists():
        rec("srt_vs_words", "FAIL", "no SRT found in final/ (pass --srt)"); return
    cues = parse_srt(srt)
    src = [(t, c["start"] + w["start"]) for c in chs if c["words"].exists() for w in json.load(open(c["words"])) for t in norm_tok(w["word"])]
    exp = [(t, src[i][1]) for t, i in numberize([t for t, _ in src])]
    if not exp:
        rec("srt_vs_words", "SKIP", "no words.json"); return
    gsrc = [(tk, i) for i, (_, _, t) in enumerate(cues) for tk in norm_tok(t)]
    got = [(t, gsrc[i][1]) for t, i in numberize([t for t, _ in gsrc])]
    sm = difflib.SequenceMatcher(None, [t for t, _ in exp], [t for t, _ in got], autojunk=False)
    mism, drift = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                ci = got[j1 + k][1]
                if j1 + k == 0 or got[j1 + k - 1][1] != ci: drift.append((cues[ci][0] - exp[i1 + k][1], exp[i1 + k][1]))
        else:
            mism.append((" ".join(t for t, _ in exp[i1:i2]), " ".join(t for t, _ in got[j1:j2]), exp[min(i1, len(exp) - 1)][1], op))
    numfmt = [m for m in mism if re.search(r"\d", m[0] + m[1])]
    wordm = [m for m in mism if m not in numfmt]
    art = [(cues[i][0], t.replace("\n", " ")) for i, (_, _, t) in enumerate(cues) if re.search(r"\b(about|around|roughly|nearly|almost|over|just|only|some) an? \$?\d", t, re.I)]
    tim, longl = [], []
    for i, (a, b, t) in enumerate(cues):
        if b <= a: tim.append(f"cue {i + 1} end<=start")
        if i and a < cues[i - 1][1] - 0.01: tim.append(f"cue {i + 1} overlaps previous")
        if b - a > C["srt_max_cue_s"]: tim.append(f"cue {i + 1} {b - a:.1f}s long")
        if max(len(x) for x in t.splitlines()) > 42: longl.append(i + 1)
    if cues and cues[-1][1] > dur + 0.5: tim.append(f"last cue ends {cues[-1][1]:.1f}s, film is {dur:.1f}s")
    mx = max((abs(d) for d, _ in drift), default=0)
    worst = max(drift, key=lambda x: abs(x[0]), default=(0, 0))
    bad = bool(mism or art or tim or mx > C["srt_drift_s"])
    parts = [f"{len(cues)} cues, {len(exp)} spoken / {len(got)} SRT tokens, {len(mism)} mismatched span(s) ({len(numfmt)} number-format, {len(wordm)} word), max timing drift {mx:.2f}s (at {fmt(worst[1])})"]
    if art: parts.append("article+number: " + "; ".join(f"{fmt(a)} '{t}'" for a, t in art[:6]))
    if tim: parts.append("timing: " + "; ".join(tim[:6]))
    if longl: parts.append(f"{len(longl)} cue line(s) > 42 chars (style note, not a FAIL; first: {longl[:5]})")
    rec("srt_vs_words", "FAIL" if bad else ("WARN" if longl else "PASS"), " | ".join(parts),
        {"srt": str(srt), "number_format": [dict(spoken=m[0], srt=m[1], t=round(m[2], 1)) for m in numfmt], "word_mismatch": [dict(spoken=m[0], srt=m[1], t=round(m[2], 1), op=m[3]) for m in wordm],
         "article_number": art, "timing": tim, "max_drift_s": mx}, {"drift_s": C["srt_drift_s"]})


# ---------------------------------------------------------------- freshness, host, queue
def newest(path):
    best = (0.0, None)
    for p in (path.rglob("*") if path.is_dir() else [path]):
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() not in (".md", ".txt", ".log", ".bak") and not p.name.upper().startswith("CREDITS"):   # notes/credits are not render inputs
            m = p.stat().st_mtime
            if m > best[0]: best = (m, p)
    return best


def check_freshness(film, chs):
    bad, ok = [], 0
    fm = film.stat().st_mtime
    for c in chs:
        if not c["raw"].exists():
            bad.append(f"{c['ch']} no raw render"); continue
        rm = c["raw"].stat().st_mtime
        deps = [c["html"]] + [d for d in (c["dir"] / "assets", c["dir"] / "kit", c["dir"] / "levels.js", c["dir"] / "words.js", c["dir"] / "pt.css") if d.exists()]
        stale = None
        for d in deps:
            m, p = newest(d)
            if p and m > rm + 1:
                stale = f"{c['ch']}: {p.relative_to(c['dir'])} is {(m - rm) / 60:.0f} min newer than {c['raw'].name}"; break
        if stale: bad.append(stale)
        else: ok += 1
        if c["voice"].exists() and c["master_voice"].exists() and c["voice"] != c["master_voice"] and hashlib.md5(c["voice"].read_bytes()).hexdigest() != hashlib.md5(c["master_voice"].read_bytes()).hexdigest():
            bad.append(f"{c['ch']}: assets/vo mp3 differs from vo/ master (stale voice)")
        if c["html"].exists() and c.get("raw_dur"):
            m = re.search(r'data-composition-id="main"[^>]*data-duration="([\d.]+)"', c["html"].read_text(errors="ignore"))
            if m and abs(float(m.group(1)) - c["raw_dur"]) > 0.15:
                bad.append(f"{c['ch']}: index.html duration {m.group(1)}s vs render {c['raw_dur']:.2f}s")
        if fm < rm - 1: bad.append(f"{c['ch']}: raw render is newer than the final (final not rebuilt)")
    rec("render_freshness", "FAIL" if bad else "PASS", ("; ".join(bad[:14]) if bad else f"all {ok} chapter renders newer than their index.html, assets, kit; voice masters identical; final newer than every raw"), {"problems": bad})


def check_host(chs, style, total):
    h = style.get("host", {}); vs = h.get("visible_share", {}); cmax = h.get("chapter_max_share", 0.6)
    rows, dsum, usum = [], 0.0, 0.0
    for c in chs:
        L = c["trim"] or 0
        if not c["html"].exists() or L <= 0: continue
        txt = c["html"].read_text(errors="ignore")
        decl = None
        mm = re.search(r"host visible[^\n]*", txt, re.I)
        if mm:
            line = mm.group(0)
            if re.search(r"host visible\s*0\s*(s|%)|no host", line, re.I): decl = 0.0
            else:
                eq = re.findall(r"=\s*~?(\d+(?:\.\d+)?)\s*s\b", line)          # '14.9 + 2.75 = 17.7 s' -> last total
                ms = re.search(r"host visible[^\n]*?[≈~=]\s*~?(\d+(?:\.\d+)?)\s*s\b", line, re.I)
                mp = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
                if eq: decl = float(eq[-1])
                elif ms: decl = float(ms.group(1))
                elif mp: decl = float(mp.group(1)) / 100 * L
        src = "host visible" if decl is not None else None
        if decl is None:   # fallback: time ranges in the 'Host: ...' header comment (union of ranges, seconds)
            lines = txt[:6000].splitlines()
            for i, l in enumerate(lines):
                if re.match(r"\s*(<!--)?\s*(beat plan:.*)?host\s*:", l, re.I) or re.search(r"\bHost:\s", l):
                    blk = [l[l.lower().find("host:"):]]
                    for l2 in lines[i + 1:i + 3]:
                        if re.match(r"\s*[A-Za-z][\w /]{0,24}:", l2) or not l2.strip() or "-->" in l2: break
                        blk.append(l2)
                    rg = sorted((float(x), float(y)) for x, y in re.findall(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)", " ".join(blk)) if 0 <= float(x) < float(y) <= L + 1)
                    tot, cur2 = 0.0, None
                    for x, y in rg:
                        if cur2 and x <= cur2[1]: cur2[1] = max(cur2[1], y)
                        else:
                            if cur2: tot += cur2[1] - cur2[0]
                            cur2 = [x, y]
                    if cur2: tot += cur2[1] - cur2[0]
                    if rg or re.search(r"presenter 0|no host", " ".join(blk), re.I): decl, src = tot, "Host: ranges"
                    break
        tags = [(m.start(), m.group(0)) for m in re.finditer(r'<div id="s\d+" class="scene[^>]*>', txt)]
        iv = []
        for i, (pos, tag) in enumerate(tags):
            body = txt[pos:(tags[i + 1][0] if i + 1 < len(tags) else len(txt))]
            if re.search(r'charwrap|class="[^"]*\bhost|host_[a-z_]+\.webp', body):
                a = re.search(r'data-start="([\d.]+)"', tag); d = re.search(r'data-duration="([\d.]+)"', tag)
                if a and d: iv.append((float(a.group(1)), min(L, float(a.group(1)) + float(d.group(1)))))
        iv.sort(); un, cur = 0.0, None
        for a, b in iv:
            if cur is None or a > cur[1]:
                if cur: un += cur[1] - cur[0]
                cur = [a, b]
            else: cur[1] = max(cur[1], b)
        if cur: un += cur[1] - cur[0]
        rows.append(dict(ch=c["ch"], source=src, len=round(L, 1), declared_s=None if decl is None else round(decl, 1), declared_share=None if decl is None else round(decl / L, 3), scene_upper_bound_s=round(un, 1)))
        dsum += decl or 0.0; usum += un
    if not rows:
        rec("host_share", "SKIP", "no index.html"); return
    undecl = [r["ch"] for r in rows if r["declared_s"] is None]
    share, ub = dsum / total, usum / total
    lo, hi, tg = vs.get("min", 0), vs.get("max", 1), vs.get("target", 0)
    pr = []
    partial = bool(undecl)
    if share < lo and not partial: pr.append(f"declared film share {share:.1%} < style min {lo:.0%}")
    elif share < lo: pr.append(f"declared share so far {share:.1%} is < style min {lo:.0%} but {len(undecl)} chapter(s) have no parsable figure")
    if share > hi: pr.append(f"declared film share {share:.1%} > style max {hi:.0%}")
    if usum > 0 and ub < lo: pr.append(f"even the scene upper bound {ub:.1%} < {lo:.0%}")
    for r in rows:
        if r["declared_share"] and r["declared_share"] > cmax: pr.append(f"{r['ch']} {r['declared_share']:.0%} > chapter max {cmax:.0%}")
        if usum > 0 and r["scene_upper_bound_s"] > 0 and r["declared_s"] and r["declared_s"] > r["scene_upper_bound_s"] + 1.0: pr.append(f"{r['ch']} declares {r['declared_s']}s but scenes with a host total {r['scene_upper_bound_s']}s")
    hard = [x for x in pr if "no parsable" not in x]
    rec("host_share", "FAIL" if hard else ("WARN" if (pr or share < tg * 0.8 or undecl) else "PASS"),
        f"declared (index.html comments) {share:.1%} of film; scene upper bound {'n/a (scene markup not recognised)' if usum == 0 else f'{ub:.1%}'}; style min/target/max {lo:.0%}/{tg:.0%}/{hi:.0%}" + (" | " + "; ".join(pr) if pr else "") +
        (f" | no declared value in {', '.join(undecl)}" if undecl else "") + " | NOT pixel-measured (template match not discriminative)",
        {"declared_share": share, "upper_bound_share": ub, "chapters": rows}, {"visible_share": vs, "chapter_max_share": cmax})


def check_factcheck(proj):
    """Independent fact-check gate: research/**/<film>/FACTCHECK.md must exist and hold no UNVERIFIED row."""
    name = proj.name
    cands = [ROOT / "research" / name / "FACTCHECK.md", ROOT / "research" / "remake" / name / "FACTCHECK.md"]
    cands += sorted((ROOT / "research").glob(f"*/{name}/FACTCHECK.md"))
    fc = next((c for c in cands if c.exists()), None)
    if not fc:
        rec("factcheck", "FAIL", f"no research/*/{name}/FACTCHECK.md (independent fact-check by a separate agent is required)"); return
    rows, bad = 0, []
    for l in fc.read_text(errors="ignore").splitlines():
        if not l.startswith("|"): continue
        cells = [c.strip().strip("*` ").upper() for c in l.strip().strip("|").split("|")]
        if cells and cells[0] in ("ID", "CLAIM") or set(l.strip("|").replace(" ", "")) <= set("-:|"): continue
        rows += 1
        if any(w in cells for w in ("UNVERIFIED", "WRONG", "FALSE", "INCORRECT")): bad.append(cells[0])
    if rows == 0: rec("factcheck", "FAIL", f"{fc.relative_to(ROOT)} has no claim table rows")
    elif bad: rec("factcheck", "FAIL", f"{len(bad)} UNVERIFIED row(s) in {fc.relative_to(ROOT)}: {', '.join(bad[:12])}; verify or cut the claim", {"unverified": bad})
    else: rec("factcheck", "PASS", f"{fc.relative_to(ROOT)}: {rows} rows, none UNVERIFIED", {"rows": rows})


def check_hook(chs, slug, title):
    """Runs qa_hook on chapter 1 (words from vo/<film>/ch01_w.words.json, script beside research, thumbnails in film/<name>/thumbs)."""
    if not chs: rec("hook", "FAIL", "no chapters"); return
    try:
        sys.path.insert(0, str(TOOLS)); import qa_hook
        c = chs[0]; r = qa_hook.run(str(c["dir"]), slug, title=title, words_path=str(c["words"]) if c["words"].exists() else None, video=c["raw"].exists())
        bad = r.get("fails", []); warn = [k for k, v in r["checks"].items() if v["status"] == "WARN"]
        det = "; ".join(f"{k}: {r['checks'][k]['detail'][:120]}" for k in bad) or "all hook checks pass"
        rec("hook", "FAIL" if bad else ("WARN" if warn else "PASS"), det + (f" | WARN {', '.join(warn)}" if warn else ""), {"checks": {k: v["status"] for k, v in r["checks"].items()}})
    except Exception as e:
        rec("hook", "FAIL", f"qa_hook crashed: {e}")


def check_queue():
    out = sh(["ps", "-eo", "pid,etimes,args"]).stdout.splitlines()[1:]
    me = {str(os.getpid()), str(os.getppid())}
    ren = [l for l in out if re.search(r"hyperframes\S* .*render|hyperframes render", l) and "qa_film" not in l and l.split()[0] not in me]
    poll = [l for l in out if re.search(r"\b(while|until)\b.*(pgrep|grep|-f )", l) and "qa_film" not in l and "ps -eo" not in l and l.split()[0] not in me]
    old = [l for l in poll if int(l.split()[1]) > 3600]
    rec("render_queue", "FAIL" if len(ren) > C["queue_cap"] else ("WARN" if old else "PASS"),
        f"{len(ren)} hyperframes render process(es) running now (cap {C['queue_cap']}); {len(poll)} wait-loop shell(s), {len(old)} older than 1 h" + "".join(f" | zombie? {l.strip()[:110]}" for l in old[:3]),
        {"renders": len(ren), "pollers": len(poll)}, {"cap": C["queue_cap"]})


# ---------------------------------------------------------------- sheets
def contact_sheets(film, chs, out):
    import cv2
    w, h = 192, 108
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(film), "-an", "-vf", f"fps=2,scale={w}:{h}", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    d = out / "contact"; d.mkdir(parents=True, exist_ok=True)
    paths = []
    for c in chs:
        seg = fr[int(round(c["start"] * 2)):min(len(fr), int(round(c["end"] * 2)))]
        if not len(seg): continue
        cols = 10; rows = math.ceil(len(seg) / cols)
        sheet = np.zeros((rows * h, cols * w, 3), np.uint8)
        for i, f in enumerate(seg):
            f = f.copy(); cv2.putText(f, f"{i / 2:.1f}", (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)
            sheet[(i // cols) * h:(i // cols + 1) * h, (i % cols) * w:(i % cols + 1) * w] = f
        p = d / f"{c['ch']}_contact_2fps.jpg"; cv2.imwrite(str(p), sheet, [cv2.IMWRITE_JPEG_QUALITY, 80]); paths.append(str(p))
    rec("contact_sheets", "PASS" if paths else "FAIL", f"{len(paths)} chapter sheets at 2 fps (label = seconds into chapter) in {d}", {"files": paths})


def join_sheet(film, chs, out):
    import cv2
    w, h = 256, 144; offs = [-0.5, -0.2, -0.033, 0.0, 0.2, 0.5]
    rows = []
    for c in chs[1:]:
        ims = []
        for o in offs:
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, c['start'] + o):.3f}", "-i", str(film), "-frames:v", "1", "-vf", f"scale={w}:{h}", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"], capture_output=True).stdout
            im = np.frombuffer(r, np.uint8).reshape(h, w, 3).copy() if len(r) == w * h * 3 else np.zeros((h, w, 3), np.uint8)
            cv2.putText(im, f"{c['ch']} {o:+.2f}s", (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA); ims.append(im)
        rows.append(np.hstack(ims))
    if rows:
        p = out / "join_frames.jpg"; cv2.imwrite(str(p), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 82])
        rec("join_frames", "PASS", f"{len(rows)} chapter joins, frames at {offs} s around each cut: {p} (review by eye for black or half-faded frames)", {"file": str(p)})


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film"); ap.add_argument("project")
    ap.add_argument("--channel"); ap.add_argument("--out"); ap.add_argument("--srt"); ap.add_argument("--fast", action="store_true"); ap.add_argument("--jobs", type=int, default=4); ap.add_argument("--title")
    a = ap.parse_args()
    film = pathlib.Path(a.film).resolve(); proj = pathlib.Path(a.project).resolve()
    slug = a.channel or guess_channel(proj.name)
    style_path = ROOT / "channels" / slug / "style.json"; style = json.loads(style_path.read_text())
    out = pathlib.Path(a.out).resolve() if a.out else proj / "qa_film"; out.mkdir(parents=True, exist_ok=True)
    srt = a.srt or next((str(p) for p in sorted((proj / "final").glob("*.srt")) if "_v1" not in p.name), None)
    t0 = time.time()
    chs, total = load_project(proj)
    dur = check_format(film, chs, total)
    with cf.ThreadPoolExecutor(6) as ex:
        fs = [ex.submit(video_scan, film, chs, dur), ex.submit(audio_scan, film, chs, dur), ex.submit(check_boundaries, film, chs),
              ex.submit(contact_sheets, film, chs, out), ex.submit(join_sheet, film, chs, out)]
        if not a.fast: fs += [ex.submit(check_pace, film, str(style_path)), ex.submit(check_sfx, chs, style, a.jobs)]
        check_srt(srt, chs, dur); check_freshness(film, chs); check_host(chs, style, total); check_queue(); check_factcheck(proj)
        title = a.title
        if not title:
            import qa_hook as _qh
            _sp = _qh.find_script(proj.name, None)
            _m = re.match(r"#\s*SCRIPT:\s*(.+)", _sp.read_text(errors="ignore").splitlines()[0]) if _sp else None
            title = _m.group(1).strip() if _m else None
        check_hook(chs, slug, title)
        for f in fs: f.result()
    order = ["format", "duration", "chapter_boundaries", "blackdetect", "freeze", "silence", "loudness", "true_peak", "max_sample", "pace", "sfx_vs_voice", "srt_vs_words", "render_freshness", "host_share", "render_queue", "factcheck", "hook", "join_frames", "contact_sheets"]
    checks = {k: R[k] for k in order if k in R}
    fails = [k for k, v in checks.items() if v["status"] == "FAIL"]; warns = [k for k, v in checks.items() if v["status"] == "WARN"]
    overall = "FAIL" if fails else "PASS"
    js = {"film": str(film), "project": str(proj), "channel": slug, "style": str(style_path), "overall": overall, "fails": fails, "warns": warns, "seconds": round(time.time() - t0),
          "checks": checks, "chapters": [{"ch": c["ch"], "start": round(c["start"], 3), "len": c["trim"]} for c in chs]}
    (out / "QA_FILM.json").write_text(json.dumps(js, indent=1, default=str))
    md = [f"# QA_FILM: {film.name}", "", f"Channel `{slug}` | overall **{overall}** | FAIL: {', '.join(fails) or 'none'} | WARN: {', '.join(warns) or 'none'} | {js['seconds']} s run", "",
          "| Check | Status | Detail |", "|---|---|---|"]
    for k, v in checks.items(): md.append(f"| {k} | {v['status']} | {v['detail'][:700].replace('|', '/')} |")
    table_end = len(md)
    md += ["", "## Notes"]
    for k in ("srt_vs_words", "host_share", "sfx_vs_voice"):
        v = checks.get(k)
        if not v: continue
        md += ["", f"### {k}", ""]
        if k == "srt_vs_words":
            d = v["data"]
            for x in d.get("number_format", [])[:30]: md.append(f"- number format @{fmt(x['t'])}: spoken `{x['spoken']}` vs SRT `{x['srt']}`")
            for x in d.get("word_mismatch", [])[:40]: md.append(f"- word @{fmt(x['t'])} ({x['op']}): spoken `{x['spoken']}` vs SRT `{x['srt']}`")
            for x in d.get("article_number", [])[:10]: md.append(f"- article + number @{fmt(x[0])}: `{x[1]}`")
        elif k == "host_share":
            md += ["| chapter | source | len s | declared s | declared share | scene upper bound s |", "|---|---|---|---|---|---|"]
            for r in v["data"].get("chapters", []): md.append(f"| {r['ch']} | {r['source']} | {r['len']} | {r['declared_s']} | {r['declared_share']} | {r['scene_upper_bound_s']} |")
        else:
            md += ["| chapter | SFX bus dB under voice | SFX per min |", "|---|---|---|"]
            for ch, r in v["data"].items():
                if isinstance(r, dict) and "bus_db" in r: md.append(f"| {ch} | {r['bus_db']} | {r['per_min']} |")
    md += ["", f"Thresholds: style `{style_path}`; constants {json.dumps({k: C[k] for k in ('lufs_target', 'tp_max', 'sample_peak_max', 'freeze_fail_s', 'silence_fail_s')})}.", f"Files: {out}/QA_FILM.json, join_frames.jpg, contact/"]
    (out / "QA_FILM.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:table_end]))
    print(f"\n-> {out}/QA_FILM.md  ({overall})")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
