"""Open to Close video renderer.

Takes a folder of numbered songs ("1.Title.mp3", "2.Title.mp3", ...) and renders one video:
the mascot walks through ever-changing line-art scenery while the sky goes from morning to night.
Between songs the mascot stops, taps the headphones, a play bubble pops up and the next song starts.

    python studio/render_video.py path/to/songs -o out.mp4
"""
import argparse, math, os, random, re, subprocess, sys, wave
import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import character as ch

ASSETS = os.path.join(HERE, 'assets')
LOGO = os.path.join(ASSETS, 'logo_horizontal.png')

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('songs', help='folder with numbered audio files, e.g. "1.Golden Hour Coffee.mp3"')
ap.add_argument('-o', '--out', default='output.mp4', help='output video path')
ap.add_argument('--gap', type=float, default=1.5, help='seconds of silence between songs')
ap.add_argument('--seed', type=int, default=21, help='scenery seed (change it for a different walk)')
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

# audio: short fade at each song end, silence gaps, loudness to YouTube's -14 LUFS
MIX = os.path.splitext(args.out)[0] + '_mix.wav'
cmd = ['ffmpeg', '-y', '-loglevel', 'error']
for _, _, p in songs: cmd += ['-i', p]
for _ in songs[1:]: cmd += ['-f', 'lavfi', '-t', str(GAP), '-i', 'anullsrc=r=48000:cl=stereo']
fl, seq = [], []
for i, d in enumerate(DURS):
    fl.append(f'[{i}]afade=t=out:st={max(0, d - 0.8):.3f}:d=0.8,aresample=48000[a{i}]')
    seq.append(f'[a{i}]')
    if i < len(songs) - 1: seq.append(f'[{len(songs) + i}]')
fl.append(''.join(seq) + f'concat=n={len(seq)}:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11')
subprocess.run(cmd + ['-filter_complex', ';'.join(fl), '-ar', '48000', '-ac', '2', MIX], check=True)

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
# each theme: which far layer sits behind it
THEMES = {'town': 'skyline', 'park': 'hills', 'shops': 'skyline', 'houses': 'hills',
          'forest': 'treeline', 'beach': 'sea', 'flowers': 'hills', 'market': 'skyline'}
order, last = [], None
end = SPEED * TOTAL + W + 2 * ZLEN
first = ['houses', 'shops', 'park']  # every walk starts in the neighbourhood
while len(order) * ZLEN < end:
    if len(order) < len(first): z = first[len(order)]
    else: z = rnd.choice([k for k in THEMES if k != last])
    order.append(z); last = z
