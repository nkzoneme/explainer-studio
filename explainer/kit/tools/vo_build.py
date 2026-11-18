#!/usr/bin/env python3
"""Join ElevenLabs chunks made by explainer/fal_tts.py into one voiceover with word timestamps.
Usage:  python3 vo_build.py <out_prefix> <chunk1.mp3> [chunk2.mp3 ...] [--gap 0.35]
Each chunk must have its <chunk>.fal_ts.json next to it (fal_tts.py writes it).
Writes: <out_prefix>.mp3            chunks joined in order, --gap seconds of silence between chunks
        <out_prefix>.words.json     [{"word","start","end"}] in seconds on the joined file
        <out_prefix>.WORDS.txt      word@start lines for the director (12 words per line) + total length
        <out_prefix>.levels.js      window.KIT_LEVELS, per-frame speech level for mouth sync (30 fps)
No paid calls. Timestamps come from the TTS itself (character-level), so no Whisper pass is needed."""
import sys, json, os, subprocess, tempfile
args = sys.argv[1:]; gap = 0.35
if '--gap' in args: i = args.index('--gap'); gap = float(args[i+1]); del args[i:i+2]
prefix, chunks = args[0], args[1:]
HERE = os.path.dirname(os.path.abspath(__file__))
def dur(p): return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p],capture_output=True,text=True,check=True).stdout)
words = []; t0 = 0.0; parts = []
for n, c in enumerate(chunks):
    ts = json.load(open(os.path.splitext(c)[0] + '.fal_ts.json'))
    segs = ts if isinstance(ts, list) else [ts]
    cur = None
    for s in segs:
        for ch, a, b in zip(s['characters'], s['character_start_times_seconds'], s['character_end_times_seconds']):
            if ch.isspace():
                if cur: words.append(cur); cur = None
            elif cur is None: cur = {'word': ch, 'start': round(t0 + a, 3), 'end': round(t0 + b, 3)}
            else: cur['word'] += ch; cur['end'] = round(t0 + b, 3)
    if cur: words.append(cur)
    parts.append(c); t0 += dur(c) + (gap if n < len(chunks) - 1 else 0)
with tempfile.TemporaryDirectory() as td:
    ins = []; flt = []
    for i, p in enumerate(parts): ins += ['-i', p]; flt.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=mono' + (f',apad=pad_dur={gap}' if i < len(parts) - 1 else '') + f'[a{i}]')
    flt.append(''.join(f'[a{i}]' for i in range(len(parts))) + f'concat=n={len(parts)}:v=0:a=1[o]')
    subprocess.run(['ffmpeg','-v','error','-y',*ins,'-filter_complex',';'.join(flt),'-map','[o]','-c:a','libmp3lame','-b:a','192k',prefix + '.mp3'], check=True)
json.dump(words, open(prefix + '.words.json', 'w'))
total = dur(prefix + '.mp3')
with open(prefix + '.WORDS.txt', 'w') as f:
    for i in range(0, len(words), 12): f.write(' '.join(f"{w['word']}@{w['start']:.2f}" for w in words[i:i+12]) + '\n')
    f.write(f'(audio length {total:.2f}s)\n')
subprocess.run([sys.executable, os.path.join(HERE, 'speech_levels.py'), prefix + '.mp3', prefix + '.levels.js'], check=True)
gaps = [(round(words[i]['end'], 2), round(words[i+1]['start'] - words[i]['end'], 2)) for i in range(len(words) - 1) if words[i+1]['start'] - words[i]['end'] > 0.6]
print(f'{len(words)} words, {total:.2f}s, {len(words)/total*60:.0f} wpm; pauses > 0.6 s (at, length): {gaps[:20]}')
