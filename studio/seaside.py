"""Seaside world (PLAY LIST 03): coastal road scenery + Haru riding a bicycle, driving an open car and walking.
Used by render_video.py with --world seaside. The scenery is drawn fresh every frame (stateless, from scroll + time)."""
import math, random
import cairo, numpy as np
from PIL import Image
import character as ch
from mobility import mob
W, H, GY = 1920, 1080, 860
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
        px = wrapx(k * 220, scroll, 1.2, W + 600); c.move_to(px, 1014); c.line_to(px + 100, 1014); c.stroke()
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


# ---------------------------------------------------------------- Haru on the move
def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
CXH = 820
SPEED = {'bike': 260, 'car': 420, 'walk': 130}

def rrect_(c, x, y, w, h, r): rrect(c, x, y, w, h, r)

def head_plain(c, hx_, hy_, t):
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

def bike_haru(c, t, ph, o, frame_col, don=1.0, reach=0.0, press=0.0, sun=1.0, helmet_k=1.0):
    """Haru on the bicycle (origin = road under the crank). sun: 1 sunglasses on, 0 pushed up onto the helmet"""
    mob.O = o
    pants, top = hx(o['bottom']), hx(o['top'])
    rw, fw, cr = (-78, -42), (86, -42), (0, -40)
    mob.wheel(c, *rw, 40, ph * 1.2, L); mob.wheel(c, *fw, 40, ph * 1.2, L)
    sad, head_t, bar = (-22, -106), (56, -122), (46, -146)
    hip = (sad[0] + 2, sad[1] - 6)
    pb = (cr[0] + 18 * math.cos(ph + math.pi), cr[1] + 18 * math.sin(ph + math.pi))
    mob.leg_to(c, hip, pb, pants, L, True)
    c.set_line_width(7); c.set_source_rgb(*hx(frame_col))
    mob.poly(c, [rw, cr, sad]); mob.poly(c, [rw, (sad[0] + 4, sad[1] + 8)]); mob.poly(c, [(sad[0] + 4, sad[1] + 8), head_t]); mob.poly(c, [cr, head_t]); mob.poly(c, [fw, head_t, bar])
    c.set_line_width(5); c.set_source_rgb(*L); mob.poly(c, [(bar[0] - 6, bar[1]), (bar[0] + 14, bar[1] - 4)])
    c.set_line_width(3); c.save(); c.translate(*sad); c.scale(1, .45); c.arc(0, 0, 18, 0, 2 * math.pi); c.restore(); shape(c, hx('#4A3F35'), L)
    c.arc(cr[0], cr[1], 11, 0, 2 * math.pi); shape(c, (.85, .87, .92), L)
    mob.cup(c, 82, -134, t, L, o)
    c.set_line_width(3); c.move_to(62, -140); c.line_to(104, -140); c.line_to(98, -112); c.line_to(68, -112); c.close_path(); shape(c, hx('#E3B778'), L)
    c.move_to(70, -128); c.line_to(98, -128); c.stroke()
    sh = (hip[0] + 6, hip[1] - 62); hxh, hyh = hip[0] + 18, hip[1] - 112
    tgt = (bar[0] - 2, bar[1] + 2)
    if reach > 0:
        _, _, _, _, _, cx_, cy_ = ch.phones_pose(hxh, hyh, 42, don)
        tgt = (tgt[0] + (cx_ + 4 - tgt[0]) * reach, tgt[1] + (cy_ + 4 - press * 2 - tgt[1]) * reach)
    mob.arm_to(c, sh, tgt, top, L, True)
    c.save(); c.translate(hip[0], hip[1]); c.rotate(math.radians(10)); c.translate(-hip[0], -hip[1]); mob.torso(c, hip, o, L, top); c.restore()
    pf = (cr[0] + 18 * math.cos(ph), cr[1] + 18 * math.sin(ph))
    mob.leg_to(c, hip, pf, pants, L, False)
    c.set_line_width(4); c.set_source_rgb(*L); mob.poly(c, [(cr[0] - 18 * math.cos(ph), cr[1] - 18 * math.sin(ph)), (pf[0], pf[1])])
    head_plain(c, hxh, hyh, t)
    ch._phones(c, 'retro', hxh, hyh, 42, hx(o['phones']), L, don)
    gx, gy2 = hxh + 24, hyh + 4
    if sun > 0.001:
        c.save(); c.translate(0, -58 * (1 - sun))
        c.arc(gx, gy2, 15, 0, 2 * math.pi); c.set_source_rgba(.13, .12, .2, .9); c.fill_preserve(); c.set_source_rgb(*L); c.set_line_width(4); c.stroke()
        c.move_to(gx - 15, gy2 - 2); c.line_to(hxh - 16, gy2 - 4); c.stroke()
        c.set_source_rgba(1, 1, 1, .8); c.set_line_width(3); c.arc(gx - 4, gy2 - 5, 6, math.pi * 1.1, math.pi * 1.6); c.stroke()
        c.restore()
    if helmet_k > 0.001:
        c.save(); c.translate(0, -70 * (1 - helmet_k)); mob.helmet(c, hxh, hyh, 42, o, L); c.restore()
    if sun <= 0.001: ch.shades_on_head(c, hxh, hyh, 42, L, lift=24 if helmet_k > .5 else 0)
    mob.arm_to(c, sh, (bar[0] + 4, bar[1]), top, L, False)