zone_of = lambda wx: order[max(0, min(len(order) - 1, int(wx // ZLEN)))]

objs = []
for zi, z in enumerate(order):
    x, xe = zi * ZLEN + 40, (zi + 1) * ZLEN - 120
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
            w_ = rnd.randint(300, 360); objs.append(('shop', x, w_, rnd.choice(['CAFE', 'BAKERY', 'BOOKS', 'RECORDS', 'FLOWERS']), p, a)); x += w_ + 30
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
            elif k < 0.85 and not any(o[0] == 'lighthouse' and o[1] > zi * ZLEN for o in objs): objs.append(('lighthouse', x + 60)); x += 260
            else: objs.append(('sandcastle', x + 40)); x += 150
        elif z == 'flowers':
            if rnd.random() < 0.15: objs.append(('windmill', x + 70)); x += 240
            else: objs.append(('flowers', x, rnd.randint(4, 7))); x += 170
        elif z == 'market':
            objs.append(('stall', x, rnd.randint(200, 240), a, p)); x += 270
            if rnd.random() < 0.3: objs.append(('lamp', x)); x += 60
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
        _, _, w_, sign, p, a = o
        ctx.rectangle(sx, GY - 260, w_, 260); shape(ctx, nf(lerp(p, (1, 1, 1), .4)), L)
        n = 8; aw = w_ / n
        for i in range(n):
            ctx.move_to(sx + i * aw, GY - 170); ctx.line_to(sx + (i + 1) * aw, GY - 170); ctx.line_to(sx + (i + 1) * aw, GY - 140)
            ctx.arc(sx + (i + .5) * aw, GY - 140, aw / 2, 0, math.pi); ctx.close_path()
            shape(ctx, nf(a if i % 2 == 0 else (1, 1, 1)), L)
        ctx.rectangle(sx + 30, GY - 120, w_ * .45, 90); lit_window(ctx, night, L)
        ctx.rectangle(sx + w_ - 90, GY - 110, 50, 110); ctx.stroke()
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(28)
        ext = ctx.text_extents(sign); ctx.move_to(sx + w_ / 2 - ext.width / 2, GY - 205); ctx.show_text(sign)
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

def scene(t, scroll, phase, walk, reach, press, ba, bs):
    u = t / TOTAL
    top, bot, night = sky_at(u)
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
    # far layer cross-fades with the zone at screen centre
    cw = scroll + W / 2; zi = int(cw // ZLEN); fr = (cw % ZLEN) / ZLEN
    k_now = THEMES[order[zi]]; k_next = THEMES[order[min(zi + 1, len(order) - 1)]]
    blend = max(0, (fr - 0.8) / 0.2)
    off = scroll * 0.35
    for kind, alpha in ((k_now, 1 - blend if k_now != k_next else 1), (k_next, blend if k_now != k_next else 0)):
        if alpha <= 0.01: continue
        ctx.push_group(); far_layer(ctx, kind, off, L, top, bot, night); ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)
    for o in objs:
        sx = o[1] - scroll
        if -520 < sx < W + 200: draw_obj(ctx, o, sx, L, night, t)
    # ground: sand on the beach, path elsewhere
    gz = zone_of(scroll + CX)
    gcol = hexc('#FFE9B8') if gz == 'beach' else (hexc('#DDF3D2') if gz in ('park', 'forest', 'flowers') else hexc('#F3E9F7'))
    ctx.rectangle(0, GY, W, H - GY); ctx.set_source_rgb(*lerp(gcol, hexc('#1A1F3D'), night)); ctx.fill()
    ctx.set_source_rgb(*L); ctx.set_line_width(4); ctx.move_to(0, GY); ctx.line_to(W, GY); ctx.stroke()
    ctx.set_line_width(3)
    for k in range(-1, W // 140 + 2):
        x_ = k * 140 - scroll % 140; ctx.move_to(x_, GY + 44); ctx.line_to(x_ + 60, GY + 44); ctx.stroke()
    # soft light behind the mascot so it stays clear at night
    if night > 0.05:
        g = cairo.RadialGradient(CX + 6, GY - 140, 10, CX + 6, GY - 140, 230)
        g.add_color_stop_rgba(0, 1, 0.93, 0.78, 0.55 * night); g.add_color_stop_rgba(1, 1, 0.93, 0.78, 0)
        ctx.set_source(g); ctx.arc(CX + 6, GY - 140, 230, 0, 2 * math.pi); ctx.fill()
    ch.draw(ctx, CX, GY, t, L=hexc('#2B2541'), phase=phase, walk=walk, reach=reach, press=press)
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

ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-i', MIX, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                       '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart',
                       args.out], stdin=subprocess.PIPE)
nframes = int(TOTAL * FPS)
scroll = phase = 0.0
for fi in range(nframes):
    t = fi / FPS
    walk, reach, press, ba, bs = motion(t)
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
    frame.alpha_composite(ov); out = frame.convert('RGB'); ff.stdin.write(out.tobytes())
    if fi % (FPS * 60) == 0: print(f'  rendered {fi // (FPS * 60)} / {int(TOTAL // 60)} min', flush=True)
ff.stdin.close(); ff.wait()
os.remove(MIX)
print('done:', args.out)
