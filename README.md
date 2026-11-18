# Explainer Studio

> 🇻🇳 Hướng dẫn tiếng Việt đầy đủ: [HUONG_DAN.md](HUONG_DAN.md)

Claude Code skills and tools for making cartoon-explainer YouTube videos (10–15 min long videos plus vertical Shorts):

**topic research → script + fact-check → ElevenLabs voice with word timings → hand-directed HyperFrames/GSAP chapters (talking host, SFX, real media) → automatic QA → −14 LUFS master → native 1080×1920 Shorts → upload pack**

Claude does the work. You approve at five gates (topic, script, hook, final cut, publish).

---

## 1. What you need

| | Version | Why |
|---|---|---|
| [Claude Code](https://docs.claude.com/en/docs/claude-code) | latest | runs the skills and agents |
| Python | 3.10+ | tools |
| Node.js + npm | 18+ | HyperFrames renderer (`npx hyperframes@0.9.46`, downloads Chromium on first run) |
| ffmpeg + ffprobe | 6+ | render, mix, master, QA |
| fontconfig (`fc-match`) | any | finds the channel font |
| tesseract | optional | thumbnail OCR checks |
| git, bash | any | |

Install the system part:

```bash
# Ubuntu / Debian
sudo apt-get install -y python3 python3-venv nodejs npm ffmpeg fontconfig fonts-noto tesseract-ocr git
# Arch
sudo pacman -S --needed python nodejs npm ffmpeg fontconfig noto-fonts tesseract tesseract-data-eng git
# macOS (Homebrew)
brew install python node ffmpeg fontconfig tesseract git && brew install --cask font-noto-sans
```

Windows: use WSL2 (Ubuntu) and follow the Ubuntu line.

## 2. API keys

| Key | Service | Needed for | Cost |
|---|---|---|---|
| `FAL_API_KEY` | [fal.ai](https://fal.ai/dashboard/keys) | voice (ElevenLabs via fal, with word timestamps) | **required**, about 0.05 USD per Short voice, about 1–2 USD per long video |
| `KIE_API_KEY` | [kie.ai](https://kie.ai/api-key) | generated props and scenes | optional, about 0.03 USD per image |
| `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai/keys) | Gemini reads of competitor videos (channel style, research) | optional, cents per video |
| `PEXELS_API_KEY` | [pexels.com/api](https://www.pexels.com/api/) | stock photos and footage | free |
| `PIXABAY_API_KEY` | [pixabay.com/api/docs](https://pixabay.com/api/docs/) | stock photos and footage | free |

Without a key, its feature is off and the rest still works. Wikimedia Commons, NASA and Internet Archive media need no key.

## 3. Install

```bash
git clone https://github.com/<owner>/explainer-studio.git
cd explainer-studio
./setup.sh
```

`setup.sh`:
1. checks system tools and prints the install command for anything missing;
2. creates `.venv` and installs `requirements.txt`;
3. caches the HyperFrames renderer;
4. asks for each API key with hidden input and writes `.env` (chmod 600, gitignored);
5. runs `explainer/check_setup.py`, which tests each key against a free endpoint and never prints it.

Other ways to give keys (no prompts):

```bash
./setup.sh --from-env                 # keys already exported in your shell
./setup.sh --keys ~/secrets/team.env  # a file with KEY=value lines
cp .env.example .env && $EDITOR .env  # by hand, then: ./setup.sh --skip-install
```

Or let Claude do it: run `claude` in the repo and say **"setup"** (skill `explainer-setup`). You can paste keys into the chat. Claude writes them to `.env` and never echoes them.

Re-check any time:

```bash
.venv/bin/python explainer/check_setup.py
```

### Demo (all keys, about 2 min, about 0.05 USD)

```bash
./demo.sh            # optional voice name: ./demo.sh Adam
```

It builds a 25 s Short ("Your pencil has no lead in it") from nothing:
- FAL voice with word timings;
- a Pexels photo (Wikimedia Commons without a key);
- a KIE cartoon prop (skipped without a key);
- HyperFrames render, −14 LUFS master and QA.

Output: `explainer/film/demo/shorts/short_1.mp4` and `short_1_contact.jpg`. Re-runs reuse the cached voice and images, so they cost nothing.

## 4. Your first channel

```bash
./setup.sh --new-channel my_channel "My Channel"
```

This creates the following (all gitignored, so your channel stays on your machine):
- `explainer/channels/my_channel/`: STYLE.md, style.json, LEARNINGS.md, trend_sources.json;
- `explainer/shorts/styles/my_channel.json`: palette, font, voice, avatar, host;
- `explainer/brand/my_channel/` and `explainer/kit/music/my_channel/`.

Then in Claude Code:

1. **"build the channel style for my_channel"**: measures 5–12 competitor channels and writes the style (skill `explainer-channel-style`). Give it competitor channels if you have them.
2. **"draft trend sources for my_channel"**: news queries, feeds, subreddits, familiar entities.
3. Edit `explainer/shorts/styles/my_channel.json`:
   - `voice` is an ElevenLabs voice name or voice ID.
   - Set the colours and `font_display` (any installed font, see `fc-list`).
   - `avatar` and the host are optional: with no host, leave `host_poses` as `{}`.
4. Add 2–4 licensed music beds to `explainer/kit/music/my_channel/` and list their credits in a `CREDITS.md` there. Kevin MacLeod and Scott Buckley (CC BY 4.0) work, and so does the YouTube Audio Library.

## 5. Daily use

| Say to Claude | Skill |
|---|---|
| "plan the next video for my_channel" / "run the trend radar" | `explainer-flow`, `explainer-research` |
| "write the script", "voice chapter 1", "direct chapter 2" | `explainer-direct` |
| "make the Short for <video>" | `explainer-shorts` |
| "status of <video>", "48 h review" | `explainer-flow` |

Agents used by the skills: `explainer-writer` (Opus: script, hook, chapter 1, final review), `explainer-worker` (Sonnet: most production), `explainer-scout` (Haiku: data pulls).

Default budget: 10 USD or less per video, including its Short. Claude reports what it spent.

**Uploading.** There is no YouTube API uploader. Claude uploads through the Playwright MCP browser after you sign in to YouTube Studio once by hand, and it never uploads, schedules or publishes without your OK for that item. Install the plugin with `/plugin` → `playwright`.

## 6. Repo layout

```
setup.sh  .env.example  requirements.txt  CLAUDE.md
.claude/skills/   explainer-setup, explainer-flow, explainer-research, explainer-channel-style, explainer-direct, explainer-shorts
.claude/agents/   explainer-writer, explainer-worker, explainer-scout
explainer/
  envload.py        key loader: environment → ./.env → explainer/.env
  check_setup.py    tools + key check
  fal_tts.py        voice;  kie.py  image generation
  kit/              kit.js / kit.css (HyperFrames craft kit), CRAFT_RULES.md, REVIEW_PASS.md, VISUAL_SOURCES.md, sfx/ (CC0), tools/ (QA, script lint, review sheets, master, media fetch, thumbnails)
  shorts/           native/ (vertical Short scaffold, shorts.js/css, finish_short.sh), pick_segments.py, make_short.py, styles/_example.json
  research_flow/    trend_radar.py, channel_style_scan.py, gemini_video.py, topic_gap.py, prompts, STORY_SHAPES.md (treatments, Story card, cold read), REFERENCE_REPOS.md
  research/         made per video on your machine (SOURCES, CLAIMS, FACTCHECK, SCRIPT); gitignored, not shipped
  channels/         README.md (style.json schema) and _template/
```

`.gitignore` keeps everything a team produces local: `.env`, `.venv`, `explainer/film`, `vo`, `brand`, `kit/music`, real channel folders and brand files.

## 7. Sound

`explainer/kit/sfx/` ships CC0 sound effects (credits in `kit/sfx/CREDITS.md`) and works out of the box (the kit's "legacy" sound mode).

For the richer "edit" sound mode, put a role-levelled library you have the rights to in `explainer/kit/sfx_v2/` (`index.js` format described in `kit/kit.js`, "SOUND MODES"). Free sources with commercial-use licences include Kenney, freesound CC0 and the Sonniss GDC bundles. Do not commit a library whose licence forbids redistribution: `.gitignore` already excludes `kit/sfx_v2/raw` and `std`.

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `X_API_KEY is not set` | `./setup.sh --skip-install` (or say "setup" to Claude) |
| `check_setup.py` shows `FAIL` on a key | key revoked or mistyped: create a new one and re-run setup |
| `font not found` | install the font, or put a .ttf path in `font_display_file` |
| first `npx hyperframes` is slow | it downloads Chromium once |
| thumbnail cut-out falls back to GrabCut | `WITH_REMBG=1 ./setup.sh` |
| `ModuleNotFoundError` | use `.venv/bin/python`, or `source .venv/bin/activate` first |

---

## Tiếng Việt

Xem [HUONG_DAN.md](HUONG_DAN.md): cài đặt, lấy key, chạy demo, làm kênh thật, upload, bảo mật, xử lý lỗi.
