"""PLAY LIST 03 draft: apartment cross-section concept (stills only)."""
import math, sys, random
import cairo
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch

W, H = 1920, 1080
OUT = sys.argv[1]
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
L = hx('#2B2541')
def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))

def shape(c, fill, lw=3):
    c.set_source_rgb(*fill); c.fill_preserve(); c.set_source_rgb(*L); c.set_line_width(lw); c.stroke()

def rrect(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()

def text(c, s, x, y, size, col=L, bold=True):
    c.select_font_face('Outfit', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size); e = c.text_extents(s); c.move_to(x - e.width / 2 - e.x_bearing, y); c.set_source_rgb(*col); c.show_text(s)

def sky(c, night, x=0, y=0, w=W, h=H):
    top, bot = (hx('#7EC8FF'), hx('#DDF1FF')) if not night else (hx('#141A3A'), hx('#3B3168'))
    g = cairo.LinearGradient(0, y, 0, y + h); g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bot)
    c.rectangle(x, y, w, h); c.set_source(g); c.fill()
    r = random.Random(3)
    if night:
        for _ in range(120):
            c.set_source_rgba(1, 1, 1, r.uniform(.4, 1)); c.arc(x + r.uniform(0, w), y + r.uniform(0, h * .6), r.uniform(1, 2.4), 0, 6.3); c.fill()
        c.set_source_rgb(1, .97, .85); c.arc(x + w * .85, y + 130, 44, 0, 6.3); c.fill()
    else:
        c.set_source_rgb(1, .93, .6); c.arc(x + w * .86, y + 140, 56, 0, 6.3); c.fill()
        for cx, cy, s in ((300, 170, 1), (1100, 120, .8), (1600, 260, .7)):
            for dx, dy, rr in ((0, 0, 34), (40, -14, 42), (82, 0, 30)):
                c.arc(x + cx + dx * s, y + cy + dy * s, rr * s, 0, 6.3)
            shape(c, (1, 1, 1), 2)

def window(c, x, y, w, h, night, lit):
    rrect(c, x, y, w, h, 6)
    shape(c, hx('#FFE9A8') if (night and lit) else (hx('#2A2F5A') if night else hx('#BFE6FF')), 3)
    c.set_line_width(2.5); c.move_to(x + w / 2, y); c.line_to(x + w / 2, y + h); c.move_to(x, y + h / 2); c.line_to(x + w, y + h / 2); c.stroke()

# ---------- rooms: (x, y) = top-left of the room interior, floor at y + h ----------
WALLS = {'mart': '#FFF3D6', 'records': '#FFE1E8', 'laundry': '#E4F6EE', 'bedroom': '#E8E2FF', 'desk': '#FFF0E0',
         'sofa': '#E0F0FF', 'kitchen': '#FFF6EC', 'plants': '#EAF7DA', 'lobby': '#F1ECE6'}
