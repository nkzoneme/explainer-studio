### A. Sound Design

#### 1. Exhaustive SFX Table (00:00.0 – 01:30.0)

| Time | Sound Description | Synced Visual Event | Loudness (vs. VO) | Timing (vs. Visual) |
| :--- | :--- | :--- | :--- | :--- |
| `00:00.1` | Rapid mechanical ticking / dial clicks | Year counter rolling from 2021 to 2024 on bottom timeline | Quieter (-12dB) | On (0 ms) |
| `00:00.9` | Soft low-mid whoosh + subtle water/ink spread | Blue map fill spreading across NYC boroughs + "NYC" label pop | Quieter (-10dB) | On (0 ms) |
| `00:02.4` | Crisp UI pop / click + light paper slide | Green pin dot and callout box with McKinsey sign popping out | Quieter (-8dB) | Slightly before (-30 ms) |
| `00:07.8` | Low atmospheric bass swell / whoosh | Fade-in of frosted glass overlay over trash bins | Quieter (-10dB) | On (0 ms) |
| `00:08.1` | Rapid soft typewriter/UI clicks (5 hits) | Words "HOW TO PUT RUBBISH IN A BIN?" appearing word-by-word | Quieter (-12dB) | On (0 ms) |
| `00:09.7` | Smooth airy whoosh | Frosted glass pill with "McKinsey & Company" logo scaling in | Quieter (-9dB) | On (0 ms) |
| `00:11.6` | Fast paper/card shuffling flutter (deck deal) | 3D stack of presentation slides fanning out from left to right | Quieter (-8dB) | On (0 ms) |
| `00:12.3` | Rapid digital/mechanical counter ticks | Red badge counter ticking up from 01PG to 80PG | Quieter (-11dB) | On (0 ms) |
| `00:16.1` | Marker highlight swipe / soft friction sound | Teal highlight wiping across "Containerization?" text | Quieter (-12dB) | On (0 ms) |
| `00:19.6` | Camera shutter click / UI card snap | "Rats" photo card popping in over street background | Quieter (-9dB) | On (0 ms) |
| `00:21.0` | Horizontal slide whoosh + card snap | "Dirty streets" card sliding in from right | Quieter (-9dB) | On (0 ms) |
| `00:22.1` | Horizontal slide whoosh + card snap | "Pedestrian obstruction" card sliding in from right | Quieter (-9dB) | On (0 ms) |
| `00:23.8` | Soft hollow pop | 3D faceless mannequin in graduation gown scaling up | Quieter (-10dB) | On (0 ms) |
| `00:25.8` | Plastic/hollow pop + light chime | Yellow wheelie bin inside frosted glass square popping in | Quieter (-9dB) | On (0 ms) |
| `00:29.8` | Smooth lateral whoosh | Camera panning right from mannequin to bin and slide deck | Quieter (-10dB) | On (0 ms) |
| `00:31.2` | Rapid digital tally / cash counter whir | "$4,000,000" text rolling up below the slide deck | Quieter (-8dB) | On (0 ms) |
| `00:32.8` | Three staggered card pops + rapid ticker whir | Three red slide cards appearing below with "$42,000" counters rolling | Quieter (-9dB) | On (0 ms) |
| `00:37.6` | Deep transition whoosh | Slide cards zooming out into grey abstract background | Quieter (-8dB) | On (0 ms) |
| `00:38.2` | 4 staggered soft thuds / UI blocks | 4 tiers of the blue organizational pyramid stacking up | Quieter (-10dB) | On (0 ms) |
| `00:40.4` | Fast camera zoom whoosh | 3D camera pushing in and tilting on the pyramid | Quieter (-9dB) | On (0 ms) |
| `00:46.1` | Subtle audio cut / room tone shift | Hard cut to Peter Thiel live interview clip | Equal (clip audio) | On (0 ms) |
| `00:49.0` | Crisp paper/screen slide whoosh | Transition from interview clip to newspaper headline canvas | Quieter (-8dB) | On (0 ms) |
| `00:49.6` | Wet marker highlight swoosh | Yellow highlight drawing over McKinsey headline | Quieter (-10dB) | On (0 ms) |
| `00:50.8` | Page flip / slide whoosh + marker swoosh | PwC Reuters article sliding in + yellow highlight | Quieter (-9dB) | On (0 ms) |
| `00:52.1` | Page flip / slide whoosh + marker swoosh | Deloitte article sliding in + yellow highlight | Quieter (-9dB) | On (0 ms) |
| `00:53.9` | Felt-tip pen circle scribble sound | Red hand-drawn circle animating around "INDUSTRY?" | Quieter (-8dB) | On (0 ms) |
| `00:56.8` | Soft group pop (staggered) | Cluster of blue graduate mannequins popping in on left | Quieter (-10dB) | On (0 ms) |
| `00:57.6` | Vertical swipe / curtain whoosh | Red vertical banner with McKinsey/PwC/Deloitte logos dropping | Quieter (-9dB) | On (0 ms) |
| `00:59.4` | Staggered soft pops (9x) | Grid of 9 red graduate mannequins appearing on right | Quieter (-11dB) | On (0 ms) |
| `01:18.0` | Broadcast news cut (diegetic audio) | Cut to news anchor ("Deloitte used artificial intelligence...") | Equal to VO | On (0 ms) |
| `01:21.7` | Broadcast news cut (diegetic audio) | Cut to Sky News Australia anchor | Equal to VO | On (0 ms) |
| `01:26.8` | Broadcast news cut (diegetic audio) | Cut to WION news anchor | Equal to VO | On (0 ms) |

