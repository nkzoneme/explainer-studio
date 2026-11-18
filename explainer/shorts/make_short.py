#!/usr/bin/env python3
"""FALLBACK: cut a 1080x1920 30 fps Short straight out of a finished 16:9 film (cheap, no new voice or animation).
The default is a native vertical Short (shorts/native/, see the explainer-shorts skill); use this when a native one is
not worth the time, or to test a moment before writing a native version.

Usage (from explainer/):
  python3 shorts/make_short.py --film film/<slug>/final/<slug>_final.mp4 --start 21.28 --end 55.62 \
      --words vo/<slug> --trim film/<slug>/final/work/trim_v2.json --srt film/<slug>/final/<slug>_final.en.srt \
      --style my_channel --hook "WHY IS THIS *SO EXPENSIVE*?" --out film/<slug>/shorts/cut_test.mp4 \
      [--zoom "0-9:860,140,1000,300;9-21:300,500,1200,360"] [--host host_thinking] [--loop]

Layout (px, 1080x1920):
  168 progress bar | 190-390 hook title (*word* = accent) | 400-1008 the film, full width |
  1022-1292 punch-in: --zoom "t0-t1:x,y,w,h;..." crops of the 1920x1080 film (Short time, best ~10:3; pick them from a
            1 fps sheet of the segment), shown in their time ranges; elsewhere the host bust + channel name |
  1300-1440 word captions (2-4 words, active word in the accent, digits from the SRT) | 1440+ nothing (Shorts UI) |
  last 1.5 s: "full story" card with the channel avatar over the punch-in panel (--loop: no card; the last 0.3 s
  dissolves back to the first frame so a replay is seamless).
Audio: the same span, 0.1 s fade in/out, mastered to -14 LUFS / <= -1.5 dBTP with kit/tools/master.sh (TP -2.0)."""
import argparse, difflib, json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, load_style, film_words, norm

W, H, FPS = 1080, 1920, 30
SRC_Y, SRC_H = 400, 608
PAN_Y, PAN_H, PAN_X, PAN_W = 1022, 270, 40, 900
CAP_Y0, CAP_Y1, CAP_CX, CAP_W = 1300, 1440, 490, 860
CARD = 1.5


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ass_col(h):
    r, g, b = hexrgb(h); return f"&H00{b:02X}{g:02X}{r:02X}&"


def srt_tokens(path, t0, t1):
    toks = []
    txt = open(path, encoding="utf-8").read()
    for blk in re.split(r"\n\s*\n", txt.strip()):
        ls = blk.strip().splitlines()
        if len(ls) < 3: continue
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", ls[1])
        if not m: continue
        g = list(map(int, m.groups()))
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000; b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        if b < t0 - 1 or a > t1 + 1: continue
        toks += " ".join(ls[2:]).split()
    return toks


def display_words(words, srt_path):
    """Map spoken words (numbers spelled out) to the SRT's written tokens (digits): equal tokens 1:1, a replaced block
    becomes one caption token spanning the spoken words' times."""
    if not srt_path or not words: return [{"text": w["word"], "start": w["start"], "end": w["end"]} for w in words]
    toks = srt_tokens(srt_path, words[0]["start"], words[-1]["end"])
    A = [" ".join(norm(w["word"])) for w in words]; B = [" ".join(norm(t)) for t in toks]
    out = []
    sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                w = words[i1 + k]; out.append({"text": toks[j1 + k], "start": w["start"], "end": w["end"]})
        elif op == "replace" and (i2 - i1) <= 6 and (j2 - j1) <= 3:
            out.append({"text": " ".join(toks[j1:j2]), "start": words[i1]["start"], "end": words[i2 - 1]["end"]})
        else:
            for k in range(i1, i2): out.append({"text": words[k]["word"], "start": words[k]["start"], "end": words[k]["end"]})
    return out