def room(c, kind, x, y, w, h, night, lit=True):
    wall = hx(WALLS.get(kind, '#F4F0EA'))
    if night: wall = lerp(wall, hx('#2B2A50'), .55) if not lit else lerp(wall, hx('#FFD98A'), .18)
    c.rectangle(x, y, w, h); c.set_source_rgb(*wall); c.fill()
    fy = y + h
    c.set_line_width(3); c.set_source_rgb(*L)
    if kind not in ('mart', 'records', 'lobby'): window(c, x + w * .5 - 55, y + 34, 110, 86, night, False)
    if kind == 'mart':
        for i in range(3):
            sx = x + 30 + i * (w - 60) / 3
            c.rectangle(sx, y + 40, (w - 60) / 3 - 20, h - 40); shape(c, hx('#FFFFFF'))
            for j in range(4):
                yy = y + 60 + j * (h - 60) / 4
                c.move_to(sx, yy + 30); c.line_to(sx + (w - 60) / 3 - 20, yy + 30); c.stroke()
                for k in range(4):
                    c.rectangle(sx + 8 + k * 22, yy + 6, 16, 22); shape(c, hx(['#FF8FB1', '#7ED6C4', '#FFC857', '#8FB8FF'][(i + j + k) % 4]), 2)
    elif kind == 'records':
        for i in range(5):
            c.arc(x + 70 + i * (w - 120) / 4, y + 70, 30, 0, 6.3); shape(c, hx('#2B2541'))
            c.arc(x + 70 + i * (w - 120) / 4, y + 70, 10, 0, 6.3); shape(c, hx(['#FF5C8A', '#FFC857', '#7ED6C4', '#8FB8FF', '#C9A7FF'][i]), 2)
        c.rectangle(x + 40, fy - 60, w - 80, 60); shape(c, hx('#D9A066'))
        for i in range(12):
            c.rectangle(x + 50 + i * (w - 100) / 12, fy - 80, 14, 40); shape(c, hx(['#FF8FB1', '#7ED6C4', '#FFC857', '#8FB8FF'][i % 4]), 2)
    elif kind == 'laundry':
        c.move_to(x + 20, y + 40); c.curve_to(x + w * .3, y + 70, x + w * .7, y + 70, x + w - 20, y + 40); c.stroke()
        for i, col in enumerate(('#FFFFFF', '#8FB8FF', '#FFC857', '#FFFFFF', '#FF8FB1')):
            sx = x + 50 + i * (w - 100) / 5; sy = y + 56 + 10 * math.sin(i / 4 * math.pi)
            c.move_to(sx, sy); c.line_to(sx + 44, sy); c.line_to(sx + 40, sy + 60); c.line_to(sx + 4, sy + 60); c.close_path(); shape(c, hx(col), 2.5)
        c.rectangle(x, fy - 40, w, 40); shape(c, hx('#CFE8DA'))   # balcony rail
        for i in range(10): c.move_to(x + i * w / 10, fy - 40); c.line_to(x + i * w / 10, fy); c.stroke()
    elif kind == 'bedroom':
        r = random.Random(7)
        for _ in range(16):   # glow-in-the-dark stars on the ceiling
            sx, sy = x + r.uniform(20, w - 20), y + r.uniform(12, 40)
            c.save(); c.translate(sx, sy); c.move_to(0, -8)
            for k in range(1, 10): rr = 8 if k % 2 == 0 else 3.5; a = k * math.pi / 5 - math.pi / 2; c.line_to(rr * math.cos(a), rr * math.sin(a))
            c.close_path(); c.set_source_rgb(*(hx('#C8FF7A') if night else hx('#F2EFC0'))); c.fill(); c.restore()
        c.rectangle(x + 30, fy - 56, w * .5, 56); shape(c, hx('#FFFFFF'))
        c.rectangle(x + 30, fy - 56, 60, 30); shape(c, hx('#C9A7FF'))
        c.rectangle(x + 30, fy - 90, 16, 90); shape(c, hx('#D9A066'))
    elif kind == 'desk':
        c.rectangle(x + w - 230, fy - 80, 190, 14); shape(c, hx('#D9A066'))
        c.move_to(x + w - 220, fy - 66); c.line_to(x + w - 220, fy); c.move_to(x + w - 50, fy - 66); c.line_to(x + w - 50, fy); c.stroke()
        for i in range(4): c.rectangle(x + w - 215 + i * 18, fy - 120, 14, 40); shape(c, hx(['#FF8FB1', '#7ED6C4', '#FFC857', '#8FB8FF'][i]), 2)
        c.move_to(x + w - 80, fy - 80); c.line_to(x + w - 90, fy - 130); c.stroke(); c.arc(x + w - 80, fy - 134, 16, math.pi, 2 * math.pi); shape(c, hx('#FFC857'))
    elif kind == 'sofa':
        c.rectangle(x + 40, fy - 70, w * .55, 50); shape(c, hx('#FF9F8A'))
        c.rectangle(x + 40, fy - 100, w * .55, 34); shape(c, hx('#FF9F8A'))
        c.rectangle(x + w - 150, fy - 120, 110, 70); shape(c, hx('#2B2541') if not night else hx('#8FB8FF'))
        c.rectangle(x + w - 120, fy - 50, 50, 50); shape(c, hx('#D9A066'))
    elif kind == 'kitchen':
        c.rectangle(x + 40, fy - 70, w * .45, 10); shape(c, hx('#D9A066'))
        for k in (0, 1):
            c.rectangle(x + 30 + k * w * .45, fy - 60, 20, 60); shape(c, hx('#FFC857'))
        c.rectangle(x + w - 160, fy - 90, 130, 90); shape(c, hx('#FFFFFF'))
        c.arc(x + w * .25, fy - 76, 14, math.pi, 2 * math.pi); shape(c, hx('#FF8FB1'))
    elif kind == 'plants':
        for i in range(4):
            px = x + 50 + i * (w - 100) / 3
            c.rectangle(px - 18, fy - 40, 36, 40); shape(c, hx('#E07A5F'))
            for a in (-0.7, 0, 0.7):
                c.save(); c.translate(px, fy - 40); c.rotate(a); c.scale(1, 2.2); c.arc(0, -14, 12, 0, 6.3); c.restore(); shape(c, hx('#7ED6A0'), 2)
    elif kind == 'lobby':
        rrect(c, x + w * .5 - 45, fy - 150, 90, 150, 10); shape(c, hx('#8FB8FF'))
        c.arc(x + w * .5 + 28, fy - 75, 5, 0, 6.3); c.set_source_rgb(*L); c.fill()
        for i in range(6): c.rectangle(x + 30 + i * 30, y + 30, 24, 30); shape(c, hx('#FFFFFF'), 2)
    if night and not lit:
        c.rectangle(x, y, w, h); c.set_source_rgba(.05, .05, .2, .35); c.fill()

