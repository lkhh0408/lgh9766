"""Haru's Christmas Playlist 01 cover, #18 reworked (colour, big sleigh, HARU tag, three title styles): the video's reindeer sky sleigh, big across the moon.
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

from PIL import ImageFilter
RED = (217, 64, 64); DRED = (150, 30, 40)
def ribbon(d, cy, txt, fs, col=RED, fg=W, w=None):
    f = font('Outfit-800.ttf', fs); tw = d.textlength(txt, font=f) + fs * 0.25 * len(txt) * .55; w = w or tw + fs * 1.6; h = fs * 1.7
    x0, x1, y0, y1 = S / 2 - w / 2, S / 2 + w / 2, cy - h / 2, cy + h / 2
    for sx in (-1, 1):
        ex = x0 - fs * .9 if sx < 0 else x1 + fs * .9; bx = x0 + fs * .4 if sx < 0 else x1 - fs * .4
        d.polygon([(bx, y0 + fs * .35), (ex, y0 + fs * .35), (ex + sx * -fs * .45, cy + fs * .35 / 2 + fs * .2), (ex, y1 + fs * .35), (bx, y1 + fs * .35)], fill=DRED)
    d.rectangle((x0, y0, x1, y1), fill=col)
    text(d, (S // 2, cy), txt, f, fg, 'mm', sp=int(fs * .25))
def big_script(im, cy, size, fill, stroke, stroke_w, glow=None):
    f = font('Pacifico-Regular.ttf', size)
    if glow:
        g = Image.new('RGBA', im.size); gd = ImageDraw.Draw(g); gd.text((S // 2, cy), 'Christmas', font=f, fill=glow, anchor='mm', stroke_width=stroke_w + 18, stroke_fill=glow)
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(22)))
    d = ImageDraw.Draw(im)
    d.text((S // 2 + 10, cy + 14), 'Christmas', font=f, fill=(0, 0, 0, 110), anchor='mm', stroke_width=stroke_w, stroke_fill=(0, 0, 0, 110))
    d.text((S // 2, cy), 'Christmas', font=f, fill=fill, anchor='mm', stroke_width=stroke_w, stroke_fill=stroke)
def snowcap(im, cy, size):
    """little snow drifts sitting on top of the script letters"""
    f = font('Pacifico-Regular.ttf', size); m = Image.new('L', im.size); ImageDraw.Draw(m).text((S // 2, cy), 'Christmas', font=f, fill=255, anchor='mm', stroke_width=14, stroke_fill=255)
    a = np.array(m) > 0; top = a & ~np.roll(a, 14, axis=0); cap = Image.fromarray((top * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
    w = Image.new('RGBA', im.size, (255, 255, 255, 255)); w.putalpha(cap); im.alpha_composite(w)
def pill(d, cx, cy, s_, fs):
    f = font('Outfit-800.ttf', fs); tw = d.textlength(s_, font=f)
    d.rounded_rectangle((cx - tw / 2 - fs * .55, cy - fs * .75, cx + tw / 2 + fs * .55, cy + fs * .75), int(fs * .75), fill=W, outline=(43, 37, 65), width=max(4, fs // 10))
    d.text((cx, cy), s_, font=f, fill=(43, 37, 65), anchor='mm')

def scene():
    im = Image.new('RGBA', (S, S), NIGHT + (255,)); flakes(im, 220, 11, (255, 255, 255, 200), 5); d = ImageDraw.Draw(im)
    d.ellipse((230, 80, 1270, 1120), fill=(255, 236, 170))
    lay = sleigh_layer(1.75, 410, 700); im.alpha_composite(lay)
    a = np.array(lay.split()[3]); hx_ = int(410 - 10 * 1.75); band = a[:, hx_ - 60:hx_ + 60]; ys = np.where(band.max(axis=1) > 0)[0]
    top = int(ys.min()) if len(ys) else 200
    pill(ImageDraw.Draw(im), hx_ + 6, top - 52, 'HARU', 46)
    return im
def v1():  # gold script, red outline, red ribbons
    im = scene(); big_script(im, 1225, 260, GOLD, RED, 12); d = ImageDraw.Draw(im)
    ribbon(d, 1035, "HARU'S", 52); ribbon(d, 1410, 'PLAYLIST 01', 50); text(d, (S // 2, 1478), 'OPEN TO CLOSE', font('Outfit-800.ttf', 30), CREAM, 'mm', sp=12); return im
def v2():  # white script, thick red outline, gold glow
    im = scene(); big_script(im, 1215, 280, W, RED, 14, glow=(255, 200, 80, 160)); d = ImageDraw.Draw(im)
    d.text((S // 2, 1030), "H A R U ' S", font=font('Outfit-800.ttf', 64), fill=GOLD, anchor='mm', stroke_width=9, stroke_fill=NIGHT)
    d.rounded_rectangle((S / 2 - 300, 1365, S / 2 + 300, 1450), 42, fill=GOLD); text(d, (S // 2, 1408), 'PLAYLIST 01', font('Outfit-800.ttf', 52), NIGHT, 'mm', sp=12)
    text(d, (S // 2, 1478), 'OPEN TO CLOSE', font('Outfit-800.ttf', 28), CREAM, 'mm', sp=12); return im
def v3():  # red script, white outline, snow on the letters
    im = scene(); big_script(im, 1220, 280, RED, W, 12); snowcap(im, 1220, 280); d = ImageDraw.Draw(im)
    d.text((S // 2, 1030), "H A R U ' S", font=font('Outfit-800.ttf', 64), fill=W, anchor='mm', stroke_width=9, stroke_fill=RED)
    text(d, (S // 2, 1408), 'PLAYLIST 01', font('Outfit-800.ttf', 64), GOLD, 'mm', sp=16)
    text(d, (S // 2, 1478), 'OPEN TO CLOSE', font('Outfit-800.ttf', 30), CREAM, 'mm', sp=12); return im

ims = [v1(), v2(), v3()]
for i, im in enumerate(ims):
    out = im.convert('RGB')
    if K > 1: out = out.resize((S * K, S * K), Image.LANCZOS)
    out.save(f'{OUTDIR}/sleigh_v{i + 1}.png')
T = 620; sheet = Image.new('RGB', (3 * T + 160, T + 110), 'white'); dd = ImageDraw.Draw(sheet)
for i, (n, im) in enumerate(zip(['1. 금색 글씨 + 빨간 리본', '2. 흰 글씨 + 빨간 테두리 + 금빛', '3. 빨간 글씨 + 눈 쌓인 글자'], ims)):
    x = 40 + i * (T + 40); dd.text((x, 30), n, font=font('NanumSquareRoundB.ttf', 30), fill=(31, 35, 64)); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, 80))
sheet.save(f'{OUTDIR}/sleigh_sheet2.png'); print('ok')
