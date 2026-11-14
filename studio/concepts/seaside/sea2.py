"""PLAY LIST 03 draft v2: richer seaside road (layers: sky, far coast village, sea, beach, promenade, road)."""
import math, random, sys
import cairo
sys.path.insert(0, '/home/user/lgh9766/studio'); sys.path.insert(0, '/home/user/lgh9766/studio/mobility')
import mob
from sea import OPTS, haru_bike, GY, W, H
hx, lerp, shape = mob.hexc, mob.lerp, mob._shape
L = hx('#2B2541')
PAL = ['#FF7A6B', '#FFC857', '#7ED6C4', '#8FB8FF', '#C9A7FF', '#FF9FC2', '#9BD3A0', '#FFFFFF']
SK = {'day': dict(sky=('#78C4FF', '#E6F6FF'), sea=('#3FA9E0', '#9EDCF5'), dim=0.0),
      'dusk': dict(sky=('#6457B8', '#FFB08A'), sea=('#5B6FC0', '#F4A88E'), dim=0.25),
      'night': dict(sky=('#111735', '#352C62'), sea=('#1B2650', '#2F3F72'), dim=0.62)}

def tone(col, m):   # darken toward the night palette
    return lerp(hx(col) if isinstance(col, str) else col, hx('#2A2850'), SK[m]['dim'])
