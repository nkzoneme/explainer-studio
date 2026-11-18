"""Find API keys without printing them.

Order: the process environment, then <repo>/.env, then explainer/.env.
Run ./setup.sh (or ask Claude: /explainer-setup) to create .env.
"""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent          # explainer/
ENV_FILES = [HERE.parent / ".env", HERE / ".env"]

HINT = {
    "FAL_API_KEY": "voice (ElevenLabs via fal.ai) - https://fal.ai/dashboard/keys",
    "KIE_API_KEY": "image generation (kie.ai) - https://kie.ai/api-key",
    "OPENROUTER_API_KEY": "Gemini video analysis via OpenRouter - https://openrouter.ai/keys",
    "PEXELS_API_KEY": "Pexels stock media - https://www.pexels.com/api/",
    "PIXABAY_API_KEY": "Pixabay stock media - https://pixabay.com/api/docs/",
}


def get_key(name: str, required: bool = True):
    if os.environ.get(name):
        return os.environ[name]
    for f in ENV_FILES:
        if f.exists():
            for line in f.read_text().splitlines():
                line = line.strip()
                if line.startswith(name + "="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    if required:
        raise SystemExit(f"{name} is not set ({HINT.get(name, 'see .env.example')}). "
                         f"Add it to {ENV_FILES[0]} or run ./setup.sh")
    return None
