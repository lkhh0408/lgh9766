"""Haru's Christmas Playlist 01, round 3: 10 more carol-album covers. python3 cover_drafts_pl04c.py OUTDIR"""
import sys, math, random
from PIL import Image, ImageDraw
OUTDIR = sys.argv[1]
sys.argv = [sys.argv[0], OUTDIR]
import cover_drafts_pl04b as B          # reuses the round-2 helpers (it also re-renders round 2, which is fine)
from cover_drafts_pl04b import haru, text, font, INK, CREAM, S, RED, DRED, GREEN, DGREEN, GOLD, NIGHT, W, flakes, title, brand, holly, pill

def lights(d, y, sag=40, n=14, seed=1, x0=0, x1=S):
    r = random.Random(seed); pts = [(x0 + (x1 - x0) * k / 60, y + sag * math.sin(math.pi * ((k / 60 * n) % 1))) for k in range(61)]
    d.line(pts, fill=(40, 60, 40), width=6)
    for k in range(n * 2):
        u = (k + .5) / (n * 2); x = x0 + (x1 - x0) * u; yy = y + sag * math.sin(math.pi * ((u * n) % 1)) + 26
        c = r.choice([RED, GOLD, (90, 170, 255), (80, 200, 120), (255, 140, 200)])
        d.rectangle((x - 9, yy - 30, x + 9, yy - 18), fill=(70, 70, 70)); d.ellipse((x - 16, yy - 22, x + 16, yy + 22), fill=c)

