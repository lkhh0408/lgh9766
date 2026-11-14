"""PLAY LIST 03 test clip: seaside bicycle ride (~37 s).
opening (headphones on, helmet on) -> song 1 by day in sunglasses -> red light: stop, tap, sunglasses up onto the helmet
-> green: ride on into sunset and night -> stop, headphones off, fade."""
import math, os, re, subprocess, sys
import numpy as np, cairo
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sea2, mob
from sea2 import scene as sea_scene, W, H, hx, lerp, shape, L, rrect
import character as ch
FPS = 24; OUT = os.path.join(HERE, 'bike_test.mp4')

# ---------- audio (fixed gain to -14 LUFS, limiter, 24-bit, silent lead / gap / tail) ----------
CLIPS = [('41', 43.3, 13.0), ('52', 38.2, 13.0)]
LEAD, GAP, TAIL = 3.2, 3.0, 3.2
def song(n): return [os.path.join(SP, 'vol03_songs', f) for f in os.listdir(os.path.join(SP, 'vol03_songs')) if f.startswith(n + '.')][0]
def lufs(p, ss, d):
    e = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-ss', str(ss), '-t', str(d), '-i', p, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', e)[-1])
MIX = os.path.join(HERE, 'bike_mix.wav')
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

def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
OUTFIT = dict(top='#FF9F8A', bottom='#3E4A6B', shoe='#FFFFFF', phones='#FFD84A', phones_style='retro', helmet='#7ED6C4', helmet_stripe='#FFFFFF', detail='scarf', scarf='#2F3E6B')
FRAME = '#2F3E6B'   # navy bicycle
mob.O = OUTFIT

def ride(t):
    """riding speed 0..1: still during the opening, braking for the red light, still at the end"""
    v = sm((t - (S1 - .3)) / 1.0)
    v = min(v, max(1 - sm((t - (E1 - 1.2)) / 1.2), sm((t - (S2 - .4)) / 1.0)))
    v = min(v, 1 - sm((t - (E2 - 1.2)) / 1.2))
    return v
SPEED = 260
POS = [0.0]
for fi in range(int(TOTAL * FPS) + 2): POS.append(POS[-1] + SPEED * ride(fi / FPS) / FPS)
def scroll_at(t): return POS[min(len(POS) - 1, int(t * FPS))]
LIGHT_X = scroll_at(E1 + .2) + 1180    # the traffic light stands just ahead of where Haru stops

def sky_mode(t):
    """blend weights for day / dusk / night"""
    a = sm((t - (E1 - 1.0)) / 4.0)        # day -> dusk around the red light
    b = sm((t - (S2 + 5.0)) / 5.0)        # dusk -> night during song 2
    return a, b

