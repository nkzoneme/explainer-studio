/* shorts.js - vertical Shorts layer for kit.js compositions (1080x1920).
 *
 *   const S = Shorts.create(K, { words: WORDS, end: END, merge: MERGE, hook: "WHY IS THIS <em>SO EXPENSIVE</em>?",
 *                                card: { at: END - 1.5, line: "FULL STORY ON THE CHANNEL", sub: "My Channel" } });
 *   ... your scene code ...
 *   S.finish();   // before K.finish()
 *
 * Builds: hook title (on screen from frame 0, tiny settle), progress bar, word-by-word captions (2-4 words per line,
 * active word in the accent colour), end card with the channel avatar (assets/img/avatar.png).
 * merge: [["twenty twenty-six,", "2026,"], ["M B A", "MBA"], ...] joins consecutive spoken words into one caption token
 * (digits read faster than spelled-out numbers). Deterministic: everything is placed on the paused timeline. */
(function () {
  "use strict";
  const FPS = 30, q = (t) => Math.round(t * FPS) / FPS;

  function mergeWords(words, rules) {
    const w = words.map((x) => ({ text: x.word || x.text, start: x.start, end: x.end }));
    (rules || []).forEach(([from, to]) => {
      const k = from.split(" ").length;
      for (let i = 0; i + k <= w.length; i++) {
        if (w.slice(i, i + k).map((x) => x.text).join(" ") === from) {
          w.splice(i, k, { text: to, start: w[i].start, end: w[i + k - 1].end });
        }
      }
    });
    return w;
  }

  // 2-4 words per line; break after punctuation, at pauses > 0.25 s, and when the line gets too long
  function chunk(ws, o) {
    const maxW = o.maxWords || 4, maxC = o.maxChars || 16, out = [];
    let cur = [];
    const flush = () => { if (cur.length) out.push(cur); cur = []; };
    ws.forEach((w, i) => {
      const len = cur.map((x) => x.text).join(" ").length + w.text.length + (cur.length ? 1 : 0);
      if (cur.length && (cur.length >= maxW || len > maxC || w.start - cur[cur.length - 1].end > 0.25)) flush();
      cur.push(w);
      const nxt = ws[i + 1];
      const punct = /[.?!:;]$/.test(w.text) || (/,$/.test(w.text) && cur.length >= 2);
      if (punct && !(nxt && cur.length === 1 && /[.?!]$/.test(w.text) === false)) flush();
    });
    flush();
    // never leave a lonely 1-word line when the neighbour can take it (unless it ends a sentence and is long)
    for (let i = out.length - 1; i > 0; i--) {
      if (out[i].length === 1 && out[i - 1].length <= 2 && !/[.?!]$/.test(out[i - 1][out[i - 1].length - 1].text)
          && out[i][0].start - out[i - 1][out[i - 1].length - 1].end < 0.25) { out[i - 1] = out[i - 1].concat(out[i]); out.splice(i, 1); }
    }
    return out;
  }

  function create(K, o) {
    const tl = K.tl, root = K.root, END = o.end;
    const mk = (tag, cls, parent, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html !== undefined) e.innerHTML = html; (parent || root).appendChild(e); return e; };
    const S = { K, end: END };

    // ---- hook title: visible on frame 0 (the first frame is the hook), a soft settle, a nudge on the first stressed word
    const tb = mk("div", "sh-title"); const tt = mk("div", "t", tb, o.hook || "");
    tl.fromTo(tt, { scale: 1.07, rotation: -1.5 }, { scale: 1, rotation: 0, duration: 0.35, ease: "back.out(2.5)", immediateRender: true }, 0);
    S.title = tt;

    // ---- progress bar
    const pb = mk("div", "sh-prog"); const pi = mk("i", "", pb);
    tl.fromTo(pi, { scaleX: 0 }, { scaleX: 1, duration: END, ease: "none", immediateRender: true }, 0);

    // ---- captions
    const caps = mk("div", "sh-caps");
    const ws = mergeWords(K.words.map((w) => ({ word: w.text, start: w.start, end: w.end })), o.merge);
    const chunks = chunk(ws, o.captions || {});
    const capEnd = o.capsUntil || END;
    const MAXW = 880, css = getComputedStyle(root);
    const FILL = css.getPropertyValue("--cap-fill").trim() || "#fff", ON = css.getPropertyValue("--cap-active").trim() || "#e4572e";
    chunks.forEach((c, ci) => {
      const el = mk("div", "sh-chunk", caps);
      const spans = c.map((w, wi) => {
        if (wi) el.appendChild(document.createTextNode(" ")); // real spaces: readers and checkers see words, not "careofthe"
        return mk("span", "", el, w.text.replace(/&/g, "&amp;").replace(/</g, "&lt;"));
      });
      // fit the line into 880 px
      el.style.opacity = 1; let fs = 92;
      while (el.scrollWidth > MAXW && fs > 56) { fs -= 4; el.style.fontSize = fs + "px"; }
      el.style.opacity = 0;
      const t0 = q(Math.max(0, c[0].start - 0.04));
      const nxt = chunks[ci + 1];
      const t1 = Math.min(capEnd, nxt ? q(Math.min(nxt[0].start - 0.04, c[c.length - 1].end + 0.6)) : q(c[c.length - 1].end + 0.5));
      tl.set(el, { opacity: 1 }, t0);
      tl.fromTo(el, { scale: 0.86, y: 10 }, { scale: 1, y: 0, duration: 0.12, ease: "back.out(3)", immediateRender: false }, t0);
      tl.set(el, { opacity: 0 }, t1);
      c.forEach((w, wi) => {
        const a = q(Math.max(t0, w.start - 0.02)), b = wi + 1 < c.length ? q(c[wi + 1].start - 0.02) : t1;
        tl.set(spans[wi], { color: ON }, a);
        tl.fromTo(spans[wi], { scale: 1.12 }, { scale: 1, duration: 0.14, ease: "sine.out", immediateRender: false }, a);
        tl.set(spans[wi], { color: FILL }, b);
      });
    });
    S.chunks = chunks;

    // ---- end card: avatar + "full story" line; pops in, avatar bobs; one pop + one ding
    S.card = function (t, line, sub, dim) {
      if (dim !== false) tl.to(dim || ".sh-scene .cam", { opacity: 0, duration: 0.2, ease: "power1.in" }, t); // stage clears, host stays
      const c = mk("div", "sh-end");
      const im = mk("img", "", c); im.src = o.avatar || "assets/img/avatar.png"; im.alt = "";
      mk("div", "l1", c, line || "FULL STORY ON THE CHANNEL");
      mk("div", "l2", c, sub || "");
      K.pop(c, t, { from: 0.4, sfx: "pop_bubble" });
      tl.fromTo(im, { rotation: -8 }, { rotation: 0, duration: 0.5, ease: "elastic.out(1, 0.4)", immediateRender: false }, t + 0.1);
      K.float(c, t + 0.4, END, { y: -8, period: 1.2 });
      K.sfx("ding_1", t + 0.25, { db: -2 });
      return c;
    };
    S.finish = function (f) {
      f = f || {};
      // phone speakers: a Short may sit its SFX bus a little hotter; target 12-18 dB under the voice (qa_audio.py)
      if (f.sfxGain) K.cues.forEach((c) => { c.db = (c.db || 0) + f.sfxGain; });
      // end card holds >= 2.1 s (HyperFrames' line_unread rule for a closing line): comp END = last word + ~2.3 s
      if (o.card !== false) S.card(o.card && o.card.at !== undefined ? o.card.at : END - 2.15, o.card && o.card.line, o.card && o.card.sub, o.card && o.card.dim);
      // safe-zone overlay boxes (only visible when #root has class sz-on)
      [[0, 0, 1080, 160], [0, 1400, 1080, 520], [950, 960, 130, 576]].forEach(([x, y, w, h]) => {
        const z = mk("div", "sz"); z.style.cssText = `left:${x}px;top:${y}px;width:${w}px;height:${h}px`;
      });
      return S;
    };
    return S;
  }
  // Pose swaps as hard cuts (+ the kit's squash accent). The kit's 0.06 s crossfade puts two half-transparent hosts on one
  // frame; with mirrored poses of different widths that reads as a ghost (seen in the film's ch01 and in the first Shorts).
  // Usage: const host = Shorts.snapPose(K, K.host("#host", {...}));
  function snapPose(K, h) {
    const tl = K.tl;
    h.pose = (name, t) => {
      Object.keys(h.poses).forEach((k) => tl.set(h.poses[k].el, { opacity: k === name ? 1 : 0 }, t));
      tl.to(h.el, { scaleY: 0.965, scaleX: 1.02, duration: 0.07, ease: "power2.out" }, t);
      tl.to(h.el, { scaleY: 1.012, scaleX: 0.995, duration: 0.1, ease: "sine.out" }, t + 0.07);
      tl.to(h.el, { scaleY: 1, scaleX: 1, duration: 0.14, ease: "sine.inOut" }, t + 0.17);
      return h;
    };
    return h;
  }
  window.Shorts = { create, mergeWords, chunk, snapPose };
})();
