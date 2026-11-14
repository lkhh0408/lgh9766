"""PLAY LIST 03 test: day bicycle -> sunset convertible -> night walk, with the two hand-over scenes (~43 s)."""
import math, os, re, subprocess, sys
import numpy as np, cairo
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sea2, mob
from sea2 import scene as sea_scene, W, H, hx, lerp, shape, L, rrect
import character as ch
from bike_test_lib import bike_haru, head_plain, bubble, OUTFIT, FRAME
FPS = 24; OUT = os.path.join(HERE, 'mix_test.mp4'); GY = 860; CXH = 880

# ---------- audio ----------
CLIPS = [('41', 43.3, 8.0), ('52', 38.2, 10.0), ('60', 21.5, 10.0)]
GAPS = [2.0, 1.5]; TAIL = 3.4
def song(n): return [os.path.join(SP, 'vol03_songs', f) for f in os.listdir(os.path.join(SP, 'vol03_songs')) if f.startswith(n + '.')][0]
def lufs(p, ss, d):
    e = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-ss', str(ss), '-t', str(d), '-i', p, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', e)[-1])
MIX = os.path.join(HERE, 'mix_mix.wav')
cmd = ['ffmpeg', '-y', '-loglevel', 'error']; fl = []
for n, ss, d in CLIPS: cmd += ['-ss', str(ss), '-t', str(d), '-i', song(n)]
for d in GAPS + [TAIL]: cmd += ['-f', 'lavfi', '-t', str(d), '-i', 'anullsrc=r=48000:cl=stereo']
for i, (n, ss, d) in enumerate(CLIPS):
    g = -14 - lufs(song(n), ss, d)
    fl.append(f'[{i}]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={g:.2f}dB,alimiter=limit={10 ** (-1.5 / 20):.4f}:attack=5:release=60:level=disabled,'
              f'afade=t=in:d=0.6,afade=t=out:st={d - 1.2:.2f}:d=1.2[a{i}]')
for k in range(3): fl.append(f'[{3 + k}]aformat=sample_fmts=fltp:channel_layouts=stereo[s{k}]')
fl.append('[a0][s0][a1][s1][a2][s2]concat=n=6:v=0:a=1')
subprocess.run(cmd + ['-filter_complex', ';'.join(fl), '-ar', '48000', '-c:a', 'pcm_s24le', MIX], check=True)
S1 = 0.0; E1 = S1 + CLIPS[0][2]; S2 = E1 + GAPS[0]; E2 = S2 + CLIPS[1][2]; S3 = E2 + GAPS[1]; E3 = S3 + CLIPS[2][2]; TOTAL = E3 + TAIL

def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
WALK_OUT = dict(top=OUTFIT['top'], bottom=OUTFIT['bottom'], phones=OUTFIT['phones'], phones_style='retro', prop='hot', scarf=OUTFIT['scarf'], shades_up=True)
CAR = '#7ED6C4'
ch.OUTFITS['pl03_walk'] = WALK_OUT

# ---------- motion plan ----------
T1_WALK = (E1 + .2, E1 + 1.25)        # walk from the parked bike to the car
def speed(t):
    if t < E1: return 260 * min(sm((t + .2) / .6), 1 - sm((t - (E1 - 1.2)) / 1.2))
    if t < S2: return 500 * min(sm((t - T1_WALK[0]) / .2), 1 - sm((t - (T1_WALK[1] - .2)) / .2))
    if t < S3: return 420 * min(sm((t - (S2 - .2)) / 1.2), 1 - sm((t - (E2 - 1.4)) / 1.4))
    return 130 * min(sm((t - (S3 - .2)) / .8), 1 - sm((t - (E3 - 1.2)) / 1.2))
