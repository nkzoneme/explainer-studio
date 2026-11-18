#!/usr/bin/env python3
"""Build kit/sfx from the stickman Skill's bundled audio library (read-only source).
Each file: mono 44.1 kHz 16-bit WAV, leading silence trimmed so the first transient sits at ~4 ms,
tail trimmed at -45 dB with a 12 ms fade, peak-normalised to -3 dBFS.
Writes sfx/index.json (durations, rms, default gain, license) and sfx/CREDITS.md.
Run: python3 tools/build_sfx.py"""
import json, os, subprocess, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.dirname(HERE)
LIB = os.path.join(KIT, '..', 'ext_stickman', 'skills', 'directing-stickman-videos', 'assets', 'b-audio-library')
SR = 44100; PEAK_DB = -3.0
# kit name -> (library path, role, note). Roles drive default loudness in kit.js.
PICK = {
 # pops / boings (object appears)
 'pop_1': ('audio/kenney-interface/pluck_001.ogg', 'pop', 'short pluck pop'),
 'pop_2': ('audio/kenney-interface/pluck_002.ogg', 'pop', 'short pluck pop, variant'),
 'pop_3': ('audio/kenney-interface/drop_002.ogg', 'pop', 'low soft drop pop'),
 'pop_bubble': ('audio/rubberduck-water-40/bubble_02.ogg', 'pop', 'bubble pop'),
 'boing_1': ('audio/ez-boings/bing_01_0.mp3', 'pop', 'spring up'),
 'boing_2': ('audio/ez-boings/bing_02.mp3', 'pop', 'spring up, variant'),
 # whoosh / swish (fast movement, transitions)
 'swish_1': ('audio/artisticdude-swishes/swish-3.wav', 'whoosh', 'short swish'),
 'swish_2': ('audio/artisticdude-swishes/swish-5.wav', 'whoosh', 'short swish'),
 'swish_3': ('audio/artisticdude-swishes/swish-7.wav', 'whoosh', 'throw swish'),
 'swish_4': ('audio/artisticdude-swishes/swish-9.wav', 'whoosh', 'longest swish, scene transition'),
 'whoosh_air': ('audio/rubberduck-general-100-2/sfx100v2_air_03.ogg', 'whoosh', 'air burst'),
 'riser_air': ('audio/rubberduck-general-100-2/sfx100v2_air_02.ogg', 'riser', '0.9 s air swell, use before a reveal'),
 'zoom_in': ('audio/kenney-interface/maximize_002.ogg', 'whoosh', 'UI grow / zoom in'),
 'zoom_out': ('audio/kenney-interface/minimize_002.ogg', 'whoosh', 'UI shrink / zoom out'),
 # clicks / ticks / typing
 'click_1': ('audio/kenney-interface/click_001.ogg', 'click', 'UI click'),
 'tick_1': ('audio/kenney-interface/tick_001.ogg', 'tick', 'counter tick'),
 'tick_2': ('audio/kenney-interface/tick_002.ogg', 'tick', 'counter tick, variant'),
 'key_1': ('audio/rubberduck-general-100-2/sfx100v2_switch_01.ogg', 'tick', 'key / switch press'),
 'key_2': ('audio/rubberduck-general-100-2/sfx100v2_switch_02.ogg', 'tick', 'key / switch press, variant'),
 'metal_click': ('audio/kenney-rpg/metalClick.ogg', 'click', 'mechanical click (gate, part snapping in)'),
 'latch': ('audio/kenney-rpg/metalLatch.ogg', 'click', 'latch / lock'),
 'camera': ('audio/owlish-home-202/Camera/Camera_01.wav', 'click', 'camera shutter (photo card appears)'),
 # ding / bell / confirm
 'ding_1': ('audio/kenney-interface/confirmation_003.ogg', 'ding', 'bright single ding'),
 'ding_2': ('audio/kenney-interface/confirmation_002.ogg', 'ding', 'two-note confirm'),
 'bell': ('audio/kenney-impact/impactBell_heavy_000.ogg', 'ding', 'bell with ring-out'),
 'glass_ting': ('audio/kenney-impact/impactGlass_light_001.ogg', 'ding', 'tiny glass ting (deliberately small things)'),
 'sting_hit': ('audio/kenney-jingles/jingles_HIT03.ogg', 'sting', 'short musical reveal sting'),
 'sting_pizz': ('audio/kenney-jingles/jingles_PIZZI00.ogg', 'sting', 'short pizzicato sting'),
 # coins / cash
 'coin_1': ('audio/owlish-home-202/Money/Money_02.wav', 'coin', 'coin'),
 'coin_2': ('audio/owlish-home-202/Money/Money_07.wav', 'coin', 'coin'),
 'coin_3': ('audio/owlish-home-202/Money/Money_09.wav', 'coin', 'coin'),
 'coin_4': ('audio/owlish-home-202/Money/Money_12.wav', 'coin', 'coin'),
 'coins_handful': ('audio/kenney-rpg/handleCoins2.ogg', 'coin', 'handful of coins'),
 'coins_pour': ('audio/kenney-rpg/handleCoins.ogg', 'coin', 'coins pouring (0.6 s)'),
 # paper / book
 'paper_place': ('audio/kenney-rpg/bookPlace1.ogg', 'paper', 'card / document slaps down'),
 'page_flip': ('audio/kenney-rpg/bookFlip2.ogg', 'paper', 'page flip'),
 'paper_unroll': ('audio/kenney-rpg/bookFlip1.ogg', 'paper', 'short paper movement'),
 # pencil / marker (line draws itself)
 'scribble_long': ('audio/owlish-home-202/Paper & Stationery/Stationery_07.wav', 'scribble', '1.1 s pencil strokes'),
 'scribble_mid': ('audio/owlish-home-202/Paper & Stationery/Stationery_06.wav', 'scribble', '0.9 s pencil strokes'),
 'scribble_short': ('audio/owlish-home-202/Paper & Stationery/Stationery_05.wav', 'scribble', '0.5 s pencil strokes'),
 'marker': ('audio/owlish-home-202/Paper & Stationery/Stationery_10.wav', 'scribble', '0.4 s marker stroke (circle / underline)'),
 'erase': ('audio/fupi-erase/erase_0.wav', 'scribble', 'eraser rub'),
 # impacts / thuds / stamps
 'thud_soft': ('audio/kenney-impact/impactSoft_medium_001.ogg', 'impact', 'soft landing'),
 'thud_heavy': ('audio/kenney-impact/impactSoft_heavy_000.ogg', 'impact', 'heavy soft landing'),
 'thud_wood': ('audio/kenney-impact/impactWood_heavy_000.ogg', 'impact', 'wooden object lands'),
 'thud_metal': ('audio/kenney-impact/impactMetal_heavy_001.ogg', 'impact', 'metal object lands'),
 'tap_light': ('audio/kenney-impact/impactGeneric_light_001.ogg', 'impact', 'light tap (small object lands)'),
 'stamp_1': ('audio/kenney-impact/impactPunch_heavy_001.ogg', 'stamp', 'stamp / red X slam'),
 'stamp_2': ('audio/kenney-impact/impactPunch_heavy_004.ogg', 'stamp', 'big stamp, variant'),
 'stamp_wood': ('audio/kenney-impact/impactWood_heavy_002.ogg', 'stamp', 'rubber-stamp on desk'),
 'flop': ('audio/kenney-impact/impactPlate_heavy_000.ogg', 'impact', 'thing falls flat'),
 # error / fail / comedy
 'error_buzz': ('audio/kenney-interface/error_006.ogg', 'error', 'low error buzz'),
 'error_double': ('audio/kenney-interface/error_005.ogg', 'error', 'double low error'),
 'splat': ('audio/rubberduck-water-40/slime_03.ogg', 'impact', 'ink splat'),
 'slide_whistle_down': ('audio/joedeshon-slide-whistle/79671__joedeshon__slide-whistle-down-01.wav', 'comedy', 'CC-BY: falling slide whistle (fail gag)'),
 # loop
 'loop_machine': ('audio/rubberduck-general-100-2/sfx100v2_loop_machine_01.ogg', 'loop', 'conveyor / machine bed, keep very low'),
}
# default gain (linear data-volume) per role: voice sits at 1.0. See CRAFT_RULES.md section 1.
def dec(path):
    raw = subprocess.run(['ffmpeg','-v','error','-i',path,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True,check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)
cat = {a['path']: a for a in json.load(open(os.path.join(LIB,'catalog.json')))['assets']}
index = {}; rows = []
for name,(rel,role,note) in PICK.items():
    src = os.path.join(LIB, rel)
    if not os.path.exists(src): raise SystemExit('missing '+rel)
    a = cat[rel]; x = dec(src); pk = np.max(np.abs(x))
    if role != 'loop':
        idx = np.where(np.abs(x) > pk*0.12)[0]; x = x[max(0, idx[0]-int(.004*SR)):]
        h = 441; env = np.array([np.sqrt(np.mean(x[i:i+h]**2)) for i in range(0, len(x), h)])
        act = np.where(env > env.max()*10**(-45/20))[0]; end = min(len(x), (act[-1]+2)*h)
        x = x[:end].copy(); f = min(len(x), int(.012*SR)); x[-f:] *= np.linspace(1,0,f)
    else:
        f = int(.05*SR); x = x.copy(); x[:f] *= np.linspace(0,1,f); x[-f:] *= np.linspace(1,0,f)
    x = x/np.max(np.abs(x))*10**(PEAK_DB/20)
    out = os.path.join(KIT,'sfx',name+'.wav')
    subprocess.run(['ffmpeg','-v','error','-y','-f','f64le','-ar',str(SR),'-ac','1','-i','-','-c:a','pcm_s16le',out], input=x.tobytes(), check=True)
    rms = 20*np.log10(np.sqrt(np.mean(x**2))+1e-12)
    index[name] = {'file':'sfx/'+name+'.wav','role':role,'dur':round(len(x)/SR,3),'rms_db':round(rms,1),'note':note,
                   'license':a['license']['id'],'author':a['author'],'source_id':a['id']}
    rows.append((name,a['title'],a['author'],a['license']['id'],a['license']['url'],a['source_url'],a['original_filename'],a['sha256'][:12],a['license'].get('attribution','')))
json.dump(index, open(os.path.join(KIT,'sfx','index.json'),'w'), indent=1)
open(os.path.join(KIT,'sfx','index.js'),'w').write('/* generated by tools/build_sfx.py */\nwindow.KIT_SFX = '+json.dumps({k:{'file':v['file'],'role':v['role'],'dur':v['dur'],'rms_db':v['rms_db']} for k,v in index.items()})+';\n')
with open(os.path.join(KIT,'sfx','CREDITS.md'),'w') as f:
    f.write('# kit/sfx credits\n\nSource: the bundled audio library of the open-source Skill "directing-stickman-videos" '
            '(`assets/b-audio-library/`, per-item licences in its `catalog.json`). Each recording keeps its own licence.\n\n'
            'Changes made to every file here: converted to mono 44.1 kHz 16-bit WAV, leading silence trimmed to the first transient, '
            'tail trimmed with a 12 ms fade, peak-normalised to -3 dBFS. In a finished video they are additionally level-adjusted and synchronised to picture.\n\n'
            '| Kit file | Original title | Author | Licence | Source | Original file | sha256 (first 12) |\n|---|---|---|---|---|---|---|\n')
    for n,t,au,lic,lu,su,of,sh,_ in rows: f.write(f'| `{n}.wav` | {t} | {au} | [{lic}]({lu}) | {su} | `{of}` | `{sh}` |\n')
    by = [r for r in rows if r[3] != 'CC0-1.0']
    f.write('\n## Attribution required\n\n')
    if not by: f.write('None. Every file is CC0-1.0.\n')
    for n,t,au,lic,lu,su,of,sh,att in by:
        f.write(f'- `{n}.wav`: "{t}" by {au}, licensed under {lic} ({lu}), source {su}. Changes: trimmed, converted to mono WAV, peak-normalised; level-adjusted and synchronised in the video.\n'
                f'  **If a video uses this file, copy this line into the video description.** Library attribution text: {att}\n')
    f.write('\nAll other files: CC0-1.0 (https://creativecommons.org/publicdomain/zero/1.0/), no attribution required. Crediting Kenney (kenney.nl), OwlishMedia, artisticdude, rubberduck, EZduzziteh and fupi is appreciated but optional.\n')
print(len(index),'files'); 
for n,v in index.items(): print(f"{n:20s} {v['role']:8s} {v['dur']:5.2f}s rms {v['rms_db']:6.1f} {v['license']}")
