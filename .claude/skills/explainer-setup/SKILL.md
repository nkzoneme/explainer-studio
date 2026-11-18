---
name: explainer-setup
description: Install and configure Explainer Studio on a new machine, or add API keys, or create a new channel — runs setup.sh, writes .env from keys the user pastes (never echoing them), verifies tools and keys with check_setup.py, and scaffolds explainer/channels/<slug>. Use when the user says setup, install, "here is my key", "add my FAL/KIE/OpenRouter/Pexels/Pixabay key", "it says KEY is not set", "make a new channel", or on the first session in a fresh clone (no .env or no .venv).
---

# Explainer Studio setup

Everything runs from the repo root. Five keys, all optional except FAL for voice:

| Key | Used by | Without it |
|---|---|---|
| `FAL_API_KEY` | `explainer/fal_tts.py` (ElevenLabs voice + word timestamps), AI SFX | no voice: nothing can be produced |
| `KIE_API_KEY` | `explainer/kie.py` (generated props/scenes) | use real media and hand-built SVG only |
| `OPENROUTER_API_KEY` | `research_flow/gemini_video.py` (competitor video reads) | channel style built from metrics and contact sheets only |
| `PEXELS_API_KEY`, `PIXABAY_API_KEY` | `kit/tools/fetch_media.py` stock | Wikimedia, NASA, Archive.org still work (no key) |

Scripts find keys in this order: process environment → `<repo>/.env` → `explainer/.env` (`explainer/envload.py`).

## 1. First run

1. Is this a fresh clone? `ls .env .venv` and `python3 explainer/check_setup.py --offline`.
2. Install: run `./setup.sh` (from Claude it runs without a TTY, so it installs and checks but skips the key prompts) and read its output. Missing system tools: give the user the printed install command (it needs sudo; they run it with `! <command>`).
3. Keys, pick the path that fits:
   - **The user pastes keys in chat.** Write them to a temp file in the scratchpad with a heredoc (`umask 077`), run `./setup.sh --skip-install --keys <file>`, then delete the file. Never echo a key, never put one in a command line argument, a commit, a log or a memory file. Reply with key names only.
   - **The keys are already exported in the user's shell**: `./setup.sh --skip-install --from-env`.
   - **The user prefers to type them**: tell them to run `! ./setup.sh --skip-install` (interactive, hidden input).
   - Never `cat .env`, never `grep` it with output, never print `get_key(...)`.
4. `python3 explainer/check_setup.py` (tests OpenRouter, kie, Pexels, Pixabay against free endpoints; FAL is only checked for presence: the first voice call, about 0.05 USD, proves it; a missing FAL key is a FAIL and the script exits 1, because nothing can be voiced without it). Report the table without values.
5. Activate for later commands: prefix Python with `.venv/bin/python` or `source .venv/bin/activate` in the same command.

## 2. New channel

1. `./setup.sh --new-channel <slug> "<Channel Name>"` → `explainer/channels/<slug>/` (STYLE.md, style.json, LEARNINGS.md, trend_sources.json), `explainer/shorts/styles/<slug>.json` (brand), `explainer/brand/<slug>/`, `explainer/kit/music/<slug>/`.
2. Ask the user only what the files cannot know: niche (one line), language/market (default US/UK English), voice (ElevenLabs name, or a voice ID), host or no host, 3–8 competitor channels if they have them.
3. Brand json: fill palette, `font_display` (any installed font; `fc-list` to see), `voice`, `thumb_look`. Avatar and host images are optional; with no host leave `host_poses` `{}`.
4. Run skill `explainer-channel-style` for STYLE.md/style.json, then draft `trend_sources.json` (queries, feeds, subreddits, familiar entities) and show it.
5. Music beds: put 2–4 licensed tracks in `explainer/kit/music/<slug>/` (Kevin MacLeod / incompetech, Scott Buckley: CC BY 4.0 with credit in the description; YouTube Audio Library). Record title, author, licence, URL in `kit/music/<slug>/CREDITS.md`.
6. Optional richer SFX: any role-levelled library you have the rights to, in `explainer/kit/sfx_v2/` (format in `kit/kit.js`, "SOUND MODES"). Without it the kit uses the CC0 sounds in `kit/sfx/`.

Then the daily work is skill `explainer-flow`.

## 3. Uploading

There is no YouTube API uploader. Uploads go through the Playwright MCP browser signed in to YouTube Studio (the user signs in once by hand). Never upload, schedule or publish without the user's OK for that item. The steps are in `explainer-shorts` → "Upload and scheduling notes".

## Troubleshooting

| Symptom | Fix |
|---|---|
| `X_API_KEY is not set` | Section 1 step 3 |
| `font not found` | install the font, or set `font_display_file` to a .ttf path |
| `npx hyperframes` hangs first time | it downloads Chromium once; wait, or check the network |
| `fc-match` missing | install fontconfig |
| Thumbnail cut-out falls back to GrabCut | `WITH_REMBG=1 ./setup.sh` |
