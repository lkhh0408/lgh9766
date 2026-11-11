"""Lyric set pieces: townspeople and props that act out a lyric line when it is sung.

Every piece is drawn around its world position with `dt` = seconds since its lyric line started,
so actions (waving, watering, ringing a bell, a window swinging open) happen in time with the song.
"""
import math
import cairo

def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))
def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

def shape(ctx, fill, L):
    ctx.set_source_rgb(*fill); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.stroke()

# width of each piece in world px (base scenery is cleared under it)
WIDTH = {'waterer': 380, 'baker': 420, 'tall_trees': 620, 'cyclist': 520, 'rooftop': 360, 'pianist': 320,
         'terrace': 560, 'friend_window': 380, 'banner': 760, 'kettle_window': 380, 'golden_neon': 440,
         'neighbors_wave': 480, 'note_door': 300, 'sip_terrace': 460, 'alarm_window': 320, 'sneaker_shop': 400,
         'windows_open': 560, 'corner_lady': 420, 'sign': 420}

SKINS = [(1, .9, .8), (.96, .8, .66), (.85, .66, .5), (.67, .5, .38)]
HAIRS = [hexc('#3B2A22'), hexc('#1E1B1A'), hexc('#8A5A3C'), hexc('#C98A4B'), hexc('#5B5F6B')]

def npc(ctx, x, gy, t, L, look, pose='stand', face=-1, s=0.92, dt=0.0, nf=lambda c: c):
    """A townsperson in the same line-art style (no glasses, so the mascot stays unique).
    look: dict(skin, hair, top, style) ; face=-1 looks left (toward the walker)."""
    skin, hair, top = SKINS[look.get('skin', 0)], HAIRS[look.get('hair', 0)], hexc(look.get('top', '#3D9BFF'))
    ctx.save(); ctx.translate(x, gy); ctx.scale(s * face * -1, s)   # drawn facing +x, mirrored by face
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    sit = pose in ('sit', 'piano', 'sip')
    hip_y = -52 if sit else -78
    # legs
    ctx.set_line_width(12); ctx.set_source_rgb(*nf(hexc(look.get('bottom', '#4A4F66'))))
    if sit:
        ctx.move_to(-4, hip_y); ctx.line_to(26, hip_y); ctx.line_to(26, 0); ctx.stroke()
    elif pose != 'ride':
        ctx.move_to(-4, hip_y); ctx.line_to(-8, 0); ctx.move_to(6, hip_y); ctx.line_to(10, 0); ctx.stroke()
    # body
    ctx.set_line_width(3.5)
    ctx.move_to(-20, hip_y + 6); ctx.curve_to(-22, hip_y - 40, -16, hip_y - 64, 2, hip_y - 66)
    ctx.curve_to(20, hip_y - 64, 24, hip_y - 40, 22, hip_y + 6); ctx.close_path(); shape(ctx, nf(top), L)
    # head
    hx, hy, R = 2, hip_y - 96, 30
    ctx.arc(hx, hy, R, 0, 2 * math.pi); shape(ctx, nf(skin), L)
    ctx.save(); ctx.arc(hx, hy, R + 1, 0, 2 * math.pi); ctx.clip()
    st = look.get('style', 'short')
    ctx.move_to(hx + R + 4, hy - 14); ctx.curve_to(hx + 10, hy - 26, hx - 8, hy - 18, hx - 10, hy - 2)
    ctx.line_to(hx - 12, hy + (R if st == 'long' else 12)); ctx.line_to(hx - R - 6, hy + R + 6); ctx.line_to(hx - R - 6, hy - R - 6); ctx.line_to(hx + R + 6, hy - R - 6); ctx.close_path()
    ctx.set_source_rgb(*nf(hair)); ctx.fill(); ctx.restore()
    ctx.set_source_rgb(*L); ctx.arc(hx, hy, R, 0, 2 * math.pi); ctx.stroke()
    if st == 'bun': ctx.arc(hx - 22, hy - 24, 12, 0, 2 * math.pi); shape(ctx, nf(hair), L)
    if st == 'long':
        ctx.move_to(hx - 24, hy - 4); ctx.curve_to(hx - 34, hy + 20, hx - 26, hy + 40, hx - 14, hy + 44); ctx.line_to(hx - 10, hy + 10); ctx.close_path(); shape(ctx, nf(hair), L)
    if look.get('hat') == 'chef':
        ctx.rectangle(hx - 22, hy - 44, 44, 18); shape(ctx, nf((1, 1, 1)), L)
        for dx in (-14, 0, 14): ctx.arc(hx + dx, hy - 50, 14, 0, 2 * math.pi); shape(ctx, nf((1, 1, 1)), L)
    ctx.arc(hx + 14, hy, 3.2, 0, 2 * math.pi); ctx.fill()                                   # eye
    ctx.set_line_width(2.5); ctx.arc(hx + 18, hy + 12, 6, math.radians(10), math.radians(120)); ctx.stroke()
    ctx.set_source_rgba(1, .45, .55, .4); ctx.arc(hx + 10, hy + 14, 5, 0, 2 * math.pi); ctx.fill(); ctx.set_source_rgb(*L)
    # arms
    sx_, sy_ = 2, hip_y - 56
    ctx.set_line_width(10); ctx.set_source_rgb(*nf(top))
    def arm(a1, a2, l1=26, l2=24):
        x1, y1 = sx_ + l1 * math.sin(a1), sy_ + l1 * math.cos(a1); x2, y2 = x1 + l2 * math.sin(a2), y1 + l2 * math.cos(a2)
        ctx.move_to(sx_, sy_); ctx.line_to(x1, y1); ctx.line_to(x2, y2); ctx.stroke(); return x2, y2
    if pose == 'wave' or (pose == 'counter' and 0 < dt < 6):
        sw = math.sin(t * 7) * 0.45
        arm(math.radians(150), math.radians(170) + sw)
    elif pose == 'water':
        hx2, hy2 = arm(math.radians(70), math.radians(95))
        ctx.set_line_width(3.5); ctx.set_source_rgb(*L)
        tilt = 0.25 + 0.15 * sm(dt / 1.0)
        ctx.save(); ctx.translate(hx2 + 4, hy2); ctx.rotate(tilt)
        ctx.rectangle(-4, -14, 34, 26); shape(ctx, nf(hexc('#7FC8A9')), L)
        ctx.move_to(30, -6); ctx.line_to(56, -20); ctx.stroke(); ctx.restore()
    elif pose == 'piano':
        arm(math.radians(75), math.radians(100) + 0.15 * math.sin(t * 9))
    elif pose == 'sip':
        cx_, cy_ = arm(math.radians(40), math.radians(170) + 0.3 * sm(math.sin(t * 0.8)))
        ctx.set_line_width(3); ctx.rectangle(cx_ - 4, cy_ - 16, 16, 18); shape(ctx, nf((1, 1, 1)), L)
    else:
        arm(math.radians(8), math.radians(-8))
    ctx.restore()

