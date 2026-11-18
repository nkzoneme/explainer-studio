#!/usr/bin/env python3
"""Build mouth / blink patches for a host pose from AI-edited variants of the same raw image.

Usage (system python3 with OpenCV + Pillow):
  python3 mouth_patches.py <face_key> <raw_base.png> <pose.webp> <out_dir> <mx> <my> <mw> <eyes_json> SHAPE=variant.png ...
    face_key  : name in Kit.FACES, e.g. host_neutral (used for file names)
    raw_base  : the green-screen PNG the pose webp was cut from (tools_cutout.py)
    pose.webp : the cut-out pose used in compositions (patch coords are in its pixels)
    mx my mw  : mouth centre and width in pose.webp pixels (from Kit.FACES / face_grid.py)
    eyes_json : '[[x,y,rx,ry],...]' eye centres/radii in pose.webp pixels (for the blink patch)
    SHAPE=png : B / A / O / E (mouth shapes) or blink, each an image-to-image edit of raw_base

For each variant: align it to the base (ECC affine, mouth/eyes masked out), find what changed near the
mouth (or eyes), make a feathered mask, colour-match to the base skin around it, and save
<out_dir>/<face_key>_<SHAPE>.webp (RGBA, cropped). Prints a JSON manifest {SHAPE: [x, y, w, h]} in
pose.webp pixels and writes <out_dir>/<face_key>_check.png (base | each patch composited, 2x head crop).
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image


def green_alpha(rgb):
    r, g, b = rgb[..., 0].astype(np.float32), rgb[..., 1].astype(np.float32), rgb[..., 2].astype(np.float32)
    gn = g - np.maximum(r, b)
    return np.clip(1.0 - (gn - 40) / 80, 0, 1)


def main():
    key, raw_p, webp_p, out_dir = sys.argv[1:5]
    mx, my, mw = (float(v) for v in sys.argv[5:8])
    eyes = json.loads(sys.argv[8])
    variants = dict(a.split("=", 1) for a in sys.argv[9:])

    base = np.asarray(Image.open(raw_p).convert("RGB"))
    pose = np.asarray(Image.open(webp_p).convert("RGBA"))
    H, W = base.shape[:2]

    # 1. where the webp sits inside the raw image (template match on an opaque head crop)
    cx, cy = int(mx), int(my)
    t = pose[max(0, cy - 150):cy + 50, max(0, cx - 120):cx + 120]
    res = cv2.matchTemplate(base, np.ascontiguousarray(t[..., :3]), cv2.TM_SQDIFF)
    _, _, loc, _ = cv2.minMaxLoc(res)
    ox, oy = loc[0] - max(0, cx - 120), loc[1] - max(0, cy - 150)
    MX, MY = mx + ox, my + oy  # mouth centre in raw pixels

    # head box (raw px) for alignment
    hx0, hy0 = int(max(0, MX - 3.2 * mw)), int(max(0, MY - 3.6 * mw))
    hx1, hy1 = int(min(W, MX + 3.2 * mw)), int(min(H, MY + 1.6 * mw))
    gbase = cv2.cvtColor(base[hy0:hy1, hx0:hx1], cv2.COLOR_RGB2GRAY).astype(np.float32)
    ecc_mask = np.full(gbase.shape, 255, np.uint8)
    cv2.ellipse(ecc_mask, (int(MX - hx0), int(MY - hy0 + 0.1 * mw)), (int(1.0 * mw), int(0.7 * mw)), 0, 0, 360, 0, -1)
    for ex, ey, erx, ery in eyes:
        cv2.ellipse(ecc_mask, (int(ex + ox - hx0), int(ey + oy - hy0)), (int(erx * 1.6), int(ery * 2.2)), 0, 0, 360, 0, -1)

    manifest, checks, aligned = {}, [], {}
    for shape, vp in variants.items():
        var = np.asarray(Image.open(vp).convert("RGB").resize((W, H), Image.LANCZOS))
        gvar = cv2.cvtColor(var[hy0:hy1, hx0:hx1], cv2.COLOR_RGB2GRAY).astype(np.float32)
        warp = np.eye(2, 3, dtype=np.float32)
        try:
            _, warp = cv2.findTransformECC(gbase, gvar, warp, cv2.MOTION_AFFINE,
                                           (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), ecc_mask, 5)
        except cv2.error as e:
            print(f"[{shape}] ECC failed ({e}); using identity", file=sys.stderr)
        # warp maps base-crop coords -> variant-crop coords; build full-image map
        full = warp.copy(); full[0, 2] += hx0 - (warp[0, 0] * hx0 + warp[0, 1] * hy0); full[1, 2] += hy0 - (warp[1, 0] * hx0 + warp[1, 1] * hy0)
        al = cv2.warpAffine(var, full, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)

        # 2. region of change, restricted to a window
        win = np.zeros((H, W), np.uint8)
        if shape == "blink":
            for ex, ey, erx, ery in eyes:
                cv2.ellipse(win, (int(ex + ox), int(ey + oy)), (int(erx * 1.9), int(ery * 2.6)), 0, 0, 360, 255, -1)
        else:
            cv2.ellipse(win, (int(MX), int(MY + 0.15 * mw)), (int(0.95 * mw), int(0.62 * mw)), 0, 0, 360, 255, -1)
        diff = np.abs(al.astype(np.int16) - base.astype(np.int16)).max(-1).astype(np.uint8)
        diff = cv2.GaussianBlur(diff, (0, 0), 2)
        ch = ((diff > 28) & (win > 0)).astype(np.uint8) * 255
        ch = cv2.morphologyEx(ch, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        n, lab, stats, _ = cv2.connectedComponentsWithStats(ch)
        keep = np.zeros_like(ch)
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] > 40:
                keep[lab == i] = 255
        pts = cv2.findNonZero(keep)
        mask = np.zeros_like(ch)
        if pts is not None:
            if shape == "blink":
                cnts, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for c in cnts:
                    cv2.fillConvexPoly(mask, cv2.convexHull(c), 255)
            else:
                cv2.fillConvexPoly(mask, cv2.convexHull(pts), 255)
        # always cover the artwork's own mouth line so no double lips survive
        if shape != "blink":
            cv2.ellipse(mask, (int(MX), int(MY)), (int(0.75 * mw), int(0.25 * mw)), 0, 0, 360, 255, -1)
        pad = max(6, int(0.09 * mw))
        mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pad + 1, 2 * pad + 1)))
        mask = mask & win if shape == "blink" else mask
        aligned[shape] = (al, mask)

    # all mouth shapes share one mask (union) so the swapped region never changes size between shapes
    mouth_keys = [k for k in aligned if k != "blink"]
    if mouth_keys:
        union = np.zeros((H, W), np.uint8)
        for k in mouth_keys:
            union |= aligned[k][1]
        for k in mouth_keys:
            aligned[k] = (aligned[k][0], union)

    for shape, (al, mask) in aligned.items():
        soft = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), max(3, 0.05 * mw))

        # 3. colour match on the ring just outside the mask
        ring = (cv2.dilate(mask, np.ones((25, 25), np.uint8)) > 0) & (mask == 0)
        patch = al.astype(np.float32)
        if ring.sum() > 50:
            for c in range(3):
                patch[..., c] += base[..., c][ring].mean() - al[..., c][ring].mean()
        patch = patch.clip(0, 255)
        # despill: the variant's green background / offset outline must never leak at the figure edge
        mx_rb = np.maximum(patch[..., 0], patch[..., 2])
        patch[..., 1] = np.minimum(patch[..., 1], mx_rb + 12)

        alpha = soft * green_alpha(base) * green_alpha(al)
        ys, xs = np.nonzero(alpha > 0.01)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        rgba = np.dstack([patch[y0:y1, x0:x1], alpha[y0:y1, x0:x1] * 255]).astype(np.uint8)
        name = f"{key}_{shape}.webp"
        Image.fromarray(rgba).save(f"{out_dir}/{name}", "WEBP", quality=94, exact=True)
        manifest[shape] = [int(x0 - ox), int(y0 - oy), int(x1 - x0), int(y1 - y0)]

        comp = base.astype(np.float32).copy()
        a3 = alpha[..., None]
        comp = comp * (1 - a3) + patch * a3
        checks.append(comp.astype(np.uint8))

    # 4. check sheet: base + composites, head crop at 2x
    tiles = [base] + checks
    crop = lambda im: cv2.resize(im[hy0:hy1, hx0:hx1], None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    sheet = np.hstack([crop(t) for t in tiles])
    Image.fromarray(sheet).save(f"{out_dir}/{key}_check.png")
    print(json.dumps({"offset_raw": [ox, oy], "patches": manifest}))


if __name__ == "__main__":
    main()
