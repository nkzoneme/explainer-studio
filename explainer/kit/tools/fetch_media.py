#!/usr/bin/env python3
"""Fetch real logos / photos / archival footage with license metadata, for the explainer kit.

Sources: Wikidata (P154 logo, P18 image) -> Wikimedia Commons / Wikipedia file pages, Commons search,
Internet Archive advancedsearch. Every file is recorded in OUT_DIR/CREDITS.json (+ CREDITS.md, ready to
paste into the video description). Files without a clear free license (non-free / fair-use logos that live
only on en.wikipedia, unknown licenses) go to OUT_DIR/nonfree/ and are flagged: a human decides.

Usage (system python3; needs requests + Pillow, rsvg-convert for SVG):
  fetch_media.py logo "Delta Air Lines" OUT_DIR            # official logo via Wikidata P154 / Wikipedia infobox
  fetch_media.py logo Q188920 OUT_DIR                      # same, by Wikidata QID
  fetch_media.py image "Tesla Model 3" OUT_DIR            # the entity's main Wikidata image (P18)
  fetch_media.py commons "Tesla Model 3" OUT_DIR --n 5  # Commons file search (photos)
  fetch_media.py file "File:Delta logo.svg" OUT_DIR        # exact Commons/Wikipedia file
  fetch_media.py archive "city street 1950s" OUT_DIR --n 3 [--video]   # Internet Archive (PD / CC only)
  fetch_media.py pexels "train station"   OUT_DIR --n 3 [--video]  # Pexels stock (PEXELS_API_KEY in project .env)
  fetch_media.py pixabay "server room" OUT_DIR --n 3 [--video]      # Pixabay stock (PIXABAY_API_KEY in project .env)
  fetch_media.py commons-video "steam train" OUT_DIR --n 3 [--min-w 640] [--max-sec 90]   # Commons video -> silent H.264 mp4
  fetch_media.py nasa-video "air traffic" OUT_DIR --n 3     # NASA Image and Video Library (no key)
  fetch_media.py archive "factory 1960s" OUT_DIR --n 3 --video --vetted [--hd]   # only gov/NASA/Prelinger collections
  fetch_media.py dvids "flight line" OUT_DIR                # stub until DVIDS_API_KEY is in .env
  fetch_media.py scan IN.mp4 OUT.png [--every 6] [--cols 5] # timestamped tile sheet: look before you cut
  fetch_media.py clip IN.mp4 START DUR OUT.mp4 [--width 960|1280|1920] [--fps 30] [--look duotone|halftone --palette <slug>]
                                                            # cut a silent clip for a K.tv prop (credit row copied)
  fetch_media.py treat IN.mp4 OUT.mp4 --palette <slug> [--look duotone|halftone] [--width 960] [--fps 30]
                                                            # ink/paper duotone or halftone in the channel palette (shorts/styles/*.json)
  fetch_media.py used OUT_DIR index.html                    # CREDITS_USED.md: only files the composition references
  fetch_media.py sheet OUT_DIR                             # rebuild OUT_DIR/contact_sheet.png
Options: --n N (results), --width W (raster width, default 1600, max 2000), --name SLUG (output base name).

Logos are trademarks even when the file is public domain (PD-textlogo): fine for commentary/identification,
never imply endorsement. The license column says whether the *file* is free to reuse.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

# Wikimedia's upload servers return 429 to agents without a URL in the UA. Default carries no personal data;
# set EXPLAINER_UA (e.g. "explainer-kit/0.1 (+https://your-channel-site)") to identify the channel properly.
UA = {"User-Agent": os.environ.get("EXPLAINER_UA") or "explainer-kit/0.1 (+https://www.mediawiki.org/wiki/API:Etiquette; educational video asset fetcher)"}
COMMONS = "https://commons.wikimedia.org/w/api.php"
ENWIKI = "https://en.wikipedia.org/w/api.php"
WIKIDATA = "https://www.wikidata.org/w/api.php"
S = requests.Session()
S.headers.update(UA)
_last = [0.0]

FREE_RE = re.compile(r"^(cc0|cc[- ]by|cc[- ]by[- ]sa|public domain|pd|pdm|attribution|no restrictions|copyrighted free use)", re.I)


def get(url: str, **params) -> requests.Response:
    """Polite GET: >= 1 s between requests, retries on 429/5xx."""
    for attempt in range(6):
        wait = 1.0 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        r = S.get(url, params=params or None, timeout=60)
        if r.status_code in (429, 500, 502, 503, 504):
            ra = r.headers.get("Retry-After", "")
            time.sleep(int(ra) if ra.isdigit() else 5 * (attempt + 1))
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r


def strip_html(s: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60] or "media"


# ------------------------------------------------------------------------------------------- wiki
def wikidata_qid(name: str) -> str | None:
    if re.fullmatch(r"Q\d+", name):
        return name
    # exact Wikipedia article title first (most reliable: "Apple Inc."), then Wikidata search
    d = get(ENWIKI, action="query", titles=name, redirects=1, prop="pageprops", ppprop="wikibase_item", format="json").json()
    for p in (d.get("query", {}).get("pages") or {}).values():
        q = (p.get("pageprops") or {}).get("wikibase_item")
        if q:
            return q
    d = get(WIKIDATA, action="wbsearchentities", search=name, language="en", format="json", limit=5, type="item").json()
    hits = d.get("search") or []
    return hits[0]["id"] if hits else None


def wikidata_claims(qid: str) -> tuple[dict, str, str | None]:
    d = get(WIKIDATA, action="wbgetentities", ids=qid, props="claims|labels|sitelinks", languages="en", format="json").json()
    e = d["entities"][qid]
    label = (e.get("labels", {}).get("en") or {}).get("value", qid)
    enwiki = (e.get("sitelinks", {}).get("enwiki") or {}).get("title")
    return e.get("claims", {}), label, enwiki


def claim_files(claims: dict, prop: str) -> list[str]:
    out = []
    for c in claims.get(prop, []):
        # prefer statements without an end date (P582) = current logo
        if "P582" in (c.get("qualifiers") or {}):
            continue
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, str):
            out.append(("File:" + v) if not v.startswith("File:") else v)
    if not out:  # all have end dates: take the last one listed
        for c in claims.get(prop, [])[-1:]:
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(v, str):
                out.append("File:" + v)
    return out


def file_info(title: str, width: int) -> dict | None:
    """imageinfo via en.wikipedia (resolves both local non-free files and shared Commons files)."""
    for api in (ENWIKI, COMMONS):
        d = get(api, action="query", titles=title, prop="imageinfo", iiprop="url|size|mime|extmetadata",
                iiurlwidth=width, format="json").json()
        for p in (d.get("query", {}).get("pages") or {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            if ii:
                ii["title"] = p.get("title", title)
                ii["repo"] = p.get("imagerepository") or ("shared" if api == COMMONS else "local")
                return ii
    return None


def gfdl_check(ii: dict, lic: str) -> tuple[bool, str]:
    """GFDL-only files are NOT free for video. Dual-licensed files (GFDL plus any CC / public-domain grant) stay free."""
    m = ii.get("extmetadata") or {}
    txt = " ".join(strip_html((m.get(k) or {}).get("value")) for k in ("LicenseShortName", "UsageTerms", "License", "LicenseUrl", "Categories", "Attribution")).lower() + " " + lic.lower()
    gfdl = bool(re.search(r"gfdl|gnu free documentation|/fdl", txt))
    other = bool(re.search(r"cc[- ]?0|cc[- ]?by|creative commons|public domain|\bpd[- ]|pdm|no restrictions", txt))
    if gfdl and not other:
        return True, "GFDL-only: the licence text has to be shipped with the work, which a video cannot do; replace the file or find a CC/PD one"
    return False, ""


def license_of(ii: dict) -> tuple[str, bool, str, str]:
    m = ii.get("extmetadata") or {}
    val = lambda k: strip_html((m.get(k) or {}).get("value"))
    lic = val("LicenseShortName") or val("UsageTerms") or val("License") or "unknown"
    nonfree = val("NonFree").lower() == "true" or "non-free" in lic.lower() or "fair use" in lic.lower()
    free = (not nonfree) and bool(FREE_RE.search(lic)) and ii.get("repo") != "local"
    if ii.get("repo") == "local" and not nonfree and FREE_RE.search(lic):
        free = True  # rare: free file uploaded locally to en.wikipedia
    gfdl_only, why = gfdl_check(ii, lic)
    if gfdl_only:
        free = False          # GFDL-only: the licence text must accompany the work, which a video cannot do (17/11/2026 review)
        lic = lic + " (GFDL-only, not free for video)" if "gfdl" in lic.lower() and "not free" not in lic else lic
    if not gfdl_only and not nonfree and ii.get("repo") != "local" and re.search(r"\bcc0\b|cc[- ]by|public domain|\bpd\b", lic, re.I):
        free = True           # dual-licensed ("GFDL 1.2 or CC BY-SA 3.0"): the CC grant makes it free
    ii["_reason"] = why if gfdl_only else ("" if free else ("non-free licence" if nonfree else "licence not recognised as free"))
    author = val("Artist") or val("Credit") or "unknown"
    return (lic if not nonfree else "non-free (fair use)"), free, author[:160], val("LicenseUrl")


def enwiki_logo_files(title: str) -> list[str]:
    """Files used on the Wikipedia article whose name looks like a logo (infobox logo fallback)."""
    d = get(ENWIKI, action="query", titles=title, prop="images", imlimit=50, format="json", redirects=1).json()
    files = []
    for p in (d.get("query", {}).get("pages") or {}).values():
        for im in p.get("images") or []:
            t = im["title"]
            if re.search(r"logo|wordmark", t, re.I) and not re.search(r"commons-logo|wikiquote|wiktionary|wikinews|wikisource|wikivoyage|wikidata|symbol_support|edit-clear|question_book|ambox|padlock|folder", t, re.I):
                files.append(t)
    return files


# ------------------------------------------------------------------------------------------- save
def load_credits(out: Path) -> list[dict]:
    p = out / "CREDITS.json"
    return json.load(open(p)) if p.exists() else []


def save_credits(out: Path, rows: list[dict]) -> None:
    json.dump(rows, open(out / "CREDITS.json", "w"), indent=1, ensure_ascii=False)
    free = [r for r in rows if r["free"]]
    flagged = [r for r in rows if not r["free"]]
    md = ["# Media credits", "", "Paste the block below into the video description.", "", "```"]
    for r in free:
        md.append(f'{r["subject"]}: "{r["title"]}" by {r["author"]}, {r["license"]} — {r["source_url"]}')
    md += ["```", ""]
    if flagged:
        md += ["## Flagged — NOT free, human decision needed (in nonfree/)", ""]
        md += [f'- {r["file"]}: {r["license"]} — {r["source_url"]}' for r in flagged]
        md.append("")
    md += ["Logos are trademarks of their owners; shown for identification/commentary only."]
    (out / "CREDITS.md").write_text("\n".join(md) + "\n")


def download(url: str, dest: Path) -> None:
    r = get(url)
    dest.write_bytes(r.content)


def store_wiki_file(ii: dict, out: Path, subject: str, kind: str, base: str, width: int) -> dict:
    lic, free, author, lic_url = license_of(ii)
    d = out if free else out / "nonfree"
    d.mkdir(parents=True, exist_ok=True)
    mime = ii.get("mime", "")
    if mime == "image/svg+xml":
        svg = d / f"{base}.svg"
        download(ii["url"], svg)
        png = d / f"{base}.png"
        ok = subprocess.run(["rsvg-convert", "-w", str(width), "--keep-aspect-ratio", "-o", str(png), str(svg)],
                            capture_output=True).returncode == 0
        if not ok and ii.get("thumburl"):
            download(ii["thumburl"], png)
        fname = png
    else:
        url = ii.get("thumburl") if (ii.get("width") or 0) > width and ii.get("thumburl") else ii["url"]
        ext = Path(url.split("?")[0]).suffix.lower() or ".jpg"
        fname = d / f"{base}{ext}"
        download(url, fname)
    page = ii.get("descriptionurl") or ii["url"]
    return {"file": str(fname.relative_to(out)), "subject": subject, "kind": kind, "title": ii["title"].replace("File:", ""),
            "author": author, "license": lic, "license_url": lic_url, "free": free, "reason": ii.get("_reason", ""), "repo": ii.get("repo"),
            "source_url": page}


def probe(p: Path) -> dict:
    """duration / width / height of a video via ffprobe (empty dict on failure)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-show_entries", "format=duration", "-of", "json", str(p)], capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
        return {"width": j["streams"][0]["width"], "height": j["streams"][0]["height"], "duration": round(float(j["format"]["duration"]), 1)}
    except Exception:
        return {}


