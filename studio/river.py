"""Riverside-park world (VOL.02): a lawn by the river with the city across the water.

render_video.py uses this when run with --world river. It supplies:
  back()    sky extras, city skyline, suspension bridges, the river and its boats, the lawn
  gen()     static park scenery for the storyboard scene kinds below
  draw()    those objects (kinds start with 'rv_') and the new lyric pieces (piece names start with 'rv_')
  actors()  people, dogs, bikes and skaters passing along the lawn paths behind the walker
  front()   a dog that sometimes trots beside the walker, fireflies, rain and other overlays
  ground()  the grass path the walker is on
"""
import math, random
import cairo
import props

W, H, GY, CX = 1920, 1080, 760, 820
RIVER_Y0, RIVER_Y1 = 560, 640
FAR_PATH, NEAR_PATH = 690, 736
KINDS = {'lawn', 'picnic', 'plaza', 'promenade', 'garden', 'sports'}

def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))
def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
DARK = hexc('#2A2F5C')
_N = 0.0      # night amount of the current frame
_L = hexc('#2B2541')
def nf(c): return lerp(c, DARK, _N * 0.85)
def fill(ctx, col, lw=None):
    if isinstance(col, str): col = hexc(col)
    if lw: ctx.set_line_width(lw)
    ctx.set_source_rgb(*nf(col)); ctx.fill_preserve(); ctx.set_source_rgb(*_L); ctx.stroke()
def blobs(ctx, circles, col, lw=1.6):
    ctx.set_source_rgb(*_L); ctx.set_line_width(lw * 2)
    for x, y, r in circles: ctx.new_path(); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.stroke()
    ctx.set_source_rgb(*nf(hexc(col) if isinstance(col, str) else col))
    for x, y, r in circles: ctx.new_path(); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()

LOOKS = [dict(skin=s, hair=h, top=c, bottom=b, style=st) for s, h, c, b, st in (
    (0, 3, '#FF5C8A', '#2B2541', 'cap'), (1, 0, '#9B7BFF', '#3E4A6B', 'long'), (2, 1, '#2EC4A6', '#4A3F35', 'short'),
    (3, 4, '#FFB21A', '#5B7DB1', 'bun'), (1, 2, '#7FC8F8', '#3E4A6B', 'short'), (0, 1, '#FF8A5B', '#2E5E4E', 'long'),
    (2, 0, '#E0457B', '#E8DCC4', 'bun'), (3, 1, '#5BC0EB', '#3A3A46', 'short'), (1, 3, '#B8D85A', '#4A4F66', 'long'),
    (0, 4, '#C9A7FF', '#2B2541', 'short'), (2, 2, '#FFD86B', '#3E4A6B', 'cap'), (3, 0, '#FF7A45', '#E8DCC4', 'long'))]
FURS = [('#E8B878', '#8A5A3C'), ('#FFFFFF', '#3A3A46'), ('#3A3A46', '#1E1B1A'), ('#C98A4B', '#6B4528'), ('#F3E9D2', '#C68B59')]
CAPS = ['#FF5C8A', '#3D9BFF', '#2EC4A6', '#FFB21A']

# ------------------------------------------------------------------ figures
def figure(ctx, x, gy, ph, look, face=1, s=.72, run=False, arm=None):
    """walking person; face=+1 walks right"""
    skin, hair = props.SKINS[look.get('skin', 0)], props.HAIRS[look.get('hair', 0)]
    top, bot = hexc(look['top']), hexc(look.get('bottom', '#4A4F66'))
    ctx.save(); ctx.translate(x, gy); ctx.scale(s * face, s)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    amp = .55 if run else .38; bob = (5 if run else 3) * abs(math.cos(ph)); hy0 = -78 - bob
    for k, off in ((0, math.pi), (1, 0)):
        a = amp * math.sin(ph + off); b = a - (.7 if run else .45) * max(0, math.cos(ph + off))
        x1, y1 = 40 * math.sin(a), hy0 + 40 * math.cos(a); x2, y2 = x1 + 40 * math.sin(b), y1 + 40 * math.cos(b)
        ctx.set_line_width(12); ctx.set_source_rgb(*nf(lerp(bot, (.1, .1, .2), .3 if k == 0 else 0)))
        ctx.move_to(0, hy0); ctx.line_to(x1, y1); ctx.line_to(x2, min(0, y2)); ctx.stroke()
        ctx.set_line_width(11); ctx.set_source_rgb(*_L); ctx.move_to(x2 - 4, min(0, y2)); ctx.line_to(x2 + 12, min(0, y2)); ctx.stroke()
    ctx.set_line_width(3.5)
    ctx.move_to(-20, hy0 + 6); ctx.curve_to(-22, hy0 - 40, -16, hy0 - 64, 2, hy0 - 66)
    ctx.curve_to(20, hy0 - 64, 24, hy0 - 40, 22, hy0 + 6); ctx.close_path(); fill(ctx, top)
    sw = -.5 * math.sin(ph) * (1.4 if run else 1)
    ctx.set_line_width(10); ctx.set_source_rgb(*nf(lerp(top, (0, 0, 0), .15)))
    if arm == 'wave':
        w = math.sin(ph * 2.5) * .35
        ctx.move_to(4, hy0 - 56); ctx.line_to(26, hy0 - 80); ctx.line_to(30 + 14 * w, hy0 - 112); ctx.stroke()
    elif arm == 'hold':     # arm forward: holding a leash, a hand or a stroller
        ctx.move_to(4, hy0 - 56); ctx.line_to(26, hy0 - 34); ctx.line_to(44, hy0 - 40); ctx.stroke()
    else:
        ex, ey = 4 + 28 * math.sin(sw), hy0 - 56 + 28 * math.cos(sw)
        ctx.move_to(4, hy0 - 56); ctx.line_to(ex, ey); ctx.line_to(ex + 24 * math.sin(sw + .6), ey + 24 * math.cos(sw + .6)); ctx.stroke()
    hx, hy, R = 2, hy0 - 96, 30
    ctx.set_line_width(3.5); ctx.arc(hx, hy, R, 0, 2 * math.pi); fill(ctx, skin)
    ctx.save(); ctx.arc(hx, hy, R + 1, 0, 2 * math.pi); ctx.clip()
    st = look.get('style', 'short')
    ctx.move_to(hx + R + 4, hy - 14); ctx.curve_to(hx + 10, hy - 26, hx - 8, hy - 18, hx - 10, hy - 2)
    ctx.line_to(hx - 12, hy + (R if st == 'long' else 12)); ctx.line_to(hx - R - 6, hy + R + 6); ctx.line_to(hx - R - 6, hy - R - 6); ctx.line_to(hx + R + 6, hy - R - 6); ctx.close_path()
    ctx.set_source_rgb(*nf(hair)); ctx.fill(); ctx.restore()
    ctx.set_source_rgb(*_L); ctx.arc(hx, hy, R, 0, 2 * math.pi); ctx.stroke()
    if st == 'bun': ctx.arc(hx - 22, hy - 24, 12, 0, 2 * math.pi); fill(ctx, hair)
    if st == 'cap':
        ctx.move_to(hx - 28, hy - 8); ctx.curve_to(hx - 26, hy - 40, hx + 26, hy - 40, hx + 28, hy - 8); ctx.close_path(); fill(ctx, look.get('cap', '#3D9BFF'))
        ctx.set_line_width(6); ctx.move_to(hx + 20, hy - 10); ctx.line_to(hx + 46, hy - 6); ctx.stroke(); ctx.set_line_width(3.5)
    ctx.set_source_rgb(*_L); ctx.arc(hx + 14, hy + 2, 3, 0, 2 * math.pi); ctx.fill()
    ctx.restore()

def dog(ctx, x, gy, ph, fur, dark, s=.62, face=1, t=0.0, wag=True):
    ctx.save(); ctx.translate(x, gy); ctx.scale(face * s, s)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    bob = 2 * abs(math.sin(ph * 2)); fur, dark = hexc(fur), hexc(dark)
    ctx.set_line_width(7); ctx.set_source_rgb(*nf(dark))
    for lx, off in ((-30, 0), (-18, math.pi), (18, math.pi), (30, 0)):
        a = .45 * math.sin(ph * 2 + off); ctx.move_to(lx, -34 - bob); ctx.line_to(lx + 14 * math.sin(a), -4); ctx.stroke()
    ctx.set_line_width(3.5)
    ctx.save(); ctx.translate(0, -44 - bob); ctx.scale(1, .55); ctx.arc(0, 0, 42, 0, 2 * math.pi); ctx.restore(); fill(ctx, fur)
    w = math.sin(t * 14) * .5 if wag else 0
    ctx.set_line_width(7); ctx.set_source_rgb(*nf(fur)); ctx.move_to(-40, -50 - bob); ctx.line_to(-58, -70 - bob + 10 * w); ctx.stroke()
    ctx.set_line_width(3.5); hx, hy = 42, -74 - bob
    ctx.arc(hx, hy, 20, 0, 2 * math.pi); fill(ctx, fur)
    ctx.save(); ctx.translate(hx + 18, hy + 8); ctx.scale(1, .7); ctx.arc(0, 0, 11, 0, 2 * math.pi); ctx.restore(); fill(ctx, fur)
    ctx.set_source_rgb(*_L); ctx.arc(hx + 28, hy + 4, 4, 0, 2 * math.pi); ctx.fill(); ctx.arc(hx + 8, hy - 4, 3, 0, 2 * math.pi); ctx.fill()
    ctx.move_to(hx - 8, hy - 14); ctx.curve_to(hx - 24, hy - 10, hx - 22, hy + 14, hx - 12, hy + 12); ctx.close_path(); fill(ctx, dark)
    ctx.restore()

