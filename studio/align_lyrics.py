"""Find when each lyric line is sung.

Listens to every song with a speech-recognition model (faster-whisper), then lines the
recognised words up with the real lyrics, so each lyric line gets a start time.

    python studio/align_lyrics.py path/to/songs path/to/lyrics -o path/to/timing

Songs and lyrics are matched by number: "3.Open the Window.mp3" <-> "3.Open the Window.txt".
Lyrics use Suno's section tags ([Verse 1], [Chorus], ...). Output: one JSON per song,
e.g. timing/3.json = [{"line": "...", "section": "Chorus", "start": 41.2, "end": 45.0}, ...]
"""
import argparse, difflib, json, os, re, subprocess

import numpy as np

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('songs'); ap.add_argument('lyrics')
ap.add_argument('-o', '--out', required=True, help='folder for the timing JSON files')
ap.add_argument('--model', default='medium.en', help='faster-whisper model name or local path')
args = ap.parse_args()

def numbered(folder, exts):
    found = {}
    for f in os.listdir(folder):
        m = re.match(r'^\s*(\d+)\s*[._-]\s*(.+)\.(%s)$' % exts, f, re.I)
        if m: found[int(m.group(1))] = os.path.join(folder, f)
    return found

def norm(w): return re.sub(r"[^a-z0-9]", '', w.lower().replace('’', "'").replace("in'", 'ing'))

def parse_lyrics(path):
    lines, section = [], ''
    for raw in open(path, encoding='utf-8'):
        s = raw.strip()
        m = re.match(r'^\[(.+)\]$', s)
        if m: section = re.sub(r'\s*\d+$', '', m.group(1)); continue
        if s: lines.append({'line': s, 'section': section})
    return lines

def load_audio(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)

from faster_whisper import WhisperModel
model = WhisperModel(args.model, device='cpu', compute_type='int8')
songs, lyrics = numbered(args.songs, 'mp3|wav|m4a|flac'), numbered(args.lyrics, 'txt')
os.makedirs(args.out, exist_ok=True)

for n in sorted(songs):
    if n not in lyrics: print(f'{n}: no lyrics, skipped'); continue
    segs, _ = model.transcribe(load_audio(songs[n]), word_timestamps=True, beam_size=5, condition_on_previous_text=False)
    heard = [(w.start, w.end, norm(w.word)) for s in segs for w in s.words if norm(w.word)]
    lines = parse_lyrics(lyrics[n])
    lyr = [(li, norm(w)) for li, l in enumerate(lines) for w in l['line'].split() if norm(w)]
    sm = difflib.SequenceMatcher(None, [w for _, w in lyr], [w for _, _, w in heard], autojunk=False)
    t_of = {}
    for a, b, size in sm.get_matching_blocks():
        for k in range(size): t_of[a + k] = heard[b + k][:2]
    # each line: first and last matched word
    for li, l in enumerate(lines):
        idx = [i for i, (lj, _) in enumerate(lyr) if lj == li and i in t_of]
        l['start'] = round(t_of[idx[0]][0], 2) if idx else None
        l['end'] = round(t_of[idx[-1]][1], 2) if idx else None
    # lines nobody heard: spread them evenly between their known neighbours
    known = [i for i, l in enumerate(lines) if l['start'] is not None]
    for i, l in enumerate(lines):
        if l['start'] is not None: continue
        prev = max([k for k in known if k < i], default=None); nxt = min([k for k in known if k > i], default=None)
        t0 = lines[prev]['end'] if prev is not None else 0.0
        t1 = lines[nxt]['start'] if nxt is not None else t0 + 4 * (i - (prev or 0))
        span = (nxt if nxt is not None else i + 1) - (prev if prev is not None else -1)
        k = i - (prev if prev is not None else -1)
        l['start'] = round(t0 + (t1 - t0) * k / span, 2); l['end'] = round(l['start'] + 3.0, 2); l['estimated'] = True
    json.dump(lines, open(os.path.join(args.out, f'{n}.json'), 'w'), ensure_ascii=False, indent=1)
    hit = sum(1 for l in lines if not l.get('estimated'))
    print(f'{n}: {hit}/{len(lines)} lines heard')