POS = [0.0]
for fi in range(int(TOTAL * FPS) + 2): POS.append(POS[-1] + speed(fi / FPS) / FPS)
def scroll_at(t): return POS[min(len(POS) - 1, int(t * FPS))]
BIKE_PARK = scroll_at(E1 + .2) + CXH            # world x where the bike stays
CAR_PARK0 = scroll_at(T1_WALK[1] + .1) + CXH     # world x of the waiting car (Haru's seat lines up with CXH)
CAR_PARK1 = scroll_at(E2 + .2) + CXH             # where the car is left at night

def sky_w(t):
    a = sm((t - (E1 - 1.0)) / 4.0); b = sm((t - (E2 - 3.0)) / 5.0)
    return {'day': (1 - a) * (1 - b), 'dusk': a * (1 - b), 'night': b}

def convertible(c, x, t, ang, seated=None):
    """open-top car, seat centre at x. seated: dict with Haru's pose or None"""
    c.save(); c.translate(x, GY)
    col = hx(CAR)
    # rear seat back
    rrect(c, -78, -132, 34, 70, 10); shape(c, hx('#F3E9D2'), L)
    if seated: seated_haru(c, t, **seated)
    # body
    c.set_line_width(4)
    c.move_to(-190, -40); c.line_to(-196, -88); c.curve_to(-196, -100, -186, -104, -170, -104); c.line_to(40, -104)
    c.curve_to(90, -104, 150, -96, 196, -80); c.curve_to(214, -74, 220, -60, 216, -44); c.line_to(210, -36); c.line_to(-184, -36); c.close_path(); shape(c, col, L)
    c.move_to(-170, -78); c.line_to(200, -70); c.set_line_width(3); c.set_source_rgb(*lerp(col, (1, 1, 1), .5)); c.stroke()
    c.move_to(-60, -102); c.line_to(-60, -44); c.set_source_rgb(*L); c.set_line_width(3); c.stroke()          # door line
    rrect(c, -40, -88, 22, 6, 3); shape(c, (.9, .9, .95), L)                                                    # handle
    c.move_to(60, -104); c.line_to(86, -160); c.line_to(96, -158); c.line_to(76, -104); c.close_path()           # windshield
    c.set_source_rgba(.85, .95, 1, .55); c.fill_preserve(); c.set_source_rgb(*L); c.stroke()
    c.arc(206, -64, 9, 0, 6.3); shape(c, hx('#FFF4C2'), L); c.rectangle(-196, -78, 10, 16); shape(c, hx('#FF6B5B'), L)
    mob.wheel(c, -120, -30, 34, ang, L); mob.wheel(c, 132, -30, 34, ang, L)
    if seated:   # front arm to the wheel, over the door
        sh = seated_haru.sh; mob.arm_to(c, sh, (52, -128), hx(OUTFIT['top']), L, False)
    c.set_line_width(5); c.set_source_rgb(*L); c.arc(52, -128, 16, 0, 6.3); c.stroke()
    c.restore()

def seated_haru(c, t, sh=None, don=1.0, reach=0.0, press=0.0, wind=0.0):
    hip = (-20, -66); top = hx(OUTFIT['top'])
    hxh, hyh = hip[0] + 6, hip[1] - 116
    # back arm: to the wheel, or reaching for the headphone cup
    tgt = (40, -132)
    if reach > 0:
        _, _, _, _, _, cx_, cy_ = ch.phones_pose(hxh, hyh, 42, don)
        tgt = (tgt[0] + (cx_ + 4 - tgt[0]) * reach, tgt[1] + (cy_ + 4 - press * 2 - tgt[1]) * reach)
    mob.arm_to(c, (hip[0] + 4, hip[1] - 62), tgt, top, L, True)
    # muffler tail streaming in the wind
    sc = hx(OUTFIT['scarf']); x, y = hip
    c.set_line_width(3); c.move_to(x - 10, y - 74)
    c.curve_to(x - 40, y - 74 + 6 * math.sin(t * 9), x - 60, y - 70 - 6 * math.sin(t * 9 + 1), x - 80 - 10 * wind, y - 66 + 4 * math.sin(t * 11))
    c.line_to(x - 76 - 10 * wind, y - 54 + 4 * math.sin(t * 11)); c.curve_to(x - 56, y - 60, x - 36, y - 62, x - 10, y - 62); c.close_path(); shape(c, sc, L)
    mob.torso(c, hip, dict(OUTFIT, bag=None), L, top)
    head_plain(c, hxh, hyh, t)
    ch._phones(c, 'retro', hxh, hyh, 42, hx(OUTFIT['phones']), L, don)
    ch.shades_on_head(c, hxh, hyh, 42, L)
    seated_haru.sh = (hip[0] + 4, hip[1] - 62)