def add(out: Path, rows: list[dict]) -> None:
    for r in rows:
        if r.get("kind") == "footage" and "duration" not in r and (out / r["file"]).exists():
            r.update(probe(out / r["file"]))
    allr = [r for r in load_credits(out) if r["file"] not in {x["file"] for x in rows}] + rows
    save_credits(out, allr)
    for r in rows:
        flag = "FREE " if r["free"] else "FLAG "
        print(f'{flag} {r["file"]}  [{r["license"]}]  {r["author"][:50]}  {r["source_url"]}' + (f'  REASON: {r["reason"]}' if r.get("reason") and not r["free"] else ""))
    contact_sheet(out)


# ------------------------------------------------------------------------------------------- modes
def cmd_logo(name: str, out: Path, width: int, base: str | None, prop: str = "P154", kind: str = "logo") -> None:
    qid = wikidata_qid(name)
    files, label, enwiki = [], name, None
    if qid:
        claims, label, enwiki = wikidata_claims(qid)
        files = claim_files(claims, prop)
    print(f"[{kind}] {name} -> {qid} ({label}), enwiki={enwiki}, wikidata files={files}")
    if not files and kind == "logo":
        files = enwiki_logo_files(enwiki or name)[:2]
        print(f"  fallback: Wikipedia article logo files {files}")
    rows = []
    for i, f in enumerate(files[:2]):
        ii = file_info(f, width)
        if not ii:
            print(f"  ! no imageinfo for {f}")
            continue
        rows.append(store_wiki_file(ii, out, label, kind, (base or f"{kind}_{slug(label)}") + (f"_{i+1}" if i else ""), width))
    if not rows:
        print("  ! nothing found — try `commons` search or an exact `file`")
    add(out, rows)


