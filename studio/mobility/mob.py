"""Test-only: Haru in five ways of getting around (run, bike, kick scooter, car, bus).
Face, glasses, bob hair and proportions are copied unchanged from studio/character.py; only pose and vehicle differ."""
import math, sys, cairo
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch
hexc, lerp, _shape = ch.hexc, ch.lerp, ch._shape
SKIN, HAIR = ch.SKIN, ch.HAIR


def ik(x0, y0, tx, ty, l1, l2, sign):
    dx, dy = tx - x0, ty - y0
    d = max(1e-3, min(l1 + l2 - 0.5, math.hypot(dx, dy)))
    a = math.atan2(dx, dy)
    off = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    a1 = a + sign * off
    kx, ky = x0 + l1 * math.sin(a1), y0 + l1 * math.cos(a1)
    a2 = math.atan2(tx - kx, ty - ky)
    return (kx, ky), (kx + l2 * math.sin(a2), ky + l2 * math.cos(a2))


def poly(ctx, pts):
    ctx.move_to(*pts[0]); [ctx.line_to(*p) for p in pts[1:]]; ctx.stroke()


def head(ctx, hx, hy, t, o, L):
    R = 42
    ctx.set_line_width(4); ctx.arc(hx, hy, R, 0, 2 * math.pi); _shape(ctx, SKIN, L)
    ctx.save(); ctx.arc(hx, hy, R + 1, 0, 2 * math.pi); ctx.clip()
    ctx.move_to(hx + R + 4, hy - 12); ctx.curve_to(hx + 20, hy - 22, hx - 6, hy - 16, hx - 12, hy - 4)
    ctx.line_to(hx - 14, hy + 30); ctx.line_to(hx - R - 6, hy + 30); ctx.line_to(hx - R - 6, hy - R - 6); ctx.line_to(hx + R + 6, hy - R - 6); ctx.close_path()
    ctx.set_source_rgb(*HAIR); ctx.fill(); ctx.restore()
    ctx.set_source_rgb(*L); ctx.set_line_width(4); ctx.arc(hx, hy, R, 0, 2 * math.pi); ctx.stroke()
    gx, gy2 = hx + 24, hy + 4
    ctx.set_line_width(4); ctx.move_to(gx - 14, gy2 - 2); ctx.line_to(hx - 16, gy2 - 4); ctx.stroke()
    ctx.arc(gx, gy2, 14, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, .45); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.stroke()
    if (t % 4.0) < 0.12: ctx.move_to(gx - 2, gy2 + 1); ctx.line_to(gx + 6, gy2 + 1); ctx.stroke()
    else: ctx.arc(gx + 2, gy2 + 1, 3.6, 0, 2 * math.pi); ctx.fill()
    ctx.set_source_rgba(1, .45, .55, .45); ctx.arc(gx + 4, gy2 + 22, 7, 0, 2 * math.pi); ctx.fill()
    ctx.set_source_rgb(*L); ctx.set_line_width(3); ctx.arc(hx + 30, hy + 26, 6, math.radians(10), math.radians(120)); ctx.stroke()
    ch._phones(ctx, o.get('phones_style', 'classic'), hx, hy, R, hexc(o['phones']), L)
    if o.get('helmet'): helmet(ctx, hx, hy, R, o, L)