def parked_bike(c, x):
    c.save(); c.translate(x, GY)
    rw, fw, cr = (-78, -42), (86, -42), (0, -40)
    mob.wheel(c, *rw, 40, 0, L); mob.wheel(c, *fw, 40, 0, L)
    sad, head_t, bar = (-22, -106), (56, -122), (46, -146)
    c.set_line_width(7); c.set_source_rgb(*hx(FRAME))
    mob.poly(c, [rw, cr, sad]); mob.poly(c, [rw, (sad[0] + 4, sad[1] + 8)]); mob.poly(c, [(sad[0] + 4, sad[1] + 8), head_t]); mob.poly(c, [cr, head_t]); mob.poly(c, [fw, head_t, bar])
    c.set_line_width(5); c.set_source_rgb(*L); mob.poly(c, [(bar[0] - 6, bar[1]), (bar[0] + 14, bar[1] - 4)])
    c.set_line_width(3); c.save(); c.translate(*sad); c.scale(1, .45); c.arc(0, 0, 18, 0, 2 * math.pi); c.restore(); shape(c, hx('#4A3F35'), L)
    c.move_to(62, -140); c.line_to(104, -140); c.line_to(98, -112); c.line_to(68, -112); c.close_path(); shape(c, hx('#E3B778'), L)
    # helmet hung on the handlebar
    c.save(); c.translate(bar[0] + 6, bar[1] + 30); c.scale(.55, .55); mob.helmet(c, 0, 0, 42, OUTFIT, L); c.restore()
    c.set_line_width(7); c.set_source_rgb(*L); c.move_to(-60, -40); c.line_to(-70, 0); c.stroke()   # kickstand
    c.restore()

