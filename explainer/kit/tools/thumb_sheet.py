#!/usr/bin/env python3
"""Thumbnail tools. Two subcommands.

1) sheet: place 3 candidate thumbnails among 6 competitor thumbnails in a mock YouTube grid (light + dark mode, 160 px and
   320 px tiles) and run the layout checks. Competitors come from yt-dlp ("ytsearch8:<query>", thumbnails only, nothing is
   downloaded but images and metadata) or from --refs <dir of images>.
   python3 thumb_sheet.py sheet --query "topic words" --cand a.png b.png c.png --channel my_channel \
        [--titles "T1" "T2" "T3"] [--words "BIG NUMBER" ...] [--refs dir] [--out dir] [--seed 7]
   Writes <out>/sheet_blind.png (no marks: give THIS to the fresh-agent click test), sheet_marked.png (ours ringed and lettered A/B/C,
   for the operator), checks.json. Layout checks per candidate at 1280x720: words <= 3 and plain English (jargon list), cap
   height >= 110 px, text contrast >= 7:1 against its plate/background, bottom-right 180x90 empty (the duration chip covers it),
   tesseract reads the words back at 320 px. "One accent colour" is not machine-checked.

2) make: thumbnail production helper. Real-photo cut-out + channel treatment + <= 3 words in the channel font, 1280x720.
   python3 thumb_sheet.py make --photo in.jpg --channel my_channel --words "BIG NUMBER" --out thumb.png \
        [--mask mask.png] [--rect x0,y0,x1,y1 (fractions, GrabCut fallback)] [--credit "Author, CC BY 4.0, <url>"] [--side right|left]
   Cut-out: rembg (local; installed in ~/.cache/explainer-venv, first use downloads the u2net model once) -> else --mask
   (white = keep) -> else OpenCV GrabCut inside --rect (default centre 90 %). thumb_look outline: ink outline on a light ground. halftone: dot screen with an
   orange edge on the dark field. The object fills about 60 % of the width and crosses the frame edge; the words sit on a solid
   plate top-left, never in the bottom-right 180x90. Writes <out> and <out>.json (credit, method).
   Prefer public domain or CC BY photos only, credited; never GFDL-only (see fetch_media.py)."""
import argparse, json, os, pathlib, random, re, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops

ROOT = pathlib.Path(__file__).resolve().parents[2]
VENV = pathlib.Path.home() / ".cache" / "explainer-venv" / "bin"
W, H = 1280, 720
JARGON = {"api", "sdk", "roi", "kpi", "ebitda", "capex", "opex", "sku", "b2b", "saas"}  # add your niche's acronyms
def _rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load_brand(slug):
    """Thumbnail brand from shorts/styles/<slug>.json (keys bg, bg2, ink, accent, text_on_primary, font_display_file,
    optional thumb_look: "outline" (light ground, outlined cut-out) or "halftone" (dark ground))."""
    p = ROOT / "shorts" / "styles" / f"{slug}.json"
    if not p.exists():
        raise SystemExit(f"no brand file {p}; copy shorts/styles/_example.json")
    st = json.load(open(p))
    light = sum(c * w for c, w in zip(_rgb(st["bg"]), (0.299, 0.587, 0.114))) > 128
    look = st.get("thumb_look", "outline" if light else "halftone")
    return dict(name=st.get("channel", slug), bg=_rgb(st["bg"]), bg2=_rgb(st.get("bg2", st["bg"])), ink=_rgb(st["ink"]),
                accent=_rgb(st["accent"]), text=_rgb(st["primary"] if light else st.get("text_on_primary", "#ffffff")),
                plate=_rgb(st["accent"] if look == "outline" else st["ink"]), font=st["font_display_file"], look=look)


def which(name):
    return shutil.which(name) or (str(VENV / name) if (VENV / name).exists() else None)


def lum(rgb):
    c = [v / 255 for v in rgb[:3]]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def ocr_words(img, scale=1):
    """-> [(text, x, y, w, h, conf)] via tesseract TSV."""
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "i.png"
        im = img.convert("RGB")
        if scale != 1: im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        im.save(p)
        r = subprocess.run(["tesseract", str(p), "-", "--psm", "11", "tsv"], capture_output=True, text=True).stdout
    out = []
    for l in r.splitlines()[1:]:
        c = l.split("\t")
        if len(c) >= 12 and c[11].strip() and float(c[10]) > 40 and re.search(r"[A-Za-z0-9]", c[11]):
            out.append((c[11].strip(), *(int(int(v) / scale) for v in c[6:10]), float(c[10])))
    return out


