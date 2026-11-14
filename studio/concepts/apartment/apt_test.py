"""PLAY LIST 03 test clip: apartment cross-section (A + B mix), ~33 s."""
import math, os, random, subprocess, sys, re
import numpy as np, cairo
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.argv = [sys.argv[0], '/dev/null']
src = open(os.path.join(HERE, 'apt.py')).read(); exec(src[:src.index('FL = [')])
from PIL import Image

FPS = 24; OUT = os.path.join(HERE, 'apt_test.mp4')
# ---------- audio: two chorus clips, fixed gain to -14 LUFS, limiter, 24-bit mix, silent lead/gap/tail ----------
CLIPS = [('46', 34.5, 13.0), ('49', 29.0, 12.0)]
LEAD, GAP, TAIL = 2.6, 2.2, 3.0
def song(n): return [os.path.join(SP, 'vol03_songs', f) for f in os.listdir(os.path.join(SP, 'vol03_songs')) if f.startswith(n + '.')][0]
def lufs(p, ss, d):
    e = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-ss', str(ss), '-t', str(d), '-i', p, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', e)[-1])
MIX = os.path.join(HERE, 'apt_mix.wav')
cmd = ['ffmpeg', '-y', '-loglevel', 'error']; fl = []
for n, ss, d in CLIPS: cmd += ['-ss', str(ss), '-t', str(d), '-i', song(n)]
for d in (LEAD, GAP, TAIL): cmd += ['-f', 'lavfi', '-t', str(d), '-i', 'anullsrc=r=48000:cl=stereo']
for i, (n, ss, d) in enumerate(CLIPS):
    g = -14 - lufs(song(n), ss, d)
    fl.append(f'[{i}]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={g:.2f}dB,alimiter=limit={10 ** (-1.5 / 20):.4f}:attack=5:release=60:level=disabled,'
              f'afade=t=in:d=0.6,afade=t=out:st={d - 1.2:.2f}:d=1.2[a{i}]')
for k in range(3): fl.append(f'[{2 + k}]aformat=sample_fmts=fltp:channel_layouts=stereo[s{k}]')
fl.append('[s0][a0][s1][a1][s2]concat=n=5:v=0:a=1')
subprocess.run(cmd + ['-filter_complex', ';'.join(fl), '-ar', '48000', '-c:a', 'pcm_s24le', MIX], check=True)
S1, E1 = LEAD, LEAD + CLIPS[0][2]; S2 = E1 + GAP; E2 = S2 + CLIPS[1][2]; TOTAL = E2 + TAIL

# ---------- world: one long building, rooms on every floor, Haru walks floor 3 then climbs to the roof ----------
WALL, FH, Z = 18, 170, 1.65
KINDS = ['bedroom', 'desk', 'sofa', 'kitchen', 'plants', 'laundry', 'records', 'mart']
RW = 300
NR = 40
rr = random.Random(5)
FLOORS = [[rr.choice(KINDS) for _ in range(NR)] for _ in range(4)]
FLOORS[0] = [rr.choice(['mart', 'records', 'lobby']) for _ in range(NR)]
FLOORS[3][0:4] = ['bedroom', 'desk', 'sofa', 'plants']
STAIR_ROOM = 6; FLOORS[3][STAIR_ROOM] = 'stairs'
LIT = {(f, i): rr.random() < .6 for f in range(4) for i in range(NR)}
def floor_y(f): return -(WALL * (f + 1) + FH * f)          # floor surface of floor f (world y, ground = 0)
ROOF = floor_y(4) - 0
def room_x(i): return WALL + i * (RW + WALL)

def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def sky_cols(t):
    day = (hx('#7EC8FF'), hx('#DDF1FF')); dusk = (hx('#6E6AC8'), hx('#FFB38A')); night = (hx('#141A3A'), hx('#3B3168'))
    u = sm((t - S1 - 6) / 10); v = sm((t - S2 - 1) / 8)
    a = [lerp(d, k, u) for d, k in zip(day, dusk)]; return [lerp(x, n, v) for x, n in zip(a, night)], v
STARS = [(random.uniform(0, W), random.uniform(0, 600), random.uniform(1, 2.4)) for _ in range(140)]

