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
    if name in ('window', 'cinema', 'tram', 'mailbox', 'boxes', 'market_lady', 'lake', 'boutique'):
        return draw_extra(ctx, name, sx, GY, t, dt, L, night, nf, opts, draw_obj, wx)
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


# ---------------------------------------------------------------- window vignettes
WIDTH.update({'window': 340, 'cinema': 440, 'tram': 520, 'mailbox': 220, 'boxes': 380, 'market_lady': 360,
              'lake': 560, 'boutique': 420})

def _book(ctx, x, y, L, nf, col):
    ctx.rectangle(x, y, 22, 16); shape(ctx, nf(col), L); ctx.move_to(x + 11, y); ctx.line_to(x + 11, y + 16); ctx.stroke()

def vignette(ctx, scene, x0, y0, w, h, t, dt, L, nf):
    """an indoor moment seen through a window (x0, y0, w, h); people drawn small"""
    floor = y0 + h
    ctx.set_line_width(2.5)
    if scene == 'breakfast':       # two people planning a trip over breakfast
        ctx.rectangle(x0 + 60, floor - 34, w - 120, 8); shape(ctx, nf(hexc('#E8C9A0')), L)
        npc(ctx, x0 + 52, floor + 8, t, L, dict(skin=1, hair=2, top='#FF8A5B', style='long'), 'sit', face=1, s=.42, nf=nf)
        npc(ctx, x0 + w - 52, floor + 8, t, L, dict(skin=0, hair=1, top='#3D9BFF'), 'sit', face=-1, s=.42, nf=nf)
        ctx.rectangle(x0 + w / 2 - 22, floor - 44, 44, 10); shape(ctx, nf((1, 1, 1)), L)       # the folded page
        ctx.set_source_rgb(*hexc('#E0457B')); ctx.arc(x0 + w / 2 + 12, floor - 39, 3, 0, 2 * math.pi); ctx.fill(); ctx.set_source_rgb(*L)
        for dx in (-40, 40): ctx.save(); ctx.translate(x0 + w / 2 + dx, floor - 37); ctx.scale(1, .35); ctx.arc(0, 0, 12, 0, 2 * math.pi); ctx.restore(); shape(ctx, nf((1, 1, 1)), L)
    elif scene == 'plant':         # basil on the sill, a new leaf every few seconds
        for k, (px, col) in enumerate(((w * .3, '#D9734A'), (w * .55, '#FFC233'), (w * .78, '#D9734A'))):
            cx = x0 + px; ctx.move_to(cx - 18, floor - 4); ctx.line_to(cx + 18, floor - 4); ctx.line_to(cx + 13, floor - 34); ctx.line_to(cx - 13, floor - 34); ctx.close_path()
            ctx.move_to(cx - 18, floor - 34)
            shape(ctx, nf(hexc(col)), L)
            n = 3 + (min(8, int(max(0, dt) / 2.5)) if k == 0 else 2)
            ctx.move_to(cx, floor - 34); ctx.line_to(cx, floor - 34 - 8 * n); ctx.stroke()
            for i in range(n):
                side = 1 if i % 2 else -1; ly = floor - 40 - 8 * i
                ctx.save(); ctx.translate(cx + side * 9, ly); ctx.rotate(side * .5); ctx.scale(1, .6); ctx.arc(0, 0, 9, 0, 2 * math.pi); ctx.restore()
                shape(ctx, nf(hexc('#5CC27A')), L)
        ctx.rectangle(x0, floor - 6, w, 6); shape(ctx, nf((1, 1, 1)), L)
    elif scene == 'drawing':       # someone drawing a little house on a hill
        ctx.rectangle(x0 + 30, floor - 30, w - 60, 8); shape(ctx, nf(hexc('#C99B6A')), L)
        npc(ctx, x0 + 60, floor + 10, t, L, dict(skin=1, hair=3, top='#3D6BFF', style='bun'), 'piano', face=1, s=.45, nf=nf)
        px, py = x0 + w / 2 + 10, floor - 92
        ctx.rectangle(px, py, 110, 64); shape(ctx, nf((1, 1, 1)), L)
        ctx.arc(px + 55, py + 70, 50, math.pi * 1.15, math.pi * 1.85); ctx.stroke()
        ctx.rectangle(px + 44, py + 26, 20, 16); shape(ctx, nf(hexc('#E0457B')), L)
        for i in range(2): ctx.set_source_rgb(*nf(hexc('#FFC233'))); ctx.arc(px + 20 + i * 70, py + 48, 5, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgb(*L)
    elif scene == 'laundry':       # dancing barefoot with the laundry
        ctx.move_to(x0 + 10, y0 + 24); ctx.curve_to(x0 + w * .3, y0 + 40, x0 + w * .7, y0 + 40, x0 + w - 10, y0 + 24); ctx.stroke()
        for i, col in enumerate(('#3D9BFF', '#FFFFFF', '#FF8A5B', '#3D9BFF')):
            sx = x0 + 40 + i * (w - 80) / 3; sw = 4 * math.sin(t * 3 + i)
            ctx.rectangle(sx - 12 + sw, y0 + 30, 24, 30); shape(ctx, nf(hexc(col)), L)
        bob = 6 * abs(math.sin(t * 4))
        npc(ctx, x0 + w * .45, floor + 6 - bob, t, L, dict(skin=2, hair=0, top='#FFC233'), 'wave', face=1 if math.sin(t * 2) > 0 else -1, s=.45, nf=nf)
        ctx.rectangle(x0 + w * .72, floor - 26, 50, 26); shape(ctx, nf(hexc('#E8C9A0')), L)
    elif scene == 'yoga':          # a class stretching on mats
        for i in range(3):
            mx = x0 + 40 + i * (w - 80) / 2
            ctx.rectangle(mx - 30, floor - 6, 60, 6); shape(ctx, nf(hexc(['#7FD99A', '#FF9AA2', '#9FD3FF'][i])), L)
            npc(ctx, mx, floor - 4, t, L, dict(skin=i % 4, hair=(i + 1) % 5, top=['#2EC4A6', '#FF5C8A', '#7B3BFF'][i], style=['long', 'bun', 'short'][i]),
                'wave' if math.sin(t * 1.2 + i) > -0.3 else 'stand', face=1, s=.4, nf=nf)
    elif scene == 'reading':       # a day off in a sunny armchair
        ctx.set_source_rgba(1, .9, .5, .35); ctx.rectangle(x0 + w * .3, y0, w * .5, h); ctx.fill(); ctx.set_source_rgb(*L)
        ctx.rectangle(x0 + w / 2 - 50, floor - 50, 100, 50); shape(ctx, nf(hexc('#FF8A5B')), L)
        ctx.rectangle(x0 + w / 2 - 50, floor - 90, 22, 90); shape(ctx, nf(hexc('#FF8A5B')), L)
        npc(ctx, x0 + w / 2 - 10, floor - 22, t, L, dict(skin=0, hair=2, top='#2EC4A6'), 'sip', face=1, s=.45, nf=nf)
        _book(ctx, x0 + w / 2 + 6, floor - 66, L, nf, hexc('#E0457B'))
    elif scene == 'videocall':     # sunrise here, sunset on the phone
        npc(ctx, x0 + w * .35, floor + 8, t, L, dict(skin=1, hair=3, top='#FFC233', style='long'), 'sip', face=1, s=.45, nf=nf)
        px, py = x0 + w * .58, floor - 104
        ctx.rectangle(px, py, 64, 104); shape(ctx, nf(hexc('#2B2541')), L)
        g = cairo.LinearGradient(0, py + 6, 0, py + 98); g.add_color_stop_rgb(0, *hexc('#7B3BFF')); g.add_color_stop_rgb(1, *hexc('#FF9A5B'))
        ctx.rectangle(px + 5, py + 6, 54, 92); ctx.set_source(g); ctx.fill(); ctx.set_source_rgb(*L)
        ctx.arc(px + 32, py + 52, 14, 0, 2 * math.pi); shape(ctx, nf(SKINS[0]), L)
        ctx.arc(px + 32, py + 40, 14, math.pi, 2 * math.pi); ctx.set_source_rgb(*nf(hexc('#C9CED6'))); ctx.fill(); ctx.set_source_rgb(*L)
        if 0 < dt % 6 < 1.5:
            ctx.set_source_rgb(*hexc('#FF5C8A')); ctx.arc(px + 48, py + 20, 6, 0, 2 * math.pi); ctx.fill(); ctx.set_source_rgb(*L)
    elif scene == 'kitchen':       # pancakes in a new kitchen, one flipping
        ctx.rectangle(x0 + 20, floor - 34, w - 40, 34); shape(ctx, nf(hexc('#FFE9A8')), L)
        npc(ctx, x0 + w * .38, floor + 4, t, L, dict(skin=2, hair=1, top='#3D9BFF'), 'stand', face=1, s=.45, nf=nf)
        npc(ctx, x0 + w * .78, floor + 4, t, L, dict(skin=0, hair=3, top='#FF5C8A', style='long'), 'wave', face=-1, s=.45, nf=nf)
        cx, cy = x0 + w * .55, floor - 40
        ctx.move_to(cx - 24, cy); ctx.line_to(cx + 10, cy); ctx.stroke(); ctx.move_to(cx - 40, cy); ctx.line_to(cx - 24, cy); ctx.set_line_width(5); ctx.stroke(); ctx.set_line_width(2.5)
        ph = (t * .8) % 1; fy = cy - 6 - 60 * math.sin(ph * math.pi)
        ctx.save(); ctx.translate(cx - 7, fy); ctx.scale(1, abs(math.cos(ph * math.pi * 2)) * .4 + .05); ctx.arc(0, 0, 13, 0, 2 * math.pi); ctx.restore()
        shape(ctx, nf(hexc('#E8B060')), L)
    elif scene == 'crossword':     # a diner booth, a pencil, a crossword
        ctx.rectangle(x0 + 50, floor - 34, w - 100, 8); shape(ctx, nf(hexc('#FF8A5B')), L)
        npc(ctx, x0 + 46, floor + 8, t, L, dict(skin=3, hair=1, top='#7B3BFF'), 'sit', face=1, s=.42, nf=nf)
        npc(ctx, x0 + w - 46, floor + 8, t, L, dict(skin=0, hair=2, top='#2EC4A6', style='long'), 'sit', face=-1, s=.42, nf=nf)
        gx, gy = x0 + w / 2 - 26, floor - 72
        ctx.rectangle(gx, gy, 52, 36); shape(ctx, nf((1, 1, 1)), L)
        for i in range(1, 4): ctx.move_to(gx + i * 13, gy); ctx.line_to(gx + i * 13, gy + 36)
        for j in range(1, 3): ctx.move_to(gx, gy + j * 12); ctx.line_to(gx + 52, gy + j * 12)
        ctx.set_line_width(1.2); ctx.stroke(); ctx.set_line_width(2.5)
        ctx.rectangle(gx + 13, gy + 12, 13, 12); ctx.set_source_rgb(*hexc('#2B2541')); ctx.fill(); ctx.set_source_rgb(*L)
    elif scene == 'turntable':     # a record spinning in the shop window
        ctx.rectangle(x0 + w * .3, floor - 30, 120, 30); shape(ctx, nf(hexc('#C99B6A')), L)
        cx, cy = x0 + w * .3 + 50, floor - 36
        ctx.save(); ctx.translate(cx, cy); ctx.scale(1, .35); ctx.arc(0, 0, 36, 0, 2 * math.pi); ctx.restore(); shape(ctx, nf(hexc('#2B2541')), L)
        a = t * 4; ctx.set_source_rgb(*hexc('#E0457B')); ctx.arc(cx + 8 * math.cos(a), cy + 3 * math.sin(a), 4, 0, 2 * math.pi); ctx.fill(); ctx.set_source_rgb(*L)
        npc(ctx, x0 + w * .82, floor + 6, t, L, dict(skin=1, hair=4, top='#FF5C8A', style='long'), 'counter', face=-1, s=.48, dt=dt, nf=nf)
    elif scene == 'guitar':        # playing a sister's song in my own key
        npc(ctx, x0 + w * .35, floor + 4, t, L, dict(skin=1, hair=0, top='#2EC4A6'), 'sit', face=1, s=.48, nf=nf)
        gx, gy = x0 + w * .35 + 14, floor - 34
        ctx.save(); ctx.translate(gx, gy); ctx.rotate(-.5); ctx.arc(0, 0, 13, 0, 2 * math.pi); ctx.restore(); shape(ctx, nf(hexc('#E8A05A')), L)
        ctx.set_line_width(4); ctx.move_to(gx + 6, gy - 6); ctx.line_to(gx + 34, gy - 30); ctx.stroke(); ctx.set_line_width(2.5)
        if dt > 4: npc(ctx, x0 + w * .75, floor + 4, t, L, dict(skin=1, hair=0, top='#FF9AA2', style='long'), 'sit', face=-1, s=.48, nf=nf)
        ctx.rectangle(x0 + w * .5, floor - 60, 36, 26); shape(ctx, nf((1, 1, 1)), L)
        for i in range(3): ctx.set_source_rgb(*hexc('#2EA36B')); ctx.arc(x0 + w * .5 + 8 + i * 10, floor - 48, 3, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgb(*L)

def draw_extra(ctx, name, sx, GY, t, dt, L, night, nf, opts, draw_obj, wx):
    """pieces added for VOL.01 songs 4-20"""
    W_ = WIDTH.get(name, 400); acc = hexc(opts.get('color', '#FF5C8A'))
    ctx.set_line_width(3); ctx.set_source_rgb(*L)
    if name == 'window':
        sign = opts.get('sign')
        bh = 300 if sign else 250
        ctx.rectangle(sx, GY - bh, W_, bh); shape(ctx, nf(lerp(acc, (1, 1, 1), .78)), L)
        if sign:
            n = 7; aw = W_ / n
            for i in range(n):
                ctx.move_to(sx + i * aw, GY - bh + 50); ctx.line_to(sx + (i + 1) * aw, GY - bh + 50); ctx.line_to(sx + (i + 1) * aw, GY - bh + 76)
                ctx.arc(sx + (i + .5) * aw, GY - bh + 76, aw / 2, 0, math.pi); ctx.close_path(); shape(ctx, nf(acc if i % 2 == 0 else (1, 1, 1)), L)
            ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(26)
            e = ctx.text_extents(sign)
            if e.width > W_ - 30: ctx.set_font_size(26 * (W_ - 30) / e.width); e = ctx.text_extents(sign)
            ctx.move_to(sx + W_ / 2 - e.width / 2, GY - bh + 36); ctx.show_text(sign)
        else:
            ctx.move_to(sx - 14, GY - bh); ctx.line_to(sx + W_ / 2, GY - bh - 70); ctx.line_to(sx + W_ + 14, GY - bh); ctx.close_path(); shape(ctx, nf(acc), L)
        x0, y0, w, h = sx + 26, GY - 210, W_ - 52, 160
        ctx.rectangle(x0, y0, w, h)
        ctx.set_source_rgb(*nf(hexc('#FFF8EC'))); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.stroke()
        if night > .3: ctx.set_source_rgba(1, .85, .45, .35 * night); ctx.rectangle(x0, y0, w, h); ctx.fill(); ctx.set_source_rgb(*L)
        ctx.save(); ctx.rectangle(x0, y0, w, h); ctx.clip(); vignette(ctx, opts.get('scene', 'reading'), x0, y0, w, h, t, dt, L, nf); ctx.restore()
        ctx.set_source_rgb(*L); ctx.set_line_width(3); ctx.rectangle(x0, y0, w, h); ctx.stroke()
        ctx.move_to(x0 + w / 2, y0); ctx.line_to(x0 + w / 2, y0 + 10); ctx.stroke()
        ctx.rectangle(x0 - 6, y0 + h, w + 12, 10); shape(ctx, nf((1, 1, 1)), L)
    elif name == 'cinema':
        ctx.rectangle(sx, GY - 330, W_, 330); shape(ctx, nf(hexc('#3A2E5C')), L)
        mx, my, mw, mh = sx + 40, GY - 300, W_ - 80, 90
        ctx.rectangle(mx, my, mw, mh); shape(ctx, nf(hexc('#FFF4DF')), L)
        n = 22
        for i in range(n):           # chasing marquee bulbs
            u = i / n; per = 2 * (mw + mh); d = u * per
            bx, by = (mx + d, my) if d < mw else ((mx + mw, my + d - mw) if d < mw + mh else ((mx + mw - (d - mw - mh), my + mh) if d < 2 * mw + mh else (mx, my + mh - (d - 2 * mw - mh))))
            on = (int(t * 6) + i) % 3 == 0
            ctx.arc(bx, by, 5, 0, 2 * math.pi); ctx.set_source_rgb(*(hexc('#FFD34D') if on else nf(hexc('#C9A23A')))); ctx.fill()
        ctx.set_source_rgb(*hexc('#E0457B')); ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        txt = opts.get('text', 'MATINEE'); ctx.set_font_size(42); e = ctx.text_extents(txt)
        if e.width > mw - 30: ctx.set_font_size(42 * (mw - 30) / e.width); e = ctx.text_extents(txt)
        ctx.move_to(mx + mw / 2 - e.width / 2, my + mh / 2 + e.height / 2); ctx.show_text(txt); ctx.set_source_rgb(*L)
        for px in (sx + 40, sx + W_ - 120):
            ctx.rectangle(px, GY - 180, 80, 110); shape(ctx, nf(hexc('#FFC233')), L)
            ctx.arc(px + 40, GY - 140, 18, 0, 2 * math.pi); shape(ctx, nf(hexc('#FF5C8A')), L)
        ctx.rectangle(sx + W_ / 2 - 50, GY - 110, 100, 110); shape(ctx, nf(hexc('#FFE3A3')), L)
        ctx.move_to(sx + W_ / 2, GY - 110); ctx.line_to(sx + W_ / 2, GY); ctx.stroke()
    elif name == 'tram':             # a little tram glides past, faster than the walker
        rx = sx + 1000 - 300 * max(0.0, dt + 2.0)
        if -600 < rx - sx < 1600:
            ctx.rectangle(rx, GY - 170, 440, 150); shape(ctx, nf(acc), L)
            ctx.rectangle(rx, GY - 170, 440, 26); shape(ctx, nf((1, 1, 1)), L)
            for i in range(5):
                wx0 = rx + 20 + i * 84; ctx.rectangle(wx0, GY - 136, 64, 56); shape(ctx, nf(hexc('#DFF3FF')), L)
                if i % 2 == 0:
                    ctx.save(); ctx.rectangle(wx0, GY - 136, 64, 56); ctx.clip()
                    ctx.arc(wx0 + 32, GY - 104, 13, 0, 2 * math.pi); shape(ctx, nf(SKINS[i % 4]), L); ctx.restore()
            for wxo in (60, 380): ctx.arc(rx + wxo, GY - 16, 16, 0, 2 * math.pi); shape(ctx, nf(hexc('#3A3A46')), L)
            ctx.move_to(rx + 220, GY - 170); ctx.line_to(rx + 200, GY - 230); ctx.line_to(rx + 260, GY - 230); ctx.stroke()
    elif name == 'mailbox':
        ctx.rectangle(sx + 80, GY - 150, 70, 150); shape(ctx, nf(hexc('#E0457B')), L)
        ctx.arc(sx + 115, GY - 150, 35, math.pi, 0); ctx.close_path(); shape(ctx, nf(hexc('#E0457B')), L)
        ctx.rectangle(sx + 93, GY - 130, 44, 8); shape(ctx, nf(hexc('#2B2541')), L)
        k = sm(dt / 1.5)
        if k < 1:
            ctx.save(); ctx.translate(sx + 30 + 85 * k, GY - 180 + 54 * k); ctx.rotate(-.3 * (1 - k)); ctx.rectangle(-20, -13, 40, 26); ctx.restore()
            shape(ctx, nf(hexc('#FFF4DF')), L)
        npc(ctx, sx + 30, GY, t, L, dict(skin=1, hair=3, top='#3D6BFF', style='bun'), 'wave' if dt > 1.5 else 'stand', face=1, s=.85, dt=dt, nf=nf)
    elif name == 'boxes':
        for i, (bx, by, bw, bh) in enumerate(((20, 0, 90, 70), (120, 0, 100, 80), (60, -70, 80, 60), (240, 0, 80, 60))):
            ctx.rectangle(sx + bx, GY - by - bh, bw, bh); shape(ctx, nf(hexc('#D9A86C')), L)
            ctx.move_to(sx + bx + bw / 2, GY - by - bh); ctx.line_to(sx + bx + bw / 2, GY - by - bh + 16); ctx.stroke()
        draw_piece(ctx, 'sign', sx + 10, GY, t, dt, L, night, nf, {'text': opts.get('text', 'NEW ADDRESS'), 'color': opts.get('color')}, draw_obj, wx)
    elif name == 'market_lady':
        draw_obj(ctx, ('stall', wx, 240, acc, hexc('#FFF1DC')), sx, L, night, t)
        for i in range(5):
            px_ = sx + 30 + i * 40
            ctx.save(); ctx.translate(px_, GY - 98); ctx.scale(.8, 1); ctx.arc(0, 0, 13, 0, 2 * math.pi); ctx.restore(); shape(ctx, nf(hexc('#B8D85A')), L)
        npc(ctx, sx + 300, GY, t, L, dict(skin=2, hair=4, top='#FF8A5B', style='bun'), 'wave' if dt > 0 else 'stand', face=-1, s=.85, dt=dt, nf=nf)
    elif name == 'lake':
        ctx.save(); ctx.translate(0, 0)
        ctx.move_to(sx, GY); ctx.curve_to(sx + 40, GY - 46, sx + W_ - 40, GY - 46, sx + W_, GY); ctx.close_path(); shape(ctx, nf(hexc('#6CC8EF')), L)
        ctx.rectangle(sx + 20, GY - 30, 150, 10); shape(ctx, nf(hexc('#C99B6A')), L)       # dock
        for px in (sx + 40, sx + 150): ctx.move_to(px, GY - 20); ctx.line_to(px, GY); ctx.stroke()
        for i in range(6):           # stone skipping: one, two, three... still going
            hop_t = dt - i * 0.45
            if hop_t > 0:
                hx = sx + 200 + i * 55; r = 6 + 22 * min(1, hop_t / 2.5)
                ctx.set_source_rgba(*L, max(0, 1 - hop_t / 3)); ctx.save(); ctx.translate(hx, GY - 14); ctx.scale(1, .3); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore(); ctx.stroke()
        ph = dt / 0.45
        if 0 < ph < 6:
            k = int(ph); f = ph - k
            ctx.set_source_rgb(*hexc('#8A8F9A')); ctx.arc(sx + 200 + (k + f) * 55, GY - 14 - 30 * math.sin(f * math.pi) * (1 - k / 7), 5, 0, 2 * math.pi); ctx.fill()
        for rx_ in (sx + W_ - 60, sx + W_ - 40): ctx.set_source_rgb(*L); ctx.move_to(rx_, GY); ctx.curve_to(rx_ - 4, GY - 40, rx_ + 4, GY - 60, rx_, GY - 80); ctx.stroke()
        ctx.restore()
    elif name == 'boutique':
        draw_obj(ctx, ('shop', wx, 420, opts.get('sign', 'BOUTIQUE'), hexc('#FFF1F4'), acc, 'clothes'), sx, L, night, t)
        npc(ctx, sx + 380, GY, t, L, dict(skin=1, hair=2, top='#FFB38A', style='long'), 'wave' if math.sin(dt * 1.5) > 0 else 'stand', face=1 if math.sin(dt) > 0 else -1, s=.85, dt=dt, nf=nf)
    ctx.set_source_rgb(*L)

def dog(ctx, x, gy, phase, walk, t, L, alpha=1.0):
    """a small dog trotting beside the walker (Follow My Nose)"""
    ctx.save(); ctx.push_group(); ctx.translate(x, gy)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    fur, dark = hexc('#E8B878'), hexc('#8A5A3C')
    bob = 2 * abs(math.sin(phase * 2)) * walk
    ctx.set_line_width(7); ctx.set_source_rgb(*dark)
    for i, (lx, off) in enumerate(((-30, 0), (-18, math.pi), (18, math.pi), (30, 0))):
        a = 0.45 * math.sin(phase * 2 + off) * walk
        ctx.move_to(lx, -34 - bob); ctx.line_to(lx + 14 * math.sin(a), -4); ctx.stroke()
    ctx.set_line_width(3.5)
    ctx.save(); ctx.translate(0, -44 - bob); ctx.scale(1, .55); ctx.arc(0, 0, 42, 0, 2 * math.pi); ctx.restore(); shape(ctx, fur, L)
    wag = math.sin(t * 12) * 0.5
    ctx.set_line_width(7); ctx.set_source_rgb(*fur); ctx.move_to(-40, -50 - bob); ctx.line_to(-58, -70 - bob + 10 * wag); ctx.stroke()
    ctx.set_line_width(3.5); ctx.set_source_rgb(*L)
    hx, hy = 42, -74 - bob
    ctx.arc(hx, hy, 20, 0, 2 * math.pi); shape(ctx, fur, L)
    ctx.save(); ctx.translate(hx + 18, hy + 8); ctx.scale(1, .7); ctx.arc(0, 0, 11, 0, 2 * math.pi); ctx.restore(); shape(ctx, fur, L)
    ctx.arc(hx + 28, hy + 4, 4, 0, 2 * math.pi); ctx.fill()
    ctx.arc(hx + 8, hy - 4, 3, 0, 2 * math.pi); ctx.fill()
    ctx.move_to(hx - 8, hy - 14); ctx.curve_to(hx - 24, hy - 10, hx - 22, hy + 14, hx - 12, hy + 12); ctx.close_path(); shape(ctx, dark, L)
    ctx.set_line_width(4); ctx.set_source_rgb(*hexc('#E0457B')); ctx.arc(hx - 4, hy + 12, 14, math.radians(60), math.radians(150)); ctx.stroke()
    ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha); ctx.restore()
