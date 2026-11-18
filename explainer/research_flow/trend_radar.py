#!/usr/bin/env python3
"""Trend radar: what is moving this week in one channel's niche, from free sources only (no keys).

Usage (from explainer/research_flow/):
  .venv/bin/python trend_radar.py <slug> [--date YYYY-MM-DD] [--top 25] [--yt-check 12] [--outliers 6] [--no-youtube] [--reuse-items]

Reads   explainer/channels/<slug>/trend_sources.json
Writes  explainer/channels/<slug>/trends/<date>.json and <date>.md

Sources (each one is optional; a failure is logged in the report's "Sources" table and the run goes on):
  Google News RSS search (per query, last N days)    news.google.com/rss/search
  Google Trends daily RSS (US, GB), niche-filtered    trends.google.com/trending/rss
  Official / trade RSS and Atom feeds                 trend_sources.json "feeds"
  CISA KEV catalogue additions (security niches)           trend_sources.json "cisa_kev"
  Reddit top of week / month (JSON, falls back to RSS rank when JSON is refused)
  Hacker News via the Algolia API (points, comments)
  YouTube search result pages (this month, sorted by views): views, age, velocity = views/day
  YouTube search-suggest (suggestqueries.google.com, client=youtube): phrasing people type

Stories: items from all sources are merged into clusters by TF-IDF cosine on title words (same event = one
cluster). Each cluster gets momentum signals, named entities (familiar ones pass topic gate 1), a lane hint
(hot = first seen < 10 days ago) and, for the top clusters, a YouTube competitor check (who already covered it,
how well, how fast). Momentum is a relative 0-100 index inside one run, not comparable across runs.

Politeness: generic User-Agent, no cookies, one request at a time, at least 1.2 s between requests to the same
host, one retry. Nothing personal is sent. Never reads .env.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import json
import math
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # explainer/
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
CACHE = Path(__file__).with_name("cache"); CACHE.mkdir(exist_ok=True)
NOW = dt.datetime.now(dt.timezone.utc)
STATUS: dict[str, dict] = {}                          # source -> {ok, fail, items, note}
_last_hit: dict[str, float] = {}

STOP = set("""a an the and or of to in on for at by with from as is are was were be been it its this that these those
into over after before about than then but not no new news says say said will would could can may might how why what
who when where which while more most up out off just now amid via vs v his her their our your you we they he she them
first one two three four five six seven eight nine ten year years day days week weeks month months report reports
update updates live latest today watch video exclusive breaking here there all some any has have had get gets got
inc ltd co plc us uk per amid amidst against under use used using also back down set big top make makes made""".split())


# ---------------------------------------------------------------- HTTP

def fetch(url: str, *, source: str, timeout: int = 20, accept: str = "*/*") -> bytes | None:
    host = urllib.parse.urlparse(url).netloc
    for attempt in range(2):
        wait = 1.2 - (time.time() - _last_hit.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        _last_hit[host] = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept, "Accept-Language": "en-US,en;q=0.8"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            note = f"HTTP {e.code}"
            if e.code in (401, 403, 404, 410):
                break
        except Exception as e:  # timeouts, DNS, TLS
            note = type(e).__name__
        time.sleep(3)
    s = STATUS.setdefault(source, {"ok": 0, "fail": 0, "items": 0, "note": ""})
    s["fail"] += 1
    s["note"] = (s["note"] + f"; {note}" if note not in s["note"] else s["note"]).strip("; ")
    return None


def st(source: str) -> dict:
    return STATUS.setdefault(source, {"ok": 0, "fail": 0, "items": 0, "note": ""})


def ok(source: str, n_items: int) -> None:
    s = st(source)
    s["ok"] += 1
    s["items"] += n_items


# ---------------------------------------------------------------- parsing helpers

def parse_date(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def parse_feed(raw: bytes) -> list[dict]:
    """RSS 2.0 or Atom -> [{title, url, published, extra}]"""
    out = []
    root = ET.fromstring(raw)
    for el in root.iter():
        if strip_ns(el.tag) not in ("item", "entry"):
            continue
        d: dict = {"extra": {}}
        for ch in el:
            t = strip_ns(ch.tag)
            if t == "title":
                d["title"] = (ch.text or "").strip()
            elif t == "link":
                d.setdefault("url", (ch.get("href") or ch.text or "").strip())
            elif t in ("pubDate", "published", "updated", "date") and "published" not in d:
                d["published"] = parse_date(ch.text)
            elif t == "source":
                d["extra"]["publisher"] = (ch.text or "").strip()
            elif t == "approx_traffic":
                d["extra"]["traffic"] = (ch.text or "").strip()
            elif t == "news_item":
                d["extra"].setdefault("news", []).append(
                    {strip_ns(x.tag): (x.text or "").strip() for x in ch if strip_ns(x.tag) in ("news_item_title", "news_item_url", "news_item_source")})
        if d.get("title"):
            out.append(d)
    return out


def words(text: str) -> list[str]:
    toks = re.findall(r"[a-z0-9][a-z0-9$&'.\-]*[a-z0-9]|[a-z0-9]", text.lower())
    out = []
    for t in toks:
        t = t.strip(".'-")
        if t.endswith("'s"):
            t = t[:-2]
        if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        if t and t not in STOP and not (t.isdigit() and len(t) < 3):
            out.append(t)
    return out


def ent_regex(name: str) -> re.Pattern:
    flags = re.I if (" " in name or not any(c.isupper() for c in name)) else 0
    return re.compile(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", flags)


# ---------------------------------------------------------------- collectors

def item(source: str, title: str, url: str, published, kind: str, **extra) -> dict:
    return {"source": source, "kind": kind, "title": re.sub(r"\s+", " ", title).strip(), "url": url,
            "published": published.isoformat() if isinstance(published, dt.datetime) else None, **extra}


def google_news(cfg: dict) -> list[dict]:
    gn = cfg.get("google_news") or {}
    days = gn.get("window_days", 30)
    out = []
    for q in gn.get("queries", []):
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
            {"q": f"{q} when:{days}d", "hl": "en-US", "gl": "US", "ceid": "US:en"})
        raw = fetch(url, source="google_news")
        if raw is None:
            continue
        try:
            rows = parse_feed(raw)
        except ET.ParseError:
            st("google_news")["note"] = "bad XML"; continue
        for r in rows:
            title, pub = r["title"], r["extra"].get("publisher", "")
            if pub and title.endswith(" - " + pub):
                title = title[: -len(pub) - 3]
            out.append(item("google_news", title, r.get("url", ""), r.get("published"), "news", publisher=pub, query=q))
        ok("google_news", len(rows))
    return out


def google_trends(cfg: dict, niche_re: list[re.Pattern]) -> tuple[list[dict], list[dict]]:
    """Daily trending searches; returns (niche-matching items, all trends for the record)."""
    out, allt = [], []
    for geo in cfg.get("google_trends_geos", []):
        raw = fetch(f"https://trends.google.com/trending/rss?geo={geo}", source="google_trends")
        if raw is None:
            continue
        try:
            rows = parse_feed(raw)
        except ET.ParseError:
            continue
        ok("google_trends", len(rows))
        for r in rows:
            news = r["extra"].get("news", [])
            blob = r["title"] + " " + " ".join(n.get("news_item_title", "") for n in news)
            allt.append({"geo": geo, "query": r["title"], "traffic": r["extra"].get("traffic")})
            if any(p.search(blob) for p in niche_re):
                head = news[0] if news else {}
                out.append(item("google_trends", f'{r["title"]} :: {head.get("news_item_title", "")}', head.get("news_item_url", ""),
                                r.get("published"), "search", geo=geo, traffic=r["extra"].get("traffic")))
    return out, allt


def feeds(cfg: dict, days: int) -> list[dict]:
    out = []
    for f in cfg.get("feeds", []):
        raw = fetch(f["url"], source="feeds", timeout=25)
        if raw is None:
            st("feeds").setdefault("failed", []).append(f["name"])
            continue
        try:
            rows = parse_feed(raw)
        except ET.ParseError:
            st("feeds").setdefault("failed", []).append(f["name"] + " (bad XML)")
            continue
        n = 0
        for r in rows:
            p = r.get("published")
            if p and (NOW - p).days > days:
                continue
            out.append(item("feed", r["title"], r.get("url", ""), p, f.get("kind", "trade"), publisher=f["name"]))
            n += 1
        ok("feeds", n)
    return out


def cisa_kev(cfg: dict) -> list[dict]:
    k = cfg.get("cisa_kev")
    if not k:
        return []
    raw = fetch(k["url"], source="cisa_kev", timeout=40)
    if raw is None:
        return []
    out = []
    for v in json.loads(raw).get("vulnerabilities", []):
        d = parse_date(v.get("dateAdded") + "T00:00:00+00:00") if v.get("dateAdded") else None
        if d and (NOW - d).days <= k.get("days", 14):
            out.append(item("cisa_kev", f'{v.get("vendorProject")} {v.get("product")}: {v.get("vulnerabilityName")} ({v.get("cveID")}) exploited',
                            f'https://nvd.nist.gov/vuln/detail/{v.get("cveID")}', d, "official",
                            ransomware=v.get("knownRansomwareCampaignUse")))
    ok("cisa_kev", len(out))
    return out


def reddit(cfg: dict) -> list[dict]:
    rc = cfg.get("reddit") or {}
    out, json_ok = [], True
    for sub in rc.get("subs", []):
        for t in rc.get("windows", ["week"]):
            raw = fetch(f"https://www.reddit.com/r/{sub}/top.json?t={t}&limit=25", source="reddit_json") if json_ok else None
            json_ok = json_ok and raw is not None
            if raw is not None:
                kids = json.loads(raw).get("data", {}).get("children", [])
                for rank, c in enumerate(kids):
                    d = c["data"]
                    out.append(item("reddit", d.get("title", ""), "https://www.reddit.com" + d.get("permalink", ""),
                                    dt.datetime.fromtimestamp(d.get("created_utc", 0), dt.timezone.utc), "social",
                                    sub=sub, window=t, rank=rank + 1, score=d.get("score"), comments=d.get("num_comments")))
                ok("reddit_json", len(kids))
                continue
            raw = fetch(f"https://www.reddit.com/r/{sub}/top/.rss?t={t}&limit=25", source="reddit_rss", accept="application/atom+xml")
            if raw is None:
                continue
            try:
                rows = parse_feed(raw)
            except ET.ParseError:
                continue
            for rank, r in enumerate(rows):
                out.append(item("reddit", r["title"], r.get("url", ""), r.get("published"), "social",
                                sub=sub, window=t, rank=rank + 1, score=None))
            ok("reddit_rss", len(rows))
            time.sleep(5)   # reddit is strict (429 at ~1 request/s); be extra slow
    return out


def hacker_news(cfg: dict, days: int) -> list[dict]:
    hc = cfg.get("hacker_news") or {}
    since = int((NOW - dt.timedelta(days=days)).timestamp())
    out, seen = [], set()
    for q in hc.get("queries", []):
        url = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode(
            {"query": q, "tags": "story", "numericFilters": f"created_at_i>{since},points>{hc.get('min_points', 40)}", "hitsPerPage": 30})
        raw = fetch(url, source="hacker_news")
        if raw is None:
            continue
        hits = json.loads(raw).get("hits", [])
        for h in hits:
            if h["objectID"] in seen:
                continue
            seen.add(h["objectID"])
            out.append(item("hacker_news", h.get("title") or "", h.get("url") or f'https://news.ycombinator.com/item?id={h["objectID"]}',
                            parse_date(h.get("created_at")), "social", points=h.get("points"), comments=h.get("num_comments"),
                            hn=f'https://news.ycombinator.com/item?id={h["objectID"]}'))
        ok("hacker_news", len(hits))
    return out


def suggest(q: str) -> list[str]:
    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode({"client": "youtube", "ds": "yt", "q": q, "hl": "en", "gl": "us"})
    raw = fetch(url, source="yt_suggest")
    if raw is None:
        return []
    m = re.search(r"\((\[.*\])\)\s*$", raw.decode("utf-8", "replace"), re.S)
    try:
        res = [s[0] for s in json.loads(m.group(1))[1]] if m else []
    except (ValueError, IndexError):
        res = []
    ok("yt_suggest", len(res))
    return res


AGE = {"s": 1 / 86400, "sec": 1 / 86400, "second": 1 / 86400, "m": 1 / 1440, "min": 1 / 1440, "minute": 1 / 1440,
       "h": 1 / 24, "hour": 1 / 24, "d": 1, "day": 1, "w": 7, "week": 7, "mo": 30, "month": 30, "y": 365, "year": 365}


def rel_age_days(txt: str | None) -> float | None:
    if not txt:
        return None
    m = re.search(r"(\d+)\s*([a-z]+)", txt.lower().replace("streamed", ""))
    if not m:
        return None
    unit = m.group(2).rstrip("s") if m.group(2) not in ("s", "mo") else m.group(2)
    return int(m.group(1)) * AGE[unit] if unit in AGE else None


def yt_search(q: str, sp: str = "CAMSAggE") -> list[dict]:
    """YouTube results page. sp=CAMSAggE: uploaded this month, sorted by view count."""
    raw = fetch("https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": q, "sp": sp}), source="youtube_search")
    if raw is None:
        return []
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", raw.decode("utf-8", "replace"), re.S)
    if not m:
        st("youtube_search")["note"] = "no ytInitialData (consent page?)"; return []
    found = []

    def walk(o):
        if isinstance(o, dict):
            v = o.get("videoRenderer")
            if v:
                views = re.sub(r"\D", "", (v.get("viewCountText") or {}).get("simpleText") or "0") or "0"
                ln = (v.get("lengthText") or {}).get("simpleText") or ""
                secs = sum(int(x) * 60 ** i for i, x in enumerate(reversed(ln.split(":")))) if re.fullmatch(r"[\d:]+", ln) else 0
                owner = ((v.get("ownerText") or {}).get("runs") or [{}])[0]
                age = rel_age_days((v.get("publishedTimeText") or {}).get("simpleText"))
                found.append({"id": v.get("videoId"), "title": "".join(r.get("text", "") for r in (v.get("title") or {}).get("runs", [])),
                              "views": int(views), "age_days": round(age, 2) if age is not None else None, "seconds": secs,
                              "channel": owner.get("text"),
                              "channel_id": (owner.get("navigationEndpoint") or {}).get("browseEndpoint", {}).get("browseId"),
                              "velocity": round(int(views) / max(age or 1, 0.5)) if age is not None else None,
                              "url": f'https://www.youtube.com/watch?v={v.get("videoId")}'})
                return
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(json.loads(m.group(1)))
    ok("youtube_search", len(found))
    return found


def channel_median(cid: str, cache: dict) -> dict | None:
    """Median views of a channel's last 30 uploads (yt-dlp flat, ~5-15 s). Cached for 14 days."""
    c = cache.get(cid)
    if c and c.get("at") and (NOW - parse_date(c["at"])).days < 14:
        return c
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": "in_playlist", "skip_download": True, "playlistend": 30}) as y:
            d = y.extract_info(f"https://www.youtube.com/channel/{cid}/videos", download=False) or {}
        views = [e.get("view_count") or 0 for e in (d.get("entries") or [])[:30] if e]
        cache[cid] = {"median": int(statistics.median(views)) if views else 0, "subs": d.get("channel_follower_count"), "at": NOW.isoformat()}
        ok("yt_channel_median", 1)
        time.sleep(1.5)
        return cache[cid]
    except Exception as e:
        st("yt_channel_median")["fail"] += 1
        st("yt_channel_median")["note"] = type(e).__name__
        return None


