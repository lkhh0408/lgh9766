"""Open to Close video renderer.

Takes a folder of numbered songs ("1.Title.mp3", "2.Title.mp3", ...) and renders one video:
the mascot walks through ever-changing line-art scenery while the sky goes from morning to night.
Between songs the mascot stops, taps the headphones, a play bubble pops up and the next song starts.

    python studio/render_video.py path/to/songs -o out.mp4
"""
import argparse, bisect, math, os, random, re, subprocess, sys, wave
import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import character as ch
import props

ASSETS = os.path.join(HERE, 'assets')
LOGO = os.path.join(ASSETS, 'logo_horizontal.png')

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('songs', help='folder with numbered audio files, e.g. "1.Golden Hour Coffee.mp3"')
ap.add_argument('-o', '--out', default='output.mp4', help='output video path')
ap.add_argument('--gap', type=float, default=1.5, help='seconds of silence between songs')
ap.add_argument('--seed', type=int, default=21, help='scenery seed (change it for a different walk)')
ap.add_argument('--outfit', default='signature', help='mascot outfit from studio/character.py OUTFITS')
ap.add_argument('--stills', help='comma-separated times in seconds: save PNG stills instead of rendering the video')
ap.add_argument('--scenes', help='storyboard JSON with per-song scenes and lyric beats (default: storyboard.json or scenes.json in the songs folder). '
                'Lyric timings are read from a timing/ folder next to it (see align_lyrics.py).')
args = ap.parse_args()

W, H, FPS = 1920, 1080, 24
GY = 760            # ground line
CX = 820            # character x
SPEED = 130         # px/s of the street layer
ZLEN = 1700         # world length of one themed zone
GAP = args.gap      # short pause between songs: stop, tap headphones, next song

def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())

songs = []
for f in os.listdir(args.songs):
    m = re.match(r'^\s*(\d+)\s*[._-]\s*(.+)\.(mp3|wav|m4a|flac)$', f, re.I)
    if m: songs.append((int(m.group(1)), m.group(2).strip(), os.path.join(args.songs, f)))
songs.sort()
if not songs: sys.exit('no numbered songs found in ' + args.songs)
TRACKS = [(f'{i + 1:02d}', title) for i, (_, title, _) in enumerate(songs)]
DURS = [probe(p) for _, _, p in songs]
for (n, t_), d in zip(TRACKS, DURS): print(f'TRACK {n}  {t_}  {int(d // 60)}:{int(d % 60):02d}')

# audio: every song brought to YouTube's -14 LUFS on its own (a fixed gain, so the sound is untouched),
# a limiter that only catches the few peaks the gain pushes over -1.5 dB, a short fade at each end, silence gaps
TARGET_LUFS, CEILING = -14.0, 10 ** (-1.5 / 20)
def loudness(path):
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', out)[-1])
MIX = os.path.splitext(args.out)[0] + '_mix.wav'
cmd = ['ffmpeg', '-y', '-loglevel', 'error']
for _, _, p in songs: cmd += ['-i', p]
for _ in songs[1:]: cmd += ['-f', 'lavfi', '-t', str(GAP), '-i', 'anullsrc=r=48000:cl=stereo']
fl, seq = [], []
for i, ((_, _, p), d) in enumerate(zip(songs, DURS)):
    gain = TARGET_LUFS - loudness(p)
    fl.append(f'[{i}]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={gain:.2f}dB,'
              f'alimiter=limit={CEILING:.4f}:attack=5:release=60:level=disabled,afade=t=out:st={max(0, d - 0.8):.3f}:d=0.8[a{i}]')
    seq.append(f'[a{i}]')
    if i < len(songs) - 1:
        fl.append(f'[{len(songs) + i}]aformat=sample_fmts=fltp:channel_layouts=stereo[g{i}]'); seq.append(f'[g{i}]')
fl.append(''.join(seq) + f'concat=n={len(seq)}:v=0:a=1')
subprocess.run(cmd + ['-filter_complex', ';'.join(fl), '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', MIX], check=True)

with wave.open(MIX) as w:
    TOTAL = w.getnframes() / w.getframerate()
starts = [sum(d + GAP for d in DURS[:i]) for i in range(len(TRACKS))]
ends = [s0 + d for s0, d in zip(starts, DURS)]
def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def motion(t):
    """walk amount, hand reach, tap pulse, bubble (alpha, scale) at time t"""
    walk, reach, press, ba, bs = 1.0, 0.0, 0.0, 0.0, 0.0
    for e, nxt in zip(ends[:-1], starts[1:]):
        if e - 1.6 <= t < nxt + 0.9:
            # slow to a stop while the song fades, tap the headphones, walk on as the next song starts
            walk = min(1 - sm((t - (e - 1.6)) / 1.2), sm((t - (nxt - 0.15)) / 0.9))
            reach = min(sm((t - (e - 0.55)) / 0.45), 1 - sm((t - (e + 0.95)) / 0.45))
            if e - 0.05 <= t < e + 0.3: press = math.sin((t - e + 0.05) / 0.35 * math.pi)
            if t >= e + 0.05:
                k = t - (e + 0.05); bs = min(1.15, k / 0.22 * 1.15) if k < 0.22 else 1.15 - 0.15 * sm((k - 0.22) / 0.18)
                ba = 1.0 - sm((t - (nxt + 0.15)) / 0.5)
    if t >= ends[-1] - 1.2: walk = 1 - sm((t - (ends[-1] - 1.2)) / 1.2)
    return walk, reach, press, ba, bs
rnd = random.Random(args.seed)

def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))
PASTEL = [hexc(c) for c in ('#FFD6E0', '#FFE9A8', '#C9F2E0', '#D7E3FF', '#E8D9FF', '#FFD8B8', '#BFF0F5')]
ACCENT = [hexc(c) for c in ('#FF5C8A', '#FFB21A', '#7B3BFF', '#3D9BFF', '#2EC4A6', '#FF7A45')]

SKY = [(0.00, '#FF9AA2', '#FFD9A0', 0.0), (0.20, '#5EB8FF', '#FFE9C7', 0.0), (0.50, '#3D8BFF', '#BDE4FF', 0.0),
       (0.72, '#8A3BFF', '#FF8A5B', 0.15), (0.86, '#3A2E7A', '#FF5C8A', 0.5), (1.00, '#141B36', '#3D3F78', 1.0)]
def sky_at(u):
    for (u0, t0, b0, d0), (u1, t1, b1, d1) in zip(SKY, SKY[1:]):
        if u <= u1:
            k = (u - u0) / (u1 - u0); k = k * k * (3 - 2 * k)
            return lerp(hexc(t0), hexc(t1), k), lerp(hexc(b0), hexc(b1), k), d0 + (d1 - d0) * k
    return hexc(SKY[-1][1]), hexc(SKY[-1][2]), 1.0

# ---------- themed zones ----------
# each zone kind: which far layer sits behind it
THEMES = {'town': 'skyline', 'park': 'hills', 'shops': 'skyline', 'houses': 'hills',
          'forest': 'treeline', 'beach': 'sea', 'flowers': 'hills', 'market': 'skyline'}
# scene kinds used by per-song plans (scenes.json)
SCENES = {'flowerhouses': 'hills', 'bakery': 'skyline', 'avenue': 'treeline', 'crossing': 'skyline',
          'pianohouse': 'skyline', 'terrace': 'skyline', 'curtainhouses': 'hills', 'goldencafe': 'skyline',
          'neighbors': 'hills', 'openwindows': 'hills', 'cornercoffee': 'skyline', 'downtown': 'skyline'}
