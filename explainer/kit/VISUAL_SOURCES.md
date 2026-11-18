# Visual sources: what a shot can be made of, beyond a prop on the ground

Read at the beat plan (explainer-direct Step 2) when a beat is planned as "card + label" or "prop slides in". The picture review of our own films (18/11/2026, `REVIEW_PASS.md`) showed the same three frames over and over: a text card in the centre of one dark ground, a small object floating in it, the host pointing from a corner. Pace QA passed on all of them. More cuts of the same picture do not fix that; a different kind of picture does.

Order of preference for any sentence: **the real thing** (photo, footage, the actual page or document, a map of the actual place) → **the thing drawn as a world the camera moves through** → **a diagram that grows** → a card with words (last, and only as a 2–3 s proof insert).

Everything here must stay deterministic under frame capture: no `Date.now`, no `requestAnimationFrame`, no unseeded `Math.random`, no `repeat: -1`; clips are muted `<video>` elements timed by `data-start`, or image sequences; SVG strokes are revealed with the `stroke-dashoffset` attribute, not CSS, and never through `<mask>` or `<clipPath>` (stale paint on reverse seeks). Source: HyperFrames `docs/concepts/determinism.mdx` and component READMEs.

## 1. Mechanisms to port from the HyperFrames registry

The renderer we already use ships about 450 blocks and components (`npx -y hyperframes@0.9.46 catalog <words> --json`; Apache-2.0). They are editable source, each with a header comment that states its timing envelope and its seek-safe laws.

**Tested 18/11/2026:** `npx -y hyperframes@0.9.46 add <name>` writes `compositions/components/<name>.html`; a `class="clip"` div with `data-composition-src`, `data-start`, `data-duration`, `data-track-index` and `data-variable-values='{…}'` mounts it inside a kit chapter, and `check` and `snapshot` run. But a component brings **its own opaque ground, fonts and colours** (`vox-annotate` drew a black panel, `hw-callout-circle` a green field over our scene). So:

- **Overlay mechanisms** (annotation, boil, shake): read the installed file and port the mechanism into the chapter with the channel's look. Do not mount as-is.
- **Whole-shot blocks** (a map, a chart, a route): install, re-skin the installed copy to the channel palette and fonts, then mount it as a full-frame insert. It counts as a mode change.
- Install into the chapter only what the chapter uses. A font or asset a component brings (for example Caveat) needs its own licence line.

| Job | Registry names to read | Use it for |
|---|---|---|
| Mark the real thing | `vox-annotate`, `hw-callout-circle`, `hw-arrow`, `hw-box-label`, `marker-highlight`, `yt-feather-highlight` | a hand-drawn circle, arrow or highlight landing on one phrase of a real document, one object in a real photo: the proof insert |
| Hand-drawn life | `hw-boil`, `stop-motion-cadence`, `whiteboard-ink`, `svg-stroke-trace` | a seeded line wobble that re-poses every 2 frames; drawings that build with a pen front |
| Seams with a cause | `match-cut`, `cut-the-curve`, `zoom-through-transition`, `parallax-zoom`, `iris-reveal`, `whip-pan-cut`, `torn-paper-rip`, `paper-collage-reveal` | entering the next set through an object already on screen (`CRAFT_RULES.md` §15) |
| A world the camera crosses | `pan-stations`, `pull-back-reveal`, `camera-rig-depth-stack`, `scroll-camera-story`, `push-in`, `camera-shake` | one large drawing with stops; a tight detail, then one pull-back that reveals where it sits; shake on an impact |
| A number that lands | `count-up`, `number-wheel`, `chart-story`, `bar-chart-race`, `mk-line-graph`, `split-flap-board`, `comparison-split`, `before-after-wipe` | number chains: one number slot that stays while the value and its picture change |
| Places and routes | `world-map`, `us-map`, `us-map-flow`, `nyc-paris-flight` | a real map with the route, the outage or the fleet drawn on it |
| Texture | `grain-overlay`, `halftone-dissolve`, `freeze-frame-dressing` | paper, grain and tape on a frozen real photo |

Product-launch items (cursors, notification stacks, device frames, chat mock-ups) are not for us: a grey mock screen standing in for the real thing is a tell.

## 2. Sources that are not animation

