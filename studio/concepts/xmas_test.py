"""PLAY LIST 04 test video (no music): snowball opening, six ride segments with a stop + headphone tap in each,
snow-burst changes (scene, ride and outfit together), snowball ending where Haru takes the headphones off.
usage: python3 xmas_test.py OUT.mp4"""
import sys, math, random, subprocess
import cairo, numpy as np
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch, xmas, xmas_rides as R
exec(open('/home/user/lgh9766/studio/concepts/xmas_outfits.py').read().split('W, H =')[0])   # O: outfit drafts
W, H, FPS = xmas.W, xmas.H, 30
L = R.L
SEG = [  # scene, ride, outfit no., scroll speed px/s
    ('canal', 'skate', 4, 230), ('downtown', 'tram', 7, 300), ('park', 'sled', 2, 420),
    ('market', 'carriage', 5, 150), ('lane', 'walk', 6, 120), ('sky', 'sleigh', 3, 260)]
for i, (_, _, oi, _) in enumerate(SEG): ch.OUTFITS[f'_s{i}'] = O[oi - 1][1]
INTRO, SEGLEN, OUTRO = 4.0, 7.0, 6.0
TOTAL = INTRO + SEGLEN * len(SEG) + OUTRO
def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

def bubble(c, x, y, a):
    if a < .02: return
    c.save(); c.translate(x, y); c.push_group(); R.rrect(c, -44, -32, 88, 64, 18); R.shape(c, (1, 1, 1), L)
    c.move_to(-12, -16); c.line_to(18, 0); c.line_to(-12, 16); c.close_path(); c.set_source_rgb(*R.hx('#FF2D87')); c.fill()
    c.pop_group_to_source(); c.paint_with_alpha(a); c.restore()

HEAD = {'skate': (826, 660), 'tram': (612, 545), 'sled': (820, 640), 'carriage': (700, 620), 'walk': (827, 655), 'sleigh': (626, 260)}

