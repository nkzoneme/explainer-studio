#!/usr/bin/env python3
"""Contact sheet of the head region: base raw + mouth variants. Usage: mouth_sheet.py <base.png> <out.png> <variant.png>..."""
import sys
from PIL import Image
base = sys.argv[1]; out = sys.argv[2]; vs = sys.argv[3:]
ims = [Image.open(p).convert("RGB") for p in [base] + vs]
W, H = ims[0].size
box = (int(W*0.25), int(H*0.0), int(W*0.75), int(H*0.33))
cs = [im.resize((W, H)).crop(box) for im in ims]
sheet = Image.new("RGB", (cs[0].width*len(cs), cs[0].height), "white")
for i, c in enumerate(cs): sheet.paste(c, (i*c.width, 0))
sheet.save(out); print(out, sheet.size)
