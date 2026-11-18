// Dump the kit cue report of a composition by loading it in headless Chrome (no render).
// Usage: node kit_cues.mjs <film_dir> [out.json]   -> prints mode, count, per-minute, anchored %, flagged cues, dips (DIPS=...)
import fs from "node:fs"; import path from "node:path"; import os from "node:os"; import { createRequire } from "node:module";
const home = os.homedir();
const pw = fs.readdirSync(path.join(home, ".npm/_npx")).map((d) => path.join(home, ".npm/_npx", d, "node_modules/playwright-core")).find((p) => fs.existsSync(p));
const { chromium } = createRequire(import.meta.url)(pw);
const chromeDir = path.join(home, ".cache/hyperframes/chrome/chrome-headless-shell");
const find = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? find(path.join(d, e.name)) : e.name === "chrome-headless-shell" ? [path.join(d, e.name)] : []));
const exe = find(chromeDir)[0];
const dir = path.resolve(process.argv[2]);
const b = await chromium.launch({ executablePath: exe, args: ["--no-sandbox", "--allow-file-access-from-files"] });
const p = await b.newPage(); if (process.env.KIT_DEBUG) p.on("console", (m) => console.error("[page]", m.text())); p.on("pageerror", (e) => console.error("[pageerror]", e.message));
await p.goto("file://" + path.join(dir, "index.html"), { waitUntil: "load" });
await p.waitForFunction("window.__kitCues", null, { timeout: 20000 });
const r = await p.evaluate("window.__kitCues");
await b.close();
if (process.argv[3]) fs.writeFileSync(process.argv[3], JSON.stringify(r, null, 1));
console.log(`mode=${r.mode || "legacy"} cues=${r.count} per_min=${r.perMinute} anchored=${r.anchoredPct ?? "n/a"}%`);
if (r.flagged && r.flagged.length) console.log("flagged: " + r.flagged.map((c) => c.t + ":" + c.name).join(" "));
if (r.dropped && r.dropped.length) console.log("dropped by rules: " + r.dropped.map((c) => c.t + ":" + c.name + "(" + c.why + ")").join(" "));
if (r.dips && r.dips.length) console.log("DIPS=" + r.dips.map((d) => d.t + ":" + d.dur).join(","));