def stroller(ctx, x, gy, s=.72, face=1):
    ctx.save(); ctx.translate(x, gy); ctx.scale(s * face, s); ctx.set_line_width(4)
    for wx in (-24, 24): ctx.arc(wx, -14, 13, 0, 2 * math.pi); fill(ctx, '#FFFFFF')
    ctx.move_to(-40, -34); ctx.line_to(40, -34); ctx.arc_negative(0, -34, 40, 0, math.pi); ctx.close_path(); fill(ctx, '#7FC8F8')
    ctx.move_to(-40, -34); ctx.curve_to(-40, -90, 20, -90, 20, -34); fill(ctx, '#4A90D9')
    ctx.set_source_rgb(*_L); ctx.move_to(-40, -40); ctx.line_to(-62, -84); ctx.stroke(); ctx.restore()

def bike(ctx, x, gy, ph, look, s=.72, face=1):
    ctx.save(); ctx.translate(x, gy); ctx.scale(s * face, s); ctx.set_line_width(4); ctx.set_source_rgb(*_L)
    for wx in (-46, 46):
        ctx.arc(wx, -32, 30, 0, 2 * math.pi); ctx.stroke()
        ctx.move_to(wx + 30 * math.cos(ph), -32 + 30 * math.sin(ph)); ctx.line_to(wx - 30 * math.cos(ph), -32 - 30 * math.sin(ph)); ctx.stroke()
    ctx.set_source_rgb(*nf(hexc(look.get('frame', '#3D9BFF')))); ctx.set_line_width(6)
    ctx.move_to(-46, -32); ctx.line_to(-6, -32); ctx.line_to(30, -78); ctx.line_to(-14, -78); ctx.close_path(); ctx.stroke()
    ctx.move_to(-6, -32); ctx.line_to(-18, -88); ctx.move_to(46, -32); ctx.line_to(30, -96); ctx.stroke()
    top, bot = hexc(look['top']), hexc(look.get('bottom', '#4A4F66'))
    ctx.set_line_width(12); ctx.set_source_rgb(*nf(bot))
    for off in (0, math.pi):
        px, py = -6 + 16 * math.cos(ph + off), -32 + 16 * math.sin(ph + off)
        ctx.move_to(-18, -96); ctx.line_to(10, -66 + 6 * math.sin(ph + off)); ctx.line_to(px, py); ctx.stroke()
    ctx.set_line_width(3.5); ctx.move_to(-36, -92); ctx.curve_to(-30, -150, 0, -160, 10, -150); ctx.curve_to(20, -120, 0, -96, -6, -92); ctx.close_path(); fill(ctx, top)
    ctx.set_line_width(10); ctx.set_source_rgb(*nf(lerp(top, (0, 0, 0), .15))); ctx.move_to(4, -140); ctx.line_to(28, -100); ctx.stroke()
    ctx.set_line_width(3.5); ctx.arc(14, -178, 28, 0, 2 * math.pi); fill(ctx, props.SKINS[look.get('skin', 1)])
    ctx.arc(14, -184, 30, math.pi, 0); fill(ctx, look.get('helmet', '#FFB21A'))
    ctx.set_source_rgb(*_L); ctx.arc(30, -176, 3.5, 0, 2 * math.pi); ctx.fill()
    ctx.restore()

def skater(ctx, x, gy, ph, look, s=.72, face=1):
    ctx.save(); ctx.translate(x, gy); ctx.scale(face, 1)
    ctx.set_line_width(4); ctx.rectangle(-40 * s, -16 * s, 80 * s, 8 * s); fill(ctx, '#FF5C8A')
    for wx in (-26, 26): ctx.arc(wx * s, -4 * s, 6 * s, 0, 2 * math.pi); fill(ctx, '#FFFFFF')
    ctx.restore()
    figure(ctx, x, gy - 16 * s, 0.4 * math.sin(ph * .3), look, face=face, s=s)

def note(ctx, x, y, a, col='#7B3BFF'):
    ctx.set_source_rgba(*nf(hexc(col)), a); ctx.arc(x, y, 7, 0, 2 * math.pi); ctx.fill()
    ctx.set_line_width(3); ctx.move_to(x + 6, y); ctx.line_to(x + 6, y - 26); ctx.line_to(x + 16, y - 20); ctx.stroke()