def chunks(ws, max_words=4, max_chars=16):
    out, cur = [], []
    for i, w in enumerate(ws):
        ln = len(" ".join(x["text"] for x in cur + [w]))
        if cur and (len(cur) >= max_words or ln > max_chars or w["start"] - cur[-1]["end"] > 0.25): out.append(cur); cur = []
        cur.append(w)
        if re.search(r"[.?!:;]$", w["text"]) or (w["text"].endswith(",") and len(cur) >= 2): out.append(cur); cur = []
    if cur: out.append(cur)
    for i in range(len(out) - 1, 0, -1):  # no lonely single word glued after a 1-2 word line mid-sentence
        if len(out[i]) == 1 and len(out[i - 1]) <= 2 and not re.search(r"[.?!]$", out[i - 1][-1]["text"]) and out[i][0]["start"] - out[i - 1][-1]["end"] < 0.25:
            out[i - 1] += out[i]; del out[i]
    return out


def ts(t):
    t = max(0, t); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def write_ass(path, ws, dur, st, font_file, captions_until):
    font = st["font_display"]; fs0 = 92
    f = lambda s: ImageFont.truetype(font_file, s)
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             f"Style: Cap,{font},{fs0},{ass_col(st['caption_fill'])},&H000000FF&,{ass_col(st['caption_outline'])},&H64000000&,0,0,0,0,100,100,1,0,1,7,4,5,0,0,0,1",
             f"Style: Bar,{font},10,{ass_col(st['accent'])},&H000000FF&,&H00000000&,&H00000000&,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
             "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    # progress bar: a drawn rectangle whose clip grows over the whole Short
    lines.append(f"Dialogue: 2,{ts(0)},{ts(dur)},Bar,,0,0,0,,{{\\pos(0,0)\\clip(60,168,61,182)\\t(0,{int(dur * 1000)},\\clip(60,168,1020,182))\\p1}}m 60 168 l 1020 168 1020 182 60 182{{\\p0}}")
    on, cy = ass_col(st["caption_active"]), (CAP_Y0 + CAP_Y1) // 2
    cs = chunks(ws)
    for ci, c in enumerate(cs):
        text = " ".join(w["text"] for w in c)
        fs = fs0
        while f(fs).getlength(text) + 30 > CAP_W and fs > 56: fs -= 4
        t0 = max(0, c[0]["start"] - 0.04)
        t1 = min(cs[ci + 1][0]["start"] - 0.04, c[-1]["end"] + 0.6) if ci + 1 < len(cs) else c[-1]["end"] + 0.5
        t1 = min(t1, captions_until)
        if t1 <= t0: continue
        for wi, w in enumerate(c):
            a = t0 if wi == 0 else max(t0, w["start"] - 0.02)
            b = t1 if wi == len(c) - 1 else c[wi + 1]["start"] - 0.02
            if b <= a: continue
            parts = [(f"{{\\1c{on}}}" + x["text"] + "{\\r}") if k == wi else x["text"] for k, x in enumerate(c)]
            pop = "\\fscx86\\fscy86\\t(0,120,\\fscx100\\fscy100)" if wi == 0 else ""
            lines.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\an5\\pos({CAP_CX},{cy})\\fs{fs}{pop}}}" + " ".join(parts).replace("{\\r}", f"{{\\r\\fs{fs}}}"))
    open(path, "w").write("\n".join(lines) + "\n")


def text_box(draw, xy, text, font_file, size, max_w, fill, accent, align="center", line_gap=1.05):
    """Draws text with *accent* words; wraps to max_w; returns height."""
    f = ImageFont.truetype(font_file, size)
    words = text.split(); lines, cur = [], []
    for w in words:
        if cur and f.getlength(" ".join(x.replace("*", "") for x in cur + [w])) > max_w: lines.append(cur); cur = []
        cur.append(w)
    if cur: lines.append(cur)
    x0, y = xy; lh = int(size * line_gap); acc = False
    for ln in lines:
        lw = f.getlength(" ".join(x.replace("*", "") for x in ln))
        x = x0 - lw / 2 if align == "center" else x0
        for w in ln:  # *several words* in the accent; the markers may sit next to punctuation ("*WORD*?")
            if w.startswith("*"): acc = True
            col = accent if acc else fill
            if "*" in w[1:]: acc = False
            s = w.replace("*", "") + " "
            draw.text((x, y), s, font=f, fill=col)
            x += f.getlength(s)
        y += lh
    return len(lines) * lh, lines


