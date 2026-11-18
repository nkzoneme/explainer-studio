#!/usr/bin/env python3
"""Scaffold a native vertical Short (HyperFrames, 1080x1920) for one channel.

Usage (from explainer/):
  python3 shorts/native/new_short.py --style my_channel --dir film/<slug>/shorts/s1 --vo film/<slug>/shorts/s1/vo/s1_w \
      --img prop_scale prop_jet_engine ... --media film/<slug>/ch01/assets/media/logo.png ... [--force]

Creates in --dir:
  kit/ (kit.js, kit.css, sfx/)   shorts.js, shorts.css, style.css (channel colours from shorts/styles/<style>.json)
  assets/fonts/display.ttf       channel display font        assets/img/avatar.png   channel avatar (end card)
  assets/img/<host poses>.webp + assets/img/mouth/            talking host (mouth patches)
  assets/img/<--img names>.webp  from film/assets/img (or a path)   assets/media/<--media files> (+ CREDITS.json if beside them)
  assets/vo/<name>.mp3, levels.js, words.json                 hyperframes.json, package.json
  index.html                     skeleton with WORDS inlined (only if missing or --force)
After editing: sh shorts/native/finish_short.sh <dir> <out.mp4>"""
import argparse, json, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
EXPL = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
from common import load_style


def font_file(st):
    """font_display_file, or "auto": ask fontconfig for font_display (fc-match)."""
    p = st.get("font_display_file", "auto")
    if p and p != "auto" and os.path.exists(p): return p
    import subprocess
    out = subprocess.run(["fc-match", "-f", "%{file}", st.get("font_display", "sans:black")], capture_output=True, text=True).stdout.strip()
    if not out: sys.exit("font not found: set font_display_file in the brand json")
    return out


def initials_avatar(st, out):
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n = 512; im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([8, 8, n - 8, n - 8], fill=st["primary"], outline=st["accent"], width=18)
    txt = "".join(w[0] for w in st.get("channel", "?").split()[:2]).upper()
    fnt = ImageFont.truetype(font_file(st), 220)
    x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=fnt)
    d.text(((n - (x1 - x0)) / 2 - x0, (n - (y1 - y0)) / 2 - y0), txt, font=fnt, fill=st.get("text_on_primary", "#ffffff"))
    im.save(out)


def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", required=True); ap.add_argument("--dir", required=True); ap.add_argument("--vo", required=True)
    ap.add_argument("--img", nargs="*", default=[]); ap.add_argument("--media", nargs="*", default=[])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    st = load_style(a.style)
    d = os.path.join(EXPL, a.dir) if not os.path.isabs(a.dir) else a.dir
    X = lambda p: p if os.path.isabs(p) else os.path.join(EXPL, p)
    os.makedirs(d, exist_ok=True)
    # kit
    for f in ("kit.js", "kit.css"): cp(X("kit/" + f), os.path.join(d, "kit", f))
    if os.path.exists(os.path.join(d, "kit", "sfx")): shutil.rmtree(os.path.join(d, "kit", "sfx"))
    shutil.copytree(X("kit/sfx"), os.path.join(d, "kit", "sfx"))
    for f in ("shorts.js", "shorts.css"): cp(os.path.join(HERE, f), os.path.join(d, f))
    # style vars
    css = (":root {\n"
           f"  --ground: {st['bg']}; --ground2: {st['bg2']}; --ink: {st['ink']}; --navy: {st['primary']};\n"
           f"  --mustard: {st['accent']}; --brick: {st['negative']}; --accent: {st['accent']};\n"
           f"  --title-bg: {st.get('title_bg', st['primary'])}; --title-fg: {st['text_on_primary']}; --card-bg: {st.get('card_bg', '#fffdf7')};\n"
           f"  --cap-fill: {st['caption_fill']}; --cap-outline: {st['caption_outline']}; --cap-active: {st['caption_active']};\n}}\n")
    open(os.path.join(d, "style.css"), "w").write(css)
    cp(font_file(st), os.path.join(d, "assets/fonts/display.ttf"))
    if st.get("avatar") and os.path.exists(X(st["avatar"])): cp(X(st["avatar"]), os.path.join(d, "assets/img/avatar.png"))
    else:
        initials_avatar(st, os.path.join(d, "assets/img/avatar.png"))
        print("note: no avatar in the brand file; made an initials badge (set \"avatar\" to use your own)")
    # host + mouth (optional: a channel without a host leaves host_poses empty)
    for face in (st.get("host_poses") or {}).values():
        src = X(os.path.join(st["host_dir"], face + ".webp"))
        if os.path.exists(src): cp(src, os.path.join(d, "assets/img", face + ".webp"))
        md = X(st.get("mouth_dir") or "")
        if not os.path.isdir(md): continue
        for f in os.listdir(md):
            if f.startswith(face + "_") and f.endswith(".webp"): cp(os.path.join(md, f), os.path.join(d, "assets/img/mouth", f))
    for n in a.img:
        src = X(n) if ("/" in n) else X(os.path.join("film/assets/img", n if n.endswith(".webp") else n + ".webp"))
        cp(src, os.path.join(d, "assets/img", os.path.basename(src)))
    credits = []
    for m in a.media:
        src = X(m); cp(src, os.path.join(d, "assets/media", os.path.basename(src)))
        cj = os.path.join(os.path.dirname(src), "CREDITS.json")
        if os.path.exists(cj):
            for row in json.load(open(cj)):
                if os.path.basename(str(row.get("file", ""))) == os.path.basename(src): credits.append(row)
    if credits: json.dump(credits, open(os.path.join(d, "assets/media/CREDITS.json"), "w"), indent=1)
    # voice
    vo = X(a.vo); name = os.path.basename(vo)
    cp(vo + ".mp3", os.path.join(d, "assets/vo", name + ".mp3"))
    cp(vo + ".levels.js", os.path.join(d, "levels.js"))
    words = json.load(open(vo + ".words.json"))
    cp(vo + ".words.json", os.path.join(d, "words.json"))
    for f in ("hyperframes.json", "package.json"): cp(os.path.join(HERE, f), os.path.join(d, f))
    idx = os.path.join(d, "index.html")
    if not os.path.exists(idx) or a.force:
        vo_len = round(words[-1]["end"] + 0.25, 2); end = round(words[-1]["end"] + 2.3, 1)
        html = open(os.path.join(HERE, "template.html")).read()
        html = (html.replace("__WORDS__", json.dumps(words, separators=(",", ":"))).replace("__END__", str(end))
                .replace("__VOLEN__", str(vo_len)).replace("__VO__", f"assets/vo/{name}.mp3")
                .replace("__CHANNEL__", st["channel"]).replace("__CARDLINE__", st["end_card_line"]))
        poses = st.get("host_poses") or {}
        if not poses:   # channel without a host: drop the host layer and its timeline lines
            import re
            html = re.sub(r"\s*<!--HOST-->.*?<!--/HOST-->", "", html, flags=re.S)
            html = re.sub(r"\s*//HOST\n.*?//HOST_END", "", html, flags=re.S)
        else:           # use the channel's first pose name
            face = list(poses.values())[0]
            html = html.replace("host_neutral", face)
        html = html.replace("<!--HOST-->", "").replace("<!--/HOST-->", "").replace("      //HOST\n", "").replace("      //HOST_END\n", "")
        open(idx, "w").write(html)
    print(f"scaffolded {d}  (VO {words[-1]['end']:.2f} s, {len(words)} words)")


if __name__ == "__main__":
    main()