def helmet(ctx, hx, hy, R, o, L):
    col = hexc(o['helmet']); acc = hexc(o.get('helmet_stripe', '#FFFFFF'))
    # chin strap first (behind the cheek line)
    ctx.set_line_width(2.5); ctx.set_source_rgb(*L); ctx.move_to(hx - 6, hy - 14); ctx.curve_to(hx - 2, hy + 10, hx + 6, hy + 30, hx + 14, hy + 40); ctx.stroke()
    # shell: covers only the top of the head, the bob stays visible below it
    ctx.set_line_width(4)
    ctx.move_to(hx - R - 6, hy - 10)
    ctx.curve_to(hx - R - 6, hy - R - 32, hx + R + 4, hy - R - 32, hx + R + 8, hy - 14)
    ctx.curve_to(hx + R - 4, hy - 20, hx - R + 6, hy - 22, hx - R - 6, hy - 10); ctx.close_path(); _shape(ctx, col, L)
    # stripe + vents
    ctx.save(); ctx.move_to(hx - R - 6, hy - 10); ctx.curve_to(hx - R - 6, hy - R - 32, hx + R + 4, hy - R - 32, hx + R + 8, hy - 14)
    ctx.curve_to(hx + R - 4, hy - 20, hx - R + 6, hy - 22, hx - R - 6, hy - 10); ctx.close_path(); ctx.clip()
    ctx.set_line_width(7); ctx.set_source_rgb(*acc); ctx.move_to(hx - R, hy - R + 2); ctx.curve_to(hx - 10, hy - R - 26, hx + 20, hy - R - 24, hx + R + 6, hy - 22); ctx.stroke()
    ctx.restore()
    ctx.set_line_width(3); ctx.set_source_rgb(*L)
    for dx in (-18, 0, 18):
        ctx.move_to(hx + dx - 4, hy - R - 10); ctx.line_to(hx + dx + 4, hy - R - 12); ctx.stroke()
    # small visor at the front
    ctx.move_to(hx + R - 2, hy - 18); ctx.curve_to(hx + R + 14, hy - 20, hx + R + 18, hy - 14, hx + R + 16, hy - 10); ctx.line_to(hx + R + 2, hy - 12); ctx.close_path(); _shape(ctx, col, L)


def torso(ctx, hip, o, L, top):
    bag = o.get('bag')
    if bag: ch._bag_back(ctx, bag, hip, hexc(o.get('bag_color', '#E9A23B')), L)
    ctx.set_line_width(4)
    ctx.move_to(hip[0] - 26, hip[1] + 8); ctx.curve_to(hip[0] - 30, hip[1] - 40, hip[0] - 24, hip[1] - 72, hip[0] + 2, hip[1] - 74)
    ctx.curve_to(hip[0] + 26, hip[1] - 72, hip[0] + 30, hip[1] - 40, hip[0] + 26, hip[1] + 8); ctx.close_path(); _shape(ctx, top, L)
    ctx.move_to(hip[0] + 4, hip[1] - 30); ctx.line_to(hip[0] + 22, hip[1] - 30); ctx.stroke()
    detail(ctx, hip, o, L)
    if bag: ch._bag_front(ctx, bag, hip, hexc(o.get('bag_color', '#E9A23B')), L, o.get('strap'))


O = {}
def paint_leg(ctx, hip, k, f, pants, L, back):
    dk = .35 if back else 0
    shorts = O.get('shorts')
    ctx.set_line_width(14); ctx.set_source_rgb(*lerp(pants, (.1, .1, .2), dk))
    if shorts:
        mx, my = hip[0] + (k[0] - hip[0]) * .75, hip[1] + (k[1] - hip[1]) * .75
        ctx.set_line_width(12); ctx.set_source_rgb(*lerp(SKIN, (.4, .3, .25), dk * .5)); poly(ctx, [(mx, my), k, f])
        ctx.set_line_width(17); ctx.set_source_rgb(*lerp(pants, (.1, .1, .2), dk)); poly(ctx, [hip, (mx, my)])
        ctx.set_line_width(11); ctx.set_source_rgb(1, 1, 1); poly(ctx, [(f[0] + (k[0] - f[0]) * .12, f[1] + (k[1] - f[1]) * .12), f])
    else:
        poly(ctx, [hip, k, f])
    shoe = hexc(O['shoe']) if O.get('shoe') else L
    ctx.set_line_width(14); ctx.set_source_rgb(*L); ctx.move_to(f[0] - 6, f[1]); ctx.line_to(f[0] + 15, f[1]); ctx.stroke()
    ctx.set_line_width(9); ctx.set_source_rgb(*lerp(shoe, (0, 0, 0), dk * .4)); ctx.move_to(f[0] - 5, f[1] - 1); ctx.line_to(f[0] + 13, f[1] - 1); ctx.stroke()

