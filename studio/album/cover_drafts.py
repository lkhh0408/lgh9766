"""Album cover drafts (square). python3 cover_drafts.py OUTDIR [outfit] [num] [accent]"""
import sys, math, cairo, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch
OUT = sys.argv[1]; OUTFIT = sys.argv[2] if len(sys.argv) > 2 else 'vol01'
NUM = sys.argv[3] if len(sys.argv) > 3 else '01'; ACC = sys.argv[4] if len(sys.argv) > 4 else '#E0457B'
F = '/home/user/lgh9766/studio/assets/fonts/'
S = 1500; INK = (43, 37, 65); CREAM = (255, 246, 224)
def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
A = rgb(ACC)
def font(n, s): return ImageFont.truetype(F + n, s)
def haru(scale, head=False, flip=True, sticker=False, walk=1.0, phase=0.9):
    w, h = (int(130 * scale), int(130 * scale)) if head else (int(240 * scale), int(290 * scale))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h); c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    if head:
        c.translate(w / 2, h / 2 + 4 * scale); c.scale(-scale if flip else scale, scale)
        ch.draw_head(c, -6, 0, 0.5, ch.OUTFITS[OUTFIT])
    else:
        c.translate(w / 2, h - 16 * scale); c.scale(-scale if flip else scale, scale)
        ch.draw(c, -6, 0, t=0.5, phase=phase, walk=walk, outfit=OUTFIT)
    b = np.ndarray((h, w, 4), np.uint8, s.get_data()); a = b[..., 3:4].astype(np.float32) / 255
    col = np.where(a > 0, b[..., [2, 1, 0]] / np.maximum(a, 1e-6), 0).clip(0, 255).astype(np.uint8)
    art = Image.fromarray(np.dstack([col, b[..., 3]]), 'RGBA')
    if not sticker: return art
    pad = int(40 * scale / 4); big = Image.new('RGBA', (w + 2 * pad, h + 2 * pad)); big.alpha_composite(art, (pad, pad)); art = big
    al = art.split()[3]; k = max(3, int(scale * 4) | 1)
    border = al.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.GaussianBlur(1.5))
    out = Image.new('RGBA', art.size); sh = Image.new('RGBA', art.size, (0, 0, 0, 255)); sh.putalpha(border.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * .4)))
    out.alpha_composite(sh, (12, 18)); wb = Image.new('RGBA', art.size, (255, 255, 255, 255)); wb.putalpha(border); out.alpha_composite(wb); out.alpha_composite(art)
    return out
def text(d, xy, s, f, fill, anchor='la', sp=0):
    if not sp: d.text(xy, s, font=f, fill=fill, anchor=anchor); return
    x, y = xy; tw = sum(d.textlength(ch_, font=f) + sp for ch_ in s) - sp
    if anchor[0] == 'm': x -= tw / 2
    for c_ in s: d.text((x, y), c_, font=f, fill=fill, anchor='l' + anchor[1]); x += d.textlength(c_, font=f) + sp
