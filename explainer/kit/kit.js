/* kit.js — craft helpers for hand-directed HyperFrames/GSAP cartoon explainers.
 *
 * Everything here is deterministic and seekable: every tween is placed at an absolute time on the one
 * paused timeline you pass in; no Math.random, no Date.now, no repeat:-1, no network fetches.
 * Sound cues are collected and written as <audio class="clip" data-start data-duration data-volume>
 * elements by K.finish().
 *
 * IMPORTANT (HyperFrames 0.9.46, verified by render): script-inserted audio is only mixed when the page's
 * INLINE script contains the text  document.createElement("audio")  - the renderer scans inline scripts
 * for it before deciding to probe the live page. kit.js is an external file, so keep this comment next to
 * K.finish() in every composition:
 *     // REQUIRED MARKER: K.finish() inserts the SFX with document.createElement("audio").
 * Confirm in the render log: "audioCount" must jump from 1 to 1 + number of cues. If it stays 1 the film
 * has no sound effects. tools/qa_audio.py also catches this (SFX bus near -55 dB).
 *
 * Load order in index.html:
 *   <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
 *   <script src="kit/sfx/index.js"></script>      (window.KIT_SFX: name -> {file, role, dur, rms_db})
 *   <script src="levels.js"></script>             (optional, window.KIT_LEVELS from tools/speech_levels.py)
 *   <script src="kit/kit.js"></script>
 *
 *   const tl = gsap.timeline({ paused: true });
 *   const K = Kit.create(tl, { root: "#root", words: WORDS, levels: window.KIT_LEVELS, sfxBase: "kit/", sfxGain: 1.5 });
 *   (sfxGain: linear multiplier on every SFX cue. LEGACY mode: default 1.0, ~1.5 lands the bus 12-18 dB under the voice.
 *    EDIT mode (kit v2): default 0.6 is correct (15.4 dB in the edit-mode test); do NOT pass 1.5, it is ignored above 1.0.
 *    Check with tools/qa_audio.py. Do not also multiply data-volume by hand.)
 *   ... K.pop("#chip", 4.3); K.stamp("#x1", 5.2); host.talk(0, 12.8); ...
 *   // REQUIRED MARKER: K.finish() inserts the SFX with document.createElement("audio").
 *   K.finish();                                    // writes the <audio> cues; call once, last
 *   window.__timelines["main"] = tl; tl.seek(0);
 *
 * SOUND MODES (kit v2). Kit.create(tl, { ..., sound: "edit" | "legacy", channel: "<slug from explainer/channels/>" }).
 *   "edit" (default when kit/sfx_v2/index.js is loaded; needs kit/sfx_v2/palette.js for the channel's role -> file map):
 *     sound follows the edit. Auto sound only for transitions (whip/wipe/zoomThrough: whoosh peaking on the cut, K.cut for hard cuts),
 *     stamp/drop/cross (impact; { big: true } layers a sub-hit) and counter (soft riser + boom on the last number, no ticks).
 *     Everything else is silent unless { sfx: "role" } (whoosh_s/m/l, riser, subhit, boom, impact, impact_soft, paper, ui_tick,
 *     glitch, stinger, chime, engine, gear, radio) or K.sfx("role", t, { force, layer, db }). Old-library file names are ignored.
 *     K.finish() enforces: 1 accent per sentence besides transitions, no two cues within 0.25 s (except whoosh/riser into a hit,
 *     layer:true), nothing inside a K.dip; K.beatGrid(bpm, offset) snaps accents within +-0.12 s; K.dip(t, dur) = bed near-silent
 *     from t to t+dur, hit at t+dur (K.drop is the falling-prop helper). t of a cue = the moment its peak lands. Level: files are
 *     level-shaped per role (kit/sfx_v2/index.json), sfxGain defaults to 0.6 here (leave it unset; values above 1.0 are ignored in this mode). window.__kitCues.anchoredPct reports the share of
 *     cues within 0.15 s of a scene change / reveal / stressed word (tools/kit_cues.mjs, qa_audio.py).
 *   "legacy": every helper sounds (pop/label/draw/ticks), old kit/sfx library. Used automatically when sfx_v2 is not loaded.
 *
 * Rule for tweens: one helper per property per element. Idle motion (float, breathe, sway) goes on a
 * WRAPPER element, entrances (pop, drop, stamp) on the child, so they never fight over scale/x/y/rotation.
 */