def cmd_file(title: str, out: Path, width: int, base: str | None) -> None:
    t = title if title.startswith("File:") else "File:" + title
    ii = file_info(t, width)
    if not ii:
        sys.exit(f"not found: {t}")
    add(out, [store_wiki_file(ii, out, t[5:], "file", base or slug(Path(t[5:]).stem), width)])


def cmd_commons(query: str, out: Path, n: int, width: int, base: str | None) -> None:
    d = get(COMMONS, action="query", generator="search", gsrsearch=f"filetype:bitmap {query}", gsrnamespace=6,
            gsrlimit=max(n * 2, 8), prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=width, format="json").json()
    pages = sorted((d.get("query", {}).get("pages") or {}).values(), key=lambda p: p.get("index", 99))
    rows = []
    for p in pages:
        ii = (p.get("imageinfo") or [None])[0]
        if not ii or (ii.get("width") or 0) < 800:
            continue
        ii["title"], ii["repo"] = p["title"], "shared"
        rows.append(store_wiki_file(ii, out, query, "photo", f"{base or slug(query)}_{len(rows)+1}", width))
        if len(rows) >= n:
            break
    add(out, rows)


IA_FREE = re.compile(r"creativecommons\.org/(publicdomain|licenses/(by|by-sa)/)|publicdomain", re.I)


