"""PLAY LIST 04 rides: ice skates, Christmas tram, husky dog sled, bell carriage, reindeer sky sleigh.
Haru is posed for each ride (bent knees, hands on handles and reins, scarf in the wind); her head is
character.draw_head, so face, glasses, bob hair and proportions never change."""
import math
import cairo
import character as ch
from mobility import mob
hx, lerp, shape = mob.hexc, mob.lerp, mob._shape
L = hx('#2B2541')
RED, GREEN, GOLD, CREAM = '#D94040', '#2E8B57', '#F2C230', '#FFF6E0'
SKIN = ch.SKIN

def rrect(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()

def glow(c, x, y, r, col=(1, .86, .5), a=.55):
    g = cairo.RadialGradient(x, y, 0, x, y, r); g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    c.set_source(g); c.arc(x, y, r, 0, 6.3); c.fill()

def shadow(c, x, y, w, a=.18):
    c.save(); c.translate(x, y); c.scale(1, .16); c.arc(0, 0, w, 0, 6.3); c.restore(); c.set_source_rgba(.15, .15, .3, a); c.fill()

def haru(c, x, gy, t, outfit, walk=0.0, phase=0.0, scale=1.0, **kw):
    c.save(); c.translate(x, gy); c.scale(scale, scale); hd = ch.draw(c, 0, 0, t, outfit=outfit, walk=walk, phase=phase, **kw); c.restore(); return hd

def light_string(c, x0, x1, y, t, lit, n=10):
    c.set_line_width(2); c.set_source_rgb(*L); c.move_to(x0, y); c.line_to(x1, y); c.stroke()
    for k in range(n):
        x = x0 + (x1 - x0) * (k + .5) / n; col = hx((RED, GOLD, GREEN, '#5BA8FF')[k % 4])
        if lit: glow(c, x, y + 5, 14, col, .5 + .2 * math.sin(t * 4 + k))
        c.arc(x, y + 5, 4.5, 0, 6.3); shape(c, col, L)

# ---------------- posed Haru ----------------
def _hand(c, p, o):
    c.set_line_width(3); c.arc(p[0], p[1], 8, 0, 6.3); shape(c, hx(o['mitten']) if o.get('mitten') else SKIN, L)

def _scarf_tail(c, hip, o, t, wind):
    if not o.get('scarf') or wind <= 0: return
    x, y = hip; sc = hx(o['scarf']); c.set_line_width(3)
    w = 50 + 40 * wind
    c.move_to(x - 14, y - 76); c.curve_to(x - w * .4, y - 80 + 6 * math.sin(t * 9), x - w * .7, y - 72 - 6 * math.sin(t * 9 + 1), x - w, y - 70 + 5 * math.sin(t * 11))
    c.line_to(x - w + 4, y - 58 + 5 * math.sin(t * 11)); c.curve_to(x - w * .6, y - 62, x - w * .35, y - 64, x - 14, y - 64); c.close_path(); shape(c, sc, L)

def pose(c, hip, t, outfit, feet, hands, lean=0.0, wind=0.0, don=1.0, reach=0.0, press=0.0, head_dy=0.0):
    """Haru with hips at `hip`, feet and hands placed in world coords (feet/hands: (back, front)).
    reach/press: the back hand goes up to tap the headphones (the song-change ritual)."""
    o = ch.OUTFITS[outfit]; mob.O = o
    top, pants = hx(o['top']), hx(o['bottom'])
    c.save(); c.translate(*hip); c.rotate(lean); c.translate(-hip[0], -hip[1])
    sh = (hip[0] + 2, hip[1] - 62); hd = (hip[0] + 6, hip[1] - 116 + head_dy)
    if reach > 0:
        _, _, _, _, _, px, py = ch.phones_pose(hd[0], hd[1], 42, don)
        tap = (px + 4 - 2 * press, py + 6)
        hb = (hands[0][0] + (tap[0] - hands[0][0]) * reach, hands[0][1] + (tap[1] - hands[0][1]) * reach)
    else: hb = hands[0]
    _scarf_tail(c, hip, o, t, wind)
    mob.leg_to(c, hip, feet[0], pants, L, True)
    if reach <= 0: mob.arm_to(c, sh, hb, top, L, True); _hand(c, mob.ik(sh[0], sh[1], hb[0], hb[1], 32, 30, -1)[1], o)
    if o.get('coat'): ch._coat(c, hip, o['top'], L)
    mob.torso(c, hip, dict(o, bag=None, detail='scarf' if o.get('scarf') else None), L, top)
    if o.get('knit'): ch._knit(c, hip, L)
    mob.leg_to(c, hip, feet[1], pants, L, False)
    ch.draw_head(c, hd[0], hd[1], t, o, L, don)
    if reach > 0: mob.arm_to(c, sh, hb, top, L, True); _hand(c, mob.ik(sh[0], sh[1], hb[0], hb[1], 32, 30, -1)[1], o)
    mob.arm_to(c, sh, hands[1], top, L, False); _hand(c, mob.ik(sh[0], sh[1], hands[1][0], hands[1][1], 32, 30, -1)[1], o)
    c.restore()

def blade(c, f):
    c.set_line_width(4); c.rectangle(f[0] - 7, f[1] - 14, 22, 12); shape(c, (1, 1, 1), L)
    c.set_line_width(4); c.set_source_rgb(*L); c.move_to(f[0] - 2, f[1] + 2); c.line_to(f[0] - 2, f[1] + 10); c.move_to(f[0] + 12, f[1] + 2); c.line_to(f[0] + 12, f[1] + 10); c.stroke()
    c.set_line_width(5); c.move_to(f[0] - 10, f[1] + 12); c.line_to(f[0] + 20, f[1] + 12); c.curve_to(f[0] + 27, f[1] + 12, f[0] + 27, f[1] + 4, f[0] + 22, f[1] + 4)
    c.set_source_rgb(*L); c.stroke_preserve(); c.set_source_rgb(.85, .89, .95); c.set_line_width(2.5); c.stroke()


def crack(c, x, y, k):
    """little star burst where a whip or the reins snap"""
    if not 0 < k < 1: return
    for j in range(8):
        a = j * math.pi / 4; r0, r1 = 8 + 20 * k, 18 + 34 * k
        c.set_line_width(3); c.set_source_rgba(1, .95, .7, 1 - k); c.move_to(x + r0 * math.cos(a), y + r0 * math.sin(a)); c.line_to(x + r1 * math.cos(a), y + r1 * math.sin(a)); c.stroke()
    glow(c, x, y, 40, (1, .9, .6), .5 * (1 - k))

def snap(t, every=5.0, dur=.9, off=0.0):
    """0..1 progress of a whip/rein snap that happens once every `every` seconds, else -1"""
    u = (t + off) % every
    return u / dur if u < dur else -1

# ---------------- 1. ice skates ----------------
def skate(c, x, gy, t, outfit, moving=1.0, **kw):
    """speed skater: bent low with both hands behind the back; the two legs take turns gliding under the body
    and pushing out behind. Feet are placed on the ice, then turned back by the lean so the boots stay on the blades."""
    ph = t * 2 * math.pi * .6; gy -= 12; feet = []
    for j in (0, 1):
        u = (ph / (2 * math.pi) + j * .5) % 1
        if u < .5: fx, fy = x + 18 - 30 * (u / .5), gy                      # glide: the foot runs back under the body
        else:                                                               # push: out behind, lifted, then back in
            v = (u - .5) / .5; a = math.sin(math.pi * v)
            fx = x - 12 - 72 * a + (30 * v if v > .5 else 0) * (1 - a); fy = gy - 18 * a
        feet.append((x + (fx - x) * moving, gy + (fy - gy) * moving))
    hip = (x, gy - 76 + 4 * abs(math.sin(ph)) * moving)
    hands = ((x - 34, hip[1] - 6), (x - 26, hip[1] - 2))
    ln = .45 * moving; fixed = []
    for fx, fy in feet:                                                     # never further than the leg can reach
        dx, dy = fx - hip[0], fy - hip[1]; d = math.hypot(dx, dy)
        if d > 84: dx, dy = dx * 84 / d, dy * 84 / d
        fixed.append((hip[0] + dx, hip[1] + dy))
    feet = fixed; co, si = math.cos(-ln), math.sin(-ln)
    loc = tuple((hip[0] + (fx - hip[0]) * co - (fy - hip[1]) * si, hip[1] + (fx - hip[0]) * si + (fy - hip[1]) * co) for fx, fy in feet)
    shadow(c, x, gy + 14, 70)
    pose(c, hip, t, outfit, loc, hands, lean=ln, wind=.6 * moving, **kw)
    for f in feet: blade(c, f)
    c.set_line_width(2.5)
    for k in range(int(4 * moving + .5)):
        c.move_to(x - 30 - k * 70, gy + 14 + k * 2); c.line_to(x - 100 - k * 70, gy + 16 + k * 2); c.set_source_rgba(1, 1, 1, .85 - k * .18); c.stroke()
    if moving > .3:
        push = min(feet, key=lambda f: f[0])
        for k in range(6):
            a = (t * 7 + k * .5) % 1; c.arc(push[0] - 10 - 50 * a, push[1] + 10 - 18 * a * (1 - a) * 4, 3 * (1 - a) + 1, 0, 6.3); c.set_source_rgba(1, 1, 1, .9 * (1 - a)); c.fill()

# ---------------- 2. tram ----------------
def tram(c, x, gy, t, outfit, lit=False, moving=1.0, **kw):
    """red Christmas tram seen from the side; Haru stands inside holding a ceiling strap"""
    sway = 0.0; bump = 0.0
    w, h = 640, 300; x0, y0 = x - w / 2, gy - 40 - h - bump
    c.save(); c.translate(x, gy); c.rotate(sway); c.translate(-x, -gy)
    shadow(c, x, gy + 6, 300, .22)
    # pantograph + spark on the wire
    c.set_line_width(4); c.set_source_rgb(*L); c.move_to(x - 120, y0 - 6); c.line_to(x - 80, y0 - 70); c.line_to(x - 10, y0 - 70); c.stroke()
    if moving > .3 and (t * 3) % 1 < .12: glow(c, x - 45, y0 - 72, 30, (.6, .85, 1), .9)
    rrect(c, x0, y0, w, h, 40); shape(c, hx('#C62E2E'), L)
    rrect(c, x0 + 20, y0 - 24, w - 40, 30, 12); shape(c, hx('#A82424'), L)
    light_string(c, x0 + 40, x0 + w - 40, y0 - 28, t, lit, 16)
    # big middle window with Haru + passengers inside
    wx, wy, ww, wh = x - 230, y0 + 36, 360, 170
    rrect(c, wx, wy, ww, wh, 18); shape(c, hx('#FFF2D0') if lit else hx('#EAF4FF'), L)
    c.save(); rrect(c, wx, wy, ww, wh, 18); c.clip()
    c.set_line_width(5); c.set_source_rgb(*hx('#B0B6C8')); c.move_to(wx, wy + 24); c.line_to(wx + ww, wy + 24); c.stroke()
    for k, px in enumerate((wx + 50, wx + 300)):   # passengers (simple, not Haru)
        c.set_line_width(3); rrect(c, px - 22, wy + 92, 44, 90, 14); shape(c, hx(('#2C3E66', '#7B1E3A')[k]), L)
        c.arc(px, wy + 72, 20, 0, 6.3); shape(c, SKIN, L); c.arc(px, wy + 66, 21, math.pi, 2 * math.pi); c.close_path(); shape(c, hx(('#5A3B2E', '#2B2541')[k]), L)
    hip = (x - 40, wy + 200)
    strap = (x - 10, wy + 40)
    c.set_line_width(3); c.set_source_rgb(*L); c.move_to(strap[0], wy + 24); c.line_to(strap[0], strap[1] - 8); c.stroke()
    c.arc(strap[0], strap[1], 9, 0, 6.3); c.set_line_width(4); c.set_source_rgb(*hx(GOLD)); c.stroke()
    pose(c, hip, t, outfit, ((hip[0] - 14, hip[1] + 86), (hip[0] + 16, hip[1] + 86)), ((hip[0] - 30, hip[1] - 20), strap), **kw)
    c.restore()
    c.set_line_width(5); c.set_source_rgb(*L)
    for k in (1, 2): c.move_to(wx + ww * k / 3, wy); c.line_to(wx + ww * k / 3, wy + wh); c.stroke()
    rrect(c, wx, wy, ww, wh, 18); c.set_line_width(5); c.stroke()
    c.set_source_rgba(1, 1, 1, .35)
    for k in range(3): c.move_to(wx + 20 + k * 120, wy + 20); c.line_to(wx + 60 + k * 120, wy + 20); c.line_to(wx + 20 + k * 120, wy + 70); c.close_path(); c.fill()
    # front window, door, wreath, cream band, number
    rrect(c, x + 160, y0 + 36, 110, 120, 18); shape(c, hx('#FFF2D0') if lit else hx('#EAF4FF'), L)
    c.set_line_width(8); c.set_source_rgb(*hx(GREEN)); c.arc(x + 215, y0 + 220, 28, 0, 6.3); c.stroke()
    c.move_to(x + 205, y0 + 248); c.line_to(x + 225, y0 + 248); c.line_to(x + 215, y0 + 232); c.close_path(); c.set_line_width(3); shape(c, hx(RED), L)
    rrect(c, x0 + 8, y0 + 214, w - 16, 34, 10); shape(c, hx(CREAM), L)
    c.select_font_face('Outfit', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(22); c.set_source_rgb(*L); c.move_to(x0 + 40, y0 + 238); c.show_text('NO. 25  CHRISTMAS LINE')
    rrect(c, x0 + w - 16, y0 + 50, 12, 28, 4); shape(c, hx('#FFE27A'), L)
    if lit: glow(c, x0 + w, y0 + 64, 70, (1, .9, .6), .5)
    for wxl in (x - 200, x + 200):
        for dx in (-36, 36):
            ang = -t * 9 * moving
            c.arc(wxl + dx, gy - 22 - bump * .3, 22, 0, 6.3); c.set_line_width(4); shape(c, hx('#3B3F5C'), L)
            c.set_line_width(3); c.set_source_rgb(*hx('#C9CCD8'))
            for k in range(3): a = ang + k * 2.09; c.move_to(wxl + dx, gy - 22); c.line_to(wxl + dx + 16 * math.cos(a), gy - 22 + 16 * math.sin(a)); c.stroke()
    c.restore()

# ---------------- 3. husky dog sled ----------------
def husky(c, x, y, t, k=0, moving=1.0):
    ph = t * 2 * math.pi * 2.2 * (.3 + .7 * moving) + k * 1.3; g = math.sin(ph) * moving
    body, belly = hx('#5E6A7D'), hx('#FFFFFF')
    by = y - 52 - 4 * abs(g)
    for j, (dx, off) in enumerate(((-30, 0), (-18, .6), (28, 3.1), (40, 3.7))):   # gallop
        a = .7 * math.sin(ph + off) * moving
        fx, fy = x + dx + 28 * math.sin(a), y - 4 * max(0, math.cos(ph + off))
        for w_, col in ((11, L), (6, body if j % 2 else belly)): c.set_line_width(w_); c.set_source_rgb(*col); c.move_to(x + dx, by + 10); c.line_to(fx, fy); c.stroke()
    c.set_line_width(4); c.save(); c.translate(x + 5, by); c.scale(1, .5); c.arc(0, 0, 54, 0, 6.3); c.restore(); shape(c, body, L)
    c.save(); c.translate(x + 5, by + 10); c.scale(1, .3); c.arc(0, 0, 44, 0, math.pi); c.restore(); c.set_source_rgb(*belly); c.fill()
    c.move_to(x - 46, by - 6); c.curve_to(x - 80, by - 40 + 6 * g, x - 70, by - 64, x - 50, by - 50); c.curve_to(x - 60, by - 30, x - 48, by - 16, x - 40, by - 10); c.close_path(); shape(c, body, L)
    hxx, hyy = x + 62, by - 30 - 3 * g
    c.move_to(x + 40, by - 10); c.line_to(hxx - 6, hyy - 6); c.line_to(hxx + 8, hyy + 14); c.line_to(x + 52, by + 6); c.close_path(); shape(c, body, L)
    c.arc(hxx, hyy, 22, 0, 6.3); shape(c, body, L)
    c.save(); c.arc(hxx, hyy, 22, 0, 6.3); c.clip(); c.move_to(hxx - 4, hyy - 22); c.line_to(hxx + 6, hyy + 4); c.line_to(hxx + 30, hyy + 4); c.line_to(hxx + 30, hyy + 30); c.line_to(hxx - 30, hyy + 30); c.line_to(hxx - 10, hyy + 6); c.close_path(); c.set_source_rgb(*belly); c.fill(); c.restore()
    c.save(); c.translate(hxx + 24, hyy + 6); c.scale(1.4, 1); c.arc(0, 0, 10, 0, 6.3); c.restore(); shape(c, belly, L)
    c.arc(hxx + 36, hyy + 2, 4, 0, 6.3); c.set_source_rgb(*L); c.fill()
    c.arc(hxx + 6, hyy - 4, 3.5, 0, 6.3); c.fill()
    for d in (-1, 1): c.move_to(hxx - 10 + 8 * d, hyy - 16); c.line_to(hxx - 6 + 10 * d, hyy - 38); c.line_to(hxx + 4 + 6 * d, hyy - 18); c.close_path(); shape(c, body, L)
    if moving > .2: c.move_to(hxx + 26, hyy + 12); c.curve_to(hxx + 30, hyy + 26, hxx + 20, hyy + 30, hxx + 18, hyy + 16); shape(c, hx('#FF7A8A'), L)
    c.set_line_width(5); c.set_source_rgb(*hx(RED)); c.move_to(x + 36, by - 14); c.line_to(x + 46, by + 8); c.stroke()

def dogsled(c, x, gy, t, outfit, moving=1.0, **kw):
    """three huskies on a gangline pull a basket sled; Haru stands with one foot on each runner, holding the handlebar"""
    bump = 3 * abs(math.sin(t * 6)) * moving
    shadow(c, x + 250, gy + 8, 360, .2)
    c.set_line_width(3); c.set_source_rgb(*L); c.move_to(x + 120, gy - 50); c.line_to(x + 620, gy - 50); c.stroke()
    for k in range(3): husky(c, x + 230 + k * 170, gy, t, k, moving)
    # runners + basket
    for k, (dy, dx, shade) in enumerate(((-20, -18, .35), (-2, 0, 0))):   # far runner (higher, darker), near runner: one ski per foot
        ry = gy + dy
        c.set_line_width(12); c.set_source_rgb(*L); c.move_to(x - 150 + dx, ry); c.line_to(x + 110 + dx, ry); c.curve_to(x + 150 + dx, ry, x + 160 + dx, ry - 36, x + 130 + dx, ry - 52); c.stroke()
        c.set_line_width(6); c.set_source_rgb(*lerp(hx('#C98F6A'), (.2, .2, .3), shade)); c.move_to(x - 150 + dx, ry); c.line_to(x + 110 + dx, ry); c.curve_to(x + 150 + dx, ry, x + 160 + dx, ry - 36, x + 130 + dx, ry - 52); c.stroke()
        c.set_line_width(2.5); c.set_source_rgb(*lerp(hx('#C9CCD8'), (.2, .2, .3), shade)); c.move_to(x - 150 + dx, ry + 4); c.line_to(x + 110 + dx, ry + 4); c.stroke()
        c.set_line_width(3); rrect(c, x - 146 + dx + 30 * k, ry - 12, 46, 8, 3); shape(c, lerp(hx('#3B3F5C'), (0, 0, 0), shade), L)   # foot pad
    hip = (x - 100, gy - 96 - bump)
    pose(c, hip, t, outfit, ((x - 134, gy - 34), (x - 88, gy - 16)), ((x - 30, hip[1] - 44), (x - 20, hip[1] - 40)), lean=.18 * moving, wind=moving, **kw)
    c.set_line_width(5); c.set_source_rgb(*L); c.move_to(x - 28, hip[1] - 44); c.line_to(x - 40, gy - 4); c.stroke()
    c.set_line_width(4); c.move_to(x - 40, gy - 90 - bump); c.line_to(x + 120, gy - 90 - bump); c.line_to(x + 120, gy - 34); c.line_to(x - 40, gy - 34); c.close_path(); shape(c, hx('#C98F6A'), L)
    for k in range(5): c.move_to(x - 20 + k * 32, gy - 88 - bump); c.line_to(x - 20 + k * 32, gy - 36); c.set_line_width(2); c.set_source_rgb(*L); c.stroke()
    c.set_line_width(4); c.rectangle(x + 10, gy - 128 - bump, 44, 38); shape(c, hx(RED), L); c.rectangle(x + 28, gy - 128 - bump, 8, 38); shape(c, hx(GOLD), L)
    c.rectangle(x + 64, gy - 116 - bump, 34, 26); shape(c, hx(GREEN), L)
    for xx in (x - 20, x + 90): c.move_to(xx, gy - 34); c.line_to(xx, gy - 4); c.set_line_width(4); c.set_source_rgb(*L); c.stroke()
    if moving > .2:
        for k in range(10):
            a = (t * 4 + k * .1) % 1; c.arc(x - 130 - 120 * a, gy - 10 - 40 * a * (1 - a) * 4 * (k % 3) / 2, (8 - 6 * a) * moving, 0, 6.3); c.set_source_rgba(1, 1, 1, .9 * (1 - a)); c.fill()

# ---------------- 4. bell carriage ----------------
def horse(c, x, gy, t, col='#F4F1EC', moving=1.0):
    ph = t * 2 * math.pi * 1.0 * (.3 + .7 * moving); c.set_line_width(4)
    for k, (dx, off) in enumerate(((-60, 0), (-44, math.pi), (44, math.pi / 2), (60, 3 * math.pi / 2))):   # walk
        a = .3 * math.sin(ph + off) * moving; lift = 14 * max(0, math.sin(ph + off)) * moving
        kx, ky = x + dx + 18 * math.sin(a), gy - 44 - lift * .5
        for w_, cc in ((13, L), (8, hx(col))): c.set_line_width(w_); c.set_source_rgb(*cc); c.move_to(x + dx, gy - 90); c.line_to(kx, ky); c.line_to(kx + 6 * math.sin(a), gy - 8 - lift); c.stroke()
        c.set_line_width(4); c.rectangle(kx + 6 * math.sin(a) - 9, gy - 14 - lift, 18, 10); shape(c, hx('#6B5B4B'), L)
    bob = 3 * math.sin(ph * 2) * moving
    c.save(); c.translate(x, gy - 116 + bob); c.scale(1, .52); c.arc(0, 0, 92, 0, 6.3); c.restore(); shape(c, hx(col), L)
    c.move_to(x + 60, gy - 126 + bob); c.line_to(x + 108, gy - 196 + bob); c.line_to(x + 148, gy - 178 + bob); c.line_to(x + 96, gy - 110 + bob); c.close_path(); shape(c, hx(col), L)
    c.save(); c.translate(x + 150, gy - 178 + bob); c.rotate(.5); c.scale(1.6, 1); c.arc(0, 0, 19, 0, 6.3); c.restore(); shape(c, hx(col), L)
    c.arc(x + 144, gy - 192 + bob, 4, 0, 6.3); c.set_source_rgb(*L); c.fill()
    c.move_to(x + 112, gy - 202 + bob); c.line_to(x + 118, gy - 222 + bob); c.line_to(x + 126, gy - 200 + bob); c.close_path(); shape(c, hx(col), L)
    c.set_line_width(11); c.set_source_rgb(*hx('#B08968')); c.move_to(x + 106, gy - 194 + bob); c.curve_to(x + 80, gy - 176 + bob, x + 70, gy - 146 + bob, x + 62, gy - 128 + bob); c.stroke()
    c.set_line_width(10); c.move_to(x - 90, gy - 124 + bob); c.curve_to(x - 124, gy - 110 + 8 * math.sin(t * 4), x - 124, gy - 70, x - 106, gy - 52); c.stroke()
    c.set_line_width(7); c.set_source_rgb(*hx(RED)); c.move_to(x + 72, gy - 156 + bob); c.line_to(x + 30, gy - 104 + bob); c.stroke()
    c.move_to(x + 120, gy - 190 + bob); c.line_to(x + 160, gy - 172 + bob); c.stroke()
    for k in range(5):   # jingle bells swing with the step
        bx, by = x + 68 - k * 10 + 3 * math.sin(t * 12 + k) * moving, gy - 150 + k * 11 + bob
        c.arc(bx, by, 6.5, 0, 6.3); c.set_line_width(3); shape(c, hx(GOLD), L)
    if (t * .8) % 1 < .45:   # breath in the cold air
        a = ((t * .8) % 1) / .45
        c.arc(x + 178 + 30 * a, gy - 168 + bob - 6 * a, 8 + 14 * a, 0, 6.3); c.set_source_rgba(1, 1, 1, .6 * (1 - a)); c.fill()

def coachman(c, x, y, t):
    c.set_line_width(3); rrect(c, x - 20, y - 70, 40, 64, 14); shape(c, hx('#2E7D4F'), L)
    c.arc(x, y - 86, 18, 0, 6.3); shape(c, SKIN, L)
    c.move_to(x - 18, y - 80); c.curve_to(x - 20, y - 60, x + 20, y - 60, x + 18, y - 80); c.close_path(); shape(c, (1, 1, 1), L)
    c.rectangle(x - 16, y - 126, 32, 30); shape(c, hx('#2B2541'), L); c.rectangle(x - 24, y - 100, 48, 6); shape(c, hx('#2B2541'), L)
    c.rectangle(x - 16, y - 108, 32, 6); shape(c, hx(RED), L)
    c.arc(x + 8, y - 90, 2.5, 0, 6.3); c.set_source_rgb(*L); c.fill()
    k = snap(t, 5.0, .9)
    lift = math.sin(math.pi * k) if k >= 0 else 0
    hand = (x + 40 + 6 * lift, y - 40 - 40 * lift)
    c.set_line_width(9); c.set_source_rgb(*hx('#2E7D4F')); c.move_to(x + 10, y - 56); c.line_to(*hand); c.stroke()
    # whip: a stick and a lash that flicks forward
    tip = (hand[0] + 30 + 20 * lift, hand[1] - 70 + 20 * lift)
    c.set_line_width(4); c.set_source_rgb(*hx('#6B4A2E')); c.move_to(*hand); c.line_to(*tip); c.stroke()
    w = 1 - abs(2 * k - 1) if k >= 0 else 0
    c.set_line_width(2); c.set_source_rgb(*L); c.move_to(*tip)
    end = (tip[0] + 60 + 50 * w, tip[1] + 30 - 60 * w)
    c.curve_to(tip[0] + 30, tip[1] - 20 - 30 * w, end[0] - 30, end[1] + 30 * (1 - w), *end); c.stroke()
    if k > .45: crack(c, *end, (k - .45) / .55)
    _hand(c, hand, {})

def carriage(c, x, gy, t, outfit, lit=False, moving=1.0, **kw):
    """open red carriage: Haru sits under a plaid blanket and waves, a coachman holds the reins of a white horse"""
    bob = 3 * math.sin(t * 2 * math.pi * 1.0 * 2) * moving
    shadow(c, x + 150, gy + 6, 340, .2)
    horse(c, x + 360, gy, t, moving=moving)
    c.set_line_width(5); c.set_source_rgb(*L); c.move_to(x + 150, gy - 110 + bob); c.line_to(x + 300, gy - 118); c.stroke()
    # seat back + Haru seated (hip on the seat, knees forward, feet on the floor)
    c.set_line_width(4); c.move_to(x - 150, gy - 120 + bob); c.curve_to(x - 170, gy - 240 + bob, x - 100, gy - 250 + bob, x - 80, gy - 200 + bob); c.line_to(x - 90, gy - 120 + bob); c.close_path(); shape(c, hx('#8E1E30'), L)
    hip = (x - 60, gy - 150 + bob)
    wave = .5 + .5 * math.sin(t * 6)
    pose(c, hip, t, outfit, ((x - 10, gy - 92 + bob), (x + 4, gy - 92 + bob)), ((x - 40, gy - 170 + bob), (x + 2 + 8 * wave, gy - 236 + bob - 10 * wave)), **kw)
    # plaid blanket over the lap
    c.save(); c.move_to(x - 96, gy - 150 + bob); c.curve_to(x - 60, gy - 168 + bob, x + 10, gy - 162 + bob, x + 30, gy - 140 + bob); c.line_to(x + 34, gy - 92 + bob); c.line_to(x - 90, gy - 92 + bob); c.close_path()
    c.set_source_rgb(*hx('#C62E2E')); c.fill_preserve(); c.clip()
    c.set_line_width(5); c.set_source_rgba(*hx('#2E7D4F'), .8)
    for k in range(8): c.move_to(x - 100 + k * 20, gy - 180); c.line_to(x - 100 + k * 20, gy - 80); c.stroke()
    for k in range(5): c.move_to(x - 110, gy - 170 + k * 18 + bob); c.line_to(x + 40, gy - 170 + k * 18 + bob); c.stroke()
    c.restore(); c.set_line_width(3.5); c.move_to(x - 96, gy - 150 + bob); c.curve_to(x - 60, gy - 168 + bob, x + 10, gy - 162 + bob, x + 30, gy - 140 + bob); c.set_source_rgb(*L); c.stroke()
    # coachman's box
    c.set_line_width(4); c.rectangle(x + 70, gy - 170 + bob, 70, 60); shape(c, hx('#8E1E30'), L)
    coachman(c, x + 104, gy - 170 + bob, t)
    c.set_line_width(2.5); c.set_source_rgb(*hx('#6B4A2E')); c.move_to(x + 146, gy - 210 + bob); c.curve_to(x + 260, gy - 200, x + 360, gy - 190, x + 440, gy - 170); c.stroke()
    # body
    c.set_line_width(4)
    c.move_to(x - 170, gy - 140 + bob); c.line_to(x + 150, gy - 140 + bob); c.curve_to(x + 170, gy - 140 + bob, x + 170, gy - 60 + bob, x + 140, gy - 60 + bob)
    c.line_to(x - 150, gy - 60 + bob); c.curve_to(x - 190, gy - 60 + bob, x - 200, gy - 140 + bob, x - 170, gy - 140 + bob); c.close_path(); shape(c, hx('#B3263A'), L)
    c.set_line_width(5); c.set_source_rgb(*hx(GOLD)); c.move_to(x - 160, gy - 126 + bob); c.line_to(x + 150, gy - 126 + bob); c.stroke()
    c.arc(x - 20, gy - 96 + bob, 20, 0, 6.3); c.set_line_width(4); shape(c, hx(GOLD), L)
    c.set_line_width(6); c.set_source_rgb(*hx(GREEN)); c.arc(x - 20, gy - 96 + bob, 12, 0, 6.3); c.stroke()
    light_string(c, x - 160, x + 150, gy - 140 + bob, t, lit, 12)
    c.move_to(x - 180, gy - 140 + bob); c.line_to(x - 180, gy - 230 + bob); c.set_line_width(4); c.set_source_rgb(*L); c.stroke()
    rrect(c, x - 192, gy - 262 + bob, 24, 34, 6); shape(c, hx('#FFE27A') if lit else hx(CREAM), L)
    if lit: glow(c, x - 180, gy - 245 + bob, 70, (1, .85, .5), .55)
    for wx, r in ((x - 110, 52), (x + 100, 40)):
        c.arc(wx, gy - r, r, 0, 6.3); c.set_line_width(5); shape(c, hx(GOLD), L)
        c.set_line_width(3); c.set_source_rgb(*L)
        for k in range(8): a = k * math.pi / 4 + t * 2.4 * moving * 60 / r; c.move_to(wx, gy - r); c.line_to(wx + r * math.cos(a), gy - r + r * math.sin(a)); c.stroke()
        c.arc(wx, gy - r, 8, 0, 6.3); shape(c, hx('#B3263A'), L)

# ---------------- 5. reindeer sky sleigh ----------------
def reindeer(c, x, y, t, k=0, nose=False, moving=1.0):
    """flying gallop: front legs reach forward, back legs kick back"""
    ph = t * 2 * math.pi * 1.4 + k; col = hx('#A0703F'); s = math.sin(ph) * moving
    for j, (dx, fw) in enumerate(((-36, -1), (-22, -1), (28, 1), (42, 1))):
        tip = (x + dx + fw * (34 + 16 * s), y + 44 - 10 * fw * s)
        for w_, cc in ((10, L), (6, col)):
            c.set_line_width(w_); c.set_source_rgb(*cc); c.move_to(x + dx, y + 16); c.line_to((x + dx + tip[0]) / 2 + fw * 4, y + 36); c.line_to(*tip); c.stroke()
    c.set_line_width(4); c.save(); c.translate(x, y); c.rotate(-.06 * s); c.scale(1, .55); c.arc(0, 0, 60, 0, 6.3); c.restore(); shape(c, col, L)
    c.save(); c.translate(x - 4, y + 10); c.scale(1, .3); c.arc(0, 0, 44, 0, math.pi); c.restore(); c.set_source_rgb(*hx('#E8D3B0')); c.fill()
    c.move_to(x + 40, y - 10); c.line_to(x + 70, y - 60); c.line_to(x + 96, y - 46); c.line_to(x + 60, y + 6); c.close_path(); c.set_line_width(4); shape(c, col, L)
    c.save(); c.translate(x + 96, y - 52); c.rotate(.4); c.scale(1.5, 1); c.arc(0, 0, 15, 0, 6.3); c.restore(); shape(c, col, L)
    for lean in (-1, 1):
        for w_, cc in ((7, L), (4, hx('#E8D3B0'))):
            c.set_line_width(w_); c.set_source_rgb(*cc)
            c.move_to(x + 82 + 6 * lean, y - 64); c.line_to(x + 76 + 16 * lean, y - 100); c.stroke()
            c.move_to(x + 79 + 10 * lean, y - 84); c.line_to(x + 92 + 18 * lean, y - 92); c.stroke()
    c.arc(x + 92, y - 66, 3.5, 0, 6.3); c.set_source_rgb(*L); c.fill()
    if nose: glow(c, x + 118, y - 44, 44, (1, .25, .25), .55 + .25 * math.sin(t * 5))
    c.arc(x + 118, y - 44, 8, 0, 6.3); shape(c, hx('#FF3B3B') if nose else hx('#5A3B2E'), L)
    c.set_line_width(7); c.set_source_rgb(*hx(RED)); c.move_to(x + 42, y - 14); c.line_to(x + 58, y + 10); c.stroke()
    for j in range(3): c.arc(x + 46 + j * 5, y - 6 + j * 7, 5, 0, 6.3); c.set_line_width(2.5); shape(c, hx(GOLD), L)
    c.move_to(x - 58, y - 8); c.line_to(x - 74, y - 20); c.line_to(x - 62, y + 2); c.close_path(); shape(c, hx('#E8D3B0'), L)

def sky_sleigh(c, x, y, t, outfit, moving=1.0, **kw):
    """Haru sits in the sleigh holding the reins; the sleigh pitches gently as it flies, sparkles trail behind"""
    bob = 12 * math.sin(t * 2); tilt = .05 * math.cos(t * 2) * moving
    for k in range(18):
        sx, sy = x - 210 - k * 36, y + 30 + 12 * math.sin(t * 2 - k * .25) + 10 * math.sin(t * 3 + k * .7)
        a = max(0, 1 - k / 18); glow(c, sx, sy, 18, (1, .9, .5), .5 * a)
        c.arc(sx, sy, 3, 0, 6.3); c.set_source_rgba(1, 1, 1, a); c.fill()
    r1, r2 = (x + 480, y - 40 + bob * .5), (x + 310, y - 24 + bob * .7)
    reindeer(c, *r1, t, 1, nose=True, moving=moving); reindeer(c, *r2, t, 0, moving=moving)
    c.save(); c.translate(x, y + bob); c.rotate(tilt); c.translate(-x, -y)
    # gift sack + presents
    c.set_line_width(4); c.move_to(x - 150, y - 70); c.curve_to(x - 170, y - 150, x - 80, y - 170, x - 60, y - 118); c.line_to(x - 74, y - 64); c.close_path(); shape(c, hx('#7A4A2E'), L)
    c.rectangle(x - 140, y - 128, 22, 20); shape(c, hx(GREEN), L); c.rectangle(x - 108, y - 150, 24, 22); shape(c, hx(GOLD), L)
    hip = (x - 10, y - 74)
    k = snap(t, 5.0, .9, 2.5); lift = math.sin(math.pi * k) if k >= 0 else 0
    hands = ((x + 52, hip[1] - 34 - 34 * lift), (x + 66, hip[1] - 30 - 34 * lift))
    pose(c, hip, t, outfit, ((x + 40, y - 30), (x + 56, y - 30)), hands, lean=.08, wind=1.0 * moving, **kw)
    c.restore()
    # reins from Haru's hands to the reindeer
    hy_ = y + bob + hands[1][1] - y
    c.set_line_width(3); c.set_source_rgb(*hx(GOLD))
    wv = 40 * math.sin(math.pi * k) * math.sin(k * 8) if k >= 0 else 0   # the wave running down the reins
    c.move_to(x + 66, hy_); c.curve_to(x + 160, hy_ + 30 - wv, x + 250, r2[1] - 10 + wv, r2[0] + 50, r2[1] - 12); c.stroke()
    if k > .4: crack(c, x + 210, (hy_ + r2[1]) / 2 + 10, (k - .4) / .6)
    c.move_to(r2[0] + 50, r2[1] - 12); c.curve_to(r2[0] + 110, r2[1], r1[0] - 60, r1[1] - 10, r1[0] + 50, r1[1] - 12); c.stroke()
    c.save(); c.translate(x, y + bob); c.rotate(tilt); c.translate(-x, -y)
    c.set_line_width(4)
    c.move_to(x - 160, y - 96); c.line_to(x + 90, y - 96); c.curve_to(x + 140, y - 96, x + 160, y - 156, x + 130, y - 166); c.curve_to(x + 176, y - 146, x + 176, y - 40, x + 110, y - 20)
    c.line_to(x - 150, y - 20); c.curve_to(x - 180, y - 20, x - 180, y - 96, x - 160, y - 96); c.close_path(); shape(c, hx('#C62E2E'), L)
    c.set_line_width(5); c.set_source_rgb(*hx(GOLD)); c.move_to(x - 150, y - 82); c.line_to(x + 100, y - 82); c.stroke()
    for k in range(5): c.arc(x - 116 + k * 50, y - 52, 7, 0, 6.3); c.set_line_width(3); shape(c, hx(GOLD), L)
    c.set_line_width(7); c.set_source_rgb(*hx(GOLD)); c.move_to(x - 180, y + 6); c.line_to(x + 124, y + 6); c.curve_to(x + 174, y + 6, x + 184, y - 30, x + 154, y - 40); c.stroke()
    c.set_line_width(2.5); c.set_source_rgb(*L); c.move_to(x - 180, y + 6); c.line_to(x + 124, y + 6); c.curve_to(x + 174, y + 6, x + 184, y - 30, x + 154, y - 40); c.stroke()
    for xx in (-120, 70): c.move_to(x + xx, y - 20); c.line_to(x + xx, y + 6); c.set_line_width(4); c.stroke()
    c.restore()
