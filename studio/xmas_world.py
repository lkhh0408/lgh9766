"""PLAY LIST 04 Christmas world for render_video.py (--world xmas).
Six neighbourhoods, each with its own ride and outfit; songs inside a segment end with a stop + headphone tap + play bubble,
and the change to the next segment happens behind advent-calendar doors in the gap. Opening: headphones go on; ending: they come off.
Same interface as seaside.Ride: frame(t) -> (PIL RGB, night 0..1 for the UI, name-tag y offset, bubble alpha)."""
import math, random
import cairo, numpy as np
from PIL import Image
import character as ch
import xmas, xmas_rides as R

W, H = xmas.W, xmas.H
HEAD_Y0 = 658          # head centre of the standard walking Haru; the name tag sits relative to it
NIGHT = {'morning': 0.0, 'day': 0.0, 'golden': 0.1, 'dusk': 0.5, 'night': 1.0, 'aurora': 1.0}
SPEED = {'skate': 230, 'tram': 300, 'dogsled': 420, 'carriage': 150, 'walk': 120, 'sleigh': 260}
# where each ride puts Haru (x of the ride so that her hips are at x 820) and her head height
PLACE = {'skate': (820, 930, 724), 'tram': (860, 950, 730), 'dogsled': (920, 930, 722),
         'carriage': (880, 930, 664), 'walk': (820, 900, 698), 'sleigh': (830, 470, 280)}

def sm(u):
    u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

def bubble(c, x, y, a):
    if a < .02: return
    c.save(); c.translate(x, y); c.push_group(); R.rrect(c, -44, -32, 88, 64, 18); R.shape(c, (1, 1, 1), R.L)
    c.move_to(-12, -16); c.line_to(18, 0); c.line_to(-12, 16); c.close_path(); c.set_source_rgb(*R.hx('#FF2D87')); c.fill()
    c.pop_group_to_source(); c.paint_with_alpha(a); c.restore()