IA_ALLOW = {"prelinger", "prelingerhomemovies", "usgovfilms", "fedflix", "nasa", "nasaaudiocollection", "us_congress"}
IA_DENY = re.compile(r"periscope|mirrortube|tvarchive|^tv-|social-media|youtube|vhsvault|c-?span|opensource_movies|community", re.I)
IA_NC = re.compile(r"/by-n[cd]|-nc|-nd", re.I)


def ia_vetted(ident: str, coll: list[str], lic_url: str) -> bool:
    """--vetted: allowlisted gov/NASA/Prelinger collection, no denylisted collection, no NC/ND licence, no C-SPAN copies."""
    low = [c.lower() for c in coll]
    return (any(c in IA_ALLOW for c in low) and not any(IA_DENY.search(c) for c in coll)
            and not IA_NC.search(lic_url or "") and not ident.lower().startswith("org.c-span"))


def cmd_archive(query: str, out: Path, n: int, video: bool, base: str | None, vetted: bool = False, hd: bool = False) -> None:
    mt = "movies" if video else "image"
    q = f"({query}) AND mediatype:{mt} AND (licenseurl:*publicdomain* OR licenseurl:*creativecommons* OR collection:prelinger OR collection:nasa)"
    if vetted:
        q = f"({query}) AND mediatype:{mt} AND (collection:prelinger OR collection:usgovfilms OR collection:FedFlix OR collection:nasa)"
    d = get("https://archive.org/advancedsearch.php", q=q, rows=n * 3, output="json",
            **{"fl[]": ["identifier", "title", "creator", "licenseurl", "collection", "year"]}).json()
    rows = []
    for doc in d.get("response", {}).get("docs", []):
        ident = doc["identifier"]
        lic_url = doc.get("licenseurl") or ""
        coll = doc.get("collection") or []
        coll = coll if isinstance(coll, list) else [coll]
        if not lic_url and "prelinger" in coll:
            lic_url = "Prelinger Archives (public domain)"
        if not lic_url and "nasa" in coll:
            lic_url = "NASA (public domain, US gov)"
        free = bool(IA_FREE.search(lic_url)) or "public domain" in lic_url.lower()
        if vetted and not ia_vetted(ident, coll, lic_url):
            print(f"  skip {ident}: not vetted (collections {coll[:3]}, licence {lic_url or 'none'})")
            continue
        meta = get(f"https://archive.org/metadata/{ident}").json()
        files = meta.get("files") or []
        if video:
            cands = [f for f in files if f.get("name", "").lower().endswith(".mp4")]
            cands.sort(key=lambda f: int(f.get("size") or 1e12))  # smallest mp4 derivative is enough for a TV prop
            if hd:  # largest mp4 up to 150 MB
                ok = [f for f in cands if int(f.get("size") or 0) <= 150e6]
                cands = sorted(ok, key=lambda f: -int(f.get("size") or 0)) or cands
        else:
            cands = [f for f in files if f.get("format") in ("JPEG", "PNG") and "thumb" not in f.get("name", "").lower()]
            cands.sort(key=lambda f: -int(f.get("size") or 0))
        if not cands:
            continue
        f = cands[0]
        if int(f.get("size") or 0) > 300e6:
            print(f"  skip {ident}: {int(f['size'])/1e6:.0f} MB")
            continue
        dd = out if free else out / "nonfree"
        dd.mkdir(parents=True, exist_ok=True)
        dest = dd / f"{base or slug(query)}_{len(rows)+1}{Path(f['name']).suffix.lower()}"
        download(f"https://archive.org/download/{ident}/{requests.utils.quote(f['name'])}", dest)
        rows.append({"file": str(dest.relative_to(out)), "subject": query, "kind": "footage" if video else "photo",
                     "title": doc.get("title") or ident, "author": (doc.get("creator") if isinstance(doc.get("creator"), str) else ", ".join(doc.get("creator") or [])) or "unknown",
                     "license": lic_url or "unknown", "license_url": lic_url, "free": free, "repo": "archive.org",
                     "source_url": f"https://archive.org/details/{ident}",
                     "tier": "A", "risk": "low" if any(c.lower() in ("prelinger", "usgovfilms", "fedflix", "nasa") for c in coll) else "check",
                     "content_id_note": "" if free else "uploader-claimed licence: verify before use"})
        if len(rows) >= n:
            break
    add(out, rows)


