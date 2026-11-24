"""Haru's Christmas Playlist 01 cover, #18 reworked: the video's reindeer sky sleigh, big across the moon.
python3 cover_pl04_sleigh.py OUTDIR [size]  -> sleigh_A.png (silhouette), sleigh_B.png (full colour), sleigh_sheet.png"""
import sys, json, cairo, numpy as np
from PIL import Image, ImageDraw
OUTDIR = sys.argv[1]; K = int(sys.argv[2]) if len(sys.argv) > 2 else 1
sys.argv = [sys.argv[0], OUTDIR, 'xmas_santa', '01', '#D94040']
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch, xmas_rides as xr
SB = json.load(open('/home/user/lgh9766/playlists/vol04/storyboard.json'))
ch.OUTFITS['xmas_santa'] = dict(SB['segments'][5][2])
from cover_drafts import text, font
from cover_drafts_pl04b import flakes, title, NIGHT, CREAM, W, GOLD
S = 1500

def sleigh_layer(scale=1.0, cx=820, cy=640):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.translate(cx, cy); c.scale(scale, scale); c.translate(-cx, -cy)
    xr.sky_sleigh(c, cx, cy, 0.35, 'xmas_santa', moving=1.0)
    b = np.ndarray((S, S, 4), np.uint8, s.get_data()); a = b[..., 3:4].astype(np.float32) / 255
    rgb = np.where(a > 0, b[..., [2, 1, 0]] / np.maximum(a, 1e-6), 0).clip(0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, b[..., 3]]), 'RGBA')

def cover(silhouette):
    im = Image.new('RGBA', (S, S), NIGHT + (255,)); flakes(im, 200, 11, (255, 255, 255, 200), 5); d = ImageDraw.Draw(im)
    d.ellipse((300, 90, 1200, 990), fill=(255, 236, 170))
    lay = sleigh_layer(1.38, 480, 640)
    if silhouette:
        sil = Image.new('RGBA', lay.size, (10, 12, 26, 255)); sil.putalpha(lay.split()[3]); lay = sil
    im.alpha_composite(lay); d = ImageDraw.Draw(im)
    title(d, 1230, CREAM, W, GOLD, 250); text(d, (S // 2, 1455), 'OPEN TO CLOSE', font('Outfit-800.ttf', 50), CREAM, 'mm', sp=14)
    return im

A, B = cover(True), cover(False)
for n, im in (('A', A), ('B', B)):
    out = im.convert('RGB')
    if K > 1: out = out.resize((S * K, S * K), Image.LANCZOS)
    out.save(f'{OUTDIR}/sleigh_{n}.png')
T = 700; sheet = Image.new('RGB', (2 * T + 120, T + 110), 'white'); dd = ImageDraw.Draw(sheet)
for i, (n, im) in enumerate((('18-A 실루엣 (원래 느낌)', A), ('18-B 컬러 (영상 속 썰매 그대로)', B))):
    x = 40 + i * (T + 40); dd.text((x, 30), n, font=font('NanumSquareRoundB.ttf', 32), fill=(31, 35, 64)); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, 80))
sheet.save(f'{OUTDIR}/sleigh_sheet.png'); print('ok')