# Haru path: (x world, floor y) over time
X0 = room_x(0) + RW * .62
SPEED = 40   # world px / s
STX0 = room_x(STAIR_ROOM) + RW * .15; STX1 = room_x(STAIR_ROOM) + RW * .85
def haru_state(t):
    """x, y (feet, world), walk, reach, press, don, bubble alpha"""
    walk = reach = press = 0.0; don = 1.0; ba = 0.0
    if t < S1:     # opening ritual in the bedroom
        x, y = X0, floor_y(3)
        reach = min(sm((t - .5) / .4), 1 - sm((t - 1.9) / .4)); don = sm((t - .9) / .7)
        if 1.6 <= t < 1.95: press = math.sin((t - 1.6) / .35 * math.pi)
        if t > 1.65: ba = 1 - sm((t - S1 - .1) / .5)
        walk = sm((t - (S1 - .2)) / .8)
        return x, y, walk, reach, press, don, ba
    # walk along floor 3 until the stairs, timed so Haru reaches the stair foot as song 1 ends
    if t < E1:
        u = (t - S1) / (E1 - S1); x = X0 + (STX0 - X0) * u; walk = min(1, sm((t - S1 + .2) / .8))
        return x, floor_y(3), walk, 0, 0, 1, 0
    if t < S2:     # climb the stairs to the roof
        u = (t - E1) / GAP; x = STX0 + (STX1 - STX0) * u; y = floor_y(3) + (ROOF - floor_y(3)) * u
        ba = min(sm(u / .2), 1 - sm((u - .7) / .3))
        return x, y, 1.0, 0, 0, 1, ba
    x = STX1 + 60 + SPEED * (min(t, E2) - S2)
    walk = 1.0 if t < E2 - 1.2 else 1 - sm((t - (E2 - 1.2)) / 1.2)
    if t > E2:
        reach = min(sm((t - E2 - .2) / .4), 1 - sm((t - E2 - 1.4) / .4)); don = 1 - sm((t - E2 - .7) / .7)
    return x, ROOF, walk, reach, press, don, 0

def draw_world(c, t, night, sk):
    top, bot = sk
    g = cairo.LinearGradient(0, -1400, 0, 400); g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bot)
    c.rectangle(-2000, -2000, 20000, 4000); c.set_source(g); c.fill()
    # far skyline (behind the building, seen above the roof)
    rs = random.Random(11)
    for i in range(60):
        bx = i * 260 - 400; bh = rs.uniform(60, 300); bw = rs.uniform(150, 240); top = ROOF - bh
        c.rectangle(bx, top, bw, -top); c.set_source_rgb(*lerp(hx('#B9D3F2'), hx('#2C2B55'), night)); c.fill_preserve(); c.set_source_rgba(*L, .25); c.set_line_width(2); c.stroke()
        if night > .3:
            for k in range(int(bh / 60)):
                for j in range(3):
                    if rs.random() < .45: c.rectangle(bx + 20 + j * 45, top + 30 + k * 60, 20, 24); c.set_source_rgba(1, .85, .45, (night - .3) * 1.4); c.fill()
    nb = night > .5
    w = WALL + NR * (RW + WALL)
    total = -floor_y(4) + WALL
    c.rectangle(0, -total, w, total); shape(c, hx('#F6E7D8'), 4)
    for f in range(4):
        fy = floor_y(f)
        for i, k in enumerate(FLOORS[f]):
            rx = room_x(i); ry = fy - FH
            if k == 'stairs':
                c.rectangle(rx, ry, RW, FH); c.set_source_rgb(*(lerp(hx('#F1ECE6'), hx('#2B2A50'), .5) if nb else hx('#F1ECE6'))); c.fill()
                n = 10; sx0, sx1 = rx + RW * .15, rx + RW * .85
                c.move_to(sx0, fy)
                for j in range(n): c.line_to(sx0 + (sx1 - sx0) * j / n, fy - (FH + WALL) * (j + 1) / n); c.line_to(sx0 + (sx1 - sx0) * (j + 1) / n, fy - (FH + WALL) * (j + 1) / n)
                c.line_to(sx1, fy); c.close_path(); shape(c, hx('#E9E2D6'))
            else:
                room(c, k, rx, ry, RW, FH, nb, LIT[(f, i)])
                if k == 'bedroom' and night > .5:   # stars glow brighter at night
                    c.rectangle(rx, ry, RW, FH); c.set_source_rgba(.6, 1, .4, .06); c.fill()
            c.rectangle(rx, ry, RW, FH); c.set_source_rgb(*L); c.set_line_width(3); c.stroke()
    # roof slab with an opening over the stairwell, string lights along the roof
    c.rectangle(-10, floor_y(4) + WALL - 4 - WALL, w + 20, 14); shape(c, hx('#B9A4C9'))
    sx = room_x(STAIR_ROOM); c.rectangle(sx + RW * .1, ROOF - 8, RW * .8, 16); c.set_source_rgb(*hx('#E9E2D6')); c.fill()
    for seg in range(8):
        x0 = room_x(STAIR_ROOM) + 220 + seg * 420; x1 = x0 + 400
        c.set_source_rgb(*L); c.set_line_width(3)
        c.move_to(x0, ROOF - 120); c.line_to(x0, ROOF); c.stroke()
        c.move_to(x0, ROOF - 120); c.curve_to(x0 + 130, ROOF - 85, x1 - 130, ROOF - 85, x1, ROOF - 120); c.stroke()
        for j in range(7):
            u = (j + .5) / 7; bx = x0 + u * 400; by = ROOF - 120 + 35 * 4 * u * (1 - u) * .85 + 6
            c.arc(bx, by, 8, 0, 6.3); shape(c, hx('#FFE27A') if night > .4 else hx('#FFF6D8'), 2)
            if night > .4: c.arc(bx, by, 22, 0, 6.3); c.set_source_rgba(1, .9, .4, .25 * night); c.fill()
        kind = seg % 4
        if kind == 0:   # two stools and a little table
            c.rectangle(x0 + 150, ROOF - 40, 44, 40); shape(c, hx('#FFC857')); c.rectangle(x0 + 230, ROOF - 40, 44, 40); shape(c, hx('#8FB8FF'))
            c.rectangle(x0 + 196, ROOF - 56, 30, 8); shape(c, hx('#D9A066'))
        elif kind == 1:   # water tank
            c.rectangle(x0 + 120, ROOF - 150, 120, 120); shape(c, hx('#CFD8E8')); c.rectangle(x0 + 130, ROOF - 30, 12, 30); shape(c, hx('#9AA3B8')); c.rectangle(x0 + 218, ROOF - 30, 12, 30); shape(c, hx('#9AA3B8'))
        elif kind == 2:   # potted plants
            for j in range(3):
                px = x0 + 110 + j * 70; c.rectangle(px - 18, ROOF - 40, 36, 40); shape(c, hx('#E07A5F'))
                c.arc(px, ROOF - 62, 26, 0, 6.3); shape(c, hx('#7ED6A0'))
        else:             # antenna + deck chair
            c.set_source_rgb(*L); c.move_to(x0 + 300, ROOF); c.line_to(x0 + 300, ROOF - 200); c.move_to(x0 + 270, ROOF - 170); c.line_to(x0 + 330, ROOF - 170); c.stroke()
            c.move_to(x0 + 110, ROOF); c.line_to(x0 + 150, ROOF - 30); c.line_to(x0 + 230, ROOF - 30); c.line_to(x0 + 250, ROOF - 70); c.stroke()