def rooftop(c, x, y, w, night):
    c.set_line_width(3); c.set_source_rgb(*L)
    c.move_to(x + 20, y - 60); c.curve_to(x + w * .3, y - 30, x + w * .7, y - 30, x + w - 20, y - 60); c.stroke()
    for i in range(9):   # string lights
        u = (i + .5) / 9; bx = x + 20 + u * (w - 40); by = y - 60 + 30 * 4 * u * (1 - u) * .75 + 6
        c.arc(bx, by, 7, 0, 6.3); shape(c, hx('#FFE27A') if night else hx('#FFF6D8'), 2)
    c.move_to(x + 20, y - 60); c.line_to(x + 20, y); c.move_to(x + w - 20, y - 60); c.line_to(x + w - 20, y); c.stroke()
    c.rectangle(x + w - 160, y - 110, 90, 110); shape(c, hx('#CFD8E8'))  # water tank
    for k in range(2): c.rectangle(x + 120 + k * 70, y - 40, 40, 40); shape(c, hx('#FFC857'))

def building(c, x, gy, w, floors, kinds, night, lit=None, roof=True, facade='#F6E7D8'):
    """floors: list of floor heights from bottom; kinds: per floor list of room kinds (left->right)."""
    WALL = 18; y = gy
    tops = []
    total = sum(floors) + WALL * (len(floors) + 1)
    c.rectangle(x, gy - total, w, total); shape(c, hx(facade), 4)
    for fi, fh in enumerate(floors):
        y -= WALL; ks = kinds[fi]; rw = (w - WALL * (len(ks) + 1)) / len(ks)
        for ri, k in enumerate(ks):
            rx = x + WALL + ri * (rw + WALL)
            on = True if lit is None else lit.get((fi, ri), True)
            room(c, k, rx, y - fh, rw, fh, night, on)
            c.rectangle(rx, y - fh, rw, fh); c.set_source_rgb(*L); c.set_line_width(3); c.stroke()
            tops.append((fi, ri, rx, y, rw, fh))
        y -= fh
    y -= WALL
    if roof:
        c.rectangle(x - 10, y - 4, w + 20, 14); shape(c, hx('#B9A4C9'))
    return tops, y

def ground(c, gy, night):
    c.rectangle(0, gy, W, H - gy); shape(c, hx('#B9DDB0') if not night else hx('#3D4A5E'))
    c.rectangle(0, gy + 40, W, 90); shape(c, hx('#D8D6DE') if not night else hx('#5A5A72'))

def haru(c, x, fy, s=.62, outfit='signature', walk=0.0, phase=1.0, t=1.0):
    c.save(); c.translate(x, fy); c.scale(s, s); ch.draw(c, 0, 0, t, L=L, outfit=outfit, walk=walk, phase=phase); c.restore()