def seg_state(t):
    """segment index, local time, moving 0..1, reach/press for the tap, bubble alpha"""
    i = min(len(SEG) - 1, int(max(0, t - INTRO) // SEGLEN)); u = max(0, t - INTRO) - i * SEGLEN
    stop = 3.0   # a 'song change' in the middle of each segment: slow down, tap, play bubble
    moving = 1 - sm((u - stop + .6) / .6) + sm((u - stop - 1.5) / .6)
    reach = sm((u - stop) / .3) * (1 - sm((u - stop - 1.1) / .3))
    press = max(0, math.sin((u - stop - .3) / .5 * math.pi)) if stop + .3 < u < stop + .8 else 0
    ba = sm((u - stop - .4) / .2) * (1 - sm((u - stop - 1.6) / .3))
    if t < INTRO: moving, reach, press, ba = 0, 0, 0, 0
    return i, u, max(0, min(1, moving)), reach, press, ba

POS = [0.0]
for f in range(int(TOTAL * FPS) + 2):
    t = f / FPS; i, u, mv, *_ = seg_state(t)
    if t > TOTAL - OUTRO + 1.0: mv *= max(0, 1 - (t - (TOTAL - OUTRO + 1.0)) / 1.0)
    POS.append(POS[-1] + SEG[i][3] * mv / FPS)

def scene_frame(t):
    i, u, mv, reach, press, ba = seg_state(t)
    scene, ride, _, _ = SEG[i]; fn, m = xmas.SCENES[scene]; outfit = f'_s{i}'
    scroll = POS[min(len(POS) - 1, int(t * FPS))] + i * 900
    tt = t if t < TOTAL - OUTRO + 2.5 else TOTAL - OUTRO + 2.5      # the ending freezes the falling snow
    don = 1.0
    if t < INTRO: don = sm((t - 1.6) / 1.4)
    if t > TOTAL - OUTRO: don = 1 - sm((t - (TOTAL - OUTRO) - .3) / 1.4)
    kw = dict(reach=reach, press=press, don=don)
    if t < INTRO: kw['reach'] = sm((t - 1.4) / .3) * (1 - sm((t - 3.1) / .3))
    if t > TOTAL - OUTRO: kw['reach'] = sm((t - (TOTAL - OUTRO)) / .3) * (1 - sm((t - (TOTAL - OUTRO) - 1.8) / .3))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    fn(c, m, scroll, tt)
    if ride == 'skate': R.skate(c, 820, 930, tt, outfit, moving=mv, **kw)
    elif ride == 'tram': R.tram(c, 820, 935, tt, outfit, moving=mv, **kw)
    elif ride == 'sled': R.sled(c, 820, 900, tt, outfit, tilt=.12 * mv, moving=mv, **kw)
    elif ride == 'carriage': R.carriage(c, 700, 900, tt, outfit, lit=True, moving=mv, **kw)
    elif ride == 'walk': R.haru(c, 820, 900, tt, outfit, walk=mv, phase=2 * math.pi * .85 * scroll / 130, scale=1.2, **kw)
    else: R.sky_sleigh(c, 620, 470, tt, outfit, moving=mv, **kw)
    bubble(c, HEAD[ride][0] - 110, HEAD[ride][1] - 60, ba)
    # snow burst: the change of scene, ride and outfit happens under a flurry
    for edge in [INTRO + SEGLEN * k for k in range(1, len(SEG))]:
        v = (t - edge) / .6
        if -1 < v < 1:
            a = 1 - abs(v); r = random.Random(int(edge))
            c.set_source_rgba(1, 1, 1, .85 * sm(a * 1.4)); c.paint()
            for _ in range(120):
                x, y, sz = r.uniform(0, W), r.uniform(0, H), r.uniform(10, 60)
                c.arc(x + 300 * v, y + 200 * v, sz * a, 0, 6.3); c.set_source_rgba(1, 1, 1, .9 * a); c.fill()
    s.flush()
    return np.ndarray((H, W, 4), np.uint8, s.get_data())[..., [2, 1, 0]].copy()

def snowball(img, k, shake=0.0, settle=0.0):
    """show the frame inside a snow globe on a table; k 0 = globe small, 1 = inside (frame fills the screen)"""
    if k >= .999: return img
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    g = cairo.RadialGradient(W / 2, H / 2, 100, W / 2, H / 2, 1200); g.add_color_stop_rgb(0, .32, .2, .26); g.add_color_stop_rgb(1, .12, .08, .14); c.set_source(g); c.paint()
    for j in range(40): R.glow(c, (j * 173) % W, (j * 97) % 500, 40, (1, .8, .5), .25)
    c.rectangle(0, 860, W, 220); c.set_source_rgb(.45, .28, .2); c.fill()
    rad = 300 + (math.hypot(W, H) / 2 + 40 - 300) * k ** 2.2
    cx, cy = W / 2 + 18 * math.sin(shake * 40) * (1 - k), 520 + (H / 2 - 520) * k
    c.save(); c.translate(cx, cy); c.rotate(.06 * math.sin(shake * 40) * (1 - k))
    bw = rad * 1.3; c.set_line_width(5)
    R.rrect(c, -bw / 2, rad * .78, bw, rad * .42, 30); R.shape(c, R.hx('#8C4A3C'), L)
    c.rectangle(-bw / 2 + 20, rad * .9, bw - 40, rad * .08); c.set_source_rgb(*R.hx('#F2C230')); c.fill()
    if rad < 900:
        c.select_font_face('Outfit', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(rad * .11)
        e = c.text_extents('OPEN TO CLOSE'); c.move_to(-e.width / 2, rad * 1.08); c.set_source_rgb(1, .96, .85); c.show_text('OPEN TO CLOSE')
    c.arc(0, 0, rad, 0, 6.3); c.clip()
    src = cairo.ImageSurface.create_for_data(np.ascontiguousarray(np.dstack([img[..., 2], img[..., 1], img[..., 0], np.full(img.shape[:2], 255, np.uint8)])), cairo.FORMAT_ARGB32, W, H)
    sc = (2 * rad) / H * .62 + (1 - .62) * k
    sc = max(sc, (2 * rad) / H * .62); c.scale(sc, sc); c.set_source_surface(src, -W / 2 - 0, -H / 2 - 80 * (1 - k)); c.paint()
    c.restore()
    c.save(); c.translate(cx, cy); c.arc(0, 0, rad, 0, 6.3); c.set_line_width(6); c.set_source_rgba(1, 1, 1, .7); c.stroke()
    c.arc(-rad * .35, -rad * .4, rad * .25, 3.6, 4.6); c.set_line_width(rad * .05); c.set_source_rgba(1, 1, 1, .35); c.stroke(); c.restore()
    r = random.Random(2)
    for _ in range(int(160 * (1 - k))):
        a, d = r.uniform(0, 6.3), r.uniform(0, rad * .95)
        y = cy + d * math.sin(a) - 60 * shake * r.random(); x = cx + d * math.cos(a)
        c.arc(x, y, r.uniform(2, 6), 0, 6.3); c.set_source_rgba(1, 1, 1, .9); c.fill()
    s.flush()
    return np.ndarray((H, W, 4), np.uint8, s.get_data())[..., [2, 1, 0]].copy()

out = sys.argv[1]
if out.endswith('/'):   # stills mode: python3 xmas_test.py DIR/ t1,t2,...
    from PIL import Image
    for tv in sys.argv[2].split(','):
        t = float(tv); img = scene_frame(t)
        if t < INTRO: img = snowball(img, sm((t - 1.0) / 2.6), shake=max(0, 1 - t / 1.2))
        elif t > TOTAL - OUTRO + 2.2: img = snowball(img, 1 - sm((t - (TOTAL - OUTRO + 2.2)) / 2.6))
        Image.fromarray(img).save(f'{out}{t:05.1f}.png')
    sys.exit()
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
N = int(TOTAL * FPS)
for f in range(N):
    t = f / FPS; img = scene_frame(t)
    if t < INTRO:   # shake the globe, then dive in
        img = snowball(img, sm((t - 1.0) / 2.6), shake=max(0, 1 - t / 1.2))
    elif t > TOTAL - OUTRO + 2.2:   # snow stops, pull back out into the globe
        img = snowball(img, 1 - sm((t - (TOTAL - OUTRO + 2.2)) / 2.6))
    ff.stdin.write(img.tobytes())
    if f % 150 == 0: print(f'{t:.0f}s / {TOTAL:.0f}s', flush=True)
ff.stdin.close(); ff.wait(); print('done', out)