def detail(ctx, hip, o, L):
    x, y = hip; d = o.get('detail'); ctx.set_line_width(3)
    if d == 'bib':        # race number
        ctx.rectangle(x - 6, y - 56, 26, 22); _shape(ctx, (1, 1, 1), L)
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(13); ctx.set_source_rgb(*L); ctx.move_to(x - 2, y - 40); ctx.show_text('07'); ctx.new_path()
    elif d == 'reflect':  # reflective band on the windbreaker
        ctx.set_line_width(6); ctx.set_source_rgb(.85, .88, .92); ctx.move_to(x - 24, y - 46); ctx.line_to(x + 26, y - 46); ctx.stroke()
        ctx.set_line_width(3); ctx.set_source_rgb(*L); ctx.move_to(x + 2, y - 74); ctx.line_to(x + 2, y + 6); ctx.stroke()
    elif d == 'graphic':  # smiley print on the hoodie
        ctx.arc(x + 4, y - 44, 10, 0, 2 * math.pi); _shape(ctx, hexc('#FFD84A'), L)
        ctx.set_source_rgb(*L); ctx.arc(x + 1, y - 46, 1.6, 0, 2 * math.pi); ctx.fill(); ctx.arc(x + 7, y - 46, 1.6, 0, 2 * math.pi); ctx.fill()
        ctx.arc(x + 4, y - 43, 5, .3, 2.8); ctx.stroke()
    elif d == 'collar':   # denim jacket over a white tee
        ctx.move_to(x - 8, y - 73); ctx.line_to(x + 2, y - 52); ctx.line_to(x + 12, y - 73); ctx.close_path(); _shape(ctx, (1, 1, 1), L)
        ctx.move_to(x + 2, y - 52); ctx.line_to(x + 2, y + 6); ctx.stroke()
    elif d == 'buttons':  # knit cardigan
        ctx.move_to(x + 6, y - 72); ctx.line_to(x + 6, y + 6); ctx.stroke()
        for yy in (-58, -40, -22): ctx.arc(x + 12, y + yy, 2.6, 0, 2 * math.pi); _shape(ctx, (1, 1, 1), L)

def leg_to(ctx, hip, foot, pants, L, back):
    k, f = ik(hip[0], hip[1], foot[0], foot[1], 44, 42, +1)
    paint_leg(ctx, hip, k, f, pants, L, back)


def arm_to(ctx, sh, hand, top, L, back):
    ctx.set_line_width(12); ctx.set_source_rgb(*lerp(top, (.3, .2, .1), .3 if back else 0))
    e, h = ik(sh[0], sh[1], hand[0], hand[1], 32, 30, -1)
    poly(ctx, [sh, e, h])
    ctx.set_line_width(3); ctx.arc(h[0], h[1], 7, 0, 2 * math.pi); _shape(ctx, SKIN, L)


def wheel(ctx, x, y, r, ang, L, tyre=True):
    ctx.set_line_width(5 if tyre else 3.5); ctx.arc(x, y, r, 0, 2 * math.pi); _shape(ctx, (1, 1, 1), L)
    ctx.set_line_width(3)
    for k in range(3):
        a = ang + k * math.pi / 3
        ctx.move_to(x + r * .9 * math.cos(a), y + r * .9 * math.sin(a)); ctx.line_to(x - r * .9 * math.cos(a), y - r * .9 * math.sin(a))
    ctx.stroke(); ctx.arc(x, y, r * .18, 0, 2 * math.pi); _shape(ctx, (.85, .87, .92), L)


def cup(ctx, x, y, t, L, o):
    ch._prop(ctx, 'hot', x - 7, y - 8, t, L, o.get('sleeve', '#C68B59'))