def m1():  # vintage greeting card
    im = Image.new('RGBA', (S, S), (110, 20, 30, 255)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((120, 120, S - 120, S - 120), 30, fill=(250, 242, 226)); d.rounded_rectangle((160, 160, S - 160, S - 160), 20, outline=GOLD, width=8)
    title(d, 420, DRED, RED, GREEN, 260, False); brand(d, 1310, DRED)
    for x in (300, 1200): holly(d, x, 260, .9, 90)
    for gx, gc in ((520, GREEN), (980, RED)):
        d.rectangle((gx - 90, 1000, gx + 90, 1170), fill=gc); d.rectangle((gx - 12, 1000, gx + 12, 1170), fill=GOLD); d.rectangle((gx - 90, 1070, gx + 90, 1094), fill=GOLD)
    w = haru(1.9, walk=0.0); im.alpha_composite(w, (750 - w.width // 2, 1230 - w.height + 30)); d = ImageDraw.Draw(im)
    pill(d, 742, 1230 - int(w.height * .83) - 34, 'HARU', 34); return im
def m2():  # moon + flying sleigh silhouette
    im = Image.new('RGBA', (S, S), NIGHT + (255,)); flakes(im, 200, 11, (255, 255, 255, 200), 5); d = ImageDraw.Draw(im)
    d.ellipse((380, 160, 1120, 900), fill=(255, 236, 170)); sil = (24, 32, 64)
    for k, x in enumerate((560, 700, 840)):
        y = 520 - k * 30; d.ellipse((x - 60, y - 22, x + 50, y + 22), fill=sil); d.polygon([(x + 40, y - 10), (x + 80, y - 50), (x + 95, y - 40), (x + 60, y)], fill=sil)
        for lx in (-45, -20, 15, 35): d.line((x + lx, y + 15, x + lx + (8 if k % 2 else -8), y + 60), fill=sil, width=8)
        d.line((x + 78, y - 48, x + 70, y - 90), fill=sil, width=6); d.line((x + 88, y - 44, x + 100, y - 84), fill=sil, width=6)
    d.polygon([(330, 600), (500, 600), (520, 560), (480, 660), (340, 660)], fill=sil); d.line((340, 680, 500, 680), fill=sil, width=10)
    d.line((500, 600, 560, 520), fill=sil, width=4)
    st = haru(2.2, head=True); im.alpha_composite(st, (400 - st.width // 2, 560 - st.height // 2 - 20)); d = ImageDraw.Draw(im)
    title(d, 1200, CREAM, W, GOLD, 280); brand(d, 1450, CREAM); return im
def m3():  # snowy village at night
    im = Image.new('RGBA', (S, S), (30, 44, 90, 255)); flakes(im, 200, 12, (255, 255, 255, 210), 6); d = ImageDraw.Draw(im)
    title(d, 330, CREAM, W, GOLD, 280)
    r = random.Random(3)
    for x in range(-40, S, 230):
        h = r.randint(260, 380); c = r.choice([(180, 70, 70), (90, 120, 160), (220, 190, 140), (70, 110, 90)])
        d.rectangle((x, 1180 - h, x + 200, 1180), fill=c); d.polygon([(x - 20, 1180 - h), (x + 100, 1180 - h - 120), (x + 220, 1180 - h)], fill=W)
        for wy in range(1180 - h + 50, 1150, 110): d.rectangle((x + 40, wy, x + 90, wy + 60), fill=GOLD); d.rectangle((x + 120, wy, x + 170, wy + 60), fill=GOLD)
    d.rectangle((0, 1180, S, S), fill=W)
    w = haru(2.2); im.alpha_composite(w, (750 - w.width // 2, 1260 - w.height + 46)); d = ImageDraw.Draw(im)
    pill(d, 742, 1260 - int(w.height * .83) - 40, 'HARU', 40); brand(d, 1430, NIGHT); return im
def m4():  # three hanging ornaments
    im = Image.new('RGBA', (S, S), (250, 242, 226, 255)); d = ImageDraw.Draw(im)
    for x, top, R, c in ((380, 0, 170, GREEN), (750, 0, 250, RED), (1120, 0, 170, GOLD)):
        cy = 330 + R if x == 750 else 300 + R
        d.line((x, top, x, cy - R), fill=(150, 120, 60), width=6); d.rounded_rectangle((x - 40, cy - R - 40, x + 40, cy - R + 10), 10, fill=GOLD)
        d.ellipse((x - R, cy - R, x + R, cy + R), fill=c); d.arc((x - R, cy - 60, x + R, cy + 60), 10, 170, fill=W, width=10)
    hd = haru(3.6, head=True); im.alpha_composite(hd, (750 - hd.width // 2, 580 - hd.height // 2 + 10)); d = ImageDraw.Draw(im)
    pill(d, 742, 300, 'HARU', 40)
    title(d, 1170, DRED, RED, GREEN, 270, False); brand(d, 1440, DRED); return im
def m5():  # gingerbread / icing
    im = Image.new('RGBA', (S, S), (166, 104, 62, 255)); d = ImageDraw.Draw(im)
    for y in (90, 1410):
        for x in range(0, S + 60, 60): d.ellipse((x - 30, y - 30, x + 30, y + 30), fill=W)
    for x, y, c in ((200, 260, RED), (1300, 260, GREEN), (200, 1240, GREEN), (1300, 1240, RED)): d.ellipse((x - 40, y - 40, x + 40, y + 40), fill=c, outline=W, width=8)
    title(d, 400, CREAM, W, (255, 220, 120), 270, False)
    gx, gy = 750, 960
    d.ellipse((gx - 150, gy - 330, gx + 150, gy - 60), fill=(190, 120, 70), outline=W, width=8)
    d.rounded_rectangle((gx - 190, gy - 90, gx + 190, gy + 230), 90, fill=(190, 120, 70), outline=W, width=8)
    for k in range(3): d.ellipse((gx - 18, gy - 30 + k * 80, gx + 18, gy + 6 + k * 80), fill=RED)
    hd = haru(2.2, head=True); im.alpha_composite(hd, (gx - hd.width // 2, gy - 200 - hd.height // 2)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((gx - 140, gy + 250, gx + 140, gy + 330), 20, fill=W); text(d, (gx, gy + 290), 'HARU', font('Outfit-800.ttf', 50), (166, 104, 62), 'mm', sp=8)
    brand(d, 1330, CREAM); return im
def m6():  # string lights border, dark bg
    im = Image.new('RGBA', (S, S), (22, 24, 40, 255)); d = ImageDraw.Draw(im); lights(d, 40, 60, 7, 2); lights(d, 1350, 60, 7, 5)
    title(d, 400, CREAM, W, GOLD, 300)
    st = haru(2.0, sticker=True, walk=0.0); im.alpha_composite(st, (750 - st.width // 2, 1330 - st.height + 30)); d = ImageDraw.Draw(im)
    text(d, (90, 1450), 'OPEN TO CLOSE', font('Outfit-800.ttf', 44), CREAM, 'lm', sp=12); return im
def m7():  # tartan plaid + badge
    im = Image.new('RGBA', (S, S), RED + (255,)); d = ImageDraw.Draw(im)
    for k in range(0, S, 200):
        d.rectangle((k + 60, 0, k + 140, S), fill=(150, 30, 40)); d.rectangle((0, k + 60, S, k + 140), fill=(150, 30, 40))
        d.rectangle((k + 95, 0, k + 105, S), fill=DGREEN); d.rectangle((0, k + 95, S, k + 105), fill=DGREEN)
    d.ellipse((270, 170, 1230, 1130), fill=(250, 242, 226), outline=GOLD, width=14)
    title(d, 480, DRED, RED, GREEN, 200, False)
    hd = haru(3.0, head=True); im.alpha_composite(hd, (750 - hd.width // 2, 880 - hd.height // 2)); d = ImageDraw.Draw(im)
    pill(d, 742, 720, 'HARU', 36)
    d.rounded_rectangle((420, 1250, 1080, 1360), 24, fill=(250, 242, 226)); text(d, (750, 1305), 'OPEN TO CLOSE', font('Outfit-800.ttf', 52), DRED, 'mm', sp=10); return im
def m8():  # hot cocoa mug
    im = Image.new('RGBA', (S, S), (245, 225, 205, 255)); flakes(im, 70, 13, (255, 255, 255, 255), 9); d = ImageDraw.Draw(im)
    title(d, 330, DRED, RED, GREEN, 260, False)
    d.rounded_rectangle((420, 760, 1020, 1320), 60, fill=RED); d.ellipse((960, 880, 1180, 1140), outline=RED, width=50)
    d.ellipse((420, 720, 1020, 820), fill=(120, 70, 40))
    for x, y in ((560, 750), (650, 735), (760, 755), (860, 738)): d.rounded_rectangle((x - 40, y - 30, x + 40, y + 30), 14, fill=W)
    for x in (600, 720, 840): d.arc((x - 50, 520, x + 50, 700), 100, 260, fill=W, width=14)
    for k in range(-1, 2): d.regular_polygon((720 + k * 140, 1040, 40), 6, rotation=30, fill=W)
    d.rounded_rectangle((560, 1150, 880, 1240), 20, fill=W); text(d, (720, 1195), 'HARU', font('Outfit-800.ttf', 54), RED, 'mm', sp=8)
    hd = haru(2.0, head=True, sticker=True); im.alpha_composite(hd, (1130, 1150)); d = ImageDraw.Draw(im)
    brand(d, 1440, DRED); return im
def m9():  # big snowflakes on blue
    im = Image.new('RGBA', (S, S), (60, 110, 190, 255)); d = ImageDraw.Draw(im); r = random.Random(9)
    for _ in range(18):
        x, y, R = r.uniform(0, S), r.uniform(0, S), r.uniform(50, 130)
        for a in range(0, 180, 30):
            t = math.radians(a); d.line((x - R * math.cos(t), y - R * math.sin(t), x + R * math.cos(t), y + R * math.sin(t)), fill=(140, 180, 235), width=8)
    title(d, 400, W, W, GOLD, 300)
    st = haru(2.0, sticker=True, walk=0.0); im.alpha_composite(st, (750 - st.width // 2, 1330 - st.height + 30)); d = ImageDraw.Draw(im)
    brand(d, 1440, W); return im
def m10():  # poinsettia corners on cream
    im = Image.new('RGBA', (S, S), (250, 244, 232, 255)); d = ImageDraw.Draw(im)
    def poin(cx, cy, s):
        for k in range(8):
            a = math.radians(k * 45 + 22); x, y = cx + 110 * s * math.cos(a), cy + 110 * s * math.sin(a)
            d.polygon([(cx, cy), (x + 40 * s * math.sin(a), y - 40 * s * math.cos(a)), (cx + 170 * s * math.cos(a), cy + 170 * s * math.sin(a)), (x - 40 * s * math.sin(a), y + 40 * s * math.cos(a))], fill=RED)
        for k in range(6): a = k * 60; d.ellipse((cx + 22 * math.cos(math.radians(a)) - 10, cy + 22 * math.sin(math.radians(a)) - 10, cx + 22 * math.cos(math.radians(a)) + 10, cy + 22 * math.sin(math.radians(a)) + 10), fill=GOLD)
    for (x, y) in ((120, 120), (1380, 120), (120, 1380), (1380, 1380)): poin(x, y, 1.4)
    title(d, 420, GREEN, RED, GREEN, 280, False)
    w = haru(2.0, walk=0.0); im.alpha_composite(w, (750 - w.width // 2, 1300 - w.height + 30)); d = ImageDraw.Draw(im)
    pill(d, 742, 1300 - int(w.height * .83) - 38, 'HARU', 38); brand(d, 1420, GREEN); return im

names = ['17 빈티지 크리스마스 카드', '18 보름달 + 썰매 실루엣', '19 눈 내린 마을 밤', '20 장식볼 세 개', '21 진저브레드 쿠키', '22 전구 줄 테두리', '23 타탄 체크 + 배지', '24 핫초코 머그', '25 큰 눈송이 패턴', '26 포인세티아 꽃']
ims = [f() for f in (m1, m2, m3, m4, m5, m6, m7, m8, m9, m10)]
for i, im in enumerate(ims): im.convert('RGB').save(f'{OUTDIR}/pl04c_cover{i + 17}.png')
T = 480; G = 36; sheet = Image.new('RGB', (5 * T + 6 * G, 2 * (T + 86) + G), 'white'); dd = ImageDraw.Draw(sheet)
for i, im in enumerate(ims):
    x = G + (i % 5) * (T + G); y = G + (i // 5) * (T + 86)
    dd.text((x, y), names[i], font=font('NanumSquareRoundB.ttf', 30), fill=INK); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, y + 46))
sheet.save(f'{OUTDIR}/pl04c_covers_sheet.png'); print('ok3')
