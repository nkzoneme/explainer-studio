#!/usr/bin/env python3
"""Audio QA for a rendered beat/film. Usage:
  python3 qa_audio.py <render.mp4> <dry_voice.mp3> [voice_gain_in_mix=1.0]
Reports: integrated loudness of the mix and of the voice alone, the level of everything that is not voice
(SFX bus = mix minus time-aligned voice), SFX-bus-under-voice in dB, and SFX events per minute (onsets in the
residual). Pass targets (CRAFT_RULES section 1): SFX bus 10-18 dB under the voice; no SFX peak above the voice peak."""
import sys, subprocess, re
import numpy as np
SR = 22050
def dec(p):
    return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True,check=True).stdout, dtype=np.float32).astype(np.float64)
def lufs(p):
    e = subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',p,'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
    tail = e[e.rfind('Summary'):]
    return float(re.search(r'I:\s+(-?[\d.]+) LUFS', tail).group(1)), float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', tail).group(1))
def xcorr_full(a, b):
    # same result as np.correlate(a, b, 'full') but FFT-based (the direct form takes minutes on a 20 s window)
    n = len(a) + len(b) - 1; N = 1 << (n - 1).bit_length()
    r = np.fft.irfft(np.fft.rfft(a, N) * np.conj(np.fft.rfft(b, N)), N)
    return np.concatenate([r[N - (len(b) - 1):], r[:len(a)]])
db = lambda x: 20*np.log10(np.sqrt(np.mean(x**2))+1e-12)
mix, vo = dec(sys.argv[1]), dec(sys.argv[2])
seg = min(len(mix), len(vo), SR*20)
c = xcorr_full(mix[:seg][::4], vo[:seg][::4]); lag = (np.argmax(c)-(len(vo[:seg][::4])-1))*4
best = None
for l in range(lag-8, lag+9):
    a = mix[max(0, l):]; b = vo[max(0, -l):]; m = min(len(a), len(b)); g = np.dot(a[:m], b[:m])/np.dot(b[:m], b[:m]); e = np.sum((a[:m]-g*b[:m])**2)
    if best is None or e < best[0]: best = (e, l, g)
_, l, g = best
a = mix[max(0, l):]; b = vo[max(0, -l):]*g; m = min(len(a), len(b)); r = a[:m]-b[:m]
h = int(SR*0.02); env = np.array([db(r[i:i+h]) for i in range(0, len(r)-h, h)])
floor = np.percentile(env, 40); ev = []; last = -9
for i in range(2, len(env)-1):
    if env[i] > max(floor+18, -52) and env[i]-env[i-2] > 8 and i*0.02-last > 0.09: ev.append(round(i*0.02, 2)); last = i*0.02
I, pk = lufs(sys.argv[1]); Iv, pkv = lufs(sys.argv[2])
dur = m/SR
act = env > -50
print(f'mix: {I} LUFS, peak {pk} dBFS | dry voice file: {Iv} LUFS, peak {pkv} dBFS | voice gain in mix x{g:.2f} ({20*np.log10(g):+.1f} dB), lag {l/SR*1000:.0f} ms')
print(f'voice RMS in mix {db(b[:m]):.1f} dB | non-voice (SFX bus) RMS {db(r):.1f} dB | SFX bus is {db(b[:m])-db(r):.1f} dB under the voice (whole-file RMS)')
print(f'loudest SFX 20 ms frame {env.max():.1f} dB vs loudest voice frame {max(db(b[i:i+h]) for i in range(0, m-h, h)):.1f} dB')
print(f'SFX onsets detected: {len(ev)} in {dur:.1f} s = {len(ev)/dur*60:.0f} per minute; share of time with SFX audible: {act.mean()*100:.0f} %')
print('onset times:', ' '.join(str(t) for t in ev))
# Optional 4th/5th argument: cue report from tools/kit_cues.mjs (sound:"edit" films): <cues.json>
# prints the share of cues that sit within 0.15 s of a scene change, a reveal helper or a stressed word (target >= 80 %).
import os, json
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]):
    c = json.load(open(sys.argv[4]))
    if c.get('rows') is not None:
        pct = c['anchoredPct']; fl = c.get('flagged', [])
        print(f"edit-anchored cues: {pct} % of {c['count']} (target >= 80 %) {'OK' if pct >= 80 else 'BELOW TARGET'}; kit cues/min {c['perMinute']}")
        if fl: print('flagged (not on a scene change / reveal / stressed word):', ' '.join(f"{x['t']}:{x['name']}" for x in fl))
        if c.get('dropped'): print('dropped by kit rules:', ' '.join(f"{x['t']}:{x['name']}({x['why']})" for x in c['dropped']))