# ---------------------------------------------------------------- the five ways
def run(ctx, t, o, L):
    ph = t * 2 * math.pi * 1.45
    pants, top = hexc(o['bottom']), hexc(o['top'])
    bob = 9 * abs(math.cos(ph))
    ctx.save(); ctx.rotate(math.radians(6))
    hip = (0, -86 - bob)
    def leg(p, back):
        a = math.radians(40) * math.sin(p); bend = math.radians(80) * max(0, math.cos(p)) + math.radians(12)
        x1, y1 = hip[0] + 44 * math.sin(a), hip[1] + 44 * math.cos(a)
        x2, y2 = x1 + 42 * math.sin(a - bend), y1 + 42 * math.cos(a - bend)
        paint_leg(ctx, hip, (x1, y1), (x2, y2), pants, L, back)
    sh = (2, hip[1] - 62)
    def arm(p, back):
        a = -math.radians(40) * math.sin(p)
        ctx.set_line_width(12); ctx.set_source_rgb(*lerp(top, (.3, .2, .1), .3 if back else 0))
        x1, y1 = sh[0] + 32 * math.sin(a), sh[1] + 32 * math.cos(a)
        x2, y2 = x1 + 28 * math.sin(a + math.radians(95)), y1 + 28 * math.cos(a + math.radians(95))
        poly(ctx, [sh, (x1, y1), (x2, y2)])
        return x2, y2
    leg(ph + math.pi, True); arm(ph, True)
    torso(ctx, hip, o, L, top)
    leg(ph, False)
    head(ctx, 6, hip[1] - 116, t, o, L)
    hx, hy = arm(ph + math.pi, False)
    # water bottle instead of the hot coffee
    ctx.set_line_width(3); ctx.rectangle(hx - 8, hy - 30, 16, 34); _shape(ctx, hexc('#7FD3F7'), L)
    ctx.rectangle(hx - 5, hy - 38, 10, 8); _shape(ctx, hexc(o['phones']), L)
    ctx.arc(hx, hy - 6, 8, 0, 2 * math.pi); _shape(ctx, SKIN, L)
    ctx.restore()


def bike(ctx, t, o, L):
    pants, top = hexc(o['bottom']), hexc(o['top'])
    frame = hexc('#FF7A6B')
    ph = t * 2 * math.pi * 1.0
    rw, fw, cr = (-78, -42), (86, -42), (0, -40)
    ang = t * 7.5
    wheel(ctx, *rw, 40, ang, L); wheel(ctx, *fw, 40, ang, L)
    sad, head_t, bar = (-22, -106), (56, -122), (46, -146)
    hip = (sad[0] + 2, sad[1] - 6)
    # back pedal + leg first
    pb = (cr[0] + 18 * math.cos(ph + math.pi), cr[1] + 18 * math.sin(ph + math.pi))
    leg_to(ctx, hip, pb, pants, L, True)
    ctx.set_line_width(7); ctx.set_source_rgb(*frame)
    poly(ctx, [rw, cr, sad]); poly(ctx, [rw, (sad[0] + 4, sad[1] + 8)]); poly(ctx, [(sad[0] + 4, sad[1] + 8), head_t]); poly(ctx, [cr, head_t]); poly(ctx, [fw, head_t, bar])
    ctx.set_line_width(5); ctx.set_source_rgb(*L); poly(ctx, [(bar[0] - 6, bar[1]), (bar[0] + 14, bar[1] - 4)])
    ctx.set_line_width(3); ctx.save(); ctx.translate(*sad); ctx.scale(1, .45); ctx.arc(0, 0, 18, 0, 2 * math.pi); ctx.restore(); _shape(ctx, hexc('#4A3F35'), L)
    ctx.arc(cr[0], cr[1], 11, 0, 2 * math.pi); _shape(ctx, (.85, .87, .92), L)
    # basket with the coffee
    cup(ctx, 82, -134, t, L, o)
    ctx.set_line_width(3); ctx.move_to(62, -140); ctx.line_to(104, -140); ctx.line_to(98, -112); ctx.line_to(68, -112); ctx.close_path(); _shape(ctx, hexc('#E3B778'), L)
    ctx.move_to(70, -128); ctx.line_to(98, -128); ctx.stroke()
    sh = (hip[0] + 6, hip[1] - 62)
    arm_to(ctx, sh, (bar[0] - 2, bar[1] + 2), top, L, True)
    ctx.save(); ctx.translate(hip[0], hip[1]); ctx.rotate(math.radians(10)); ctx.translate(-hip[0], -hip[1])
    torso(ctx, hip, o, L, top)
    ctx.restore()
    pf = (cr[0] + 18 * math.cos(ph), cr[1] + 18 * math.sin(ph))
    leg_to(ctx, hip, pf, pants, L, False)
    ctx.set_line_width(4); ctx.set_source_rgb(*L); poly(ctx, [(cr[0] - 18 * math.cos(ph), cr[1] - 18 * math.sin(ph)), (pf[0], pf[1])])
    head(ctx, hip[0] + 18, hip[1] - 112, t, o, L)
    arm_to(ctx, sh, (bar[0] + 4, bar[1]), top, L, False)