# ------------------------------------------------------------------ checks
def check_candidate(path, words_expected=None):
    im = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
    res, notes = {}, []
    ws = ocr_words(im)
    texts = [w[0] for w in ws]
    # words: use the largest-height words (headline), ignore tiny text
    if ws:
        mh = max(w[4] for w in ws)
        big = [w for w in ws if w[4] >= mh * 0.5]
    else:
        big = []
    res["words_read"] = [w[0] for w in big]
    nwords = len(words_expected.split()) if words_expected else len(big)
    res["words"] = {"ok": nwords <= 3, "detail": f"{nwords} words ({' '.join(res['words_read']) or 'none read'})"}
    jar = [t for t in (words_expected.split() if words_expected else res["words_read"]) if t.lower().strip(".,!?") in JARGON]
    res["plain_english"] = {"ok": not jar, "detail": f"jargon: {jar}" if jar else "no listed jargon (list is short; a human still checks)"}
    ch = max((w[4] for w in big), default=0)
    res["cap_height"] = {"ok": ch >= 110, "detail": f"largest headline word box {ch} px high at 1280x720 (need >= 110)"}
    # contrast of headline words vs local background
    arr = np.asarray(im).astype(float)
    worst = 99.0
    for t, x, y, w, h, _ in big:
        box = arr[max(0, y):y + h, max(0, x):x + w].reshape(-1, 3)
        if len(box) < 20: continue
        l = box @ np.array([0.299, 0.587, 0.114])
        bgc = np.median(box[l <= np.percentile(l, 100)], axis=0)
        ring = np.concatenate([arr[max(0, y - 6):y, x:x + w].reshape(-1, 3), arr[y + h:y + h + 6, x:x + w].reshape(-1, 3)]) if y > 6 else box
        bgc = np.median(ring, axis=0) if len(ring) else bgc
        fg = box[np.argmax(np.abs(l - (bgc @ np.array([0.299, 0.587, 0.114]))))]
        worst = min(worst, contrast(fg, bgc))
    res["contrast"] = {"ok": worst >= 7, "detail": f"worst headline word contrast {worst:.1f}:1 (need >= 7:1)" if worst < 99 else "no headline words measured"}
    # bottom-right empty
    br = np.asarray(im.crop((W - 180, H - 90, W, H)).convert("L").filter(ImageFilter.FIND_EDGES)).astype(float)
    frac = float((br > 40).mean())
    res["bottom_right_empty"] = {"ok": frac < 0.03, "detail": f"{frac * 100:.1f} % edge pixels in the 180x90 corner (need < 3 %)"}
    # readability at 320 px
    small = im.resize((320, 180), Image.LANCZOS)
    got = {re.sub(r"\W", "", w[0]).lower() for w in ocr_words(small, scale=2.0)}
    exp = {re.sub(r"\W", "", t).lower() for t in (words_expected.split() if words_expected else res["words_read"])}
    miss = sorted(x for x in exp if x and x not in got)
    res["ocr_320"] = {"ok": not miss and bool(exp), "detail": f"tesseract at 320 px read {sorted(got)[:6]}; missing {miss}" if exp else "no words to read back"}
    res["pass"] = all(v["ok"] for k, v in res.items() if isinstance(v, dict))
    return res


# ------------------------------------------------------------------ competitors + grid
def fetch_refs(query, n, workdir):
    yt = which("yt-dlp")
    if not yt: raise SystemExit("yt-dlp not found (pip install yt-dlp, or pass --refs <dir>)")
    subprocess.run([yt, "--skip-download", "--write-thumbnail", "--write-info-json", "--convert-thumbnails", "jpg", "--no-warnings", "-q",
                    "--playlist-end", str(n + 4), "-o", str(workdir / "%(id)s.%(ext)s"), f"ytsearch{n + 4}:{query}"], capture_output=True, text=True, timeout=240)
    refs = []
    for j in sorted(workdir.glob("*.info.json")):
        d = json.loads(j.read_text()); img = j.with_name(j.name.replace(".info.json", ".jpg"))
        if img.exists() and (d.get("duration") or 0) > 240:
            refs.append(dict(img=img, title=d.get("title", ""), channel=d.get("channel") or d.get("uploader") or "", views=d.get("view_count") or 0, dur=d.get("duration") or 0))
    return refs[:n]


