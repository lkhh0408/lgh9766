"""Album cover drafts, round 2 (10 more styles). python3 cover_drafts2.py OUTDIR [outfit] [num] [accent]"""
import math
from PIL import Image, ImageDraw, ImageFilter
from cover_drafts import *
SKY = (143, 208, 255); SUN = (255, 214, 102); NAVY = (31, 35, 64)
def paste_c(im, art, cx, cy): im.alpha_composite(art, (int(cx - art.width / 2), int(cy - art.height / 2)))
def d1():  # sunburst retro poster
    im = Image.new('RGBA', (S, S), CREAM + (255,)); d = ImageDraw.Draw(im); cx, cy = S // 2, 820
    for k in range(24):
        a0, a1 = k * 15, k * 15 + 7.5; d.pieslice((cx - 1400, cy - 1400, cx + 1400, cy + 1400), a0, a1, fill=SUN)
    d.ellipse((cx - 380, cy - 380, cx + 380, cy + 380), fill=A)
    w = haru(3.2); im.alpha_composite(w, (cx - w.width // 2, cy + 380 - w.height + 46))
    d.rectangle((0, 1250, S, S), fill=NAVY)
    text(d, (S // 2, 1330), 'OPEN TO CLOSE', font('Outfit-800.ttf', 110), CREAM, 'mm', sp=10)
    text(d, (S // 2, 1430), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 56), SUN, 'mm', sp=18); return im
def d2():  # street sign
    im = Image.new('RGBA', (S, S), SKY + (255,)); d = ImageDraw.Draw(im)
    d.rectangle((560, 700, 610, S), fill=(150, 156, 170))
    d.rounded_rectangle((100, 200, 1070, 700), 40, fill=(34, 120, 82)); d.rounded_rectangle((125, 225, 1045, 675), 26, outline=CREAM, width=10)
    text(d, (585, 380), 'OPEN TO CLOSE', font('Outfit-800.ttf', 96), CREAM, 'mm', sp=6)
    text(d, (585, 540), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 72), CREAM, 'mm', sp=10)
    d.rectangle((0, 1300, S, S), fill=(200, 196, 210)); w = haru(3.2); im.alpha_composite(w, (1230 - w.width // 2, 1330 - w.height + 54)); return im
def d3():  # giant coffee cup
    im = Image.new('RGBA', (S, S), A + (255,)); d = ImageDraw.Draw(im)
    d.polygon([(430, 380), (1070, 380), (990, 1380), (510, 1380)], fill=(255, 255, 255))
    d.rounded_rectangle((390, 300, 1110, 400), 30, fill=(240, 236, 228)); d.rounded_rectangle((460, 230, 1040, 320), 30, fill=(255, 255, 255))
    d.polygon([(458, 640), (1042, 640), (1020, 960), (480, 960)], fill=(196, 150, 104))
    text(d, (750, 760), 'OPEN TO', font('Outfit-800.ttf', 96), CREAM, 'mm', sp=6); text(d, (750, 860), 'CLOSE', font('Outfit-800.ttf', 96), CREAM, 'mm', sp=6)
    text(d, (750, 1120), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 56), INK, 'mm', sp=12)
    for x in (660, 760, 860): d.arc((x - 40, 60, x + 40, 220), 100, 260, fill=CREAM, width=12)
    hd = haru(2.6, head=True, sticker=True); paste_c(im, hd, 1180, 1220); return im
def d4():  # window frame
    im = Image.new('RGBA', (S, S), (240, 226, 200, 255)); d = ImageDraw.Draw(im)
    d.rectangle((250, 200, 1250, 1200), fill=SKY); d.ellipse((850, 300, 1100, 550), fill=SUN)
    for x, y, r in [(420, 420, 90), (520, 400, 110), (620, 430, 80)]: d.ellipse((x - r, y - r * .6, x + r, y + r * .6), fill=(255, 255, 255))
    d.rectangle((250, 960, 1250, 1200), fill=(200, 196, 210)); w = haru(2.9); im.alpha_composite(w, (750 - w.width // 2, 1060 - w.height + 46))
    d.rectangle((250, 200, 1250, 1200), outline=(255, 255, 255), width=40);     d.rectangle((200, 1200, 1300, 1260), fill=(255, 255, 255))
    text(d, (S // 2, 1360), 'OPEN TO CLOSE', font('Outfit-800.ttf', 100), INK, 'mm', sp=12); text(d, (S // 2, 1450), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 50), A, 'mm', sp=18)
    text(d, (S // 2, 110), '', font('Outfit-800.ttf', 10), INK); return im
def d5():  # risograph two-colour halftone
    im = Image.new('RGBA', (S, S), (247, 240, 226, 255)); d = ImageDraw.Draw(im)
    for y in range(0, S, 22):
        for x in range(0, S, 22):
            r = 9 * max(0, 1 - math.hypot(x - 1000, y - 500) / 900); d.ellipse((x - r, y - r, x + r, y + r), fill=A)
    w = haru(5.0); sh = Image.new('RGBA', w.size, NAVY + (255,)); sh.putalpha(w.split()[3].point(lambda v: int(v * .9)))
    im.alpha_composite(sh, (1030 - w.width // 2 + 18, S - w.height + 90)); im.alpha_composite(w, (1030 - w.width // 2, S - w.height + 70))
    f = font('Outfit-800.ttf', 210)
    for i, l in enumerate(['OPEN', 'TO', 'CLOSE']): text(d, (96, 140 + i * 205), l, f, A); text(d, (90, 132 + i * 205), l, f, NAVY)
    text(d, (100, 800), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 64), A, sp=14); return im
def d6():  # ticket
    im = Image.new('RGBA', (S, S), NAVY + (255,)); dots(im, (44, 49, 84), 54, 4); d = ImageDraw.Draw(im)
    t = Image.new('RGBA', (1300, 640), (0, 0, 0, 0)); td = ImageDraw.Draw(t); td.rounded_rectangle((0, 0, 1300, 640), 40, fill=CREAM)
    for y in (0, 640): td.ellipse((900 - 50, y - 50, 900 + 50, y + 50), fill=(0, 0, 0, 0))
    for y in range(70, 600, 46): td.rectangle((896, y, 904, y + 24), fill=(200, 190, 170))
    td.rectangle((0, 0, 1300, 110), fill=A); text(td, (450, 56), 'OPEN TO CLOSE', font('Outfit-800.ttf', 72), CREAM, 'mm', sp=10)
    text(td, (450, 300), 'PLAY LIST', font('Outfit-800.ttf', 120), INK, 'mm'); text(td, (450, 460), NUM, font('Outfit-800.ttf', 170), A, 'mm')
    hd = haru(3.2, head=True); t.alpha_composite(hd, (1100 - hd.width // 2, 360 - hd.height // 2))
    t = t.rotate(-6, expand=True, resample=Image.BICUBIC); paste_c(im, t, S // 2, S // 2 + 20); return im
def d7():  # sticker collage on a laptop lid
    im = Image.new('RGBA', (S, S), (160, 166, 180, 255)); d = ImageDraw.Draw(im); d.rounded_rectangle((90, 90, S - 90, S - 90), 70, fill=(196, 200, 210))
    def tag(txt, cx, cy, ang, bg, fg, fs):
        f = font('Outfit-800.ttf', fs); tw = int(d.textlength(txt, font=f)) + 80; t = Image.new('RGBA', (tw, fs + 70)); td = ImageDraw.Draw(t)
        td.rounded_rectangle((0, 0, tw - 1, fs + 69), (fs + 70) // 2, fill=bg, outline=(255, 255, 255), width=10); td.text((tw // 2, (fs + 70) // 2), txt, font=f, fill=fg, anchor='mm')
        paste_c(im, t.rotate(ang, expand=True, resample=Image.BICUBIC), cx, cy)
    tag('OPEN TO CLOSE', 640, 300, 6, NAVY, CREAM, 110); tag(f'PLAY LIST {NUM}', 560, 520, -5, A, CREAM, 90)
    for cx, cy, r, c in [(1200, 260, 90, SUN), (300, 1250, 70, SKY)]: d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c, outline=(255, 255, 255), width=10)
    text(d, (1200, 262), '♪', font('NanumSquareRoundB.ttf', 120), NAVY, 'mm')
    st = haru(3.6, sticker=True); paste_c(im, st, 1110, 1090); hd = haru(2.2, head=True, sticker=True); paste_c(im, hd.rotate(12, expand=True), 380, 900); return im
def d8():  # comic 4 panels
    im = Image.new('RGBA', (S, S), (255, 255, 255, 255)); d = ImageDraw.Draw(im); g = 40; c = (S - 3 * g) // 2
    cols = [SUN, SKY, A, NAVY]
    for k in range(4):
        x, y = g + (k % 2) * (c + g), g + (k // 2) * (c + g); d.rectangle((x, y, x + c, y + c), fill=cols[k], outline=INK, width=8)
    hd = haru(4.6, head=True); im.alpha_composite(hd.crop((0, 0, hd.width, hd.height)), (g + c // 2 - hd.width // 2, g + c // 2 - hd.height // 2 + 30))
    w = haru(2.4, phase=2.2); im.alpha_composite(w, (2 * g + c + c // 2 - w.width // 2, g + c - w.height + 20))
    st = haru(2.6, flip=False); im.alpha_composite(st, (g + c // 2 - st.width // 2, 2 * g + 2 * c - st.height + 20))
    x0, y0 = 2 * g + c, 2 * g + c
    text(d, (x0 + c // 2, y0 + c // 2 - 90), 'OPEN TO', font('Outfit-800.ttf', 96), CREAM, 'mm'); text(d, (x0 + c // 2, y0 + c // 2 + 10), 'CLOSE', font('Outfit-800.ttf', 96), CREAM, 'mm')
    text(d, (x0 + c // 2, y0 + c // 2 + 130), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 50), A, 'mm', sp=10); return im
def d9():  # morning-to-night stripes
    im = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(im)
    cols = [(255, 214, 160), (255, 178, 140), (240, 130, 140), (150, 110, 170), (70, 70, 130), (31, 35, 64)]; h = S / len(cols)
    for i, c in enumerate(cols): d.rectangle((0, int(i * h), S, int((i + 1) * h)), fill=c)
    w = haru(3.6); im.alpha_composite(w, (1080 - w.width // 2, S - w.height + 40))
    f = font('Outfit-800.ttf', 150); text(d, (110, 110), 'OPEN', f, NAVY); text(d, (110, 270), 'TO', f, NAVY); text(d, (110, 1010), 'CLOSE', f, CREAM)
    text(d, (116, 1200), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 60), SUN, sp=14); return im
def d10():  # type-only, Haru as the O
    im = Image.new('RGBA', (S, S), SUN + (255,)); d = ImageDraw.Draw(im); f = font('Outfit-800.ttf', 330)
    d.ellipse((90, 120, 410, 440), fill=A); hd = haru(2.6, head=True); paste_c(im, hd, 250, 290)
    text(d, (420, 120), 'PEN', f, NAVY); text(d, (90, 470), 'TO', f, NAVY); text(d, (90, 820), 'CLOSE', f, NAVY)
    d.rounded_rectangle((90, 1240, 760, 1360), 60, fill=A); text(d, (425, 1300), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 60), CREAM, 'mm', sp=10); return im
names = ['① 레트로 선버스트', '② 거리 표지판', '③ 커다란 커피컵', '④ 창문 너머', '⑤ 2색 인쇄(리소)', '⑥ 티켓', '⑦ 스티커 콜라주', '⑧ 4컷 만화', '⑨ 아침→밤 줄무늬', '⑩ 글자 속 하루']
ims = [f() for f in (d1, d2, d3, d4, d5, d6, d7, d8, d9, d10)]
for i, im in enumerate(ims): im.convert('RGB').save(f'{OUT}/v2_cover{i + 1}.png')
T = 480; G = 36; sheet = Image.new('RGB', (5 * T + 6 * G, 2 * (T + 86) + G), 'white'); d = ImageDraw.Draw(sheet)
for i, im in enumerate(ims):
    x = G + (i % 5) * (T + G); y = G + (i // 5) * (T + 86)
    d.text((x, y), names[i], font=font('NanumSquareRoundB.ttf', 32), fill=INK); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, y + 46))
sheet.save(f'{OUT}/covers_sheet2.png'); print('ok')
