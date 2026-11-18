#!/usr/bin/env python3
"""Review sheets for the picture review (kit/REVIEW_PASS.md): what a first-time viewer sees, with what is being said. Usage:
  python3 qa_review.py <chNN_raw.mp4> --words vo/<slug>/chNN_w.words.json [--out DIR]
  python3 qa_review.py <final.mp4>    --srt final/film.srt                [--out DIR] [--max 96]

Takes one frame about a second after every full-frame change (same detector as qa_pace.py; 1.2 s in, or the
middle of a shorter shot, so entrances are over) plus a second frame 70 % into any framing held over 8 s, and writes into DIR (default <video stem>_review/ next to the video):
  review_beats_NN.jpg   480 px tiles, each with its time and the sentence spoken at that moment
  review_phone_NN.jpg   the same frames at 360 px wide, shown 1:1: what a phone shows. Text you cannot read here is a P0.
  review.json           the tiles, and "unanswered": sentences of 2 s or more during which the picture did not change
                        (the narrator says something and nothing on screen reacts)
It measures and lays out; it does not judge. The judging is the review pass.
Needs ffmpeg, numpy, Pillow.
"""
import argparse, io, json, pathlib, re, subprocess, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 96, 54, 5
FONTS = ["/usr/share/fonts/noto/NotoSans-Bold.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]


def font(size):
    for p in FONTS:
        if pathlib.Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def changes(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={FPS},scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    f = np.frombuffer(raw, dtype=np.uint8).reshape(-1, H, W).astype(np.int16)
    return (np.abs(f[1:] - f[:-1]) > 24).mean(axis=(1, 2)), len(f) / FPS      # share of pixels changed per 0.2 s step


def shot_times(changed):
    out, last = [], -1e9
    for i in np.nonzero(changed > 0.20)[0]:
        t = (i + 1) / FPS
        if t - last >= 0.8:
            out.append(t)
        last = t
    return out


def spoken(words_path, srt_path):
    """-> [{text,start,end}] sentences (words.json) or cues (SRT)"""
    if words_path:
        ws = json.loads(pathlib.Path(words_path).read_text())
        ws = ws.get("words", ws) if isinstance(ws, dict) else ws
        out, cur = [], []
        for w in ws:
            cur.append(w)
            if re.search(r"[.!?][\"')\]]*$", w["word"].strip()):
                out.append(cur); cur = []
        if cur: out.append(cur)
        return [{"text": " ".join(x["word"].strip() for x in s), "start": s[0]["start"], "end": s[-1]["end"]} for s in out]
    if srt_path:
        out = []
        for block in re.split(r"\n\s*\n", pathlib.Path(srt_path).read_text(encoding="utf-8-sig").strip()):
            m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)\s*\n(.*)", block, re.S)
            if m:
                g = [int(x) for x in m.groups()[:8]]
                out.append({"text": " ".join(m.group(9).split()), "start": g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, "end": g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000})
        return out
    return []


def grab(video, t, w):
    png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGB") if png else Image.new("RGB", (w, w * 9 // 16), (40, 0, 0))


def sheet(video, tiles, w, cols, path, title):
    th, cap, pad = w * 9 // 16, 62, 10
    f_t, f_c = font(15), font(12)
    rows = -(-len(tiles) // cols)
    img = Image.new("RGB", (pad + cols * (w + pad), 30 + rows * (th + cap + pad)), (24, 24, 24))
    d = ImageDraw.Draw(img)
    d.text((pad, 7), title, fill=(170, 170, 170), font=f_t)
    for i, tl in enumerate(tiles):
        x, y = pad + (i % cols) * (w + pad), 30 + (i // cols) * (th + cap + pad)
        img.paste(grab(video, tl["t"], w), (x, y))
        label = f"{int(tl['t'] // 60)}:{tl['t'] % 60:04.1f}" + ("  held" if tl["kind"] == "mid" else "")
        d.text((x, y + th + 3), label, fill=(255, 190, 80), font=f_t)
        for k, line in enumerate(textwrap.wrap(tl["said"], width=max(20, w // 7))[:2]):
            d.text((x, y + th + 23 + k * 15), line, fill=(215, 215, 215), font=f_c)
    img.save(path, quality=88)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--words"); ap.add_argument("--srt"); ap.add_argument("--out")
    ap.add_argument("--max", type=int, default=96, help="most tiles (a long film is thinned evenly after the first 30 s; run it per chapter to see every shot)")
    a = ap.parse_args()
    video = pathlib.Path(a.video)
    out = pathlib.Path(a.out) if a.out else video.with_name(video.stem + "_review")
    out.mkdir(parents=True, exist_ok=True)
    changed, dur = changes(video)
    shots = shot_times(changed)
    said = spoken(a.words, a.srt)

    def at(t):
        s = next((x for x in said if x["start"] - 0.15 <= t <= x["end"] + 0.25), None)
        return s["text"] if s else ""

    edges = [0.0] + shots + [dur]
    tiles = []
    for s, e in zip(edges, edges[1:]):
        if e - s < 0.5: continue
        tiles.append({"t": round(s + min(1.2, (e - s) / 2), 2), "kind": "start"})      # entrances are over, the shot's content is on
        if e - s > 8:
            tiles.append({"t": round(s + (e - s) * 0.7, 2), "kind": "mid"})            # a long build, mostly built
    thinned = len(tiles) > a.max
    if thinned:
        head = [x for x in tiles if x["t"] <= 30]
        rest = [x for x in tiles if x["t"] > 30]
        keep = max(1, a.max - len(head))
        rest = [rest[int(i * len(rest) / keep)] for i in range(keep)] if len(rest) > keep else rest
        tiles = head + rest
    for x in tiles: x["said"] = at(x["t"])
    for n, i in enumerate(range(0, len(tiles), 24), 1):
        part = tiles[i:i + 24]
        span = f"{video.name}  {part[0]['t']:.0f}-{part[-1]['t']:.0f} s"
        sheet(video, part, 480, 4, out / f"review_beats_{n:02d}.jpg", span + "  |  one frame after each full-frame change, with the sentence being spoken")
        sheet(video, part, 360, 4, out / f"review_phone_{n:02d}.jpg", span + "  |  360 px = a phone, shown 1:1: can every line meant to be read be read?")
    unanswered = []
    for s in said:
        if s["end"] - s["start"] < 2.0: continue
        i0, i1 = max(0, int((s["start"] - 0.4) * FPS)), min(len(changed), int(s["end"] * FPS) + 1)
        if i1 > i0 and float(changed[i0:i1].max()) < 0.012:
            unanswered.append({"start": round(s["start"], 1), "end": round(s["end"], 1), "text": s["text"]})
    rep = {"video": str(video), "duration_s": round(dur, 1), "full_frame_changes": len(shots), "thinned": thinned, "tiles": tiles, "unanswered": unanswered,
           "sheets": sorted(str(p) for p in out.glob("review_*.jpg"))}
    (out / "review.json").write_text(json.dumps(rep, indent=1))
    print(f"{video.name}: {dur:.1f} s, {len(shots)} full-frame changes, {len(tiles)} tiles on {len(rep['sheets']) // 2} sheet pair(s) in {out}/")
    if not said:
        print("no --words or --srt given: the tiles carry no sentences and 'unanswered' was not measured")
    for u in unanswered:
        print(f"UNANSWERED {u['start']}-{u['end']} s: nothing on screen changes while the voice says: \"{u['text'][:90]}\"")
    if thinned:
        print(f"thinned to {len(tiles)} tiles (--max): after the first 30 s not every shot is on the sheets; the chapter runs show them all")
    print(f"qa_review: {len(unanswered)} sentence(s) with no picture change. Now do the review pass on the sheets (kit/REVIEW_PASS.md).")


if __name__ == "__main__":
    main()
