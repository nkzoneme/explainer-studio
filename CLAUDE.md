# Explainer Studio

Cartoon-explainer YouTube production with Claude Code: research → script → voice → hand-directed HyperFrames/GSAP chapters → QA → master → Shorts → upload pack.

- First session in a fresh clone, missing keys, or a new channel: skill `explainer-setup`.
- Daily work: skill `explainer-flow` (it calls explainer-research, explainer-direct, explainer-shorts, explainer-channel-style).
- Agents: `explainer-writer` (Opus: script, hook, ch1, final review), `explainer-worker` (Sonnet: most production), `explainer-scout` (Haiku: data pulls).
- Run tools from `explainer/` with the repo venv: `source ../.venv/bin/activate` (or `.venv/bin/python` from the root).
- Never read or print `.env`; keys load through `explainer/envload.py`.
- Never upload, schedule or publish without the user's OK for that item. Budget default ≤ 10 USD per video (voice, images, Shorts included); say what you spent.
- Channel data (`explainer/channels/<slug>/`, brand, music, film/) is gitignored: it stays on this machine.
