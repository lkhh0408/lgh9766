"""10-second city test clips: Haru rides a bike through Seoul / Paris / London / Shanghai / Tokyo, landmarks on the skyline.
usage: python3 city_test.py CITY out.mp4|out.png [t]"""
import sys, math, random, subprocess, cairo
S = '/tmp/claude-0/-home-user-lgh9766/b52f1d6d-22f0-5bcd-a4bc-05ad7db7a50f/scratchpad'
ARGV = sys.argv[:]; sys.argv = sys.argv[:1]
sys.path.insert(0, S + '/vol02'); sys.path.insert(0, S + '/mobility'); sys.path.insert(0, '/home/user/lgh9766/studio')
import numpy as np
from PIL import Image
import props, mob
import river_drafts as R
import river_test as RT
hexc, lerp = mob.hexc, mob.lerp
L = R.L
W, H, GY, CX, FPS = 1920, 1080, 760, 820, 24
SPEED = 130 * 2.6
BASE_FAR, BASE_MID = 640, 690
CITY = ARGV[1]


def sh(ctx, col, lw=3.5):
    ctx.set_line_width(lw); ctx.set_source_rgb(*(hexc(col) if isinstance(col, str) else col)); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.stroke()


def rect(ctx, x, y, w, h, col, lw=3.5):
    ctx.rectangle(x, y, w, h); sh(ctx, col, lw)


def line(ctx, pts, lw=3, col=None):
    ctx.set_line_width(lw); ctx.set_source_rgb(*(hexc(col) if col else L)); ctx.move_to(*pts[0]); [ctx.line_to(*p) for p in pts[1:]]; ctx.stroke()


def windows(ctx, x, y, w, h, cols, rows, col='#FFFDF6', pad=10, ww=None, wh=None):
    cw = (w - 2 * pad) / cols; rh = (h - 2 * pad) / rows
    ww = ww or cw * .55; wh = wh or rh * .6
    for i in range(cols):
        for j in range(rows):
            rect(ctx, x + pad + i * cw + (cw - ww) / 2, y + pad + j * rh + (rh - wh) / 2, ww, wh, col, 2.5)


# ------------------------------------------------------------------ landmarks (far layer)
def eiffel(ctx, x, by, h=520, col='#C49A6C', bands=None):
    pts = [(150, 0), (120, -50), (95, -110), (70, -180), (52, -250), (30, -340), (14, -430), (6, -h + 40)]
    pts = [(p * h / 520, q * h / 520) for p, q in pts]
    ctx.new_path(); ctx.move_to(x - pts[0][0], by)
    for p, q in pts[1:]: ctx.line_to(x - p, by + q)
    ctx.line_to(x, by - h)
    for p, q in reversed(pts[1:]): ctx.line_to(x + p, by + q)
    ctx.line_to(x + pts[0][0], by)
    aw, ah = 92 * h / 520, 80 * h / 520
    ctx.line_to(x + aw, by); ctx.curve_to(x + aw, by - ah, x - aw, by - ah, x - aw, by); ctx.close_path()
    sh(ctx, col)
    if bands:
        for q in (-110, -250, -430):
            y = by + q * h / 520; hw = dict(pts)[-q * 0] if False else None
    for q, hw in ((-110, 98), (-250, 56), (-430, 18)):
        rect(ctx, x - hw * h / 520, by + q * h / 520 - 9, 2 * hw * h / 520, 12, bands or col, 3)
    ctx.set_line_width(2); ctx.set_source_rgb(*L)
    for (q0, a0), (q1, a1) in (((-20, 135), (-100, 98)), ((-120, 90), (-240, 56)), ((-262, 50), (-420, 18))):
        for s in (-1, 1):
            ctx.move_to(x + s * a0 * h / 520, by + q0 * h / 520); ctx.line_to(x - s * a1 * .2 * h / 520, by + q1 * h / 520)
    ctx.stroke()


def arc_triomphe(ctx, x, by):
    rect(ctx, x - 100, by - 170, 200, 170, '#E9DCC0')
    rect(ctx, x - 108, by - 184, 216, 18, '#E2D2B2')
    ctx.new_path(); ctx.move_to(x - 34, by); ctx.line_to(x - 34, by - 80); ctx.curve_to(x - 34, by - 122, x + 34, by - 122, x + 34, by - 80); ctx.line_to(x + 34, by); ctx.close_path(); sh(ctx, '#BFD0E6')
    line(ctx, [(x - 100, by - 140), (x + 100, by - 140)], 2.5)


