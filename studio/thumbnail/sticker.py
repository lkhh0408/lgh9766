"""Mascot as a die-cut sticker (white border + soft shadow), facing left."""
import sys
import cairo, numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch
V = '/tmp/claude-0/-home-user-lgh9766/b52f1d6d-22f0-5bcd-a4bc-05ad7db7a50f/scratchpad/vid/'
def render(outfit, path, scale=2.7, w=640, h=760):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h); ctx = cairo.Context(s)
    ctx.translate(w / 2, h - 60); ctx.scale(-scale, scale)
    ch.draw(ctx, -6, 0, t=0.5, phase=0.9, walk=1.0, outfit=outfit)
    b = np.ndarray((h, w, 4), np.uint8, s.get_data())
    a = b[..., 3:4].astype(np.float32) / 255
    rgb = np.where(a > 0, b[..., [2, 1, 0]] / np.maximum(a, 1e-6), 0).clip(0, 255).astype(np.uint8)
    art = Image.fromarray(np.dstack([rgb, b[..., 3]]), 'RGBA')
    alpha = art.split()[3]
    border = alpha.filter(ImageFilter.MaxFilter(17)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
    shadow = border.filter(ImageFilter.GaussianBlur(14))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 255)); sh.putalpha(shadow.point(lambda v: int(v * .55)))
    out.alpha_composite(sh, (10, 16))
    wb = Image.new('RGBA', (w, h), (255, 255, 255, 255)); wb.putalpha(border); out.alpha_composite(wb)
    out.alpha_composite(art)
    out.rotate(4, resample=Image.BICUBIC, expand=False).save(path)
render('street', V + 'sticker_street.png')
print('ok')