# ------------------------------------------------------------------------------------------- stock (Pexels, Pixabay)
ENV_FILES = [Path(__file__).resolve().parents[3] / ".env", Path(__file__).resolve().parents[2] / ".env"]  # <repo>/.env, explainer/.env


def env_key(name: str) -> str:
    """Read one key from the project .env without printing it."""
    if os.environ.get(name):
        return os.environ[name]
    for f in ENV_FILES:
        if f.exists():
            for line in f.read_text().splitlines():
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit(f"{name} not set (add it to the project .env)")


def stock_get(url: str, params: dict, headers: dict | None = None) -> dict:
    """GET without ever echoing the URL (Pixabay puts the key in the query string)."""
    for attempt in range(4):
        wait = 1.0 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        r = requests.get(url, params=params, headers=headers or {}, timeout=60)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 * (attempt + 1)); continue
        if r.status_code != 200:
            sys.exit(f"stock API error {r.status_code} from {url.split('?')[0]}")
        return r.json()
    sys.exit(f"stock API kept failing: {url.split('?')[0]}")


def stock_save(out: Path, url: str, base: str, ext: str) -> Path:
    dest = out / f"{base}{ext}"
    r = requests.get(url, timeout=180, headers={"User-Agent": UA["User-Agent"]})
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def cmd_pexels(query: str, out: Path, n: int, video: bool, base: str | None) -> None:
    hdr = {"Authorization": env_key("PEXELS_API_KEY")}
    rows = []
    if video:
        d = stock_get("https://api.pexels.com/videos/search", {"query": query, "per_page": max(n * 2, 6), "orientation": "landscape"}, hdr)
        for v in d.get("videos", []):
            files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and (f.get("width") or 0) <= 1920]
            files.sort(key=lambda f: -(f.get("width") or 0))
            if not files:
                continue
            dest = stock_save(out, files[0]["link"], f"{base or slug(query)}_px{len(rows)+1}", ".mp4")
            rows.append({"file": str(dest.relative_to(out)), "subject": query, "kind": "footage", "title": f"Pexels video {v['id']}",
                         "author": (v.get("user") or {}).get("name", "unknown"), "license": "Pexels License (free, no attribution required)",
                         "license_url": "https://www.pexels.com/license/", "free": True, "repo": "pexels", "source_url": v.get("url", "")})
            if len(rows) >= n:
                break
    else:
        d = stock_get("https://api.pexels.com/v1/search", {"query": query, "per_page": max(n * 2, 6)}, hdr)
        for p in d.get("photos", []):
            dest = stock_save(out, p["src"]["large2x"], f"{base or slug(query)}_px{len(rows)+1}", ".jpg")
            rows.append({"file": str(dest.relative_to(out)), "subject": query, "kind": "photo", "title": p.get("alt") or f"Pexels photo {p['id']}",
                         "author": p.get("photographer", "unknown"), "license": "Pexels License (free, no attribution required)",
                         "license_url": "https://www.pexels.com/license/", "free": True, "repo": "pexels", "source_url": p.get("url", "")})
            if len(rows) >= n:
                break
    add(out, rows)


def cmd_pixabay(query: str, out: Path, n: int, video: bool, base: str | None) -> None:
    key = env_key("PIXABAY_API_KEY")
    rows = []
    if video:
        d = stock_get("https://pixabay.com/api/videos/", {"key": key, "q": query, "per_page": max(n * 2, 6), "safesearch": "true"})
        for h in d.get("hits", []):
            vids = h.get("videos") or {}
            v = vids.get("large") if (vids.get("large") or {}).get("url") else vids.get("medium")
            if not v or not v.get("url"):
                continue
            dest = stock_save(out, v["url"], f"{base or slug(query)}_pb{len(rows)+1}", ".mp4")
            rows.append({"file": str(dest.relative_to(out)), "subject": query, "kind": "footage", "title": h.get("tags") or f"Pixabay video {h['id']}",
                         "author": h.get("user", "unknown"), "license": "Pixabay Content License (free, no attribution required)",
                         "license_url": "https://pixabay.com/service/license-summary/", "free": True, "repo": "pixabay", "source_url": h.get("pageURL", "")})
            if len(rows) >= n:
                break
    else:
        d = stock_get("https://pixabay.com/api/", {"key": key, "q": query, "per_page": max(n * 2, 6), "image_type": "photo", "safesearch": "true"})
        for h in d.get("hits", []):
            url = h.get("largeImageURL") or h.get("webformatURL")
            dest = stock_save(out, url, f"{base or slug(query)}_pb{len(rows)+1}", Path(url.split("?")[0]).suffix or ".jpg")
            rows.append({"file": str(dest.relative_to(out)), "subject": query, "kind": "photo", "title": h.get("tags") or f"Pixabay image {h['id']}",
                         "author": h.get("user", "unknown"), "license": "Pixabay Content License (free, no attribution required)",
                         "license_url": "https://pixabay.com/service/license-summary/", "free": True, "repo": "pixabay", "source_url": h.get("pageURL", "")})
            if len(rows) >= n:
                break
    add(out, rows)