def big_ben(ctx, x, by):
    # Palace of Westminster
    rect(ctx, x - 420, by - 150, 400, 150, '#D8C59A')
    for i in range(14):
        px = x - 405 + i * 28; line(ctx, [(px, by - 150), (px, by - 172)], 3)
        ctx.move_to(px - 5, by - 172); ctx.line_to(px, by - 184); ctx.line_to(px + 5, by - 172); ctx.close_path(); sh(ctx, '#C9B482', 2)
    windows(ctx, x - 420, by - 140, 400, 120, 16, 3, '#F3EBD2', 8)
    # Elizabeth Tower
    rect(ctx, x - 32, by - 330, 64, 330, '#D8C59A')
    for j in range(6): line(ctx, [(x - 32, by - 40 - j * 48), (x + 32, by - 40 - j * 48)], 2)
    rect(ctx, x - 40, by - 400, 80, 76, '#D2BE8E')
    ctx.arc(x, by - 362, 27, 0, 2 * math.pi); sh(ctx, '#FFF8E6')
    line(ctx, [(x, by - 362), (x, by - 380)], 3); line(ctx, [(x, by - 362), (x + 12, by - 356)], 3)
    rect(ctx, x - 34, by - 430, 68, 30, '#C9B482')
    ctx.new_path(); ctx.move_to(x - 34, by - 430); ctx.line_to(x, by - 520); ctx.line_to(x + 34, by - 430); ctx.close_path(); sh(ctx, '#556B7A')
    for s in (-1, 1):
        ctx.move_to(x + s * 34 - 6, by - 430); ctx.line_to(x + s * 34, by - 456); ctx.line_to(x + s * 34 + 6, by - 430); ctx.close_path(); sh(ctx, '#556B7A', 2)


def london_eye(ctx, x, by, t):
    cy, r = by - 250, 225
    for s in (-1, 1): line(ctx, [(x + s * 120, by), (x, cy)], 6, '#E6E9EE'); line(ctx, [(x + s * 120, by), (x, cy)], 2)
    ctx.set_line_width(5); ctx.set_source_rgb(*L); ctx.arc(x, cy, r, 0, 2 * math.pi); ctx.stroke()
    ctx.set_line_width(1.5)
    for k in range(16):
        a = k * math.pi / 8 + t * .05; ctx.move_to(x, cy); ctx.line_to(x + r * math.cos(a), cy + r * math.sin(a))
    ctx.stroke()
    for k in range(24):
        a = k * math.pi / 12 + t * .05; px, py = x + (r + 10) * math.cos(a), cy + (r + 10) * math.sin(a)
        ctx.save(); ctx.translate(px, py); ctx.scale(1, .7); ctx.arc(0, 0, 9, 0, 2 * math.pi); ctx.restore(); sh(ctx, '#BFE3FF', 2)
    ctx.arc(x, cy, 14, 0, 2 * math.pi); sh(ctx, '#E6E9EE')


def tower_bridge(ctx, x, by):
    for s in (-1, 1):
        tx = x + s * 130
        rect(ctx, tx - 32, by - 230, 64, 230, '#D9CDB4')
        windows(ctx, tx - 32, by - 220, 64, 160, 2, 4, '#F3EBD2', 8)
        ctx.new_path(); ctx.move_to(tx - 36, by - 230); ctx.line_to(tx, by - 290); ctx.line_to(tx + 36, by - 230); ctx.close_path(); sh(ctx, '#6B7F8C')
        for d in (-26, 26):
            ctx.move_to(tx + d - 5, by - 230); ctx.line_to(tx + d, by - 252); ctx.line_to(tx + d + 5, by - 230); ctx.close_path(); sh(ctx, '#6B7F8C', 2)
        # suspension chain to the bank
        ctx.set_line_width(5); ctx.set_source_rgb(*hexc('#5FA8D3')); ctx.move_to(tx + s * 32, by - 150); ctx.curve_to(tx + s * 80, by - 60, tx + s * 140, by - 50, tx + s * 200, by - 70); ctx.stroke()
    rect(ctx, x - 98, by - 214, 196, 22, '#5FA8D3'); rect(ctx, x - 98, by - 190, 196, 12, '#5FA8D3')
    rect(ctx, x - 330, by - 70, 660, 16, '#5FA8D3')


def namsan_tower(ctx, x, by):
    ctx.new_path(); ctx.move_to(x - 420, by); ctx.curve_to(x - 240, by - 290, x + 220, by - 310, x + 440, by); ctx.close_path(); sh(ctx, '#8CC98C')
    for k in range(9):
        tx = x - 300 + k * 75; ty = by - 50 - 170 * math.sin(math.pi * (k + .5) / 9)
        ctx.arc(tx, ty, 22, 0, 2 * math.pi); sh(ctx, '#74B874', 2.5)
    top = by - 222
    rect(ctx, x - 14, top - 170, 28, 170, '#F1F3F7')
    rect(ctx, x - 36, top - 220, 72, 50, '#E8ECF2'); line(ctx, [(x - 36, top - 202), (x + 36, top - 202)], 2)
    rect(ctx, x - 26, top - 238, 52, 18, '#DDE3EC')
    rect(ctx, x - 5, top - 300, 10, 62, '#F1F3F7')
    line(ctx, [(x, top - 300), (x, top - 335)], 3)