def string_lights(ctx, x0, x1, y, sag, t, L, alpha=1.0):
    ctx.set_source_rgba(*L, alpha); ctx.set_line_width(2)
    ctx.move_to(x0, y); ctx.curve_to(x0 + (x1 - x0) * .33, y + sag, x0 + (x1 - x0) * .66, y + sag, x1, y); ctx.stroke()
    cols = [hexc(c) for c in ('#FFD34D', '#FF5C8A', '#7FE3C4', '#FF9A3D')]
    n = max(3, int((x1 - x0) // 34))
    for i in range(1, n):
        u = i / n; bx = x0 + (x1 - x0) * u; by = y + sag * 4 * u * (1 - u) * 0.75 + 8
        tw = 0.6 + 0.4 * math.sin(t * 4 + i)
        ctx.set_source_rgba(*cols[i % 4], alpha * tw); ctx.arc(bx, by, 6, 0, 2 * math.pi); ctx.fill()

def neon_text(ctx, text, cx, y, size, col, t, alpha=1.0):
    ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(size)
    e = ctx.text_extents(text); x = cx - e.width / 2
    flick = 0.85 + 0.15 * math.sin(t * 13) * math.sin(t * 3.1)
    for r, a in ((10, .12), (5, .25)):
        ctx.set_line_width(r); ctx.set_source_rgba(*col, a * alpha * flick); ctx.move_to(x, y); ctx.text_path(text); ctx.stroke()
    ctx.set_source_rgba(1, 1, 1, alpha); ctx.move_to(x, y); ctx.show_text(text)

def draw_piece(ctx, name, sx, GY, t, dt, L, night, nf, opts, draw_obj, wx):
    """Draw piece `name` whose left edge is at screen x `sx`. dt = seconds since its lyric line."""
    W_ = WIDTH.get(name, 400)
    acc = hexc(opts.get('color', '#FF5C8A'))
    lit = lambda: (ctx.set_source_rgba(1, .85, .45, min(1, night * 1.4)), ctx.fill_preserve()) if night > .3 else None
    ctx.set_line_width(3); ctx.set_source_rgb(*L)
    if name == 'waterer':
        draw_obj(ctx, ('house2', wx, 190, 150, hexc('#FFE3EC'), acc, 'flowerbox'), sx, L, night, t)
        draw_obj(ctx, ('flowers', wx + 210, 6), sx + 210, L, night, t)
        npc(ctx, sx + 340, GY, t, L, dict(skin=1, hair=3, top='#7FC8A9', style='bun'), 'water', face=1, dt=dt, nf=nf)
        if dt > 0:                         # arcs of water catching gold
            for i in range(8):
                ph = (t * 1.3 + i / 8) % 1
                px = sx + 300 - 90 * ph; py = GY - 120 + 160 * ph * ph - 40 * ph
                ctx.set_source_rgba(.45, .75, 1, .9 * (1 - ph)); ctx.arc(px, py, 4, 0, 2 * math.pi); ctx.fill()
                if i % 3 == 0: ctx.set_source_rgba(1, .85, .3, (1 - ph) * (1 - night)); ctx.arc(px + 6, py - 6, 3, 0, 2 * math.pi); ctx.fill()
    elif name == 'baker':
        draw_obj(ctx, ('shop', wx, 400, opts.get('sign', 'BAKERY'), hexc('#FFF1DC'), acc, 'bread'), sx, L, night, t)
        ctx.save(); ctx.rectangle(sx + 30, GY - 120, 180, 90); ctx.clip()
        npc(ctx, sx + 120, GY + 40, t, L, dict(skin=0, hair=1, top='#FFFFFF', hat='chef'), 'counter', face=-1, s=.75, dt=dt, nf=nf)
        ctx.restore()
        if dt > 1:                          # a smile drawn in the flour on the glass
            ctx.set_source_rgba(1, 1, 1, .9 * sm(dt - 1)); ctx.set_line_width(4)
            ctx.arc(sx + 170, GY - 84, 14, math.radians(20), math.radians(160)); ctx.stroke()
            for ex in (-6, 6): ctx.arc(sx + 170 + ex, GY - 92, 2.5, 0, 2 * math.pi); ctx.fill()
    elif name == 'tall_trees':
        for i, (dx, r, h) in enumerate(((70, 120, 250), (300, 135, 280), (530, 115, 240))):
            draw_obj(ctx, ('tree', wx + dx, r, h), sx + dx, L, night, t)
        # the two crowns meeting over the path
        ctx.set_source_rgba(1, .9, .4, .5 * (1 - night))
        for i in range(10):
            ph = (t * .5 + i / 10) % 1; ctx.arc(sx + 60 + i * 52, GY - 300 + 260 * ph, 3, 0, 2 * math.pi); ctx.fill()
    elif name == 'cyclist':
        draw_obj(ctx, ('zebra', wx, 420), sx, L, night, t)
        draw_obj(ctx, ('signal', wx + 470), sx + 470, L, night, t)
        # friend rides in from the right, rings the bell, passes the walker
        rx = sx + 900 - 260 * max(0.0, dt + 1.0)
        if -200 < rx - sx < 1400:
            draw_obj(ctx, ('bicycle', wx, acc), rx, L, night, t)
            npc(ctx, rx - 4, GY - 46, t, L, dict(skin=2, hair=0, top='#FF9A3D'), 'ride', face=-1, s=.8, dt=dt, nf=nf)
            if 0 < dt < 2.2:
                ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(30)
                ctx.set_source_rgb(*hexc('#FF5C8A')); ctx.move_to(rx + 20, GY - 250 - 10 * math.sin(t * 20)); ctx.show_text('RING!'); ctx.set_source_rgb(*L)
    elif name == 'rooftop':
        draw_obj(ctx, ('bldg', wx, 320, 300, 3, hexc('#E6E0FF')), sx, L, night, t)
        top = GY - 300
        string_lights(ctx, sx + 10, sx + 310, top - 120, 30, t, L)
        for px in (sx + 10, sx + 310): ctx.move_to(px, top); ctx.line_to(px, top - 122); ctx.stroke()
        ctx.rectangle(sx + 120, top - 50, 90, 10); shape(ctx, nf(hexc('#FFFFFF')), L)
        ctx.move_to(sx + 165, top - 40); ctx.line_to(sx + 165, top); ctx.stroke()
        npc(ctx, sx + 95, top, t, L, dict(skin=1, hair=2, top='#FF5C8A'), 'sit', face=1, s=.62, nf=nf)
        npc(ctx, sx + 235, top, t, L, dict(skin=3, hair=1, top='#3D9BFF', style='short'), 'sit', face=-1, s=.62, nf=nf)
    elif name == 'pianist':
        draw_obj(ctx, ('bldg', wx, 300, 340, 3, hexc('#FFE9C7')), sx, L, night, t)
        wx0, wy0 = sx + 70, GY - 250
        ctx.rectangle(wx0, wy0, 160, 110); shape(ctx, nf(hexc('#FFF8E8')), L)
        ctx.save(); ctx.rectangle(wx0, wy0, 160, 110); ctx.clip()
        ctx.rectangle(wx0 + 70, wy0 + 60, 90, 50); shape(ctx, nf(hexc('#2B2541')), L)       # upright piano
        for k in range(8): ctx.rectangle(wx0 + 72 + k * 11, wy0 + 60, 9, 12); shape(ctx, nf((1, 1, 1)), L)
        npc(ctx, wx0 + 52, wy0 + 120, t, L, dict(skin=0, hair=4, top='#7B3BFF', style='long'), 'piano', face=1, s=.55, nf=nf)
        ctx.restore()
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        for i in range(5):
            ph = (t * .5 + i / 5) % 1; ctx.set_font_size(30 + 10 * (i % 2)); ctx.set_source_rgba(*L, (1 - ph) * sm(dt + 1))
            ctx.move_to(wx0 + 150 + 120 * ph, wy0 + 10 - 120 * ph + 12 * math.sin(t * 2 + i)); ctx.show_text('♪' if i % 2 else '♫')
    elif name in ('terrace', 'sip_terrace'):
        if name == 'terrace': draw_obj(ctx, ('shop', wx, 330, opts.get('sign', 'CAFE'), hexc('#FFF1DC'), hexc('#FF8A3D'), 'cups'), sx, L, night, t)
        base = sx + (360 if name == 'terrace' else 40)
        for j in range(2 if name == 'terrace' else 1):
            tx = base + j * 110 if name == 'terrace' else base + 180
            draw_obj(ctx, ('table', wx, hexc('#FF8A3D')), tx, L, night, t)
            draw_obj(ctx, ('chair', wx, True), tx - 70, L, night, t)
            npc(ctx, tx - 50, GY, t, L, dict(skin=j % 4, hair=(j + 2) % 5, top=['#3D9BFF', '#2EC4A6'][j % 2], style=['short', 'long'][j % 2]), 'sip' if name == 'sip_terrace' else 'sit', face=1, s=.7, nf=nf)
    elif name == 'friend_window':
        draw_obj(ctx, ('shop', wx, 380, opts.get('sign', 'CAFE'), hexc('#E8F7F0'), acc, None), sx, L, night, t)
        ctx.save(); ctx.rectangle(sx + 30, GY - 120, 171, 90); ctx.clip()
        npc(ctx, sx + 110, GY + 10, t, L, dict(skin=2, hair=0, top='#FF9A3D'), 'wave' if dt > 0 else 'stand', face=-1, s=.7, dt=dt, nf=nf)
        ctx.restore()
    elif name == 'banner':
        y = GY - 330 + 6 * math.sin(t * 1.4)
        for px in (sx, sx + W_): ctx.move_to(px, GY); ctx.line_to(px, GY - 360); ctx.stroke()
        ctx.move_to(sx, GY - 350); ctx.curve_to(sx + W_ * .3, y - 30, sx + W_ * .7, y - 30, sx + W_, GY - 350); ctx.stroke()
        bw = W_ - 120; bx = sx + 60
        ctx.rectangle(bx, y - 40, bw, 76); shape(ctx, nf(acc), L)
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        txt = opts.get('text', ''); size = 40; ctx.set_font_size(size); e = ctx.text_extents(txt)
        if e.width > bw - 40: size = size * (bw - 40) / e.width; ctx.set_font_size(size); e = ctx.text_extents(txt)
        ctx.set_source_rgb(1, 1, 1); ctx.move_to(bx + bw / 2 - e.width / 2, y + 14); ctx.show_text(txt); ctx.set_source_rgb(*L)
        string_lights(ctx, sx, sx + W_, GY - 300, 60, t, L)
    elif name == 'kettle_window':
        draw_obj(ctx, ('house2', wx, 240, 200, hexc('#FFF0D6'), acc, 'curtain'), sx, L, night, t)
        kx, ky = sx + 60, GY - 120
        ctx.rectangle(kx - 30, ky - 70, 110, 80); shape(ctx, nf(hexc('#FFF8EC')), L)       # kitchen window
        ctx.save(); ctx.translate(kx + 24, ky - 18); ctx.scale(1, .8); ctx.arc(0, 0, 22, math.pi, 2 * math.pi); ctx.restore(); ctx.close_path(); shape(ctx, nf(acc), L)
        ctx.move_to(kx + 46, ky - 30); ctx.line_to(kx + 62, ky - 40); ctx.stroke()
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        for i in range(4):                  # the kettle sings
            ph = (t * .7 + i / 4) % 1; ctx.set_font_size(26); ctx.set_source_rgba(*L, (1 - ph) * sm(dt + 2))
            ctx.move_to(kx + 60 + 70 * ph, ky - 50 - 110 * ph + 10 * math.sin(t * 3 + i)); ctx.show_text('♪')
    elif name == 'golden_neon':
        draw_obj(ctx, ('shop', wx, 440, ' ', hexc('#FFF1DC'), hexc('#FFB21A'), 'cups'), sx, L, night, t)
        ctx.rectangle(sx + 40, GY - 360, 360, 90); shape(ctx, nf(hexc('#2B2541')), L)
        for px in (sx + 100, sx + 340): ctx.move_to(px, GY - 270); ctx.line_to(px, GY - 260); ctx.stroke()
        neon_text(ctx, opts.get('sign', 'GOLDEN HOUR'), sx + 220, GY - 300, 44, hexc('#FFB21A'), t, sm(dt + 1.5))
    elif name == 'neighbors_wave':
        for j in range(2):
            draw_obj(ctx, ('house2', wx + j * 240, 200, 150 + 20 * j, [hexc('#DFF3FF'), hexc('#FFE3EC')][j], acc, 'wave' if dt > -1 else 'curtain'), sx + j * 240, L, night, t)
    elif name == 'note_door':
        draw_obj(ctx, ('house2', wx, 220, 170, hexc('#E8F7F0'), acc, 'curtain'), sx, L, night, t)
        k = sm(dt / 0.6)
        if k > 0:
            ctx.save(); ctx.translate(sx + 38, GY - 40); ctx.rotate(-0.1); ctx.scale(.4 + 1.4 * k, .4 + 1.4 * k)
            ctx.rectangle(-14, -14, 28, 28); shape(ctx, nf(hexc('#FFE14D')), L)
            ctx.set_font_size(8); ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.move_to(-11, 3); ctx.show_text('TODAY!'); ctx.restore()
    elif name == 'alarm_window':
        draw_obj(ctx, ('house2', wx, 240, 180, hexc('#E6E0FF'), acc, 'curtain'), sx, L, night, t)
        cx_, cy_ = sx + 90, GY - 110
        shake = 4 * math.sin(t * 50) if 0 < dt < 2.5 else 0
        ctx.save(); ctx.translate(cx_ + shake, cy_)
        ctx.arc(0, 0, 30, 0, 2 * math.pi); shape(ctx, nf((1, 1, 1)), L)
        for bx in (-22, 22): ctx.arc(bx, -28, 10, 0, 2 * math.pi); shape(ctx, nf(acc), L)
        ctx.move_to(0, 0); ctx.line_to(0, -18); ctx.move_to(0, 0); ctx.line_to(12, 4); ctx.stroke(); ctx.restore()
        if 0 < dt < 2.5:
            for a in (-0.6, 0, 0.6):
                ctx.move_to(cx_ + 44 * math.sin(a) * 1.0, cy_ - 44 * math.cos(a)); ctx.line_to(cx_ + 62 * math.sin(a), cy_ - 62 * math.cos(a)); ctx.stroke()
    elif name == 'sneaker_shop':
        draw_obj(ctx, ('shop', wx, 400, opts.get('sign', 'SNEAKERS'), hexc('#EAF4FF'), hexc('#3D9BFF'), None), sx, L, night, t)
        for i in range(3):
            bx = sx + 50 + i * 54; by = GY - 56
            ctx.move_to(bx, by); ctx.line_to(bx + 18, by); ctx.curve_to(bx + 26, by + 12, bx + 44, by + 8, bx + 46, by + 20)
            ctx.line_to(bx, by + 20); ctx.close_path(); shape(ctx, nf([hexc('#FF5C8A'), (1, 1, 1), hexc('#FFB21A')][i]), L)
    elif name == 'windows_open':
        draw_obj(ctx, ('bldg', wx, 560, 360, 4, hexc('#EAF4FF')), sx, L, night, t)
        for r in range(2):
            for c in range(5):
                wx0 = sx + 30 + c * 104; wy0 = GY - 330 + r * 120
                ctx.rectangle(wx0, wy0, 70, 80); shape(ctx, nf(hexc('#BDE4FF')), L)
                k = sm((dt - (c * .25 + r * .4)) / .5)       # shutters swing open one by one
                for side in (0, 1):
                    w2 = 35 * (1 - k)
                    if side == 0: ctx.rectangle(wx0, wy0, w2, 80)
                    else: ctx.rectangle(wx0 + 70 - w2, wy0, w2, 80)
                    if w2 > 1: shape(ctx, nf(acc), L)
                    ctx.move_to(wx0 + (0 if side == 0 else 70), wy0); ctx.line_to(wx0 + (0 if side == 0 else 70) + (-20 if side == 0 else 20) * k, wy0 + 6 * k)
                    ctx.line_to(wx0 + (0 if side == 0 else 70) + (-20 if side == 0 else 20) * k, wy0 + 80 - 6 * k); ctx.line_to(wx0 + (0 if side == 0 else 70), wy0 + 80)
                    if k > 0.05: shape(ctx, nf(acc), L)
                    else: ctx.new_path()
    elif name == 'corner_lady':
        draw_obj(ctx, ('shop', wx, 420, opts.get('sign', 'CORNER COFFEE'), hexc('#FFF1DC'), acc, 'cups'), sx, L, night, t)
        ctx.save(); ctx.rectangle(sx + 30, GY - 120, 189, 90); ctx.clip()
        npc(ctx, sx + 150, GY + 36, t, L, dict(skin=1, hair=2, top='#2EC4A6', style='bun'), 'counter', face=-1, s=.75, dt=dt, nf=nf)
        ctx.restore()
    elif name == 'sign':
        ctx.move_to(sx + 40, GY); ctx.line_to(sx + 40, GY - 260); ctx.stroke()
        ctx.rectangle(sx + 40, GY - 260, W_ - 60, 62); shape(ctx, nf(hexc('#2EA36B')), L)
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        txt = opts.get('text', ''); size = 30; ctx.set_font_size(size); e = ctx.text_extents(txt)
        if e.width > W_ - 100: ctx.set_font_size(size * (W_ - 100) / e.width); e = ctx.text_extents(txt)
        ctx.set_source_rgb(1, 1, 1); ctx.move_to(sx + 40 + (W_ - 60) / 2 - e.width / 2, GY - 218); ctx.show_text(txt)
    ctx.set_source_rgb(*L)