# ------------------------------------------------------------------------------------------- footage (video-first sources)
GOV_RE = re.compile(r"federal bureau|\bfbi\b|nasa|white house|department of|u\.s\. |united states|public affairs|dvids|us navy|noaa|\bfaa\b|ntsb|national archives", re.I)
NEWS_RE = re.compile(r"\b(news|tv|television|broadcast|getty|reuters|associated press|ap|cbs|nbc|cnn|fox|bbc|afp|storyful|promo|trailer)\b", re.I)


def commons_risk(ii: dict) -> tuple[str, str]:
    """(risk, content_id_note) for a Commons video: PD claims on TV/news/promo material are the trap."""
    m = ii.get("extmetadata") or {}
    text = " ".join(strip_html((m.get(k) or {}).get("value")) for k in ("Credit", "ImageDescription", "Artist", "Categories", "Source", "Permission"))
    gov = bool(GOV_RE.search(strip_html((m.get("Artist") or {}).get("value"))))  # author field only: descriptions mention "U.S." everywhere
    news, yt = bool(NEWS_RE.search(text)), "youtube" in text.lower()
    if news and not gov:
        return "high", "looks like TV/news/promo material behind a free-licence claim: tier D, human review (file goes to review/)"
    if yt and not gov:
        return "check", "also exists on YouTube: Content ID may match; keep the cut under 12 s, silent, keep a dispute note"
    return "low", ""


def stream_download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=180, headers={"User-Agent": UA["User-Agent"]}) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)


def transcode(src: str, dest: Path, width: int = 1280, fps: int = 30, max_sec: float | None = None, vf_extra: str = "") -> None:
    """Silent H.264 mp4 (reads remote URLs too; -t keeps huge files cheap)."""
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if src.startswith("http"):
        cmd += ["-user_agent", UA["User-Agent"]]
    cmd += ["-i", src]
    if max_sec:
        cmd += ["-t", str(max_sec)]
    vf = f"scale='min({width},iw)':-2:flags=lanczos,fps={fps}" + (("," + vf_extra) if vf_extra else "")
    subprocess.run(cmd + ["-an", "-vf", vf, "-c:v", "libx264", "-crf", "20", "-g", str(fps), "-pix_fmt", "yuv420p", str(dest)], check=True)


def cmd_commons_video(query: str, out: Path, n: int, base: str | None, min_w: int, max_sec: float) -> None:
    d = get(COMMONS, action="query", generator="search", gsrsearch=f"filetype:video {query}", gsrnamespace=6,
            gsrlimit=max(n * 4, 12), prop="imageinfo", iiprop="url|size|mime|extmetadata|mediatype", format="json").json()
    pages = sorted((d.get("query", {}).get("pages") or {}).values(), key=lambda p: p.get("index", 99))
    rows = []
    for p in pages:
        ii = (p.get("imageinfo") or [None])[0]
        if not ii or (ii.get("width") or 0) < min_w:
            continue
        ii["title"], ii["repo"] = p["title"], "shared"
        lic, free, author, lic_url = license_of(ii)
        risk, note = commons_risk(ii)
        if risk == "high":
            free = False
        dd = out if free else out / "review"
        dd.mkdir(parents=True, exist_ok=True)
        dest = dd / f"{base or slug(query)}_cv{len(rows)+1}.mp4"
        print(f"  {p['title']}: {ii.get('width')}x{ii.get('height')} {ii.get('duration', 0):.0f}s {lic} risk={risk} -> first {max_sec:.0f}s")
        transcode(ii["url"], dest, max_sec=max_sec)
        rows.append({"file": str(dest.relative_to(out)), "subject": query, "kind": "footage", "title": p["title"].replace("File:", ""),
                     "author": author, "license": lic, "license_url": lic_url, "free": free and risk != "high", "reason": ii.get("_reason", "") or ("high content-id risk" if risk == "high" else ""), "repo": "commons",
                     "source_url": ii.get("descriptionurl") or ii["url"], "tier": "A", "risk": risk, "content_id_note": note,
                     "source_duration": round(ii.get("duration") or 0, 1), "source_width": ii.get("width"), "source_height": ii.get("height")})
        if len(rows) >= n:
            break
    add(out, rows)


def cmd_nasa_video(query: str, out: Path, n: int, base: str | None) -> None:
    d = get("https://images-api.nasa.gov/search", q=query, media_type="video").json()
    rows = []
    for it in (d.get("collection", {}).get("items") or []):
        x = it["data"][0]
        nid = x["nasa_id"]
        urls = [u.replace("http://", "https://") for u in get(it["href"].replace("http://", "https://")).json() if u.lower().endswith(".mp4")]
        pick = next((u for tag in ("~large", "~medium", "~orig") for u in urls if tag in u), None)
        if not pick:
            continue
        text = f'{x.get("description", "")} {x.get("secondary_creator", "")} {x.get("photographer", "")}'
        third = bool(re.search(r"copyright|courtesy|©|licensed", text, re.I))
        dd = out if not third else out / "review"
        dd.mkdir(parents=True, exist_ok=True)
        dest = dd / f"{base or slug(query)}_nasa{len(rows)+1}.mp4"
        stream_download(pick, dest)
        rows.append({"file": str(dest.relative_to(out)), "subject": query, "kind": "footage", "title": x.get("title") or nid,
                     "author": f'NASA/{x.get("center", "")}'.rstrip("/"), "license": "NASA media usage guidelines (acknowledge NASA; no endorsement)",
                     "license_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/", "free": not third, "repo": "nasa",
                     "source_url": f"https://images.nasa.gov/details/{nid}", "tier": "A", "risk": "check" if third else "low",
                     "content_id_note": "third-party material flagged in the NASA record: human review" if third else "",
                     "notice": "Source: NASA. NASA does not endorse this video."})
        if len(rows) >= n:
            break
    add(out, rows)


