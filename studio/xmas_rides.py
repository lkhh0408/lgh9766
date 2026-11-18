"""PLAY LIST 04 rides: skates, Christmas tram, snow sled, bell carriage, reindeer sky sleigh.
Haru is the regular character (studio/character.py); for seated rides the vehicle's side panel is drawn over her legs."""
import math
import cairo
import character as ch
from mobility import mob
hx, lerp, shape = mob.hexc, mob.lerp, mob._shape
L = hx('#2B2541')
RED, GREEN, GOLD, CREAM = '#D94040', '#2E8B57', '#F2C230', '#FFF6E0'

def rrect(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()

def glow(c, x, y, r, col=(1, .86, .5), a=.55):
    g = cairo.RadialGradient(x, y, 0, x, y, r); g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    c.set_source(g); c.arc(x, y, r, 0, 6.3); c.fill()

def haru(c, x, gy, t, outfit, walk=0.0, phase=0.0, scale=1.0, **kw):
    c.save(); c.translate(x, gy); c.scale(scale, scale); hd = ch.draw(c, 0, 0, t, outfit=outfit, walk=walk, phase=phase, **kw); c.restore(); return hd

def light_string(c, x0, x1, y, t, lit, n=10):
    c.set_line_width(2); c.set_source_rgb(*L); c.move_to(x0, y); c.line_to(x1, y); c.stroke()
    for k in range(n):
        x = x0 + (x1 - x0) * (k + .5) / n; col = hx((RED, GOLD, GREEN, '#5BA8FF')[k % 4])
        if lit: glow(c, x, y + 5, 14, col, .5 + .2 * math.sin(t * 4 + k))
        c.arc(x, y + 5, 4.5, 0, 6.3); shape(c, col, L)

def skate(c, x, gy, t, outfit, moving=1.0, **kw):
    """gliding on ice: a slow stride with skate blades"""
    o = dict(ch.OUTFITS[outfit], skates=True); ch.OUTFITS['_skate'] = o
    ph = t * 2 * math.pi * .45
    c.save(); c.translate(x, gy); c.rotate(.04 * math.sin(ph) * moving); ch.draw(c, 0, -12, t, outfit='_skate', walk=.75 * moving, phase=ph, **kw); c.restore()
    c.set_line_width(2.5); c.set_source_rgba(1, 1, 1, .8)
    for k in range(int(3 * moving + .5)): c.move_to(x - 40 - k * 60, gy + 2 + k * 3); c.line_to(x - 90 - k * 60, gy + 3 + k * 3); c.stroke()

def tram(c, x, gy, t, outfit, lit=False, moving=1.0, **kw):
    """red Christmas tram; Haru stands at the second window"""
    w, h, y0 = 560, 220, gy - 250
    c.set_line_width(4)
    c.move_to(x - 160, y0 - 14); c.line_to(x - 120, y0 - 70); c.line_to(x - 40, y0 - 70); c.stroke()   # pantograph
    rrect(c, x - w / 2, y0, w, h, 34); shape(c, hx('#C62E2E'), L)
    rrect(c, x - w / 2 + 6, y0 + 150, w - 12, 34, 10); shape(c, hx(CREAM), L)
    rrect(c, x - w / 2 + 20, y0 - 22, w - 40, 28, 12); shape(c, hx('#A82424'), L)
    light_string(c, x - w / 2 + 30, x + w / 2 - 30, y0 - 26, t, lit, 14)
    wins = [x - 240 + k * 120 for k in range(4)]
    for i, wx in enumerate(wins):
        rrect(c, wx, y0 + 30, 96, 100, 14); shape(c, hx('#FFE9A8') if lit else hx('#D6EEFF'), L)
        if i == 1:
            c.save(); rrect(c, wx, y0 + 30, 96, 100, 14); c.clip()
            haru(c, wx + 46, y0 + 240, t, outfit, scale=.8, **kw); c.restore()
            c.set_line_width(4); rrect(c, wx, y0 + 30, 96, 100, 14); c.set_source_rgb(*L); c.stroke()
        elif i == 3:
            c.set_line_width(7); c.set_source_rgb(*hx(GREEN)); c.arc(wx + 48, y0 + 80, 26, 0, 6.3); c.stroke()
            c.move_to(wx + 38, y0 + 106); c.line_to(wx + 58, y0 + 106); c.line_to(wx + 48, y0 + 92); c.close_path(); shape(c, hx(RED), L)
    rrect(c, x + w / 2 - 14, y0 + 40, 10, 24, 4); shape(c, hx('#FFE27A'), L)
    if lit: glow(c, x + w / 2, y0 + 52, 60, (1, .9, .6), .5)
    for wx in (x - 170, x + 170):
        c.arc(wx, gy - 18, 22, 0, 6.3); shape(c, hx('#3B3F5C'), L); c.arc(wx, gy - 18, 8, 0, 6.3); shape(c, hx('#C9CCD8'), L)
    c.set_line_width(3); c.set_source_rgb(*L); c.move_to(x - w / 2 + 40, y0 + 170); c.select_font_face('Outfit', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(22); c.show_text('NO. 25  CHRISTMAS LINE')

def sled(c, x, gy, t, outfit, tilt=0.0, moving=1.0, **kw):
    """wooden toboggan sliding downhill; tilt in radians"""
    c.save(); c.translate(x, gy); c.rotate(tilt)
    c.save(); c.rectangle(-400, -600, 800, 572); c.clip(); haru(c, -10, 56, t, outfit, scale=1.0, **kw); c.restore()   # sitting: legs hidden in the sled
    c.set_line_width(4)
    c.move_to(-110, -40); c.line_to(90, -40); c.curve_to(150, -40, 150, -110, 110, -100); c.curve_to(130, -70, 120, -10, 90, -10); c.line_to(-110, -10); c.close_path()
    shape(c, hx('#C98F6A'), L)
    for k in range(5): c.move_to(-100 + k * 40, -38); c.line_to(-100 + k * 40, -12); c.set_source_rgb(*L); c.set_line_width(2); c.stroke()
    c.set_line_width(4); c.move_to(-120, 6); c.line_to(100, 6); c.curve_to(140, 6, 150, -30, 120, -40); c.set_source_rgb(*L); c.stroke()
    for xx in (-80, 40): c.move_to(xx, -10); c.line_to(xx, 6); c.stroke()
    c.move_to(110, -96); c.line_to(150, -110); c.set_line_width(3); c.stroke()
    c.restore()
    c.set_line_width(3)
    for k in range(int(6 * moving + .5)):
        c.arc(x - 140 - k * 34, gy + 4 - 10 * math.sin(t * 12 + k), 6 + k, 0, 6.3); c.set_source_rgba(1, 1, 1, .8 - k * .1); c.fill()

def horse(c, x, gy, t, col='#F4F1EC', moving=1.0):
    ph = t * 2 * math.pi * 1.1 * moving; c.set_line_width(4)
    for k, dx in enumerate((-60, -40, 40, 60)):
        a = .35 * math.sin(ph + k * math.pi / 2) * moving
        c.set_line_width(12); c.set_source_rgb(*L); c.move_to(x + dx, gy - 80); c.line_to(x + dx + 40 * math.sin(a), gy - 4); c.stroke()
        c.set_line_width(7); c.set_source_rgb(*hx(col)); c.move_to(x + dx, gy - 80); c.line_to(x + dx + 40 * math.sin(a), gy - 4); c.stroke()
    c.set_line_width(4); c.save(); c.translate(x, gy - 110); c.scale(1, .55); c.arc(0, 0, 90, 0, 6.3); c.restore(); shape(c, hx(col), L)
    c.move_to(x + 60, gy - 120); c.line_to(x + 110, gy - 190); c.line_to(x + 150, gy - 170); c.line_to(x + 96, gy - 108); c.close_path(); shape(c, hx(col), L)
    c.save(); c.translate(x + 150, gy - 172); c.rotate(.5); c.scale(1.6, 1); c.arc(0, 0, 18, 0, 6.3); c.restore(); shape(c, hx(col), L)
    c.arc(x + 146, gy - 186, 4, 0, 6.3); c.set_source_rgb(*L); c.fill()
    c.move_to(x + 112, gy - 196); c.line_to(x + 120, gy - 214); c.line_to(x + 126, gy - 194); c.close_path(); shape(c, hx(col), L)
    c.move_to(x + 106, gy - 186); c.curve_to(x + 80, gy - 170, x + 70, gy - 140, x + 64, gy - 124); c.set_line_width(10); c.set_source_rgb(*hx('#B08968')); c.stroke()
    c.set_line_width(4); c.move_to(x - 88, gy - 120); c.curve_to(x - 120, gy - 110, x - 120, gy - 70, x - 104, gy - 50); c.set_source_rgb(*hx('#B08968')); c.set_line_width(9); c.stroke()
    c.set_line_width(6); c.set_source_rgb(*hx(RED)); c.move_to(x + 70, gy - 150); c.line_to(x + 30, gy - 100); c.stroke()
    for k in range(4):
        bx, by = x + 66 - k * 12, gy - 146 + k * 14; c.arc(bx, by, 6, 0, 6.3); shape(c, hx(GOLD), L)

def carriage(c, x, gy, t, outfit, lit=False, moving=1.0, **kw):
    """open red carriage with gold trim pulled by a white horse with jingle bells"""
    horse(c, x + 330, gy, t, moving=moving)
    c.set_line_width(5); c.set_source_rgb(*L); c.move_to(x + 130, gy - 110); c.line_to(x + 270, gy - 110); c.stroke()
    c.save(); c.rectangle(x - 400, 0, 800, gy - 70); c.clip(); haru(c, x - 10, gy - 40, t, outfit, scale=1.0, **kw); c.restore()
    c.set_line_width(4)
    c.move_to(x - 150, gy - 160); c.line_to(x + 120, gy - 160); c.curve_to(x + 160, gy - 160, x + 160, gy - 60, x + 120, gy - 60); c.line_to(x - 140, gy - 60); c.curve_to(x - 170, gy - 60, x - 180, gy - 160, x - 150, gy - 160); c.close_path()
    shape(c, hx('#B3263A'), L)
    c.set_line_width(5); c.set_source_rgb(*hx(GOLD)); c.move_to(x - 140, gy - 146); c.line_to(x + 118, gy - 146); c.stroke()
    c.arc(x - 10, gy - 112, 22, 0, 6.3); c.set_line_width(4); shape(c, hx(GOLD), L)
    c.set_line_width(6); c.set_source_rgb(*hx(GREEN)); c.arc(x - 10, gy - 112, 14, 0, 6.3); c.stroke()
    c.move_to(x - 160, gy - 160); c.line_to(x - 160, gy - 230); c.set_line_width(4); c.set_source_rgb(*L); c.stroke()
    rrect(c, x - 172, gy - 262, 24, 34, 6); shape(c, hx('#FFE27A') if lit else hx(CREAM), L)
    if lit: glow(c, x - 160, gy - 245, 70, (1, .85, .5), .55)
    for wx, r in ((x - 110, 50), (x + 90, 40)):
        c.arc(wx, gy - r, r, 0, 6.3); c.set_line_width(5); shape(c, hx(GOLD), L)
        c.set_line_width(3); c.set_source_rgb(*L)
        for k in range(8): a = k * math.pi / 4 + t * 3 * moving; c.move_to(wx, gy - r); c.line_to(wx + r * math.cos(a), gy - r + r * math.sin(a)); c.stroke()
        c.arc(wx, gy - r, 8, 0, 6.3); shape(c, hx('#B3263A'), L)

def reindeer(c, x, y, t, k=0, nose=False):
    ph = t * 2 * math.pi * 1.4 + k; col = hx('#A0703F'); c.set_line_width(4)
    for j, dx in enumerate((-36, -20, 26, 42)):
        a = .6 * math.sin(ph + j * math.pi / 2)
        c.set_line_width(10); c.set_source_rgb(*L); c.move_to(x + dx, y + 20); c.line_to(x + dx + 30 * math.sin(a), y + 64); c.stroke()
        c.set_line_width(6); c.set_source_rgb(*col); c.move_to(x + dx, y + 20); c.line_to(x + dx + 30 * math.sin(a), y + 64); c.stroke()
    c.set_line_width(4); c.save(); c.translate(x, y); c.scale(1, .55); c.arc(0, 0, 60, 0, 6.3); c.restore(); shape(c, col, L)
    c.move_to(x + 40, y - 10); c.line_to(x + 70, y - 60); c.line_to(x + 96, y - 46); c.line_to(x + 60, y + 6); c.close_path(); shape(c, col, L)
    c.save(); c.translate(x + 96, y - 52); c.rotate(.4); c.scale(1.5, 1); c.arc(0, 0, 15, 0, 6.3); c.restore(); shape(c, col, L)
    for lean in (-1, 1):
        for w_, cc in ((7, L), (4, hx('#E8D3B0'))):
            c.set_line_width(w_); c.set_source_rgb(*cc)
            c.move_to(x + 82 + 6 * lean, y - 64); c.line_to(x + 76 + 16 * lean, y - 100); c.stroke()
            c.move_to(x + 79 + 10 * lean, y - 84); c.line_to(x + 92 + 18 * lean, y - 92); c.stroke()
    c.arc(x + 92, y - 66, 3.5, 0, 6.3); c.set_source_rgb(*L); c.fill()
    if nose: glow(c, x + 118, y - 44, 40, (1, .25, .25), .7)
    c.arc(x + 118, y - 44, 8, 0, 6.3); shape(c, hx('#FF3B3B') if nose else hx('#5A3B2E'), L)
    c.set_line_width(6); c.set_source_rgb(*hx(RED)); c.move_to(x + 40, y - 12); c.line_to(x + 56, y + 10); c.stroke()
    c.arc(x + 50, y + 4, 6, 0, 6.3); c.set_line_width(3); shape(c, hx(GOLD), L)

def sky_sleigh(c, x, y, t, outfit, moving=1.0, **kw):
    """flying sleigh: two reindeer in front, gift sack behind, trail of sparkles"""
    bob = 10 * math.sin(t * 2)
    for k in range(14):
        sx, sy = x - 200 - k * 40, y + 40 + bob + 12 * math.sin(t * 3 + k * .7)
        a = max(0, 1 - k / 14); glow(c, sx, sy, 16, (1, .9, .5), .5 * a)
        c.arc(sx, sy, 3, 0, 6.3); c.set_source_rgba(1, 1, 1, a); c.fill()
    reindeer(c, x + 470, y - 20 + bob * .6, t, 1, nose=True); reindeer(c, x + 300, y - 10 + bob * .8, t, 0)
    c.set_line_width(4); c.set_source_rgb(*hx(GOLD)); c.move_to(x + 140, y - 10 + bob); c.line_to(x + 300, y - 20 + bob); c.line_to(x + 470, y - 30 + bob); c.stroke()
    c.save(); c.translate(0, bob)
    c.move_to(x - 130, y - 70); c.curve_to(x - 150, y - 140, x - 60, y - 160, x - 40, y - 110); c.line_to(x - 60, y - 60); c.close_path(); shape(c, hx('#7A4A2E'), L)
    c.rectangle(x - 120, y - 120, 18, 16); shape(c, hx(GREEN), L); c.rectangle(x - 90, y - 140, 20, 18); shape(c, hx(GOLD), L)
    haru(c, x, y + 20, t, outfit, scale=1.0, **kw)
    c.set_line_width(4)
    c.move_to(x - 150, y - 90); c.line_to(x + 90, y - 90); c.curve_to(x + 140, y - 90, x + 160, y - 150, x + 130, y - 160); c.curve_to(x + 170, y - 140, x + 170, y - 40, x + 110, y - 20)
    c.line_to(x - 140, y - 20); c.curve_to(x - 170, y - 20, x - 170, y - 90, x - 150, y - 90); c.close_path(); shape(c, hx('#C62E2E'), L)
    c.set_line_width(5); c.set_source_rgb(*hx(GOLD)); c.move_to(x - 140, y - 76); c.line_to(x + 100, y - 76); c.stroke()
    for k in range(5): c.arc(x - 110 + k * 50, y - 48, 7, 0, 6.3); c.set_line_width(3); shape(c, hx(GOLD), L)
    c.set_line_width(6); c.set_source_rgb(*hx(GOLD)); c.move_to(x - 170, y + 6); c.line_to(x + 120, y + 6); c.curve_to(x + 170, y + 6, x + 180, y - 30, x + 150, y - 40); c.stroke()
    c.set_line_width(3); c.set_source_rgb(*L); c.move_to(x - 170, y + 6); c.line_to(x + 120, y + 6); c.curve_to(x + 170, y + 6, x + 180, y - 30, x + 150, y - 40); c.stroke()
    for xx in (-110, 60): c.move_to(x + xx, y - 20); c.line_to(x + xx, y + 6); c.stroke()
    c.restore()
