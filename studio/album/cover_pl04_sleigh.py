"""Merry Christmas from Haru (PLAY LIST 04) cover, #18 reworked (colour, big sleigh, HARU tag, three title styles): the video's reindeer sky sleigh, big across the moon.
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
    d.ellipse((300, 100, 1200, 1000), fill=(255, 236, 170))
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

def t1():  # modern: huge bold CHRISTMAS, letter-spaced
    im = scene(); d = ImageDraw.Draw(im)
    text(d, (S // 2, 1150), "HARU'S", font('Outfit-800.ttf', 62), GOLD, 'mm', sp=22)
    f = font('Outfit-800.ttf', 190); d.text((S // 2 + 6, 1290 + 8), 'CHRISTMAS', font=f, fill=(0, 0, 0, 120), anchor='mm')
    d.text((S // 2, 1290), 'CHRISTMAS', font=f, fill=W, anchor='mm')
    text(d, (S // 2, 1420), 'PLAYLIST 01  ·  OPEN TO CLOSE', font('Outfit-800.ttf', 40), CREAM, 'mm', sp=10); return im
def t2():  # snowy ground band, red bold title on white
    im = scene(); d = ImageDraw.Draw(im)
    d.rectangle((0, 1180, S, S), fill=W)
    for x in range(-60, S + 60, 120): d.ellipse((x - 90, 1120, x + 90, 1250), fill=W)
    text(d, (S // 2, 1215), "HARU'S", font('Outfit-800.ttf', 52), NIGHT, 'mm', sp=20)
    text(d, (S // 2, 1325), 'CHRISTMAS', font('Outfit-800.ttf', 170), RED, 'mm', sp=6)
    text(d, (S // 2, 1440), 'PLAYLIST 01  ·  OPEN TO CLOSE', font('Outfit-800.ttf', 38), NIGHT, 'mm', sp=10); return im
def t3():  # hanging shop sign
    im = scene(); d = ImageDraw.Draw(im)
    for x in (430, 1070): d.line((x, 1060, x, 1130), fill=GOLD, width=8)
    d.rounded_rectangle((210, 1120, 1290, 1440), 50, fill=RED, outline=GOLD, width=12)
    text(d, (S // 2, 1182), "HARU'S", font('Outfit-800.ttf', 42), GOLD, 'mm', sp=18)
    d.text((S // 2, 1268), 'Christmas', font=font('Pacifico-Regular.ttf', 170), fill=W, anchor='mm')
    text(d, (S // 2, 1385), 'PLAYLIST 01', font('Outfit-800.ttf', 46), GOLD, 'mm', sp=18)
    text(d, (S // 2, 1478), 'OPEN TO CLOSE', font('Outfit-800.ttf', 30), CREAM, 'mm', sp=12); return im
def t4():  # white label card at the bottom
    im = scene(); d = ImageDraw.Draw(im)
    d.rounded_rectangle((190, 1110, 1310, 1460), 40, fill=W)
    text(d, (S // 2, 1160), "HARU'S", font('Outfit-800.ttf', 46), NIGHT, 'mm', sp=18)
    d.text((S // 2, 1262), 'Christmas', font=font('Pacifico-Regular.ttf', 180), fill=RED, anchor='mm')
    text(d, (S // 2, 1385), 'PLAYLIST 01', font('Outfit-800.ttf', 46), (46, 125, 79), 'mm', sp=18)
    text(d, (S // 2, 1430), 'OPEN TO CLOSE', font('Outfit-800.ttf', 26), NIGHT, 'mm', sp=12); return im
def t5():  # two-line bold stack, cream, red pill
    im = scene(); d = ImageDraw.Draw(im)
    text(d, (S // 2, 1160), "HARU'S", font('Outfit-800.ttf', 120), CREAM, 'mm', sp=10)
    text(d, (S // 2, 1290), 'CHRISTMAS', font('Outfit-800.ttf', 150), CREAM, 'mm', sp=10)
    d.rounded_rectangle((S / 2 - 260, 1370, S / 2 + 260, 1450), 40, fill=RED); text(d, (S // 2, 1410), 'PLAYLIST 01', font('Outfit-800.ttf', 46), W, 'mm', sp=14)
    text(d, (S // 2, 1478), 'OPEN TO CLOSE', font('Outfit-800.ttf', 24), CREAM, 'mm', sp=12); return im
def t6():  # elegant: cream script, no outline, gold underline
    im = scene(); d = ImageDraw.Draw(im)
    text(d, (S // 2, 1135), "HARU'S", font('Outfit-800.ttf', 50), GOLD, 'mm', sp=24)
    d.text((S // 2, 1255), 'Christmas', font=font('Pacifico-Regular.ttf', 220), fill=CREAM, anchor='mm')
    d.line((S / 2 - 300, 1372, S / 2 + 300, 1372), fill=GOLD, width=5); d.regular_polygon((S / 2, 1372, 16), 4, fill=GOLD)
    text(d, (S // 2, 1420), 'PLAYLIST 01  ·  OPEN TO CLOSE', font('Outfit-800.ttf', 38), GOLD, 'mm', sp=12); return im

ims = [t1(), t2(), t3(), t4(), t5(), t6()]
for i, im in enumerate(ims):
    out = im.convert('RGB')
    if K > 1: out = out.resize((S * K, S * K), Image.LANCZOS)
    out.save(f'{OUTDIR}/sleigh_t{i + 1}.png')
T = 560; sheet = Image.new('RGB', (3 * T + 160, 2 * (T + 80) + 40), 'white'); dd = ImageDraw.Draw(sheet)
labels = ['A. 굵은 대문자 (모던)', 'B. 눈 쌓인 땅 + 빨간 글씨', 'C. 매달린 간판', 'D. 흰 라벨 카드', 'E. 두 줄 굵은 글씨', 'F. 깔끔한 필기체 + 금색 선']
for i, (n, im) in enumerate(zip(labels, ims)):
    x = 40 + (i % 3) * (T + 40); y = 30 + (i // 3) * (T + 80)
    dd.text((x, y), n, font=font('NanumSquareRoundB.ttf', 30), fill=(31, 35, 64)); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, y + 46))
sheet.save(f'{OUTDIR}/sleigh_sheet3.png'); print('ok')

def final18b():  # big sleigh + HARU tag, title exactly like the first 18-B
    im = scene(); d = ImageDraw.Draw(im)
    f = font('Pacifico-Regular.ttf', 250); fm = font('Pacifico-Regular.ttf', 120)
    for (txt, ff, x, y) in (('Merry', fm, 600, 1045), ('Christmas', f, S // 2, 1262)):
        d.text((x + 8, y + 12), txt, font=ff, fill=(0, 0, 0, 90), anchor='mm'); d.text((x, y), txt, font=ff, fill=W, anchor='mm')
    text(d, (S // 2, 1415), 'FROM HARU', font('Outfit-800.ttf', 50), GOLD, 'mm', sp=15)
    text(d, (S // 2, 1468), 'OPEN TO CLOSE', font('Outfit-800.ttf', 36), CREAM, 'mm', sp=14)
    return im
_f = final18b().convert('RGB'); _f.save(f'{OUTDIR}/sleigh_final_preview.png')
if K > 1: _f.resize((S * K, S * K), Image.LANCZOS).save(f'{OUTDIR}/sleigh_final_{S * K}.png')
print('final ok')

# ---- lettering variants for "Merry Christmas from Haru" (same scene) ----
def _s(d, xy, txt, size, fill=W, anchor='mm'):
    f = font('Pacifico-Regular.ttf', size); d.text((xy[0] + 8, xy[1] + 12), txt, font=f, fill=(0, 0, 0, 90), anchor=anchor); d.text(xy, txt, font=f, fill=fill, anchor=anchor)
def _oc(d, y=1468, size=36): text(d, (S // 2, y), 'OPEN TO CLOSE', font('Outfit-800.ttf', size), CREAM, 'mm', sp=14)
def L1(d):  # current
    _s(d, (600, 1045), 'Merry', 120); _s(d, (S // 2, 1262), 'Christmas', 250); text(d, (S // 2, 1415), 'FROM HARU', font('Outfit-800.ttf', 50), GOLD, 'mm', sp=15); _oc(d)
def L2(d):  # one line + gold script signature
    _s(d, (S // 2, 1150), 'Merry Christmas', 170); _s(d, (S // 2 + 150, 1330), 'from Haru', 120, GOLD); _oc(d, 1465)
def L3(d):  # stacked, same size
    _s(d, (S // 2, 1080), 'Merry', 175); _s(d, (S // 2, 1255), 'Christmas', 200); text(d, (S // 2, 1405), 'FROM HARU', font('Outfit-800.ttf', 50), GOLD, 'mm', sp=15); _oc(d)
def L4(d):  # big Christmas, gold Merry + gold signature
    _s(d, (560, 1060), 'Merry', 120, GOLD); _s(d, (S // 2, 1250), 'Christmas', 250); _s(d, (1060, 1395), 'from Haru', 90, GOLD); _oc(d, 1470, 32)
def L5(d):  # one line + red pill
    _s(d, (S // 2, 1160), 'Merry Christmas', 175)
    d.rounded_rectangle((S / 2 - 230, 1300, S / 2 + 230, 1390), 45, fill=(217, 64, 64)); text(d, (S // 2, 1345), 'FROM HARU', font('Outfit-800.ttf', 50), W, 'mm', sp=15); _oc(d, 1455)
def L6(d):  # all script, centred, letter-like
    _s(d, (S // 2, 1090), 'Merry Christmas', 160); _s(d, (S // 2, 1270), 'from Haru', 150, GOLD); _oc(d, 1450, 40)
variants = [('1. 지금 시안', L1), ('2. 한 줄 + 금색 서명', L2), ('3. 두 줄 같은 크기', L3), ('4. 금색 Merry + 금색 서명', L4), ('5. 한 줄 + 빨간 바', L5), ('6. 전부 필기체 (편지처럼)', L6)]
ims = []
for n, fn in variants:
    im = scene(); fn(ImageDraw.Draw(im)); ims.append(im); im.convert('RGB').save(f'{OUTDIR}/merry_{n[0]}.png')
T = 560; sheet = Image.new('RGB', (3 * T + 160, 2 * (T + 80) + 40), 'white'); dd = ImageDraw.Draw(sheet)
for i, ((n, _), im) in enumerate(zip(variants, ims)):
    x = 40 + (i % 3) * (T + 40); y = 30 + (i // 3) * (T + 80)
    dd.text((x, y), n, font=font('NanumSquareRoundB.ttf', 30), fill=(31, 35, 64)); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, y + 46))
sheet.save(f'{OUTDIR}/merry_sheet.png'); print('merry ok')