def build_bg(path, st, hook, font_file, host_png, has_zoom):
    im = Image.new("RGB", (W, H), hexrgb(st["bg"]))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1300, W, H], fill=hexrgb(st["bg2"]))
    ink = hexrgb(st["ink"])
    d.rounded_rectangle([60, 168, 1020, 182], radius=7, fill=tuple(int(c * 0.86) for c in hexrgb(st["bg"])))
    # hook title: navy pill, white text, accent words; auto-size to <= 2 lines
    hk = hook.upper() if st.get("title_case") == "upper" else hook
    for size in (78, 72, 66, 60, 56):
        f = ImageFont.truetype(font_file, size)
        tmp = Image.new("RGB", (10, 10)); _, lines = text_box(ImageDraw.Draw(tmp), (0, 0), hk, font_file, size, 900, (0, 0, 0), (0, 0, 0))
        if len(lines) <= 2: break
    lh = int(size * 1.05); th = len(lines) * lh
    tw = max(f.getlength(" ".join(x.replace("*", "") for x in ln)) for ln in lines)
    by0 = 290 - th // 2 - 22
    d.rounded_rectangle([W / 2 - tw / 2 - 34, by0, W / 2 + tw / 2 + 34, by0 + th + 40], radius=26, fill=hexrgb(st["primary"]), outline=ink, width=7)
    text_box(d, (W / 2, by0 + 14), hk, font_file, size, 900, hexrgb(st["text_on_primary"]), hexrgb(st["accent"]))
    # frames around the film and the panel
    d.rectangle([0, SRC_Y - 6, W, SRC_Y + SRC_H + 6], fill=ink)
    d.rounded_rectangle([PAN_X - 7, PAN_Y - 7, PAN_X + PAN_W + 7, PAN_Y + PAN_H + 7], radius=18, fill=hexrgb(st["bg2"]), outline=ink, width=7)
    if not has_zoom and host_png:
        hp = Image.open(host_png).convert("RGBA")
        bust = hp.crop((0, 0, hp.width, int(hp.height * 0.42)))
        bust = bust.resize((int(bust.width * PAN_H / bust.height), PAN_H))
        im.paste(bust, (PAN_X + 20, PAN_Y), bust)
        text_box(d, (PAN_X + 40 + bust.width, PAN_Y + 70), st["channel"].upper(), font_file, 64, 560, hexrgb(st["primary"]), hexrgb(st["accent"]), align="left")
    im.save(path)