def kick(ctx, t, o, L):
    pants, top = hexc(o['bottom']), hexc(o['top'])
    per = 1.6; u = (t % per) / per
    deck_y = -16
    wheel(ctx, -52, -12, 12, t * 12, L); wheel(ctx, 54, -12, 12, t * 12, L)
    ctx.set_line_width(4); ctx.rectangle(-62, deck_y - 6, 116, 10); _shape(ctx, hexc('#2EC4A6'), L)
    ctx.set_line_width(7); ctx.set_source_rgb(*hexc('#2EC4A6')); poly(ctx, [(54, -12), (44, -168)])
    ctx.set_line_width(6); ctx.set_source_rgb(*L); poly(ctx, [(30, -170), (58, -168)])
    hip = (-4, deck_y - 6 - 86 + 2 * math.sin(u * 2 * math.pi))
    # push leg: pushes the ground for the first 45 %, then comes back to the deck
    if u < .45:
        k = u / .45; foot = (12 - 86 * k, 0)
    else:
        k = (u - .45) / .55; foot = (-74 + 70 * k, -6 - 22 * math.sin(k * math.pi))
    leg_to(ctx, hip, foot, pants, L, True)
    sh = (hip[0] + 4, hip[1] - 62)
    arm_to(ctx, sh, (36, -170), top, L, True)
    torso(ctx, hip, o, L, top)
    leg_to(ctx, hip, (6, deck_y - 6), pants, L, False)
    head(ctx, hip[0] + 8, hip[1] - 116, t, o, L)
    arm_to(ctx, sh, (44, -168), top, L, False)


def _car_body(ctx, L, col):
    ctx.new_path()
    ctx.move_to(-170, -34); ctx.line_to(-176, -110); ctx.curve_to(-176, -128, -160, -134, -140, -136)
    ctx.line_to(-118, -230); ctx.curve_to(-114, -244, -100, -248, -84, -248); ctx.line_to(56, -248)
    ctx.curve_to(70, -248, 80, -242, 88, -230); ctx.line_to(130, -140); ctx.curve_to(170, -136, 196, -128, 200, -104)
    ctx.line_to(200, -46); ctx.curve_to(200, -36, 192, -34, 184, -34); ctx.close_path()
    # windows (cut out so Haru shows through)
    ctx.move_to(-104, -138); ctx.line_to(-88, -232); ctx.line_to(-30, -232); ctx.line_to(-30, -138); ctx.close_path()
    ctx.move_to(-16, -138); ctx.line_to(-16, -232); ctx.line_to(52, -232); ctx.curve_to(62, -232, 68, -228, 72, -220); ctx.line_to(108, -138); ctx.close_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgb(*col); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.set_line_width(4); ctx.stroke()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