def label(c, s, x, y):
    c.select_font_face('NanumSquareRound', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(30)
    e = c.text_extents(s); rrect(c, x - 14, y - 34, e.width + 28, 48, 14); shape(c, (1, 1, 1), 3)
    c.set_source_rgb(*L); c.move_to(x, y); c.show_text(s)

def frame(fn):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    fn(c); return s

FL = [190, 170, 170, 170]
K1 = [['mart', 'records'], ['laundry', 'kitchen'], ['sofa', 'desk'], ['bedroom', 'plants']]
K2 = [['lobby', 'kitchen'], ['desk', 'sofa'], ['bedroom', 'laundry'], ['plants', 'kitchen']]

def A(c, night=False):     # row of cut-open buildings sliding past (camera close)
    sky(c, night); c.save(); c.translate(-560, -560); c.scale(1.7, 1.7); gy = 900; ground(c, gy, night)
    building(c, -220, gy, 560, FL, K2, night, facade='#E9DDF0')
    tops, ry = building(c, 420, gy, 720, FL, K1, night)
    rooftop(c, 420, ry - 4, 720, night)
    building(c, 1220, gy, 640, FL[:3], [['records', 'mart'], ['sofa', 'bedroom'], ['desk', 'laundry']], night, facade='#DDEBF5')
    fi, ri, rx, fy, rw, fh = [tp for tp in tops if tp[0] == 1 and tp[1] == 1][0]
    haru(c, rx + rw * .3, fy, outfit='signature')
    c.restore()
    c.set_source_rgba(1, 1, 1, .9); c.set_line_width(6)
    for dx in (0, 40, 80): c.move_to(W - 190 + dx, 1000); c.line_to(W - 170 + dx, 1020); c.line_to(W - 190 + dx, 1040); c.stroke()

def B(c, night=False):     # Haru walks the stairs and corridors, camera follows
    sky(c, night); c.save(); c.translate(-1500, -640); c.scale(1.9, 1.9); gy = 940; ground(c, gy, night)
    x0, w = 160, 1600
    tops, ry = building(c, x0, gy, w, FL, [['mart', 'records', 'lobby'], ['laundry', 'kitchen', 'desk'], ['sofa', 'bedroom', 'plants'], ['desk', 'laundry', 'kitchen']], night)
    # stairwell column on the right of the middle room of floor 2
    fi, ri, rx, fy, rw, fh = [tp for tp in tops if tp[0] == 1 and tp[1] == 1][0]
    c.set_source_rgb(*hx('#E9E2D6')); sx0 = rx + rw * .15; sx1 = rx + rw * .85
    c.move_to(sx0, fy);
    n = 9
    for k in range(n): c.line_to(sx0 + (sx1 - sx0) * k / n, fy - fh * (k + 1) / n); c.line_to(sx0 + (sx1 - sx0) * (k + 1) / n, fy - fh * (k + 1) / n)
    c.line_to(sx1, fy); c.close_path(); shape(c, hx('#E9E2D6'))
    k = 4; px = sx0 + (sx1 - sx0) * (k + .5) / n; py = fy - fh * (k + 1) / n
    haru(c, px, py, s=.62, walk=1.0, phase=.6)
    rooftop(c, x0, ry - 4, w, night); c.restore()

def C(c, night=False, lit=None):      # dollhouse: one building, fixed camera
    sky(c, night); gy = 960; ground(c, gy, night)
    w = 900; x0 = (W - w) / 2
    tops, ry = building(c, x0, gy, w, [180, 160, 160, 160], K1, night, lit=lit)
    rooftop(c, x0, ry - 4, w, night)
    fi, ri, rx, fy, rw, fh = [tp for tp in tops if tp[0] == 3 and tp[1] == 0][0]
    haru(c, rx + rw * .72, fy, s=.62)
    for tx in (x0 - 220, x0 + w + 120):   # street trees
        c.rectangle(tx + 40, gy - 90, 16, 90); shape(c, hx('#B07A4F'))
        c.arc(tx + 48, gy - 120, 60, 0, 6.3); shape(c, hx('#9BD3A0') if not night else hx('#3E6B5A'))

def DN(c):
    lit = {(0, 0): True, (0, 1): True, (1, 0): False, (1, 1): True, (2, 0): True, (2, 1): False, (3, 0): True, (3, 1): False}
    s1 = frame(lambda cc: C(cc, False)); s2 = frame(lambda cc: C(cc, True, lit))
    for k, sf in enumerate((s1, s2)):
        c.save(); c.rectangle(k * W / 2, 0, W / 2, H); c.clip(); c.translate(k * W / 2 - W * .12, H * .38); c.scale(.62, .62)
        c.set_source_surface(sf, 0, 0); c.paint(); c.restore()
        c.save(); c.rectangle(k * W / 2, 0, W / 2, H * .38 + 2); c.clip(); sky(c, k == 1); c.restore()
    c.set_source_rgb(1, 1, 1); c.set_line_width(6); c.move_to(W / 2, 0); c.line_to(W / 2, H); c.stroke()
    label(c, '낮', 60, 80); label(c, '밤', W / 2 + 40, 80)

panels = [('A. 옆으로 흐르는 건물들 (곡마다 다른 방)', frame(A)), ('B. 하루(Haru)가 계단과 복도를 이동', frame(B)),
          ('C. 인형의 집 (건물 한 채 고정)', frame(C)), ('낮과 밤 비교 (C 기준, 밤엔 방마다 불)', frame(DN))]
for i, (_, s) in enumerate(panels): s.write_to_png(OUT.replace('.png', f'_{"ABCD"[i]}.png'))
sw, sh = 940, 529; pad = 40
sheet = cairo.ImageSurface(cairo.FORMAT_RGB24, pad * 3 + sw * 2, pad * 3 + (sh + 60) * 2 + 60); c = cairo.Context(sheet)
c.set_source_rgb(*hx('#FAF8F2')); c.paint()
c.select_font_face('NanumSquareRound', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(40); c.set_source_rgb(*L)
c.move_to(pad, 70); c.show_text('PLAY LIST 03 시안 · 아파트 단면도')
for i, (lab, s) in enumerate(panels):
    x = pad + (i % 2) * (sw + pad); y = 110 + (i // 2) * (sh + 60 + pad)
    c.set_font_size(28); c.set_source_rgb(*L); c.move_to(x, y + 30); c.show_text(lab)
    c.save(); c.translate(x, y + 50); c.scale(sw / W, sh / H); c.set_source_surface(s, 0, 0); c.paint(); c.restore()
sheet.write_to_png(OUT)