def lotte_tower(ctx, x, by):
    ctx.new_path(); ctx.move_to(x - 52, by); ctx.curve_to(x - 50, by - 250, x - 34, by - 450, x - 8, by - 570)
    ctx.line_to(x + 8, by - 570); ctx.curve_to(x + 34, by - 450, x + 50, by - 250, x + 52, by); ctx.close_path(); sh(ctx, '#D7E2EE')
    line(ctx, [(x, by), (x, by - 560)], 2)
    for q in range(1, 9): w = 52 - q * 5; line(ctx, [(x - w, by - q * 60), (x + w, by - q * 60)], 1.5)


def gwanghwamun(ctx, x, by):
    rect(ctx, x - 190, by - 110, 380, 110, '#D9D2C2')
    for dx in (-110, 0, 110):
        ctx.new_path(); ctx.move_to(x + dx - 26, by); ctx.line_to(x + dx - 26, by - 52); ctx.curve_to(x + dx - 26, by - 86, x + dx + 26, by - 86, x + dx + 26, by - 52); ctx.line_to(x + dx + 26, by); ctx.close_path(); sh(ctx, '#5C4436')
    rect(ctx, x - 140, by - 170, 280, 60, '#C8463A')
    for k in range(8): line(ctx, [(x - 130 + k * 37, by - 170), (x - 130 + k * 37, by - 110)], 2.5)
    def roof(y, hw, lift):
        ctx.new_path(); ctx.move_to(x - hw - 30, y - lift); ctx.curve_to(x - hw, y + 4, x - hw * .5, y - 26, x, y - 30)
        ctx.curve_to(x + hw * .5, y - 26, x + hw, y + 4, x + hw + 30, y - lift); ctx.line_to(x + hw - 30, y - 50); ctx.line_to(x - hw + 30, y - 50); ctx.close_path(); sh(ctx, '#4E5A63')
    roof(by - 166, 200, 14)
    rect(ctx, x - 100, by - 236, 200, 40, '#C8463A')
    roof(by - 232, 140, 12)


def pearl_tower(ctx, x, by):
    for s in (-1, 0, 1):
        line(ctx, [(x + s * 70, by), (x + s * 14, by - 150)], 9, '#E6E9EE'); line(ctx, [(x + s * 70, by), (x + s * 14, by - 150)], 2)
    for s in (-1, 1): line(ctx, [(x + s * 14, by - 150), (x + s * 10, by - 380)], 8, '#E6E9EE')
    line(ctx, [(x - 14, by - 150), (x - 10, by - 380)], 2); line(ctx, [(x + 14, by - 150), (x + 10, by - 380)], 2)
    ctx.arc(x, by - 190, 64, 0, 2 * math.pi); sh(ctx, '#E4789A')
    for s in (-1, 1): ctx.arc(x + s * 40, by - 300, 12, 0, 2 * math.pi); sh(ctx, '#E4789A', 2.5)
    ctx.arc(x, by - 400, 38, 0, 2 * math.pi); sh(ctx, '#E4789A')
    rect(ctx, x - 7, by - 470, 14, 30, '#E6E9EE'); ctx.arc(x, by - 478, 12, 0, 2 * math.pi); sh(ctx, '#E4789A', 2.5)
    line(ctx, [(x, by - 490), (x, by - 560)], 3)


def shanghai_tower(ctx, x, by):
    ctx.new_path(); ctx.move_to(x - 58, by); ctx.curve_to(x - 56, by - 300, x - 40, by - 500, x - 16, by - 620)
    ctx.line_to(x + 22, by - 600); ctx.curve_to(x + 44, by - 480, x + 58, by - 300, x + 58, by); ctx.close_path(); sh(ctx, '#BFD3E3')
    ctx.set_line_width(2); ctx.set_source_rgb(*L); ctx.move_to(x - 20, by); ctx.curve_to(x + 40, by - 200, x - 30, by - 420, x + 10, by - 610); ctx.stroke()


