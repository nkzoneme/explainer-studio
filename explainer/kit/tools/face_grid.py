#!/usr/bin/env python3
"""Measure mouth/eye coordinates of a host pose for Kit.FACES. Usage:
  python3 face_grid.py <pose.webp> <out.png> [x0 y0 x1 y1]
Writes a 2x enlarged crop of the head (default: top 30 % of the image) with a 20 px grid labelled in
NATIVE image pixels. Read off: mouth centre + width + tilt, each eye centre + radii, and sample the skin
colour printed for the point under each eye."""
import sys
from PIL import Image, ImageDraw
im = Image.open(sys.argv[1]).convert('RGBA'); out = sys.argv[2]
x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7]) if len(sys.argv) >= 7 else (0, 0, im.width, int(im.height*0.3))
bg = Image.new('RGBA', im.size, (243, 233, 216, 255)); bg.alpha_composite(im)
c = bg.crop((x0, y0, x1, y1)); c = c.resize((c.width*2, c.height*2), Image.LANCZOS).convert('RGB'); d = ImageDraw.Draw(c)
for gx in range((x0//20+1)*20, x1, 20):
    d.line([((gx-x0)*2, 0), ((gx-x0)*2, c.height)], fill=(255, 0, 0) if gx % 100 == 0 else (0, 160, 255), width=1)
    if gx % 40 == 0: d.text(((gx-x0)*2+2, 2), str(gx), fill=(255, 0, 0))
for gy in range((y0//20+1)*20, y1, 20):
    d.line([(0, (gy-y0)*2), (c.width, (gy-y0)*2)], fill=(255, 0, 0) if gy % 100 == 0 else (0, 160, 255), width=1)
    if gy % 40 == 0: d.text((2, (gy-y0)*2+2), str(gy), fill=(255, 0, 0))
c.save(out); print(out, 'crop', (x0, y0, x1, y1))