def car(ctx, t, o, L):
    top = hexc(o['top']); col = hexc('#FF8F6B')
    bnc = 1.5 * math.sin(t * 9)
    ctx.save(); ctx.translate(0, bnc)
    # interior + Haru (seated, hands on the wheel)
    hip = (-2, -96)
    sh = (hip[0] + 4, hip[1] - 62)
    torso(ctx, hip, o, L, top)
    head(ctx, hip[0] + 8, hip[1] - 116 + 2 * math.sin(t * 5), t, o, L)
    ctx.set_line_width(5); ctx.set_source_rgb(*L); ctx.save(); ctx.translate(70, -150); ctx.scale(.35, 1); ctx.arc(0, 0, 26, 0, 2 * math.pi); ctx.restore(); ctx.stroke()
    arm_to(ctx, sh, (64, -160), top, L, False)
    # glass tint over the window holes, then the body around them
    ctx.set_source_rgba(.75, .9, 1, .08); ctx.rectangle(-110, -236, 224, 100); ctx.fill()
    _car_body(ctx, L, col)
    ctx.set_line_width(3); ctx.set_source_rgb(*L)
    poly(ctx, [(-22, -136), (-22, -60)]); poly(ctx, [(-10, -100), (8, -100)]); poly(ctx, [(-150, -100), (-132, -100)])
    ctx.arc(188, -96, 10, 0, 2 * math.pi); _shape(ctx, hexc('#FFF4C2'), L)
    ctx.rectangle(-180, -70, 16, 14); _shape(ctx, hexc('#FF5C5C'), L)
    ctx.restore()
    ang = t * 9
    wheel(ctx, -112, -34, 34, ang, L); wheel(ctx, 132, -34, 34, ang, L)