def tile(img, title, channel, meta, w, dark, mark=None):
    th = int(w * 9 / 16); pad = 8
    fs = max(10, int(w / 24)); font = ImageFont.truetype("/usr/share/fonts/noto/NotoSans-Bold.ttf", fs); small = ImageFont.truetype("/usr/share/fonts/noto/NotoSans-Regular.ttf", max(9, int(fs * .85)))
    fg, sub = ((241, 241, 241), (170, 170, 170)) if dark else ((15, 15, 15), (96, 96, 96))
    out = Image.new("RGB", (w, th + int(fs * 5.4)), (15, 15, 15) if dark else (255, 255, 255))
    t = ImageOps.fit(Image.open(img).convert("RGB"), (w, th), Image.LANCZOS)
    r = ImageDraw.Draw(t); chip = "12:04"; cw = r.textlength(chip, font=small)
    r.rounded_rectangle([w - cw - 12, th - fs - 8, w - 4, th - 4], 3, fill=(0, 0, 0)); r.text((w - cw - 8, th - fs - 6), chip, font=small, fill=(255, 255, 255))
    mask = Image.new("L", t.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, th - 1], int(w / 28), fill=255)
    out.paste(t, (0, 0), mask)
    d = ImageDraw.Draw(out)
    if mark:
        d.rounded_rectangle([0, 0, w - 1, th - 1], int(w / 28), outline=(230, 30, 30), width=max(3, w // 60)); by = th - int(fs * 1.9) - 4
        d.ellipse([6, by, 6 + fs * 1.6, by + fs * 1.6], fill=(230, 30, 30))
        d.text((6 + fs * .45, by + fs * .1), mark, font=font, fill=(255, 255, 255))
    # two-line title
    words, lines, cur = title.split(), [], ""
    for wd in words:
        if d.textlength((cur + " " + wd).strip(), font=font) <= w - pad: cur = (cur + " " + wd).strip()
        else: lines.append(cur); cur = wd
    lines.append(cur)
    y = th + 6
    for l in lines[:2]: d.text((0, y), l, font=font, fill=fg); y += fs + 3
    d.text((0, y + 2), channel[:34], font=small, fill=sub); d.text((0, y + 2 + small.size + 3), meta, font=small, fill=sub)
    return out


def panel(items, w, cols, dark, marked):
    tiles = [tile(i["img"], i["title"], i["channel"], i["meta"], w, dark, i.get("letter") if marked else None) for i in items]
    gap = 18; rows = (len(tiles) + cols - 1) // cols; cellh = max(t.height for t in tiles)
    pw = cols * w + (cols + 1) * gap; ph = rows * cellh + (rows + 1) * gap + 28
    canvas = Image.new("RGB", (pw, ph), (15, 15, 15) if dark else (255, 255, 255))
    for i, t in enumerate(tiles): canvas.paste(t, (gap + (i % cols) * (w + gap), 28 + gap + (i // cols) * (cellh + gap)))
    d = ImageDraw.Draw(canvas); d.text((gap, 6), f"{'DARK' if dark else 'LIGHT'} mode, {w}px tiles", fill=(150, 150, 150) if dark else (90, 90, 90), font=ImageFont.truetype("/usr/share/fonts/noto/NotoSans-Bold.ttf", 14))
    return canvas


def cmd_sheet(a):
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    refs = []
    if a.refs:
        for p in sorted(pathlib.Path(a.refs).glob("*"))[:6]:
            if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"): refs.append(dict(img=p, title=p.stem.replace("_", " "), channel="reference", views=0, dur=0))
    else:
        refs = fetch_refs(a.query, 6, out / "refs")
    if len(refs) < 6: print(f"WARNING: only {len(refs)} competitor thumbnails", file=sys.stderr)
    rnd = random.Random(a.seed)
    titles = a.titles or [f"Our video {c}" for c in "ABC"]
    ours = [dict(img=pathlib.Path(c), title=titles[i] if i < len(titles) else f"Our video {i}", channel=a.channel.replace("_", " ").title(), meta="1.2K views - 2 hours ago", letter="ABC"[i], ours=True) for i, c in enumerate(a.cand)]
    comp = [dict(img=r["img"], title=r["title"], channel=r["channel"], meta=f"{int(r['views']):,} views" if r["views"] else "views", letter=None) for r in refs]
    items = ours + comp; rnd.shuffle(items)
    for kind, marked in (("blind", False), ("marked", True)):
        ps = [panel(items, 320, 3, False, marked), panel(items, 320, 3, True, marked), panel(items, 160, 5, False, marked), panel(items, 160, 5, True, marked)]
        W2 = max(p.width for p in ps[:2]) + max(p.width for p in ps[2:]) + 20; H2 = max(ps[0].height + ps[1].height, ps[2].height + ps[3].height) + 20
        sheet = Image.new("RGB", (W2, H2), (128, 128, 128))
        lw = max(p.width for p in ps[:2])
        sheet.paste(ps[0], (0, 0)); sheet.paste(ps[1], (0, ps[0].height + 10)); sheet.paste(ps[2], (lw + 20, 0)); sheet.paste(ps[3], (lw + 20, ps[2].height + 10))
        sheet.save(out / f"sheet_{kind}.png")
    checks = {}
    for i, c in enumerate(a.cand):
        checks["ABC"[i]] = {"file": str(c), **check_candidate(c, a.words[i] if a.words and i < len(a.words) else None)}
    meta = {"query": a.query, "order": [("ours " + i["letter"]) if i.get("ours") else i["title"] for i in items], "competitors": [{"title": r["title"], "channel": r["channel"]} for r in refs]}
    (out / "checks.json").write_text(json.dumps({"meta": meta, "checks": checks}, indent=1, default=str))
    for k, v in checks.items():
        print(f"candidate {k} {'PASS' if v['pass'] else 'FAIL'}: " + "; ".join(f"{n}={'ok' if d['ok'] else 'NO'}" for n, d in v.items() if isinstance(d, dict)))
    print(f"-> {out}/sheet_blind.png, sheet_marked.png, checks.json")
    sys.exit(0 if all(v["pass"] for v in checks.values()) else 1)


# ------------------------------------------------------------------ make
def cutout(photo, mask_path, rect, method_out):
    im = Image.open(photo).convert("RGB")
    rb = which("rembg")
    try:
        import rembg  # noqa
        from rembg import remove
        r = remove(im); method_out.append("rembg"); return r.convert("RGBA")
    except Exception:
        pass
    if rb:
        with tempfile.TemporaryDirectory() as td:
            o = pathlib.Path(td) / "o.png"
            p = subprocess.run([str(VENV / "python"), "-c", "import sys;from rembg import remove;from PIL import Image;remove(Image.open(sys.argv[1]).convert('RGB')).save(sys.argv[2])", str(photo), str(o)], capture_output=True, text=True, timeout=600)
            if o.exists(): method_out.append("rembg(venv)"); return Image.open(o).convert("RGBA")
            print("rembg failed, falling back:", p.stderr[-200:], file=sys.stderr)
    if mask_path:
        m = Image.open(mask_path).convert("L").resize(im.size); r = im.convert("RGBA"); r.putalpha(m); method_out.append("manual mask"); return r
    import cv2
    a = np.array(im)[:, :, ::-1].copy(); h, w = a.shape[:2]
    f = rect or (0.05, 0.05, 0.95, 0.95)
    rc = (int(f[0] * w), int(f[1] * h), int((f[2] - f[0]) * w), int((f[3] - f[1]) * h))
    mk = np.zeros((h, w), np.uint8); bg = np.zeros((1, 65)); fg = np.zeros((1, 65))
    cv2.grabCut(a, mk, rc, bg, fg, 6, cv2.GC_INIT_WITH_RECT)
    m = np.where((mk == 1) | (mk == 3), 255, 0).astype(np.uint8)
    r = im.convert("RGBA"); r.putalpha(Image.fromarray(m).filter(ImageFilter.GaussianBlur(1.2))); method_out.append("grabcut (manual-mask fallback; check edges)"); return r


def halftone(rgba, cell=9):
    g = ImageOps.autocontrast(rgba.convert("L"), cutoff=2); w, h = g.size; S = 2
    ga = np.asarray(g).astype(float) / 255
    yy, xx = np.mgrid[0:h * S, 0:w * S] / S
    ca = sa = np.sqrt(.5); u = (xx * ca + yy * sa) / cell; v = (-xx * sa + yy * ca) / cell
    d = np.sqrt((u - np.round(u)) ** 2 + (v - np.round(v)) ** 2)
    gb = np.asarray(g.resize((w * S, h * S), Image.BILINEAR)).astype(float) / 255
    ink = d < (1 - gb) * 0.62
    out = Image.fromarray(np.where(ink, 20, 238).astype(np.uint8)).resize((w, h), Image.LANCZOS).convert("RGBA")
    out.putalpha(rgba.split()[3]); return out


def outline(rgba, color, px):
    a = rgba.split()[3].point(lambda v: 255 if v > 40 else 0)
    big = a.filter(ImageFilter.MaxFilter(px * 2 + 1)).filter(ImageFilter.GaussianBlur(1))
    ring = Image.new("RGBA", rgba.size, color + (255,)); ring.putalpha(big)
    ring.alpha_composite(rgba); return ring


def cmd_make(a):
    b = load_brand(a.channel); words = a.words.upper().split()
    if len(words) > 3: sys.exit("max 3 words")
    meth = []
    obj = cutout(a.photo, a.mask, [float(x) for x in a.rect.split(",")] if a.rect else None, meth)
    bb = obj.split()[3].point(lambda v: 255 if v > 40 else 0).getbbox()
    if bb: obj = obj.crop(bb)
    canvas = Image.new("RGBA", (W, H), b["bg"] + (255,))
    d = ImageDraw.Draw(canvas)
    if b["look"] == "outline":
        d.ellipse([W * .25, -H * .3, W * 1.25, H * 1.3], fill=b["bg2"])
        obj = outline(obj, b["ink"], 8)
    else:
        d.rectangle([0, 0, W, H], fill=b["bg"]); d.polygon([(0, H), (W * .55, H), (W * .75, 0), (0, 0)], fill=b["bg2"])
        obj = outline(halftone(obj), b["accent"], 6)
    tw = int(W * .64); obj = obj.resize((tw, int(obj.height * tw / obj.width)), Image.LANCZOS)
    if obj.height > H * 0.95: obj = obj.resize((int(obj.width * H * .95 / obj.height), int(H * .95)), Image.LANCZOS)
    x = W - obj.width + int(W * .06) if a.side == "right" else -int(W * .06)       # crosses the frame edge
    y = int(H * .5 - obj.height * .5) + int(H * .06)
    sh = Image.new("RGBA", obj.size, (0, 0, 0, 0)); sh.putalpha(obj.split()[3].point(lambda v: 90 if v > 40 else 0)); sh = sh.filter(ImageFilter.GaussianBlur(8))
    canvas.alpha_composite(sh, (x + 10, y + 12)); canvas.alpha_composite(obj, (x, y))
    # words on a solid plate, top-left, cap height >= 110
    fs = 175
    font = ImageFont.truetype(b["font"], fs)
    lines = [" ".join(words)]
    while True:
        bbs = [font.getbbox(l) for l in lines]; tw_ = max(bb[2] for bb in bbs)
        if tw_ <= W * .6 or fs <= 160: break
        if len(lines) == 1 and len(words) > 1: lines = words; continue    # stack words before shrinking: keeps cap height >= 110 px
        fs -= 6; font = ImageFont.truetype(b["font"], fs)
    capH = font.getbbox("H")[3] - font.getbbox("H")[1]
    pad = 26; lh = capH + 30
    pw = tw_ + pad * 2; ph = lh * len(lines) + pad * 2 - 6
    px, py = 36, 34
    plate = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); ImageDraw.Draw(plate).rounded_rectangle([0, 0, pw - 1, ph - 1], 22, fill=b["plate"], outline=b["ink"] if b["look"] == "outline" else b["accent"], width=8)
    canvas.alpha_composite(plate, (px, py))
    dd = ImageDraw.Draw(canvas)
    for i, l in enumerate(lines): dd.text((px + pad, py + pad - font.getbbox("H")[1] + i * lh), l, font=font, fill=b["text"])
    canvas.convert("RGB").save(a.out)
    side = {"method": meth[0] if meth else "?", "photo": a.photo, "credit": a.credit or "MISSING: add author, licence and URL before publishing", "words": words, "cap_height_px": capH, "channel": a.channel}
    pathlib.Path(str(a.out) + ".json").write_text(json.dumps(side, indent=1))
    print(f"wrote {a.out} (cut-out: {side['method']}, cap height {capH}px)")


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("sheet"); s.add_argument("--query"); s.add_argument("--cand", nargs=3, required=True); s.add_argument("--channel", required=True)
    s.add_argument("--titles", nargs="*"); s.add_argument("--words", nargs="*"); s.add_argument("--refs"); s.add_argument("--out", default="thumb_sheet_out"); s.add_argument("--seed", type=int, default=7)
    m = sp.add_parser("make"); m.add_argument("--photo", required=True); m.add_argument("--channel", required=True); m.add_argument("--words", required=True)
    m.add_argument("--out", required=True); m.add_argument("--mask"); m.add_argument("--rect"); m.add_argument("--credit"); m.add_argument("--side", default="right", choices=["right", "left"])
    a = ap.parse_args()
    if a.cmd == "sheet":
        if not a.query and not a.refs: sys.exit("--query or --refs needed")
        cmd_sheet(a)
    else:
        cmd_make(a)


if __name__ == "__main__":
    main()