FAR = {**THEMES, **SCENES}
GREEN = {'park', 'forest', 'flowers', 'avenue'}

objs = []
def gen_zone(z, x, xe, sign=None):
    """fill world x..xe with objects for zone kind z"""
    zstart = x
    x += 40; xe -= 120
    while x < xe:
        p = rnd.choice(PASTEL); a = rnd.choice(ACCENT)
        if z == 'town':
            w_ = rnd.randint(170, 260); objs.append(('bldg', x, w_, rnd.randint(230, 400), rnd.choice([3, 4]), p)); x += w_ + rnd.randint(20, 50)
            if rnd.random() < 0.35: objs.append(('lamp', x - 10)); x += 40
        elif z == 'park':
            k = rnd.random()
            if k < 0.5: objs.append(('tree', x + 60, rnd.randint(70, 105), rnd.randint(110, 160))); x += rnd.randint(170, 230)
            elif k < 0.75: objs.append(('bush', x + 40, rnd.randint(32, 50))); x += 120
            else: objs.append(('bench', x + 60)); x += 190
        elif z == 'shops':
            w_ = rnd.randint(300, 360); objs.append(('shop', x, w_, sign or rnd.choice(['CAFE', 'BAKERY', 'BOOKS', 'RECORDS', 'FLOWERS']), p, a)); x += w_ + 30
            if rnd.random() < 0.6: objs.append(('table', x + 50, a)); x += 150
        elif z == 'houses':
            w_ = rnd.randint(150, 190); objs.append(('house', x, w_, rnd.randint(120, 160), p, a)); x += w_ + 20
            objs.append(('fence', x, 90)); x += 100
            if rnd.random() < 0.3: objs.append(('tree', x + 50, 60, 100)); x += 130
        elif z == 'forest':
            objs.append(('pine', x + 40, rnd.randint(150, 260))); x += rnd.randint(70, 120)
            if rnd.random() < 0.2: objs.append(('mushroom', x + 10, a)); x += 50
        elif z == 'beach':
            k = rnd.random()
            if k < 0.35: objs.append(('palm', x + 40, rnd.randint(220, 300))); x += 220
            elif k < 0.7: objs.append(('umbrella', x + 50, a)); x += 200
            elif k < 0.85 and not any(o[0] == 'lighthouse' and o[1] > zstart for o in objs): objs.append(('lighthouse', x + 60)); x += 260
            else: objs.append(('sandcastle', x + 40)); x += 150
        elif z == 'flowers':
            if rnd.random() < 0.15: objs.append(('windmill', x + 70)); x += 240
            else: objs.append(('flowers', x, rnd.randint(4, 7))); x += 170
        elif z == 'market':
            objs.append(('stall', x, rnd.randint(200, 240), a, p)); x += 270
            if rnd.random() < 0.3: objs.append(('lamp', x)); x += 60
        # ---- scene kinds (per-song plans)
        elif z == 'flowerhouses':
            w_ = rnd.randint(160, 190); objs.append(('house2', x, w_, rnd.randint(130, 160), p, a, 'flowerbox')); x += w_ + 30
            objs.append(('flowers', x, rnd.randint(3, 4))); x += 110
        elif z in ('bakery', 'goldencafe', 'cornercoffee'):
            items = {'bakery': 'bread', 'goldencafe': 'cups', 'cornercoffee': 'cups'}[z]
            w_ = 380 if z == 'cornercoffee' else rnd.randint(320, 360)
            objs.append(('shop', x, w_, sign or {'bakery': 'BAKERY', 'goldencafe': 'CAFE', 'cornercoffee': 'COFFEE'}[z], p, a, items)); x += w_ + 40
            objs.append(('table', x + 50, a)); x += 160
            if z == 'goldencafe': objs.append(('house2', x, 170, 140, p, a, 'note')); x += 210
        elif z == 'avenue':
            objs.append(('tree', x + 60, rnd.randint(95, 120), rnd.randint(170, 210))); x += 210
            if rnd.random() < 0.4: objs.append(('bench', x + 50)); x += 150
            elif rnd.random() < 0.5: objs.append(('lamp', x)); x += 70
        elif z == 'crossing':
            objs.append(('signal', x + 20)); x += 80
            objs.append(('zebra', x, 420)); x += 440
            objs.append(('bicycle', x + 60, a)); x += 200
            w_ = rnd.randint(170, 220); objs.append(('bldg', x, w_, rnd.randint(230, 330), 3, p)); x += w_ + 40
        elif z in ('pianohouse', 'downtown'):
            w_ = rnd.randint(200, 260)
            if z == 'pianohouse' or rnd.random() < 0.5: objs.append(('pianobldg', x, w_, rnd.randint(300, 400), 3, p))
            else: objs.append(('bldg', x, w_, rnd.randint(240, 400), rnd.choice([3, 4]), p))
            x += w_ + rnd.randint(30, 60)
            if rnd.random() < 0.4: objs.append(('lamp', x - 10)); x += 40
        elif z == 'terrace':
            objs.append(('table', x + 60, hexc('#FF8A3D'))); objs.append(('chair', x + 130)); objs.append(('chair', x - 10, True)); x += 240
            if rnd.random() < 0.35: w_ = 320; objs.append(('shop', x, w_, sign or 'CAFE', p, hexc('#FF8A3D'), 'cups')); x += w_ + 40
        elif z in ('curtainhouses', 'openwindows', 'neighbors'):
            w_ = rnd.randint(160, 190)
            style = {'curtainhouses': 'curtain', 'openwindows': 'open', 'neighbors': 'wave'}[z]
            objs.append(('house2', x, w_, rnd.randint(130, 160), p, a, style)); x += w_ + 30
            if rnd.random() < 0.5: objs.append(('fence', x, 80)); x += 100
            elif rnd.random() < 0.5: objs.append(('tree', x + 50, 60, 100)); x += 130
        else:
            raise SystemExit(f'unknown scene kind: {z}')