def render(t, scroll, ph, wph):
    ws = sky_w(t); out = None
    for m, w in ws.items():
        if w < .002: continue
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
        c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        sea_scene(c, m, scroll, t)
        a = np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32) * w
        out = a if out is None else out + a
    s = cairo.ImageSurface.create_for_data(np.ascontiguousarray(out.clip(0, 255).astype(np.uint8)), cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    def layer(fn, alpha):
        if alpha <= .01: return
        c.push_group(); fn(); c.pop_group_to_source(); c.paint_with_alpha(min(1, alpha))
    ba = 0.0
    # ---- day: bicycle ----
    if t < E1 + .2:
        sun = 1 - sm((t - (E1 - .6)) / .4); helm = 1 - sm((t - (E1 - .6)) / .4)
        rider = 1 - sm((t - (E1 - .05)) / .25)
        if t >= E1 - .05:
            bx = BIKE_PARK - scroll; layer(lambda: parked_bike(c, bx), 1 - rider)
        def b():
            c.save(); c.translate(CXH, GY); bike_haru(c, t, ph, OUTFIT, 1.0, 0, 0, sun, helm); c.restore()
        layer(b, rider)
        walker_a = sm((t - (E1 - .05)) / .25)
        if walker_a > 0:
            layer(lambda: ch.draw(c, CXH, GY, t, L=L, outfit='pl03_walk', walk=0, phase=wph), walker_a)
    # ---- hand-over 1: walk to the car, get in ----
    if E1 - .05 <= t < S2 + 2:
        bx = BIKE_PARK - scroll
        if t >= E1 + .2 and -300 < bx < W + 300: parked_bike(c, bx)
    if E1 + .2 <= t < S2:
        cx = CAR_PARK0 - scroll
        inside = sm((t - T1_WALK[1]) / .2)
        reach = min(sm((t - (T1_WALK[1] + .15)) / .2), 1 - sm((t - (S2 - .2)) / .2)); press = math.sin((t - (T1_WALK[1] + .3)) / .3 * math.pi) if T1_WALK[1] + .3 <= t < T1_WALK[1] + .6 else 0
        convertible(c, cx, t, 0, seated=dict(reach=reach, press=press) if inside > .5 else None)
        w = walk_amt(t)
        layer(lambda: ch.draw(c, CXH, GY, t, L=L, outfit='pl03_walk', walk=w, phase=wph), 1 - inside)
        if t > T1_WALK[1] + .35: ba = 1 - sm((t - (S2 + .1)) / .5)
    # ---- sunset: convertible ----
    if S2 <= t < S3:
        if t < E2 + .3:
            convertible(c, CXH, t, ph * 1.4, seated=dict(wind=sm(speed(t) / 420)))
        else:
            cx = CAR_PARK1 - scroll
            out_a = sm((t - (E2 + .05)) / .25)
            convertible(c, cx, t, 0, seated=dict() if out_a < .5 else None)
            reach = min(sm((t - (E2 + .3)) / .2), 1 - sm((t - (E2 + 1.1)) / .25)); press = math.sin((t - (E2 + .45)) / .3 * math.pi) if E2 + .45 <= t < E2 + .75 else 0
            layer(lambda: ch.draw(c, CXH, GY, t, L=L, outfit='pl03_walk', walk=0, phase=wph, reach=reach, press=press), out_a)
            if t > E2 + .5: ba = 1 - sm((t - (S3 + .1)) / .5)
    # ---- night: walking ----
    if t >= S3:
        cx = CAR_PARK1 - scroll
        if -400 < cx < W + 400: convertible(c, cx, t, 0)
        don = 1 - sm((t - (E3 + .7)) / .7) if t > E3 else 1.0
        reach = min(sm((t - E3 - .2) / .4), 1 - sm((t - E3 - 1.4) / .4)) if t > E3 else 0
        ch.draw(c, CXH, GY, t, L=L, outfit='pl03_walk', walk=walk_amt(t), phase=wph, reach=reach, don=don)
    bubble(c, CXH + 60, GY - 300, ba)
    s.flush()
    fade = min(1.0, sm(t / .5), 1 - sm((t - (TOTAL - 1.1)) / 1.0))
    buf = np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32); buf[..., :3] *= fade
    return buf.astype(np.uint8)

def walk_amt(t):
    if E1 < t < S2: return min(1.0, speed(t) / 500)
    if t >= S3: return min(1.0, speed(t) / 130)
    return 0.0

ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', MIX,
                       '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '384k', '-aac_coder', 'twoloop',
                       '-ar', '48000', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
ph = wph = 0.0
STILLS = [float(v) for v in sys.argv[1].split(',')] if len(sys.argv) > 1 else None
for fi in range(int(TOTAL * FPS)):
    t = fi / FPS; sc = scroll_at(t)
    if STILLS is None or any(abs(t - v) < .5 / FPS for v in STILLS):
        img = render(t, sc, ph, wph)
        if STILLS is None: ff.stdin.write(img.tobytes())
        else: cairo.ImageSurface.create_for_data(np.ascontiguousarray(img), cairo.FORMAT_ARGB32, W, H).write_to_png(os.path.join(HERE, f'mix_{t:05.1f}.png'))
    ph += 2 * math.pi * (speed(t) / 260 if t < E1 else 0) / FPS
    if S2 <= t < S3: ph += 2 * math.pi * speed(t) / 420 / FPS
    wph += 2 * math.pi * .85 * walk_amt(t) * (3.0 if E1 < t < S2 else 1.0) / FPS
ff.stdin.close(); ff.wait(); os.remove(MIX); print('done', OUT, f'{TOTAL:.1f}s')