| Source | Tool | Cost per shot | Suits | Flags |
|---|---|---|---|---|
| **Proof capture**: the real web page, filing or status page, scrolled or clicked | Playwright `recordVideo` at 1920×1080, trimmed with ffmpeg; `hyperframes capture <url>` | 0 | reveal, evidence | Government and court pages are safe; a news page is a tier-C crop of 4 s or less with outlet and date visible |
| **Archive photo with depth**: a slow push with parallax instead of a flat photo | DepthFlow (AGPL-3.0, runs locally, needs a GPU), or cut the photo into 2–3 layers by hand and move them at different rates in GSAP | 0 | chapter opener, b-roll | Looks wrong on flat cartoons; the layered cut-out works without a GPU |
| **Real footage** inside the world | `fetch_media.py` (`commons-video`, `nasa-video`, `archive --vetted`, `pexels --video`) | 0 | era and place b-roll, 5–15 % of runtime | already in explainer-direct "Footage"; licence and Content ID note per clip |
| **Line-draw reveal** of a real object | `vtracer` (MIT) to SVG paths, then the stroke-trace mechanism | 0 | diagram b-roll | trace only free-licensed photos |
| **Image-to-video hero shot**: a still of ours that moves (a vehicle pulling away, a screen flickering off) | kie.ai `grok-imagine/image-to-video` through `kie.py` (upload the still, `mode normal`, `duration 6`, `resolution 480p`) | **0.072 USD per 6 s clip** (0.012 USD/s, 6 s minimum; price read on kie.ai/grok-imagine 18/11/2026: read it again when ordering) | the hook, one chapter opener, the peak | **Paid: needs the operator's OK and counts in the 10 USD.** Tested 18/11/2026 on three of our stills (5 clips, 0.36 USD): the flat outlines and colours held in all five. What decides the result is the prompt: **name one part and one small action** ("only the top screen panel flickers and goes dark", "strictly side profile, the nose tilts up a few degrees") and add "flat 2D cartoon, clean bold outlines, flat colours, fixed camera, no shading, no 3D, no new objects, no text"; a loose prompt ("the plane takes off") turned the aircraft toward the camera and dimmed the whole frame. Output is 752×416: scale it up about 2.5× (fine for flat art, soft on small detail), and the clip's ground comes back a shade off the still's, so match the colour or mask the object. Look at an 8-frame strip of every clip before using it and trim at the first frame that drifts. H.264 mp4, 30 fps, no audio, embedded as a muted `<video>` |
| **3D object reveal**: one turntable or cutaway | TripoSR or TRELLIS (MIT) for a mesh from a photo, Blender scripted (ahujasid/mcp-for-blender, MIT), rendered to a PNG sequence | 0 cash, 30–60 min and a GPU | the peak of an engineering film | at most one per film; soft meshes; Hunyuan3D's licence excludes the EU, UK and South Korea |

**Hero-shot budget.** At most three generated clips per film (hook, one opener, the peak), at most 2 USD together, at most three attempts per kept shot. The beat plan marks each chapter's `hero` shot (explainer-direct Step 2); that is where a paid or slow source may go. Everywhere else stays free.

**Policy (YouTube).** A realistic synthetic scene, or altered footage of a real event or place, needs the altered-content label at upload; a clearly drawn cartoon does not. Never generate or animate a real person's face. The same generated-clip recipe on every video reads as templated content under the inauthentic-content policy: vary where and how hero shots are used.

## 3. Not now, and why

| Idea | Why not |
|---|---|
| Veo 3.x or Sora-class models for whole sequences | 0.4–0.7 USD per second breaks the budget; realism brings the disclosure label |
| Neural talking-head models on the cartoon host (LatentSync, MuseTalk, LivePortrait) | Trained on human faces; no evidence they hold a flat cartoon; several weights are non-commercial or unclear |
| Rhubarb Lip Sync (MIT) for 9 mouth shapes from the voice | The best-value host upgrade found, but host craft is on the stop-doing list while the host is on screen under a fifth of the film. Revisit if a channel's style raises the host share |
| Google Earth Studio flyovers | Attribution is required on screen and Google does not license the imagery for commercial use: medium risk on a monetised channel. Use our own map block |
| LTX video weights | Community licence with a paid tier above 10 million USD revenue; nothing we need from it |
| Mounting a registry component as-is | It brings its own ground and fonts (tested); port or re-skin |
| Remotion, Motion Canvas, Revideo, Manim code | Separate renderers. Borrow ideas only; Remotion needs a company licence above 3 employees |