zones = []     # (world_x_start, kind, track_index)
TRACK_FX = [set() for _ in TRACKS]
scenes_path = args.scenes or next((os.path.join(args.songs, f) for f in ('storyboard.json', 'scenes.json') if os.path.exists(os.path.join(args.songs, f))), '')
TINTS = [None] * len(TRACKS)
EVENT_FX, REACTS, CHORUS = [], [], []      # (t0, t1, name) / (t, icon) / (t0, t1)
if os.path.exists(scenes_path):
    import json
    plan = json.load(open(scenes_path))['tracks']
    timing_dir = os.path.join(os.path.dirname(scenes_path), 'timing')
    # where will the walker be at every moment? simulate the walk once
    pos, POS = 0.0, []
    for fi in range(int(TOTAL * FPS) + 2):
        POS.append(pos); pos += SPEED * motion(fi / FPS)[0] / FPS
    scroll_at = lambda tt: POS[max(0, min(len(POS) - 1, int(tt * FPS)))]
    world_end = pos + W + 800
    # each song's scenery begins just ahead of the walker, so the tap leads into the new song's street
    bounds = [0.0] + [scroll_at(starts[i]) + CX + 180 for i in range(1, len(TRACKS))] + [world_end]
    SEG = 1100
    base_pal = (PASTEL, ACCENT)
    pieces = []
    for i in range(len(TRACKS)):
        spec = plan.get(str(i + 1), {})
        if spec.get('palette'): ACCENT = [hexc(c) for c in spec['palette']]
        else: PASTEL, ACCENT = base_pal
        TINTS[i] = tuple(hexc(c) for c in spec['sky']) if spec.get('sky') else None
        kinds = spec.get('scenes') or ['houses', 'shops', 'park']
        signs = spec.get('signs', {})
        TRACK_FX[i] = set(spec.get('effects', []))
        x, k = bounds[i], 0
        while x < bounds[i + 1]:
            z = kinds[k % len(kinds)]; xe = min(x + SEG, bounds[i + 1])
            zones.append((x, z, i)); gen_zone(z, x, xe, signs.get(z)); x = xe; k += 1
        # lyric beats: a set piece arrives on screen as its line is sung
        tfile = os.path.join(timing_dir, f'{i + 1}.json')
        lines = json.load(open(tfile)) if os.path.exists(tfile) else []
        def when(beat):
            hits = [l['start'] for l in lines if beat['line'].lower() in l['line'].lower()]
            if beat.get('all'): return hits
            n = beat.get('nth', 1) - 1
            return hits[n:n + 1]
        accents = ACCENT
        for b in spec.get('beats', []):
            for T in when(b):
                at = starts[i] + T
                if b.get('piece'):
                    opts = {k_: v for k_, v in b.items() if k_ in ('sign', 'text')}
                    opts['color'] = '#%02x%02x%02x' % tuple(int(c * 255) for c in accents[len(pieces) % len(accents)])
                    pieces.append([at, b['piece'], opts])
                if b.get('effect'): EVENT_FX.append((at - 0.5, at + b.get('dur', 8), b['effect']))
                if b.get('react'): REACTS.append((at + 1.2, b['react']))
        # chorus blocks: lights over the street, a banner as each chorus begins
        block = []
        for l in lines + [{'section': '', 'start': 1e9}]:
            if 'chorus' in l['section'].lower() and 'pre' not in l['section'].lower(): block.append(l); continue
            if block:
                c0, c1 = starts[i] + block[0]['start'], starts[i] + block[-1]['end'] + 1.0
                if spec.get('chorus', {}).get('lights'): CHORUS.append((c0, c1))
                if spec.get('chorus', {}).get('banner'):
                    pieces.append([c0 - 0.8, 'banner', {'text': spec['chorus']['banner'], 'color': '#%02x%02x%02x' % tuple(int(c * 255) for c in accents[0])}])
                block = []
    PASTEL, ACCENT = base_pal
    # place pieces: centred around screen x 1250 when their line starts, never overlapping each other
    pieces.sort(key=lambda p: p[0]); right = -1e9; placed = []
    for at, name, opts in pieces:
        wdt = props.WIDTH.get(name, 400)
        left = max(scroll_at(at) + 1250 - wdt / 2, right + 60)
        placed.append((left, left + wdt)); right = left + wdt
        objs.append(('piece', left, name, at, opts))
    # clear the generic scenery under each piece
    objs[:] = [o for o in objs if o[0] == 'piece' or not any(a - 80 < o[1] < b + 40 for a, b in placed)]
else:
    end = SPEED * TOTAL + W + 2 * ZLEN
    first = ['houses', 'shops', 'park']  # every walk starts in the neighbourhood
    last = None
    while len(zones) * ZLEN < end:
        z = first[len(zones)] if len(zones) < len(first) else rnd.choice([k for k in THEMES if k != last])
        zones.append((len(zones) * ZLEN, z, None)); gen_zone(z, len(zones) * ZLEN - ZLEN, len(zones) * ZLEN); last = z
ZSTART = [z[0] for z in zones]
def zone_at(wx):
    i = max(0, bisect.bisect_right(ZSTART, wx) - 1)
    return i
zone_of = lambda wx: zones[zone_at(wx)][1]
objs.sort(key=lambda o: o[1])
clouds = [(rnd.uniform(0, 7000), rnd.uniform(190, 360), rnd.uniform(0.7, 1.3)) for _ in range(16)]
birds = [(rnd.uniform(0, 9000), rnd.uniform(220, 420), rnd.uniform(0.6, 1.0)) for _ in range(10)]
stars = [(rnd.uniform(0, W), rnd.uniform(40, 520), rnd.uniform(1.2, 2.6)) for _ in range(90)]

def blob(ctx, circles, fill, line, lw):
    ctx.set_line_width(lw * 2); ctx.set_source_rgb(*line)
    for cx, cy, r in circles: ctx.new_path(); ctx.arc(cx, cy, r, 0, 2 * math.pi); ctx.stroke()
    ctx.set_source_rgb(*fill)
    for cx, cy, r in circles: ctx.new_path(); ctx.arc(cx, cy, r, 0, 2 * math.pi); ctx.fill()

def shape(ctx, fill, L):
    ctx.set_source_rgb(*fill); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.stroke()

def lit_window(ctx, night, L):
    if night > 0.3: ctx.set_source_rgba(1, 0.85, 0.45, min(1, night * 1.4)); ctx.fill_preserve()
    ctx.set_source_rgb(*L); ctx.stroke()