def parked_bike(c, x, o, frame_col):
    c.save(); c.translate(x, GY)
    rw, fw, cr = (-78, -42), (86, -42), (0, -40)
    mob.wheel(c, *rw, 40, 0, L); mob.wheel(c, *fw, 40, 0, L)
    sad, head_t, bar = (-22, -106), (56, -122), (46, -146)
    c.set_line_width(7); c.set_source_rgb(*hx(frame_col))
    mob.poly(c, [rw, cr, sad]); mob.poly(c, [rw, (sad[0] + 4, sad[1] + 8)]); mob.poly(c, [(sad[0] + 4, sad[1] + 8), head_t]); mob.poly(c, [cr, head_t]); mob.poly(c, [fw, head_t, bar])
    c.set_line_width(5); c.set_source_rgb(*L); mob.poly(c, [(bar[0] - 6, bar[1]), (bar[0] + 14, bar[1] - 4)])
    c.set_line_width(3); c.save(); c.translate(*sad); c.scale(1, .45); c.arc(0, 0, 18, 0, 2 * math.pi); c.restore(); shape(c, hx('#4A3F35'), L)
    c.move_to(62, -140); c.line_to(104, -140); c.line_to(98, -112); c.line_to(68, -112); c.close_path(); shape(c, hx('#E3B778'), L)
    c.save(); c.translate(bar[0] + 6, bar[1] + 30); c.scale(.55, .55); mob.helmet(c, 0, 0, 42, o, L); c.restore()
    c.set_line_width(7); c.set_source_rgb(*L); c.move_to(-60, -40); c.line_to(-70, 0); c.stroke()
    c.restore()

def seated_haru(c, t, o, don=1.0, reach=0.0, press=0.0, wind=0.0):
    hip = (-20, -66); top = hx(o['top']); mob.O = o
    hxh, hyh = hip[0] + 6, hip[1] - 116
    tgt = (40, -132)
    if reach > 0:
        _, _, _, _, _, cx_, cy_ = ch.phones_pose(hxh, hyh, 42, don)
        tgt = (tgt[0] + (cx_ + 4 - tgt[0]) * reach, tgt[1] + (cy_ + 4 - press * 2 - tgt[1]) * reach)
    mob.arm_to(c, (hip[0] + 4, hip[1] - 62), tgt, top, L, True)
    sc = hx(o['scarf']); x, y = hip
    c.set_line_width(3); c.move_to(x - 10, y - 74)
    c.curve_to(x - 40, y - 74 + 6 * math.sin(t * 9), x - 60, y - 70 - 6 * math.sin(t * 9 + 1), x - 80 - 10 * wind, y - 66 + 4 * math.sin(t * 11))
    c.line_to(x - 76 - 10 * wind, y - 54 + 4 * math.sin(t * 11)); c.curve_to(x - 56, y - 60, x - 36, y - 62, x - 10, y - 62); c.close_path(); shape(c, sc, L)
    mob.torso(c, hip, dict(o, bag=None), L, top)
    head_plain(c, hxh, hyh, t)
    ch._phones(c, 'retro', hxh, hyh, 42, hx(o['phones']), L, don)
    ch.shades_on_head(c, hxh, hyh, 42, L)
    return (hip[0] + 4, hip[1] - 62)