def bubble(c, x, y, a):
    if a < .02: return
    c.save(); c.translate(x, y); c.push_group(); c.set_line_width(4)
    rrect(c, -44, -32, 88, 64, 18); shape(c, (1, 1, 1), 4)
    c.move_to(-12, -16); c.line_to(18, 0); c.line_to(-12, 16); c.close_path(); c.set_source_rgb(*hx('#FF2D87')); c.fill()
    c.pop_group_to_source(); c.paint_with_alpha(a); c.restore()

CX, CY = 860, 690
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', MIX,
                       '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '384k', '-aac_coder', 'twoloop',
                       '-ar', '48000', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
phase = 0.0; camy = None
for fi in range(int(TOTAL * FPS)):
    t = fi / FPS
    x, y, walk, reach, press, don, ba = haru_state(t)
    sk, night = sky_cols(t)
    target = y; camy = target if camy is None else camy + (target - camy) * .12
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.save(); c.translate(CX, CY); c.scale(Z, Z); c.translate(-x, -camy)
    draw_world(c, t, night, sk)
    c.save(); c.translate(x, y); c.scale(.62, .62)
    ch.draw(c, 0, 0, t, L=L, outfit='signature', walk=walk, phase=phase, reach=reach, press=press, don=don)
    c.restore()
    bubble(c, x + 30, y - 200, ba)
    c.restore()
    phase += 2 * math.pi * .85 * walk / FPS
    fade = min(1.0, sm(t / .5), 1 - sm((t - (TOTAL - 1.1)) / 1.0))
    buf = np.ndarray((H, W, 4), np.uint8, s.get_data())[..., [2, 1, 0]].astype(np.float32) * fade
    ff.stdin.write(buf.astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait(); os.remove(MIX); print('done', OUT, f'{TOTAL:.1f}s')
