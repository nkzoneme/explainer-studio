#!/usr/bin/env python3
"""Minimal resumable kie.ai client.

Usage:
  python3 kie.py run <job.json>      # submit once, poll, download; rerun resumes
  python3 kie.py credit

job.json: {"name": "...", "model": "...", "input": {...}, "out": "assets/x.png"}
State is kept in state/<name>.json. createTask is never retried when its outcome is unknown.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
API = "https://api.kie.ai/api/v1"
CREDIT_USD = 0.005


def key() -> str:
    import sys; sys.path.insert(0, str(ROOT)); from envload import get_key
    return get_key("KIE_API_KEY")


def call(method: str, path: str, **kw):
    r = httpx.request(method, API + path, headers={"Authorization": "Bearer " + key()}, timeout=60, **kw)
    body = r.json()
    if body.get("code") != 200:
        raise RuntimeError(f"kie {path} -> {body.get('code')}: {body.get('msg')}")
    return body.get("data")


def save(name: str, st: dict) -> None:
    STATE.mkdir(exist_ok=True)
    tmp = STATE / f"{name}.json.tmp"
    tmp.write_text(json.dumps(st, indent=2, ensure_ascii=False))
    tmp.replace(STATE / f"{name}.json")


def run(job_path: str) -> dict:
    job = json.loads(Path(job_path).read_text())
    name = job["name"]
    sf = STATE / f"{name}.json"
    st = json.loads(sf.read_text()) if sf.exists() else {}

    if st.get("status") == "done":
        print(f"[{name}] already done -> {st['out']}")
        return st
    if st.get("status") == "submitting":
        raise SystemExit(f"[{name}] previous submit outcome unknown; check kie dashboard before retrying (delete state file to force)")

    if not st.get("task_id"):
        st = {"status": "submitting", "model": job["model"], "t_submit": time.time()}
        save(name, st)
        data = call("POST", "/jobs/createTask", json={"model": job["model"], "input": job["input"]})
        st.update(status="submitted", task_id=data["taskId"])
        save(name, st)
        print(f"[{name}] submitted {st['task_id']}")

    while True:
        d = call("GET", "/jobs/recordInfo", params={"taskId": st["task_id"]}) or {}
        state = d.get("state")
        if state in ("success", "fail"):
            break
        print(f"[{name}] {state} ...", flush=True)
        time.sleep(10)

    credits = d.get("creditsConsumed")
    st.update(kie_state=state, credits=credits, cost_usd=round(float(credits) * CREDIT_USD, 4) if credits else None,
              cost_time_ms=d.get("costTime"), wall_s=round(time.time() - st["t_submit"], 1))
    if state == "fail":
        st.update(status="failed", error=f"{d.get('failCode')}: {d.get('failMsg')}")
        save(name, st)
        raise SystemExit(f"[{name}] FAILED {st['error']}")

    raw = d.get("resultJson") or {}
    urls = (json.loads(raw) if isinstance(raw, str) else raw).get("resultUrls") or []
    out = ROOT / job["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", urls[0], timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with open(out, "wb") as fh:
            for chunk in r.iter_bytes():
                fh.write(chunk)
    st.update(status="done", url=urls[0], out=str(out))
    save(name, st)
    print(f"[{name}] done -> {out} | credits={credits} cost=${st['cost_usd']} wall={st['wall_s']}s")
    return st


if __name__ == "__main__":
    if sys.argv[1] == "credit":
        c = call("GET", "/chat/credit")
        print(f"credits={c} (~${float(c) * CREDIT_USD:.2f})")
    else:
        for p in sys.argv[2:]:
            run(p)