#### 2. Music, Room Tone & Mix Architecture
* **Music Genre & Instrumentation:** Minimalist investigative documentary score. Starts at `00:00.0` with a pulsing, muted pluck synth bass and a sparse, melancholic piano/marimba ostinato in a minor key. Around `01:40.0` (the 1990s historical section), it shifts to a slightly warmer, rhythmic pulsing synth pad before returning to tension-building Rhodes chords and subtle sub-bass swells.
* **Music Ducking:** The music sits consistently at roughly -18dB to -22dB below the narrator's voiceover. During live-action soundbites (`00:46.1–00:49.0` and `01:18.0–01:32.0`), the music ducks another 6dB or fades out almost completely (`01:31.0` hits a dead-stop dramatic pause after "...laid off 2,000 employees" before resuming at `01:32.8`).
* **Room Tone:** The narrator's voiceover is studio-dry, close-miked with heavy compression and a clean noise gate (no audible room tone). Archival clips (`01:18–01:32`) carry their native broadcast room tone/compression, which creates a deliberate texture contrast.
* **Transition Audio:** Almost every transition between motion-graphic canvases and B-roll uses a layered low-pass filtered airy whoosh (`200Hz–2kHz`) paired with a subtle mechanical click or paper rustle.
* **SFX Density:** In motion-graphic-heavy segments (`00:00–01:00`), SFX density is high—approximately **22–25 distinct audio events per minute** (roughly one every 2.5 seconds). During archival B-roll montages (`01:01–01:17`), SFX drop to near zero, letting the music and VO carry the pacing.

---

### B. Character Acting

This video deliberately avoids traditional 2D rigged character animation (no lip-syncing cartoons), opting instead for a **3D minimalist mannequin/figurine aesthetic** paired with real archival footage:
* **Lip Sync & Facial Features:** The animated characters (`00:24.0`, `00:57.0`, `03:18.0`) are faceless matte-white 3D mannequins or flat vector silhouettes (`05:43.0`). There are **no mouths, eyes, blinks, or eyebrows**.
* **3D Mannequin Acting & Idle Motion (`00:24.0–00:37.0`, `00:57.0–01:00.5`):**
  * At `00:24.0`, the graduate mannequin is rendered as a 3D object with subtle ambient occlusion and cloth folds on the black gown. It does not breathe or wave, but at `00:28.5` the camera pushes into a close-up of its head while the **tassel on the mortarboard cap sways slightly** and a green glowing node pulses on its temple (`00:29.0`) before a dotted line shoots out to the right.
  * At `03:18.0–03:29.0`, a 3D businessman mannequin in a dark suit stands with a briefcase. While the pose itself is static (no limb articulation), "acting" and status are conveyed via **floating UI status badges** (`-` red minus circles orbiting the torso at `03:21.5`) and a pulsing green radial aura behind the figure.