def swfc(ctx, x, by):
    ctx.new_path(); ctx.move_to(x - 54, by); ctx.line_to(x - 46, by - 500); ctx.line_to(x - 18, by - 560); ctx.line_to(x + 18, by - 560); ctx.line_to(x + 46, by - 500); ctx.line_to(x + 54, by); ctx.close_path(); sh(ctx, '#C9D6E6')
    ctx.new_path(); ctx.move_to(x - 22, by - 470); ctx.line_to(x + 22, by - 470); ctx.line_to(x + 14, by - 530); ctx.line_to(x - 14, by - 530); ctx.close_path(); sh(ctx, '#9CC3E8')
    for q in range(1, 9): line(ctx, [(x - 50, by - q * 52), (x + 50, by - q * 52)], 1.5)


def jinmao(ctx, x, by):
    y = by; w = 50
    for k in range(9):
        h = 52 - k * 3; rect(ctx, x - w, y - h, 2 * w, h, '#A9B8C9', 2.5); y -= h; w -= 4.5
    ctx.new_path(); ctx.move_to(x - w, y); ctx.line_to(x, y - 60); ctx.line_to(x + w, y); ctx.close_path(); sh(ctx, '#A9B8C9')
    line(ctx, [(x, y - 60), (x, y - 110)], 3)


def fuji(ctx, x, by):
    ctx.new_path(); ctx.move_to(x - 520, by); ctx.curve_to(x - 260, by - 120, x - 90, by - 250, x - 50, by - 270); ctx.line_to(x + 50, by - 270)
    ctx.curve_to(x + 90, by - 250, x + 260, by - 120, x + 520, by); ctx.close_path(); sh(ctx, '#A9C1E3')
    ctx.new_path(); ctx.move_to(x - 50, by - 270); ctx.line_to(x + 50, by - 270); ctx.line_to(x + 110, by - 200); ctx.line_to(x + 70, by - 210); ctx.line_to(x + 40, by - 185)
    ctx.line_to(x + 5, by - 212); ctx.line_to(x - 30, by - 188); ctx.line_to(x - 66, by - 214); ctx.line_to(x - 110, by - 200); ctx.close_path(); sh(ctx, '#FFFFFF')


def skytree(ctx, x, by):
    ctx.new_path(); ctx.move_to(x - 46, by); ctx.curve_to(x - 30, by - 250, x - 14, by - 450, x - 8, by - 640); ctx.line_to(x + 8, by - 640)
    ctx.curve_to(x + 14, by - 450, x + 30, by - 250, x + 46, by); ctx.close_path(); sh(ctx, '#EEF2F7')
    for q in range(1, 12): w = 44 - q * 3; line(ctx, [(x - w, by - q * 34), (x + w, by - q * 34)], 1.2)
    rect(ctx, x - 30, by - 400, 60, 24, '#DDE6F2'); rect(ctx, x - 22, by - 500, 44, 16, '#DDE6F2')
    line(ctx, [(x, by - 640), (x, by - 690)], 3)