def rrect(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()
def tx(c, s, x, y, size, col=L):
    c.select_font_face('Outfit', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size); c.set_source_rgb(*col); c.move_to(x, y); c.show_text(s)
def wrapx(base, scroll, f, period):
    return (base - scroll * f) % period - 300

def person(c, x, y, s, top, m, pose='stand', t=0.0, hair='#5A3B2E'):
    """tiny generic beach-goer (not Haru): pose stand/walk/lie/sit"""
    c.save(); c.translate(x, y); c.scale(s, s); c.set_line_width(3)
    skin = tone((1, .88, .78), m)
    if pose == 'lie':
        rrect(c, -30, -14, 46, 14, 7); shape(c, tone(top, m), L); c.arc(24, -9, 9, 0, 6.3); shape(c, skin, L)
    else:
        sw = math.sin(t * 6) * 6 if pose == 'walk' else 0
        c.set_line_width(5); c.set_source_rgb(*tone('#3E4A6B', m))
        if pose == 'sit':
            c.move_to(0, -18); c.line_to(14, -18); c.line_to(14, 0); c.stroke()
        else:
            c.move_to(0, -22); c.line_to(-4 + sw, 0); c.move_to(0, -22); c.line_to(4 - sw, 0); c.stroke()
        c.set_line_width(3); rrect(c, -9, -50, 18, 32, 8); shape(c, tone(top, m), L)
        c.arc(0, -60, 10, 0, 6.3); shape(c, skin, L)
        c.arc(0, -63, 10, math.pi, 2 * math.pi); c.set_source_rgb(*tone(hair, m)); c.fill()
    c.restore()

def dog(c, x, y, s, col, m, t):
    c.save(); c.translate(x, y); c.scale(s, s); c.set_line_width(3)
    b = math.sin(t * 10) * 2
    rrect(c, -18, -22 + b, 34, 16, 8); shape(c, tone(col, m), L)
    c.arc(20, -26 + b, 9, 0, 6.3); shape(c, tone(col, m), L)
    c.set_source_rgb(*L)
    for dx in (-12, 8): c.move_to(dx, -8 + b); c.line_to(dx + math.sin(t * 12 + dx) * 4, 0); c.stroke()
    c.move_to(-18, -18 + b); c.line_to(-26, -26 + b); c.stroke()
    c.restore()

def scene(c, m, scroll=0.0, t=1.0):
    night = m == 'night'; dusk = m == 'dusk'
    s0, s1 = SK[m]['sky']
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgb(0, *hx(s0)); g.add_color_stop_rgb(1, *hx(s1)); c.rectangle(0, 0, W, 600); c.set_source(g); c.fill()
    r = random.Random(4)
    if night:
        for _ in range(170): c.arc(r.uniform(0, W), r.uniform(0, 470), r.uniform(.8, 2.4), 0, 6.3); c.set_source_rgba(1, 1, 1, r.uniform(.4, 1)); c.fill()
        c.arc(1480, 150, 46, 0, 6.3); c.set_source_rgb(1, .97, .85); c.fill()
        c.arc(1462, 140, 40, 0, 6.3); c.set_source_rgb(*hx(s0)); c.fill()
    elif dusk:
        c.arc(1250, 560, 96, math.pi, 2 * math.pi); c.set_source_rgb(1, .8, .5); c.fill()
    else:
        c.arc(1600, 140, 62, 0, 6.3); c.set_source_rgb(1, .93, .6); c.fill()
    # clouds (slow)
    for k, (cy, sc) in enumerate(((150, 1.0), (90, .7), (230, .85), (120, .6), (200, 1.1))):
        cx = wrapx(k * 520 + 100, scroll, .05, W + 600)
        blobs = ((0, 0, 34), (40, -16, 44), (86, 0, 32), (44, 10, 30))
        for dx, dy, rr in blobs: c.new_sub_path(); c.arc(cx + dx * sc, cy + dy * sc, rr * sc + 2.5, 0, 6.3)
        c.set_source_rgb(*L); c.fill()
        for dx, dy, rr in blobs: c.new_sub_path(); c.arc(cx + dx * sc, cy + dy * sc, rr * sc, 0, 6.3)
        c.set_source_rgb(*((1, 1, 1) if m == 'day' else (hx('#FFD3C2') if dusk else hx('#3A3C6E')))); c.fill()
    # hot-air balloon + kites + plane banner
    bx = wrapx(700, scroll, .08, W + 900); by = 210 + 8 * math.sin(t)
    c.set_line_width(3)
    for k, col in enumerate(('#FF7A6B', '#FFC857', '#7ED6C4', '#FFC857', '#FF7A6B')):
        c.save(); c.arc(bx, by, 48, 0, 6.3); c.clip(); c.rectangle(bx - 48 + k * 19.2, by - 50, 19.2, 100); c.set_source_rgb(*tone(col, m)); c.fill(); c.restore()
    c.arc(bx, by, 48, 0, 6.3); c.set_source_rgb(*L); c.stroke()
    c.move_to(bx - 30, by + 38); c.line_to(bx - 12, by + 72); c.move_to(bx + 30, by + 38); c.line_to(bx + 12, by + 72); c.stroke()
    c.rectangle(bx - 14, by + 72, 28, 20); shape(c, tone('#C68B59', m), L)
    if not night:
        px = wrapx(1500, scroll, -.6, W + 1400) ; py = 80
        c.set_source_rgb(*L); c.move_to(px, py); c.line_to(px + 40, py); c.stroke(); c.move_to(px + 40, py); c.line_to(px + 70, py + 6); c.line_to(px + 40, py + 10); c.close_path(); shape(c, (1, 1, 1), L)
        c.move_to(px, py + 5); c.line_to(px - 30, py + 5); c.stroke()
        rrect(c, px - 250, py - 10, 220, 30, 6); shape(c, hx('#FFF6D8'), L); tx(c, 'HAVE A GOOD DAY', px - 236, py + 12, 18)
    c.save(); c.translate(0, -120)
    # far coast: hills, cliff village, wind turbines
    c.move_to(0, 600)
    for k in range(9): xx = k * 260; c.curve_to(xx + 60, 520 - (k % 3) * 30, xx + 200, 520 - ((k + 1) % 3) * 30, xx + 260, 600 - 40 * (k % 2))
    c.line_to(W, 620); c.line_to(0, 620); c.close_path(); shape(c, tone('#A9D7B4', m), L)
    for k in range(4):   # wind turbines: outlined white towers and turning blades
        wx = wrapx(k * 480 + 300, scroll, .12, W + 600); wy = 500
        a = t * 2 + k
        for lw, col in ((8, L), (4, tone('#FFFFFF', m))):
            c.set_line_width(lw); c.set_source_rgb(*col); c.move_to(wx, wy + 100); c.line_to(wx, wy); c.stroke()
            for j in range(3):
                aa = a + j * 2.094; c.move_to(wx, wy); c.line_to(wx + 40 * math.cos(aa), wy + 40 * math.sin(aa)); c.stroke()
        c.arc(wx, wy, 5, 0, 6.3); shape(c, tone('#FFFFFF', m), L)
    # sea
    a0, a1 = SK[m]['sea']
    g = cairo.LinearGradient(0, 610, 0, 770); g.add_color_stop_rgb(0, *hx(a0)); g.add_color_stop_rgb(1, *hx(a1)); c.rectangle(0, 610, W, 300); c.set_source(g); c.fill()
    if dusk:
        for k in range(7): c.rectangle(1190 + k * 6 - 20, 620 + k * 20, 120 - k * 12, 6); c.set_source_rgba(1, .85, .55, .8); c.fill()
    if night:
        for k in range(6): c.rectangle(1420 + (k % 2) * 10, 625 + k * 22, 80 - k * 8, 5); c.set_source_rgba(1, .97, .8, .55); c.fill()
    c.set_line_width(2.5); c.set_source_rgba(1, 1, 1, .75)
    for k in range(40):
        wx = wrapx(k * 97, scroll, .35, W + 400); wy = 630 + (k * 41) % 130
        c.move_to(wx, wy); c.curve_to(wx + 10, wy - 7, wx + 20, wy - 7, wx + 30, wy); c.stroke()
    # lighthouse on a rock
    lx = wrapx(420, scroll, .3, W + 1600); ly = 650
    c.move_to(lx - 70, ly + 20); c.curve_to(lx - 50, ly - 20, lx + 50, ly - 20, lx + 70, ly + 20); c.close_path(); shape(c, tone('#8C8FA8', m), L)
    c.move_to(lx - 20, ly); c.line_to(lx - 13, ly - 120); c.line_to(lx + 13, ly - 120); c.line_to(lx + 20, ly); c.close_path(); shape(c, tone('#FFFFFF', m), L)
    for k in range(3): c.rectangle(lx - 17 + k * 2, ly - 92 + k * 30, 34 - k * 4, 12); c.set_source_rgb(*tone('#FF6B5B', m)); c.fill()
    c.rectangle(lx - 17, ly - 142, 34, 22); shape(c, hx('#FFE27A') if night else tone('#DDF1FF', m), L)
    c.move_to(lx - 21, ly - 142); c.line_to(lx, ly - 160); c.line_to(lx + 21, ly - 142); c.close_path(); shape(c, tone('#FF6B5B', m), L)
    if night: c.move_to(lx, ly - 131); c.line_to(lx + 560, ly - 200); c.line_to(lx + 560, ly - 70); c.close_path(); c.set_source_rgba(1, .95, .6, .2); c.fill()
    # boats: ferry, sailboats, windsurfer, buoys
    fx = wrapx(1300, scroll, .2, W + 1200)
    c.move_to(fx - 110, 660); c.line_to(fx + 110, 660); c.line_to(fx + 90, 690); c.line_to(fx - 96, 690); c.close_path(); shape(c, tone('#FFFFFF', m), L)
    rrect(c, fx - 70, 630, 120, 30, 6); shape(c, tone('#8FB8FF', m), L)
    for k in range(5): c.rectangle(fx - 60 + k * 22, 638, 12, 12); c.set_source_rgb(*(hx('#FFE27A') if night else tone('#DDF1FF', m))); c.fill()
    c.rectangle(fx + 20, 606, 18, 24); shape(c, tone('#FF6B5B', m), L)
    for k, (bx0, col) in enumerate(((600, '#FFC857'), (1750, '#FF9FC2'), (2300, '#7ED6C4'))):
        sx = wrapx(bx0, scroll, .28, W + 900); sy = 700 + k * 18 + 3 * math.sin(t * 2 + k)
        c.move_to(sx - 34, sy); c.line_to(sx + 34, sy); c.line_to(sx + 24, sy + 14); c.line_to(sx - 24, sy + 14); c.close_path(); shape(c, tone('#FFFFFF', m), L)
        c.move_to(sx, sy - 4); c.line_to(sx, sy - 66); c.line_to(sx + 30, sy - 8); c.close_path(); shape(c, tone(col, m), L)
        c.move_to(sx - 4, sy - 60); c.line_to(sx - 26, sy - 8); c.line_to(sx - 4, sy - 8); c.close_path(); shape(c, tone('#FFFFFF', m), L)
    wsx = wrapx(980, scroll, .45, W + 700); wsy = 742
    c.move_to(wsx - 30, wsy); c.line_to(wsx + 30, wsy); c.stroke(); c.move_to(wsx, wsy); c.line_to(wsx + 4, wsy - 60); c.line_to(wsx + 40, wsy - 10); c.close_path(); shape(c, tone('#FF7A6B', m), L)
    person(c, wsx - 10, wsy, .7, '#2F5BEA', m)
    for k in range(5):
        bx = wrapx(k * 410 + 200, scroll, .4, W + 500); by = 758 + 3 * math.sin(t * 3 + k)
        c.arc(bx, by, 8, math.pi, 2 * math.pi); c.close_path(); shape(c, tone(['#FF6B5B', '#FFC857'][k % 2], m), L)
    c.restore()
    c.rectangle(0, 700, W, 160); c.set_source_rgb(*tone('#F7E2B5', m)); c.fill()   # sand apron down to the promenade
    # beach (closer, a little bigger)
    c.save(); c.translate(0, 650); c.scale(1.25, 1.25); c.translate(0, -770)
    c.move_to(0, 770); c.curve_to(500, 760, 1300, 782, W, 768); c.line_to(W, 812); c.line_to(0, 812); c.close_path(); shape(c, tone('#F7E2B5', m), L)
    rb = random.Random(12)
    for k in range(10):
        bx = wrapx(k * 260 + 60, scroll, .7, W + 800); kind = k % 5
        if kind == 0:   # parasol + someone sunbathing on a towel
            c.set_line_width(3); rrect(c, bx - 40, 792, 70, 12, 4); shape(c, tone(PAL[(k + 2) % 7], m), L)
            person(c, bx - 6, 800, .7, PAL[(k + 4) % 7], m, 'lie')
            c.set_source_rgb(*L); c.move_to(bx + 34, 806); c.line_to(bx + 34, 734); c.stroke()
            c.move_to(bx - 20, 744); c.curve_to(bx - 10, 706, bx + 78, 706, bx + 88, 744); c.close_path(); shape(c, tone(PAL[k % 7], m), L)
        elif kind == 1:   # sandcastle + kid with bucket
            c.move_to(bx - 26, 806); c.line_to(bx - 26, 784); c.line_to(bx - 14, 784); c.line_to(bx - 14, 774); c.line_to(bx + 2, 774); c.line_to(bx + 2, 784); c.line_to(bx + 14, 784); c.line_to(bx + 14, 806); c.close_path(); shape(c, tone('#E8C88A', m), L)
            c.move_to(bx - 6, 774); c.line_to(bx - 6, 760); c.line_to(bx + 6, 765); c.line_to(bx - 6, 768); c.stroke()
            person(c, bx + 40, 806, .55, '#FFC857', m, 'sit', t)
        elif kind == 2:   # volleyball net + two players
            c.set_source_rgb(*L); c.move_to(bx - 50, 806); c.line_to(bx - 50, 748); c.move_to(bx + 50, 806); c.line_to(bx + 50, 748); c.stroke()
            for j in range(4): c.move_to(bx - 50, 750 + j * 7); c.line_to(bx + 50, 750 + j * 7); c.stroke()
            person(c, bx - 80, 806, .7, '#FF7A6B', m, 'walk', t); person(c, bx + 80, 806, .7, '#7ED6C4', m, 'walk', t + 1)
            c.arc(bx + 10, 720 + 14 * math.sin(t * 3), 8, 0, 6.3); shape(c, tone('#FFFFFF', m), L)
        elif kind == 3:   # lifeguard tower + surfboards
            c.set_source_rgb(*L); c.move_to(bx - 24, 806); c.line_to(bx - 16, 752); c.move_to(bx + 24, 806); c.line_to(bx + 16, 752); c.stroke()
            c.rectangle(bx - 26, 728, 52, 26); shape(c, tone('#FF6B5B', m), L); c.rectangle(bx - 26, 718, 52, 10); shape(c, tone('#FFFFFF', m), L)
            for j, col in enumerate(('#FFC857', '#7ED6C4', '#FF9FC2')):
                c.save(); c.translate(bx + 50 + j * 16, 806); c.rotate(-.08 + j * .08); c.scale(.32, 1); c.arc(0, -32, 34, 0, 6.3); c.restore(); shape(c, tone(col, m), L)
        else:   # dog running with an owner
            dog(c, bx, 806, .8, '#E9C29B', m, t); person(c, bx - 50, 806, .7, '#9BD3A0', m, 'walk', t)
    c.restore()
    # promenade: palms, ice-cream truck, surf shop, bench, planters, bus stop (big, close to the road)
    c.save(); c.translate(0, 830); c.scale(1.6, 1.6); c.translate(0, -830)
    c.rectangle(-50, 812, W + 100, 18); shape(c, tone('#E9DFD0', m), L)
    for k in range(8):
        px = wrapx(k * 360 + 150, scroll, 1.0, W + 1100); kind = k % 4
        if kind == 0:   # palm
            c.set_line_width(10); c.set_source_rgb(*tone('#B07A4F', m)); c.move_to(px, 830); c.curve_to(px + 6, 760, px - 4, 700, px + 10, 640); c.stroke()
            c.set_line_width(3)
            for a in range(6):
                aa = -math.pi / 2 + (a - 2.5) * .55; c.save(); c.translate(px + 10, 640); c.rotate(aa); c.scale(1, .32); c.arc(42, 0, 42, 0, 6.3); c.restore(); shape(c, tone('#5DBB7A', m), L)
        elif kind == 1:   # ice-cream truck
            rrect(c, px - 80, 744, 150, 70, 10); shape(c, tone('#FFD6E4', m), L)
            c.rectangle(px - 60, 756, 70, 30); shape(c, tone('#FFF6D8', m) if not night else hx('#FFE9A8'), L)
            c.move_to(px - 60, 756); c.line_to(px + 10, 756); c.stroke()
            for j in range(5): c.arc(px - 54 + j * 15, 756, 7.5, 0, math.pi); c.set_source_rgb(*tone(['#FF7A6B', '#FFFFFF'][j % 2], m)); c.fill()
            c.arc(px + 52, 726, 14, 0, 6.3); shape(c, tone('#FF9FC2', m), L); c.move_to(px + 42, 734); c.line_to(px + 52, 760); c.line_to(px + 62, 734); c.close_path(); shape(c, tone('#E3B778', m), L)
            mob.wheel(c, px - 50, 814, 13, 0, L); mob.wheel(c, px + 40, 814, 13, 0, L)
        elif kind == 2:   # surf shop with sign and flags
            c.rectangle(px - 90, 712, 180, 118); shape(c, tone('#7ED6C4', m), L)
            c.rectangle(px - 70, 752, 60, 50); shape(c, tone('#FFF6D8', m) if not night else hx('#FFE9A8'), L)
            c.rectangle(px + 14, 752, 50, 78); shape(c, tone('#FFFFFF', m), L)
            rrect(c, px - 80, 690, 160, 28, 8); shape(c, tone('#FFC857', m), L); tx(c, 'SURF SHOP', px - 58, 711, 18)
            c.set_source_rgb(*L); c.move_to(px - 90, 690)
            for j in range(9): c.line_to(px - 90 + j * 22.5, 690 - 10 * (j % 2 == 0))
            c.stroke()
        else:   # bench with a couple + flower planter + bus stop
            c.rectangle(px - 60, 804, 120, 10); shape(c, tone('#D9A066', m), L); c.rectangle(px - 60, 786, 120, 8); shape(c, tone('#D9A066', m), L)
            person(c, px - 20, 812, .7, '#C9A7FF', m, 'sit'); person(c, px + 22, 812, .7, '#FFC857', m, 'sit', hair='#2B2541')
            c.rectangle(px + 90, 806, 70, 24); shape(c, tone('#E07A5F', m), L)
            for j in range(5): c.arc(px + 98 + j * 14, 800, 8, 0, 6.3); shape(c, tone(PAL[j], m), L)
            c.set_source_rgb(*L); c.set_line_width(4); c.move_to(px - 120, 830); c.line_to(px - 120, 730); c.stroke()
            rrect(c, px - 144, 712, 48, 32, 6); shape(c, tone('#2F5BEA', m), L); tx(c, 'BUS', px - 136, 735, 16, (1, 1, 1))
    c.restore()
    # street lamps (glow at night) + guardrail
    for k in range(4):
        lpx = wrapx(k * 540 + 330, scroll, 1.0, W + 760)
        c.set_line_width(5); c.set_source_rgb(*L); c.move_to(lpx, 860); c.line_to(lpx, 700); c.curve_to(lpx, 680, lpx + 20, 674, lpx + 36, 678); c.stroke()
        c.arc(lpx + 40, 686, 12, 0, 6.3); shape(c, hx('#FFE27A') if (night or dusk) else hx('#F2F2F2'), L)
        if night: c.arc(lpx + 40, 700, 80, 0, 6.3); c.set_source_rgba(1, .9, .5, .16); c.fill()
    c.rectangle(0, 830, W, 30); c.set_source_rgb(*tone('#D7EEF5', m)); c.fill()
    c.set_line_width(4); c.set_source_rgb(*L); c.move_to(0, 836); c.line_to(W, 836); c.stroke()
    for k in range(30):
        px = wrapx(k * 80, scroll, 1.0, W + 400); c.move_to(px, 836); c.line_to(px, 860); c.stroke()
    # road + flower verge at the bottom edge
    c.rectangle(0, GY, W, H - GY); shape(c, tone('#C9C6D6', m), L)
    c.set_line_width(6); c.set_source_rgba(1, 1, 1, .8)
    for k in range(12):
        px = wrapx(k * 220, scroll, 1.2, W + 600); c.move_to(px, 960); c.line_to(px + 100, 960); c.stroke()
    for k in range(26):
        px = wrapx(k * 95, scroll, 1.35, W + 600)
        for dx, rr in ((-26, 26), (0, 34), (28, 24)): c.new_sub_path(); c.arc(px + dx, 1066, rr + 2.5, 0, 6.3)
        c.set_source_rgb(*L); c.fill()
        for dx, rr in ((-26, 26), (0, 34), (28, 24)): c.new_sub_path(); c.arc(px + dx, 1066, rr, 0, 6.3)
        c.set_source_rgb(*tone('#7FC98F', m)); c.fill()
        for j in range(3): c.arc(px - 20 + j * 20, 1046 + (j % 2) * 10, 5, 0, 6.3); c.set_source_rgb(*tone(PAL[(k + j) % 6], m)); c.fill()
    # seagulls
    if not night:
        c.set_line_width(3); c.set_source_rgb(*L)
        for k in range(6):
            gx = wrapx(k * 330 + 200, scroll, -.3, W + 800) ; gy = 300 + (k * 53) % 160 + 6 * math.sin(t * 4 + k)
            f = 8 * math.sin(t * 8 + k)
            c.move_to(gx - 14, gy - f); c.curve_to(gx - 6, gy - 10, gx, gy - 4, gx, gy); c.curve_to(gx, gy - 4, gx + 6, gy - 10, gx + 14, gy - f); c.stroke()

def surf(fn):
    sf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(sf)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND); fn(c); return sf

