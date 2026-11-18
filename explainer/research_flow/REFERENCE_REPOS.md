# Reference repos: what we studied and what we took

Study of 18/11/2026. Stars, last push and licence were read from the GitHub API that day; the files named were read through the API, nothing was cloned or run except the HyperFrames CLI we already use. **None of these repos shows retention or click-through data for its own output.** Their rules are their authors' beliefs: we adopt them as experiments (channel `LEARNINGS.md`, "Experiments"), not as facts.

Licence rule: MIT and Apache-2.0 code may be ported with its notice. A repo with no licence or `NOASSERTION` is read for ideas only. AGPL code is never copied into this repo.

## Worth reading

| Repo | Stars · pushed · licence | What it teaches | What we took |
|---|---|---|---|
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | 86k · 2026-11-18 · Apache-2.0 | Our renderer. `skills/hyperframes/references/`: `review.md` (review the render as a stranger, P0/P1/P2 notes, phone-width sheet), `story.md` (three storylines, device and form, tells of a generated film), `spec.md` (adjectives into numbers, a BANNED list that grows), `motion.md` (ease by role, seams with a cause), `types/explainer.md` (ground it first, one diagram that grows). `registry/`: about 450 blocks and components | `kit/REVIEW_PASS.md`, `research_flow/STORY_SHAPES.md` §1, `kit/CRAFT_RULES.md` §15–16, `kit/VISUAL_SOURCES.md` §1 |
| [BusyBee3333/animated-explainer-skills](https://github.com/BusyBee3333/animated-explainer-skills) | 32 · 2026-07-13 · MIT | GSAP explainers. `skills/retention-pass/SKILL.md`: the hook must open the loop the peak closes ("the cold open showed the trap while the packaging promised the peak"); say it = show it within 1.5 s; a scene's last content beat at 70–85 % of its length; `tools/beat-audit.mjs` | Story card "First 10 s" and "Peak" slots; `qa_review.py` `unanswered` |
| [browser-use/video-use](https://github.com/browser-use/video-use) | 31k · 2026-10-08 · MIT | Self-evaluation on the rendered output, then one critic sub-agent briefed "to roast, not to praise"; capped passes; "You cannot listen: say so, and report the numbers" | `kit/REVIEW_PASS.md` §5–6 |
| [OpenMontageInc/OpenMontage](https://github.com/OpenMontageInc/OpenMontage) | 81k · 2026-11-16 · AGPL-3.0 | Scene plan with `shot_intent`, `information_role`, `hero_moment`; a plan-level "slideshow risk" score (one scene type over 70 %, one shot size over 60 %); reviewer rule "every critical finding must carry a proposed fix"; two rounds at most | the beat plan's `why` and `hero` (explainer-direct Step 2); the note shape in `REVIEW_PASS.md` §4. Ideas only: AGPL |
| [prajwal-y/video_explainer](https://github.com/prajwal-y/video_explainer) | 254 · 2026-02-24 · no licence | Voice before storyboard; beats with `SyncPoint(trigger_word, trigger_seconds, target, action)`; narration principles (build tension before release, one insight per scene, strong scene endings) | confirms our voice-first flow; rules E5, E7, E8 in `STORY_SHAPES.md`. Ideas only |
| [showlab/Code2Video](https://github.com/showlab/Code2Video), [TIGER-AI-Lab/TheoremExplainAgent](https://github.com/TIGER-AI-Lab/TheoremExplainAgent) | 2.4k · MIT; 1.5k · MIT | A vision model critiques rendered frames with a fixed rubric and must name the object and the fix; a text-only judge kept apart from the frame judge so pretty frames cannot hide a weak script | the cold read (text only) kept apart from the picture review |
| [Alisa0808/vox-director](https://github.com/Alisa0808/vox-director) | 2.9k · 2026-10-05 · MIT | One `beats.json`; named arcs and hook patterns; a "style bake-off" of one beat in several looks before spending on the rest | hook mechanisms in `STORY_SHAPES.md` §4 |
| [yaxeen/storytelling-skills](https://github.com/yaxeen/storytelling-skills) | 30 · 2026-07-16 · MIT | Claude skills for loops, bookends, titles and thumbnails, built from creator podcasts; thresholds without data | rule E5; the loop tracker we already had |
| [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) | 2.6k · 2026-11-17 · MIT | Render quality-control notes (motion that stops dead, black gaps, loudness targets) | nothing new: `qa_freeze`, `qa_film` already cover it |
| [syydaniel/kazi](https://github.com/syydaniel/kazi), [HeyChengC/wallstreet-explainer](https://github.com/HeyChengC/wallstreet-explainer) | 32, 748 · NOASSERTION (Chinese) | The action lands 3 frames before the keyword; a measured keyword-hit rate; three hooks of different mechanism roughed out and one picked; "elements each doing their own entrance read as slides: give the shot a camera instead" | hook mechanism varies per video (`STORY_SHAPES.md` §4). Ideas only |
| [mutonby/openshorts](https://github.com/mutonby/openshorts) | 9k · 2026-11-18 · MIT | Rewrites a clip's hook after looking at three frames of the actual clip | the fresh-eyes question "do the first three tiles show the promise?" |

## Tools found, not yet used

| Tool | Licence | For |
|---|---|---|
| [DanielSWolf/rhubarb-lip-sync](https://github.com/DanielSWolf/rhubarb-lip-sync) | MIT | 6–9 mouth shapes from the voice file. Parked: host craft is on the stop-doing list |
| [BrokenSource/DepthFlow](https://github.com/BrokenSource/DepthFlow) | AGPL-3.0 (a tool we would run, not code we ship) | depth parallax on archive photos; needs a GPU |
| [visioncortex/vtracer](https://github.com/visioncortex/vtracer) | MIT | photo to SVG paths for line-draw reveals |
| [microsoft/TRELLIS](https://github.com/microsoft/TRELLIS), [VAST-AI-Research/TripoSR](https://github.com/VAST-AI-Research/TripoSR), [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) | MIT | one 3D object reveal per film |
| [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) | MIT | a self-hosted voice fallback with an expressiveness control |
| `yt-dlp`, `youtube-transcript-api`, `youtube-comment-downloader`, `textstat` | Unlicense / MIT | already the base of our radar; a comment miner for audience questions is the open gap |

## Read and set aside

- **Content mills** (MoneyPrinterTurbo, ShortGPT, short-video-maker, MoneyPrinterV2, NarratoAI): script → TTS → keyword stock footage → captions, with no critic and no hook craft. Nothing to take; it is the look the inauthentic-content policy names.
- **Marketing "retention" skills** that quote "65 % decide in 3 s", "the first 42 seconds", "a pattern interrupt every 60–90 s": the numbers lead to vendor pages with no study.
- **Open retention predictors and click-through predictors**: none found that is credible. Our own 48 h and 7-day loop is ahead of every repo here.
- **Remotion skills, Motion Canvas, Revideo, Manim**: other renderers. Remotion's licence needs a paid company plan above 3 employees.
- **Model weights with non-commercial terms**: MusicGen (CC-BY-NC), F5-TTS weights (CC-BY-NC). Not for a monetised channel.

## Music and voice (decisions still open: see the channel's STYLE.md)

- The only source where the platform itself says Content ID will not claim the track is the **YouTube Audio Library filtered to "Attribution not required"** (YouTube Help 3376882). It has no API: the operator downloads a house family of 3–4 beds per channel once.
- A Creative Commons licence, CC0 included, does not stop someone registering the track in Content ID later. Pixabay needs no credit but claims are reported: keep the licence certificate per track. CC BY sources (Incompetech; Scott Buckley, whose library auto-claims a video with no credit) need the credit line in the description.
- Generated beds: ElevenLabs Music is listed on fal at about 0.80 USD per minute and describes its output as cleared for commercial use; one 60–90 s loop per mood, reused, is 1–2 USD once. Paid: operator's OK first.
- `kit/tools/mix_bed.sh` already ducks the bed under the voice and dips it at `K.dip` marks. The missing piece was never the mix; it was a licensed track in `kit/music/` with a line in a ledger (track, source, licence, date, credit text).
- Voice: ElevenLabs v3 takes audio tags and ellipses but no SSML breaks; pauses before a reveal come from the text (an ellipsis or a paragraph break), then check the gap in `WORDS.txt`. Tested 18/11/2026 on one hook (63 words, same voice, `fal-ai/elevenlabs/tts/eleven-v3`, 0.10 USD per 1,000 characters): v3 at speed 1.0 read at 136 wpm plain and 129 wpm with tags; the film's v2 take was made at speed 1.1 (158 wpm), so most of that gap is the speed setting, not the model. Pitch movement was about the same and the loudness range slightly wider (1.8–2.4 LU against 1.4). v3 returns character timestamps `vo_build.py` can read; audio tags arrive as zero-length tokens that would need filtering. Measured, not heard: nothing in the numbers argues for a switch. Stay on multilingual v2 unless a listening test says otherwise (the A/B file is in `vo/_lab/`).
