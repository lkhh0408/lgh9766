"""PLAY LIST 04 test video (no music): opening where Haru puts the headphones on, six ride segments with a stop + headphone tap
in each, snow-burst changes (scene, ride and outfit together), ending where Haru takes the headphones off.
usage: python3 xmas_test.py OUT.mp4"""
import sys, math, random, subprocess
import cairo, numpy as np
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch, xmas, xmas_rides as R
exec(open('/home/user/lgh9766/studio/concepts/xmas_outfits.py').read().split('W, H =')[0])   # O: outfit drafts
W, H, FPS = xmas.W, xmas.H, 30
L = R.L
SEG = [  # scene, ride, outfit no., scroll speed px/s
    ('canal', 'skate', 4, 230), ('downtown', 'tram', 7, 300), ('park', 'dogsled', 2, 420),
    ('market', 'carriage', 5, 150), ('lane', 'walk', 6, 120), ('sky', 'sleigh', 3, 260)]
for i, (_, _, oi, _) in enumerate(SEG): ch.OUTFITS[f'_s{i}'] = O[oi - 1][1]
INTRO, SEGLEN, OUTRO = 3.5, 7.0, 4.0
TOTAL = INTRO + SEGLEN * len(SEG) + OUTRO
def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

def bubble(c, x, y, a):
    if a < .02: return
    c.save(); c.translate(x, y); c.push_group(); R.rrect(c, -44, -32, 88, 64, 18); R.shape(c, (1, 1, 1), L)
    c.move_to(-12, -16); c.line_to(18, 0); c.line_to(-12, 16); c.close_path(); c.set_source_rgb(*R.hx('#FF2D87')); c.fill()
    c.pop_group_to_source(); c.paint_with_alpha(a); c.restore()

HEAD = {'skate': (826, 724), 'tram': (786, 730), 'dogsled': (470, 728), 'carriage': (566, 664), 'walk': (827, 658), 'sleigh': (616, 280)}

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
    elif ride == 'tram': R.tram(c, 820, 950, tt, outfit, moving=mv, **kw)
    elif ride == 'dogsled': R.dogsled(c, 560, 930, tt, outfit, moving=mv, **kw)
    elif ride == 'carriage': R.carriage(c, 620, 930, tt, outfit, lit=True, moving=mv, **kw)
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

out = sys.argv[1]
if out.endswith('/'):   # stills mode: python3 xmas_test.py DIR/ t1,t2,...
    from PIL import Image
    for tv in sys.argv[2].split(','):
        t = float(tv); img = scene_frame(t)
        Image.fromarray(img).save(f'{out}{t:05.1f}.png')
    sys.exit()
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
N = int(TOTAL * FPS)
for f in range(N):
    t = f / FPS; img = scene_frame(t)
    ff.stdin.write(img.tobytes())
    if f % 150 == 0: print(f'{t:.0f}s / {TOTAL:.0f}s', flush=True)
ff.stdin.close(); ff.wait(); print('done', out)