def bike_haru(c, t, ph, o, don, reach, press, sun, helmet_k):
    """mob.bike with extras: headphones don/reach, sunglasses (sun: 1 on the eyes, 0 pushed up on the helmet), helmet_k (0 off .. 1 on)"""
    pants, top = hx(o['bottom']), hx(o['top'])
    frame = hx(FRAME)
    rw, fw, cr = (-78, -42), (86, -42), (0, -40)
    ang = ph * 1.2
    mob.wheel(c, *rw, 40, ang, L); mob.wheel(c, *fw, 40, ang, L)
    sad, head_t, bar = (-22, -106), (56, -122), (46, -146)
    hip = (sad[0] + 2, sad[1] - 6)
    pb = (cr[0] + 18 * math.cos(ph + math.pi), cr[1] + 18 * math.sin(ph + math.pi))
    mob.leg_to(c, hip, pb, pants, L, True)
    c.set_line_width(7); c.set_source_rgb(*frame)
    mob.poly(c, [rw, cr, sad]); mob.poly(c, [rw, (sad[0] + 4, sad[1] + 8)]); mob.poly(c, [(sad[0] + 4, sad[1] + 8), head_t]); mob.poly(c, [cr, head_t]); mob.poly(c, [fw, head_t, bar])
    c.set_line_width(5); c.set_source_rgb(*L); mob.poly(c, [(bar[0] - 6, bar[1]), (bar[0] + 14, bar[1] - 4)])
    c.set_line_width(3); c.save(); c.translate(*sad); c.scale(1, .45); c.arc(0, 0, 18, 0, 2 * math.pi); c.restore(); shape(c, hx('#4A3F35'), L)
    c.arc(cr[0], cr[1], 11, 0, 2 * math.pi); shape(c, (.85, .87, .92), L)
    mob.cup(c, 82, -134, t, L, o)
    c.set_line_width(3); c.move_to(62, -140); c.line_to(104, -140); c.line_to(98, -112); c.line_to(68, -112); c.close_path(); shape(c, hx('#E3B778'), L)
    c.move_to(70, -128); c.line_to(98, -128); c.stroke()
    sh = (hip[0] + 6, hip[1] - 62)
    hxh, hyh = hip[0] + 18, hip[1] - 112
    # back hand: handlebar, or reaching for the headphone cup
    if reach > 0:
        _, _, _, _, _, cx_, cy_ = ch.phones_pose(hxh, hyh, 42, don)
        tgt = (bar[0] - 2 + (cx_ + 4 - bar[0] + 2) * reach, bar[1] + 2 + (cy_ + 4 - press * 2 - bar[1] - 2) * reach)
    else: tgt = (bar[0] - 2, bar[1] + 2)
    mob.arm_to(c, sh, tgt, top, L, True)
    c.save(); c.translate(hip[0], hip[1]); c.rotate(math.radians(10)); c.translate(-hip[0], -hip[1])
    mob.torso(c, hip, o, L, top)
    c.restore()
    pf = (cr[0] + 18 * math.cos(ph), cr[1] + 18 * math.sin(ph))
    mob.leg_to(c, hip, pf, pants, L, False)
    c.set_line_width(4); c.set_source_rgb(*L); mob.poly(c, [(cr[0] - 18 * math.cos(ph), cr[1] - 18 * math.sin(ph)), (pf[0], pf[1])])
    # head without helmet first, headphones at their ritual pose, then helmet dropping on
    o2 = dict(o); o2.pop('helmet', None)
    R = 42
    mob.head.__globals__['ch']._phones  # (same module)
    _head_no_phones(c, hxh, hyh, t)
    ch._phones(c, 'retro', hxh, hyh, R, hx(o['phones']), L, don)
    gx, gy2 = hxh + 24, hyh + 4
    if sun > 0.001:   # round sunglasses over the round glasses, sliding up onto the helmet
        oy = -58 * (1 - sun)
        c.save(); c.translate(0, oy)
        c.arc(gx, gy2, 15, 0, 2 * math.pi); c.set_source_rgba(.13, .12, .2, .9); c.fill_preserve(); c.set_source_rgb(*L); c.set_line_width(4); c.stroke()
        c.set_line_width(4); c.move_to(gx - 15, gy2 - 2); c.line_to(hxh - 16, gy2 - 4); c.stroke()
        c.set_source_rgba(1, 1, 1, .8); c.set_line_width(3); c.arc(gx - 4, gy2 - 5, 6, math.pi * 1.1, math.pi * 1.6); c.stroke()
        c.restore()
    if helmet_k > 0.001:
        c.save(); c.translate(0, -70 * (1 - helmet_k)); mob.helmet(c, hxh, hyh, R, o, L); c.restore()
    if sun <= 0.001:   # sunglasses resting on top of the helmet (after the red light)
        c.save(); c.translate(hxh + 4, hyh - R - 22); c.rotate(-.1)
        c.arc(0, 0, 11, math.pi, 2 * math.pi); c.close_path(); c.set_source_rgba(.13, .12, .2, .95); c.fill_preserve(); c.set_source_rgb(*L); c.set_line_width(3); c.stroke()
        c.restore()
    mob.arm_to(c, sh, (bar[0] + 4, bar[1]), top, L, False)

