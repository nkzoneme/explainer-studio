#!/usr/bin/env python3
"""Analyze a YouTube video (URL) or a local .mp4 file with a Gemini model via OpenRouter.
Usage: python3 gemini_video.py <youtube_url> <out.md> [model] [prompt_file]"""
import base64, json, pathlib, sys, time, httpx
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1])); from envload import get_key
KEY = get_key("OPENROUTER_API_KEY")
url, out = sys.argv[1], pathlib.Path(sys.argv[2])
model = sys.argv[3] if len(sys.argv) > 3 else "google/gemini-3.5-flash-lite"
prompt = pathlib.Path(sys.argv[4]).read_text() if len(sys.argv) > 4 else open(pathlib.Path(__file__).with_name("video_analysis_prompt.md")).read()
if not url.startswith("http"):
    url = "data:video/mp4;base64," + base64.b64encode(pathlib.Path(url).read_bytes()).decode()
t0 = time.time()
r = httpx.post("https://openrouter.ai/api/v1/chat/completions", timeout=600,
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "X-Title": "explainer-research"},
    json={"model": model, "messages": [{"role": "user", "content": [
        {"type": "video_url", "video_url": {"url": url}},
        {"type": "text", "text": prompt}]}], "usage": {"include": True}})
d = r.json()
if r.status_code != 200 or "choices" not in d:
    raise SystemExit(f"error {r.status_code}: {json.dumps(d)[:600]}")
u = d.get("usage", {})
out.write_text(d["choices"][0]["message"]["content"])
print(f"{out}: {time.time()-t0:.0f}s, prompt_tokens={u.get('prompt_tokens')}, completion_tokens={u.get('completion_tokens')}, cost=${u.get('cost')}")
