#!/usr/bin/env python3
"""fal.ai ElevenLabs TTS with word timestamps. Usage: python3 fal_tts.py <text_file> <out.mp3> [voice] [prev_text_file] [next_text_file]"""
import json, os, sys, time, pathlib, httpx
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); from envload import get_key
KEY = get_key("FAL_API_KEY")
H = {"Authorization": "Key " + KEY}
EP = "fal-ai/elevenlabs/tts/multilingual-v2"
text = pathlib.Path(sys.argv[1]).read_text().strip()
out = pathlib.Path(sys.argv[2]); voice = sys.argv[3] if len(sys.argv) > 3 else "Rachel"
inp = {"text": text, "voice": voice, "stability": 0.55, "similarity_boost": 0.75, "style": 0.0, "speed": float(os.environ.get("TTS_SPEED", "1.0")), "timestamps": True}
if len(sys.argv) > 4 and sys.argv[4] != "-": inp["previous_text"] = pathlib.Path(sys.argv[4]).read_text().strip()[-1000:]
if len(sys.argv) > 5: inp["next_text"] = pathlib.Path(sys.argv[5]).read_text().strip()[:1000]
t0 = time.time()
r = httpx.post(f"https://queue.fal.run/{EP}", headers=H, json=inp, timeout=60); r.raise_for_status(); q = r.json()
while True:
    s = httpx.get(q["status_url"], headers=H, timeout=30).json()
    if s.get("status") == "COMPLETED": break
    if s.get("status") not in ("IN_QUEUE", "IN_PROGRESS"): raise SystemExit(f"fal status {s}")
    time.sleep(2)
res = httpx.get(q["response_url"], headers=H, timeout=60).json()
audio = httpx.get(res["audio"]["url"], timeout=120).content
out.write_bytes(audio)
ts = res.get("timestamps")
json.dump(ts, open(out.with_suffix(".fal_ts.json"), "w"))
print(f"{out} {len(text)} chars, {time.time()-t0:.1f}s, timestamps type={type(ts).__name__} sample={str(ts)[:200]}")