* **2D Vector Silhouette Acting (`05:43.0–05:45.5`):** In the McKinsey org-chart easel scene, black vector stick figures have static poses (arms raised at top, hands on hips in middle), and state changes are shown by **color-swapping** individual figures from black to red (indicating layoffs) rather than articulating limbs.
* **Live-Action "Character" Framing:** When real speakers appear (`00:46.1` Peter Thiel, `01:18.0` news anchors, `04:58.0` Sam Altman), they are cut in mid-gesture (e.g., Thiel's hand chopping downward on "total racket") to provide human kinetic energy that contrasts with the sterile corporate graphics.

---

### C. Object Motion

* **Entry & ExitChoreography:**
  * **3D Card Fanning (`00:11.5–00:15.5`):** The 80-page McKinsey deck enters by fanning out horizontally in 3D space (rotated ~25° on the Y-axis) like a dealer spreading playing cards, settling with a smooth exponential ease-out (`cubic-bezier(0.16, 1, 0.3, 1)`).
  * ** Glassmorphic Containers (`00:09.8`, `00:26.0`, `05:36.0`, `06:45.0`):** Key brand logos and 3D icons sit inside rounded-rectangle frosted-glass pills (`backdrop-filter: blur()`). They enter via a subtle scale-up (`0.85` to `1.0`) combined with an opacity fade over `350ms–450ms`, with almost no overshoot—giving a heavy, premium corporate feel rather than a bouncy cartoon feel.
  * **Photo Callout Cards (`00:19.5–00:23.5`):** White-framed window cards ("Rats", "Dirty streets", "Pedestrian obstruction") enter via a horizontal carousel slide from right to left (`duration: ~400ms`, strong ease-out), pushing the previous card off-screen to the left while the background B-roll cross-dissolves underneath.
  * **Icon Grid Pop & Color-Swap (`02:20.0–02:33.5`):** A 3D isometric blue skyscraper pops up in the center (`scale: 0 -> 1` with slight overshoot). Six rounded square icons (Finance, HR, Marketing) pop in around it in pairs (`stagger: ~150ms`). At `02:31.0`, red diagonal slash lines draw across three of the icons (`stroke-dashoffset` wipe over `250ms`) while the remaining three swap from pink to green.
* **Secondary Motion:**
  * **Floating / Parallax Drift:** Even when an object has finished its main entry animation, the camera or the object itself maintains a continuous slow drift (`scale: 1.0 -> 1.04` over 3–4 seconds, or a slow 3D orbital tilt like the pyramid at `00:40.0–00:45.0`).
  * **Background Wave Displacement:** The signature grey/white background (`00:24.0`, `00:56.0`, `03:18.0`, `05:35.0`) is never static—it is a continuously morphing 3D undulating liquid/cloth surface (or animated Perlin noise displacement map) that ripples slowly throughout the scene.
  * **Particle / Money Rain (`05:26.5–05:29.0`):** Dollar bills flutter downward in 3D space with rotation and sine-wave horizontal drift behind the red-tinted McKinsey Compass slide.
* **Motion Frequency:** There is **virtually never a static frame lasting more than 1 second**. Even on static newspaper clippings (`00:50.0`, `01:57.0`, `06:25.0`), the camera is continuously pushing in (`zoom: 1.0 -> 1.08`), tilting slightly in 3D space, or animating a highlighter stroke across the text.

---

### D. Camera & Transitions

* **2.5D / 3D Canvas Camera Moves:**
  * **Spatial Canvas Panning (`00:24.0–00:37.0`):** Instead of hard-cutting between the graduate, the bin, and the cost breakdown, all elements live on a single large grey canvas. The camera starts centered on the graduate (`00:24.0`), pans right to include the bin (`00:26.0`), pushes into an extreme close-up of the graduate's cap (`00:28.8`), whip-pans right along a dotted line to the bin and 80-page deck (`00:30.0`), and then pulls back and pans down to reveal the three red "$42,000" slide cards (`00:33.0`).
  * **Dutch Angle / 3D Perspective Tilts (`00:40.5`, `01:57.0`, `04:05.0`, `06:26.0`):** When showing documents, org pyramids, or web articles, the camera rarely views them flat-on. It orbits in 3D space (`rotateX(15deg) rotateY(-20deg) rotateZ(3deg)`) while slowly pushing in, giving flat screenshots depth and cinematic tension.
* **Transitions Between Scenes:**
  * **Frosted Glass Blur-Over (`00:07.8`, `00:54.0`):** Live-action B-roll doesn't just cut to graphics; a translucent white/grey frosted glass layer fades in *over* the video (`backdrop-filter: blur(16px)`), turning the video into an abstract moving background for the typography.
  * **Timeline Scrubbing (`00:00.0–00:01.0`, `01:40.0–01:41.5`):** Historical transitions use a horizontal tick-mark ruler at the bottom of the frame with a red year badge (`2021 -> 2024`, `2003 -> 1990`) that scrubs backward or forward to anchor the viewer in time.
  * **Match-Position / Thematic Cuts (`05:43.0`):** A real Congressional hearing room cuts to a staged office room where a presenter points at a McKinsey pyramid chart on an easel, maintaining the visual motif of "people being lectured by consultants."

---

### E. Text & Graphics

* **On-Screen Typography:**
  * **Primary Display Font:** Bold, geometric sans-serif (resembling *Montserrat Bold* or *Futura PT Heavy*), all-caps, wide tracking (`letter-spacing: 0.08em`), usually dark charcoal (`#222222`) on light backgrounds or white on dark backgrounds.
  * **Word-by-Word / Highlight Emphasis (`00:08.0`, `00:54.5`):** In "HOW TO PUT RUBBISH IN A BIN?", the word `RUBBISH` is inverted (white text inside a solid white/translucent box). At `00:54.5`, "WHAT HAPPENED TO THE INDUSTRY?" types on word-by-word, and a hand-drawn red ink circle loops around `INDUSTRY?`.
* **Captions:** There are **no burned-in subtitles/captions** for the narrator's voiceover—only intentional kinetic typography titles for key hooks and section headers (`00:08.0`, `00:54.5`, `02:53.0`, `04:01.0`, `05:35.0`, `06:45.0`, `08:53.0`).
* **Numbers & Counters:**
  * **Slot-Machine / Odometer Counters (`00:31.5`, `00:33.5`, `08:50.0`):** Large currency numbers (`$4,000,000`, `$42,000`, `$300,000,000`) use rapid digit-scrolling/odometer animations where each place value spins vertically or ticks up rapidly before locking into the final figure.
  * **Badge Counters (`00:12.0–00:15.0`):** A circular red badge (`80PG`) scales up and counts from `1` to `80` as the slide deck fans out.
* **Charts & Data Visualizations:**
  * **1990s M&A Line Chart (`02:02.5–02:09.0`):** Drawn on a textured light-grey grid with a 3D perspective tilt. A bright cyan line draws from left to right (`1985` to `2000`) with a glowing white leading dot and a soft cyan gradient fill underneath. A red callout box (`$0.4 TRILLION` -> `$1.7 TRILLION`) tracks along the tip of the line, scaling up as the line spikes vertically in 1998–2000.
  * **Grouped Bar Chart (`02:44.5–02:55.0`):** "RISE IN MANAGEMENT CONSULTANCIES REVENUE" features three color-coded vertical bars per year (McKinsey dark blue, BCG medium blue, Bain light blue) that grow upward from the X-axis (`scaleY: 0 -> 1`), accompanied by a red dotted trend curve arching over the McKinsey bars.
  * **M&A Crash Chart (`03:11.0–03:17.5`):** The blue line climbs to 2000, then switches to a **red line** as it plunges downward from 2000 to 2003, with a pink shaded danger zone highlighting the drop.
  * **Multiplier Callout (`03:41.5–03:46.5`):** As the red line for "RISE IN US SPENDINGS" climbs from 2000 to 2009, a central green circle badge ticks up from `0X` -> `1X` -> `2X` -> `3X`.
* **Highlighting Techniques:**
  * **Article Highlighter (`00:50.0`, `01:57.0`, `04:06.0`, `06:27.0`, `08:00.0`):** Web articles are shown in full, then a bright yellow (`#FFE600` with `mix-blend-mode: multiply`) highlight bar wipes left-to-right across the key headline and sub-sentences, often staggered across 2–3 lines.

---

### F. Visual Style

* **Color Palette:**
  * **Base Canvas:** Cool clinical greys and off-whites (`#E8EAEB` to `#F5F7F8`) for the main motion-graphic environments; deep obsidian/black (`#0A0B0D`) for the late-video data sections (`05:03.0–05:33.0`).
  * **Accent Colors:** High-contrast "investigative" accents—Signal Red (`#E63946`) for negative metrics, costs, and circles; Highlighter Yellow (`#FFEA00`) for text callouts; Corporate Blues (`#005082`, `#00A8E8`) for McKinsey/NYC/M&A charts; Emerald Green (`#2A9D8F`) for positive multipliers (`3X` at `03:45.0`).
* **Textures & Surfaces:**
  * **Liquid/Topo Grey Background (`00:24.0`, `00:56.0`, `03:18.0`, `04:01.0`, `05:35.0`, `06:45.0`):** A signature visual motif—a soft, matte-grey 3D undulating metaball/topographic surface that slowly morphs in the background, giving a modern, abstract, slightly unsettling "corporate lava lamp" texture.
  * **Glassmorphism (`00:10.0`, `00:26.0`, `05:37.0`, `06:45.0`, `08:42.0`):** Heavy use of translucent white/grey containers with `backdrop-filter: blur(12px)`, crisp `1px` white specular borders (`rgba(255,255,255,0.6)`), and soft drop shadows (`0 20px 40px rgba(0,0,0,0.12)`).
  * **Archival Film Frame (`01:40.0–01:55.0`, `02:34.0`, `03:47.0`):** Historical B-roll is framed inside a 4:3 or 16:9 Matte Black film border with vertical white sprockets/timecode text (`CINEMA 200T ISO`, `24A 51827`) on the left edge, instantly signaling "historical context."
* **Depth & Parallax:** Strong separation between background (blurred video or undulating 3D waves), midground (charts, document planes), and foreground (floating badges, counters, red circles), enhanced by shallow depth-of-field blur on the edges of tilted 3D newspaper shots (`00:50.0`, `04:06.0`).

---

### G. 10 Micro-Techniques to Copy (with HTML/GSAP Implementation Hints)

1. **Frosted Glass Title Over Live Video (`00:08.0` / `00:10.0`)**
   * *Hint:* Place a `div` over `<video>` with `backdrop-filter: blur(14px); background: rgba(255,255,255,0.45); border: 1px solid rgba(255,255,255,0.7); border-radius: 24px;` and animate `gsap.from(el, {scale: 0.88, opacity: 0, duration: 0.45, ease: "power3.out"})`.
2. **3D Slide Deck Fan-Out with Live Page Counter (`00:11.5–00:15.0`)**
   * *Hint:* Stack 15 card `div`s inside a `perspective: 1000px` container and run `gsap.to(".card", {x: (i) => i * 18, z: (i) => -i * 12, rotationY: -22, stagger: 0.03, ease: "power2.out"})` while tweening a counter object `gsap.to(counter, {val: 80, roundProps: "val", duration: 1.5})`.
3. **3D Tilted Article Push-In with Multi-Line Highlighter (`00:50.0–00:53.5`)**
   * *Hint:* Wrap the article screenshot in a 3D plane (`transform: perspective(900px) rotateX(12deg) rotateY(-15deg) rotateZ(2deg)`) with a slow scale tween, and animate `<span class="hl">` pseudo-elements using `gsap.fromTo(".hl", {scaleX: 0, transformOrigin: "left"}, {scaleX: 1, duration: 0.35, stagger: 0.15, ease: "power2.inOut"})` with `mix-blend-mode: multiply`.
4. **Infinite Spatial Canvas Pan with Dotted Connector Line (`00:28.5–00:36.0`)**
   * *Hint:* Put all scene assets inside a `4000px`-wide `<div id="world">` and pan the camera by animating `gsap.to("#world", {x: -1400, y: -300, scale: 0.85, duration: 1.2, ease: "expo.inOut"})` while animating an SVG `<line stroke-dasharray="6 6">` via `strokeDashoffset`.
5. **Tracking Callout Badge on a Drawing SVG Line Chart (`02:03.0–02:09.0`)**
   * *Hint:* Use GSAP `MotionPathPlugin` (`gsap.to("#priceBadge", {motionPath: {path: "#chartLine", align: "#chartLine"}, duration: 3, ease: "power1.inOut"})`) synced with `DrawSVGPlugin` on `#chartLine` and a live number tween from `0.4` to `1.7`.
6. **Isometric Icon Pruning (Red Slash + Color Swap) (`02:21.0–02:33.0`)**
   * *Hint:* Pop in 6 grid cards with `gsap.from(".dept", {scale: 0, stagger: 0.1, ease: "back.out(1.7)"})`, then at the beat, animate an SVG diagonal red line (`strokeDashoffset: 0`) across the "cut" cards while tweening `backgroundColor: "#8BC34A"` on the survivors.
7. **Dual-Color Regime-Change Line Chart (`03:11.0–03:17.5`)**
   * *Hint:* Split the SVG polyline at the peak (`year 2000`) into `#growthPath` (blue) and `#crashPath` (red); sequence them in a GSAP timeline so the red line draws downward immediately after the blue peaks, accompanied by a `gsap.fromTo("#dangerZone", {opacity: 0}, {opacity: 0.25})` pink background rect.
8. **Archival Film Gate Overlay for Historical B-Roll (`01:40.0–01:55.0`)**
   * *Hint:* Overlay a fixed PNG/SVG frame with rounded inner corners, a left sidebar containing vertical monospace text (`writing-mode: vertical-rl`), and a subtle CSS film grain overlay (`opacity: 0.07`) to unify disparate low-res archival clips.
9. **Red Tinted "Danger" Breakdown with Falling Cash (`05:26.0–05:29.0`)**
   * *Hint:* Tween a red color-overlay `div` (`background: rgba(220, 20, 20, 0.35); box-shadow: 0 0 30px red`) over the corporate slide while spawning 30 particle `div`s with dollar-bill sprites animated via `gsap.to(bill, {y: 800, rotationX: "random(180,720)", rotationZ: "random(-90,90)", duration: "random(2,4)"})`.
10. **Odometer Currency Ticker Over Live B-Roll (`08:49.5–08:52.5`)**
    * *Hint:* Composite bold white text with `text-shadow: 0 8px 24px rgba(0,0,0,0.6)` over drone ship footage and use a custom JS formatter inside GSAP's `onUpdate` to rapidly cycle random digits before settling on `$300,000,000` over `1.4s`.

---

### H. Flaws & Cheap-Looking Moments

* **`00:31.0–00:35.5` ( awkward 3D Capitol Building cutout & math mismatch):** A low-poly pink/red US Capitol dome is pasted directly on top of the black NYC McKinsey slide (`00:31.2`) even though the contract was with the *New York City* municipal government, not the federal government in DC. Furthermore, the narrator says the 80-page deck cost $4,000,000, "equivalent to $42,000 per slide" ($4M / 80 is actually $50,000, and the counter on the three cards at `00:34.0` glitches between `$37,333` and `$42,000`).
* **`00:39.5–00:44.5` (Unedited PowerPoint template placeholder text):** In the 3D "Organizational Pyramid for Stakeholder Relationship Management" graphic, the bullet callouts on the left and right literally say **"Add text here"** four times (`00:41.0`), and the title has a typo (`RELATIONSHP MANAGEMENT` missing the `I`), revealing it was ripped directly from a stock slide template without cleanup.
* **`00:51.0–00:53.0` & `08:01.0` (Future/hallucinated article dates):** Several news screenshots have bizarre or future dates (e.g., at `00:52.5`, the Deloitte UK job cuts article is dated `October 1, 2025`; at `08:29.0`, the CIO Dive article is dated `March 14, 2025`), and at `01:36.0–01:39.0`, while talking about "one of the most useful industries in America," the B-roll shows **Russian Foreign Minister Sergey Lavrov and Dmitry Medvedev** at a diplomatic banquet.
* **`02:03.0–02:08.5` (Misspelled chart title):** The major full-screen chart title reads `ANNUAL VALUE OF MERGERS & AQUISITIONS` (missing the `C` in *Acquisitions*), and the typo is repeated again at `03:12.0` (`FALL OF MERGERS & AQUISITIONS`).
* **`03:05.0–03:09.5` (Completely mismatched historical B-roll):** While the narrator says "Scandals like Enron... ended up forcing the government to reintroduce the very same rules [Sarbanes-Oxley, 2002]," the archival footage shows **Yitzhak Rabin, Yasser Arafat, and Bill Clinton signing the 1993 Oslo Accords** on the White House lawn.
* **`03:30.0–03:34.5` (Chart data vs. narration contradiction):** The narrator says "By the 2000s, the government's workforce had nearly doubled," while showing a chart (`GROWTH OF GOVERNMENT EMPLOYEES IN US`) whose Y-axis is truncated from `18` million to `23` million—meaning the visual line goes from bottom to top, but the actual number only rose from 18M to 22.5M (~25%, nowhere near doubling).
* **`05:08.5` (Truncated text in callout frame):** Above the NYC trash pile photo, the typewriter header inside the white border cuts off mid-word: `WASTE DIDN'T SEEM TO BE GETTING ANY BET` (missing `TER`).