def convertible(c, x, t, ang, o, col, seated=None):
    c.save(); c.translate(x, GY)
    rrect(c, -78, -132, 34, 70, 10); shape(c, hx('#F3E9D2'), L)
    sh = seated_haru(c, t, o, **seated) if seated is not None else None
    c.set_line_width(4)
    c.move_to(-190, -40); c.line_to(-196, -88); c.curve_to(-196, -100, -186, -104, -170, -104); c.line_to(40, -104)
    c.curve_to(90, -104, 150, -96, 196, -80); c.curve_to(214, -74, 220, -60, 216, -44); c.line_to(210, -36); c.line_to(-184, -36); c.close_path(); shape(c, hx(col), L)
    c.move_to(-170, -78); c.line_to(200, -70); c.set_line_width(3); c.set_source_rgb(*lerp(hx(col), (1, 1, 1), .5)); c.stroke()
    c.move_to(-60, -102); c.line_to(-60, -44); c.set_source_rgb(*L); c.stroke()
    rrect(c, -40, -88, 22, 6, 3); shape(c, (.9, .9, .95), L)
    c.move_to(60, -104); c.line_to(86, -160); c.line_to(96, -158); c.line_to(76, -104); c.close_path()
    c.set_source_rgba(.85, .95, 1, .55); c.fill_preserve(); c.set_source_rgb(*L); c.stroke()
    c.arc(206, -64, 9, 0, 6.3); shape(c, hx('#FFF4C2'), L); c.rectangle(-196, -78, 10, 16); shape(c, hx('#FF6B5B'), L)
    mob.wheel(c, -120, -30, 34, ang, L); mob.wheel(c, 132, -30, 34, ang, L)
    if sh: mob.arm_to(c, sh, (52, -128), hx(o['top']), L, False)
    c.set_line_width(5); c.set_source_rgb(*L); c.arc(52, -128, 16, 0, 6.3); c.stroke()
    c.restore()

def traffic_light(c, x, green):
    c.set_line_width(6); c.set_source_rgb(*L); c.move_to(x, 900); c.line_to(x, 700); c.stroke()
    rrect(c, x - 22, 620, 44, 90, 12); shape(c, hx('#2B2541'), L)
    c.arc(x, 645, 13, 0, 6.3); c.set_source_rgb(*(hx('#FF5A5A') if not green else hx('#5A3A3A'))); c.fill()
    c.arc(x, 685, 13, 0, 6.3); c.set_source_rgb(*(hx('#3AD98A') if green else hx('#24453A'))); c.fill()
    for k in range(6): c.rectangle(x + 30 + k * 34, 900, 20, 170); c.set_source_rgba(1, 1, 1, .85); c.fill()

def bubble(c, x, y, a, sc=1.0):
    if a < .02: return
    c.save(); c.translate(x, y); c.scale(sc, sc); c.push_group(); rrect(c, -44, -32, 88, 64, 18); shape(c, (1, 1, 1), L)
    c.move_to(-12, -16); c.line_to(18, 0); c.line_to(-12, 16); c.close_path(); c.set_source_rgb(*hx('#FF2D87')); c.fill()
    c.pop_group_to_source(); c.paint_with_alpha(a); c.restore()


