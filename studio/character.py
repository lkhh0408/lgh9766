"""Open to Close mascot: fixed body (face, glasses, bob hair, proportions) + swappable outfit."""
import math
import cairo

def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))

# fixed identity
SKIN, HAIR = (1, 0.93, 0.86), hexc('#5A3B2E')

OUTFITS = {
    'morning': dict(top='#FFC53D', bottom='#3D5BFF', phones='#7B3BFF', prop='coffee'),
    'street': dict(top='#1E1E24', bottom='#6B6F7A', phones='#F2C230', prop='coffee'),
    # channel signature look: sky-blue hoodie, retro headphones
    'signature': dict(top='#8FD0FF', bottom='#3E4A6B', phones='#E0457B', phones_style='retro', prop='coffee'),
}

def _shape(ctx, fill, L):
    ctx.set_source_rgb(*fill); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.stroke()

def _smooth(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

def _phones(ctx, style, hx, hy, R, col, L):
    if style == 'retro':   # slim silver band, big round cups with a cream plate
        for w_, c in ((7, L), (3.5, (0.86, 0.88, 0.92))):
            ctx.set_line_width(w_); ctx.set_source_rgb(*c); ctx.arc(hx - 2, hy - 2, R + 8, math.radians(198), math.radians(325)); ctx.stroke()
        ctx.arc(hx - 24, hy + 6, 20, 0, 2 * math.pi); ctx.set_source_rgb(*lerp(col, (0.12, 0.1, 0.15), 0.55)); ctx.fill_preserve()
        ctx.set_source_rgb(*L); ctx.set_line_width(3); ctx.stroke()
        ctx.arc(hx - 28, hy + 6, 18, 0, 2 * math.pi); ctx.set_source_rgb(*col); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.stroke()
        ctx.arc(hx - 28, hy + 6, 9, 0, 2 * math.pi); ctx.set_source_rgb(1, .96, .88); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.set_line_width(2.5); ctx.stroke()
    else:                  # classic thin band
        ctx.set_line_width(8); ctx.set_source_rgb(*col); ctx.arc(hx - 4, hy, R + 6, math.radians(195), math.radians(320)); ctx.stroke()
        ctx.arc(hx - 24, hy + 4, 11, 0, 2 * math.pi); ctx.fill_preserve(); ctx.set_source_rgb(*L); ctx.set_line_width(3); ctx.stroke()

def draw(ctx, cx, gy, t, L=hexc('#2B2541'), outfit='signature', walking=True, phase=None, walk=None, reach=0.0, press=0.0):
    """Draw the mascot standing on ground line gy at x=cx, facing right.
    phase: walk-cycle phase (radians); walk: 0..1 stride amount (0 = standing still);
    reach: 0..1 back hand raised to the headphone; press: 0..1 tap pulse while reaching."""
    o = OUTFITS[outfit]
    if walk is None: walk = 1.0 if walking else 0.0
    walking = walk > 0
    ph = phase if phase is not None else t * 2 * math.pi * 0.85
    bob = 4 * abs(math.cos(ph)) * walk
    hip = (cx, gy - 86 - bob)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    pants, top, phones = hexc(o['bottom']), hexc(o['top']), hexc(o['phones'])

    def limb(x0, y0, a1, l1, a2, l2):
        x1, y1 = x0 + l1 * math.sin(a1), y0 + l1 * math.cos(a1)
        x2, y2 = x1 + l2 * math.sin(a2), y1 + l2 * math.cos(a2)
        ctx.move_to(x0, y0); ctx.line_to(x1, y1); ctx.line_to(x2, y2); ctx.stroke(); return x2, y2

    def leg(p, back):
        a = math.radians(24) * math.sin(p) * walk + (1 - walk) * math.radians(6 if back else -4)
        bend = math.radians(36) * max(0, math.cos(p)) * walk
        ctx.set_line_width(14); ctx.set_source_rgb(*lerp(pants, (.1, .1, .2), .35 if back else 0))
        fx, fy = limb(hip[0], hip[1], a, 44, a - bend, 42)
        ctx.set_line_width(13); ctx.set_source_rgb(*L); ctx.move_to(fx - 5, fy); ctx.line_to(fx + 14, fy); ctx.stroke()

    leg(ph + math.pi, True)
    sh = (cx + 2, hip[1] - 62)
    a_sw = -math.radians(22) * math.sin(ph) * walk
    def back_arm(r):
        # blend the swinging arm into an IK pose touching the headphone cup
        hx_, hy_ = cx + 6, hip[1] - 116
        tx, ty = hx_ - 24 + 6 - 2 * press, hy_ + 10
        dx, dy = tx - sh[0], ty - sh[1]; d = min(61.0, math.hypot(dx, dy))
        at = math.atan2(dx, dy); off = math.acos(max(-1, min(1, (32 ** 2 + d ** 2 - 30 ** 2) / (2 * 32 * d))))
        r1 = at + off; ex_, ey_ = sh[0] + 32 * math.sin(r1), sh[1] + 32 * math.cos(r1); r2 = math.atan2(tx - ex_, ty - ey_)
        a1 = a_sw + (r1 - a_sw) * r; a2 = (a_sw + math.radians(18)) + (r2 - a_sw - math.radians(18)) * r
        ctx.set_line_width(12); ctx.set_source_rgb(*lerp(top, (.3, .2, .1), .3 * (1 - r)))
        limb(sh[0], sh[1], a1, 32, a2, 30)
    if reach <= 0: back_arm(0)
    ctx.set_line_width(4)
    ctx.move_to(hip[0] - 26, hip[1] + 8); ctx.curve_to(hip[0] - 30, hip[1] - 40, hip[0] - 24, hip[1] - 72, hip[0] + 2, hip[1] - 74)
    ctx.curve_to(hip[0] + 26, hip[1] - 72, hip[0] + 30, hip[1] - 40, hip[0] + 26, hip[1] + 8); ctx.close_path(); _shape(ctx, top, L)
    ctx.move_to(hip[0] + 4, hip[1] - 30); ctx.line_to(hip[0] + 22, hip[1] - 30); ctx.stroke()
    leg(ph, False)
    # head (fixed identity)
    hx, hy, R = cx + 6, hip[1] - 116, 42
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
    # outfit: headphones
    _phones(ctx, o.get('phones_style', 'classic'), hx, hy, R, phones, L)
    if reach > 0: back_arm(_smooth(reach))
    # outfit: front arm + prop
    ctx.set_line_width(12); ctx.set_source_rgb(*top)
    ex, ey = limb(sh[0], sh[1], math.radians(10), 30, math.radians(-75), 28)
    if o['prop'] == 'coffee':
        ctx.set_line_width(3.5)
        ctx.move_to(ex - 4, ey - 24); ctx.line_to(ex + 16, ey - 24); ctx.line_to(ex + 13, ey + 4); ctx.line_to(ex - 1, ey + 4); ctx.close_path(); _shape(ctx, (1, 1, 1), L)
        ctx.rectangle(ex - 2, ey - 16, 16, 8); _shape(ctx, hexc('#FF5C8A'), L)
        for i, dx in enumerate((2, 10)):
            s = math.sin(t * 3 + i)
            ctx.move_to(ex + dx, ey - 30); ctx.curve_to(ex + dx + 6 * s, ey - 40, ex + dx - 6 * s, ey - 50, ex + dx, ey - 60); ctx.stroke()
    return (hx, hy, R)
