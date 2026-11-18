"""Christmas world (PLAY LIST 04): six neighbourhoods, one per ride segment, all under falling snow.
canal (skate, morning) -> downtown (tram, day) -> park hill (sled, afternoon) -> market square (carriage, dusk)
-> residential lane (walk, night) -> night sky (reindeer sleigh, night). Stateless drawing from scroll + time."""
import math, random
import cairo
from mobility import mob
W, H, GY = 1920, 1080, 860
hx, lerp, shape = mob.hexc, mob.lerp, mob._shape
L = hx('#2B2541')
RED, GREEN, GOLD, CREAM, SNOW = '#D94040', '#2E8B57', '#F2C230', '#FFF6E0', '#FFFFFF'
SKY = {  # top, bottom, how much the scene darkens, are lights on
    'morning': ('#9FC8F0', '#FFE3E8', 0.00, False),
    'day':     ('#6FB8F2', '#E3F3FF', 0.00, False),
    'golden':  ('#8DB2E8', '#FFE2B0', 0.06, False),
    'dusk':    ('#5B4FA8', '#FF9F8A', 0.30, True),
    'night':   ('#0F1530', '#2E2A5C', 0.58, True),
    'aurora':  ('#081028', '#1C2450', 0.62, True)}

def tone(col, m):
    return lerp(hx(col) if isinstance(col, str) else col, hx('#25244A'), SKY[m][2])