# ------------------------------------------------------------------ street facades (mid layer)
def facade(ctx, kind, x, w, h, rnd, t):
    by = BASE_MID; top = by - h
    if kind == 'paris':
        rect(ctx, x, top, w, h, '#F2E6CF')
        ctx.new_path(); ctx.move_to(x - 4, top); ctx.line_to(x + 14, top - 40); ctx.line_to(x + w - 14, top - 40); ctx.line_to(x + w + 4, top); ctx.close_path(); sh(ctx, '#8D9DB0')
        for i in range(max(1, int(w // 50))): rect(ctx, x + 22 + i * 50, top - 34, 18, 22, '#FFFDF6', 2.5)
        windows(ctx, x, top + 6, w, h - 70, max(2, int(w // 46)), max(2, int((h - 70) // 52)), '#BFD5EA', 8)
        for f in range(1, max(2, int((h - 70) // 52))): line(ctx, [(x + 6, top + 6 + f * 52 - 2), (x + w - 6, top + 6 + f * 52 - 2)], 3)
        aw = rnd.choice(['#C8463A', '#2E6E5E', '#2B3A67'])
        rect(ctx, x + 6, by - 62, w - 12, 62, '#EADBC0')
        ctx.new_path(); ctx.move_to(x + 2, by - 66); ctx.line_to(x + w - 2, by - 66); ctx.line_to(x + w - 10, by - 44); ctx.line_to(x + 10, by - 44); ctx.close_path(); sh(ctx, aw)
        for i in range(int((w - 20) // 16)): ctx.rectangle(x + 12 + i * 16, by - 64, 8, 18); ctx.set_source_rgba(1, 1, 1, .7); ctx.fill()
    elif kind == 'london':
        col = rnd.choice(['#C8664A', '#B85C45', '#D07A5A', '#EFE6D6'])
        rect(ctx, x, top, w, h, col)
        for cx_ in (x + 18, x + w - 34): rect(ctx, cx_, top - 26, 16, 26, col, 2.5)
        cols = max(2, int(w // 52)); rows = max(2, int((h - 60) // 60))
        windows(ctx, x, top + 4, w, h - 64, cols, rows, '#FFFFFF', 10, 22, 34)
        rect(ctx, x + w / 2 - 14, by - 56, 28, 56, rnd.choice(['#1F2340', '#2E6E5E', '#C8463A']))
        ctx.arc(x + w / 2, by - 58, 14, math.pi, 0); sh(ctx, '#FFFFFF', 2.5)
    elif kind == 'seoul':
        col = rnd.choice(['#E7EDF5', '#F4E3D2', '#DDEBE2', '#F1F1EC', '#D9E4F5'])
        rect(ctx, x, top, w, h, col)
        for f in range(int((h - 50) // 40)): rect(ctx, x + 10, top + 12 + f * 40, w - 20, 22, '#BFD5EA', 2.5)
        rect(ctx, x + 8, by - 48, w - 16, 48, '#FFFDF6')
        sc = rnd.choice(['#FF7A6B', '#2EC4A6', '#FFB21A', '#7B8CFF'])
        rect(ctx, x + w - 34, top + 16, 22, min(100, h - 70), sc, 2.5)
    elif kind == 'shanghai':
        col = rnd.choice(['#E8DCC2', '#DCCFB3', '#EDE4D0'])
        rect(ctx, x, top, w, h, col)
        for i in range(int((w - 20) // 30) + 1): line(ctx, [(x + 14 + i * 30, top + 40), (x + 14 + i * 30, by - 60)], 5, '#F7F1E4')
        windows(ctx, x, top + 30, w, h - 100, max(2, int(w // 40)), max(2, int((h - 100) // 50)), '#BFD5EA', 8, 14, 26)
        rect(ctx, x - 4, top, w + 8, 16, '#D2C4A6')
        if w > 170: ctx.arc(x + w / 2, top - 2, 34, math.pi, 0); sh(ctx, '#7FA79A')
        rect(ctx, x + w / 2 - 22, by - 60, 44, 60, '#6B4E3D')
    elif kind == 'tokyo':
        col = rnd.choice(['#F6EEE2', '#E4EEF4', '#F2E4E4', '#E9F0E1', '#FFF6DE'])
        rect(ctx, x, top, w, h, col)
        for f in range(int((h - 70) // 46)):
            rect(ctx, x + 10, top + 12 + f * 46, w - 20, 26, '#BFD5EA', 2.5); line(ctx, [(x + 6, top + 42 + f * 46), (x + w - 6, top + 42 + f * 46)], 3)
        rect(ctx, x + 6, by - 54, w - 12, 54, '#FFFDF6')
        nc = rnd.choice(['#2B3A67', '#C8463A', '#2E6E5E'])
        for i in range(3): rect(ctx, x + 14 + i * (w - 28) / 3, by - 54, (w - 28) / 3 - 4, 22, nc, 2.5)
        rect(ctx, x + w - 24, top + 20, 16, min(120, h - 80), rnd.choice(['#FF7A6B', '#FFB21A', '#2EC4A6']), 2.5)


# ------------------------------------------------------------------ near props and vehicles
def tree(ctx, x, col='#7CC47F', r=60, h=150):
    line(ctx, [(x, GY), (x, GY - h + 30)], 8, '#8A5A3C')
    for dx, dy, rr in ((0, -h, r), (-r * .6, -h + 22, r * .7), (r * .6, -h + 22, r * .7)): ctx.arc(x + dx, GY + dy, rr, 0, 2 * math.pi); sh(ctx, col)


def lamp(ctx, x, col='#2B2541', ornate=False):
    line(ctx, [(x, GY), (x, GY - 190)], 6, col)
    if ornate:
        ctx.new_path(); ctx.move_to(x - 16, GY - 190); ctx.line_to(x + 16, GY - 190); ctx.line_to(x + 10, GY - 222); ctx.line_to(x - 10, GY - 222); ctx.close_path(); sh(ctx, '#FFF4C2')
        rect(ctx, x - 14, GY - 230, 28, 8, col, 2)
    else:
        line(ctx, [(x, GY - 190), (x + 40, GY - 196)], 5, col); ctx.arc(x + 44, GY - 190, 9, 0, 2 * math.pi); sh(ctx, '#FFF4C2', 2.5)


def phone_box(ctx, x):
    rect(ctx, x - 26, GY - 150, 52, 150, '#D9372B'); rect(ctx, x - 30, GY - 162, 60, 14, '#D9372B')
    windows(ctx, x - 26, GY - 140, 52, 110, 2, 4, '#E9F4FF', 6, 16, 18)


def post_box(ctx, x):
    rect(ctx, x - 16, GY - 80, 32, 80, '#D9372B'); ctx.arc(x, GY - 80, 16, math.pi, 0); sh(ctx, '#D9372B'); rect(ctx, x - 9, GY - 66, 18, 4, '#1F2340', 2)


def cafe_table(ctx, x):
    line(ctx, [(x, GY), (x, GY - 120)], 4)
    ctx.new_path(); ctx.move_to(x - 60, GY - 110); ctx.curve_to(x - 40, GY - 140, x + 40, GY - 140, x + 60, GY - 110); ctx.close_path(); sh(ctx, '#C8463A')
    rect(ctx, x - 26, GY - 48, 52, 6, '#FFFFFF', 2.5); line(ctx, [(x - 20, GY - 42), (x - 24, GY)], 3); line(ctx, [(x + 20, GY - 42), (x + 24, GY)], 3)


def flower_stall(ctx, x):
    rect(ctx, x - 60, GY - 60, 120, 60, '#C68B59')
    for i in range(7): ctx.arc(x - 48 + i * 16, GY - 66, 9, 0, 2 * math.pi); sh(ctx, ['#FF5C8A', '#FFB21A', '#FFFFFF', '#9B7BFF'][i % 4], 2)


def bus_stop(ctx, x):
    rect(ctx, x - 70, GY - 150, 140, 12, '#3D9BFF'); line(ctx, [(x - 60, GY), (x - 60, GY - 140)], 5); line(ctx, [(x + 60, GY), (x + 60, GY - 140)], 5)
    rect(ctx, x - 46, GY - 120, 30, 70, '#E9F4FF', 2.5); rect(ctx, x - 50, GY - 40, 100, 8, '#D9A066', 2.5)


def lanterns(ctx, x0, x1, t):
    line(ctx, [(x0, GY - 230), (x0, GY)], 5); line(ctx, [(x1, GY - 230), (x1, GY)], 5)
    ctx.set_line_width(2); ctx.set_source_rgb(*L); ctx.move_to(x0, GY - 220); ctx.curve_to(x0 + (x1 - x0) * .3, GY - 180, x0 + (x1 - x0) * .7, GY - 180, x1, GY - 220); ctx.stroke()
    for k in range(1, 6):
        u = k / 6; lx = x0 + (x1 - x0) * u; ly = GY - 220 + 4 * 30 * u * (1 - u) * 1.33 + 14 + 2 * math.sin(t * 2 + k)
        ctx.save(); ctx.translate(lx, ly); ctx.scale(1, .8); ctx.arc(0, 0, 14, 0, 2 * math.pi); ctx.restore(); sh(ctx, '#E0453A', 2.5)
        rect(ctx, lx - 6, ly + 10, 12, 5, '#FFB21A', 1.5)


def util_pole(ctx, x, x_next):
    line(ctx, [(x, GY), (x, GY - 300)], 9, '#9AA0A8'); line(ctx, [(x, GY), (x, GY - 300)], 2)
    for dy in (-280, -250): line(ctx, [(x - 30, GY + dy), (x + 30, GY + dy)], 4)
    ctx.set_line_width(1.6); ctx.set_source_rgb(*L)
    for dy in (-280, -250, -240):
        ctx.move_to(x + 24, GY + dy); ctx.curve_to(x + 200, GY + dy + 26, x_next - 200, GY + dy + 26, x_next - 24, GY + dy)
    ctx.stroke()


def vending(ctx, x):
    rect(ctx, x - 30, GY - 130, 60, 130, '#E9F2FA'); rect(ctx, x - 22, GY - 120, 44, 54, '#FFFFFF', 2.5)
    for i in range(3):
        for j in range(2): rect(ctx, x - 18 + i * 13, GY - 114 + j * 24, 9, 18, ['#FF7A6B', '#2EC4A6', '#FFB21A'][i], 1.5)
    rect(ctx, x - 20, GY - 40, 40, 14, '#2B2541', 2)


def vehicle(ctx, kind, x, by, t):
    ang = t * 9
    if kind == 'double':
        rect(ctx, x, by - 190, 300, 170, '#D9372B'); ctx.new_path()
        for row in (0, 1):
            for i in range(6): rect(ctx, x + 16 + i * 46, by - 176 + row * 76, 36, 44, '#E9F4FF', 2.5)
        rect(ctx, x + 2, by - 108, 296, 8, '#FFFFFF', 2)
        for wx in (x + 60, x + 240): mob.wheel(ctx, wx, by - 20, 24, ang, L)
    elif kind in ('cab', 'taxi', 'car', 'tokyo_taxi'):
        col = {'cab': '#2B2541', 'taxi': '#E0453A', 'car': '#F2E6CF', 'tokyo_taxi': '#2E8B57'}[kind]
        ctx.new_path(); ctx.move_to(x, by - 24); ctx.line_to(x, by - 70); ctx.line_to(x + 40, by - 76); ctx.line_to(x + 64, by - 120); ctx.line_to(x + 150, by - 120); ctx.line_to(x + 172, by - 76); ctx.line_to(x + 210, by - 70); ctx.line_to(x + 210, by - 24); ctx.close_path(); sh(ctx, col)
        rect(ctx, x + 70, by - 112, 36, 32, '#E9F4FF', 2.5); rect(ctx, x + 112, by - 112, 34, 32, '#E9F4FF', 2.5)
        if kind in ('taxi', 'tokyo_taxi'): rect(ctx, x + 92, by - 134, 30, 14, '#FFD86B', 2.5)
        for wx in (x + 46, x + 166): mob.wheel(ctx, wx, by - 20, 20, ang, L)
    elif kind == 'seoul_bus':
        rect(ctx, x, by - 150, 330, 130, '#2F8FD8')
        for i in range(6): rect(ctx, x + 14 + i * 50, by - 136, 40, 50, '#E9F4FF', 2.5)
        rect(ctx, x + 2, by - 76, 326, 10, '#FFFFFF', 2)
        for wx in (x + 60, x + 270): mob.wheel(ctx, wx, by - 20, 24, ang, L)


# ------------------------------------------------------------------ city definitions
CITIES = {
    'seoul': dict(label='SEOUL', sky=('#5AAEF0', '#E6F4FF'), ground='#F1D9CF', road='#C3C7CF', far=lambda c, sc, t: (
        namsan_tower(c, 520 - sc * .06, BASE_FAR), lotte_tower(c, 1480 - sc * .06, BASE_FAR)),
        special=('gwang', 1500), near='seoul', vehicles=['seoul_bus', 'car']),
    'paris': dict(label='PARIS', sky=('#8EC5F0', '#FFF1E0'), ground='#E3DCCF', road='#BDB8B0', far=lambda c, sc, t: (
        eiffel(c, 1180 - sc * .06, BASE_FAR, 560), arc_triomphe(c, 420 - sc * .06, BASE_FAR)),
        special=None, near='paris', vehicles=['car', 'car']),
    'london': dict(label='LONDON', sky=('#9FB9D6', '#EEF2F6'), ground='#D7D9DE', road='#B4B8C0', far=lambda c, sc, t: (
        london_eye(c, 1500 - sc * .06, BASE_FAR, t), tower_bridge(c, 320 - sc * .06, BASE_FAR), big_ben(c, 1010 - sc * .06, BASE_FAR)),
        special=None, near='london', vehicles=['double', 'cab']),
    'shanghai': dict(label='SHANGHAI', sky=('#F0B58A', '#FFF0DA'), ground='#DDD6CA', road='#BEB9B2', far=lambda c, sc, t: (
        jinmao(c, 1260 - sc * .06, BASE_FAR), swfc(c, 1420 - sc * .06, BASE_FAR), shanghai_tower(c, 1580 - sc * .06, BASE_FAR), pearl_tower(c, 860 - sc * .06, BASE_FAR)),
        special=None, near='shanghai', vehicles=['taxi', 'car']),
    'tokyo': dict(label='TOKYO', sky=('#9CC8F2', '#FFE9EF'), ground='#E2E4E8', road='#BCC0C8', far=lambda c, sc, t: (
        fuji(c, 400 - sc * .03, BASE_FAR), skytree(c, 1560 - sc * .06, BASE_FAR), eiffel(c, 1000 - sc * .06, BASE_FAR, 500, '#F0642A', '#FFFFFF')),
        special=None, near='tokyo', vehicles=['tokyo_taxi', 'car']),
}
C = CITIES[CITY]
rnd = random.Random({'seoul': 1, 'paris': 2, 'london': 3, 'shanghai': 4, 'tokyo': 5}[CITY])
MID = []
x = -300
while x < 4200:
    w = rnd.choice([150, 170, 190, 210, 230]); h = rnd.choice([120, 135, 150, 165, 180])
    if C['special'] and abs(x - C['special'][1]) < 200 and not any(m[0] == 'special' for m in MID):
        MID.append(('special', x + 200, 0, 0, random.Random(0))); x += 420; continue
    MID.append((C['near'], x, w, h, random.Random(rnd.random())))
    x += w + rnd.choice([0, 20, 60, 140])
NEAR = []
x = 300
items = {'paris': ['lamp_o', 'cafe', 'tree', 'flower', 'lamp_o', 'tree'], 'london': ['lamp', 'phone', 'tree', 'post', 'lamp', 'tree'],
         'seoul': ['tree', 'lamp', 'busstop', 'tree', 'lamp'], 'shanghai': ['lantern', 'tree', 'lamp', 'lantern', 'tree'],
         'tokyo': ['pole', 'vending', 'sakura', 'pole', 'lamp', 'sakura']}[CITY]
k = 0
while x < 5600:
    NEAR.append((items[k % len(items)], x)); x += rnd.choice([260, 320, 380]); k += 1
PEDS = [(rnd.uniform(0, 4000), rnd.choice([-1, 1]), rnd.uniform(40, 70), dict(skin=rnd.randrange(4), hair=rnd.randrange(5), top=rnd.choice(['#FF7A45', '#9B7BFF', '#2EC4A6', '#FFB21A', '#E0457B', '#7FC8F8']), bottom='#3E4A6B', style=rnd.choice(['short', 'long', 'bun', 'cap']))) for _ in range(16)]


def scene(t):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); ctx = cairo.Context(s)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    sc = SPEED * t
    R.sky(ctx, *C['sky']); R.sun(ctx, 1700, 140)
    for cx_, cy_, cs in ((420, 150, .9), (1150, 210, 1.1), (1850, 110, .8)): R.cloud(ctx, (cx_ - 12 * t) % 2300 - 180, cy_, cs)
    C['far'](ctx, sc, t)
    # mid street facades
    for kind, x, w, h, r in MID:
        X = x - sc * .45
        if X < -500 or X > W + 300: continue
        if kind == 'special': gwanghwamun(ctx, X, BASE_MID)
        else: facade(ctx, kind, X, w, h, random.Random(r.random()), t)
    # far pavement + people
    ctx.rectangle(0, BASE_MID, W, 14); sh(ctx, C['ground'], 3)
    for x0, d, v, look in PEDS:
        X = (x0 - sc * .45 + d * v * t) % 4400 - 300
        RT.figure(ctx, X, BASE_MID + 14, t * 6 + x0, look, face=d, s=.5)
    # road
    ctx.rectangle(0, BASE_MID + 14, W, GY - BASE_MID - 14); ctx.set_source_rgb(*hexc(C['road'])); ctx.fill()
    ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(5)
    off = sc * .75 % 120
    for i in range(-1, 18): ctx.move_to(i * 120 - off, 728); ctx.line_to(i * 120 - off + 60, 728)
    ctx.stroke()
    for i, kind in enumerate(C['vehicles']):
        X = (1800 + i * 1500 - t * (SPEED * .75 + 160)) % 3400 - 600
        vehicle(ctx, kind, X, 748, t)
    # near props
    for i, (it, x) in enumerate(NEAR):
        X = x - sc
        if X < -300 or X > W + 300: continue
        if it == 'tree': tree(ctx, X, '#7CC47F' if CITY != 'seoul' else '#9BCB6E')
        elif it == 'sakura': tree(ctx, X, '#F7B6C8')
        elif it == 'lamp': lamp(ctx, X)
        elif it == 'lamp_o': lamp(ctx, X, '#2B3A3A', True)
        elif it == 'cafe': cafe_table(ctx, X)
        elif it == 'flower': flower_stall(ctx, X)
        elif it == 'phone': phone_box(ctx, X)
        elif it == 'post': post_box(ctx, X)
        elif it == 'busstop': bus_stop(ctx, X)
        elif it == 'lantern': lanterns(ctx, X, X + 240, t)
        elif it == 'vending': vending(ctx, X)
        elif it == 'pole':
            nx = next((x2 for it2, x2 in NEAR[i + 1:] if it2 == 'pole'), x + 700) - sc
            util_pole(ctx, X, nx)
    # front pavement
    ctx.rectangle(0, GY, W, H - GY); sh(ctx, C['ground'], 3)
    ctx.set_line_width(1.5); ctx.set_source_rgba(*L, .25)
    po = sc % 80
    for i in range(-1, 26): ctx.move_to(i * 80 - po, GY); ctx.line_to(i * 80 - po - 30, GY + 60)
    ctx.stroke()
    # Haru on the bike
    ctx.save(); ctx.translate(CX, GY); mob.bike(ctx, t, mob.OUTFITS['bike'], L); ctx.restore()
    a = np.ndarray((H, W, 4), np.uint8, s.get_data()); im = Image.fromarray(a[..., [2, 1, 0]].copy())
    R.ui(im, f'TEST · {C["label"]}', (80, 170, 110)); return im


mob.O.clear(); mob.O.update(mob.OUTFITS['bike'])
if __name__ == '__main__':
    out = ARGV[2]
    if out.endswith('.png'):
        scene(float(ARGV[3]) if len(ARGV) > 3 else 3.0).save(out); sys.exit()
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f in range(int(10 * FPS)): p.stdin.write(scene(f / FPS).tobytes())
    p.stdin.close(); p.wait(); print('done', out)