def dots(im, col, step=46, r=4):
    d = ImageDraw.Draw(im)
    for y in range(0, S, step):
        for x in range((y // step % 2) * step // 2, S, step): d.ellipse((x - r, y - r, x + r, y + r), fill=col)
def cover1():  # thumbnail style: accent bg, big sticker, title
    im = Image.new('RGBA', (S, S), A + (255,)); dots(im, tuple(min(255, v + 18) for v in A))
    st = haru(5.0, sticker=True); im.alpha_composite(st, (1130 - st.width // 2, S - st.height + 200))
    d = ImageDraw.Draw(im); text(d, (100, 120), 'OPEN TO CLOSE', font('Outfit-800.ttf', 64), CREAM, sp=10)
    text(d, (96, 200), 'PLAY', font('Outfit-800.ttf', 250), CREAM); text(d, (96, 430), 'LIST', font('Outfit-800.ttf', 250), CREAM)
    text(d, (96, 660), NUM, font('Outfit-800.ttf', 250), INK); return im
def cover2():  # minimal cream, big head
    im = Image.new('RGBA', (S, S), CREAM + (255,)); d = ImageDraw.Draw(im)
    d.ellipse((330, 250, 1170, 1090), fill=A + (255,))
    hd = haru(7.0, head=True); im.alpha_composite(hd, ((S - hd.width) // 2, 670 - hd.height // 2))
    text(d, (S // 2, 1220), 'OPEN TO CLOSE', font('Outfit-800.ttf', 96), INK, 'mm', sp=14)
    text(d, (S // 2, 1330), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 60), A, 'mm', sp=18); return im
def cover3():  # vinyl
    im = Image.new('RGBA', (S, S), (31, 35, 64, 255)); d = ImageDraw.Draw(im)
    cx, cy, R = 900, 860, 560
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(18, 18, 26))
    for r in range(R - 30, 260, -22): d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(40, 40, 52), width=3)
    d.ellipse((cx - 250, cy - 250, cx + 250, cy + 250), fill=A)
    hd = haru(4.2, head=True); im.alpha_composite(hd, (cx - hd.width // 2, cy - hd.height // 2))
    d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(31, 35, 64))
    text(d, (100, 110), 'OPEN TO CLOSE', font('Outfit-800.ttf', 110), CREAM)
    text(d, (104, 240), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 64), A, sp=12); return im
def cover4():  # cassette
    im = Image.new('RGBA', (S, S), (247, 205, 90, 255)); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 110, 430, 1110, 1080
    d.rounded_rectangle((x0 + 18, y0 + 24, x1 + 18, y1 + 24), 60, fill=(0, 0, 0, 60))
    d.rounded_rectangle((x0, y0, x1, y1), 60, fill=INK); d.rounded_rectangle((x0 + 70, y0 + 70, x1 - 70, y0 + 470), 30, fill=CREAM)
    d.rectangle((x0 + 70, y0 + 70, x1 - 70, y0 + 160), fill=A)
    text(d, ((x0 + x1) // 2, y0 + 118), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 70), CREAM, 'mm', sp=10)
    for ex in (x0 + 300, x1 - 300):
        d.ellipse((ex - 85, y0 + 230, ex + 85, y0 + 400), fill=INK)
        for k in range(6):
            a = k * math.pi / 3; d.line((ex, y0 + 315, ex + 55 * math.cos(a), y0 + 315 + 55 * math.sin(a)), fill=CREAM, width=12)
        d.ellipse((ex - 22, y0 + 293, ex + 22, y0 + 337), fill=CREAM)
    d.rounded_rectangle((x0 + 220, y1 - 140, x1 - 220, y1 - 40), 20, fill=(70, 62, 98))
    text(d, (S // 2, 240), 'OPEN TO CLOSE', font('Outfit-800.ttf', 120), INK, 'mm', sp=8)
    st = haru(3.6, sticker=True); im.alpha_composite(st, (1270 - st.width // 2, S - st.height + 40)); return im
def cover5():  # sun circle walk
    im = Image.new('RGBA', (S, S), (143, 208, 255, 255)); d = ImageDraw.Draw(im)
    d.ellipse((250, 180, 1250, 1180), fill=(255, 214, 102)); d.rectangle((0, 1060, S, S), fill=(62, 74, 107))
    for x in range(0, S, 190): d.rectangle((x + 40, 1180, x + 130, 1196), fill=CREAM)
    w = haru(3.6); im.alpha_composite(w, (S // 2 - w.width // 2, 1080 - w.height + 58))
    text(d, (S // 2, 1300), 'OPEN TO CLOSE', font('Outfit-800.ttf', 100), CREAM, 'mm', sp=12)
    text(d, (S // 2, 1405), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 54), (255, 214, 102), 'mm', sp=18); return im
def cover6():  # headphone pattern + badge
    im = Image.new('RGBA', (S, S), CREAM + (255,)); d = ImageDraw.Draw(im)
    for j, y in enumerate(range(-40, S + 100, 150)):
        for x in range(-40 + (j % 2) * 75, S + 100, 150):
            d.arc((x - 40, y - 40, x + 40, y + 40), 200, 340, fill=A, width=12)
            d.rounded_rectangle((x - 50, y - 6, x - 26, y + 34), 10, fill=A); d.rounded_rectangle((x + 26, y - 6, x + 50, y + 34), 10, fill=A)
    d.ellipse((340, 300, 1160, 1120), fill=INK); d.ellipse((370, 330, 1130, 1090), fill=A)
    hd = haru(6.0, head=True); im.alpha_composite(hd, (S // 2 - hd.width // 2, 720 - hd.height // 2))
    d.rounded_rectangle((300, 1190, 1200, 1400), 40, fill=INK)
    text(d, (S // 2, 1255), 'OPEN TO CLOSE', font('Outfit-800.ttf', 92), CREAM, 'mm', sp=10)
    text(d, (S // 2, 1345), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 52), A, 'mm', sp=16); return im
def cover7():  # polaroid
    im = Image.new('RGBA', (S, S), (238, 226, 205, 255)); dots(im, (226, 212, 188), 60, 5)
    p = Image.new('RGBA', (1000, 1180), (255, 255, 255, 255)); pd = ImageDraw.Draw(p)
    pd.rectangle((60, 60, 940, 940), fill=(143, 208, 255)); pd.rectangle((60, 760, 940, 940), fill=(200, 196, 210))
    pd.ellipse((620, 120, 820, 320), fill=(255, 214, 102))
    w = haru(3.0); p.alpha_composite(w, (500 - w.width // 2, 860 - w.height + 40))
    text(pd, (500, 1060), f'play list {NUM}', font('Pacifico-Regular.ttf', 92), INK, 'mm')
    sh = Image.new('RGBA', p.size, (0, 0, 0, 90)).filter(ImageFilter.GaussianBlur(20))
    pr = p.rotate(-5, expand=True, resample=Image.BICUBIC); ps = Image.new('RGBA', pr.size); ps.putalpha(pr.split()[3].point(lambda v: v // 3).filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(ps, (270, 230)); im.alpha_composite(pr, (240, 190))
    d = ImageDraw.Draw(im); text(d, (S // 2, 120), 'OPEN TO CLOSE', font('Outfit-800.ttf', 96), INK, 'mm', sp=14); return im
def cover8():  # big number
    im = Image.new('RGBA', (S, S), INK + (255,)); d = ImageDraw.Draw(im)
    text(d, (560, 800), NUM, font('Outfit-800.ttf', 960), A, 'mm')
    st = haru(4.0, sticker=True); im.alpha_composite(st, (1250 - st.width // 2, S - st.height + 110))
    text(d, (100, 110), 'OPEN TO CLOSE', font('Outfit-800.ttf', 84), CREAM, sp=12)
    text(d, (104, 215), 'PLAY LIST', font('Outfit-800.ttf', 56), A, sp=18); return im
names = ['① 썸네일 스타일', '② 미니멀 (얼굴 크게)', '③ LP 레코드', '④ 카세트 테이프', '⑤ 해 아래 걷는 하루', '⑥ 헤드폰 패턴 + 배지', '⑦ 폴라로이드', '⑧ 큰 숫자']
ims = [f() for f in (cover1, cover2, cover3, cover4, cover5, cover6, cover7, cover8)]
for i, im in enumerate(ims): im.convert('RGB').save(f'{OUT}/cover{i + 1}.png')
T = 520; G = 40; sheet = Image.new('RGB', (4 * T + 5 * G, 2 * (T + 90) + G), 'white'); d = ImageDraw.Draw(sheet)
for i, im in enumerate(ims):
    x = G + (i % 4) * (T + G); y = G + (i // 4) * (T + 90)
    d.text((x, y), names[i], font=font('NanumSquareRoundB.ttf', 34), fill=INK); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, y + 50))
sheet.save(f'{OUT}/covers_sheet.png'); print('ok')