def cmd_dvids(query: str, out: Path) -> None:
    env_key("DVIDS_API_KEY")  # exits with a clear message when the key is missing
    sys.exit("dvids: DVIDS_API_KEY is set but the fetch is not built yet. "
             "Remember the notice 'The appearance of U.S. Department of War visual information does not imply or constitute DoW endorsement.'")


def cmd_scan(src: Path, dst: Path, every: float, cols: int) -> None:
    dur = probe(src).get("duration") or 60
    count = int(dur // every) + 1
    rows = min(8, -(-count // cols))
    vf = (f"fps=1/{every},scale=320:-2,drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontcolor=yellow:fontsize=18:box=1:boxcolor=black,"
          f"tile={cols}x{rows}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf, "-frames:v", "1", str(dst)], check=True)
    print(f"{dst}  ({dur:.0f}s, one frame per {every:g}s, {cols}x{rows} tiles)")


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def palette_for(channel: str) -> tuple[str, str]:
    """(dark, light) hex from shorts/styles/<channel>.json: ink -> paper (light bg) or ink -> text_on_primary (dark bg)."""
    f = Path(__file__).resolve().parents[2] / "shorts" / "styles" / f"{channel}.json"
    if not f.exists():
        sys.exit(f"palette: {f} not found (make one from shorts/styles/_example.json)")
    st = json.load(open(f))
    lum = lambda h: sum(c * w for c, w in zip(hex_rgb(h), (0.299, 0.587, 0.114)))
    return st["ink"], (st["bg"] if lum(st["bg"]) > 128 else st.get("text_on_primary", "#ffffff"))


def treat_filter(look: str, dark: str, light: str, pitch: int) -> str:
    (dr, dg, db), (lr, lg, lb) = hex_rgb(dark), hex_rgb(light)
    lut = f"format=rgb24,lutrgb=r='{dr}+val*{(lr-dr)/255:.4f}':g='{dg}+val*{(lg-dg)/255:.4f}':b='{db}+val*{(lb-db)/255:.4f}'"
    if look == "halftone":  # 45 degree dot screen
        k = 0.7071 / pitch
        return (f"format=gray,eq=contrast=1.25,geq=lum='255*gt(lum(X\\,Y)/255\\,0.5+0.25*(cos(2*PI*(X+Y)*{k:.5f})+cos(2*PI*(X-Y)*{k:.5f})))'," + lut)
    return "format=gray,eq=contrast=1.3," + lut  # duotone


def copy_credit(src: Path, dst: Path, **extra) -> None:
    out = src.parent
    try:
        rel_dst = str(dst.relative_to(out))
    except ValueError:
        return
    rows = load_credits(out)
    for r in list(rows):
        if r["file"] == src.name:
            nr = dict(r, file=rel_dst, **extra)
            nr.update(probe(dst))
            rows = [x for x in rows if x["file"] != rel_dst] + [nr]
            save_credits(out, rows)
            return


def cmd_treat(src: Path, dst: Path, palette: str, look: str, width: int, fps: int, start: str | None = None, dur: str | None = None) -> None:
    dark, light = palette_for(palette)
    pitch = max(4, round(width / 213))
    cmd = ["ffmpeg", "-v", "error", "-y"] + (["-ss", start] if start else []) + ["-i", str(src)] + (["-t", dur] if dur else [])
    vf = f"scale={width}:-2:flags=lanczos,fps={fps}," + treat_filter(look, dark, light, pitch)
    subprocess.run(cmd + ["-an", "-vf", vf, "-c:v", "libx264", "-crf", "18", "-g", str(fps), "-pix_fmt", "yuv420p", str(dst)], check=True)
    copy_credit(src, dst, treatment=f"{look}:{palette}")
    print(dst)


# ------------------------------------------------------------------------------------------- contact sheet
def contact_sheet(out: Path) -> None:
    from PIL import Image, ImageDraw
    rows = load_credits(out)
    cells = []
    for r in rows:
        p = out / r["file"]
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif") and p.exists():
            try:
                im = Image.open(p).convert("RGBA")
            except Exception:
                continue
        elif p.suffix.lower() in (".mp4", ".webm", ".ogv") and p.exists():
            tmp = out / ".sheet_frame.png"
            ss = min(3.0, (probe(p).get("duration") or 6) / 2)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", str(p), "-frames:v", "1", str(tmp)])
            if not tmp.exists():
                continue
            im = Image.open(tmp).convert("RGBA"); tmp.unlink()
        else:
            continue
        cells.append((im, r))
    if not cells:
        return
    W, H, cols = 360, 300, 4
    sheet = Image.new("RGB", (W * cols, H * ((len(cells) + cols - 1) // cols)), (243, 233, 216))
    d = ImageDraw.Draw(sheet)
    for i, (im, r) in enumerate(cells):
        x, y = (i % cols) * W, (i // cols) * H
        # checker behind transparent logos so the alpha is visible
        for cx in range(0, W - 20, 20):
            for cy in range(0, H - 70, 20):
                if (cx // 20 + cy // 20) % 2:
                    d.rectangle([x + 10 + cx, y + 10 + cy, x + 30 + cx, y + 30 + cy], fill=(232, 222, 205))
        im.thumbnail((W - 20, H - 80))
        sheet.paste(im, (x + 10 + (W - 20 - im.width) // 2, y + 10 + (H - 80 - im.height) // 2), im)
        col = (40, 120, 40) if r["free"] else (190, 40, 40)
        d.text((x + 10, y + H - 64), Path(r["file"]).name[:44], fill=(30, 30, 30))
        d.text((x + 10, y + H - 46), (("FREE " if r["free"] else "FLAG ") + r["license"])[:48], fill=col)
        d.text((x + 10, y + H - 28), r["author"][:48], fill=(80, 80, 80))
    sheet.save(out / "contact_sheet.png")


def main() -> None:
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    opt = lambda k, dflt=None: a[a.index(k) + 1] if k in a else dflt
    n, width, base = int(opt("--n", 3)), min(2000, int(opt("--width", 1600))), opt("--name")
    mode = a[0]
    if mode == "clip":
        src, start, dur, dst = Path(a[1]), a[2], a[3], Path(a[4])
        cw, cf, look = int(opt("--width", 960)), int(opt("--fps", 30)), opt("--look")
        if look:
            cmd_treat(src, dst, opt("--palette") or sys.exit("clip --look needs --palette <slug>"), look, cw, cf, start, dur)
            return
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", start, "-i", str(src), "-t", dur, "-an", "-vf",
                        f"scale={cw}:-2:flags=lanczos,fps={cf}", "-c:v", "libx264", "-crf", "18", "-g", str(cf), "-pix_fmt", "yuv420p", str(dst)], check=True)
        copy_credit(src, dst, title_cut=f"{start}s+{dur}s")
        print(dst); return
    if mode == "scan":
        cmd_scan(Path(a[1]), Path(a[2]), float(opt("--every", 6)), int(opt("--cols", 5))); return
    if mode == "treat":
        cmd_treat(Path(a[1]), Path(a[2]), opt("--palette") or sys.exit("treat needs --palette <slug>"),
                  opt("--look", "duotone"), int(opt("--width", 960)), int(opt("--fps", 30))); return
    if mode == "used":
        out, html = Path(a[1]), Path(a[2]).read_text()
        rows = [r for r in load_credits(out) if Path(r["file"]).name in html]
        lines = [f'{r["subject"]}: "{r["title"]}" by {r["author"]}, {r["license"]} — {r["source_url"]}' for r in rows if r["free"]]
        bad = [r["file"] for r in rows if not r["free"]]
        notes = sorted({r["notice"] for r in rows if r.get("notice")})
        if notes:
            txt_extra = "\n".join(notes) + "\n"
        risky = [f'{r["file"]}: {r["content_id_note"]}' for r in rows if r.get("content_id_note")]
        txt = "Media credits:\n" + "\n".join(lines) + "\nLogos are trademarks of their owners; shown for identification/commentary only.\n"
        if notes:
            txt += txt_extra
        (out / "CREDITS_USED.md").write_text(txt); print(txt)
        for x in risky:
            print("!! Content ID / licence note:", x)
        if bad:
            print("!! NON-FREE files used (human decision needed):", bad)
        return
    if mode == "sheet":
        contact_sheet(Path(a[1])); print(Path(a[1]) / "contact_sheet.png"); return
    query, out = a[1], Path(a[2])
    out.mkdir(parents=True, exist_ok=True)
    if mode == "logo":
        cmd_logo(query, out, width, base)
    elif mode == "image":
        cmd_logo(query, out, width, base, prop="P18", kind="photo")
    elif mode == "file":
        cmd_file(query, out, width, base)
    elif mode == "commons":
        cmd_commons(query, out, n, width, base)
    elif mode == "archive":
        cmd_archive(query, out, n, "--video" in a, base, vetted="--vetted" in a, hd="--hd" in a)
    elif mode == "commons-video":
        cmd_commons_video(query, out, n, base, int(opt("--min-w", 640)), float(opt("--max-sec", 90)))
    elif mode == "nasa-video":
        cmd_nasa_video(query, out, n, base)
    elif mode == "dvids":
        cmd_dvids(query, out)
    elif mode == "pexels":
        cmd_pexels(query, out, n, "--video" in a, base)
    elif mode == "pixabay":
        cmd_pixabay(query, out, n, "--video" in a, base)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
