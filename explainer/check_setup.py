#!/usr/bin/env python3
"""Check tools and API keys. Prints OK/MISSING/FAIL per item, never a key value.
Usage: python3 explainer/check_setup.py [--offline]   (--offline: presence only, no network)"""
import importlib, shutil, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from envload import get_key

offline = "--offline" in sys.argv
bad = 0


def line(status, name, note=""):
    global bad
    if status == "FAIL": bad += 1
    print(f"{status:8} {name:22} {note}")


import os
os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")   # venv tools (yt-dlp, rembg)
print("== tools")
for c, need in [("python3", True), ("node", True), ("npx", True), ("ffmpeg", True), ("ffprobe", True),
                ("tesseract", False), ("fc-match", True), ("yt-dlp", False), ("rembg", False)]:
    line("OK" if shutil.which(c) else ("FAIL" if need else "MISSING"), c, "" if shutil.which(c) else ("required" if need else "optional"))
if shutil.which("node"):
    v = subprocess.run(["node", "-v"], capture_output=True, text=True).stdout.strip()
    line("OK" if int(v.lstrip("v").split(".")[0]) >= 18 else "FAIL", "node version", v)
print("== python packages")
for m in ("httpx", "requests", "numpy", "PIL", "cv2", "yt_dlp"):
    try: importlib.import_module(m); line("OK", m)
    except Exception: line("FAIL" if m in ("httpx", "numpy", "PIL") else "MISSING", m, "pip install -r requirements.txt")

print("== API keys")
import httpx
TESTS = {
    "OPENROUTER_API_KEY": lambda k: httpx.get("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {k}"}, timeout=20).status_code == 200,
    "KIE_API_KEY": lambda k: httpx.get("https://api.kie.ai/api/v1/chat/credit", headers={"Authorization": f"Bearer {k}"}, timeout=20).json().get("code") == 200,
    "PEXELS_API_KEY": lambda k: httpx.get("https://api.pexels.com/v1/search", params={"query": "sky", "per_page": 1}, headers={"Authorization": k}, timeout=20).status_code == 200,
    "PIXABAY_API_KEY": lambda k: httpx.get("https://pixabay.com/api/", params={"key": k, "q": "sky", "per_page": 3}, timeout=20).status_code == 200,
    "FAL_API_KEY": None,   # no free check endpoint; the first fal_tts.py call tests it (about 0.05 USD)
}
for name, test in TESTS.items():
    k = get_key(name, required=False)
    if not k: line("MISSING", name, "REQUIRED to produce videos (voice)" if name == "FAL_API_KEY" else "feature off (see .env.example)"); continue
    if offline or test is None: line("SET", name, "not tested" if test is None else "offline"); continue
    try: line("OK" if test(k) else "FAIL", name, "" )
    except Exception as e: line("FAIL", name, type(e).__name__)
sys.exit(1 if bad else 0)