def build_card(path, st, font_file):
    w, h = PAN_W + 14, PAN_H + 14
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=(255, 253, 247, 255), outline=hexrgb(st["ink"]), width=8)
    av = Image.open(os.path.join(ROOT, st["avatar"])).convert("RGB").resize((210, 210))
    m = Image.new("L", (210, 210), 0); ImageDraw.Draw(m).ellipse([0, 0, 209, 209], fill=255)
    im.paste(av, (30, (h - 210) // 2), m)
    d.ellipse([30, (h - 210) // 2, 239, (h - 210) // 2 + 209], outline=hexrgb(st["ink"]), width=7)
    text_box(d, (270, 62), st["end_card_line"], font_file, 58, 600, hexrgb(st["primary"]), hexrgb(st["accent"]), align="left")
    text_box(d, (270, 200), st["channel"], font_file, 40, 600, hexrgb(st["ink"]), hexrgb(st["accent"]), align="left")
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", required=True); ap.add_argument("--start", type=float, required=True); ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--words", required=True); ap.add_argument("--trim", required=True); ap.add_argument("--srt")
    ap.add_argument("--style", required=True); ap.add_argument("--hook", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--zoom", help='"t0-t1:x,y,w,h;..." crops of the 1920x1080 film for the punch-in panel, times in Short seconds (or one x,y,w,h for all)')
    ap.add_argument("--host", default="host_thinking", help="pose name in style host_dir/film assets for the panel when no --zoom")
    ap.add_argument("--loop", action="store_true")
    a = ap.parse_args()
    st = load_style(a.style); X = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
    font_file = st["font_display_file"]; dur = round(a.end - a.start, 3)
    ws = [w for w in film_words(X(a.words), X(a.trim)) if w["start"] >= a.start - 0.01 and w["end"] <= a.end + 0.01]
    ws = [{"word": w["word"], "start": round(w["start"] - a.start, 3), "end": round(w["end"] - a.start, 3)} for w in ws]
    disp = display_words(ws, X(a.srt) if a.srt else None)
    td = tempfile.mkdtemp(prefix="short_")
    host_png = None
    for cand in (os.path.join(X("film/assets/img"), a.host + ".webp"), os.path.join(X(st["host_dir"]), a.host + ".webp")):
        if os.path.exists(cand): host_png = cand; break
    bg, card, ass = os.path.join(td, "bg.png"), os.path.join(td, "card.png"), os.path.join(td, "caps.ass")
    build_bg(bg, st, a.hook, font_file, host_png, False); build_card(card, st, font_file)
    write_ass(ass, disp, dur, st, font_file, dur)
    fc = [f"[0:v]trim=start={a.start}:end={a.end},setpts=PTS-STARTPTS,fps={FPS},split=3[v1][v2][v3]",
          f"[v1]scale={W}:{SRC_H}:flags=lanczos[src]",
          f"[1:v]format=rgba[bg]", f"[bg][src]overlay=0:{SRC_Y}[b1]"]
    last = "b1"
    zooms = []
    for part in (a.zoom or "").split(";"):
        if not part.strip(): continue
        rng, box = part.split(":") if ":" in part else (f"0-{dur}", part)
        t0, t1 = map(float, rng.split("-")); zooms.append((t0, t1, tuple(map(int, box.split(",")))))
    if zooms:
        fc += [f"[v2]split={len(zooms)}" + "".join(f"[z{i}]" for i in range(len(zooms)))]
        for i, (t0, t1, (x, y, w, h)) in enumerate(zooms):
            fc += [f"[z{i}]crop={w}:{h}:{x}:{y},scale={PAN_W}:{PAN_H}:flags=lanczos[zm{i}]",
                   f"[{last}][zm{i}]overlay={PAN_X}:{PAN_Y}:enable='between(t,{t0},{t1})'[bz{i}]"]; last = f"bz{i}"
    else:
        fc += ["[v2]nullsink"]
    if a.loop:  # dissolve the film window back to its own first frame over the last 0.3 s
        fc += [f"[v3]trim=end_frame=1,scale={W}:{SRC_H},loop=loop=-1:size=1,trim=duration={dur},setpts=PTS-STARTPTS,format=rgba,fade=t=in:st={dur - 0.3}:d=0.3:alpha=1[first]",
               f"[{last}][first]overlay=0:{SRC_Y}[b3]"]; last = "b3"
    else:
        fc += ["[v3]nullsink",
               f"[2:v]format=rgba,fade=t=in:st={dur - CARD}:d=0.2:alpha=1[cd]", f"[{last}][cd]overlay={PAN_X - 7}:{PAN_Y - 7}:enable='gte(t,{dur - CARD})'[b3]"]; last = "b3"
    assp = ass.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    fc += [f"[{last}]ass='{assp}',format=yuv420p[vout]",
           f"[0:a]atrim=start={a.start}:end={a.end},asetpts=PTS-STARTPTS,afade=t=in:d=0.1,afade=t=out:st={dur - 0.1}:d=0.1[aout]"]
    raw = os.path.join(td, "raw.mkv")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", X(a.film),
           "-loop", "1", "-framerate", str(FPS), "-t", str(dur), "-i", bg,
           "-loop", "1", "-framerate", str(FPS), "-t", str(dur), "-i", card,
           "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]", "-t", str(dur),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "pcm_s24le", raw]
    subprocess.run(cmd, check=True)
    out = X(a.out); os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["sh", X("kit/tools/master.sh"), raw, out], check=True, env={**os.environ, "TP": "-2.0"})
    print("wrote", out, f"({dur:.2f} s)")


if __name__ == "__main__":
    main()