def rrect(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()
def wrapx(base, scroll, f, period):
    return (base - scroll * f) % period - 300
def tx(c, s, x, y, size, col=L):
    c.select_font_face('Outfit', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size); c.set_source_rgb(*col); c.move_to(x, y); c.show_text(s)

def glow(c, x, y, r, col=(1, .86, .5), a=.55):
    g = cairo.RadialGradient(x, y, 0, x, y, r); g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    c.set_source(g); c.arc(x, y, r, 0, 6.3); c.fill()

def bulbs(c, x0, y0, x1, y1, sag, m, t, n=14, cols=(RED, GOLD, GREEN, '#5BA8FF')):
    """a sagging string of coloured lights"""
    c.set_line_width(2.5); c.set_source_rgb(*L); c.move_to(x0, y0); c.curve_to(x0 + (x1 - x0) / 3, y0 + sag, x0 + 2 * (x1 - x0) / 3, y1 + sag, x1, y1); c.stroke()
    lit = SKY[m][3]
    for k in range(1, n):
        u = k / n; x = (1 - u) ** 3 * x0 + 3 * (1 - u) ** 2 * u * (x0 + (x1 - x0) / 3) + 3 * (1 - u) * u * u * (x0 + 2 * (x1 - x0) / 3) + u ** 3 * x1
        y = (1 - u) ** 3 * y0 + 3 * (1 - u) ** 2 * u * (y0 + sag) + 3 * (1 - u) * u * u * (y1 + sag) + u ** 3 * y1
        col = hx(cols[k % len(cols)])
        if lit: glow(c, x, y + 6, 18, col, .5 + .2 * math.sin(t * 3 + k))
        c.arc(x, y + 6, 5, 0, 6.3); shape(c, col if lit else lerp(col, (1, 1, 1), .25), L)

def sky(c, m, t):
    s0, s1, _, lit = SKY[m]
    g = cairo.LinearGradient(0, 0, 0, 700); g.add_color_stop_rgb(0, *hx(s0)); g.add_color_stop_rgb(1, *hx(s1)); c.rectangle(0, 0, W, H); c.set_source(g); c.fill()
    r = random.Random(7)
    if m in ('night', 'aurora', 'dusk'):
        for _ in range(160 if m != 'dusk' else 40):
            c.arc(r.uniform(0, W), r.uniform(0, 420), r.uniform(.8, 2.2), 0, 6.3); c.set_source_rgba(1, 1, 1, r.uniform(.3, .9) * (.5 + .5 * math.sin(t * 2 + r.random() * 6))); c.fill()
    if m == 'aurora':
        for k, col in enumerate(((.35, 1, .7), (.4, .8, 1), (.75, .5, 1))):
            c.save(); c.move_to(0, 220 + k * 40)
            for xx in range(0, W + 160, 160): c.line_to(xx, 180 + k * 40 + 60 * math.sin(xx / 260 + t * .4 + k))
            c.line_to(W, 40); c.line_to(0, 40); c.close_path()
            g = cairo.LinearGradient(0, 40, 0, 300 + k * 40); g.add_color_stop_rgba(0, *col, 0); g.add_color_stop_rgba(1, *col, .28); c.set_source(g); c.fill(); c.restore()
    if m in ('night', 'aurora'):
        c.arc(1560, 150, 48, 0, 6.3); c.set_source_rgb(1, .97, .85); c.fill(); c.arc(1542, 138, 42, 0, 6.3); c.set_source_rgb(*hx(s0)); c.fill()
    elif m == 'dusk':
        glow(c, 1300, 640, 260, (1, .7, .45), .5)
    else:
        sx, sy = (1580, 150) if m != 'golden' else (1450, 300)
        glow(c, sx, sy, 140, (1, .95, .7), .5); c.arc(sx, sy, 56, 0, 6.3); c.set_source_rgb(1, .93, .62); c.fill()
    for k, (cy, sc) in enumerate(((140, 1.0), (90, .7), (220, .85))):
        if m in ('night', 'aurora'): break
        cx = 300 + k * 620 + 40 * math.sin(t * .1 + k)
        blobs = ((0, 0, 34), (40, -16, 44), (86, 0, 32), (44, 10, 30))
        for dx, dy, rr in blobs: c.new_sub_path(); c.arc(cx + dx * sc, cy + dy * sc, rr * sc + 2.5, 0, 6.3)
        c.set_source_rgb(*L); c.fill()
        for dx, dy, rr in blobs: c.new_sub_path(); c.arc(cx + dx * sc, cy + dy * sc, rr * sc, 0, 6.3)
        c.set_source_rgb(*(hx('#FFE0D0') if m == 'dusk' else (1, 1, 1))); c.fill()

def snowfall(c, t, scroll, n=220, seed=3):
    r = random.Random(seed)
    for _ in range(n):
        x0, y0, sp, sz, ph = r.uniform(0, W + 200), r.uniform(0, H), r.uniform(40, 110), r.uniform(2, 6), r.uniform(0, 6.3)
        y = (y0 + t * sp) % (H + 40) - 20; x = (x0 - scroll * .5 * (sz / 6) + 18 * math.sin(t * .8 + ph)) % (W + 200) - 100
        c.arc(x, y, sz, 0, 6.3); c.set_source_rgba(1, 1, 1, .55 + .08 * sz); c.fill()

def snowy_roof(c, pts, m):
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.close_path(); shape(c, tone(SNOW, m), L)

def house(c, x, base, w, h, col, m, t, wreath=True, tree=False):
    """gabled house with a snowy roof, lit windows at dusk/night"""
    lit = SKY[m][3]
    c.set_line_width(3.5); c.rectangle(x, base - h, w, h); shape(c, tone(col, m), L)
    c.move_to(x - 10, base - h); c.line_to(x + w / 2, base - h - w * .55); c.line_to(x + w + 10, base - h); c.close_path(); shape(c, tone('#8C4A3C', m), L)
    snowy_roof(c, [(x - 12, base - h + 2), (x + w / 2, base - h - w * .55 - 4), (x + w + 12, base - h + 2), (x + w + 6, base - h + 10), (x + w / 2, base - h - w * .55 + 8), (x - 6, base - h + 10)], m)
    for k in range(2):
        wx, wy = x + 14 + k * (w - 52), base - h + 24
        if lit: glow(c, wx + 12, wy + 14, 40, (1, .85, .45), .45)
        c.rectangle(wx, wy, 24, 28); shape(c, hx('#FFD772') if lit else tone('#CFE6FF', m), L)
        c.set_line_width(2); c.move_to(wx + 12, wy); c.line_to(wx + 12, wy + 28); c.move_to(wx, wy + 14); c.line_to(wx + 24, wy + 14); c.stroke(); c.set_line_width(3.5)
    if tree and lit:
        tx_, ty = x + w / 2, base - 40
        c.move_to(tx_ - 12, ty + 10); c.line_to(tx_, ty - 14); c.line_to(tx_ + 12, ty + 10); c.close_path(); shape(c, hx(GREEN), L)
    c.rectangle(x + w / 2 - 11, base - 42, 22, 42); shape(c, tone('#7A4A2E', m), L)
    if wreath:
        c.set_line_width(6); c.set_source_rgb(*tone(GREEN, m)); c.arc(x + w / 2, base - 56, 9, 0, 6.3); c.stroke()
        c.arc(x + w / 2, base - 47, 3.5, 0, 6.3); c.set_source_rgb(*hx(RED)); c.fill(); c.set_line_width(3.5)

def pine(c, x, base, s, m, t, lights=True):
    c.set_line_width(3)
    for k in range(3):
        w_, y_ = (46 - k * 10) * s, base - (30 + k * 32) * s
        c.move_to(x - w_, y_ + 26 * s); c.line_to(x, y_ - 30 * s); c.line_to(x + w_, y_ + 26 * s); c.close_path(); shape(c, tone('#2F7D55', m), L)
        c.move_to(x - w_ + 6, y_ + 22 * s); c.line_to(x, y_ - 24 * s); c.line_to(x - w_ * .2, y_ + 4 * s); c.close_path(); c.set_source_rgba(1, 1, 1, .85); c.fill()
    c.rectangle(x - 6 * s, base - 4 * s, 12 * s, 10 * s); shape(c, tone('#7A4A2E', m), L)
    if lights:
        for k in range(7):
            a = k * 2.4; lx, ly = x + math.cos(a) * 26 * s * (1 - k / 9), base - (24 + k * 12) * s
            col = hx((RED, GOLD, '#5BA8FF')[k % 3])
            if SKY[m][3]: glow(c, lx, ly, 12 * s, col, .5)
            c.arc(lx, ly, 3.5 * s, 0, 6.3); c.set_source_rgb(*col); c.fill()

def lamp(c, x, base, m, t, garland=True):
    c.set_line_width(7); c.set_source_rgb(*L); c.move_to(x, base); c.line_to(x, base - 190); c.stroke()
    c.set_line_width(3.5); c.set_source_rgb(*tone('#3B3F5C', m)); c.move_to(x, base); c.line_to(x, base - 190); c.stroke()
    if SKY[m][3]: glow(c, x, base - 200, 90, (1, .88, .55), .5)
    rrect(c, x - 14, base - 222, 28, 30, 6); shape(c, hx('#FFE08A') if SKY[m][3] else tone('#EEF4FF', m), L)
    snowy_roof(c, [(x - 18, base - 222), (x, base - 236), (x + 18, base - 222)], m)
    if garland:
        c.set_line_width(5); c.set_source_rgb(*tone(GREEN, m))
        for k in range(5): c.arc(x, base - 170 + k * 26, 7, 0, 6.3); c.stroke()
        c.move_to(x - 10, base - 182); c.line_to(x + 10, base - 182); c.line_to(x + 6, base - 168); c.line_to(x - 6, base - 168); c.close_path(); shape(c, hx(RED), L)

def kid(c, x, base, s, col, m, t, pose='stand'):
    c.save(); c.translate(x, base); c.scale(s, s); c.set_line_width(3)
    sw = math.sin(t * 6) * 5 if pose == 'walk' else 0
    c.set_line_width(5); c.set_source_rgb(*tone('#3E4A6B', m)); c.move_to(0, -20); c.line_to(-4 + sw, 0); c.move_to(0, -20); c.line_to(4 - sw, 0); c.stroke()
    c.set_line_width(3); rrect(c, -10, -48, 20, 30, 8); shape(c, tone(col, m), L)
    c.arc(0, -58, 10, 0, 6.3); shape(c, tone((1, .88, .78), m), L)
    c.arc(0, -61, 10.5, math.pi, 2 * math.pi); c.close_path(); shape(c, tone(RED if col != RED else GREEN, m), L)
    c.arc(0, -73, 4, 0, 6.3); c.set_source_rgb(1, 1, 1); c.fill()
    c.restore()

def snowman(c, x, base, s, m):
    c.set_line_width(3.5)
    for r_, dy in ((28, -28), (20, -72), (14, -104)): c.arc(x, base + dy * s, r_ * s, 0, 6.3); shape(c, tone(SNOW, m), L)
    c.move_to(x, base - 104 * s); c.line_to(x + 18 * s, base - 101 * s); c.line_to(x, base - 99 * s); c.close_path(); shape(c, hx('#FF8A3D'), L)
    c.rectangle(x - 13 * s, base - 134 * s, 26 * s, 18 * s); shape(c, tone('#2B2541', m), L)
    c.set_line_width(6 * s); c.set_source_rgb(*tone(RED, m)); c.move_to(x - 16 * s, base - 90 * s); c.line_to(x + 16 * s, base - 90 * s); c.stroke()

def ground(c, m, top=GY, col=SNOW, edge='#DCE8F5'):
    c.rectangle(0, top, W, H - top); c.set_source_rgb(*tone(col, m)); c.fill()
    c.set_line_width(4); c.set_source_rgb(*L); c.move_to(0, top); c.line_to(W, top); c.stroke()
    c.rectangle(0, top + 2, W, 10); c.set_source_rgb(*tone(edge, m)); c.fill()

# ---------- the six neighbourhoods ----------
def canal(c, m, scroll, t):
    """01-04 skate: frozen canal through a gabled town (morning)"""
    sky(c, m, t)
    r = random.Random(11); cols = ['#F6C6A8', '#F3E1B8', '#BFD9C8', '#F2B8C6', '#C9D6F2', '#F5D58E']
    for k in range(14):
        x = wrapx(k * 170, scroll, .45, 14 * 170) ; w = 120 + (k % 3) * 18; h = 150 + (k * 37) % 90
        house(c, x, 700, w, h, cols[k % len(cols)], m, t, wreath=True)
    # quay wall + railing + lamps with garland
    c.rectangle(0, 700, W, 60); shape(c, tone('#B9A48C', m), L)
    for k in range(40): bx = wrapx(k * 60, scroll, .6, 40 * 60); c.rectangle(bx, 704, 56, 24); c.set_source_rgb(*tone('#CDB9A0', m)); c.fill()
    snowy_roof(c, [(0, 700), (W, 700), (W, 708), (0, 708)], m)
    for k in range(6): lamp(c, wrapx(k * 380 + 120, scroll, .6, 6 * 380), 700, m, t)
    # arched bridge
    bx = wrapx(900, scroll, .75, 2600)
    c.set_line_width(4); c.move_to(bx - 230, 760); c.curve_to(bx - 160, 610, bx + 160, 610, bx + 230, 760); c.line_to(bx + 190, 760)
    c.curve_to(bx + 130, 660, bx - 130, 660, bx - 190, 760); c.close_path(); shape(c, tone('#C98F6A', m), L)
    snowy_roof(c, [(bx - 236, 760), (bx - 160, 606), (bx + 160, 606), (bx + 236, 760), (bx + 228, 752), (bx + 156, 618), (bx - 156, 618), (bx - 228, 752)], m)
    bulbs(c, bx - 200, 690, bx + 200, 690, -60, m, t, 12)
    # ice
    g = cairo.LinearGradient(0, 760, 0, H); g.add_color_stop_rgb(0, *tone('#BFE3F5', m)); g.add_color_stop_rgb(1, *tone('#E8F6FF', m)); c.rectangle(0, 760, W, H - 760); c.set_source(g); c.fill()
    c.set_line_width(2.5)
    for k in range(30):
        sx = wrapx(k * 113, scroll, 1.0, 30 * 113); sy = 790 + (k * 53) % 230
        c.move_to(sx, sy); c.line_to(sx + 60, sy - 6); c.set_source_rgba(1, 1, 1, .7); c.stroke()
        if (k + int(t * 2)) % 7 == 0: c.arc(sx + 30, sy - 3, 3, 0, 6.3); c.set_source_rgba(1, 1, 1, .95); c.fill()
    for k, col in enumerate(('#5BA8FF', RED, GOLD)):
        kid(c, wrapx(k * 640 + 300, scroll, .9, 1900), 900 + k * 30, 1.2, col, m, t, 'walk')
    snowfall(c, t, scroll, 120, 4)

def downtown(c, m, scroll, t):
    """05-07 tram: shop windows, clock tower, garlands over the street, choir, bungeoppang stall (day)"""
    sky(c, m, t)
    ctx = wrapx(1200, scroll, .2, 3400)
    c.set_line_width(4); c.rectangle(ctx - 50, 260, 100, 440); shape(c, tone('#E8D5B5', m), L)
    c.move_to(ctx - 62, 260); c.line_to(ctx, 180); c.line_to(ctx + 62, 260); c.close_path(); shape(c, tone('#2F7D55', m), L)
    c.arc(ctx, 320, 34, 0, 6.3); shape(c, tone(CREAM, m), L)
    c.set_source_rgb(*L); c.move_to(ctx, 320); c.line_to(ctx, 296); c.move_to(ctx, 320); c.line_to(ctx + 16, 326); c.stroke()
    shops = [('#C62E2E', 'TOYS'), ('#2E7D4F', 'BAKERY'), ('#7B1E3A', 'GIFTS'), ('#2C3E66', 'BOOKS'), ('#B5651D', 'CAFE')]
    for k in range(10):
        x = wrapx(k * 300, scroll, .55, 3000); col, name = shops[k % 5]
        c.rectangle(x, 380, 270, 340); shape(c, tone('#F1E4CC', m), L)
        for j in range(3): c.rectangle(x + 24 + j * 80, 410, 60, 70); shape(c, tone('#CFE6FF', m), L)
        rrect(c, x + 20, 506, 230, 40, 8); shape(c, tone(col, m), L); tx(c, name, x + 40, 536, 26, (1, 1, 1))
        for j in range(8): c.move_to(x + 20 + j * 29, 546); c.line_to(x + 34 + j * 29, 566); c.line_to(x + 49 + j * 29, 546); c.close_path(); shape(c, tone(col if j % 2 else CREAM, m), L)
        c.rectangle(x + 30, 580, 210, 120); shape(c, tone('#FFF1C9', m), L)
        pine(c, x + 80, 690, .9, 'night', t);
        c.rectangle(x + 150, 640, 30, 50); shape(c, hx(RED), L); c.rectangle(x + 190, 655, 30, 35); shape(c, hx(GOLD), L)
        c.set_line_width(7); c.set_source_rgb(*tone(GREEN, m)); c.arc(x + 135, 430, 26, 0, 6.3); c.stroke(); c.set_line_width(4)
        c.move_to(x + 125, 456); c.line_to(x + 145, 456); c.line_to(x + 135, 440); c.close_path(); shape(c, hx(RED), L)
    for k in range(5): bulbs(c, wrapx(k * 600, scroll, .7, 3000), 330, wrapx(k * 600, scroll, .7, 3000) + 600, 330, 70, m, t, 16)
    ground(c, m, 720, '#E9E4EC', '#D7D2DE')
    c.set_line_width(3); c.set_source_rgb(*tone('#9A93A8', m))
    for yy in (900, 930): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    c.set_line_width(3); c.set_source_rgb(*L); c.move_to(0, 300); c.line_to(W, 300); c.stroke()
    sx = wrapx(400, scroll, .9, 2300)
    rrect(c, sx - 70, 640, 140, 80, 10); shape(c, tone('#FF8A3D', m), L)
    c.select_font_face('NanumSquareRound', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(26); c.set_source_rgb(1, 1, 1); c.move_to(sx - 46, 690); c.show_text('붕어빵')
    for k in range(3):
        fx = sx - 40 + k * 30; c.move_to(fx - 12, 630); c.curve_to(fx - 6, 618, fx + 8, 618, fx + 12, 630); c.curve_to(fx + 6, 640, fx - 6, 640, fx - 12, 630); shape(c, hx('#E2A04A'), L)
    for k, col in enumerate((RED, GREEN, RED, GOLD)):
        kid(c, wrapx(1600 + k * 46, scroll, .9, 2300), 760, 1.25, col, m, t)
    snowfall(c, t, scroll, 120, 5)

def park(c, m, scroll, t):
    """08-10 sled: rolling snowy hills, snowmen, rink, ferris wheel (golden afternoon)"""
    sky(c, m, t)
    fx = wrapx(1500, scroll, .12, 3400); fy = 420
    c.set_line_width(4); c.set_source_rgb(*L)
    for a in range(12):
        aa = a * math.pi / 6 + t * .1; c.move_to(fx, fy); c.line_to(fx + 150 * math.cos(aa), fy + 150 * math.sin(aa)); c.stroke()
    c.arc(fx, fy, 150, 0, 6.3); c.stroke()
    for a in range(12):
        aa = a * math.pi / 6 + t * .1; c.arc(fx + 150 * math.cos(aa), fy + 150 * math.sin(aa) + 14, 13, 0, 6.3); shape(c, tone((RED, GOLD, GREEN, '#5BA8FF')[a % 4], m), L)
    c.move_to(fx - 60, 640); c.line_to(fx, fy); c.line_to(fx + 60, 640); c.stroke()
    for k, (yy, col, amp, per) in enumerate(((600, '#E3EDF8', 70, 900), (690, '#F4F8FC', 50, 700))):
        off = (scroll * (.25 + k * .2)) % per
        c.move_to(0, H)
        for xx in range(0, W + 41, 40): c.line_to(xx, yy - amp * (.5 + .5 * math.sin((xx + off) / per * 2 * math.pi)))
        c.line_to(W, H); c.close_path(); c.set_source_rgb(*tone(col, m)); c.fill_preserve(); c.set_source_rgb(*L); c.set_line_width(4)
        c.new_path()
        for i, xx in enumerate(range(0, W + 41, 40)):
            y_ = yy - amp * (.5 + .5 * math.sin((xx + off) / per * 2 * math.pi)); (c.move_to if i == 0 else c.line_to)(xx, y_)
        c.stroke()
    for k in range(9): pine(c, wrapx(k * 260 + 60, scroll, .5, 9 * 260), 680 + (k % 2) * 20, .9 + (k % 3) * .15, m, t)
    rx = wrapx(500, scroll, .6, 2600)
    c.save(); c.translate(rx, 760); c.scale(1, .35); c.arc(0, 0, 230, 0, 6.3); c.restore(); shape(c, tone('#CFEAF7', m), L)
    for k, col in enumerate((RED, '#5BA8FF', GOLD, GREEN)): kid(c, rx - 150 + k * 95, 770 + (k % 2) * 14, 1.0, col, m, t, 'walk')
    for k in range(4): snowman(c, wrapx(k * 520 + 300, scroll, .8, 4 * 520), GY + 10, 1.0 + (k % 2) * .2, m)
    ground(c, m, GY)
    for k, col in enumerate(('#5BA8FF', RED)):
        kx = wrapx(1300 + k * 70, scroll, .9, 2400); kid(c, kx, GY + 40, 1.3, col, m, t)
        c.arc(kx + 40, GY - 20 + 10 * math.sin(t * 3 + k), 8, 0, 6.3); shape(c, tone(SNOW, m), L)
    snowfall(c, t, scroll, 140, 6)

def market(c, m, scroll, t):
    """11-14 carriage: wooden stalls, giant tree, carousel, gingerbread shop (dusk, lights on)"""
    sky(c, m, t)
    tx0 = wrapx(1100, scroll, .25, 3200)
    for k in range(6):
        w_, y_ = 230 - k * 34, 700 - k * 80
        c.set_line_width(4); c.move_to(tx0 - w_, y_); c.line_to(tx0, y_ - 120); c.line_to(tx0 + w_, y_); c.close_path(); shape(c, tone('#2F7D55', m), L)
    for k in range(40):
        a = k * 2.39; lx = tx0 + math.cos(a) * 180 * (1 - (k / 40)); ly = 680 - k * 12
        col = hx((RED, GOLD, '#5BA8FF', '#FF9FC2')[k % 4]); glow(c, lx, ly, 16, col, .55); c.arc(lx, ly, 5, 0, 6.3); c.set_source_rgb(*col); c.fill()
    glow(c, tx0, 196, 90, (1, .9, .4), .6)
    c.move_to(tx0, 160)
    for k in range(10): rr = 34 if k % 2 == 0 else 14; a = -math.pi / 2 + k * math.pi / 5; c.line_to(tx0 + rr * math.cos(a), 196 + rr * math.sin(a))
    c.close_path(); shape(c, hx(GOLD), L)
    cx0 = wrapx(300, scroll, .45, 3000)
    c.move_to(cx0 - 130, 520); c.line_to(cx0, 440); c.line_to(cx0 + 130, 520); c.close_path(); shape(c, tone(RED, m), L)
    for k in range(6): c.move_to(cx0 - 130 + k * 43, 520); c.line_to(cx0 - 108 + k * 43, 540); c.line_to(cx0 - 86 + k * 43, 520); c.close_path(); shape(c, tone(CREAM if k % 2 else GOLD, m), L)
    c.rectangle(cx0 - 120, 690, 240, 18); shape(c, tone('#B5651D', m), L)
    for k in range(4):
        px = cx0 - 90 + k * 60; py = 620 + 14 * math.sin(t * 2 + k)
        c.set_line_width(3); c.set_source_rgb(*hx(GOLD)); c.move_to(px, 540); c.line_to(px, 690); c.stroke()
        rrect(c, px - 22, py, 44, 26, 10); shape(c, tone(('#FFFFFF', '#F2B8C6', '#C9D6F2', '#F5D58E')[k], m), L)
    bulbs(c, cx0 - 130, 520, cx0 + 130, 520, 0, m, t, 8)
    stall = [('#C62E2E', '뱅쇼'), ('#2E7D4F', '쿠키'), ('#B5651D', '진저브레드'), ('#7B1E3A', '오너먼트')]
    for k in range(8):
        sx = wrapx(k * 340 + 150, scroll, .65, 8 * 340); col, name = stall[k % 4]
        c.set_line_width(4); c.rectangle(sx, 620, 250, 160); shape(c, tone('#C98F6A', m), L)
        for j in range(5): c.rectangle(sx + j * 50, 620, 25, 160); c.set_source_rgba(1, 1, 1, .08); c.fill()
        c.move_to(sx - 20, 620); c.line_to(sx + 125, 540); c.line_to(sx + 270, 620); c.close_path(); shape(c, tone(col, m), L)
        snowy_roof(c, [(sx - 24, 620), (sx + 125, 536), (sx + 274, 620), (sx + 260, 626), (sx + 125, 550), (sx - 10, 626)], m)
        glow(c, sx + 125, 690, 120, (1, .8, .45), .35); c.rectangle(sx + 20, 650, 210, 70); shape(c, hx('#FFE6A8'), L)
        c.select_font_face('NanumSquareRound', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(28); c.set_source_rgb(*L); c.move_to(sx + 40, 696); c.show_text(name)
        bulbs(c, sx - 10, 626, sx + 260, 626, 26, m, t, 10)
        if k % 4 == 0:
            for j in range(3): c.move_to(sx + 90 + j * 26, 640); c.curve_to(sx + 96 + j * 26, 625, sx + 84 + j * 26, 612, sx + 92 + j * 26, 598); c.set_source_rgba(1, 1, 1, .6); c.set_line_width(4); c.stroke()
    ground(c, m, 780, '#F4F1F6', '#E4DDEA')
    for k, col in enumerate((RED, GREEN, GOLD, '#5BA8FF', RED)):
        kid(c, wrapx(k * 380 + 200, scroll, .9, 1900), 860 + (k % 2) * 30, 1.3, col, m, t, 'walk')
    snowfall(c, t, scroll, 160, 8)

def lane(c, m, scroll, t):
    """15-17 walk: quiet residential lane at night, lit windows with trees, chimney smoke, lamps"""
    sky(c, m, t)
    cols = ['#E7C9A9', '#C9D6F2', '#F2B8C6', '#BFD9C8', '#F3E1B8']
    for k in range(9):
        x = wrapx(k * 300 + 40, scroll, .5, 9 * 300); w = 220 + (k % 2) * 30; h = 200 + (k * 31) % 60
        house(c, x, 800, w, h, cols[k % 5], m, t, wreath=True, tree=True)
        chx = x + w * .75; c.rectangle(chx, 800 - h - w * .4, 26, 50); shape(c, tone('#8C4A3C', m), L)
        for j in range(4):
            yy = 800 - h - w * .4 - 20 - j * 26 - (t * 20) % 26; c.arc(chx + 13 + 8 * math.sin(t + j), yy, 10 + j * 3, 0, 6.3); c.set_source_rgba(.9, .9, 1, .25); c.fill()
        bulbs(c, x - 4, 800 - h, x + w + 4, 800 - h, 10, m, t, 9)
    for k in range(5): lamp(c, wrapx(k * 480 + 260, scroll, .8, 5 * 480), 820, m, t, garland=False)
    ground(c, m, 820)
    for k in range(16):
        fx = wrapx(k * 70, scroll, 1.0, 16 * 70); c.save(); c.translate(fx, 900 + (k % 2) * 16); c.scale(1, .5); c.arc(0, 0, 8, 0, 6.3); c.restore(); c.set_source_rgba(.7, .75, .9, .5); c.fill()
    snowfall(c, t, scroll, 240, 9)

def nightsky(c, m, scroll, t):
    """18-20 reindeer sleigh: aurora, moon, the whole town far below with its lights, the giant tree"""
    sky(c, 'aurora', t)
    r = random.Random(13)
    for k, (yy, col) in enumerate(((760, '#3B4677'), (850, '#56618F'))):
        c.move_to(0, H)
        for xx in range(0, W + 41, 40): c.line_to(xx, yy - 30 * math.sin((xx + scroll * (.15 + k * .1)) / 300))
        c.line_to(W, H); c.close_path(); c.set_source_rgb(*hx(col)); c.fill()
    for layer, (yy, f, sc) in enumerate(((820, .2, .55), (900, .35, .75))):
        for k in range(26):
            x = wrapx(k * 110 + layer * 50, scroll, f, 26 * 110); h = r.uniform(60, 140) * sc; w = r.uniform(60, 100) * sc
            c.set_line_width(2.5); c.rectangle(x, yy - h, w, h); shape(c, tone('#3A3E6E', 'night'), L)
            c.move_to(x - 4, yy - h); c.line_to(x + w / 2, yy - h - w * .45); c.line_to(x + w + 4, yy - h); c.close_path(); shape(c, hx('#E8EEFA'), L)
            for j in range(int(h // 30)):
                wx, wy = x + w * .3, yy - h + 14 + j * 26
                glow(c, wx + 5, wy + 5, 16, (1, .85, .45), .4); c.rectangle(wx, wy, 10 * sc + 4, 12 * sc + 4); c.set_source_rgb(1, .86, .5); c.fill()
    tx0 = wrapx(1400, scroll, .3, 3400)
    for k in range(4):
        w_, y_ = 90 - k * 18, 900 - k * 46
        c.move_to(tx0 - w_, y_); c.line_to(tx0, y_ - 70); c.line_to(tx0 + w_, y_); c.close_path(); shape(c, tone('#2F7D55', 'night'), L)
    for k in range(18):
        a = k * 2.39; lx, ly = tx0 + math.cos(a) * 70 * (1 - k / 18), 890 - k * 10
        col = hx((RED, GOLD, '#5BA8FF')[k % 3]); glow(c, lx, ly, 12, col, .6); c.arc(lx, ly, 4, 0, 6.3); c.set_source_rgb(*col); c.fill()
    glow(c, tx0, 690, 70, (1, .9, .4), .7)
    c.move_to(tx0, 664)
    for k in range(10): rr = 24 if k % 2 == 0 else 10; a = -math.pi / 2 + k * math.pi / 5; c.line_to(tx0 + rr * math.cos(a), 690 + rr * math.sin(a))
    c.close_path(); shape(c, hx(GOLD), L)
    c.rectangle(0, 960, W, 120); c.set_source_rgb(*hx('#6C77A3')); c.fill()
    snowfall(c, t, scroll, 160, 10)

SCENES = {'canal': (canal, 'morning'), 'downtown': (downtown, 'day'), 'park': (park, 'golden'),
          'market': (market, 'dusk'), 'lane': (lane, 'night'), 'sky': (nightsky, 'aurora')}
