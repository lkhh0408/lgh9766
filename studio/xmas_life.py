"""PLAY LIST 04: street life for the six Christmas neighbourhoods, so there is always something new passing by.
Each scene gets its own cast of small animated scenes on different scroll periods (they meet in new combinations)."""
import math, random
import cairo
import xmas as X
hx, shape, L, tone, rrect, glow, wrapx = X.hx, X.shape, X.L, X.tone, X.rrect, X.glow, X.wrapx
RED, GREEN, GOLD, CREAM, SNOW = X.RED, X.GREEN, X.GOLD, X.CREAM, X.SNOW
SKIN = (1, .88, .78)

def person(c, x, base, s, top, m, t, pose='walk', hair='#5A3B2E', hat=None, legs='#3E4A6B'):
    """a small passer-by (not Haru)"""
    c.save(); c.translate(x, base); c.scale(s, s); c.set_line_width(3)
    sw = math.sin(t * 6) * 6 if pose == 'walk' else 0
    c.set_line_width(5); c.set_source_rgb(*tone(legs, m)); c.move_to(0, -22); c.line_to(-4 + sw, 0); c.move_to(0, -22); c.line_to(4 - sw, 0); c.stroke()
    c.set_line_width(3); rrect(c, -11, -54, 22, 36, 9); shape(c, tone(top, m), L)
    c.arc(0, -64, 11, 0, 6.3); shape(c, tone(SKIN, m), L)
    c.arc(0, -67, 11.5, math.pi, 2 * math.pi); c.close_path(); shape(c, tone(hat or hair, m), L)
    if hat: c.arc(0, -80, 4, 0, 6.3); c.set_source_rgb(*tone(SNOW, m)); c.fill()
    c.arc(5, -64, 1.8, 0, 6.3); c.set_source_rgb(*L); c.fill()
    c.restore()

def couple(c, x, base, m, t):
    """two skaters holding hands"""
    for k, (col, hat) in enumerate(((RED, '#2E7D4F'), ('#2C3E66', RED))):
        person(c, x + k * 30, base + 4 * math.sin(t * 2 + k), 1.15, col, m, t, 'walk', hat=hat)
    c.set_line_width(4); c.set_source_rgb(*L); c.move_to(x + 8, base - 44); c.line_to(x + 22, base - 44); c.stroke()

def hockey(c, x, base, m, t):
    for k, col in enumerate(('#5BA8FF', GOLD)):
        px = x + k * 120 + 20 * math.sin(t * 1.5 + k * 2); person(c, px, base, 1.1, col, m, t, 'walk', hat=('#FFFFFF', RED)[k])
        c.set_line_width(4); c.set_source_rgb(*hx('#7A4A2E')); c.move_to(px + 8, base - 40); c.line_to(px + 30, base - 2); c.line_to(px + 44, base - 2); c.stroke()
    px = x + 60 + 50 * math.sin(t * 3); c.save(); c.translate(px, base); c.scale(1, .4); c.arc(0, 0, 7, 0, 6.3); c.restore(); c.set_source_rgb(*L); c.fill()

def ice_hut(c, x, base, m, t):
    c.set_line_width(4); c.rectangle(x - 50, base - 80, 100, 80); shape(c, tone('#C62E2E', m), L)
    c.move_to(x - 60, base - 80); c.line_to(x, base - 120); c.line_to(x + 60, base - 80); c.close_path(); shape(c, tone(SNOW, m), L)
    c.rectangle(x - 14, base - 50, 28, 50); shape(c, tone('#7A4A2E', m), L)
    c.rectangle(x + 40, base - 140, 12, 40); shape(c, tone('#3B3F5C', m), L)
    for j in range(4): yy = base - 150 - j * 20 - (t * 16) % 20; c.arc(x + 46 + 6 * math.sin(t + j), yy, 7 + j * 3, 0, 6.3); c.set_source_rgba(1, 1, 1, .4); c.fill()