if __name__ == '__main__':
    OUT = sys.argv[1]
    O1 = OPTS[0][2]
    def bike_on(c, m, sc, t):
        scene(c, m, sc, t); haru_bike(c, 880, O1, t=t, s=1.0)
    big = surf(lambda c: bike_on(c, 'day', 300, 1.0))
    small = [surf(lambda c, m=m, i=i: bike_on(c, m, 1500 + i * 700, 2.0 + i)) for i, m in enumerate(('day', 'dusk', 'night'))]
    sw, pad = 620, 30; sh = sw * H // W
    bw = sw * 3 + pad * 2; bh = bw * H // W
    sheet = cairo.ImageSurface(cairo.FORMAT_RGB24, pad * 2 + bw, 120 + bh + 80 + sh + 70); c = cairo.Context(sheet)
    c.set_source_rgb(*hx('#FAF8F2')); c.paint()
    c.select_font_face('NanumSquareRound', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    c.set_font_size(34); c.set_source_rgb(*L); c.move_to(pad, 56); c.show_text('PLAY LIST 03 시안 v2 · 바닷가 자전거 (배경 디테일 추가)')
    c.set_font_size(22); c.move_to(pad, 96); c.show_text('낮 장면 크게 보기')
    c.save(); c.translate(pad, 110); c.scale(bw / W, bh / H); c.set_source_surface(big, 0, 0); c.paint(); c.restore()
    y = 110 + bh + 50
    c.set_font_size(22); c.move_to(pad, y); c.show_text('같은 길의 다른 구간: 낮 → 노을 → 밤')
    for i, p in enumerate(small):
        x = pad + i * (sw + pad)
        c.save(); c.translate(x, y + 14); c.scale(sw / W, sh / H); c.set_source_surface(p, 0, 0); c.paint(); c.restore()
    sheet.write_to_png(OUT)