def bus(ctx, t, o, L):
    top = hexc(o['top']); col = hexc('#3FBF8F'); win = (.82, .93, 1)
    bnc = 1.2 * math.sin(t * 7)
    x0, x1, yb, yt = -360, 260, -44, -300
    ctx.save(); ctx.translate(0, bnc)
    wins = [(-330, -246), (-232, -148), (-134, -50), (-36, 48), (62, 146)]
    # window glass + passengers + Haru (window 4)
    for i, (a, b) in enumerate(wins):
        ctx.rectangle(a, -268, b - a, 104); ctx.set_source_rgb(*win); ctx.fill()
    import random
    rnd = random.Random(3)
    for i, (a, b) in enumerate(wins):
        if i == 3: continue
        if i in (0, 2):
            c = hexc(['#FF7A45', '#9B7BFF', '#FFB21A'][i % 3]); m = (a + b) / 2
            ctx.set_line_width(3); ctx.move_to(m - 26, -164); ctx.curve_to(m - 26, -200, m + 26, -200, m + 26, -164); ctx.close_path(); _shape(ctx, c, L)
            ctx.arc(m + 2, -222, 22, 0, 2 * math.pi); _shape(ctx, (1, .9, .8), L)
            ctx.save(); ctx.arc(m + 2, -222, 23, 0, 2 * math.pi); ctx.clip(); ctx.rectangle(m - 24, -250, 48, 18 + 6 * i); ctx.set_source_rgb(*hexc('#3B2A22')); ctx.fill(); ctx.restore()
            ctx.set_source_rgb(*L); ctx.arc(m + 2, -222, 22, 0, 2 * math.pi); ctx.stroke(); ctx.arc(m + 12, -220, 2.5, 0, 2 * math.pi); ctx.fill()
    a, b = wins[3]
    ctx.save(); ctx.rectangle(a, -268, b - a, 104); ctx.clip()
    hip = ((a + b) / 2 - 8, -102)
    torso(ctx, hip, o, L, top)
    head(ctx, hip[0] + 8, hip[1] - 116 + 2.5 * abs(math.sin(t * 4.2)), t, o, L)
    ctx.set_line_width(12); ctx.set_source_rgb(*top)
    ex, ey = ch.math.sin(math.radians(10)) * 30 + hip[0] + 2, hip[1] - 62 + math.cos(math.radians(10)) * 30
    poly(ctx, [(hip[0] + 2, hip[1] - 62), (ex, ey), (ex + 28 * math.sin(math.radians(-75)), ey + 28 * math.cos(math.radians(-75)))])
    ch._prop(ctx, 'iced', ex + 28 * math.sin(math.radians(-75)), ey + 28 * math.cos(math.radians(-75)), t, L, '#C68B59')
    ctx.restore()
    # body with window holes
    ctx.new_path(); ctx.set_line_width(4)
    ctx.move_to(x0 + 20, yb); ctx.line_to(x0, yb - 20); ctx.line_to(x0, yt + 24); ctx.curve_to(x0, yt + 6, x0 + 10, yt, x0 + 28, yt)
    ctx.line_to(x1 - 30, yt); ctx.curve_to(x1 - 6, yt, x1 + 8, yt + 20, x1 + 10, yt + 44); ctx.line_to(x1 + 14, yb - 16); ctx.curve_to(x1 + 14, yb - 4, x1 + 6, yb, x1 - 4, yb); ctx.close_path()
    for a, b in wins: ctx.rectangle(a, -268, b - a, 104)
    ctx.move_to(170, -268); ctx.line_to(250, -268); ctx.line_to(262, -150); ctx.line_to(170, -150); ctx.close_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); ctx.set_source_rgb(*col); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.stroke(); ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.set_source_rgba(.75, .9, 1, .35); ctx.move_to(170, -268); ctx.line_to(250, -268); ctx.line_to(262, -150); ctx.line_to(170, -150); ctx.close_path(); ctx.fill()
    ctx.rectangle(x0, -140, x1 - x0 + 12, 16); ctx.set_source_rgb(*hexc('#FFFFFF')); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.set_line_width(3); ctx.stroke()
    ctx.rectangle(-300, -290, 260, 20); _shape(ctx, hexc('#2B2541'), L)
    ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(15); ctx.set_source_rgb(*hexc('#FFD86B'))
    ctx.move_to(-288, -275); ctx.show_text('OPEN TO CLOSE  ·  RIVERSIDE'); ctx.new_path()
    ctx.arc(256, -80, 10, 0, 2 * math.pi); _shape(ctx, hexc('#FFF4C2'), L)
    ctx.rectangle(110, -120, 46, 70); _shape(ctx, lerp(col, (1, 1, 1), .25), L)
    ctx.restore()
    ang = t * 8
    wheel(ctx, -250, -40, 38, ang, L); wheel(ctx, 160, -40, 38, ang, L)


OUTFITS = {
    'run':  dict(top='#FF6B5B', bottom='#2B2541', shorts=True, shoe='#2EC4A6', phones='#FFD84A', phones_style='retro', detail='bib'),
    'bike': dict(top='#FFD84A', bottom='#3E4A6B', shoe='#FFFFFF', phones='#2EC4A6', phones_style='retro', detail='reflect', helmet='#FF7A6B', helmet_stripe='#FFFFFF', bag='crossbody', bag_color='#FF7A6B', strap='#2B2541'),
    'kick': dict(top='#B9A4FF', bottom='#7A8B5A', shoe='#E0457B', phones='#FF8A3D', phones_style='retro', detail='graphic', helmet='#2EC4A6', helmet_stripe='#B9A4FF'),
    'car':  dict(top='#7FB6E8', bottom='#3E4A6B', shoe='#FFFFFF', phones='#FF5C8A', phones_style='retro', detail='collar'),
    'bus':  dict(top='#E9B44C', bottom='#5B6B8A', shoe='#FFFFFF', phones='#7B3BFF', phones_style='retro', detail='buttons', bag='tote', bag_color='#F3E9D2'),
}

MODES = {'run': (run, 2.2, 'Running'), 'bike': (bike, 2.6, 'Bicycle'), 'kick': (kick, 2.0, 'Kick Scooter'),
         'car': (car, 3.2, 'Car'), 'bus': (bus, 2.6, 'Bus')}