def stand(c, x, base, m, t, label='HOT COCOA', col=RED):
    """little cart with a striped awning and steam"""
    c.set_line_width(4); rrect(c, x - 70, base - 90, 140, 70, 10); shape(c, tone(CREAM, m), L)
    for k in range(6): c.move_to(x - 76 + k * 26, base - 120); c.line_to(x - 63 + k * 26, base - 104); c.line_to(x - 50 + k * 26, base - 120); c.close_path(); shape(c, tone(col if k % 2 else SNOW, m), L)
    c.rectangle(x - 76, base - 136, 152, 18); shape(c, tone(col, m), L)
    c.select_font_face('Outfit', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(18); e = c.text_extents(label); c.move_to(x - e.width / 2, base - 60); c.set_source_rgb(*tone('#7A1E2A', m)); c.show_text(label)
    for wx in (x - 44, x + 44): c.arc(wx, base - 12, 12, 0, 6.3); shape(c, tone('#3B3F5C', m), L)
    for j in range(3):
        a = (t * .6 + j / 3) % 1; c.arc(x - 20 + j * 20 + 8 * math.sin(t * 2 + j), base - 96 - 50 * a, 6 + 8 * a, 0, 6.3); c.set_source_rgba(1, 1, 1, .5 * (1 - a)); c.fill()
    if X.SKY[m][3]: glow(c, x, base - 60, 90, (1, .85, .5), .3)

def dog_sweater(c, x, base, m, t, col=RED):
    b = math.sin(t * 10) * 2; c.save(); c.translate(x, base); c.set_line_width(3)
    rrect(c, -20, -24 + b, 38, 18, 9); shape(c, tone('#C68B59', m), L)
    rrect(c, -14, -26 + b, 24, 20, 6); shape(c, tone(col, m), L)
    c.arc(22, -28 + b, 10, 0, 6.3); shape(c, tone('#C68B59', m), L); c.arc(26, -30 + b, 2, 0, 6.3); c.set_source_rgb(*L); c.fill()
    c.set_source_rgb(*L)
    for dx in (-14, 10): c.move_to(dx, -8 + b); c.line_to(dx + math.sin(t * 12 + dx) * 5, 0); c.stroke()
    c.move_to(-20, -20 + b); c.line_to(-28, -30 + b + 4 * math.sin(t * 14)); c.stroke()
    c.restore()

def shopper(c, x, base, m, t, col='#7B1E3A'):
    person(c, x, base, 1.2, col, m, t, 'walk', hat=GREEN)
    for k, bc in enumerate((GOLD, RED)):
        c.set_line_width(3); c.rectangle(x - 26 + k * 40, base - 42 + 2 * math.sin(t * 6 + k), 20, 22); shape(c, tone(bc, m), L)

def balloon_kid(c, x, base, m, t):
    person(c, x, base, 1.0, '#5BA8FF', m, t, 'walk', hat=RED)
    by = base - 140 + 8 * math.sin(t * 1.5); bx = x + 20 + 6 * math.sin(t)
    c.set_line_width(1.5); c.set_source_rgb(*L); c.move_to(x + 8, base - 40); c.curve_to(x + 14, base - 80, bx, by + 50, bx, by + 30); c.stroke()
    c.set_line_width(3); c.save(); c.translate(bx, by); c.scale(1, 1.2); c.arc(0, 0, 24, 0, 6.3); c.restore(); shape(c, tone(RED, m), L)
    c.arc(bx - 8, by - 10, 5, 0, 6.3); c.set_source_rgba(1, 1, 1, .6); c.fill()

def violinist(c, x, base, m, t):
    person(c, x, base, 1.25, '#2C3E66', m, t, 'stand', hat=RED)
    c.set_line_width(3); c.save(); c.translate(x + 12, base - 66); c.rotate(-.5); rrect(c, -6, -14, 26, 14, 6); shape(c, tone('#B5651D', m), L); c.restore()
    c.set_line_width(2); c.set_source_rgb(*L); a = .3 * math.sin(t * 6); c.move_to(x - 10 + 10 * a, base - 50); c.line_to(x + 40 + 10 * a, base - 86); c.stroke()
    c.set_line_width(3); rrect(c, x - 40, base - 14, 34, 14, 4); shape(c, tone('#7A4A2E', m), L)
    for k in range(3):
        u = (t * .5 + k / 3) % 1; nx, ny = x + 30 + 40 * u, base - 110 - 60 * u
        c.set_source_rgba(*L, 1 - u); c.arc(nx, ny, 5, 0, 6.3); c.fill(); c.set_line_width(2.5); c.move_to(nx + 5, ny); c.line_to(nx + 5, ny - 16); c.stroke()

def tree_lot(c, x, base, m, t):
    for k in range(5): X.pine(c, x + k * 46, base, .55 + (k % 2) * .1, m, t, lights=False)
    c.set_line_width(3); rrect(c, x - 30, base - 140, 120, 34, 6); shape(c, tone(GREEN, m), L)
    c.select_font_face('Outfit', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(20); c.move_to(x - 18, base - 116); c.set_source_rgb(1, 1, 1); c.show_text('TREES $25')
    c.set_line_width(4); c.set_source_rgb(*L); c.move_to(x + 30, base - 106); c.line_to(x + 30, base); c.stroke()

def snowball_fight(c, x, base, m, t):
    person(c, x, base, 1.1, RED, m, t, 'stand', hat=GOLD); person(c, x + 200, base, 1.1, '#5BA8FF', m, t, 'stand', hat=GREEN)
    for k in range(2):
        u = ((t * .7 + k * .5) % 1); sx = x + 10 + 180 * u if k == 0 else x + 190 - 180 * u
        c.arc(sx, base - 70 - 70 * 4 * u * (1 - u), 7, 0, 6.3); c.set_line_width(2.5); shape(c, tone(SNOW, m), L)
        if u > .92:
            for j in range(5): a = j * 1.25; c.arc(sx + 12 * math.cos(a), base - 70 + 12 * math.sin(a), 3, 0, 6.3); c.set_source_rgba(1, 1, 1, .9); c.fill()

def snow_angel(c, x, base, m, t):
    f = .5 + .5 * math.sin(t * 3)
    c.save(); c.translate(x, base - 8); c.scale(1, .45)
    c.set_source_rgba(.75, .82, .95, .7); c.move_to(-50, 0)
    for k in range(2):
        d = 1 - 2 * k; c.move_to(0, 0); c.line_to(d * 70, -30 - 30 * f); c.line_to(d * 40, 30); c.close_path(); c.fill()
    c.restore()
    c.set_line_width(3); rrect(c, x - 34, base - 18, 52, 16, 8); shape(c, tone(GREEN, m), L)
    c.arc(x + 28, base - 12, 10, 0, 6.3); shape(c, tone(SKIN, m), L)
    c.set_line_width(5); c.set_source_rgb(*tone(GREEN, m))
    for d in (-1, 1): c.move_to(x - 6, base - 12); c.line_to(x - 6 + 24 * math.cos(1.2 * f), base - 12 + d * 24 * math.sin(1.2 * f)); c.stroke()

def snowball_roll(c, x, base, m, t):
    r = 30 + 6 * math.sin(t * .4); person(c, x - 50, base, 1.1, '#FF9FC2', m, t, 'walk', hat='#5BA8FF')
    c.arc(x + 10, base - r, r, 0, 6.3); c.set_line_width(3.5); shape(c, tone(SNOW, m), L)
    c.set_line_width(2); c.set_source_rgba(.7, .78, .9, .8); c.arc(x + 10, base - r, r * .6, t * 2, t * 2 + 1.5); c.stroke()

def ice_sculpture(c, x, base, m, t):
    c.set_line_width(3); rrect(c, x - 50, base - 30, 100, 30, 6); shape(c, tone('#D8EEFA', m), L)
    c.move_to(x - 40, base - 30); c.curve_to(x - 50, base - 90, x + 10, base - 100, x + 30, base - 60); c.curve_to(x + 20, base - 120, x + 50, base - 150, x + 60, base - 120)
    c.curve_to(x + 70, base - 100, x + 50, base - 40, x + 40, base - 30); c.close_path(); c.set_source_rgba(.8, .93, 1, .85); c.fill_preserve(); c.set_source_rgb(*L); c.stroke()
    if int(t * 2) % 3 == 0: c.arc(x + 20, base - 80, 4, 0, 6.3); c.set_source_rgb(1, 1, 1); c.fill()

def gazebo(c, x, base, m, t):
    c.set_line_width(4)
    for dx in (-90, -30, 30, 90): c.move_to(x + dx, base); c.line_to(x + dx, base - 140); c.set_source_rgb(*L); c.stroke()
    c.rectangle(x - 110, base - 20, 220, 20); shape(c, tone('#E8DCCB', m), L)
    c.move_to(x - 120, base - 140); c.line_to(x, base - 220); c.line_to(x + 120, base - 140); c.close_path(); shape(c, tone(GREEN, m), L)
    X.snowy_roof(c, [(x - 124, base - 138), (x, base - 224), (x + 124, base - 138), (x + 112, base - 134), (x, base - 208), (x - 112, base - 134)], m)
    X.bulbs(c, x - 120, base - 140, x + 120, base - 140, 30, m, t, 12)

def firepit(c, x, base, m, t):
    c.set_line_width(3); rrect(c, x - 40, base - 20, 80, 20, 6); shape(c, tone('#6B5B4B', m), L)
    for k in range(4):
        fl = 30 + 12 * math.sin(t * 9 + k * 2); c.move_to(x - 24 + k * 16, base - 20); c.curve_to(x - 34 + k * 16, base - 20 - fl * .6, x - 20 + k * 16, base - 20 - fl, x - 16 + k * 16, base - 20 - fl)
        c.curve_to(x - 10 + k * 16, base - 20 - fl * .6, x - 8 + k * 16, base - 30, x - 14 + k * 16, base - 20); c.set_source_rgb(1, .6 + .2 * (k % 2), .2); c.fill()
    glow(c, x, base - 30, 120, (1, .6, .3), .35 + .08 * math.sin(t * 9))
    for k, col in enumerate(('#2C3E66', '#7B1E3A')):
        px = x - 90 + k * 180; person(c, px, base, 1.15, col, m, t, 'stand', hat=(RED, GOLD)[k])
        c.set_line_width(2.5); c.set_source_rgb(*hx('#7A4A2E')); d = 1 - 2 * k; c.move_to(px + 8 * d, base - 46); c.line_to(x - 10 * d, base - 48); c.stroke()
        c.arc(x - 12 * d, base - 48, 5, 0, 6.3); shape(c, (1, 1, 1), L)

def puppet_stage(c, x, base, m, t):
    c.set_line_width(4); c.rectangle(x - 70, base - 170, 140, 170); shape(c, tone('#7B1E3A', m), L)
    c.rectangle(x - 50, base - 140, 100, 60); shape(c, tone('#2B2541', m), L)
    for d in (-1, 1): c.move_to(x + 50 * d, base - 140); c.curve_to(x + 30 * d, base - 120, x + 40 * d, base - 90, x + 50 * d, base - 80); c.line_to(x + 50 * d, base - 140); shape(c, tone(RED, m), L)
    py = base - 88 - 14 * abs(math.sin(t * 3))
    c.arc(x, py - 20, 14, 0, 6.3); shape(c, tone(SKIN, m), L); c.move_to(x - 14, py - 28); c.line_to(x, py - 56); c.line_to(x + 14, py - 28); c.close_path(); shape(c, tone(RED, m), L)
    for k in range(3): person(c, x - 60 + k * 60, base + 60, 1.0, ('#5BA8FF', GOLD, GREEN)[k], m, t, 'stand', hat=RED)

def shoveler(c, x, base, m, t):
    u = (t * .8) % 1; person(c, x, base, 1.2, '#2E7D4F', m, t, 'stand', hat='#5BA8FF')
    ang = -.6 + 1.1 * math.sin(u * math.pi)
    c.set_line_width(4); c.set_source_rgb(*hx('#7A4A2E')); c.move_to(x + 6, base - 50); ex, ey = x + 6 + 46 * math.cos(ang), base - 50 + 46 * math.sin(ang) + 30; c.line_to(ex, ey); c.stroke()
    c.rectangle(ex - 6, ey - 4, 22, 12); shape(c, tone('#C9CCD8', m), L)
    if u > .5:
        for j in range(6): a = (u - .5) * 2; c.arc(ex + 30 * a + j * 6, ey - 50 * a + j * 4 + 40 * a * a, 4, 0, 6.3); c.set_source_rgba(1, 1, 1, .9 * (1 - a)); c.fill()

def porch_cat(c, x, base, m, t):
    c.set_line_width(3); c.save(); c.translate(x, base); c.scale(1, 1)
    c.arc(0, -16, 16, 0, 6.3); shape(c, tone('#3B3F5C', m), L); c.arc(10, -34, 11, 0, 6.3); shape(c, tone('#3B3F5C', m), L)
    for d in (-1, 1): c.move_to(10 + 6 * d, -42); c.line_to(10 + 9 * d, -54); c.line_to(10 + 2 * d, -44); c.close_path(); shape(c, tone('#3B3F5C', m), L)
    c.arc(14, -36, 2, 0, 6.3); c.set_source_rgb(1, .9, .3); c.fill()
    c.set_line_width(4); c.set_source_rgb(*tone('#3B3F5C', m)); c.move_to(-14, -10); c.curve_to(-34, -14, -30, -30 + 6 * math.sin(t * 3), -24, -36 + 6 * math.sin(t * 3)); c.stroke()
    c.restore()

def packages(c, x, base, m, t):
    for k, (w_, h_, col, rib) in enumerate(((40, 30, RED, GOLD), (30, 26, GREEN, RED), (34, 22, '#5BA8FF', SNOW))):
        c.set_line_width(3); c.rectangle(x + k * 38, base - h_, w_, h_); shape(c, tone(col, m), L); c.rectangle(x + k * 38 + w_ / 2 - 3, base - h_, 6, h_); shape(c, tone(rib, m), L)

def landmark_tower(c, x, base, m, t):
    c.set_line_width(3); c.rectangle(x - 24, base - 160, 48, 160); shape(c, hx('#4A5285'), L)
    c.move_to(x - 30, base - 160); c.line_to(x, base - 210); c.line_to(x + 30, base - 160); c.close_path(); shape(c, hx('#2F7D55'), L)
    c.arc(x, base - 128, 14, 0, 6.3); glow(c, x, base - 128, 40, (1, .9, .6), .5); c.arc(x, base - 128, 14, 0, 6.3); shape(c, hx('#FFE9A8'), L)

def landmark_wheel(c, x, base, m, t):
    c.set_line_width(3); c.set_source_rgb(*L)
    for a in range(10): aa = a * .628 + t * .1; c.move_to(x, base - 120); c.line_to(x + 90 * math.cos(aa), base - 120 + 90 * math.sin(aa)); c.stroke()
    for a in range(10):
        aa = a * .628 + t * .1; px, py = x + 90 * math.cos(aa), base - 120 + 90 * math.sin(aa); col = hx((RED, GOLD, GREEN, '#5BA8FF')[a % 4])
        glow(c, px, py, 16, col, .6); c.arc(px, py, 5, 0, 6.3); c.set_source_rgb(*col); c.fill()

def firework(c, t, x, y, period=5.0, seed=0, col=(1, .85, .4)):
    u = ((t + seed * 1.7) % period) / period
    if u > .35: return
    k = u / .35
    if k < .3:
        c.arc(x, y + 200 * (1 - k / .3), 3, 0, 6.3); c.set_source_rgba(1, 1, 1, .9); c.fill(); return
    e = (k - .3) / .7
    for j in range(16):
        a = j * math.pi / 8; r_ = 90 * e
        glow(c, x + r_ * math.cos(a), y + r_ * math.sin(a) + 30 * e * e, 12, col, .6 * (1 - e))
        c.arc(x + r_ * math.cos(a), y + r_ * math.sin(a) + 30 * e * e, 3, 0, 6.3); c.set_source_rgba(*col, 1 - e); c.fill()

def birds(c, t, scroll, y, n=5, seed=0):
    for k in range(n):
        x = wrapx(k * 70 + seed * 400, scroll, .15 - 0.02, 2400) + (t * 40) % 2400 * 0; yy = y + 14 * math.sin(k) + 4 * math.sin(t * 6 + k)
        f = 6 * math.sin(t * 8 + k); c.set_line_width(2.5); c.set_source_rgb(*L)
        c.move_to(x - 10, yy - f); c.line_to(x, yy); c.line_to(x + 10, yy - f); c.stroke()

# --- the cast of each neighbourhood: (draw function, base x, parallax, period, ground y) ---
CAST = {
    'canal':    [(couple, 200, .95, 2600, 860), (hockey, 1200, .95, 3400, 900), (ice_hut, 1800, .9, 3900, 840), (stand, 700, .9, 4300, 860), (dog_sweater, 1400, .95, 2900, 905)],
    'downtown': [(shopper, 300, .9, 2500, 780), (balloon_kid, 900, .9, 3100, 785), (violinist, 1500, .9, 3700, 790), (tree_lot, 2200, .9, 4100, 780), (dog_sweater, 600, .9, 2700, 790), (stand, 1900, .9, 4700, 785)],
    'park':     [(snowball_fight, 200, .9, 3200, 920), (snow_angel, 1300, .9, 2900, 940), (snowball_roll, 800, .9, 3500, 925), (ice_sculpture, 1700, .85, 4100, 900), (gazebo, 2400, .55, 3800, 700)],
    'market':   [(firepit, 400, .9, 3000, 840), (puppet_stage, 1500, .75, 3800, 760), (stand, 2100, .9, 3400, 850), (shopper, 900, .9, 2600, 860), (balloon_kid, 1700, .9, 3100, 870)],
    'lane':     [(shoveler, 500, .9, 2800, 850), (porch_cat, 1300, .8, 2400, 800), (packages, 900, .8, 2600, 800), (dog_sweater, 1800, .9, 3000, 860), (couple, 2300, .9, 3600, 860)],
    'sky':      [(landmark_tower, 600, .3, 3000, 820), (landmark_wheel, 1600, .3, 3600, 820)],
}

def life(c, scene, m, scroll, t):
    for fn, bx, f, period, gy in CAST.get(scene, ()):
        x = wrapx(bx, scroll, f, period)
        if -300 < x < X.W + 300: fn(c, x, gy, m, t)
    if scene in ('park', 'canal', 'downtown'): birds(c, t, scroll, 160, 5, {'park': 0, 'canal': 1, 'downtown': 2}[scene])
    if scene == 'sky':
        for k, (fx, fy, col) in enumerate(((400, 380, (1, .85, .4)), (1300, 330, (1, .5, .6)), (1700, 420, (.5, .85, 1)))):
            firework(c, t, fx, fy, 6.0, k, col)
    if scene == 'lane':
        firework(c, t, 1500, 260, 9.0, 1, (1, .8, .4))