def draw_obj(ctx, o, sx, L, night, t):
    nf = lambda c: lerp(c, hexc('#2A2F5C'), night * 0.85)
    ctx.set_source_rgb(*L); ctx.set_line_width(3)
    k = o[0]
    if k == 'piece':
        props.draw_piece(ctx, o[2], sx, GY, t, t - o[3], L, night, nf, o[4], draw_obj, o[1]); return
    if k == 'bldg':
        _, _, w_, h_, cols, p = o
        ctx.rectangle(sx, GY - h_, w_, h_); shape(ctx, nf(lerp(p, (1, 1, 1), .5)), L)
        ww, wh = 26, 34; gx = (w_ - cols * ww) / (cols + 1)
        for r_ in range(int((h_ - 60) // 70)):
            for c in range(cols):
                ctx.rectangle(sx + gx + c * (ww + gx), GY - h_ + 30 + r_ * 70, ww, wh)
                if hash((o[1], r_, c)) % 3: lit_window(ctx, night, L)
                else: ctx.stroke()
        ctx.rectangle(sx + w_ / 2 - 18, GY - 64, 36, 64); ctx.stroke()
    elif k == 'lamp':
        ctx.move_to(sx, GY); ctx.line_to(sx, GY - 230); ctx.curve_to(sx, GY - 260, sx + 40, GY - 260, sx + 40, GY - 235); ctx.stroke()
        if night > 0.3:
            g = cairo.RadialGradient(sx + 40, GY - 225, 0, sx + 40, GY - 225, 120)
            g.add_color_stop_rgba(0, 1, 0.85, 0.5, 0.55 * night); g.add_color_stop_rgba(1, 1, 0.85, 0.5, 0)
            ctx.set_source(g); ctx.arc(sx + 40, GY - 225, 120, 0, 2 * math.pi); ctx.fill(); ctx.set_source_rgb(*L)
        ctx.arc(sx + 40, GY - 228, 9, 0, 2 * math.pi); ctx.stroke()
    elif k == 'tree':
        _, _, cr, th = o
        ctx.move_to(sx, GY); ctx.line_to(sx, GY - th); ctx.stroke()
        top = GY - th - cr * 0.6
        blob(ctx, [(sx, top, cr), (sx - cr * .7, top + cr * .4, cr * .7), (sx + cr * .7, top + cr * .35, cr * .75)], nf(hexc('#C2F0CF')), L, 1.6)
    elif k == 'bush':
        _, _, r = o
        blob(ctx, [(sx, GY - r * .6, r), (sx - r, GY - r * .4, r * .7), (sx + r, GY - r * .45, r * .75)], nf(hexc('#B5EBC4')), L, 1.6)
    elif k == 'bench':
        for yy in (45, 80): ctx.move_to(sx - 60, GY - yy); ctx.line_to(sx + 60, GY - yy)
        for bx in (-50, 50): ctx.move_to(sx + bx, GY); ctx.line_to(sx + bx, GY - 80)
        ctx.stroke()
    elif k == 'shop':
        _, _, w_, sign, p, a = o[:6]; items = o[6] if len(o) > 6 else None
        ctx.rectangle(sx, GY - 260, w_, 260); shape(ctx, nf(lerp(p, (1, 1, 1), .4)), L)
        n = 8; aw = w_ / n
        for i in range(n):
            ctx.move_to(sx + i * aw, GY - 170); ctx.line_to(sx + (i + 1) * aw, GY - 170); ctx.line_to(sx + (i + 1) * aw, GY - 140)
            ctx.arc(sx + (i + .5) * aw, GY - 140, aw / 2, 0, math.pi); ctx.close_path()
            shape(ctx, nf(a if i % 2 == 0 else (1, 1, 1)), L)
        wx0, ww_ = sx + 30, w_ * .45
        ctx.rectangle(wx0, GY - 120, ww_, 90); lit_window(ctx, night, L)
        if items == 'bread':     # loaves on the shelf
            for i in range(int(ww_ // 44)):
                bx = wx0 + 26 + i * 44
                ctx.save(); ctx.translate(bx, GY - 52); ctx.scale(1, .6); ctx.arc(0, 0, 18, math.pi, 0); ctx.restore(); ctx.close_path()
                shape(ctx, nf(hexc('#F2B562')), L)
                for d in (-6, 2, 10): ctx.move_to(bx + d - 3, GY - 62); ctx.line_to(bx + d + 3, GY - 56); ctx.stroke()
        elif items == 'cups':    # coffee cups with steam
            for i in range(int(ww_ // 46)):
                bx = wx0 + 22 + i * 46
                ctx.rectangle(bx - 10, GY - 64, 20, 24); shape(ctx, nf((1, 1, 1)), L)
                ctx.arc(bx + 12, GY - 53, 6, -math.pi / 2, math.pi / 2); ctx.stroke()
                ww = math.sin(t * 2.5 + i)
                ctx.move_to(bx, GY - 70); ctx.curve_to(bx + 5 * ww, GY - 80, bx - 5 * ww, GY - 88, bx, GY - 98); ctx.stroke()
        ctx.rectangle(sx + w_ - 90, GY - 110, 50, 110); ctx.stroke()
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(28)
        ext = ctx.text_extents(sign)
        if ext.width > w_ - 40: ctx.set_font_size(28 * (w_ - 40) / ext.width); ext = ctx.text_extents(sign)
        ctx.move_to(sx + w_ / 2 - ext.width / 2, GY - 205); ctx.show_text(sign)
    elif k == 'house2':
        _, _, w_, h_, p, a, style = o
        ctx.rectangle(sx, GY - h_, w_, h_); shape(ctx, nf(p), L)
        ctx.move_to(sx - 16, GY - h_); ctx.line_to(sx + w_ / 2, GY - h_ - 80); ctx.line_to(sx + w_ + 16, GY - h_); ctx.close_path(); shape(ctx, nf(a), L)
        ctx.rectangle(sx + 22, GY - 62, 32, 62); ctx.stroke()                           # door
        if style == 'note':                                                             # little note stuck on the door
            ctx.save(); ctx.translate(sx + 38, GY - 40); ctx.rotate(-0.12); ctx.rectangle(-9, -9, 18, 18); ctx.restore()
            shape(ctx, nf(hexc('#FFE14D')), L)
        wx, wy, ww, wh = sx + w_ - 82, GY - h_ + 26, 54, 58                             # window
        ctx.rectangle(wx, wy, ww, wh); lit_window(ctx, night, L)
        if style == 'wave':      # a neighbour waving from the window
            ctx.save(); ctx.rectangle(wx, wy, ww, wh); ctx.clip()
            ctx.arc(wx + ww / 2, wy + 30, 12, 0, 2 * math.pi); shape(ctx, nf((1, .9, .8)), L)
            ctx.rectangle(wx + ww / 2 - 14, wy + 42, 28, 30); shape(ctx, nf(ACCENT[int(o[1]) % len(ACCENT)]), L)
            ctx.restore()
            sw = math.sin(t * 6 + o[1]) * 0.5
            ax, ay = wx + ww / 2 + 12, wy + 46
            ctx.set_line_width(5); ctx.move_to(ax, ay); ctx.line_to(ax + 22 * math.sin(0.6 + sw), ay - 26 * math.cos(0.6 + sw)); ctx.stroke(); ctx.set_line_width(3)
        if style in ('curtain', 'open', 'wave'):   # curtains swaying in the breeze
            amp = 14 if style == 'open' else 5
            for side in (0, 1):
                x0 = wx + (0 if side == 0 else ww); d = 1 if side == 0 else -1
                sway = amp * (0.6 + 0.4 * math.sin(t * 2 + side + o[1]))
                if style == 'open': d = -d                                             # blown outside the frame
                ctx.move_to(x0, wy); ctx.curve_to(x0 + d * (18 + sway), wy + 20, x0 + d * (6 + sway), wy + 40, x0 + d * (12 + sway * 1.2), wy + wh)
                ctx.line_to(x0, wy + wh); ctx.close_path(); shape(ctx, nf(hexc('#FFF4E8')), L)
        if style == 'flowerbox':  # flower box under the window, drops of water catching the light
            ctx.rectangle(wx - 6, wy + wh, ww + 12, 16); shape(ctx, nf(hexc('#B07A4F')), L)
            for i in range(4):
                fx_ = wx + 4 + i * 15; c = ACCENT[(i + int(o[1])) % len(ACCENT)]
                ctx.arc(fx_, wy + wh - 4, 6, 0, 2 * math.pi); shape(ctx, nf(c), L)
            if night < 0.5:
                for i in range(3):
                    tw = 0.5 + 0.5 * math.sin(t * 4 + i * 2 + o[1])
                    ctx.set_source_rgba(1, .85, .3, tw * (1 - night)); ctx.arc(wx + 10 + i * 18, wy + wh - 22 - i * 6, 3, 0, 2 * math.pi); ctx.fill()
                ctx.set_source_rgb(*L)
    elif k == 'pianobldg':
        _, _, w_, h_, cols, p = o
        draw_obj(ctx, ('bldg', o[1], w_, h_, cols, p), sx, L, night, t)
        nx, ny = sx + w_ * .5, GY - h_ + 100                                           # notes drifting out of a 2nd floor window
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        for i in range(3):
            ph = (t * 0.6 + i / 3) % 1
            ctx.set_font_size(30 + 6 * i); ctx.set_source_rgba(*L, 1 - ph)
            ctx.move_to(nx + 40 * ph + 14 * math.sin(t * 2 + i), ny - 110 * ph); ctx.show_text('\u266a' if i % 2 else '\u266b')
        ctx.set_source_rgb(*L)
    elif k == 'zebra':
        _, _, w_ = o
        for i in range(0, int(w_), 56):
            ctx.rectangle(sx + i, GY + 12, 34, 70); ctx.set_source_rgb(*nf((1, 1, 1))); ctx.fill_preserve(); ctx.set_source_rgba(*L, .5); ctx.stroke()
        ctx.set_source_rgb(*L)
    elif k == 'signal':
        ctx.move_to(sx, GY); ctx.line_to(sx, GY - 200); ctx.stroke()
        ctx.rectangle(sx - 18, GY - 270, 36, 76); shape(ctx, nf(hexc('#3A3A46')), L)
        ctx.arc(sx, GY - 250, 10, 0, 2 * math.pi); ctx.set_source_rgb(*lerp(hexc('#5A2A2A'), hexc('#FF5C5C'), 0)); ctx.fill()
        ctx.arc(sx, GY - 216, 10, 0, 2 * math.pi); ctx.set_source_rgb(*hexc('#3DDC84')); ctx.fill(); ctx.set_source_rgb(*L)
    elif k == 'bicycle':
        a = o[2]
        for wxo in (-36, 36): ctx.arc(sx + wxo, GY - 26, 24, 0, 2 * math.pi); ctx.stroke()
        ctx.move_to(sx - 36, GY - 26); ctx.line_to(sx - 8, GY - 66); ctx.line_to(sx + 22, GY - 66); ctx.line_to(sx + 36, GY - 26)
        ctx.move_to(sx - 8, GY - 66); ctx.line_to(sx, GY - 26); ctx.line_to(sx + 22, GY - 66)
        ctx.set_source_rgb(*nf(a)); ctx.set_line_width(5); ctx.stroke(); ctx.set_line_width(3); ctx.set_source_rgb(*L)
        ctx.move_to(sx - 14, GY - 76); ctx.line_to(sx - 2, GY - 76); ctx.move_to(sx + 22, GY - 66); ctx.line_to(sx + 26, GY - 80); ctx.line_to(sx + 36, GY - 82); ctx.stroke()
    elif k == 'chair':
        flip = len(o) > 2 and o[2]; d = -1 if flip else 1
        ctx.move_to(sx, GY); ctx.line_to(sx, GY - 50); ctx.line_to(sx + d * 40, GY - 50); ctx.line_to(sx + d * 40, GY)
        ctx.move_to(sx + d * 40, GY - 50); ctx.line_to(sx + d * 40, GY - 100)
        ctx.set_source_rgb(*nf(hexc('#FF8A3D'))); ctx.set_line_width(6); ctx.stroke(); ctx.set_line_width(3); ctx.set_source_rgb(*L)
    elif k == 'table':
        a = o[2]
        ctx.move_to(sx, GY); ctx.line_to(sx, GY - 150); ctx.stroke()
        ctx.move_to(sx - 70, GY - 150); ctx.curve_to(sx - 40, GY - 200, sx + 40, GY - 200, sx + 70, GY - 150); ctx.close_path(); shape(ctx, nf(a), L)
        ctx.move_to(sx - 40, GY - 60); ctx.line_to(sx + 40, GY - 60); ctx.stroke()
    elif k == 'house':
        _, _, w_, h_, p, a = o
        ctx.rectangle(sx, GY - h_, w_, h_); shape(ctx, nf(p), L)
        ctx.move_to(sx - 16, GY - h_); ctx.line_to(sx + w_ / 2, GY - h_ - 80); ctx.line_to(sx + w_ + 16, GY - h_); ctx.close_path(); shape(ctx, nf(a), L)
        ctx.rectangle(sx + w_ * .68, GY - h_ - 70, 20, 40); shape(ctx, nf(p), L)
        if night < 0.5:  # chimney smoke
            for i in range(3):
                yy = GY - h_ - 85 - ((t * 25 + i * 30) % 90); r = 8 + i * 2
                ctx.set_source_rgba(*L, 0.5); ctx.arc(sx + w_ * .68 + 10 + 6 * math.sin(t + i), yy, r, 0, 2 * math.pi); ctx.stroke()
            ctx.set_source_rgb(*L)
        ctx.rectangle(sx + 22, GY - 62, 32, 62); ctx.stroke()
        ctx.arc(sx + w_ - 50, GY - h_ / 2 - 6, 20, 0, 2 * math.pi); lit_window(ctx, night, L)
    elif k == 'fence':
        _, _, w_ = o
        for i in range(0, w_, 22): ctx.move_to(sx + i, GY); ctx.line_to(sx + i, GY - 50)
        ctx.move_to(sx - 4, GY - 36); ctx.line_to(sx + w_, GY - 36); ctx.stroke()
    elif k == 'pine':
        _, _, h_ = o
        ctx.move_to(sx, GY); ctx.line_to(sx, GY - 30); ctx.stroke()
        for i in range(3):
            base = GY - 30 - i * h_ * .25; wdt = 55 - i * 12
            ctx.move_to(sx - wdt, base); ctx.line_to(sx, base - h_ * .45); ctx.line_to(sx + wdt, base); ctx.close_path()
            shape(ctx, nf(hexc('#9FE0B5')), L)
    elif k == 'mushroom':
        a = o[2]
        ctx.rectangle(sx - 6, GY - 26, 12, 26); shape(ctx, nf((1, 1, 1)), L)
        ctx.arc(sx, GY - 26, 22, math.pi, 0); ctx.close_path(); shape(ctx, nf(a), L)
    elif k == 'palm':
        _, _, h_ = o
        ctx.set_line_width(5); ctx.move_to(sx, GY); ctx.curve_to(sx + 10, GY - h_ * .5, sx + 30, GY - h_ * .8, sx + 40, GY - h_); ctx.stroke(); ctx.set_line_width(3)
        tx, ty = sx + 40, GY - h_
        for ang in (-150, -110, -60, -20, 20):
            r = math.radians(ang + 6 * math.sin(t * 1.5))
            ex, ey = tx + 90 * math.cos(r), ty + 90 * math.sin(r) + 40
            ctx.move_to(tx, ty); ctx.curve_to(tx + 50 * math.cos(r), ty + 50 * math.sin(r) - 25, ex, ey - 20, ex, ey)
            ctx.curve_to(ex - 10, ey - 5, tx + 30 * math.cos(r), ty + 30 * math.sin(r), tx, ty); shape(ctx, nf(hexc('#9FE0B5')), L)
    elif k == 'umbrella':
        a = o[2]
        ctx.move_to(sx, GY); ctx.line_to(sx + 8, GY - 160); ctx.stroke()
        for i in range(4):
            a0, a1 = math.pi + i * math.pi / 4, math.pi + (i + 1) * math.pi / 4
            ctx.move_to(sx + 8, GY - 160); ctx.arc(sx + 8, GY - 160, 80, a0, a1); ctx.close_path(); shape(ctx, nf(a if i % 2 == 0 else (1, 1, 1)), L)
        ctx.rectangle(sx - 50, GY - 14, 90, 14); shape(ctx, nf(hexc('#FFE9A8')), L)
    elif k == 'lighthouse':
        ctx.move_to(sx - 40, GY); ctx.line_to(sx - 24, GY - 300); ctx.line_to(sx + 24, GY - 300); ctx.line_to(sx + 40, GY); ctx.close_path(); shape(ctx, nf((1, 1, 1)), L)
        for i in range(3):
            y0 = GY - 60 - i * 90
            ctx.rectangle(sx - 36 + i * 5, y0 - 30, 72 - i * 10, 30); shape(ctx, nf(hexc('#FF5C8A')), L)
        ctx.rectangle(sx - 20, GY - 340, 40, 40); lit_window(ctx, max(night, 0.0), L)
        ctx.move_to(sx - 30, GY - 340); ctx.line_to(sx, GY - 370); ctx.line_to(sx + 30, GY - 340); ctx.close_path(); shape(ctx, nf(hexc('#FF5C8A')), L)
        if night > 0.4:
            ang = t * 1.2; g = cairo.LinearGradient(sx, 0, sx + 400 * math.cos(ang), 0)
            ctx.set_source_rgba(1, 0.9, 0.6, 0.25 * night)
            ctx.move_to(sx, GY - 320); ctx.line_to(sx + 500 * math.cos(ang), GY - 360); ctx.line_to(sx + 500 * math.cos(ang), GY - 280); ctx.close_path(); ctx.fill()
            ctx.set_source_rgb(*L)
    elif k == 'sandcastle':
        ctx.rectangle(sx - 40, GY - 40, 80, 40); shape(ctx, nf(hexc('#FFE3A3')), L)
        ctx.rectangle(sx - 15, GY - 70, 30, 30); shape(ctx, nf(hexc('#FFE3A3')), L)
        ctx.move_to(sx, GY - 70); ctx.line_to(sx, GY - 95); ctx.line_to(sx + 18, GY - 88); ctx.line_to(sx, GY - 82); ctx.stroke()
    elif k == 'flowers':
        _, _, n = o
        for i in range(n):
            fx = sx + i * 24; fh = 40 + (hash((o[1], i)) % 40); c = ACCENT[hash((o[1], i, 1)) % len(ACCENT)]
            ctx.move_to(fx, GY); ctx.line_to(fx, GY - fh); ctx.stroke()
            for pt in range(5):
                pa = pt * 2 * math.pi / 5 + t * .3
                ctx.arc(fx + 9 * math.cos(pa), GY - fh + 9 * math.sin(pa), 7, 0, 2 * math.pi); shape(ctx, nf(c), L)
            ctx.arc(fx, GY - fh, 5, 0, 2 * math.pi); shape(ctx, nf(hexc('#FFE9A8')), L)
    elif k == 'windmill':
        ctx.move_to(sx - 40, GY); ctx.line_to(sx - 22, GY - 220); ctx.line_to(sx + 22, GY - 220); ctx.line_to(sx + 40, GY); ctx.close_path(); shape(ctx, nf((1, 1, 1)), L)
        ctx.rectangle(sx - 14, GY - 60, 28, 60); ctx.stroke()
        hx, hy = sx, GY - 220
        for i in range(4):
            a = t * 0.8 + i * math.pi / 2
            ctx.move_to(hx, hy); ctx.line_to(hx + 120 * math.cos(a), hy + 120 * math.sin(a)); ctx.stroke()
            px, py = -math.sin(a), math.cos(a)
            ctx.move_to(hx + 40 * math.cos(a), hy + 40 * math.sin(a)); ctx.line_to(hx + 120 * math.cos(a), hy + 120 * math.sin(a))
            ctx.line_to(hx + 120 * math.cos(a) + 24 * px, hy + 120 * math.sin(a) + 24 * py); ctx.line_to(hx + 40 * math.cos(a) + 24 * px, hy + 40 * math.sin(a) + 24 * py)
            ctx.close_path(); shape(ctx, nf(hexc('#FFE9A8')), L)
        ctx.arc(hx, hy, 8, 0, 2 * math.pi); shape(ctx, nf((1, 1, 1)), L)
    elif k == 'stall':
        _, _, w_, a, p = o
        ctx.rectangle(sx, GY - 80, w_, 80); shape(ctx, nf(lerp(p, (1, 1, 1), .3)), L)
        for px_ in (sx + 8, sx + w_ - 8): ctx.move_to(px_, GY - 80); ctx.line_to(px_, GY - 210); ctx.stroke()
        n = 6; aw = w_ / n
        for i in range(n):
            ctx.rectangle(sx + i * aw, GY - 230, aw, 34); shape(ctx, nf(a if i % 2 == 0 else (1, 1, 1)), L)
        for i in range(int(w_ // 30) - 1):
            c = ACCENT[(i + int(o[1])) % len(ACCENT)]
            ctx.arc(sx + 24 + i * 30, GY - 94, 12, 0, 2 * math.pi); shape(ctx, nf(c), L)

def far_layer(ctx, kind, off, L, top, bot, night):
    col = lerp(bot, top, 0.25)
    ctx.set_line_width(2.5)
    if kind == 'hills':
        ctx.move_to(0, GY)
        for xx in range(0, W + 21, 20):
            wx = xx + off; ctx.line_to(xx, GY - 130 - 50 * math.sin(wx / 420) - 30 * math.sin(wx / 190 + 1.7))
        ctx.line_to(W, GY); ctx.close_path(); shape(ctx, col, L)
    elif kind == 'skyline':
        x = -((off) % 140) - 140; i = int(off // 140)
        while x < W + 140:
            h_ = 120 + (hash(('sky', i)) % 200); w_ = 110 + hash(('w', i)) % 40
            ctx.rectangle(x, GY - h_, w_, h_); shape(ctx, col, L); x += 140; i += 1
    elif kind == 'treeline':
        ctx.move_to(0, GY); x = -((off) % 60); i = int(off // 60)
        while x < W + 60:
            h_ = 140 + hash(('t', i)) % 90
            ctx.line_to(x, GY - 90); ctx.line_to(x + 30, GY - h_); ctx.line_to(x + 60, GY - 90); x += 60; i += 1
        ctx.line_to(W + 60, GY); ctx.close_path(); shape(ctx, lerp(col, hexc('#5FBF8A'), 0.35 * (1 - night)), L)
    elif kind == 'sea':
        ctx.rectangle(0, GY - 150, W, 150); shape(ctx, lerp(hexc('#5EC8F2'), hexc('#1B2A55'), night), L)
        ctx.set_line_width(2)
        for row in range(4):
            y = GY - 120 + row * 32
            for k in range(-1, W // 90 + 2):
                x = k * 90 - (off * (1 + row * .3)) % 90
                ctx.move_to(x, y); ctx.curve_to(x + 15, y - 8, x + 30, y - 8, x + 45, y)
            ctx.stroke()

GROUND_KINDS = {'zebra'}
def fx_alpha(name, t):
    """0..1 strength of an effect at time t: per-song effects, or ones a lyric line switches on for a while"""
    a = 0.0
    for i, (s0, e) in enumerate(zip(starts, ends)):
        if s0 - 0.5 <= t < e + 0.5 and name in TRACK_FX[i]:
            a = max(a, min(sm((t - s0 + 0.5) / 2.0), 1 - sm((t - e + 0.5) / 1.5)))
    for t0, t1, n in EVENT_FX:
        if n == name and t0 <= t < t1 + 1.5: a = max(a, min(sm((t - t0) / 1.5), 1 - sm((t - t1) / 1.5)))
    return a

def chorus_alpha(t):
    return max([min(sm((t - c0) / 1.2), 1 - sm((t - c1) / 1.2)) for c0, c1 in CHORUS if c0 - 1 <= t <= c1 + 1.5] + [0.0])

def track_tint(t):
    """(sky colours, weight) of the song playing at t, cross-fading through the gap between songs"""
    best = (None, 0.0)
    for i, (s0, e) in enumerate(zip(starts, ends)):
        if TINTS[i] is None: continue
        w = min(sm((t - s0 + 1.0) / 2.0), 1 - sm((t - e - 0.5) / 2.0))
        if w > best[1]: best = (TINTS[i], w)
    return best

def scene(t, scroll, phase, walk, reach, press, ba, bs):
    u = t / TOTAL
    top, bot, night = sky_at(u)
    tint, tw = track_tint(t)
    if tint:   # each song brings its own sky; night still darkens it
        k = 0.7 * tw * (1 - night)
        top, bot = lerp(top, tint[0], k), lerp(bot, tint[1], k)
    L = lerp(hexc('#2B2541'), hexc('#EDE6FF'), min(1, night * 1.3))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); ctx = cairo.Context(s)
    g = cairo.LinearGradient(0, 0, 0, GY); g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bot); ctx.set_source(g); ctx.paint()
    if night > 0.2:
        for x_, y_, r in stars:
            ctx.set_source_rgba(1, 1, 1, min(1, (night - .2) * 1.5) * (.6 + .4 * math.sin(t * 2 + x_))); ctx.arc(x_, y_, r, 0, 2 * math.pi); ctx.fill()
    ang = math.pi * (0.1 + 0.8 * u); sxp, syp = W * .5 - math.cos(ang) * 780, 620 - math.sin(ang) * 460
    if night < 0.6: ctx.set_source_rgba(1, .95, .75, 1 - night); ctx.arc(sxp, syp, 58, 0, 2 * math.pi); ctx.fill()
    else: ctx.set_source_rgba(1, .97, .85, (night - .6) * 2.5); ctx.arc(W * .78, 200, 42, 0, 2 * math.pi); ctx.fill()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for cx0, cy, sc in clouds:
        cx = (cx0 - t * SPEED * .12) % 7000 - 600
        if -300 < cx < W + 300:
            r = 34 * sc; blob(ctx, [(cx, cy, r), (cx + r * 1.1, cy - r * .4, r * 1.2), (cx + r * 2.3, cy, r * .9)], lerp((1, 1, 1), hexc('#4A4E78'), night), L, 1.6)
    if night < 0.4:
        ctx.set_source_rgb(*L); ctx.set_line_width(3)
        for bx0, by, sc in birds:
            bx = (bx0 - t * SPEED * .5) % 9000 - 300
            if -50 < bx < W + 50:
                f = 10 * sc * math.sin(t * 8 + bx0)
                ctx.move_to(bx - 14 * sc, by - f); ctx.curve_to(bx - 6 * sc, by - 8 * sc, bx, by - 2, bx, by)
                ctx.curve_to(bx, by - 2, bx + 6 * sc, by - 8 * sc, bx + 14 * sc, by - f); ctx.stroke()
    fx = lambda name: fx_alpha(name, t)
    if fx('birds') > 0.01 and night < 0.5:   # a flock passing over the street
        ctx.set_source_rgba(*L, fx('birds')); ctx.set_line_width(3)
        for j in range(7):
            bx = W + 200 - ((t * 140 + j * 37) % (W + 600)) + (j % 3) * 30; by = 250 + (j * 47) % 160
            f = 9 * math.sin(t * 9 + j)
            ctx.move_to(bx - 13, by - f); ctx.curve_to(bx - 6, by - 7, bx, by - 2, bx, by)
            ctx.curve_to(bx, by - 2, bx + 6, by - 7, bx + 13, by - f); ctx.stroke()
    # far layer cross-fades with the zone at screen centre
    cw = scroll + W / 2; zi = zone_at(cw)
    z0 = zones[zi][0]; z1 = zones[zi + 1][0] if zi + 1 < len(zones) else z0 + ZLEN
    fr = (cw - z0) / max(1, z1 - z0)
    k_now = FAR[zones[zi][1]]; k_next = FAR[zones[min(zi + 1, len(zones) - 1)][1]]
    blend = max(0, (fr - 0.8) / 0.2)
    off = scroll * 0.35
    for kind, alpha in ((k_now, 1 - blend if k_now != k_next else 1), (k_next, blend if k_now != k_next else 0)):
        if alpha <= 0.01: continue
        ctx.push_group(); far_layer(ctx, kind, off, L, top, bot, night); ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)
    for o in objs:
        sx = o[1] - scroll
        if o[0] not in GROUND_KINDS and (-520 < sx < W + 200 or (o[0] == 'piece' and -1000 < sx < W + 1000)): draw_obj(ctx, o, sx, L, night, t)
    # ground: sand on the beach, grass paths in green zones, pavement elsewhere
    gz = zone_of(scroll + CX)
    gcol = hexc('#FFE9B8') if gz == 'beach' else (hexc('#DDF3D2') if gz in GREEN else hexc('#F3E9F7'))
    ctx.rectangle(0, GY, W, H - GY); ctx.set_source_rgb(*lerp(gcol, hexc('#1A1F3D'), night)); ctx.fill()
    ctx.set_source_rgb(*L); ctx.set_line_width(4); ctx.move_to(0, GY); ctx.line_to(W, GY); ctx.stroke()
    ctx.set_line_width(3)
    for k in range(-1, W // 140 + 2):
        x_ = k * 140 - scroll % 140; ctx.move_to(x_, GY + 44); ctx.line_to(x_ + 60, GY + 44); ctx.stroke()
    for o in objs:
        sx = o[1] - scroll
        if o[0] in GROUND_KINDS and -520 < sx < W + 200: draw_obj(ctx, o, sx, L, night, t)
    if fx('golden') > 0.01:   # warm golden-hour wash
        ctx.set_source_rgba(1, 0.78, 0.35, 0.09 * fx('golden') * (1 - night)); ctx.paint()
    if fx('breeze') > 0.01:   # leaves and petals carried on the wind
        for j in range(26):
            px = W + 100 - ((t * (220 + j * 9) + j * 211) % (W + 300)); py = 180 + (j * 83) % 520 + 30 * math.sin(t * 1.7 + j)
            ang = t * 3 + j
            ctx.save(); ctx.translate(px, py); ctx.rotate(ang); ctx.scale(1, 0.55)
            ctx.arc(0, 0, 9, 0, 2 * math.pi); ctx.restore()
            ctx.set_source_rgba(*(ACCENT[j % len(ACCENT)] if j % 3 else hexc('#7FD99A')), 0.85 * fx('breeze')); ctx.fill_preserve()
            ctx.set_source_rgba(*L, 0.6 * fx('breeze')); ctx.set_line_width(2); ctx.stroke()
    # soft light behind the mascot so it stays clear at night
    if night > 0.05:
        g = cairo.RadialGradient(CX + 6, GY - 140, 10, CX + 6, GY - 140, 230)
        g.add_color_stop_rgba(0, 1, 0.93, 0.78, 0.55 * night); g.add_color_stop_rgba(1, 1, 0.93, 0.78, 0)
        ctx.set_source(g); ctx.arc(CX + 6, GY - 140, 230, 0, 2 * math.pi); ctx.fill()
    ca = chorus_alpha(t)
    if ca > 0.01:      # chorus: lights strung over the street, notes bouncing around the mascot
        for j in range(3):
            x0 = -60 + j * (W + 120) / 3; props.string_lights(ctx, x0, x0 + (W + 120) / 3, GY - 470 + 18 * (j % 2), 70, t, L, ca)
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        for j in range(3):
            ph = (t * .8 + j / 3) % 1
            ctx.set_font_size(30 + 6 * j); ctx.set_source_rgba(*hexc(['#FF5C8A', '#FFB21A', '#7B3BFF'][j]), ca * (1 - ph))
            ctx.move_to(CX - 70 + j * 60 + 10 * math.sin(t * 3 + j), GY - 250 - 90 * ph); ctx.show_text('\u266a' if j % 2 else '\u266b')
    ch.draw(ctx, CX, GY, t, L=hexc('#2B2541'), outfit=args.outfit, phase=phase, walk=walk, reach=reach, press=press)
    for rt, icon in REACTS:   # the mascot reacts to what it passes
        k = t - rt
        if 0 <= k < 2.2 and ba < 0.05:
            sc = min(1.1, k / 0.2 * 1.1) if k < 0.2 else 1.0
            al = 1 - sm((k - 1.6) / 0.6)
            bx, by = CX - 34, GY - 86 - 116 - 42 - 40
            ctx.save(); ctx.translate(bx, by); ctx.scale(sc, sc); ctx.push_group()
            ctx.arc(0, 0, 30, 0, 2 * math.pi); ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve()
            ctx.set_source_rgb(*hexc('#2B2541')); ctx.set_line_width(4); ctx.stroke()
            ctx.move_to(14, 22); ctx.line_to(26, 40); ctx.line_to(2, 28); ctx.close_path(); ctx.set_source_rgb(1, 1, 1); ctx.fill()
            if icon == 'heart':
                ctx.move_to(0, 14); ctx.curve_to(-26, -4, -12, -24, 0, -10); ctx.curve_to(12, -24, 26, -4, 0, 14); ctx.set_source_rgb(*hexc('#FF5C8A')); ctx.fill()
            elif icon == 'sun':
                ctx.set_source_rgb(*hexc('#FFB21A')); ctx.arc(0, 0, 9, 0, 2 * math.pi); ctx.fill(); ctx.set_line_width(3)
                for a in range(8): ctx.move_to(14 * math.cos(a * .785), 14 * math.sin(a * .785)); ctx.line_to(20 * math.cos(a * .785), 20 * math.sin(a * .785))
                ctx.stroke()
            else:
                ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(32)
                ctx.set_source_rgb(*hexc('#7B3BFF')); ctx.move_to(-11, 12); ctx.show_text('\u266a')
            ctx.pop_group_to_source(); ctx.paint_with_alpha(al); ctx.restore()
    if ba > 0.01 and bs > 0.01:   # play bubble above the head
        bx, by = CX + 40, GY - 86 - 116 - 42 - 62
        ctx.save(); ctx.translate(bx, by); ctx.scale(bs, bs)
        ctx.push_group()
        ctx.set_line_width(4); ctx.set_source_rgb(1, 1, 1)
        ctx.new_path(); r = 18; w2, h2 = 44, 32
        ctx.arc(-w2 + r, -h2 + r, r, math.pi, 1.5 * math.pi); ctx.arc(w2 - r, -h2 + r, r, 1.5 * math.pi, 0)
        ctx.arc(w2 - r, h2 - r, r, 0, 0.5 * math.pi); ctx.line_to(-6, h2); ctx.line_to(-22, h2 + 18); ctx.line_to(-20, h2)
        ctx.arc(-w2 + r, h2 - r, r, 0.5 * math.pi, math.pi); ctx.close_path()
        ctx.fill_preserve(); ctx.set_source_rgb(*hexc('#2B2541')); ctx.stroke()
        ctx.move_to(-12, -16); ctx.line_to(18, 0); ctx.line_to(-12, 16); ctx.close_path(); ctx.set_source_rgb(*hexc('#FF2D87')); ctx.fill()
        ctx.pop_group_to_source(); ctx.paint_with_alpha(ba); ctx.restore()
    buf = np.ndarray((H, W, 4), np.uint8, s.get_data())
    return Image.fromarray(buf[..., [2, 1, 0]].copy(), 'RGB'), night

F_BIG = ImageFont.truetype(os.path.join(ASSETS, 'fonts', 'Outfit-800.ttf'), 54)
F_SM = ImageFont.truetype(os.path.join(ASSETS, 'fonts', 'Outfit-500.ttf'), 28)
logo = Image.open(LOGO).convert('RGBA'); logo.thumbnail((360, 90))
la = np.array(logo); la[..., 3] = (la[..., 3] * .75).astype(np.uint8); logo_w = Image.fromarray(la)
ld = la.copy(); ld[..., :3] = (43, 37, 65); logo_d = Image.fromarray(ld)
def gradbar(w, h):
    a = np.zeros((h, w, 4), np.uint8); stops = [(0, (255, 178, 26)), (.45, (255, 45, 135)), (1, (123, 59, 255))]
    for x in range(w):
        tt = x / max(1, w - 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= tt <= p1: q = (tt - p0) / (p1 - p0); a[:, x, :3] = [int(c0[i] + (c1[i] - c0[i]) * q) for i in range(3)]
    a[..., 3] = 255; return Image.fromarray(a)
BAR_X, BAR_Y, BAR_W = 96, 1000, W - 192
barfill = gradbar(BAR_W, 6)
def card(num, title, col):
    c = Image.new('RGBA', (W, 140), (0, 0, 0, 0)); cd = ImageDraw.Draw(c)
    cd.text((96, 0), f"TRACK {num}", font=F_SM, fill=col + (210,)); cd.text((96, 36), title, font=F_BIG, fill=col + (255,))
    return c
cards_d = [card(n, ti, (43, 37, 65)) for n, ti in TRACKS]; cards_l = [card(n, ti, (255, 255, 255)) for n, ti in TRACKS]
fmt = lambda s: f"{int(s // 60)}:{int(s % 60):02d}"

STILLS = {int(float(v) * FPS) for v in args.stills.split(',')} if args.stills else None
ff = None if STILLS else subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-i', MIX, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                       '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '384k', '-aac_coder', 'twoloop', '-ar', '48000', '-shortest', '-movflags', '+faststart',
                       args.out], stdin=subprocess.PIPE)
nframes = int(TOTAL * FPS)
scroll = phase = 0.0
for fi in range(nframes):
    t = fi / FPS
    walk, reach, press, ba, bs = motion(t)
    if STILLS is not None and fi not in STILLS:
        scroll += SPEED * walk / FPS; phase += 2 * math.pi * 0.85 * walk / FPS; continue
    img, night = scene(t, scroll, phase, walk, reach, press, ba, bs)
    scroll += SPEED * walk / FPS; phase += 2 * math.pi * 0.85 * walk / FPS
    frame = img.convert('RGBA'); dark_ui = night < 0.45
    frame.alpha_composite(logo_d if dark_ui else logo_w, (64, 52))
    ti = max(i for i, s0 in enumerate(starts) if t >= s0); since = t - starts[ti]
    a = min(1.0, since / 1.2)
    a = min(a, (ends[ti] - t) / 1.0)
    cdc = np.array((cards_d if dark_ui else cards_l)[ti]); cdc[..., 3] = (cdc[..., 3] * max(0, a)).astype(np.uint8)
    frame.alpha_composite(Image.fromarray(cdc), (0, 858 - int(10 * (1 - a))))
    dur = DURS[ti]; pr = min(1, since / dur); since = min(since, dur)
    ov = Image.new('RGBA', (W, H), (255, 255, 255, 0)); dl = ImageDraw.Draw(ov)
    tc = (43, 37, 65, 200) if dark_ui else (255, 255, 255, 220)
    dl.rounded_rectangle((BAR_X, BAR_Y, BAR_X + BAR_W, BAR_Y + 6), 3, fill=tc[:3] + (60,))
    fw = max(6, int(BAR_W * pr)); ov.alpha_composite(barfill.crop((0, 0, fw, 6)), (BAR_X, BAR_Y))
    dl.ellipse((BAR_X + fw - 10, BAR_Y - 7, BAR_X + fw + 10, BAR_Y + 13), fill=(255, 255, 255, 255), outline=(43, 37, 65, 120))
    dl.text((BAR_X + BAR_W, BAR_Y + 18), f"{fmt(since)} / {fmt(dur)}", font=F_SM, fill=tc, anchor='ra')
    frame.alpha_composite(ov); out = frame.convert('RGB')
    if STILLS is not None:
        out.save(f'{os.path.splitext(args.out)[0]}_{t:06.1f}s.png'); continue
    ff.stdin.write(out.tobytes())
    if fi % (FPS * 60) == 0: print(f'  rendered {fi // (FPS * 60)} / {int(TOTAL // 60)} min', flush=True)
if ff: ff.stdin.close(); ff.wait()
if not STILLS: os.remove(MIX)
print('done:', args.out)