# ---------------------------------------------------------------- clustering and scoring

def cluster(items: list[dict], threshold: float = 0.34, merge_threshold: float = 0.42) -> list[list[dict]]:
    docs = [Counter(words(i["title"])) for i in items]
    df = Counter(t for d in docs for t in d)
    n = len(docs)
    idf = {t: math.log((n + 1) / (c + 0.5)) for t, c in df.items()}
    vecs = []
    for d in docs:
        v = {t: c * idf[t] for t, c in d.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1
        vecs.append({t: x / norm for t, x in v.items()})
    order = sorted(range(n), key=lambda i: (items[i]["kind"] not in ("news", "official", "trade"), items[i]["published"] or ""), reverse=False)
    clusters: list[dict] = []          # {"members": [...], "centroid": {}, "index": {token: weight}}
    by_token: dict[str, set] = defaultdict(set)
    for i in order:
        v = vecs[i]
        if not v:
            continue
        cand = set()
        for t in sorted(v, key=v.get, reverse=True)[:6]:
            cand |= by_token[t]
        best, best_sim = None, 0.0
        for ci in cand:
            c = clusters[ci]["centroid"]
            sim = sum(w * c.get(t, 0) for t, w in v.items())
            if sim > best_sim:
                best, best_sim = ci, sim
        if best is not None and best_sim >= threshold:
            c = clusters[best]
            c["members"].append(i)
            k = len(c["members"])
            for t in set(c["centroid"]) | set(v):
                c["centroid"][t] = (c["centroid"].get(t, 0) * (k - 1) + v.get(t, 0)) / k
            norm = math.sqrt(sum(x * x for x in c["centroid"].values())) or 1
            c["centroid"] = {t: x / norm for t, x in c["centroid"].items() if x / norm > 0.02}
            for t in v:
                by_token[t].add(best)
        else:
            clusters.append({"members": [i], "centroid": dict(v)})
            for t in v:
                by_token[t].add(len(clusters) - 1)
    # second pass: merge clusters about the same event that were split by paraphrased headlines
    def cos(a, b):
        return sum(w * b.get(t, 0) for t, w in a.items())
    big = sorted(range(len(clusters)), key=lambda i: -len(clusters[i]["members"]))
    alive = [True] * len(clusters)
    for x in big:
        if not alive[x] or len(clusters[x]["members"]) < 2:
            continue
        for y in big:
            if y == x or not alive[y]:
                continue
            if cos(clusters[x]["centroid"], clusters[y]["centroid"]) >= merge_threshold:
                cx, cy = clusters[x], clusters[y]
                kx, ky = len(cx["members"]), len(cy["members"])
                cen = {t: (cx["centroid"].get(t, 0) * kx + cy["centroid"].get(t, 0) * ky) / (kx + ky) for t in set(cx["centroid"]) | set(cy["centroid"])}
                norm = math.sqrt(sum(v * v for v in cen.values())) or 1
                cx["centroid"] = {t: v / norm for t, v in cen.items() if v / norm > 0.02}
                cx["members"] += cy["members"]
                alive[y] = False
    clusters = [c for c, a in zip(clusters, alive) if a]
    for c in clusters:
        c["key_terms"] = [t for t, _ in sorted(c["centroid"].items(), key=lambda x: -x[1])[:6]]
    return [{"items": [items[i] for i in c["members"]], "key_terms": c["key_terms"]} for c in clusters]


def entities_in(text: str, ents: dict[str, list[re.Pattern]]) -> tuple[list[str], list[str]]:
    fam = [name for name, p in ents["familiar"] if p.search(text)]
    oth = [name for name, p in ents["other"] if p.search(text)]
    # drop shorter names covered by a longer match ("737" when "737 MAX" matched)
    fam = [f for f in fam if not any(f != g and f in g for g in fam)]
    return fam, oth


def summarize(c: dict, ents: dict) -> dict:
    its = c["items"]
    dates = sorted(parse_date(i["published"]) for i in its if i["published"])
    first, last = (dates[0], dates[-1]) if dates else (None, None)
    news = [i for i in its if i["kind"] in ("news", "trade", "official")]
    pubs7 = {i.get("publisher") or i["source"] for i in news if i["published"] and (NOW - parse_date(i["published"])).days < 7}
    pubs30 = {i.get("publisher") or i["source"] for i in news}
    fam, oth = Counter(), Counter()
    caps = Counter()
    for i in its:
        f, o = entities_in(i["title"], ents)
        fam.update(f); oth.update(o)
        caps.update(m for m in re.findall(r"\b[A-Z][a-zA-Z0-9&'\-]+(?:\s[A-Z][a-zA-Z0-9&'\-]+)*", i["title"]) if m.lower() not in STOP and len(m) > 2)
    reddit_pts = sum(1 / (1 + (i.get("rank") or 25) / 8) for i in its if i["source"] == "reddit")
    hn_pts = sum(i.get("points") or 0 for i in its if i["source"] == "hacker_news")
    trends = [i for i in its if i["source"] == "google_trends"]
    official = [i for i in its if i["kind"] == "official"]
    # label: the news title closest to the centroid terms, else the first title
    def label_score(i):
        return sum(t in words(i["title"]) for t in c["key_terms"]) - (len(i["title"]) > 110)
    label = max(news or its, key=label_score)["title"]
    age_first = (NOW - first).total_seconds() / 86400 if first else None
    return {
        "label": label, "key_terms": c["key_terms"],
        "first_seen": first.date().isoformat() if first else None, "latest": last.date().isoformat() if last else None,
        "age_days": round(age_first, 1) if age_first is not None else None,
        "hours_since_latest": round((NOW - last).total_seconds() / 3600, 1) if last else None,
        "n_items": len(its), "news_7d_outlets": len(pubs7), "news_30d_outlets": len(pubs30),
        "official_items": len(official), "reddit_signal": round(reddit_pts, 2),
        "reddit_posts": sum(i["source"] == "reddit" for i in its), "hn_points": hn_pts,
        "google_trends": [f'{i.get("geo")} {i.get("traffic")}' for i in trends],
        "familiar_entities": [e for e, _ in fam.most_common(6)], "other_entities": [e for e, _ in oth.most_common(6)],
        "names_in_titles": [e for e, n in caps.most_common(10) if n >= 2][:8],
        "lane_hint": ("hot" if age_first is not None and age_first < 10 else "evergreen-with-hook (old story, fresh news)" if len(pubs7) else "background"),
        "links": [{"source": i.get("publisher") or i["source"], "title": i["title"], "url": i["url"], "date": (i["published"] or "")[:10],
                   **({"points": i["points"]} if i.get("points") else {}), **({"hn": i["hn"]} if i.get("hn") else {})}
                  for i in sorted(its, key=lambda i: ({"official": 0, "news": 1, "trade": 1, "search": 2, "social": 3}.get(i["kind"], 4), -(len(i.get("publisher") or ""))))[:8]],
    }


def momentum(s: dict) -> float:
    rec = 1.0 if s["hours_since_latest"] is None else math.exp(-s["hours_since_latest"] / (24 * 10))
    raw = (10 * math.log1p(s["news_7d_outlets"]) + 4 * math.log1p(max(s["news_30d_outlets"] - s["news_7d_outlets"], 0))
           + 3 * math.log1p(s["official_items"]) + 6 * s["reddit_signal"] + 5 * math.log1p(s["hn_points"] / 50)
           + 8 * len(s["google_trends"]) + 4 * s.get("suggest_hits", 0) + 5 * math.log1p((s.get("yt", {}).get("velocity_sum") or 0) / 2000))
    return raw * (0.5 + 0.5 * rec)


def yt_check(s: dict, min_long: int, cache: dict, do_median: bool) -> dict:
    """Who already covered this story on YouTube this month, and how well."""
    lw = words(s["label"])
    terms = sorted([t for t in s["key_terms"][:5] if t in lw], key=lw.index)[:4] or s["key_terms"][:3]
    ent = s["familiar_entities"][:1] or s["other_entities"][:1]
    q = " ".join(ent + [t for t in terms if t not in words(" ".join(ent))])
    res = yt_search(q)
    key = set(s["key_terms"][:5]) | {w for e in s["familiar_entities"][:2] for w in words(e)}
    rel = [v for v in res if len(key & set(words(v["title"]))) >= 2]
    longs = [v for v in rel if v["seconds"] >= min_long]
    shorts = [v for v in rel if 0 < v["seconds"] < min_long]
    best = max(longs, key=lambda v: v["views"], default=None)
    if best and do_median and best.get("channel_id"):
        m = channel_median(best["channel_id"], cache)
        if m:
            best = dict(best, ch_median=m["median"], ch_subs=m["subs"], outlier=round(best["views"] / max(m["median"], 1000), 1))
    covered = "none"
    if best:
        covered = "strong" if best["views"] >= 100_000 else "medium" if best["views"] >= 20_000 else "weak"
    return {"query": q, "long_videos": len(longs), "shorts": len(shorts), "coverage": covered,
            "best_long": best, "velocity_sum": sum(v["velocity"] or 0 for v in rel),
            "fresh_14d_long": sum(1 for v in longs if (v["age_days"] or 99) <= 14),
            "top": sorted(rel, key=lambda v: -v["views"])[:4]}


# ---------------------------------------------------------------- report

def md_report(R: dict) -> str:
    L = [f'# Trend radar: {R["channel"]} — {R["date"]}', "",
         f'Generated by `research_flow/trend_radar.py` at {R["generated_utc"][:16]} UTC from free sources. Momentum is a 0-100 index relative to the top story of THIS run. '
         "Lane hint: hot = first item < 10 days old; evergreen-with-hook = older story with fresh coverage this week. "
         "YouTube coverage: strong = a long video >= 100k views this month, medium >= 20k, weak < 20k, none = no long video on the story found.", "",
         "## Sources", "", "| Source | Requests ok | Failed | Items | Note |", "|---|---|---|---|---|"]
    for k, v in sorted(R["sources"].items()):
        note = v.get("note", "") + ((" failed: " + ", ".join(v["failed"])) if v.get("failed") else "")
        L.append(f'| {k} | {v["ok"]} | {v["fail"]} | {v["items"]} | {note.strip()} |')
    L += ["", f'## Top {len(R["stories"])} stories', "",
          "| # | Momentum | Story | Lane | Age d | News outlets 7d/30d | Reddit / HN | Suggest | YT coverage (best long video) | Familiar entities |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for n, s in enumerate(R["stories"], 1):
        y = s.get("yt") or {}
        b = y.get("best_long")
        cov = f'{y.get("coverage", "n/a")}' + (f' ({b["views"]:,} v, {b["age_days"]} d, {b["channel"]})' if b else "")
        L.append(f'| {n} | {s["momentum"]} | {s["label"][:95]} | {s["lane_hint"].split(" ")[0]} | {s["age_days"]} | {s["news_7d_outlets"]}/{s["news_30d_outlets"]} | '
                 f'{s["reddit_posts"]} / {s["hn_points"]} | {s.get("suggest_hits", 0)} | {cov} | {", ".join(s["familiar_entities"][:4]) or "—"} |')
    L += ["", "## Story details", ""]
    for n, s in enumerate(R["stories"], 1):
        L += [f'### {n}. {s["label"]}', "",
              f'- Momentum {s["momentum"]}; first seen {s["first_seen"]}, latest {s["latest"]} ({s["hours_since_latest"]} h ago); lane hint: {s["lane_hint"]}',
              f'- Signals: {s["n_items"]} items; news outlets 7d {s["news_7d_outlets"]}, 30d {s["news_30d_outlets"]}; official {s["official_items"]}; '
              f'Reddit posts {s["reddit_posts"]}; HN points {s["hn_points"]}; Google Trends {", ".join(s["google_trends"]) or "no"}; '
              f'search-suggest hits {s.get("suggest_hits", 0)} {s.get("suggest_examples", [])[:3]}',
              f'- Entities: familiar {s["familiar_entities"] or "none (gate 1 fails as is)"}; other {s["other_entities"]}; names {s["names_in_titles"]}',
              f'- Key terms: {", ".join(s["key_terms"])}']
        y = s.get("yt")
        if y:
            L.append(f'- YouTube this month for "{y["query"]}": {y["long_videos"]} long, {y["shorts"]} Shorts on the story, {y["fresh_14d_long"]} long in the last 14 d; coverage **{y["coverage"]}**')
            for v in y["top"]:
                extra = f', channel median {v["ch_median"]:,}, x{v["outlier"]}' if v.get("ch_median") is not None else ""
                b = y.get("best_long") or {}
                if b.get("id") == v["id"] and b.get("ch_median") is not None:
                    extra = f', channel median {b["ch_median"]:,}, x{b["outlier"]}'
                L.append(f'  - [{v["title"][:90]}]({v["url"]}) — {v["channel"]}, {v["views"]:,} views, {v["age_days"]} d, {v["velocity"]:,}/day, {v["seconds"]//60} min{extra}')
        L.append("- Links:")
        for l in s["links"]:
            L.append(f'  - {l["date"]} {l["source"]}: [{l["title"][:110]}]({l["url"]})' + (f' (HN {l["points"]} pts)' if l.get("points") else ""))
        L.append("")
    L += ["## Niche YouTube this month (most viewed, long form)", "",
          "| Video | Channel | Views | Age d | Views/day | Channel median | Outlier |", "|---|---|---|---|---|---|---|"]
    for v in R["youtube_niche"]:
        L.append(f'| [{v["title"][:80]}]({v["url"]}) | {v["channel"]} | {v["views"]:,} | {v["age_days"]} | {v["velocity"]:,} | {v.get("ch_median", "")} | {v.get("outlier", "")} |')
    L += ["", "## Search-suggest phrasing (YouTube)", ""]
    for seed, sug in R["suggest"]["seeds"].items():
        new = set(R["suggest"]["new_since_last"].get(seed, []))
        L.append(f'- **{seed}**: ' + "; ".join(f"**{x}** (new)" if x in new else x for x in sug))
    if R["google_trends_all"]:
        L += ["", "## Google Trends today matching the niche", ""]
        L += [f'- {i["title"]} ({i.get("geo")}, {i.get("traffic")})' for i in R["google_trends_matched"]] or ["- none matched the niche terms"]
    L += ["", "Next step: explainer-research Stage 2 (trend radar → topic pick) gates and scores these stories; this file is evidence, not a pick.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--date", default=NOW.date().isoformat(), help="UTC date by default")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--yt-check", type=int, default=12, help="top N stories that get a YouTube coverage check")
    ap.add_argument("--outliers", type=int, default=6, help="channel-median lookups (yt-dlp) for the best videos")
    ap.add_argument("--no-youtube", action="store_true")
    ap.add_argument("--reuse-items", action="store_true", help="re-use today's fetched news/feeds/social items from cache/")
    a = ap.parse_args()

    chan = ROOT / "channels" / a.slug
    cfg = json.load(open(chan / "trend_sources.json"))
    out_dir = chan / "trends"; out_dir.mkdir(exist_ok=True)
    window = (cfg.get("google_news") or {}).get("window_days", 30)
    ents = {k: [(n, ent_regex(n)) for n in v] for k, v in cfg["entities"].items()}
    niche_re = [ent_regex(t) for t in cfg.get("niche_terms", [])]   # Google Trends filter: a niche word must appear
    cache_p = CACHE / "channel_medians.json"
    med_cache = json.load(open(cache_p)) if cache_p.exists() else {}

    t0 = time.time()
    log = lambda m: print(f"[{time.time() - t0:5.0f}s] {m}", file=sys.stderr, flush=True)
    raw_p = CACHE / f"items_{a.slug}_{a.date}.json"
    if a.reuse_items and raw_p.exists():          # re-cluster without fetching again (tuning, re-runs)
        saved = json.load(open(raw_p))
        items, tr, tr_all = saved["items"], saved["trends"], saved["trends_all"]
        STATUS.update(saved["status"])
        log(f"reused {len(items)} items from {raw_p.name}")
    else:
        items: list[dict] = []
        items += google_news(cfg); log(f"google news {len(items)}")
        tr, tr_all = google_trends(cfg, niche_re); items += tr; log(f"google trends {len(tr_all)} total, {len(tr)} niche")
        items += feeds(cfg, window); log("feeds")
        items += cisa_kev(cfg)
        items += reddit(cfg); log("reddit")
        items += hacker_news(cfg, window); log("hacker news")
        raw_p.write_text(json.dumps({"items": items, "trends": tr, "trends_all": tr_all, "status": STATUS}, default=str))

    # de-duplicate identical titles (syndication)
    seen, uniq = set(), []
    for i in items:
        k = re.sub(r"\W+", " ", i["title"].lower()).strip()[:90]
        if k and k not in seen:
            seen.add(k); uniq.append(i)
    clusters = cluster(uniq)
    stories = [summarize(c, ents) for c in clusters]
    stories = [s for s in stories if s["n_items"] >= 2 or s["google_trends"] or s["hn_points"] >= 150]
    for s in stories:
        s["momentum_raw"] = momentum(s)
    stories.sort(key=lambda s: -s["momentum_raw"])
    stories = stories[: max(a.top * 2, 40)]
    log(f"{len(uniq)} unique items -> {len(clusters)} clusters, {len(stories)} kept")

    # search-suggest: seeds (with diff against the last run) and presence of each top story
    prev = sorted(p for p in out_dir.glob("20*.json") if p.stem != a.date)
    prev_sug = json.load(open(prev[-1])).get("suggest", {}).get("seeds", {}) if prev else {}
    seeds = {sd: suggest(sd) for sd in cfg.get("suggest_seeds", [])}
    new_since = {sd: [x for x in v if prev_sug and x not in prev_sug.get(sd, [])] for sd, v in seeds.items()}
    flat = [x for v in seeds.values() for x in v]
    for s in stories[: a.top]:
        probe = (s["familiar_entities"] or s["other_entities"] or s["key_terms"])[0]
        sug = suggest(probe.lower())
        pool = flat + sug
        key = [t for t in s["key_terms"][:5] if t not in words(probe)]
        pw = set(words(probe))
        hits = [x for x in pool if sum(t in words(x) for t in key) >= 2 or (pw and pw <= set(words(x)) and sum(t in words(x) for t in key) >= 1)]
        s["suggest_hits"], s["suggest_examples"] = min(len(hits), 5), hits[:5]
    log("suggest")

    yt_niche = []
    if not a.no_youtube:
        for s in stories[: a.yt_check]:
            s["yt"] = yt_check(s, cfg["youtube"].get("min_long_s", 240), med_cache, do_median=False)
        log("youtube story checks")
        vids = {}
        for q in cfg["youtube"].get("queries", []):
            for v in yt_search(q):
                if v["seconds"] >= cfg["youtube"].get("min_long_s", 240):
                    vids[v["id"]] = v
        yt_niche = sorted(vids.values(), key=lambda v: -(v["velocity"] or 0))[:20]
        # outlier vs channel median for the fastest few and for the best covering video of the top stories
        budget = a.outliers
        for v in yt_niche[:budget]:
            if v.get("channel_id"):
                m = channel_median(v["channel_id"], med_cache)
                if m:
                    v.update(ch_median=m["median"], ch_subs=m["subs"], outlier=round(v["views"] / max(m["median"], 1000), 1))
        for s in stories[: min(a.yt_check, budget)]:
            b = (s.get("yt") or {}).get("best_long")
            if b and b.get("channel_id"):
                m = channel_median(b["channel_id"], med_cache)
                if m:
                    b.update(ch_median=m["median"], ch_subs=m["subs"], outlier=round(b["views"] / max(m["median"], 1000), 1))
        json.dump(med_cache, open(cache_p, "w"))
        log("youtube niche + medians")
    for s in stories:
        s["momentum_raw"] = momentum(s)
    stories.sort(key=lambda s: -s["momentum_raw"])
    stories = stories[: a.top]
    top = max((s["momentum_raw"] for s in stories), default=1) or 1
    for s in stories:
        s["momentum"] = round(100 * s.pop("momentum_raw") / top)

    R = {"channel": cfg["channel"], "slug": a.slug, "date": a.date, "generated_utc": NOW.isoformat(),
         "sources": STATUS, "stories": stories, "youtube_niche": yt_niche,
         "suggest": {"seeds": seeds, "new_since_last": new_since, "compared_with": prev[-1].name if prev else None},
         "google_trends_matched": tr, "google_trends_all": tr_all, "n_items": len(uniq)}
    (out_dir / f"{a.date}.json").write_text(json.dumps(R, indent=1, ensure_ascii=False, default=str))
    (out_dir / f"{a.date}.md").write_text(md_report(R))
    log(f"wrote {out_dir / (a.date + '.md')}")


if __name__ == "__main__":
    main()