class XRide:
    """segments: [[scene, ride, outfit dict, first track, last track], ...] (tracks 1-based)"""
    def __init__(self, starts, ends, total, fps, segments):
        self.s, self.e, self.total, self.fps = starts, ends, total, fps
        self.seg_of = {}
        self.segs = []
        for k, (scene, ride, outfit, a, b) in enumerate(segments):
            name = f'_xmas{k}'; ch.OUTFITS[name] = dict(outfit)
            self.segs.append((scene, ride, name, a - 1, b - 1))
            for i in range(a - 1, b): self.seg_of[i] = k
        self.n = len(starts)
        # a segment change happens in the gap after the last track of a segment
        self.cuts = {self.segs[k][4]: k + 1 for k in range(len(self.segs) - 1)}
        self.pos = [0.0]
        for f in range(int(total * fps) + 2):
            t = f / fps; k = self.seg_at(t)
            self.pos.append(self.pos[-1] + SPEED[self.segs[k][1]] * self.moving(t) / fps)

    def track_at(self, t):
        """(kind, index): 'pre' before the first song, 'song' i, 'gap' after song i, 'post' after the last"""
        if t < self.s[0]: return 'pre', 0
        for i in range(self.n):
            if t < self.e[i]: return 'song', i
            if i + 1 < self.n and t < self.s[i + 1]: return 'gap', i
        return 'post', self.n - 1

    def seg_at(self, t):
        k, i = self.track_at(t)
        if k == 'gap' and i in self.cuts and t >= (self.e[i] + self.s[i + 1]) / 2: return self.cuts[i]
        return self.seg_of[i]

    def moving(self, t):
        k, i = self.track_at(t)
        if k in ('pre', 'post'): return 0.0
        if k == 'gap': return 0.0
        return min(sm((t - self.s[i]) / .8), 1 - sm((t - (self.e[i] - .8)) / .8))

    def gestures(self, t):
        """reach, press, don, bubble alpha"""
        k, i = self.track_at(t); reach = press = ba = 0.0; don = 1.0
        if k == 'pre':
            don = sm((t - .9) / .9)
            reach = sm((t - .6) / .3) * (1 - sm((t - (self.s[0] - .9)) / .3))
            u = t - (self.s[0] - 1.6); press = max(0, math.sin(u / .5 * math.pi)) if 0 < u < .5 else 0
            ba = sm((t - (self.s[0] - 1.3)) / .2) * (1 - sm((t - self.s[0] - .3) / .3))
        elif k == 'post':
            u = t - self.e[-1]
            don = 1 - sm((u - .5) / 1.2)
            reach = sm((u - .3) / .3) * (1 - sm((u - 2.0) / .3))
        else:
            # tap in the gap after song i (also covers the start of the next song for the bubble fade)
            j = i if k == 'gap' else i - 1
            if j >= 0:
                u = t - self.e[j]; nxt = self.s[j + 1]
                reach = sm((u - .1) / .25) * (1 - sm((u - .95) / .25))
                press = max(0, math.sin((u - .35) / .45 * math.pi)) if .35 < u < .8 else 0
                ba = sm((u - .45) / .2) * (1 - sm((t - nxt - .2) / .3))
                if j in self.cuts:   # the bubble hides before the snow burst
                    mid = (self.e[j] + nxt) / 2; ba *= 1 - sm((t - (mid - .45)) / .2)
        return reach, press, don, ba

    def doors(self):
        """closed advent-calendar doors with "Merry Christmas" in white round script, drawn once"""
        if getattr(self, '_doors', None) is None:
            from PIL import ImageDraw, ImageFont
            import os
            s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
            c.rectangle(0, 0, W, H); c.set_source_rgb(*R.hx('#B8323A')); c.fill()
            c.set_line_width(6); c.set_source_rgb(*R.L); c.move_to(W / 2, 0); c.line_to(W / 2, H); c.stroke()
            c.set_line_width(12); c.set_source_rgb(*R.hx('#F2C230'))
            R.rrect(c, 60, 60, W / 2 - 100, H - 120, 30); c.stroke(); R.rrect(c, W / 2 + 40, 60, W / 2 - 100, H - 120, 30); c.stroke()
            for x in (W / 2 - 40, W / 2 + 40): c.arc(x, H / 2 + 170, 14, 0, 6.3); R.shape(c, R.hx('#F2C230'), R.L)
            s.flush()
            im = Image.fromarray(np.ndarray((H, W, 4), np.uint8, s.get_data())[..., [2, 1, 0]].copy()).convert('RGBA')
            d = ImageDraw.Draw(im); ft = ImageFont.truetype(os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'Pacifico-Regular.ttf'), 170)
            txt = 'Merry Christmas'; bb = d.textbbox((0, 0), txt, font=ft)
            x, y = W / 2 - (bb[2] - bb[0]) / 2 - bb[0], H / 2 - (bb[3] - bb[1]) / 2 - bb[1] - 40
            d.text((x + 4, y + 6), txt, font=ft, fill=(90, 20, 30, 160)); d.text((x, y), txt, font=ft, fill=(255, 255, 255))
            a = np.array(im.convert('RGB')); bgra = np.dstack([a[..., 2], a[..., 1], a[..., 0], np.full(a.shape[:2], 255, np.uint8)]).copy()
            self._doors = cairo.ImageSurface.create_for_data(bgra, cairo.FORMAT_ARGB32, W, H); self._dbuf = bgra
        return self._doors

    def burst(self, c, t):
        """segment change: advent-calendar doors slide shut after the headphone tap, the scene, ride and outfit
        change behind them, and they slide open on the next place"""
        self.cover = 0.0
        for i, k in self.cuts.items():
            mid = (self.e[i] + self.s[i + 1]) / 2
            if mid - .6 < t < mid + .8:
                a = sm((t - (mid - .55)) / .5) if t < mid else 1 - sm((t - (mid + .05)) / .7)
                if a <= 0: continue
                self.cover = a
                off = W / 2 * (1 - a); ds = self.doors()
                c.save(); c.rectangle(0, 0, W / 2 - off, H); c.clip(); c.set_source_surface(ds, -off, 0); c.paint(); c.restore()
                c.save(); c.rectangle(W / 2 + off, 0, W / 2, H); c.clip(); c.set_source_surface(ds, off, 0); c.paint(); c.restore()

    def frame(self, t):
        k = self.seg_at(t); scene, ride, outfit, _, _ = self.segs[k]
        fn, sky = xmas.SCENES[scene]
        f = min(len(self.pos) - 1, int(t * self.fps)); scroll = self.pos[f] + k * 900
        mv = self.moving(t)
        reach, press, don, ba = self.gestures(t)
        tt = t if t < self.e[-1] + 1.0 else self.e[-1] + 1.0   # at the very end the snow holds still
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
        c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        fn(c, sky, scroll, tt)
        x, gy, hy = PLACE[ride]; kw = dict(reach=reach, press=press, don=don)
        if ride == 'skate': R.skate(c, x, gy, tt, outfit, moving=mv, **kw)
        elif ride == 'tram': R.tram(c, x, gy, tt, outfit, moving=mv, **kw)
        elif ride == 'dogsled': R.dogsled(c, x, gy, tt, outfit, moving=mv, **kw)
        elif ride == 'carriage': R.carriage(c, x, gy, tt, outfit, lit=True, moving=mv, **kw)
        elif ride == 'walk': R.haru(c, x, gy, tt, outfit, walk=mv, phase=2 * math.pi * .85 * scroll / 130, **kw)
        else: R.sky_sleigh(c, x, gy, tt, outfit, moving=mv, **kw)
        bubble(c, 826 + 60, hy - 100, ba)
        self.burst(c, t)
        s.flush()
        rgb = np.ndarray((H, W, 4), np.uint8, s.get_data())[..., [2, 1, 0]].copy()
        return Image.fromarray(rgb, 'RGB'), NIGHT[sky], hy - HEAD_Y0, ba