class Ride:
    """Timeline of one video: which way Haru travels in every track, the hand-over scenes, the opening and ending.
    groups: [('bike', 0, 6), ('car', 7, 13), ('walk', 14, 19)] (0-based track indices)."""
    def __init__(self, starts, ends, total, fps, groups, outfit, bike_col='#2F3E6B', car_col='#7ED6C4'):
        self.s, self.e, self.total, self.fps = starts, ends, total, fps
        self.mode = {}
        for m, a, b in groups:
            for i in range(a, b + 1): self.mode[i] = m
        self.n = len(starts); self.o = outfit; self.bike_col, self.car_col = bike_col, car_col
        self.walk_out = dict(top=outfit['top'], bottom=outfit['bottom'], phones=outfit['phones'], phones_style='retro', prop='hot',
                             scarf=outfit['scarf'], shades_up=True)
        ch.OUTFITS['_seaside_walk'] = self.walk_out
        self.swaps = {i: (self.mode[i], self.mode[i + 1]) for i in range(self.n - 1) if self.mode[i] != self.mode[i + 1]}
        self.pos = [0.0]
        for fi in range(int(total * fps) + 2): self.pos.append(self.pos[-1] + self.speed(fi / fps) / fps)
        self.park = {}
        for i, (a, b) in self.swaps.items():
            if (a, b) == ('bike', 'car'):
                self.park[('bike', i)] = self.at(self.e[i] + .05) + CXH
                self.park[('car', i)] = self.at(self.e[i] + 1.3) + CXH
            if (a, b) == ('car', 'walk'):
                self.park[('car2', i)] = self.at(self.e[i] + .1) + CXH
        self.lights = [(i, self.at(self.e[i] + .1) + CXH + 330) for i in range(self.n - 1) if i not in self.swaps and self.mode[i] in ('bike', 'car')]
        bikes = [i for i in range(self.n) if self.mode[i] == 'bike']; cars = [i for i in range(self.n) if self.mode[i] == 'car']
        self.t_dusk = self.e[bikes[-1]] - 1.0 if bikes else -1
        self.t_night = self.e[cars[-1]] - 3.0 if cars else 1e9

    def at(self, t): return self.pos[max(0, min(len(self.pos) - 1, int(t * self.fps)))]

    def where(self, t):
        """('pre'|'song'|'gap'|'post', track index)"""
        if t < self.s[0]: return 'pre', 0
        for i in range(self.n):
            if self.s[i] <= t <= self.e[i]: return 'song', i
            if i + 1 < self.n and self.e[i] < t < self.s[i + 1]: return 'gap', i
        return 'post', self.n - 1

    def speed(self, t):
        k, i = self.where(t)
        if k == 'pre': return 0.0
        if k == 'post': return 0.0
        m = self.mode[i]
        if k == 'song':
            up = sm((t - (self.s[i] - .2)) / (1.0 if m != 'car' else 1.2))
            down = 1 - sm((t - (self.e[i] - (1.4 if m == 'car' else 1.2))) / (1.4 if m == 'car' else 1.2))
            return SPEED[m] * min(up, down if i < self.n - 1 or True else 1)
        if (m, self.mode[i + 1]) == ('bike', 'car'):   # walk from the parked bike to the car
            a, b = self.e[i] + .2, self.e[i] + 1.25
            return 500 * min(sm((t - a) / .2), 1 - sm((t - (b - .2)) / .2)) if a <= t <= b else 0.0
        return 0.0

    def sky(self, t):
        a = sm((t - self.t_dusk) / 4.0); b = sm((t - self.t_night) / 5.0)
        return {'day': (1 - a) * (1 - b), 'dusk': a * (1 - b), 'night': b}

    def frame(self, t):
        """returns (PIL RGB image, night 0..1 for the UI colour, name-tag y offset, play-bubble alpha)"""
        scroll = self.at(t); out = None
        for m, w in self.sky(t).items():
            if w < .002: continue
            s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
            c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
            scene(c, m, scroll, t)
            a = np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(np.float32) * w
            out = a if out is None else out + a
        s = cairo.ImageSurface.create_for_data(np.ascontiguousarray(out.clip(0, 255).astype(np.uint8)), cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(s); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        ba, tag_dy = self.draw_haru(c, t, scroll)
        s.flush()
        rgb = np.ndarray((H, W, 4), np.uint8, s.get_data())[..., [2, 1, 0]].copy()
        sk = self.sky(t)
        return Image.fromarray(rgb, 'RGB'), sk['night'] + .35 * sk['dusk'], tag_dy, ba

    def layer(self, c, fn, alpha):
        if alpha <= .01: return
        c.push_group(); fn(); c.pop_group_to_source(); c.paint_with_alpha(min(1, alpha))

    def draw_haru(self, c, t, scroll):
        o = self.o; k, i = self.where(t); ba = 0.0
        # parked things and traffic lights in the world
        for (what, j), wx in self.park.items():
            x = wx - scroll
            if not (-400 < x < W + 400): continue
            if what == 'bike' and t > self.e[j] + .2: parked_bike(c, x, o, self.bike_col)
            if what == 'car' and t < self.s[j + 1] - .02 and t > self.e[j] + .2: pass   # drawn with Haru below
            if what == 'car2' and t > self.e[j] + .4: convertible(c, x, t, 0, o, self.car_col)
        for j, wx in self.lights:
            x = wx - scroll
            if -300 < x < W + 300: traffic_light(c, x, t > self.s[j + 1] - .4)
        m = self.mode[i]
        ph = 2 * math.pi * self.at(t) / 260
        sun = 1.0
        bikes = [j for j in range(self.n) if self.mode[j] == 'bike']
        if bikes: sun = 1 - sm((t - (self.e[bikes[-1]] - .6)) / .4)
        # ---------- opening on the bike ----------
        if k == 'pre':
            reach = min(sm((t - .5) / .4), 1 - sm((t - 1.9) / .4)); don = sm((t - .9) / .7)
            press = math.sin((t - 1.6) / .35 * math.pi) if 1.6 <= t < 1.95 else 0
            if t > 1.65: ba = 1 - sm((t - (self.s[0] - .6)) / .5)
            helm = sm((t - 2.2) / .6)
            c.save(); c.translate(CXH, GY); bike_haru(c, t, ph, o, self.bike_col, don, reach, press, sun, helm); c.restore()
            bubble(c, CXH + 60, GY - 300, ba); return ba, 50
        # ---------- hand-overs ----------
        if k == 'gap' and i in self.swaps:
            a, b = self.swaps[i]; E, S = self.e[i], self.s[i + 1]
            if (a, b) == ('bike', 'car'):
                if t < E + .2:
                    rider = 1 - sm((t - (E - .05)) / .25)
                    self.layer(c, lambda: (c.save(), c.translate(CXH, GY), bike_haru(c, t, ph, o, self.bike_col, 1, 0, 0, sun, 1 - sm((t - (E - .6)) / .4)), c.restore()), rider)
                    self.layer(c, lambda: ch.draw(c, CXH, GY, t, L=L, outfit='_seaside_walk', walk=0, phase=0), 1 - rider)
                    return 0.0, 100
                walk_end = E + 1.25
                cx = self.park[('car', i)] - scroll
                inside = sm((t - walk_end) / .2)
                reach = min(sm((t - (walk_end + .15)) / .2), 1 - sm((t - (S - .2)) / .2))
                press = math.sin((t - (walk_end + .3)) / .3 * math.pi) if walk_end + .3 <= t < walk_end + .6 else 0
                convertible(c, cx, t, 0, o, self.car_col, seated=dict(reach=reach, press=press) if inside > .5 else None)
                w_ = min(1.0, self.speed(t) / 500)
                self.layer(c, lambda: ch.draw(c, CXH, GY, t, L=L, outfit='_seaside_walk', walk=w_, phase=2 * math.pi * self.at(t) / 180), 1 - inside)
                if t > walk_end + .35: ba = 1 - sm((t - (S + .1)) / .5)
                bubble(c, CXH + 60, GY - 300, ba); return ba, 120 if inside > .5 else 100
            if (a, b) == ('car', 'walk'):
                cx = self.park[('car2', i)] - scroll
                out_a = sm((t - (E + .05)) / .25)
                if out_a < .99: convertible(c, cx, t, 0, o, self.car_col, seated=dict() if out_a < .5 else None)
                reach = min(sm((t - (E + .3)) / .2), 1 - sm((t - (S - .4)) / .25))
                press = math.sin((t - (E + .45)) / .3 * math.pi) if E + .45 <= t < E + .75 else 0
                self.layer(c, lambda: ch.draw(c, CXH, GY, t, L=L, outfit='_seaside_walk', walk=0, phase=0, reach=reach, press=press), out_a)
                if t > E + .5: ba = 1 - sm((t - (S + .1)) / .5)
                bubble(c, CXH + 60, GY - 300, ba); return ba, 100
        # ---------- steady travel (and same-mode stops: brake, tap, play) ----------
        reach = press = 0.0
        if k == 'gap' or (k == 'song' and i > 0 and t < self.s[i] + .9):
            j = i if k == 'gap' else i - 1
            E, S = self.e[j], self.s[j + 1]
            reach = min(sm((t - (E - .1)) / .4), 1 - sm((t - (S - .1)) / .4))
            press = math.sin((t - (E + .2)) / .35 * math.pi) if E + .2 <= t < E + .55 else 0
            if t > E + .25: ba = 1 - sm((t - (S + .15)) / .5)
        if k == 'song' and i == 0 or (k == 'song' and t > self.e[i] - .6 and False): pass
        don = 1.0
        if k == 'post':
            E = self.e[-1]
            reach = min(sm((t - E - .2) / .4), 1 - sm((t - E - 1.4) / .4)); don = 1 - sm((t - E - .7) / .7)
        if m == 'bike':
            c.save(); c.translate(CXH, GY); bike_haru(c, t, ph, o, self.bike_col, don, reach, press, sun, 1.0); c.restore(); dy = 50
        elif m == 'car':
            wind = sm(self.speed(t) / 420)
            convertible(c, CXH, t, self.at(t) / 34, o, self.car_col, seated=dict(reach=reach, press=press, wind=wind)); dy = 120
        else:
            w_ = min(1.0, self.speed(t) / 130)
            ch.draw(c, CXH, GY, t, L=L, outfit='_seaside_walk', walk=w_, phase=2 * math.pi * .85 * self.at(t) / 130, reach=reach, press=press, don=don); dy = 100
        bubble(c, CXH + 60, GY - 300, ba)
        return ba, dy