(function () {
  "use strict";
  const FPS = 30;
  const q = (t) => Math.round(t * FPS) / FPS; // snap to frame
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const NS = "http://www.w3.org/2000/svg";

  // Seeded PRNG (mulberry32): the only source of "randomness" allowed.
  function rng(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ---------------------------------------------------------------------------------------------
  // Sound roles. Gain in dB relative to the voiceover clip at data-volume 1 (kit files peak at -3 dBFS,
  // an ElevenLabs VO peaks around -4 dBFS). Measured basis: the stickman B5 film places cue peaks
  // 9-19 dB under the voice peak (median 15). See CRAFT_RULES.md section 1.
  const ROLE_DB = {
    stamp: -10, impact: -12, error: -14, coin: -15, pop: -15, click: -14, ding: -16, paper: -14,
    scribble: -15, whoosh: -17, sting: -18, tick: -19, comedy: -19, riser: -19, loop: -30,
  };
  // Helper -> default sound (array = rotate through variants so repeats never sound copy-pasted).
  const DEFAULT_SFX = {
    pop: ["pop_1", "pop_2", "pop_3"], drop: ["thud_soft", "thud_wood", "tap_light"], stamp: ["stamp_1", "stamp_2"],
    draw: "scribble", circle: "marker", underline: "marker", whip: "swish_4", wipe: "whoosh_air",
    zoomThrough: "zoom_in", counterTick: ["tick_1", "tick_2"], counterEnd: "ding_1", coin: ["coin_1", "coin_2", "coin_3", "coin_4"],
    label: "swish_2", cross: "stamp_1", poseSwap: "swish_1",
    sticker: ["pop_1", "pop_bubble"], photo: "paper_place", tv: "swish_3",
  };

  // Face geometry per host pose, in native image pixels.
  // patches (preferred): painted mouth/blink images cut from AI edits of the same artwork
  // (tools/mouth_patches.py) -> <mouthDir>/<face key>_<B|A|O|E|blink>.webp, value = [x, y, w, h] in pose pixels.
  // Without patches the host falls back to the drawn SVG mouths/lids below (looks like a sticker on painted faces). mouth: centre, width, rotation (deg).
  // eyes: centre, radii, rotation. skin: flat skin colour next to the eyes. Add a pose by measuring it
  // with tools/face_grid.py. A pose without an entry simply gets no mouth/blink overlay.
  // Host face geometry per pose image, used for mouth patches, blinks and lip-sync. Register yours before kit.js loads:
  //   window.KIT_FACES = { host_neutral: { w: 900, h: 1500, skin: "#f4a86d", mouth: { x: 450, y: 360, w: 100, rot: 0 },
  //     patches: { B: [x, y, w, h], A: [...], O: [...], E: [...], blink: [...] }, eyes: [{ x, y, rx, ry, rot }, ...] } };
  // Measure with kit/tools/face_grid.py, paint patches with kit/tools/mouth_patches.py. A pose without an entry still works (no lip-sync).
  const FACES = Object.assign({}, (typeof window !== "undefined" && window.KIT_FACES) || {});
  const INK = "#2a1a14", MOUTH_DARK = "#4a1a16", TONGUE = "#d9675c";
  // Mouth shapes drawn for a mouth 100 units wide, centred on the closed-mouth line.
  // rest = the artwork's own closed mouth (no overlay). B small, D wide with teeth, C big open, O rounded.
  const MOUTHS = {
    B: `<path d="M-27 -2Q0 3 27 -2Q20 13 0 14Q-20 13 -27 -2Z" fill="${MOUTH_DARK}" stroke="${INK}" stroke-width="4.5" stroke-linejoin="round"/>`,
    D: `<path d="M-41 -5Q0 3 41 -5Q32 22 0 25Q-32 22 -41 -5Z" fill="${MOUTH_DARK}" stroke="${INK}" stroke-width="4.5" stroke-linejoin="round"/>` +
       `<path d="M-33 -1Q0 5 33 -1L29 6Q0 11 -29 6Z" fill="#fff"/>`,
    C: `<path d="M-37 -6Q0 1 37 -6Q34 38 0 42Q-34 38 -37 -6Z" fill="${MOUTH_DARK}" stroke="${INK}" stroke-width="4.5" stroke-linejoin="round"/>` +
       `<path d="M-30 -2Q0 4 30 -2L27 6Q0 10 -27 6Z" fill="#fff"/><ellipse cx="0" cy="31" rx="17" ry="8" fill="${TONGUE}"/>`,
    O: `<path d="M-17 2Q-15 -8 0 -8Q15 -8 17 2Q16 17 0 18Q-16 17 -17 2Z" fill="${MOUTH_DARK}" stroke="${INK}" stroke-width="4.5" stroke-linejoin="round"/>` +
       `<ellipse cx="0" cy="12" rx="8" ry="4" fill="${TONGUE}"/>`,
  };

  function create(tl, opt) {
    opt = opt || {};
    const root = typeof opt.root === "string" ? document.querySelector(opt.root) : opt.root || document.getElementById("root");
    const words = (opt.words || []).map((w) => ({ text: w.word || w.text || "", start: w.start, end: w.end }));
    const levels = opt.levels || null; // per-frame 0..1 speech level at 30 fps (optional)
    const sfxBase = opt.sfxBase || "";
    // sfxGain: linear multiplier on every SFX cue volume, applied in K.finish() (default 1 = old behaviour).
    // LEGACY mode only: ~1.5. At 1.0 the bus measured 18.7-20 dB under the voice in every chapter of a 12-chapter test film
    // (target 12-18); 1.33-1.6 brought it to 16-17.5. In "edit" mode the default is 0.6 and values above 1.0 are ignored (see below).
    // Verify with tools/qa_audio.py after the render.
    const sfxGain0 = () => (opt.sfxGain !== undefined ? +opt.sfxGain : 1);
    const SFX = window.KIT_SFX || {};
    const cues = [];
    const rot = {}; // rotation counters for variant lists
    let uid = 0;
    // ---- sound mode (kit v2). "edit": sound follows the edit (transition > reveal > key word > nothing); small
    // helpers are silent unless given { sfx: "role" }. "legacy": every helper sounds (old behaviour). Default: "edit"
    // when the sfx_v2 library is loaded (it has whoosh_m_1), else "legacy" so old films keep working unchanged.
    const EDIT = (opt.sound || (SFX.whoosh_m_1 ? "edit" : "legacy")) === "edit";
    const PAL = Object.assign({}, (window.KIT_PALETTES || {})[opt.channel] || {}, opt.palette || {}); // role -> [file names]
    const EDIT_DEFAULT = { stamp: "impact", drop: "impact", cross: "impact_soft", whip: "whoosh_m", wipe: "whoosh_s", zoomThrough: "whoosh_l" };
    // trim in dB per file role (files carry their own per-role peak, see kit/sfx_v2/index.json)
    const EDIT_TRIM = { whoosh_s: -4, whoosh_m: -2, whoosh_l: -1, riser: -3, boom: -3, subhit: -6, impact: -2, impact_soft: -2, stinger: -2,
      paper: -3, tick: -2, ui: -2, glitch: -3, chime: -4, theme: -4, radio: -2, mechanical: -3 };
    const LEGACY_NAMES = /^(pop|boing|swish|click|tick|ding|coin|scribble|marker|stamp|thud|whoosh_air|riser_air|zoom|sting|paper_place|tap|key|bell|camera|splat|flop|latch|metal|error|erase|glass|slide|loop|page|bubble)/;
    const anchors = []; // {t, type} scene changes and reveals, for the QA report
    const dips = [];
    let GRID = null;
    // sfxGain in "edit" mode (resolved 17/11/2026, sfx_ab/AB.md C_auto): the v2 files are level-shaped per role, and the DEFAULT 0.6 measured
    // 15.4 dB under the voice (target 12-18). The old 1.5 from explainer-direct is for LEGACY mode only: on v2 files it would sit about 8 dB
    // louder (roughly 7 dB under the voice, out of range). So in edit mode: unset -> 0.6; a value above 1.0 is treated as the legacy habit,
    // ignored with a warning; tune per chapter only inside 0.3-1.0 (qa_audio.py must show 12-18 dB).
    if (EDIT) {
      if (opt.sfxGain === undefined) opt.sfxGain = 0.6;
      else if (+opt.sfxGain > 1.0) { console.warn("[kit] sfxGain " + opt.sfxGain + " ignored in sound:'edit' (legacy value); using 0.6. See kit.js header."); opt.sfxGain = 0.6; }
    }
    const $ = (s, ctx) => (typeof s === "string" ? (ctx || document).querySelector(s) : s);
    const $$ = (s, ctx) => (typeof s === "string" ? Array.from((ctx || document).querySelectorAll(s)) : s.length !== undefined ? Array.from(s) : [s]);
    const mk = (tag, cls, parent, css) => {
      const e = document.createElement(tag);
      if (cls) e.className = cls;
      if (css) e.style.cssText = css;
      (parent || root).appendChild(e);
      return e;
    };
    const svgEl = (parent, w, h, css) => {
      const s = document.createElementNS(NS, "svg");
      s.setAttribute("viewBox", `0 0 ${w} ${h}`);
      s.setAttribute("width", w); s.setAttribute("height", h);
      s.style.cssText = "position:absolute;overflow:visible;pointer-events:none;" + (css || "");
      parent.appendChild(s);
      return s;
    };
    const K = { tl, root, words, cues, FPS, rng, FACES };
    // default parent for generated effects (puff, rays, sparkle, circle from a box): pass { fx: "#cam" } so they
    // live inside the camera wrapper and move with it
    const fxParent = () => $(opt.fx) || root;

    // ------------------------------------------------------------------------------- sound scheduler
    // K.sfx("pop_1", 4.32)                      one cue; t = the moment the sound's transient must hit
    // K.sfx(["coin_1","coin_2"], t)             rotates through the list on successive calls
    // K.sfx("stamp_1", t, { db: +2 })           trim relative to the role default; { vol } overrides
    // K.sfx("loop_machine", t, { dur: 4 })      loops are cut to dur with 0.3 s fades
    function pick(name, key) {
      if (!Array.isArray(name)) return name;
      const k = key || name.join("|");
      const i = rot[k] || 0;
      rot[k] = i + 1;
      return name[i % name.length];
    }
    K.sfx = function (name, t, o) {
      if (name === false || name == null) return null;
      o = o || {};
      if (EDIT && typeof name === "string" && !SFX[name] && !PAL[name] && LEGACY_NAMES.test(name)) return null; // old-library name in edit mode: silent
      let role = null;
      if (typeof name === "string" && PAL[name] && !SFX[name]) { role = name; name = PAL[name]; } // role -> palette variants
      name = pick(name, o.key || role);
      if (!EDIT && name === "scribble") name = (o.len || 0.6) > 0.95 ? "scribble_long" : (o.len || 0.6) > 0.7 ? "scribble_mid" : "scribble_short";
      const meta = SFX[name];
      if (!meta) { console.warn("[kit] unknown sfx: " + name); return null; }
      const cue = { name, t: Math.max(0, t), db: o.db || 0, vol: o.vol, dur: o.dur, meta, why: o.why || "" };
      if (EDIT) {
        // t = the moment the sound's main hit must land. Whooshes and hits are shifted so their peak lands on t;
        // risers end on t.
        const fr = meta.role, hit = /^(boom|impact|subhit|stinger|impact_soft)$/.test(fr), wh = /^whoosh/.test(fr);
        cue.ht = cue.t;
        cue.cls = o.cls || (wh ? "trans" : fr === "riser" ? "riser" : hit ? "hit" : "accent");
        cue.anchor = o.anchor || (o.explicit === false ? "" : "explicit");
        cue.force = !!o.force; cue.layer = !!o.layer; cue.pair = o.pair;
        if (fr === "riser") { cue.t = cue.ht - meta.dur; if (o.notBefore !== undefined && cue.t < o.notBefore) return null; cue.t = Math.max(0, cue.t); }
        else if (meta.role !== "loop" && meta.role !== "ambience" && meta.peak_t !== undefined)
          cue.t = Math.max(0, cue.ht - Math.max(meta.peak_t, o.lead || 0));
        if (cue.vol === undefined) cue.vol = Math.pow(10, ((EDIT_TRIM[fr] || 0) + cue.db) / 20);
      }
      cues.push(cue);
      return cue;
    };
    // transition sound: whoosh sized to the move, starts >= 0.1 s before the cut (move midpoint), peaks on it
    K.trans = function (role, t, dur, o) {
      o = o || {};
      const cutT = t + dur / 2;
      anchors.push({ t: cutT, type: "scene" });
      return K.sfx(role, cutT, { lead: 0.1, cls: "trans", anchor: "scene", db: o.db });
    };
    // cut: a scene change that is not a kit transition (hard cut, camera swap): whoosh peaking on t
    K.cut = function (t, o) { o = o || {}; anchors.push({ t, type: "scene" }); return K.sfx(o.sfx || "whoosh_s", t, { lead: 0.1, cls: "trans", anchor: "scene", db: o.db }); };
    K.beatGrid = function (bpm, offset) { GRID = { p: 60 / bpm, off: offset || 0 }; return K; };
    // dip: bed + ambience near-silent from t to t+dur (the hit lands at t+dur). Consumed by tools/mix_bed.sh (DIPS=...)
    // via tools/kit_cues.mjs; also removes other cues inside the dip. (K.drop is the falling-prop helper.)
    K.dip = function (t, dur) { dips.push({ t, dur: dur || 0.8 }); return K; };
    K.anchor = function (t, type) { anchors.push({ t, type: type || "scene" }); return K; };
    // resolve a helper's sound option: undefined -> default, false -> none, string/array -> that sound
    const snd = (o, key) => {
      if (o && o.sfx !== undefined) {
        // ported old films: a legacy file name on a helper means "the helper's default role" in edit mode
        if (EDIT && typeof o.sfx === "string" && !SFX[o.sfx] && !PAL[o.sfx] && LEGACY_NAMES.test(o.sfx)) return EDIT_DEFAULT[key];
        return o.sfx;
      }
      return EDIT ? EDIT_DEFAULT[key] : DEFAULT_SFX[key];
    };
    const inWord = (t) => words.some((w) => t >= w.start - 0.02 && t <= w.end);

    // ---- edit-mode rules + QA (kit v2). Returns the cues to write. Dropped cues are listed in K.dropped.
    K.dropped = [];
    function editRules() {
      const drop = (c, why) => { c.dropped = why; K.dropped.push({ t: +c.ht.toFixed(2), name: c.name, why }); };
      let list = cues.slice();
      // 1. beat grid: non-transition accents snap to the bed's beat when within 0.12 s
      if (GRID) list.forEach((c) => {
        if (c.cls === "trans" || c.cls === "riser") return;
        const n = Math.round((c.ht - GRID.off) / GRID.p), bt = GRID.off + n * GRID.p;
        if (Math.abs(bt - c.ht) <= 0.12 && bt >= 0) { c.t += bt - c.ht; c.ht = bt; c.snapped = true; }
      });
      // 2. near-silence dips: nothing sounds inside a dip except its closing hit and risers
      dips.forEach((d) => list.forEach((c) => { if (!c.dropped && c.cls !== "riser" && c.ht > d.t && c.ht < d.t + d.dur - 0.05) drop(c, "inside dip"); }));
      // 3. one accent (hit / explicit accent) per sentence besides transitions; priority force > hit > accent
      const starts = [], ends = [];
      words.forEach((w, i) => { if (i === 0 || /[.?!]["')]?$/.test(words[i - 1].text)) starts.push(w.start); });
      const sent = (t) => { let k = 0; for (let i = 0; i < starts.length; i++) if (t >= starts[i] - 0.15) k = i; return k; };
      const prio = (c) => (c.force ? 6 : c.cls === "trans" ? 5 : c.cls === "hit" ? 4 : c.cls === "riser" ? 3 : 2);
      const bySent = {};
      list.filter((c) => !c.dropped && (c.cls === "hit" || c.cls === "accent") && !c.force && !c.layer).forEach((c) => {
        const k = sent(c.ht), p = bySent[k];
        if (!p) bySent[k] = c; else if (prio(c) > prio(p)) { drop(p, "one accent per sentence"); bySent[k] = c; } else drop(c, "one accent per sentence");
      });
      // a riser/hit pair (counter) survives or dies together
      list.forEach((c) => { if (c.pair && c.cls === "riser" && list.some((x) => x.pair === c.pair && x.dropped)) drop(c, "pair dropped"); });
      // 4. no two cues within 0.25 s, except whoosh/riser into a hit and explicit layers
      list = list.filter((c) => !c.dropped).sort((a, b) => a.ht - b.ht);
      const kept = [];
      for (const c of list) {
        const k = kept.filter((x) => Math.abs(x.ht - c.ht) < 0.25 && !x.dropped);
        let bad = false;
        for (const x of k) {
          const ok = c.layer || x.layer || ((x.cls === "trans" || x.cls === "riser") && c.cls === "hit" && c.ht >= x.ht);
          if (!ok) { if (prio(c) > prio(x)) drop(x, "within 0.25 s"); else { bad = true; drop(c, "within 0.25 s"); } }
        }
        if (!bad) kept.push(c);
      }
      return kept.filter((c) => !c.dropped);
    }
    function editQA(out) {
      // anchored = hit time within 0.15 s of a scene change, a reveal helper, or a stressed word
      const NUM = /^(\d|zero|one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion|half|double)/i;
      const pk = words.map((w) => { let m = 0; if (levels) for (let f = Math.floor(w.start * FPS); f <= Math.ceil(w.end * FPS); f++) m = Math.max(m, levels[f] || 0); return m; });
      const sorted = pk.slice().sort((a, b) => a - b), p80 = sorted[Math.floor(sorted.length * 0.8)] || 1;
      const stressed = words.filter((w, i) => NUM.test(w.text) || (levels && pk[i] >= p80 && w.text.length > 3)).map((w) => w.start);
      const near = (t, arr) => arr.some((a) => Math.abs(a - t) <= 0.15);
      const rows = out.map((c) => {
        const why = near(c.ht, anchors.filter((a) => a.type === "scene").map((a) => a.t)) ? "scene" : near(c.ht, anchors.filter((a) => a.type === "reveal").map((a) => a.t)) ? "reveal" : near(c.ht, stressed) ? "word" : "";
        return { t: +c.ht.toFixed(2), name: c.name, anchored: why || null };
      });
      const n = rows.length, ok = rows.filter((r) => r.anchored).length;
      return { anchoredPct: n ? Math.round((ok / n) * 100) : 100, flagged: rows.filter((r) => !r.anchored), rows };
    }

    K.finish = function () {
      if (EDIT) { const keep = editRules(); cues.length = 0; keep.forEach((c) => cues.push(c)); }
      cues.sort((a, b) => a.t - b.t);
      const out = [];
      for (const c of cues) {
        const prev = out[out.length - 1];
        if (prev && prev.name === c.name && c.t - prev.t < 0.05) continue; // identical double hit
        let db = ROLE_DB[c.meta.role] !== undefined ? ROLE_DB[c.meta.role] : -16;
        db += clamp((-21 - c.meta.rms_db) / 2, -4, 4); // half-way loudness matching between files
        db += c.db;
        if (prev && c.t - prev.t < 0.06) db -= 3; // pile-up: the later hit steps back
        if (c.meta.role !== "loop" && inWord(c.t)) db -= 2; // under speech: slightly lower
        c.volume = (c.vol !== undefined ? c.vol : Math.pow(10, db / 20)) * sfxGain0();
        out.push(c);
      }
      out.forEach((c, i) => {
        const a = document.createElement("audio");
        a.id = "kit-sfx-" + i;
        a.className = "clip kit-sfx";
        a.setAttribute("data-start", c.t.toFixed(3));
        a.setAttribute("data-duration", (c.dur || c.meta.dur).toFixed(3));
        a.setAttribute("data-volume", clamp(c.volume, 0, 2).toFixed(3));
        a.setAttribute("data-track-index", String(10 + (i % 6)));
        if (c.meta.role === "loop") { a.setAttribute("data-fade-in", "0.3"); a.setAttribute("data-fade-out", "0.3"); }
        a.setAttribute("data-sfx", c.name);
        a.src = sfxBase + c.meta.file;
        root.appendChild(a);
      });
      const dur = parseFloat(root.getAttribute("data-duration")) || (out.length ? out[out.length - 1].t : 1);
      K.cueReport = { count: out.length, perMinute: Math.round((out.length / dur) * 60), cues: out.map((c) => ({ t: +c.t.toFixed(2), name: c.name, vol: +c.volume.toFixed(3) })) };
      if (EDIT) { const q2 = editQA(out); Object.assign(K.cueReport, { mode: "edit", anchoredPct: q2.anchoredPct, flagged: q2.flagged, rows: q2.rows, dropped: K.dropped, dips: dips, anchors: anchors }); root.setAttribute("data-kit-qa", q2.anchoredPct + "% anchored; " + q2.flagged.length + " flagged"); }
      window.__kitCues = K.cueReport;
      root.setAttribute("data-kit-sfx", out.map((c) => c.t.toFixed(2) + ":" + c.name).join(" "));
      return K.cueReport;
    };

    // ------------------------------------------------------------------------------- basic motion
    // (pop / label / out / drawOn / enter / bump / fly / push keep the feel of the hand_opus helpers)
    K.pop = function (sel, t, o) {
      o = o || {};
      const els = $$(sel), each = o.stagger || 0;
      tl.fromTo(els, { scale: o.from !== undefined ? o.from : 0.2, opacity: 0 },
        { scale: 1, opacity: 1, duration: o.dur || 0.35, ease: `back.out(${o.overshoot || 2.2})`, stagger: each, immediateRender: true }, t);
      const s = snd(o, "pop");
      if (s) els.forEach((_, i) => { if (i < (o.maxSfx || 8)) K.sfx(s, t + i * each, { key: "pop", db: (o.db || 0) - Math.min(i, 3) }); });
      return K;
    };
    K.label = function (sel, t, o) {
      o = o || {};
      tl.fromTo(sel, { y: 60, opacity: 0 }, { y: 0, opacity: 1, duration: 0.3, ease: "power3.out", immediateRender: true }, t);
      if (o.sfx) K.sfx(o.sfx === true ? DEFAULT_SFX.label : o.sfx, t);
      return K;
    };
    K.out = (sel, t, d) => (tl.to(sel, { opacity: 0, duration: d || 0.25, ease: "power1.in" }, t), K);
    K.popOut = (sel, t) => (tl.to(sel, { scale: 0.6, opacity: 0, duration: 0.18, ease: "back.in(2)" }, t), K);
    K.enter = function (sel, t, fromX, o) {
      tl.fromTo(sel, { x: fromX, y: 40, opacity: 0 }, { x: 0, y: 0, opacity: 1, duration: 0.45, ease: "back.out(1.6)", immediateRender: true }, t);
      if (EDIT ? o && o.sfx : !o || o.sfx !== false) K.sfx((o && o.sfx) || "swish_3", t + 0.05);
      return K;
    };
    K.bump = function (sel, t, s) {
      tl.to(sel, { scale: s || 1.08, duration: 0.12, ease: "sine.out" }, t);
      tl.to(sel, { scale: 1, duration: 0.18, ease: "sine.in" }, t + 0.12);
      return K;
    };
    K.push = function (sel, t0, d, from, to, x0, y0, x, y) { // slow camera push/pan on a .cam wrapper
      tl.fromTo(sel, { scale: from === undefined ? 1 : from, x: x0 || 0, y: y0 || 0 },
        { scale: to === undefined ? 1.08 : to, x: x || 0, y: y || 0, duration: d, ease: "power1.inOut", immediateRender: t0 === 0 }, t0);
      return K;
    };
    // fly: element travels dx,dy along an arc (lifted by o.lift px) and vanishes on arrival (coin into a building).
    // The sound, if any, lands on arrival.
    K.fly = function (sel, t, dx, dy, o) {
      o = o || {};
      const d = o.dur || 0.55, lift = o.lift === undefined ? 110 : o.lift, DY = Math.abs(dy) < 1 ? 1 : dy;
      tl.fromTo(sel, { x: 0, opacity: 0 }, { x: dx, opacity: 1, duration: d, ease: "sine.inOut", immediateRender: true }, t);
      tl.fromTo(sel, { y: 0 }, { y: DY, duration: d, ease: (p) => p - (lift / DY) * 4 * p * (1 - p), immediateRender: true }, t);
      if (o.spin) tl.fromTo(sel, { rotation: 0 }, { rotation: o.spin, duration: d, ease: "none", immediateRender: true }, t);
      if (o.keep !== true) tl.to(sel, { opacity: 0, scale: 0.6, duration: 0.08 }, t + d);
      if (o.sfx) K.sfx(o.sfx, t + d - 0.02, { key: "fly", db: o.db });
      return K;
    };
    // drop with bounce: falls from above, squashes on contact, settles; dust puff + thud on the contact frame
    K.drop = function (sel, t, o) {
      o = o || {};
      const el = $(sel), d = o.dur || 0.3, tc = q(t + d);
      tl.fromTo(el, { y: o.from !== undefined ? o.from : -520, opacity: 0 }, { y: 0, opacity: 1, duration: d, ease: "power2.in", immediateRender: true }, t);
      tl.set(el, { transformOrigin: "50% 100%" }, 0);
      tl.to(el, { scaleY: 0.84, scaleX: 1.12, duration: 0.07, ease: "power2.out" }, tc);
      tl.to(el, { scaleY: 1.06, scaleX: 0.97, duration: 0.11, ease: "sine.out" }, tc + 0.07);
      tl.to(el, { scaleY: 1, scaleX: 1, duration: 0.16, ease: "sine.inOut" }, tc + 0.18);
      const s = snd(o, "drop");
      if (EDIT) { if (s) { anchors.push({ t: tc, type: "reveal" }); K.sfx(s, tc, { key: "drop", db: o.db, anchor: "reveal", force: o.force }); } }
      else if (s) K.sfx(s, tc - 0.01, { key: "drop", db: o.db });
      if (o.puff !== false) {
        const b = box(el);
        K.puff(b.x + b.w / 2, b.y + b.h, tc, { parent: el.offsetParent || root, spread: Math.max(60, b.w * 0.45) });
      }
      return K;
    };
    // stamp / slam: scales down fast onto the page, shakes on contact, burst of rays, punchy sound
    K.stamp = function (sel, t, o) {
      o = o || {};
      const el = $(sel), d = o.dur || 0.1, tc = q(t + d);
      tl.fromTo(el, { scale: o.from || 2.2, opacity: 0, rotation: (o.rot !== undefined ? o.rot : -8) - 6 },
        { scale: 1, opacity: 1, rotation: o.rot !== undefined ? o.rot : -8, duration: d, ease: "power4.in", immediateRender: true }, t);
      tl.to(el, { scale: 1.06, duration: 0.05, ease: "sine.out" }, tc);
      tl.to(el, { scale: 1, duration: 0.12, ease: "sine.inOut" }, tc + 0.05);
      const s = snd(o, "stamp");
      if (EDIT) {
        if (s) { anchors.push({ t: tc, type: "reveal" }); K.sfx(s, tc, { key: "stamp", db: o.db, anchor: "reveal", force: o.force });
          if (o.big) K.sfx("subhit", tc, { db: -2, anchor: "reveal", layer: true }); } // o.big: sub-hit layered under the impact
      } else if (s) K.sfx(s, tc - 0.01, { key: "stamp", db: o.db });
      if (o.shake) K.shake(o.shake, tc, { amp: o.amp || 8 });
      if (o.rays !== false) { const b = box(el); K.rays(b.x + b.w / 2, b.y + b.h / 2, tc, { parent: el.offsetParent || root, r: Math.max(b.w, b.h) * 0.75, color: o.color }); }
      return K;
    };
    // draw-on: every path/line/polyline/circle in the SVG draws itself in order; pencil sound for the duration
    K.draw = function (svgSel, t, o) {
      o = o || {};
      const each = o.each || 0.5, gap = o.gap === undefined ? 0.12 : o.gap;
      const shapes = $$(typeof svgSel === "string" ? svgSel + " path," + svgSel + " line," + svgSel + " polyline," + svgSel + " circle," + svgSel + " rect," + svgSel + " ellipse" : svgSel);
      shapes.forEach((p, i) => {
        const L = Math.ceil(p.getTotalLength()) + 2;
        p.style.strokeDasharray = L;
        tl.fromTo(p, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: each, ease: o.ease || "power1.inOut", immediateRender: true }, t + i * gap);
      });
      const total = each + gap * Math.max(0, shapes.length - 1);
      const s = snd(o, "draw");
      if (s) K.sfx(s, t + 0.03, { len: total, db: o.db });
      return total;
    };
    // red X drawn over a thing: two strokes, one sound per stroke is too much; one hit on the second stroke
    K.cross = function (svgSel, t, o) {
      o = o || {};
      const shapes = $$(svgSel + " path," + svgSel + " line");
      shapes.forEach((p, i) => {
        const L = Math.ceil(p.getTotalLength()) + 2;
        p.style.strokeDasharray = L;
        tl.fromTo(p, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: 0.14, ease: "power3.in", immediateRender: true }, t + i * 0.13);
      });
      const tc = q(t + 0.13 + 0.14);
      const s = snd(o, "cross");
      if (EDIT) { if (s) { anchors.push({ t: tc, type: "reveal" }); K.sfx(s, tc, { key: "stamp", db: o.db, anchor: "reveal", force: o.force }); } }
      else if (s) { K.sfx("swish_1", t, { db: -3 }); K.sfx(s, tc - 0.01, { key: "stamp", db: o.db }); }
      if (o.shake) K.shake(o.shake, tc, { amp: 6 });
      return K;
    };

    // ------------------------------------------------------------------------------- secondary motion
    function box(el) { // layout box relative to offsetParent, ignoring transforms (works for HTML and positioned <svg>)
      if (el.offsetWidth !== undefined) return { x: el.offsetLeft, y: el.offsetTop, w: el.offsetWidth, h: el.offsetHeight };
      const cs = getComputedStyle(el);
      return { x: parseFloat(cs.left) || 0, y: parseFloat(cs.top) || 0, w: parseFloat(cs.width) || 0, h: parseFloat(cs.height) || 0 };
    }
    K.box = (sel) => box($(sel));
    // wobble: decaying rotation after something lands or is hit
    K.wobble = function (sel, t, o) {
      o = o || {};
      const deg = o.deg || 6, n = o.cycles || 3, d = (o.dur || 0.6) / (n * 2);
      for (let i = 0; i < n * 2; i++) {
        const a = deg * Math.pow(0.6, i) * (i % 2 ? -1 : 1);
        tl.to(sel, { rotation: (o.base || 0) + (i === n * 2 - 1 ? 0 : a), duration: d, ease: "sine.inOut" }, t + i * d);
      }
      return K;
    };
    // shake: short decaying horizontal shake (screen or object) on an impact. Under 0.25 s.
    K.shake = function (sel, t, o) {
      o = o || {};
      const amp = o.amp || 8, n = 5, d = (o.dur || 0.2) / n;
      for (let i = 0; i < n; i++) tl.to(sel, { x: (o.baseX || 0) + (i === n - 1 ? 0 : amp * (1 - i / n) * (i % 2 ? 1 : -1)), duration: d, ease: "sine.inOut" }, t + i * d);
      return K;
    };
    // squash: quick squash-and-recover, 0.26 s (thing receives a coin, gets bumped). Space repeats >= 0.27 s apart.
    K.squash = function (sel, t, o) {
      o = o || {};
      const k = o.amount || 0.1;
      tl.to(sel, { scaleY: 1 - k, scaleX: 1 + k * 0.8, duration: 0.06, ease: "power2.out" }, t);
      tl.to(sel, { scaleY: 1 + k * 0.4, scaleX: 1 - k * 0.25, duration: 0.08, ease: "sine.out" }, t + 0.06);
      tl.to(sel, { scaleY: 1, scaleX: 1, duration: 0.12, ease: "sine.inOut" }, t + 0.14);
      return K;
    };
    // float / sway: idle life for a prop between events. Finite yoyo, ends where it started.
    K.float = function (sel, t0, t1, o) {
      o = o || {};
      const half = (o.period || 3) / 2, n = Math.max(1, Math.floor((t1 - t0) / half));
      const vars = { duration: (t1 - t0) / (n % 2 ? n + 1 : n), ease: "sine.inOut", yoyo: true, repeat: (n % 2 ? n + 1 : n) - 1 };
      if (o.y !== 0) vars.y = o.y || -8;
      if (o.rot) vars.rotation = o.rot;
      if (o.x) vars.x = o.x;
      tl.to(sel, vars, t0);
      return K;
    };
    // breathe: chest-rise idle for a character wrapper (transform origin at the feet)
    K.breathe = function (sel, t0, t1, o) {
      o = o || {};
      const half = (o.period || 3.4) / 2;
      let n = Math.max(2, Math.round((t1 - t0) / half)); if (n % 2) n++;
      tl.set(sel, { transformOrigin: "50% 100%" }, 0);
      tl.to(sel, { scaleY: 1 + (o.amp || 0.012), scaleX: 1 - (o.amp || 0.012) * 0.4, duration: (t1 - t0) / n, ease: "sine.inOut", yoyo: true, repeat: n - 1 }, t0);
      return K;
    };
    // puff: dust circles thrown sideways from a landing point
    K.puff = function (x, y, t, o) {
      o = o || {};
      const parent = $(o.parent) || fxParent(), n = o.n || 4, spread = o.spread || 90, size = o.size || 38;
      for (let i = 0; i < n; i++) {
        const side = i % 2 ? 1 : -1, k = 0.55 + 0.45 * ((i >> 1) / Math.max(1, (n >> 1) - 1 || 1));
        const e = mk("div", "kit-puff", parent, `left:${x - size / 2}px;top:${y - size / 2}px;width:${size}px;height:${size}px;` + (o.color ? `background:${o.color};` : ""));
        tl.fromTo(e, { x: side * spread * 0.25, y: 0, scale: 0.4, opacity: 0 },
          { x: side * spread * k, y: -22 * k, scale: 1 + 0.5 * k, opacity: 0.9, duration: 0.22, ease: "power2.out", immediateRender: true }, t);
        tl.to(e, { x: side * spread * (k + 0.25), y: -34 * k, scale: 1.4 + 0.5 * k, opacity: 0, duration: 0.32, ease: "sine.out" }, t + 0.22);
      }
      return K;
    };
    // rays: radial burst lines on a reveal or an impact (0.45 s)
    K.rays = function (x, y, t, o) {
      o = o || {};
      const parent = $(o.parent) || fxParent(), n = o.n || 10, r = o.r || 120, len = o.len || r * 0.32;
      const wrap = mk("div", "kit-rays", parent, `left:${x}px;top:${y}px;`);
      for (let i = 0; i < n; i++) {
        const a = (360 / n) * i + (o.turn || 9), L = len * (i % 2 ? 0.7 : 1);
        const e = mk("div", "kit-ray", wrap, `width:${L}px;transform:rotate(${a}deg) translateX(${r * 0.72}px);` + (o.color ? `background:${o.color};` : "") + (o.thick ? `height:${o.thick}px;margin-top:${-o.thick / 2}px;` : ""));
        e.dataset.a = a;
      }
      tl.fromTo(wrap, { scale: 0.45, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.12, ease: "power2.out", immediateRender: true }, t);
      tl.to(wrap, { scale: 1.18, opacity: 0, duration: 0.3, ease: "power1.in" }, t + 0.15);
      return K;
    };
    // sparkle: 4-point stars twinkling around a point (value, success, "it worked")
    K.sparkle = function (x, y, t, o) {
      o = o || {};
      const parent = $(o.parent) || fxParent(), n = o.n || 5, r = o.r || 90, R = rng(o.seed || Math.round(x * 7 + y * 13));
      for (let i = 0; i < n; i++) {
        const a = (Math.PI * 2 * i) / n + R() * 0.8, d = r * (0.6 + R() * 0.5), s = (o.size || 34) + R() * 30;
        const e = mk("div", "kit-spark", parent, `left:${x + Math.cos(a) * d - s / 2}px;top:${y + Math.sin(a) * d - s / 2}px;width:${s}px;height:${s}px;` + (o.color ? `background:${o.color};` : ""));
        const ti = t + i * 0.05;
        tl.fromTo(e, { scale: 0, opacity: 0, rotation: 0 }, { scale: 1, opacity: 1, rotation: 45, duration: 0.16, ease: "back.out(3)", immediateRender: true }, ti);
        tl.to(e, { scale: 0, opacity: 0, rotation: 90, duration: 0.26, ease: "power1.in" }, ti + 0.22);
      }
      if (o.sfx) K.sfx(o.sfx === true ? "ding_1" : o.sfx, t);
      return K;
    };
    // hand-drawn circle around an element (or explicit box); draws on with a marker sound
    K.circle = function (target, t, o) {
      o = o || {};
      const b = target.w !== undefined ? target : box($(target)), parent = $(o.parent) || (target.w !== undefined ? fxParent() : $(target).offsetParent || $(target).parentNode) || root;
      const pad = o.pad === undefined ? 18 : o.pad, w = b.w + pad * 2, h = b.h + pad * 2, cx = w / 2, cy = h / 2, rx = w / 2, ry = h / 2;
      const s = svgEl(parent, w, h, `left:${b.x - pad}px;top:${b.y - pad}px;z-index:${o.z || 30};`);
      // one and a bit turns, slightly off-centre so it reads as drawn by hand
      const d = `M${cx - rx * 0.92} ${cy - ry * 0.35}C${cx - rx * 0.6} ${cy - ry * 1.18} ${cx + rx * 0.75} ${cy - ry * 1.15} ${cx + rx * 0.98} ${cy - ry * 0.1}` +
        `C${cx + rx * 1.12} ${cy + ry * 0.95} ${cx - rx * 0.55} ${cy + ry * 1.2} ${cx - rx * 0.98} ${cy + ry * 0.3}C${cx - rx * 1.12} ${cy - ry * 0.45} ${cx - rx * 0.5} ${cy - ry * 1.02} ${cx + rx * 0.1} ${cy - ry * 1.05}`;
      const p = document.createElementNS(NS, "path");
      p.setAttribute("d", d); p.setAttribute("fill", "none"); p.setAttribute("stroke", o.color || "#c0463a");
      p.setAttribute("stroke-width", o.width || 9); p.setAttribute("stroke-linecap", "round");
      s.appendChild(p);
      const L = Math.ceil(p.getTotalLength()) + 2;
      p.style.strokeDasharray = L;
      tl.fromTo(p, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: o.dur || 0.42, ease: "power2.inOut", immediateRender: true }, t);
      if (o.until) tl.to(s, { opacity: 0, duration: 0.2 }, o.until);
      const sn = snd(o, "circle");
      if (sn) K.sfx(sn, t + 0.02, { db: o.db });
      return s;
    };
    // hand-drawn underline under an element; draws left to right
    K.underline = function (target, t, o) {
      o = o || {};
      const b = target.w !== undefined ? target : box($(target)), parent = $(o.parent) || (target.w !== undefined ? fxParent() : $(target).offsetParent || $(target).parentNode) || root;
      const w = b.w + 16, s = svgEl(parent, w, 30, `left:${b.x - 8}px;top:${b.y + b.h + (o.gap === undefined ? 2 : o.gap)}px;z-index:${o.z || 30};`);
      const p = document.createElementNS(NS, "path");
      p.setAttribute("d", `M4 14Q${w * 0.35} 4 ${w * 0.62} 13T${w - 4} 10`);
      p.setAttribute("fill", "none"); p.setAttribute("stroke", o.color || "#c0463a"); p.setAttribute("stroke-width", o.width || 9); p.setAttribute("stroke-linecap", "round");
      s.appendChild(p);
      const L = Math.ceil(p.getTotalLength()) + 2;
      p.style.strokeDasharray = L;
      tl.fromTo(p, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: o.dur || 0.3, ease: "power2.out", immediateRender: true }, t);
      if (o.until) tl.to(s, { opacity: 0, duration: 0.2 }, o.until);
      const sn = snd(o, "underline");
      if (sn) K.sfx(sn, t + 0.02, { db: (o.db || 0) - 2 });
      return s;
    };
    // counter: number rolls up, ticking, and lands with a ding and a small bump
    K.counter = function (sel, t, o) {
      const el = $(sel), from = o.from || 0, to = o.to, d = o.dur || 0.9, st = { v: from };
      const fmt = o.fmt || ((v) => (o.prefix || "") + Math.round(v).toLocaleString("en-US") + (o.suffix || ""));
      el.textContent = fmt(from);
      tl.fromTo(st, { v: from }, { v: to, duration: d, ease: o.ease || "power2.out", immediateRender: true, onUpdate: () => { el.textContent = fmt(st.v); } }, t);
      if (EDIT) {
        // edit mode: no ticks. A soft riser over the count (when it is long enough) + one hit on the final number.
        if (o.sfx !== false) {
          const pr = "c" + (++uid);
          anchors.push({ t: t + d, type: "reveal" });
          if (d >= 1.2 && o.riser !== false) K.sfx("riser", t + d, { db: -4, pair: pr, anchor: "reveal", notBefore: t - 0.3 });
          K.sfx(typeof o.sfx === "string" ? o.sfx : "boom", t + d, { db: -3, pair: pr, anchor: "reveal", force: o.force });
        }
      } else {
        if (o.tick !== false) for (let k = 0, n = Math.floor(d / 0.075); k < n; k++) K.sfx(DEFAULT_SFX.counterTick, t + k * 0.075, { key: "tick", db: -2 });
        if (o.sfx !== false) K.sfx(o.sfx || DEFAULT_SFX.counterEnd, t + d);
      }
      K.bump(el, t + d, 1.12);
      return K;
    };
    // each: K.each(".phone", 0.8, 0.06, (el, t, i) => K.pop(el, t))  — explicit stagger with per-item code
    K.each = function (sel, t, each, fn) { $$(sel).forEach((el, i) => fn(el, t + i * each, i)); return K; };

    // ------------------------------------------------------------------------------- transitions
    // Cut ~0.12 s before the first word of the new beat. The whoosh starts with the move.
    K.whip = function (inSel, outSel, t, o) {
      o = o || {};
      const dir = o.dir === "right" ? -1 : 1;
      tl.fromTo(inSel, { x: 1920 * dir }, { x: 0, duration: 0.42, ease: "power3.inOut", immediateRender: true }, t);
      if (outSel) tl.to(outSel, { x: -900 * dir, duration: 0.42, ease: "power3.inOut" }, t);
      const s = snd(o, "whip"); if (s) { if (EDIT) K.trans(s, t, 0.42, o); else K.sfx(s, t + 0.06); }
      return K;
    };
    K.wipe = function (inSel, t, o) {
      o = o || {};
      const from = o.dir === "right" ? "inset(0% 100% 0% 0%)" : o.dir === "down" ? "inset(0% 0% 100% 0%)" : "inset(0% 0% 0% 100%)";
      tl.fromTo(inSel, { clipPath: from }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.45, ease: "power3.inOut", immediateRender: true }, t);
      const s = snd(o, "wipe"); if (s) { if (EDIT) K.trans(s, t, 0.45, o); else K.sfx(s, t + 0.08); }
      return K;
    };
    K.zoomThrough = function (inSel, outSel, t, o) {
      o = o || {};
      if (outSel) tl.to(outSel, { scale: 1.8, opacity: 0, duration: 0.4, ease: "power2.in" }, t);
      tl.fromTo(inSel, { scale: 0.7, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.42, ease: "power2.out", immediateRender: true }, t);
      const s = snd(o, "zoomThrough"); if (s) { if (EDIT) K.trans(s, t, 0.42, o); else K.sfx(s, t + 0.04); }
      return K;
    };

    // ------------------------------------------------------------------------------- real media
    // Real logos / photos / archival footage (fetched with tools/fetch_media.py, credited in CREDITS.md).
    // They must look like objects in the cartoon world, not pasted screenshots:
    //   <div class="kit-sticker" id="lg"><img src="assets/media/logo_delta.png" alt=""></div>          die-cut sticker
    //   <figure class="kit-photo" id="ph"><img src="..."><figcaption>Tesla Model 3</figcaption>
    //           <small class="kit-credit">Photo: A. Author / CC BY-SA 4.0</small></figure>           taped print
    //   <div class="kit-tv" id="tv"><video class="clip" data-start=".." data-duration=".." muted src=".."></video></div>
    // Size the wrapper (width) in the page; images fill it. Keep the named entity's TEXT as a .label caption at most.
    // sticker: slap-on pop with overshoot + a small rotation settle, pop sound, sparkle as the one secondary effect
    K.sticker = function (sel, t, o) {
      o = o || {};
      const el = $(sel), rot = o.rot !== undefined ? o.rot : -4, tc = q(t + 0.24);
      tl.fromTo(el, { scale: 0.15, opacity: 0, rotation: rot - 14 },
        { scale: 1, opacity: 1, rotation: rot, duration: 0.36, ease: "back.out(2.4)", immediateRender: true }, t);
      const s = snd(o, "sticker");
      if (s) K.sfx(s, t, { key: "sticker", db: o.db });
      if (o.sparkle !== false) { const b = box(el); K.sparkle(b.x + b.w / 2, b.y + b.h / 2, tc, { parent: el.offsetParent || root, r: Math.max(b.w, b.h) * 0.62, n: 4, seed: o.seed || 3 }); }
      return K;
    };
    // photo: a print dropped onto the board — falls a little with rotation, lands (squash), tape slaps on;
    // paper sound on contact, small dust puff as the secondary effect
    K.photo = function (sel, t, o) {
      o = o || {};
      const el = $(sel), rot = o.rot !== undefined ? o.rot : 3, d = o.dur || 0.32, tc = q(t + d);
      tl.set(el, { transformOrigin: "50% 60%" }, 0);
      tl.fromTo(el, { y: -160, scale: 1.18, opacity: 0, rotation: rot - 9 },
        { y: 0, scale: 1, opacity: 1, rotation: rot, duration: d, ease: "power2.in", immediateRender: true }, t);
      tl.to(el, { scaleY: 0.96, scaleX: 1.025, duration: 0.06, ease: "power2.out" }, tc);
      tl.to(el, { scaleY: 1, scaleX: 1, duration: 0.16, ease: "back.out(2)" }, tc + 0.06);
      const tapes = el.querySelectorAll(".kit-tape");
      if (tapes.length) tl.fromTo(tapes, { scale: 1.6, opacity: 0 }, { scale: 1, opacity: 0.92, duration: 0.1, ease: "power3.in", stagger: 0.06, immediateRender: true }, tc + 0.02);
      const s = snd(o, "photo");
      if (s) K.sfx(s, tc - 0.01, { key: "photo", db: o.db });
      if (o.puff !== false) { const b = box(el); K.puff(b.x + b.w / 2, b.y + b.h, tc, { parent: el.offsetParent || root, spread: b.w * 0.4, n: 4, size: 30 }); }
      return K;
    };
    // tv: an archival-footage screen rolls in from the side and settles; the screen flickers on (white flash)
    K.tv = function (sel, t, o) {
      o = o || {};
      const el = $(sel), from = o.from !== undefined ? o.from : 900, d = 0.42;
      tl.fromTo(el, { x: from, rotation: from > 0 ? 8 : -8, opacity: 1 },
        { x: 0, rotation: o.rot || 0, duration: d, ease: "back.out(1.5)", immediateRender: true }, t);
      let flash = el.querySelector(".kit-tv-flash");
      if (!flash) flash = mk("div", "kit-tv-flash", el);
      tl.fromTo(flash, { opacity: 1 }, { opacity: 0, duration: 0.25, ease: "power2.out", immediateRender: true }, t + d);
      const s = snd(o, "tv");
      if (s) K.sfx(s, t, { key: "tv", db: o.db });
      if (!EDIT) K.sfx("click_1", t + d, { key: "tvon", db: -2 });
      return K;
    };
    // screen: any footage prop. .kit-tv / .kit-crt roll in from the side (K.tv); .kit-phone rises from below and tilts in.
    //   <div class="kit-phone" id="ph" style="width:420px"><video class="clip" data-start data-duration muted src></video></div>
    //   K.screen("#ph", t, { rot: -3 });   split with the host: footage prop on one side, K.host on the other.
    // RULE (check error video_nested_in_timed_element): a <video data-start> must not sit inside an element that also has
    // data-start; wrap the beat in an untimed <div class="scene"> and fade it with GSAP opacity.
    K.screen = function (sel, t, o) {
      o = o || {};
      const el = $(sel);
      if (!el.classList.contains("kit-phone")) return K.tv(sel, t, o);
      const d = 0.4, rot = o.rot || 0;
      tl.fromTo(el, { y: o.fromY !== undefined ? o.fromY : 800, rotation: rot + 9, opacity: 1 },
        { y: 0, rotation: rot, duration: d, ease: "back.out(1.5)", immediateRender: true }, t);
      let flash = el.querySelector(".kit-tv-flash");
      if (!flash) flash = mk("div", "kit-tv-flash", el);
      tl.fromTo(flash, { opacity: 1 }, { opacity: 0, duration: 0.25, ease: "power2.out", immediateRender: true }, t + d);
      if (!EDIT) K.sfx("click_1", t + d, { key: "tvon", db: -2 });
      return K;
    };

    // ------------------------------------------------------------------------------- talking host
    // const host = K.host("#s1host", { poses: { point: "assets/img/host_point_left.webp", shrug: "assets/img/host_shrug.webp" },
    //                                  faces: { point: "host_point_left", shrug: "host_shrug" }, start: "point",
    //                                  offsets: { shrug: 30 } });   // optional px shift per pose so heads line up
    // host.pose("shrug", 5.9); host.talk(0, 11); host.blinks(0, 11, { seed: 3 }); host.breathe(0, 11); host.nod(2.09);
    // The wrapper element must have a fixed height; images are bottom-anchored at height 100% (like .charwrap).
    K.host = function (wrapSel, cfg) {
      const wrap = $(wrapSel);
      wrap.classList.add("kit-host");
      const sway = mk("div", "kit-host-sway", wrap), bob = mk("div", "kit-host-bob", sway), br = mk("div", "kit-host-breathe", bob);
      const mouthDir = cfg.mouthDir || "assets/img/mouth/";
      const poses = {};
      let current = cfg.start || Object.keys(cfg.poses)[0];
      Object.keys(cfg.poses).forEach((name) => {
        const p = mk("div", "kit-pose", br);
        const img = mk("img", "", p); img.src = cfg.poses[name]; img.alt = "";
        const face = FACES[(cfg.faces && cfg.faces[name]) || name] || null;
        const o = { el: p, img, face, mouths: {}, lids: null };
        if (face) {
          const s = document.createElementNS(NS, "svg");
          s.setAttribute("viewBox", `0 0 ${face.w} ${face.h}`);
          s.setAttribute("class", "kit-face");
          const m = face.mouth, key = (cfg.faces && cfg.faces[name]) || name;
          if (face.patches) {
            // painted patches: same artwork, swapped whole (2D "mouth chart"), never a drawn sticker
            Object.keys(face.patches).forEach((k) => {
              const r = face.patches[k], im = document.createElementNS(NS, "image");
              im.setAttribute("href", `${mouthDir}${key}_${k}.webp`);
              im.setAttribute("x", r[0]); im.setAttribute("y", r[1]); im.setAttribute("width", r[2]); im.setAttribute("height", r[3]);
              im.setAttribute("opacity", "0");
              s.appendChild(im);
              if (k === "blink") o.lids = im; else o.mouths[k] = im;
            });
          } else {
            let html = "";
            Object.keys(MOUTHS).forEach((k) => {
              html += `<g class="kit-mouth" data-shape="${k}" opacity="0" transform="translate(${m.x} ${m.y}) rotate(${m.rot}) scale(${m.w / 100})">${MOUTHS[k]}</g>`;
            });
            html += `<g class="kit-lids" opacity="0">` + face.eyes.map((e) =>
              `<g transform="translate(${e.x} ${e.y}) rotate(${e.rot})"><ellipse rx="${e.rx}" ry="${e.ry}" fill="${face.skin}"/>` +
              `<path d="M${-e.rx + 2} ${e.ry * 0.15}Q0 ${e.ry * 0.95} ${e.rx - 2} ${e.ry * 0.15}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/></g>`).join("") + `</g>`;
            s.innerHTML = html;
            const g = {}; s.querySelectorAll(".kit-mouth").forEach((e) => (g[e.dataset.shape] = e));
            o.mouths = { B: g.B, A: g.C, O: g.O, E: g.D }; // SVG fallback: map track shapes to drawn ones
            o.lids = s.querySelector(".kit-lids");
          }
          p.appendChild(s);
        }
        if (cfg.offsets && cfg.offsets[name]) p.style.left = cfg.offsets[name] + "px"; // line poses up (px, at wrapper scale)
        if (name !== current) p.style.opacity = 0;
        poses[name] = o;
      });
      const all = Object.values(poses);
      const H = { wrap, poses, el: bob };
      // swap pose in place: 2-frame crossfade plus a small squash so the change reads as acting, not a glitch
      H.pose = function (name, t, o) {
        o = o || {};
        all.forEach((p) => tl.to(p.el, { opacity: p === poses[name] ? 1 : 0, duration: 0.06, ease: "none" }, t));
        if (o.accent !== false) {
          tl.to(bob, { scaleY: 0.965, scaleX: 1.02, duration: 0.07, ease: "power2.out" }, t);
          tl.to(bob, { scaleY: 1.012, scaleX: 0.995, duration: 0.1, ease: "sine.out" }, t + 0.07);
          tl.to(bob, { scaleY: 1, scaleX: 1, duration: 0.14, ease: "sine.inOut" }, t + 0.17);
        }
        if (o.sfx) K.sfx(o.sfx === true ? DEFAULT_SFX.poseSwap : o.sfx, t, { db: -3 });
        return H;
      };
      // nod: small emphasis dip on a stressed word (use on the 1-2 key words per sentence)
      H.nod = function (t, o) {
        o = o || {};
        tl.to(bob, { y: o.y || 10, rotation: o.rot || 0, duration: 0.09, ease: "power2.out" }, t);
        tl.to(bob, { y: 0, rotation: 0, duration: 0.2, ease: "sine.inOut" }, t + 0.09);
        return H;
      };
      H.hop = function (t, o) { // happy bounce
        o = o || {};
        tl.to(bob, { y: -(o.y || 26), duration: 0.14, ease: "power2.out" }, t);
        tl.to(bob, { y: 0, duration: 0.16, ease: "power2.in" }, t + 0.14);
        return H;
      };
      H.breathe = function (t0, t1, o) { K.breathe(br, t0, t1, o); return H; };
      // blinks: 3 frames closed, every 2.3-4.4 s (seeded), sometimes a double blink
      H.blinks = function (t0, t1, o) {
        o = o || {};
        const R = rng(o.seed || 7), lids = all.filter((p) => p.lids).map((p) => p.lids);
        H.blinkTimes = [];
        if (!lids.length) return H;
        const one = (t) => { t = q(t); H.blinkTimes.push(t); tl.set(lids, { opacity: 1 }, t); tl.set(lids, { opacity: 0 }, t + 0.1); };
        for (let t = t0 + 0.9 + R() * 1.2; t < t1 - 0.2; t += 2.3 + R() * 2.1) { one(t); if (R() < 0.2) one(t + 0.24); }
        (o.at || []).forEach(one); // extra blinks on pose changes / emphasis
        return H;
      };
      // talk: mouth shapes from the word timestamps (+ optional per-frame speech level).
      // Mouth changes at most every 2 frames ("on twos"); closed in gaps > 0.09 s and on b/m/p onsets.
      H.talk = function (t0, t1, o) {
        o = o || {};
        const seq = mouthTrack(words, levels, t0, t1);
        H.mouthTrack = seq;
        const groups = { B: [], A: [], O: [], E: [] };
        all.forEach((p) => Object.keys(groups).forEach((k) => p.mouths[k] && groups[k].push(p.mouths[k])));
        if (!groups.B.length) return H;
        let prev = "rest";
        seq.forEach((s) => {
          if (s.shape === prev) return;
          if (prev !== "rest") tl.set(groups[prev], { opacity: 0 }, s.t);
          if (s.shape !== "rest") tl.set(groups[s.shape], { opacity: 1 }, s.t);
          prev = s.shape;
        });
        if (prev !== "rest") tl.set(groups[prev], { opacity: 0 }, t1);
        // tiny jaw life: 2 px dip on longer words only (pose layer y; nod owns the bob wrapper)
        if (o.bob !== false) {
          const imgs = all.map((p) => p.el);
          words.filter((w) => w.start >= t0 && w.start < t1 && w.end - w.start > 0.22).forEach((w) => {
            tl.to(imgs, { y: 2, duration: 0.08, ease: "sine.out" }, q(w.start));
            tl.to(imgs, { y: 0, duration: 0.16, ease: "sine.inOut" }, q(w.start) + 0.08);
          });
        }
        // head/body drift per phrase (not per word): settle into a new small tilt at each phrase start
        if (o.sway !== false) {
          const R = rng(o.seed || 5), ws = words.filter((w) => w.start >= t0 && w.start < t1);
          tl.set(sway, { transformOrigin: "50% 100%" }, 0);
          let side = R() < 0.5 ? -1 : 1;
          ws.forEach((w, i) => {
            if (i > 0 && w.start - ws[i - 1].end < 0.28) return; // only at phrase starts
            side = -side;
            const amp = o.swayDeg || 0.8;
            tl.to(sway, { rotation: side * amp * (0.45 + 0.55 * R()), x: side * (2 + 3 * R()), duration: 0.7 + 0.4 * R(), ease: "sine.inOut" }, q(Math.max(t0, w.start - 0.15)));
          });
          tl.to(sway, { rotation: 0, x: 0, duration: 0.6, ease: "sine.inOut" }, q(Math.max(t0, t1 - 0.6)));
        }
        return H;
      };
      return H;
    };

    return K;
  }

  // Mouth track: [{t, shape}] with shape in rest|B|A|O|E (B slight, A open "ah", O round, E wide "ee"),
  // frame-snapped, min hold 2 frames. rest <-> A/O/E always passes through B for one step.
  const VOWEL_SHAPE = (ch) => ("ou".includes(ch) ? "O" : "eiy".includes(ch) ? "E" : "A");
  const BIG = (s) => s === "A" || s === "O" || s === "E";
  function mouthTrack(words, levels, t0, t1) {
    const ws = words.filter((w) => w.end > t0 && w.start < t1);
    const frames = []; // one decision per 2 frames
    const step = 2 / FPS;
    for (let t = Math.ceil(t0 / step) * step; t < t1; t += step) {
      const tm = t + step / 2;
      const w = ws.find((x) => tm >= x.start - 0.02 && tm <= x.end + 0.03);
      let shape = "rest";
      if (w) {
        const txt = w.text.toLowerCase().replace(/[^a-z]/g, ""), dur = Math.max(0.06, w.end - w.start), ph = clamp((tm - w.start) / dur, 0, 0.999);
        const vowels = txt.match(/[aeiouy]+/g) || ["a"];
        const syl = Math.max(1, Math.min(vowels.length, Math.round(dur / 0.14) || 1));
        const si = Math.min(syl - 1, Math.floor(ph * syl)), sph = ph * syl - si; // phase inside the syllable
        const vs = VOWEL_SHAPE((vowels[Math.min(vowels.length - 1, si)] || "a")[0]);
        if (/^[bmp]/.test(txt) && tm - w.start < 0.05) shape = "rest"; // lips closed on b/m/p
        else if (levels) {
          const lv = levels[Math.min(levels.length - 1, Math.max(0, Math.round(tm * FPS)))] || 0;
          shape = lv < 0.12 ? "rest" : lv < 0.38 ? "B" : vs;
        } else shape = sph < 0.15 ? "B" : sph < 0.6 ? vs : "B"; // open on the vowel, half-close between syllables
        if (shape === "rest" && tm - w.start > 0.05 && w.end - tm > 0.05) shape = "B"; // never fully shut mid-word
      } else {
        const nxt = ws.find((x) => x.start > tm), prv = [...ws].reverse().find((x) => x.end < tm);
        if (nxt && prv && nxt.start - prv.end < 0.09) shape = "B"; // tiny gap: keep the mouth slightly open
      }
      frames.push({ t: Math.round(t * FPS) / FPS, shape });
    }
    // in-betweens: never snap closed <-> open; open through B, close through B (keeps closure timing)
    for (let i = 1; i < frames.length; i++) {
      if (frames[i - 1].shape === "rest" && BIG(frames[i].shape)) frames[i].shape = "B";
    }
    for (let i = frames.length - 2; i >= 1; i--) {
      if (frames[i + 1].shape === "rest" && BIG(frames[i].shape) && BIG(frames[i - 1].shape)) frames[i].shape = "B";
    }
    return frames;
  }

  window.Kit = { create, rng, FACES, MOUTHS, ROLE_DB, DEFAULT_SFX, mouthTrack };
})();