def _head_no_phones(c, hx_, hy_, t):
    R = 42; SKIN, HAIR = ch.SKIN, ch.HAIR
    c.set_line_width(4); c.arc(hx_, hy_, R, 0, 2 * math.pi); shape(c, SKIN, L)
    c.save(); c.arc(hx_, hy_, R + 1, 0, 2 * math.pi); c.clip()
    c.move_to(hx_ + R + 4, hy_ - 12); c.curve_to(hx_ + 20, hy_ - 22, hx_ - 6, hy_ - 16, hx_ - 12, hy_ - 4)
    c.line_to(hx_ - 14, hy_ + 30); c.line_to(hx_ - R - 6, hy_ + 30); c.line_to(hx_ - R - 6, hy_ - R - 6); c.line_to(hx_ + R + 6, hy_ - R - 6); c.close_path()
    c.set_source_rgb(*HAIR); c.fill(); c.restore()
    c.set_source_rgb(*L); c.set_line_width(4); c.arc(hx_, hy_, R, 0, 2 * math.pi); c.stroke()
    gx, gy2 = hx_ + 24, hy_ + 4
    c.set_line_width(4); c.move_to(gx - 14, gy2 - 2); c.line_to(hx_ - 16, gy2 - 4); c.stroke()
    c.arc(gx, gy2, 14, 0, 2 * math.pi); c.set_source_rgba(1, 1, 1, .45); c.fill_preserve(); c.set_source_rgb(*L); c.stroke()
    if (t % 4.0) < 0.12: c.move_to(gx - 2, gy2 + 1); c.line_to(gx + 6, gy2 + 1); c.stroke()
    else: c.arc(gx + 2, gy2 + 1, 3.6, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(1, .45, .55, .45); c.arc(gx + 4, gy2 + 22, 7, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*L); c.set_line_width(3); c.arc(hx_ + 30, hy_ + 26, 6, math.radians(10), math.radians(120)); c.stroke()

def state(t):
    don = 1.0; reach = press = 0.0; helmet_k = 1.0; sun = 1.0; ba = 0.0
    if t < S1:    # opening: headphones from the neck onto the head, tap play, helmet on
        reach = min(sm((t - .5) / .4), 1 - sm((t - 1.9) / .4)); don = sm((t - .9) / .7)
        if 1.6 <= t < 1.95: press = math.sin((t - 1.6) / .35 * math.pi)
        if t > 1.65: ba = 1 - sm((t - 2.6) / .5)
        helmet_k = sm((t - 2.2) / .6)
    if E1 - .2 < t < S2:   # red light: tap for the next song, push the sunglasses up
        reach = min(sm((t - E1 + .1) / .4), 1 - sm((t - E1 - 1.3) / .4))
        if E1 + .3 <= t < E1 + .65: press = math.sin((t - E1 - .3) / .35 * math.pi)
        if t > E1 + .35: ba = 1 - sm((t - S2 + .2) / .5)
    sun = 1 - sm((t - (E1 + 1.4)) / .6)
    if t > E2:   # ending: headphones off onto the neck
        reach = min(sm((t - E2 - .2) / .4), 1 - sm((t - E2 - 1.4) / .4)); don = 1 - sm((t - E2 - .7) / .7)
    return don, reach, press, helmet_k, sun, ba

def traffic_light(c, x, t):
    green = t > S2 - .4
    c.set_line_width(6); c.set_source_rgb(*L); c.move_to(x, 900); c.line_to(x, 700); c.stroke()
    rrect(c, x - 22, 620, 44, 90, 12); shape(c, hx('#2B2541'), L)
    c.arc(x, 645, 13, 0, 6.3); c.set_source_rgb(*(hx('#FF5A5A') if not green else hx('#5A3A3A'))); c.fill()
    c.arc(x, 685, 13, 0, 6.3); c.set_source_rgb(*(hx('#3AD98A') if green else hx('#24453A'))); c.fill()
    for k in range(6): c.rectangle(x + 30 + k * 34, 900, 20, 170); c.set_source_rgba(1, 1, 1, .85); c.fill()

def bubble(c, x, y, a):
    if a < .02: return
    c.save(); c.translate(x, y); c.push_group(); rrect(c, -44, -32, 88, 64, 18); shape(c, (1, 1, 1), L)
    c.move_to(-12, -16); c.line_to(18, 0); c.line_to(-12, 16); c.close_path(); c.set_source_rgb(*hx('#FF2D87')); c.fill()
    c.pop_group_to_source(); c.paint_with_alpha(a); c.restore()

def render_bg(t, scroll):
    a, b = sky_mode(t)
    imgs = {}
    for m in ('day', 'dusk', 'night'):
        w = {'day': (1 - a) * (1 - b), 'dusk': a * (1 - b), 'night': b}[m]
        if w > .002: imgs[m] = w
    out = None
    for m, w in imgs.items():
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
        c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        sea_scene(c, m, scroll, t)
        arr = np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32) * w
        out = arr if out is None else out + arr
    return out

CXH = 880
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', MIX,
                       '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '384k', '-aac_coder', 'twoloop',
                       '-ar', '48000', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
ph = 0.0
for fi in range(int(TOTAL * FPS)):
    t = fi / FPS; sc = scroll_at(t)
    bg = render_bg(t, sc)
    s = cairo.ImageSurface.create_for_data(np.ascontiguousarray(bg.clip(0, 255).astype(np.uint8)), cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    lx = LIGHT_X - sc
    if -300 < lx < W + 300: traffic_light(c, lx, t)
    don, reach, press, helmet_k, sun, ba = state(t)
    c.save(); c.translate(CXH, 860)
    bike_haru(c, t, ph, OUTFIT, don, reach, press, sun, helmet_k)
    c.restore()
    bubble(c, CXH + 60, 860 - 300, ba)
    ph += 2 * math.pi * 1.0 * ride(t) / FPS
    s.flush()
    fade = min(1.0, sm(t / .5), 1 - sm((t - (TOTAL - 1.1)) / 1.0))
    buf = np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32); buf[..., :3] *= fade
    ff.stdin.write(buf.astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait(); os.remove(MIX); print('done', OUT, f'{TOTAL:.1f}s')