# ------------------------------------------------------------------ schedules
class World:
    def __init__(self, rnd, total, starts, ends, scroll_at, sky_at, speed):
        self.rnd, self.total, self.starts, self.ends, self.scroll_at, self.sky_at, self.speed = rnd, total, starts, ends, scroll_at, sky_at, speed
        r = rnd
        # passers-by on the two lawn paths
        self.walkers = []; t = 1.0
        while t < total:
            night = sky_at(t / total)[2]
            k = r.random(); look = dict(r.choice(LOOKS)); look['cap'] = r.choice(CAPS)
            if night > .6: kind = r.choice(['couple', 'dogwalk', 'walk', 'couple'])
            elif t / total < .3: kind = r.choice(['jog', 'dogwalk', 'walk', 'jog', 'bike', 'dogwalk', 'stroller'])
            else: kind = r.choice(['walk', 'couple', 'dogwalk', 'stroller', 'bike', 'skate', 'jog', 'kids', 'balloon', 'walk'])
            v = {'walk': r.uniform(50, 70), 'couple': r.uniform(45, 60), 'dogwalk': r.uniform(55, 75), 'stroller': r.uniform(45, 60),
                 'jog': r.uniform(240, 280), 'bike': r.uniform(330, 380), 'skate': r.uniform(280, 320), 'kids': r.uniform(70, 90), 'balloon': r.uniform(50, 60)}[kind]
            # slow people mostly come toward the walker; quick ones overtake from behind or come toward
            d = -1 if (v < 120 and r.random() < .8) or (v >= 120 and r.random() < .45) else 1
            path = NEAR_PATH if r.random() < .65 else FAR_PATH
            look2 = dict(r.choice(LOOKS)); fur = r.choice(FURS)
            self.walkers.append(dict(t0=t, kind=kind, v=v * d, path=path, look=look, look2=look2, fur=fur, seed=r.random() * 10))
            t += r.uniform(3.5, 6.5) * (1.8 if night > .6 else 1)
        for w in self.walkers:
            rel = w['v'] - speed
            s0 = scroll_at(w['t0'])
            w['wx0'] = s0 + (W + 200 if rel < 0 else -260)
        # boats and things on the river / in the sky (world x in the river layer, which scrolls at 0.1)
        self.boats = []; t = 2.0
        while t < total:
            kind = r.choice(['ferry', 'kayak', 'sail', 'ferry', 'rowboat'])
            v = {'ferry': 45, 'kayak': 70, 'sail': 35, 'rowboat': 40}[kind] * r.choice([-1, 1])
            self.boats.append(dict(t0=t, kind=kind, v=v, y=r.uniform(588, 628), col=r.choice(['#FF8A6B', '#3D9BFF', '#FFB21A', '#2EC4A6'])))
            t += r.uniform(14, 26)
        self.sky = []; t = 30.0
        while t < total:
            self.sky.append(dict(t0=t, kind=r.choice(['balloon', 'plane', 'balloon']), y=r.uniform(130, 300), col=r.choice(['#FF5C8A', '#FFB21A', '#7B3BFF', '#2EC4A6'])))
            t += r.uniform(120, 240)
        # a dog trots beside the walker once in most songs
        self.visits = []
        for s0, e in zip(starts, ends):
            if e - s0 > 60 and r.random() < .8:
                a = r.uniform(s0 + 25, e - 30); self.visits.append((a, a + r.uniform(5, 8), r.choice(FURS)))
        self.ducks = [(r.uniform(0, 30000), r.choice([3, 4, 5])) for _ in range(40)]
        self.flies = [(r.uniform(0, W), r.uniform(650, 750), r.uniform(0, 6)) for _ in range(40)]
        self.kites = [(r.uniform(0, 40000), r.uniform(220, 380), r.choice(['#FF5C8A', '#FFB21A', '#7B3BFF', '#3D9BFF'])) for _ in range(30)]

    # ---------------------------------------------------------------- far layers
    def back(self, ctx, t, scroll, night, L, top, bot, u):
        global _N, _L
        _N, _L = night, L
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        self._sky_things(ctx, t, scroll, night)
        off = scroll * 0.1
        # skyline across the river
        base = lerp(lerp(bot, top, .25), hexc('#C7D7EE'), .55)
        x = -(off % 90) - 90; i = int(off // 90)
        rnd = random.Random()
        while x < W + 120:
            rnd.seed(i); w_ = rnd.randint(60, 120); h_ = rnd.randint(60, 200)
            ctx.rectangle(x, RIVER_Y0 - h_, w_, h_); ctx.set_source_rgb(*lerp(base, hexc('#2C3566'), night * .8)); ctx.fill_preserve()
            ctx.set_source_rgb(*L); ctx.set_line_width(2); ctx.stroke()
            if rnd.random() < .25:   # a spire or a water tank
                ctx.move_to(x + w_ / 2, RIVER_Y0 - h_); ctx.line_to(x + w_ / 2, RIVER_Y0 - h_ - 30); ctx.stroke()
            if night > .25:
                for yy in range(int(RIVER_Y0 - h_ + 12), RIVER_Y0 - 10, 18):
                    for xx in range(int(x + 8), int(x + w_ - 8), 16):
                        rnd2 = (hash((i, xx - int(x), yy)) % 100) / 100
                        if rnd2 < .45 * min(1, (night - .25) * 3):
                            tw = .75 + .25 * math.sin(t * 1.3 + rnd2 * 40)
                            ctx.set_source_rgba(1, .85, .45, .9 * tw); ctx.rectangle(xx, yy, 7, 9); ctx.fill()
            x += w_ + 4 + (i % 3) * 6; i += 1
        # river
        rc = lerp(hexc('#73BDE6'), hexc('#1E2D5A'), night * .9)
        ctx.rectangle(0, RIVER_Y0, W, RIVER_Y1 - RIVER_Y0); ctx.set_source_rgb(*rc); ctx.fill()
        # bridges (same far layer) with lights at night
        for k in range(int((off - 1200) // 2600), int((off + W) // 2600) + 1):
            bx = 300 + k * 2600 - off
            self._bridge(ctx, bx, bx + 1100, 600, night, t)
        # ripples and night reflections
        ctx.set_line_width(3)
        rnd.seed(7)
        for j in range(30):
            x0 = (rnd.uniform(0, W + 200) - scroll * .3) % (W + 200) - 100; y = rnd.uniform(RIVER_Y0 + 10, RIVER_Y1 - 8); w = rnd.uniform(30, 90)
            ctx.set_source_rgba(1, 1, 1, .6 * (1 - night) + .15); ctx.move_to(x0, y); ctx.line_to(x0 + w, y); ctx.stroke()
        if night > .3:
            for j in range(26):
                x0 = (j * 83 + 40 - off * 1.0) % (W + 80) - 40
                for r_ in range(3):
                    y = RIVER_Y0 + 12 + r_ * 22 + 4 * math.sin(t * 2 + j); w = 18 + 10 * math.sin(t * 3 + j + r_)
                    ctx.set_source_rgba(1, .82, .45, .5 * (night - .3) * (1 - r_ * .25)); ctx.move_to(x0 - w / 2, y); ctx.line_to(x0 + w / 2, y); ctx.stroke()
        ctx.set_source_rgb(*L); ctx.set_line_width(3); ctx.move_to(0, RIVER_Y0); ctx.line_to(W, RIVER_Y0); ctx.stroke()
        # ducks, then boats
        for dx, n in self.ducks:
            x = dx - scroll * .3
            if -200 < x < W + 50 and night < .7: self._ducks(ctx, x, 630, t, n)
        for b in self.boats:
            x = b['v'] * (t - b['t0']) + (W + 250 if b['v'] < 0 else -300)
            if -320 < x < W + 320 and t >= b['t0']: self._boat(ctx, x, b, t, night)
        # lawn
        lc = lerp(hexc('#BFE3B0'), hexc('#24304F'), night * .85)
        ctx.rectangle(0, RIVER_Y1, W, GY - RIVER_Y1); ctx.set_source_rgb(*lc); ctx.fill()
        ctx.set_source_rgb(*L); ctx.set_line_width(3); ctx.move_to(0, RIVER_Y1); ctx.line_to(W, RIVER_Y1); ctx.stroke()
        # two faint footpaths across the lawn
        pc = lerp(hexc('#D9EDCF'), hexc('#2C3858'), night * .85)
        for py, hh in ((FAR_PATH - 6, 10), (NEAR_PATH - 8, 14)):
            ctx.rectangle(0, py, W, hh); ctx.set_source_rgb(*pc); ctx.fill()
        if night < .35:
            for kx, ky, kc in self.kites:
                x = kx - scroll * .3
                if -100 < x < W + 100: self._kite(ctx, x + 14 * math.sin(t * 1.3 + kx), ky + 10 * math.sin(t * 1.7 + kx), kc, 1 - night / .35)

    def _sky_things(self, ctx, t, scroll, night):
        if night > .55: return
        for s in self.sky:
            k = t - s['t0']
            if not 0 <= k < 60: continue
            if s['kind'] == 'balloon':
                x = W + 120 - k * 38; y = s['y'] + 10 * math.sin(k * .5)
                ctx.move_to(x - 40, y); ctx.curve_to(x - 44, y - 70, x + 44, y - 70, x + 40, y); ctx.curve_to(x + 30, y + 30, x + 10, y + 46, x, y + 50)
                ctx.curve_to(x - 10, y + 46, x - 30, y + 30, x - 40, y); ctx.close_path(); fill(ctx, s['col'], 3)
                ctx.move_to(x - 14, y - 50); ctx.curve_to(x - 20, y - 10, x - 10, y + 30, x - 4, y + 50); ctx.stroke()
                ctx.move_to(x + 14, y - 50); ctx.curve_to(x + 20, y - 10, x + 10, y + 30, x + 4, y + 50); ctx.stroke()
                ctx.rectangle(x - 10, y + 62, 20, 16); fill(ctx, '#C68B59')
                ctx.move_to(x - 8, y + 50); ctx.line_to(x - 8, y + 62); ctx.move_to(x + 8, y + 50); ctx.line_to(x + 8, y + 62); ctx.stroke()
            else:
                x = -200 + k * 90; y = s['y'] - k * 1.5
                if x > W + 200: continue
                ctx.set_source_rgba(1, 1, 1, .7 * (1 - night)); ctx.set_line_width(4); ctx.move_to(max(-200, x - 500), y + 4); ctx.line_to(x - 30, y + 2); ctx.stroke()
                ctx.move_to(x - 30, y); ctx.line_to(x + 20, y - 3); ctx.line_to(x + 30, y); ctx.line_to(x - 30, y + 6); ctx.close_path(); fill(ctx, '#FFFFFF', 2.5)
                ctx.move_to(x - 4, y); ctx.line_to(x - 14, y - 12); ctx.stroke(); ctx.move_to(x - 26, y); ctx.line_to(x - 32, y - 10); ctx.stroke()

    def _bridge(self, ctx, x0, x1, y, night, t):
        if x1 < -50 or x0 > W + 50: return
        ctx.set_line_width(3); ctx.rectangle(x0, y - 12, x1 - x0, 12); fill(ctx, '#F5F0E6')
        a, b = x0 + (x1 - x0) * .25, x0 + (x1 - x0) * .75
        for tx in (a, b): ctx.rectangle(tx - 9, y - 150, 18, 150); fill(ctx, '#FF8A6B')
        ctx.set_source_rgb(*_L)
        ctx.move_to(x0, y - 12); ctx.curve_to(x0 + 60, y - 60, a - 40, y - 120, a, y - 145)
        ctx.curve_to(a + 80, y - 40, b - 80, y - 40, b, y - 145); ctx.curve_to(b + 40, y - 120, x1 - 60, y - 60, x1, y - 12); ctx.stroke()
        for hx in range(int(a) + 40, int(b) - 30, 40):   # hangers
            u = (hx - a) / (b - a); cy = y - 145 + 4 * 105 * u * (1 - u) * 1.0
            ctx.set_line_width(1.5); ctx.move_to(hx, cy); ctx.line_to(hx, y - 12); ctx.stroke()
        if night > .3:
            for j in range(24):
                u = j / 23; hx = a + (b - a) * u; cy = y - 145 + 4 * 105 * u * (1 - u)
                on = .6 + .4 * math.sin(t * 2 + j)
                ctx.set_source_rgba(1, .9, .55, (night - .3) * 1.4 * on); ctx.arc(hx, cy, 3.5, 0, 2 * math.pi); ctx.fill()
            for hx in range(int(x0) + 20, int(x1), 60):
                ctx.set_source_rgba(1, .85, .5, (night - .3) * 1.2); ctx.arc(hx, y - 14, 3, 0, 2 * math.pi); ctx.fill()

    def _ducks(self, ctx, x, y, t, n):
        for i in range(n):
            s = 1 if i == 0 else .7; xx = x + i * 30; yy = y + math.sin(t * 2 + i) * 2
            ctx.save(); ctx.translate(xx, yy); ctx.scale(s * .8, s * .8)
            ctx.save(); ctx.scale(1, .55); ctx.arc(0, 0, 16, 0, 2 * math.pi); ctx.restore(); fill(ctx, '#FFFFFF' if i == 0 else '#FFE48A', 2.5)
            ctx.arc(12, -12, 7, 0, 2 * math.pi); fill(ctx, '#FFFFFF' if i == 0 else '#FFE48A')
            ctx.set_source_rgb(*nf(hexc('#FFB21A'))); ctx.set_line_width(4); ctx.move_to(18, -12); ctx.line_to(26, -10); ctx.stroke(); ctx.restore()

    def _boat(self, ctx, x, b, t, night):
        y = b['y']; face = 1 if b['v'] > 0 else -1
        ctx.save(); ctx.translate(x, y); ctx.scale(face, 1); ctx.set_line_width(3)
        if b['kind'] == 'ferry':
            ctx.move_to(-90, 0); ctx.line_to(90, 0); ctx.line_to(70, 24); ctx.line_to(-74, 24); ctx.close_path(); fill(ctx, '#FFFFFF')
            ctx.rectangle(-60, -32, 110, 32); fill(ctx, b['col'])
            for i in range(4):
                ctx.rectangle(-50 + i * 24, -24, 14, 14)
                if night > .3: ctx.set_source_rgba(1, .85, .45, 1); ctx.fill_preserve(); ctx.set_source_rgb(*_L); ctx.stroke()
                else: fill(ctx, '#FFFDF6')
            ctx.rectangle(30, -56, 14, 24); fill(ctx, '#FF5C8A')
        elif b['kind'] == 'sail':
            ctx.move_to(-50, 0); ctx.curve_to(-20, 18, 30, 18, 50, 0); ctx.close_path(); fill(ctx, '#FFFFFF')
            ctx.move_to(0, 0); ctx.line_to(0, -110); ctx.stroke()
            ctx.move_to(4, -104); ctx.line_to(48, -8); ctx.line_to(4, -8); ctx.close_path(); fill(ctx, b['col'])
            ctx.move_to(-4, -90); ctx.line_to(-36, -8); ctx.line_to(-4, -8); ctx.close_path(); fill(ctx, '#FFFDF6')
        else:
            ctx.move_to(-56, 0); ctx.curve_to(-28, 12, 28, 12, 56, 0); ctx.curve_to(28, -4, -28, -4, -56, 0); fill(ctx, b['col'])
            ctx.arc(0, -20, 10, 0, 2 * math.pi); fill(ctx, props.SKINS[1])
            a = math.sin(t * 3) * .5; ctx.set_line_width(4)
            if b['kind'] == 'kayak':
                ctx.move_to(-34 * math.cos(a), -8 - 18 * math.sin(a)); ctx.line_to(34 * math.cos(a), -8 + 18 * math.sin(a)); ctx.stroke()
            else:
                ctx.move_to(-10, -6); ctx.line_to(-40 - 10 * math.sin(t * 2), 6); ctx.move_to(10, -6); ctx.line_to(40 + 10 * math.sin(t * 2), 6); ctx.stroke()
        ctx.restore()

    def _kite(self, ctx, x, y, col, a):
        ctx.push_group()
        ctx.move_to(x, y - 30); ctx.line_to(x + 22, y); ctx.line_to(x, y + 30); ctx.line_to(x - 22, y); ctx.close_path(); fill(ctx, col, 3)
        ctx.move_to(x, y - 30); ctx.line_to(x, y + 30); ctx.move_to(x - 22, y); ctx.line_to(x + 22, y); ctx.set_line_width(1.5); ctx.stroke()
        ctx.set_line_width(2); ctx.move_to(x, y + 30)
        for j in range(1, 5): ctx.line_to(x + 8 * math.sin(j * 1.3), y + 30 + j * 16)
        ctx.stroke()
        for j in (1, 3): ctx.arc(x + 8 * math.sin(j * 1.3), y + 30 + j * 16, 4, 0, 2 * math.pi); fill(ctx, col, 1.5)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(a)

    # ---------------------------------------------------------------- people on the lawn
    def actors(self, ctx, t, scroll, night, L, which):
        global _N, _L
        _N, _L = night, L
        for w in self.walkers:
            if w['path'] != which or t < w['t0']: continue
            wx = w['wx0'] + w['v'] * (t - w['t0']); x = wx - scroll
            if not -300 < x < W + 300: continue
            face = 1 if w['v'] > 0 else -1; s = .72 if which == NEAR_PATH else .55; gy = which
            ph = t * (11 if w['kind'] in ('jog',) else 6) + w['seed']
            k = w['kind']
            if k == 'walk': figure(ctx, x, gy, ph, w['look'], face, s)
            elif k == 'balloon':
                figure(ctx, x, gy, ph, w['look'], face, s * .7)
                sw = math.sin(t * 2 + w['seed']) * 6; bx = x + face * 14 * s
                ctx.set_source_rgb(*_L); ctx.set_line_width(2); ctx.move_to(bx, gy - 70 * s); ctx.line_to(bx + sw, gy - 160 * s); ctx.stroke()
                ctx.save(); ctx.translate(bx + sw, gy - 184 * s); ctx.scale(.85, 1); ctx.arc(0, 0, 24 * s, 0, 2 * math.pi); ctx.restore(); fill(ctx, w['look2']['top'], 2.5)
                figure(ctx, x - face * 46 * s, gy, ph + 1, w['look2'], face, s)
            elif k == 'couple':
                figure(ctx, x, gy, ph, w['look'], face, s, arm='hold'); figure(ctx, x - face * 52 * s, gy, ph + .8, w['look2'], face, s)
            elif k == 'jog': figure(ctx, x, gy, ph, w['look'], face, s, run=True)
            elif k == 'kids':
                figure(ctx, x, gy, ph * 1.3, w['look'], face, s * .62, run=True); figure(ctx, x - face * 50 * s, gy, ph * 1.3 + 2, w['look2'], face, s * .58, run=True)
            elif k == 'stroller':
                stroller(ctx, x + face * 70 * s, gy, s, face); figure(ctx, x, gy, ph, w['look'], face, s, arm='hold')
            elif k == 'dogwalk':
                fur, dark = w['fur']; dx = x + face * 110 * s
                dog(ctx, dx, gy, ph * 1.2, fur, dark, s * .8, face, t)
                ctx.set_source_rgb(*_L); ctx.set_line_width(2); ctx.move_to(x + face * 44 * s, gy - 52 * s); ctx.curve_to(x + face * 70 * s, gy - 30 * s, dx, gy - 70 * s, dx + face * 18 * s, gy - 52 * s); ctx.stroke()
                figure(ctx, x, gy, ph, w['look'], face, s, arm='hold')
            elif k == 'bike': bike(ctx, x, gy, ph * 1.4 * face, dict(w['look'], frame=w['look2']['top'], helmet=w['look']['cap']), s, face)
            elif k == 'skate': skater(ctx, x, gy, ph, w['look'], s, face)

    # ---------------------------------------------------------------- near overlays
    def front(self, ctx, t, scroll, phase, walk, night, L, fx):
        global _N, _L
        _N, _L = night, L
        for a, b, (fur, dark) in self.visits:     # a dog runs up, trots beside the walker, then runs on ahead
            if a - 1.6 <= t <= b + 2.5:
                if t < a: x = CX + 230 - (a - t) * 520
                elif t <= b: x = CX + 230 + 6 * math.sin(t * 2)
                else: x = CX + 230 + (t - b) * 620
                dog(ctx, x, GY + 2, t * 7 if (t < a or t > b) else phase * 1.6 + 1, fur, dark, .6, 1, t)
        if night > .45:   # fireflies over the lawn
            for x0, y0, p in self.flies:
                x = (x0 + 30 * math.sin(t * .4 + p)) % W; y = y0 + 12 * math.sin(t * .7 + p)
                a = (night - .45) * 1.8 * (.5 + .5 * math.sin(t * 2.2 + p * 3))
                g = cairo.RadialGradient(x, y, 0, x, y, 12); g.add_color_stop_rgba(0, 1, .95, .55, a); g.add_color_stop_rgba(1, 1, .95, .55, 0)
                ctx.set_source(g); ctx.arc(x, y, 12, 0, 2 * math.pi); ctx.fill()
        r = fx('rain')
        if r > .01:
            ctx.set_source_rgba(.85, .92, 1, .55 * r); ctx.set_line_width(2)
            for j in range(140):
                x = (j * 137 + t * 90) % (W + 100) - 50; y = (j * 263 + t * 900) % (GY + 60) - 60
                ctx.move_to(x, y); ctx.line_to(x - 6, y + 22); ctx.stroke()
            ctx.set_source_rgba(.3, .35, .5, .12 * r); ctx.rectangle(0, 0, W, GY); ctx.fill()
        rb = fx('rainbow')
        if rb > .01:
            for j, c in enumerate(('#FF5C8A', '#FF8A3D', '#FFD34D', '#7FD99A', '#5BC0EB', '#9B7BFF')):
                ctx.set_source_rgba(*hexc(c), .45 * rb); ctx.set_line_width(14); ctx.arc(W * .62, GY + 40, 620 - j * 14, math.pi, 2 * math.pi); ctx.stroke()
        bu = fx('bubbles')
        if bu > .01:
            for j in range(22):
                k = (t * .25 + j / 22) % 1; x = CX + 120 + j * 37 % 700 + 40 * math.sin(t + j); y = GY - 80 - k * 520
                ctx.set_source_rgba(1, 1, 1, .5 * bu * (1 - k)); ctx.arc(x, y, 8 + j % 4 * 3, 0, 2 * math.pi); ctx.fill_preserve()
                ctx.set_source_rgba(*hexc('#7FC8F8'), .8 * bu * (1 - k)); ctx.set_line_width(2); ctx.stroke()

    def ground(self, ctx, scroll, night, L):
        ctx.rectangle(0, GY, W, H - GY); ctx.set_source_rgb(*lerp(hexc('#E3F1E0'), hexc('#1A1F3D'), night)); ctx.fill()
        ctx.rectangle(0, GY, W, 70); ctx.set_source_rgb(*lerp(hexc('#A8D5A2'), hexc('#22304A'), night)); ctx.fill()
        ctx.set_source_rgba(*L, .45); ctx.set_line_width(2)
        for x in range(10 - int(scroll) % 34, W, 34): ctx.move_to(x, GY + 70); ctx.line_to(x + 5, GY + 58); ctx.stroke()
        ctx.set_source_rgb(*L); ctx.set_line_width(4); ctx.move_to(0, GY); ctx.line_to(W, GY); ctx.stroke()

# ------------------------------------------------------------------ static park scenery
def gen(z, x, xe, rnd, objs, accent):
    x += 40; xe -= 100
    while x < xe:
        a = rnd.choice(accent)
        if z == 'lawn':
            k = rnd.random()
            if k < .4: objs.append(('rv_tree', x + 70, rnd.randint(64, 88), rnd.randint(110, 150), rnd.choice(['#7CC47F', '#95D18A', '#6FBF73']))); x += rnd.randint(180, 240)
            elif k < .6: objs.append(('rv_bench', x + 60, rnd.random() < .5, rnd.choice(LOOKS))); x += 190
            elif k < .8: objs.append(('rv_flowerbed', x, rnd.randint(4, 7))); x += 200
            else: objs.append(('lamp', x + 20)); x += 90
        elif z == 'picnic':
            k = rnd.random()
            if k < .45: objs.append(('rv_picnic', x + 100, rnd.choice(['#FF8A9B', '#FFD86B', '#7FC8F8', '#B8D85A']), rnd.sample(LOOKS, 2))); x += 260
            elif k < .7: objs.append(('rv_kiteflyer', x + 40, rnd.choice(LOOKS), rnd.choice(['#FF5C8A', '#FFB21A', '#7B3BFF', '#3D9BFF']))); x += 160
            else: objs.append(('rv_tree', x + 70, rnd.randint(64, 88), rnd.randint(110, 150), '#7CC47F')); x += 200
        elif z == 'plaza':
            k = rnd.random()
            recent = {o[0] for o in objs[-4:]}
            if k < .2 and 'rv_icecart' not in recent: objs.append(('rv_icecart', x)); x += 220
            elif k < .45 and 'rv_busker' not in recent: objs.append(('rv_busker', x + 80, rnd.choice(LOOKS))); x += 230
            elif k < .65: objs.append(('rv_pigeons', x + 20)); x += 200
            elif k < .82 and 'rv_bubblekid' not in recent: objs.append(('rv_bubblekid', x + 40, rnd.choice(LOOKS))); x += 170
            elif k < .9: objs.append(('rv_tree', x + 70, rnd.randint(64, 88), rnd.randint(110, 150), '#7CC47F')); x += 200
            else: objs.append(('lamp', x + 20)); x += 90
        elif z == 'promenade':
            k = rnd.random()
            if k < .35: objs.append(('lamp', x + 20)); x += 120
            elif k < .6: objs.append(('rv_bench', x + 60, rnd.random() < .6, rnd.choice(LOOKS))); x += 190
            elif k < .8: objs.append(('rv_pigeons', x + 20)); x += 180
            else: objs.append(('rv_flowerbed', x, rnd.randint(3, 5))); x += 160
        elif z == 'garden':
            k = rnd.random()
            if k < .5: objs.append(('rv_flowerbed', x, rnd.randint(5, 8))); x += 230
            elif k < .75: objs.append(('rv_tree', x + 70, rnd.randint(70, 90), rnd.randint(120, 150), '#95D18A')); x += 200
            else: objs.append(('rv_gardener', x + 50, rnd.choice(LOOKS))); x += 170
        elif z == 'sports':
            k = rnd.random()
            if k < .35: objs.append(('rv_badminton', x + 20, rnd.sample(LOOKS, 2))); x += 300
            elif k < .6: objs.append(('rv_tree', x + 70, 70, 120, '#6FBF73')); x += 190
            else: objs.append(('rv_stretch', x + 40, rnd.choice(LOOKS))); x += 150

def draw(ctx, o, sx, L, night, t, nf_unused=None):
    global _N, _L
    _N, _L = night, L
    ctx.set_source_rgb(*L); ctx.set_line_width(3)
    k = o[0]
    if k == 'rv_tree':
        _, _, r, h, col = o
        ctx.set_line_width(4); ctx.move_to(sx, GY); ctx.line_to(sx, GY - h); ctx.stroke()
        blobs(ctx, [(sx, GY - h - r * .3, r), (sx - r * .7, GY - h + r * .2, r * .75), (sx + r * .7, GY - h + r * .15, r * .8)], col)
    elif k == 'rv_bench':
        _, _, sitter, look = o
        if sitter:
            props.npc(ctx, sx + 20, GY, t, L, dict(look, style=look['style'] if look['style'] != 'cap' else 'short'), pose='sip' if hash(o[1]) % 2 else 'sit', face=-1, s=.72, nf=nf)
        ctx.rectangle(sx - 50, GY - 50, 110, 10); fill(ctx, '#D9A066')
        ctx.rectangle(sx - 50, GY - 84, 110, 10); fill(ctx, '#D9A066')
        ctx.set_source_rgb(*L)
        for bx in (sx - 40, sx + 50): ctx.move_to(bx, GY - 40); ctx.line_to(bx, GY); ctx.stroke()
    elif k == 'rv_flowerbed':
        _, _, n = o
        ctx.move_to(sx - 10, GY); ctx.curve_to(sx, GY - 30, sx + n * 26, GY - 30, sx + n * 26 + 10, GY); ctx.close_path(); fill(ctx, '#7CC47F')
        cols = ['#FF5C8A', '#FFB21A', '#FFFFFF', '#9B7BFF', '#FF8A3D']
        for i in range(n):
            fx = sx + 8 + i * 26; fh = 34 + (hash((o[1], i)) % 24)
            ctx.set_source_rgb(*L); ctx.set_line_width(2.5); ctx.move_to(fx, GY - 20); ctx.line_to(fx, GY - fh); ctx.stroke()
            ctx.arc(fx, GY - fh, 9, 0, 2 * math.pi); fill(ctx, cols[(hash((o[1], i, 2))) % len(cols)], 2.5)
            ctx.arc(fx, GY - fh, 3.5, 0, 2 * math.pi); fill(ctx, '#FFE48A', 1.5)
    elif k == 'rv_picnic':
        _, _, col, (l1, l2) = o
        ctx.save(); ctx.translate(sx, GY - 8); ctx.scale(1, .3); ctx.rectangle(-100, -60, 200, 120); ctx.restore(); fill(ctx, col)
        props.npc(ctx, sx - 50, GY - 10, t, L, dict(l1, style='long' if l1['style'] == 'cap' else l1['style']), pose='sit', face=1, s=.62, nf=nf)
        props.npc(ctx, sx + 56, GY - 10, t, L, dict(l2, style='bun' if l2['style'] == 'cap' else l2['style']), pose='sip', face=-1, s=.62, nf=nf)
        ctx.rectangle(sx - 10, GY - 34, 30, 20); fill(ctx, '#C68B59')
        ctx.move_to(sx - 6, GY - 34); ctx.curve_to(sx - 6, GY - 50, sx + 16, GY - 50, sx + 16, GY - 34); ctx.stroke()
    elif k == 'rv_kiteflyer':
        _, _, look, col = o
        props.npc(ctx, sx, GY, t, L, dict(look, style='short' if look['style'] == 'cap' else look['style']), pose='wave', face=1, s=.78, dt=t, nf=nf)
        if night < .4:
            kx, ky = sx + 160 + 20 * math.sin(t * 1.1 + sx * .01), GY - 470 + 16 * math.sin(t * 1.6)
            ctx.set_source_rgba(*L, .8); ctx.set_line_width(1.5); ctx.move_to(sx + 22, GY - 160); ctx.curve_to(sx + 80, GY - 260, kx - 40, ky + 120, kx, ky + 30); ctx.stroke()
            ctx.move_to(kx, ky - 30); ctx.line_to(kx + 22, ky); ctx.line_to(kx, ky + 30); ctx.line_to(kx - 22, ky); ctx.close_path(); fill(ctx, col, 3)
    elif k == 'rv_icecart':
        ctx.rectangle(sx, GY - 90, 120, 60); fill(ctx, '#FFF4E0')
        for i in range(4): ctx.rectangle(sx + i * 30, GY - 112, 30, 22); fill(ctx, '#FF8A9B' if i % 2 else '#FFFFFF')
        for wx in (sx + 24, sx + 96): ctx.arc(wx, GY - 16, 14, 0, 2 * math.pi); fill(ctx, '#FFFFFF')
        ctx.set_source_rgb(*L); ctx.move_to(sx + 60, GY - 112); ctx.line_to(sx + 60, GY - 170); ctx.stroke()
        ctx.move_to(sx + 10, GY - 170); ctx.curve_to(sx + 30, GY - 200, sx + 90, GY - 200, sx + 110, GY - 170); ctx.close_path(); fill(ctx, '#FFB21A')
        for i, c in enumerate(('#FF8A9B', '#FFE48A', '#9B7BFF')):
            ctx.arc(sx + 30 + i * 30, GY - 70, 9, 0, 2 * math.pi); fill(ctx, c, 2)
    elif k == 'rv_busker':
        _, _, look = o
        props.npc(ctx, sx, GY, t, L, dict(look, style='short' if look['style'] == 'cap' else look['style']), pose='sit', face=1, s=.72, nf=nf)
        ctx.save(); ctx.translate(sx + 12, GY - 52); ctx.rotate(-.5); ctx.scale(.72, .72)
        ctx.arc(0, 0, 20, 0, 2 * math.pi); fill(ctx, '#D9A066'); ctx.rectangle(16, -5, 60, 10); fill(ctx, '#8A5A3C'); ctx.restore()
        for i in range(3):
            u = (t * .6 + i / 3) % 1; note(ctx, sx + 10 + 30 * u + 10 * math.sin(u * 6), GY - 140 - 120 * u, 1 - u)
        ctx.rectangle(sx - 70, GY - 16, 44, 16); fill(ctx, '#4A3F35')
    elif k == 'rv_pigeons':
        dist = sx - CX     # they lift off as the walker comes close
        kk = max(0.0, (260 - dist) / 260)
        for i, (dx, dy) in enumerate(((0, 0), (34, 4), (70, -2), (100, 3), (128, 1))):
            q = max(0, kk * 1.6 - i * .12)
            px, py = sx + dx + 220 * q, GY + dy - 4 - 380 * q * q - 60 * q
            ctx.save(); ctx.translate(px, py)
            if q <= 0:
                peck = max(0, math.sin(t * 3 + i * 1.7)) * 4
                ctx.save(); ctx.scale(1, .7); ctx.arc(0, -10, 12, 0, 2 * math.pi); ctx.restore(); fill(ctx, '#B8BEC9', 2.5)
                ctx.arc(10, -20 + peck, 6, 0, 2 * math.pi); fill(ctx, '#B8BEC9', 2.5)
            else:
                f = math.sin(t * 30 + i) * 10
                ctx.set_source_rgb(*L); ctx.set_line_width(3); ctx.move_to(-16, -f); ctx.curve_to(-8, -6, -2, -4, 0, 0); ctx.curve_to(2, -4, 8, -6, 16, -f); ctx.stroke()
            ctx.restore()
    elif k == 'rv_bubblekid':
        _, _, look = o
        props.npc(ctx, sx, GY, t, L, dict(look, style='short' if look['style'] == 'cap' else look['style']), pose='wave', face=1, s=.55, dt=t, nf=nf)
        for j in range(6):
            u = (t * .35 + j / 6) % 1; bx = sx + 30 + 140 * u + 16 * math.sin(t * 2 + j); by = GY - 110 - 260 * u
            ctx.set_source_rgba(1, 1, 1, .5 * (1 - u)); ctx.arc(bx, by, 7 + j % 3 * 4, 0, 2 * math.pi); ctx.fill_preserve()
            ctx.set_source_rgba(*hexc('#7FC8F8'), (1 - u)); ctx.set_line_width(2); ctx.stroke()
    elif k == 'rv_gardener':
        _, _, look = o
        props.npc(ctx, sx, GY, t, L, dict(look, style='bun' if look['style'] == 'cap' else look['style']), pose='water', face=1, s=.72, dt=t, nf=nf)
    elif k == 'rv_badminton':
        _, _, (l1, l2) = o
        u = (t * .7) % 2; u = u if u < 1 else 2 - u
        props.npc(ctx, sx, GY, t, L, dict(l1, style='short'), pose='wave', face=1, s=.7, dt=t, nf=nf)
        props.npc(ctx, sx + 240, GY, t, L, dict(l2, style='long'), pose='wave', face=-1, s=.7, dt=t + 1, nf=nf)
        bx = sx + 40 + 160 * u; by = GY - 170 - 120 * math.sin(u * math.pi)
        ctx.arc(bx, by, 6, 0, 2 * math.pi); fill(ctx, '#FFFFFF', 2)
    elif k == 'rv_stretch':
        _, _, look = o
        props.npc(ctx, sx, GY, t, L, dict(look, style='bun' if look['style'] == 'cap' else look['style']), pose='wave' if math.sin(t) > 0 else 'stand', face=-1, s=.72, dt=t, nf=nf)
    elif k == 'piece':
        return False
    ctx.set_source_rgb(*L)
    return True

# ------------------------------------------------------------------ lyric pieces for VOL.02 songs
props.WIDTH.update({'rv_readers': 360, 'rv_pingpong': 440, 'rv_jar': 360, 'rv_dogmeet': 380, 'rv_lamps': 620,
                    'rv_beach': 460, 'rv_busstop': 380, 'rv_metro': 360, 'rv_rink': 520, 'rv_photobooth': 300,
                    'rv_sunflowers': 520, 'rv_awning': 420, 'rv_kitekids': 420, 'rv_bowling': 380})

def piece(ctx, name, sx, t, dt, L, night, opts, draw_obj, wx):
    global _N, _L
    _N, _L = night, L
    acc = opts.get('color', '#FF5C8A')
    ctx.set_line_width(3); ctx.set_source_rgb(*L)
    W_ = props.WIDTH.get(name, 400)
    if name == 'rv_readers':        # two people reading on a blanket, a little record player
        ctx.save(); ctx.translate(sx + 180, GY - 10); ctx.scale(1, .3); ctx.rectangle(-170, -60, 340, 120); ctx.restore(); fill(ctx, acc)
        props.npc(ctx, sx + 110, GY - 12, t, L, dict(skin=1, hair=0, top='#7FC8F8', style='short'), pose='sit', face=1, s=.7, nf=nf)
        props.npc(ctx, sx + 230, GY - 12, t, L, dict(skin=0, hair=3, top='#FFD86B', style='long'), pose='sit', face=-1, s=.7, nf=nf)
        for bx in (sx + 128, sx + 196):
            ctx.save(); ctx.translate(bx, GY - 64); ctx.rotate(-.3 if bx < sx + 150 else .3); ctx.rectangle(-14, -10, 28, 20); ctx.restore(); fill(ctx, '#FFFFFF', 2.5)
        ctx.rectangle(sx + 280, GY - 40, 56, 26); fill(ctx, '#C68B59')
        ctx.save(); ctx.translate(sx + 308, GY - 40); ctx.scale(1, .35); ctx.arc(0, 0, 22, 0, 2 * math.pi); ctx.restore(); fill(ctx, '#2B2541', 2)
        for i in range(2):
            u = (t * .5 + i / 2) % 1; note(ctx, sx + 300 + 20 * u, GY - 70 - 90 * u, 1 - u, '#FF5C8A')
    elif name == 'rv_pingpong':
        ctx.rectangle(sx + 80, GY - 90, 280, 16); fill(ctx, '#2EA36B')
        ctx.move_to(sx + 220, GY - 90); ctx.line_to(sx + 220, GY - 112); ctx.set_line_width(4); ctx.stroke(); ctx.set_line_width(3)
        ctx.set_source_rgb(*nf((1, 1, 1))); ctx.move_to(sx + 84, GY - 82); ctx.line_to(sx + 356, GY - 82); ctx.stroke(); ctx.set_source_rgb(*L)
        for lx in (sx + 100, sx + 340): ctx.move_to(lx, GY - 74); ctx.line_to(lx, GY); ctx.stroke()
        props.npc(ctx, sx + 40, GY, t, L, dict(skin=2, hair=1, top='#FF5C8A', style='short'), pose='wave', face=1, s=.8, dt=dt * 2, nf=nf)
        props.npc(ctx, sx + 410, GY, t, L, dict(skin=0, hair=2, top='#3D9BFF', style='long'), pose='wave', face=-1, s=.8, dt=dt * 2 + .7, nf=nf)
        u = (dt * 1.4) % 2; u = u if u < 1 else 2 - u
        bx = sx + 90 + 260 * u; by = GY - 96 - 90 * abs(math.sin(u * math.pi * 1.5))
        ctx.arc(bx, by, 7, 0, 2 * math.pi); fill(ctx, '#FFFFFF', 2.5)
    elif name == 'rv_jar':            # a peach tree, two chairs, a jar on a little table
        ctx.set_line_width(5); ctx.move_to(sx + 90, GY); ctx.line_to(sx + 90, GY - 150); ctx.stroke(); ctx.set_line_width(3)
        blobs(ctx, [(sx + 90, GY - 210, 80), (sx + 30, GY - 170, 56), (sx + 150, GY - 172, 60)], '#7CC47F')
        for px, py in ((60, -200), (110, -230), (140, -170), (40, -160), (95, -175)):
            ctx.arc(sx + px, GY + py, 10, 0, 2 * math.pi); fill(ctx, '#FFB38A', 2.5)
        ctx.rectangle(sx + 200, GY - 60, 80, 8); fill(ctx, '#D9A066')
        for lx in (sx + 210, sx + 270): ctx.move_to(lx, GY - 52); ctx.line_to(lx, GY); ctx.stroke()
        ctx.rectangle(sx + 226, GY - 100, 28, 40); fill(ctx, '#DFF3FF'); ctx.rectangle(sx + 222, GY - 108, 36, 10); fill(ctx, '#FFB21A')
        for i in range(3): ctx.arc(sx + 240, GY - 88 + i * 10, 6, 0, 2 * math.pi); fill(ctx, '#FFB38A', 2)
        for cx_ in (sx + 180, sx + 310):
            ctx.rectangle(cx_ - 20, GY - 46, 40, 6); fill(ctx, '#FFFFFF'); ctx.move_to(cx_ - 16, GY - 40); ctx.line_to(cx_ - 16, GY); ctx.move_to(cx_ + 16, GY - 40); ctx.line_to(cx_ + 16, GY); ctx.stroke()
    elif name == 'rv_dogmeet':        # two dogs say hello, owners laugh
        ph = t * 3
        props.npc(ctx, sx + 30, GY, t, L, dict(skin=1, hair=1, top='#2EC4A6', style='short'), pose='wave', face=1, s=.82, dt=dt, nf=nf)
        dog(ctx, sx + 140, GY, 0, '#E8B878', '#8A5A3C', .6, 1, t)
        dog(ctx, sx + 260, GY, 0, '#FFFFFF', '#3A3A46', .55, -1, t + 1)
        props.npc(ctx, sx + 350, GY, t, L, dict(skin=3, hair=0, top='#FF8A5B', style='bun'), pose='stand', face=-1, s=.82, nf=nf)
        if dt > 0 and (dt % 3) < 1.6:
            ctx.arc(sx + 200, GY - 110 - 10 * (dt % 3), 10, 0, 2 * math.pi)
            ctx.move_to(sx + 200, GY - 96 - 10 * (dt % 3)); ctx.curve_to(sx + 186, GY - 110 - 10 * (dt % 3), sx + 192, GY - 124 - 10 * (dt % 3), sx + 200, GY - 116 - 10 * (dt % 3))
            ctx.curve_to(sx + 208, GY - 124 - 10 * (dt % 3), sx + 214, GY - 110 - 10 * (dt % 3), sx + 200, GY - 96 - 10 * (dt % 3)); ctx.new_path()
            hx, hy = sx + 200, GY - 120 - 10 * (dt % 3)
            ctx.move_to(hx, hy + 12); ctx.curve_to(hx - 22, hy - 4, hx - 10, hy - 20, hx, hy - 8); ctx.curve_to(hx + 10, hy - 20, hx + 22, hy - 4, hx, hy + 12)
            ctx.set_source_rgb(*hexc('#FF5C8A')); ctx.fill()
    elif name == 'rv_lamps':          # a row of lamps switching on one by one
        for i in range(5):
            lx = sx + 40 + i * 140; on = dt > i * .6
            ctx.set_source_rgb(*L); ctx.move_to(lx, GY); ctx.line_to(lx, GY - 230); ctx.curve_to(lx, GY - 260, lx + 40, GY - 260, lx + 40, GY - 235); ctx.stroke()
            if on:
                a = min(1, (dt - i * .6) / .4) * (.35 + .65 * max(night, .3))
                g = cairo.RadialGradient(lx + 40, GY - 225, 0, lx + 40, GY - 225, 130); g.add_color_stop_rgba(0, 1, .85, .5, .6 * a); g.add_color_stop_rgba(1, 1, .85, .5, 0)
                ctx.set_source(g); ctx.arc(lx + 40, GY - 225, 130, 0, 2 * math.pi); ctx.fill()
            ctx.arc(lx + 40, GY - 228, 9, 0, 2 * math.pi); fill(ctx, '#FFE48A' if on else '#FFFFFF')
    elif name == 'rv_beach':          # a sandy patch: umbrella, towel, sandcastle, a seashell
        ctx.move_to(sx, GY); ctx.curve_to(sx + 60, GY - 30, W_ + sx - 60, GY - 30, sx + W_, GY); ctx.close_path(); fill(ctx, '#FFE3A3')
        draw_obj(ctx, ('umbrella', wx + 120, hexc(acc)), sx + 120, L, night, t)
        draw_obj(ctx, ('sandcastle', wx + 340), sx + 340, L, night, t)
        ctx.save(); ctx.translate(sx + 230, GY - 10); ctx.rotate(-.2); ctx.arc(0, 0, 14, math.pi, 0); ctx.close_path(); ctx.restore(); fill(ctx, '#FF9EB5', 2.5)
        props.npc(ctx, sx + 200, GY, t, L, dict(skin=2, hair=3, top='#FF8A5B', style='long'), pose='sit', face=1, s=.6, nf=nf)
    elif name == 'rv_busstop':
        ctx.rectangle(sx + 20, GY - 210, 220, 16); fill(ctx, acc)
        for px in (sx + 30, sx + 230): ctx.move_to(px, GY - 194); ctx.line_to(px, GY); ctx.stroke()
        ctx.rectangle(sx + 50, GY - 60, 160, 10); fill(ctx, '#FFFFFF')
        ctx.rectangle(sx + 270, GY - 200, 50, 50); fill(ctx, '#FFFFFF'); ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(22); ctx.set_source_rgb(*L); ctx.move_to(sx + 281, GY - 167); ctx.show_text('BUS')
        ctx.move_to(sx + 295, GY - 150); ctx.line_to(sx + 295, GY); ctx.stroke()
        bx = sx + 900 - 320 * max(0, dt + 1.5) if dt < 1.5 else sx + 420 - 300 * max(0, dt - 4)
        if -500 < bx - sx < 1200:
            ctx.rectangle(bx, GY - 170, 380, 150); fill(ctx, '#FFC233')
            for i in range(4): ctx.rectangle(bx + 20 + i * 88, GY - 150, 66, 50); fill(ctx, '#DFF3FF')
            for wxo in (60, 320): ctx.arc(bx + wxo, GY - 16, 18, 0, 2 * math.pi); fill(ctx, '#3A3A46')
        sig = '#2EC4A6'
        ctx.rectangle(sx + 360, GY - 260, 30, 80); fill(ctx, '#3A3A46')
        for i, c in enumerate(('#FF5C8A', '#FFD34D', sig)):
            ctx.arc(sx + 375, GY - 246 + i * 24, 8, 0, 2 * math.pi); fill(ctx, c if i == 2 else '#5A5A66', 2)
        ctx.move_to(sx + 375, GY - 180); ctx.line_to(sx + 375, GY); ctx.stroke()
    elif name == 'rv_metro':
        ctx.rectangle(sx + 40, GY - 160, 280, 160); fill(ctx, '#E9EEF5')
        ctx.rectangle(sx + 40, GY - 200, 280, 44); fill(ctx, acc)
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(30); ctx.set_source_rgb(*nf((1, 1, 1)))
        e = ctx.text_extents('METRO'); ctx.move_to(sx + 180 - e.width / 2, GY - 166); ctx.show_text('METRO'); ctx.set_source_rgb(*L)
        for i in range(5): ctx.move_to(sx + 80, GY - 20 - i * 26); ctx.line_to(sx + 280, GY - 20 - i * 26); ctx.stroke()
        props.npc(ctx, sx + 200, GY, t, L, dict(skin=0, hair=1, top='#FF8A5B', style='long'), pose='wave', face=1, s=.8, dt=dt, nf=nf)
    elif name == 'rv_rink':           # a little roller rink: skaters circling under a mirror ball
        ctx.save(); ctx.translate(sx + W_ / 2, GY - 10); ctx.scale(1, .22); ctx.arc(0, 0, W_ / 2 - 10, 0, 2 * math.pi); ctx.restore(); fill(ctx, '#C9A7FF')
        ctx.move_to(sx + W_ / 2, GY - 330); ctx.line_to(sx + W_ / 2, GY - 270); ctx.stroke()
        ctx.arc(sx + W_ / 2, GY - 250, 22, 0, 2 * math.pi); fill(ctx, '#E9EEF5')
        for j in range(8):
            a = t * 1.5 + j * .8
            ctx.set_source_rgba(*hexc(['#FF5C8A', '#FFD34D', '#5BC0EB', '#7FD99A'][j % 4]), .6); ctx.arc(sx + W_ / 2 + 200 * math.cos(a), GY - 200 + 60 * math.sin(a * 1.3), 6, 0, 2 * math.pi); ctx.fill()
        for j in range(3):
            a = dt * .9 + j * 2.1; x = sx + W_ / 2 + (W_ / 2 - 80) * math.cos(a); face = -1 if math.sin(a) > 0 else 1
            skater(ctx, x, GY - 6 + 8 * math.sin(a), t * 6 + j, LOOKS[(j * 3 + 1) % len(LOOKS)], .62, face)
    elif name == 'rv_photobooth':
        ctx.rectangle(sx + 40, GY - 280, 200, 280); fill(ctx, acc)
        ctx.rectangle(sx + 60, GY - 250, 160, 30); fill(ctx, '#FFFFFF')
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(20); ctx.set_source_rgb(*L)
        e = ctx.text_extents('PHOTO'); ctx.move_to(sx + 140 - e.width / 2, GY - 228); ctx.show_text('PHOTO')
        ctx.rectangle(sx + 80, GY - 200, 120, 200); fill(ctx, '#3D9BFF')
        for i in range(5):
            ctx.move_to(sx + 84 + i * 28, GY - 200); ctx.curve_to(sx + 90 + i * 28, GY - 120, sx + 80 + i * 28, GY - 60, sx + 88 + i * 28, GY); ctx.stroke()
        fl = max(0, 1 - ((dt % 1.6) / .25)) if dt > 0 and dt < 8 else 0
        if fl > 0:
            g = cairo.RadialGradient(sx + 140, GY - 120, 0, sx + 140, GY - 120, 260); g.add_color_stop_rgba(0, 1, 1, 1, .9 * fl); g.add_color_stop_rgba(1, 1, 1, 1, 0)
            ctx.set_source(g); ctx.arc(sx + 140, GY - 120, 260, 0, 2 * math.pi); ctx.fill()
        for i in range(4):
            if dt > i * 1.6 + .3:
                ctx.rectangle(sx + 250, GY - 200 + i * 44, 36, 40); fill(ctx, '#FFFFFF', 2.5)
                ctx.arc(sx + 268, GY - 182 + i * 44, 8, 0, 2 * math.pi); fill(ctx, props.SKINS[i % 4], 2)
    elif name == 'rv_sunflowers':
        for i in range(9):
            fx = sx + 30 + i * 56; fh = 120 + (i * 37) % 60
            sway = 4 * math.sin(t * 1.5 + i)
            ctx.set_source_rgb(*L); ctx.set_line_width(4); ctx.move_to(fx, GY); ctx.line_to(fx + sway, GY - fh); ctx.stroke(); ctx.set_line_width(3)
            ctx.save(); ctx.translate(fx + 10, GY - fh * .5); ctx.rotate(-.6); ctx.scale(1, .45); ctx.arc(0, 0, 16, 0, 2 * math.pi); ctx.restore(); fill(ctx, '#7CC47F')
            for p in range(10):
                a = p * math.pi / 5
                ctx.save(); ctx.translate(fx + sway + 22 * math.cos(a), GY - fh + 22 * math.sin(a)); ctx.rotate(a); ctx.scale(1, .5); ctx.arc(0, 0, 12, 0, 2 * math.pi); ctx.restore(); fill(ctx, '#FFD34D', 2)
            ctx.arc(fx + sway, GY - fh, 14, 0, 2 * math.pi); fill(ctx, '#8A5A3C')
    elif name == 'rv_awning':         # people sheltering under a striped awning, daisies handed round
        ctx.rectangle(sx + 20, GY - 300, 380, 300); fill(ctx, '#FFF1DC')
        n = 7; aw = 380 / n
        for i in range(n):
            ctx.move_to(sx + 20 + i * aw, GY - 220); ctx.line_to(sx + 20 + (i + 1) * aw, GY - 220); ctx.line_to(sx + 20 + (i + 1) * aw, GY - 190)
            ctx.arc(sx + 20 + (i + .5) * aw, GY - 190, aw / 2, 0, math.pi); ctx.close_path(); fill(ctx, acc if i % 2 == 0 else '#FFFFFF')
        for j in range(4):
            props.npc(ctx, sx + 70 + j * 90, GY, t, L, LOOKS[(j * 5 + 2) % len(LOOKS)] | {'style': ['short', 'long', 'bun', 'short'][j]}, pose='wave' if (j + int(dt)) % 3 == 0 else 'stand', face=-1 if j % 2 else 1, s=.74, dt=dt, nf=nf)
        for j in range(5):
            ctx.arc(sx + 40 + j * 80, GY - 6, 7, 0, 2 * math.pi); fill(ctx, '#FFFFFF', 2)
    elif name == 'rv_kitekids':
        for j in range(3):
            kx = sx + 80 + j * 130
            props.npc(ctx, kx, GY, t, L, LOOKS[(j * 4) % len(LOOKS)] | {'style': 'short'}, pose='wave', face=1, s=.6, dt=t + j, nf=nf)
            if night < .5:
                ky = GY - 380 - j * 40 + 14 * math.sin(t * 1.4 + j); kxx = kx + 120 + 16 * math.sin(t + j)
                ctx.set_source_rgba(*L, .8); ctx.set_line_width(1.5); ctx.move_to(kx + 16, GY - 120); ctx.curve_to(kx + 60, GY - 220, kxx - 30, ky + 100, kxx, ky + 30); ctx.stroke()
                ctx.move_to(kxx, ky - 30); ctx.line_to(kxx + 22, ky); ctx.line_to(kxx, ky + 30); ctx.line_to(kxx - 22, ky); ctx.close_path(); fill(ctx, ['#FF5C8A', '#FFB21A', '#7B3BFF'][j], 3)
                ctx.set_line_width(2); ctx.move_to(kxx, ky + 30)
                for q in range(1, 5): ctx.line_to(kxx + 8 * math.sin(q * 1.3 + t), ky + 30 + q * 16)
                ctx.stroke()
    elif name == 'rv_bowling':
        ctx.rectangle(sx + 20, GY - 300, 340, 300); fill(ctx, '#2E5E9E')
        ctx.rectangle(sx + 50, GY - 280, 280, 60); fill(ctx, '#FFF4DF')
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(36); ctx.set_source_rgb(*nf(hexc('#E0457B')))
        e = ctx.text_extents('BOWLING'); ctx.move_to(sx + 190 - e.width / 2, GY - 236); ctx.show_text('BOWLING'); ctx.set_source_rgb(*L)
        for i in range(5):
            px = sx + 120 + i * 34
            ctx.save(); ctx.translate(px, GY - 120); ctx.scale(.6, 1); ctx.arc(0, 0, 22, 0, 2 * math.pi); ctx.restore(); fill(ctx, '#FFFFFF')
            ctx.set_source_rgb(*nf(hexc('#E0457B'))); ctx.set_line_width(3); ctx.move_to(px - 8, GY - 130); ctx.line_to(px + 8, GY - 130); ctx.stroke()
        ctx.rectangle(sx + 140, GY - 90, 100, 90); fill(ctx, '#FFE3A3')
    ctx.set_source_rgb(*L)
