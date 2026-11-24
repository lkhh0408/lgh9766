"""Haru's Christmas Playlist 01, round 2: covers that read as a carol album at a glance
(big script "Christmas" from the album title, wreath, holly, candy cane, stockings, snowman...).
python3 cover_drafts_pl04b.py OUTDIR"""
import sys, math, json, random
from PIL import Image, ImageDraw, ImageFilter
OUTDIR = sys.argv[1]
sys.argv = [sys.argv[0], OUTDIR, 'xmas_santa', '01', '#D94040']
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch
SB = json.load(open('/home/user/lgh9766/playlists/vol04/storyboard.json'))
ch.OUTFITS['xmas_santa'] = dict(SB['segments'][5][2])
from cover_drafts import haru, text, font, INK, CREAM, S
RED = (217, 64, 64); DRED = (160, 36, 44); GREEN = (46, 125, 79); DGREEN = (28, 88, 56); GOLD = (242, 194, 48); NIGHT = (24, 32, 64); W = (255, 255, 255)

def flakes(im, n, seed, col=(255, 255, 255, 220), rmax=7, box=(0, 0, S, S)):
    r = random.Random(seed); d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y, s = r.uniform(box[0], box[2]), r.uniform(box[1], box[3]), r.uniform(2, rmax); d.ellipse((x - s, y - s, x + s, y + s), fill=col)
def title(d, cy, c_small=CREAM, c_big=W, c_num=GOLD, big=300, shadow=True):
    """album title as a carol lockup: HARU'S / Christmas (script) / PLAYLIST 01"""
    text(d, (S // 2, cy - big * .62), "HARU'S", font('Outfit-800.ttf', int(big * .2)), c_small, 'mm', sp=int(big * .06))
    f = font('Pacifico-Regular.ttf', big)
    if shadow: d.text((S // 2 + 8, cy + 12), 'Christmas', font=f, fill=(0, 0, 0, 90), anchor='mm')
    d.text((S // 2, cy), 'Christmas', font=f, fill=c_big, anchor='mm')
    text(d, (S // 2, cy + big * .66), 'PLAYLIST 01', font('Outfit-800.ttf', int(big * .2)), c_num, 'mm', sp=int(big * .06))
def brand(d, y, col=CREAM): text(d, (S // 2, y), 'OPEN TO CLOSE', font('Outfit-800.ttf', 54), col, 'mm', sp=14)
def holly(d, cx, cy, s=1.0, ang=0):
    for a in (ang - 35, ang + 35):
        r = math.radians(a); ex, ey = cx + 120 * s * math.cos(r), cy + 120 * s * math.sin(r)
        nx, ny = -math.sin(r), math.cos(r); pts = []
        for k in range(9):
            u = k / 8; bx, by = cx + (ex - cx) * u, cy + (ey - cy) * u; w = 38 * s * math.sin(math.pi * u) * (1.25 if k % 2 else .8)
            pts.append((bx + nx * w, by + ny * w))
        for k in range(8, -1, -1):
            u = k / 8; bx, by = cx + (ex - cx) * u, cy + (ey - cy) * u; w = 38 * s * math.sin(math.pi * u) * (1.25 if k % 2 else .8)
            pts.append((bx - nx * w, by - ny * w))
        d.polygon(pts, fill=GREEN, outline=DGREEN)
        d.line((cx, cy, ex, ey), fill=DGREEN, width=max(2, int(5 * s)))
    for dx, dy in ((-16, 4), (14, 6), (0, -14)): d.ellipse((cx + dx * s - 20 * s, cy + dy * s - 20 * s, cx + dx * s + 20 * s, cy + dy * s + 20 * s), fill=RED, outline=DRED, width=3)
def pill(d, cx, cy, s, fs, fill=W, fg=INK):
    f = font('Outfit-800.ttf', fs); tw = d.textlength(s, font=f)
    d.rounded_rectangle((cx - tw / 2 - fs * .55, cy - fs * .75, cx + tw / 2 + fs * .55, cy + fs * .75), int(fs * .75), fill=fill, outline=INK, width=max(4, fs // 10))
    d.text((cx, cy), s, font=f, fill=fg, anchor='mm')

def k1():  # wreath around Haru, big script title below
    im = Image.new('RGBA', (S, S), DRED + (255,)); flakes(im, 120, 1, (255, 255, 255, 120), 5); d = ImageDraw.Draw(im)
    cx, cy, R = 750, 520, 330; r = random.Random(2)
    for k in range(260):
        a = r.uniform(0, 2 * math.pi); rr = R + r.uniform(-70, 70); x, y = cx + rr * math.cos(a), cy + rr * math.sin(a); s = r.uniform(30, 58)
        d.ellipse((x - s, y - s, x + s, y + s), fill=r.choice([GREEN, DGREEN, (60, 150, 95)]))
    for k in range(22):
        a = k / 22 * 2 * math.pi + .1; x, y = cx + (R + r.uniform(-40, 40)) * math.cos(a), cy + (R + r.uniform(-40, 40)) * math.sin(a); d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=RED, outline=W, width=3)
    d.polygon([(cx, cy + R - 10), (cx - 150, cy + R - 90), (cx - 150, cy + R + 70)], fill=RED); d.polygon([(cx, cy + R - 10), (cx + 150, cy + R - 90), (cx + 150, cy + R + 70)], fill=RED)
    d.polygon([(cx - 20, cy + R), (cx - 90, cy + R + 190), (cx - 30, cy + R + 160)], fill=RED); d.polygon([(cx + 20, cy + R), (cx + 90, cy + R + 190), (cx + 30, cy + R + 160)], fill=RED)
    d.ellipse((cx - 40, cy + R - 50, cx + 40, cy + R + 30), fill=DRED)
    hd = haru(4.0, head=True); im.alpha_composite(hd, (cx - hd.width // 2, cy - hd.height // 2 + 10)); d = ImageDraw.Draw(im)
    title(d, 1160, CREAM, W, GOLD, 250); brand(d, 1440, (255, 220, 220)); return im
def k2():  # candy-cane border + big script, Haru sticker
    im = Image.new('RGBA', (S, S), W + (255,)); d = ImageDraw.Draw(im); b = 70
    for k in range(-S, 2 * S, 70): d.polygon([(k, 0), (k + 35, 0), (k + 35 - S, S), (k - S, S)], fill=RED)
    d.rectangle((b, b, S - b, S - b), fill=(250, 244, 232)); d.rectangle((b, b, S - b, S - b), outline=DRED, width=6)
    flakes(im, 60, 3, (220, 226, 236, 255), 8, (b, b, S - b, S - b)); d = ImageDraw.Draw(im)
    holly(d, 200, 200, 1.0, 45); holly(d, 1300, 200, 1.0, 135)
    title(d, 470, INK, RED, GREEN, 280, False); brand(d, 170, INK)
    st = haru(2.4, sticker=True, walk=0.0); im.alpha_composite(st, (750 - st.width // 2, S - b - st.height + 30)); return im
def k3():  # red with holly corners and snow, white script
    im = Image.new('RGBA', (S, S), RED + (255,)); flakes(im, 160, 4, (255, 255, 255, 200), 7); d = ImageDraw.Draw(im)
    for (x, y, a) in ((130, 130, 45), (1370, 130, 135), (130, 1370, -45), (1370, 1370, -135)): holly(d, x, y, 1.3, a)
    title(d, 360, CREAM, W, GOLD, 300); brand(d, 1380, CREAM)
    w = haru(2.2, walk=0.0); im.alpha_composite(w, (750 - w.width // 2, 1290 - w.height)); d = ImageDraw.Draw(im)
    pill(d, 742, 1290 - int(w.height * .83) - 40, 'HARU', 40); return im
def k4():  # big tree with title, starry night
    im = Image.new('RGBA', (S, S), NIGHT + (255,)); flakes(im, 180, 5, (255, 255, 255, 200), 6); d = ImageDraw.Draw(im)
    for w_, y in [(380, 420), (560, 640), (760, 880), (960, 1130)]: d.polygon([(750, y - 300), (750 - w_ // 2, y), (750 + w_ // 2, y)], fill=GREEN)
    d.rectangle((700, 1130, 800, 1220), fill=(120, 80, 50)); d.regular_polygon((750, 120, 80), 5, rotation=-90, fill=GOLD)
    r = random.Random(6)
    for _ in range(40):
        y = r.uniform(200, 1120); half = (y - 100) * .42; x = 750 + r.uniform(-half, half); d.ellipse((x - 16, y - 16, x + 16, y + 16), fill=r.choice([RED, GOLD, W, (110, 180, 255)]))
    d.rectangle((0, 1220, S, S), fill=W)
    st = haru(2.4, sticker=True, walk=0.0); im.alpha_composite(st, (1170 - st.width // 2, 1250 - st.height + 30)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((340, 1150, 620, 1260), 16, fill=RED, outline=W, width=6); text(d, (480, 1205), 'HARU', font('Outfit-800.ttf', 52), W, 'mm', sp=8)
    title(d, 1365, NIGHT, RED, GREEN, 150, False); text(d, (90, 70), 'OPEN TO CLOSE', font('Outfit-800.ttf', 48), CREAM, 'lm', sp=12); return im
def k5():  # fireplace with stockings
    im = Image.new('RGBA', (S, S), (64, 36, 40, 255)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, S, 700), fill=(245, 230, 205)); title(d, 330, DRED, RED, GREEN, 260, False); brand(d, 80, DRED)
    d.rectangle((150, 700, 1350, 1500), fill=(170, 70, 60))
    for y in range(720, 1500, 70):
        for x in range(150 + (y // 70 % 2) * 60, 1350, 120): d.rectangle((x, y, x + 110, y + 60), outline=(140, 52, 46), width=5)
    d.rectangle((110, 660, 1390, 740), fill=(120, 80, 60)); d.rectangle((420, 900, 1080, 1500), fill=(30, 20, 24))
    for fx, c in ((620, (255, 150, 40)), (750, (255, 200, 60)), (880, (255, 150, 40))): d.polygon([(fx - 70, 1500), (fx, 1180), (fx + 70, 1500)], fill=c)
    for k, (x, col, nm) in enumerate(((330, RED, ''), (750, GREEN, 'HARU'), (1170, RED, ''))):
        d.rectangle((x - 60, 740, x + 60, 960), fill=col); d.ellipse((x - 60, 900, x + 110, 1020), fill=col); d.rectangle((x - 70, 740, x + 70, 800), fill=W)
        if nm: text(d, (x, 860), nm, font('Outfit-800.ttf', 40), W, 'mm', sp=4)
    hd = haru(2.0, head=True, sticker=True); im.alpha_composite(hd, (1080, 470)); return im
def k6():  # snowman with Haru
    im = Image.new('RGBA', (S, S), (120, 176, 230, 255)); flakes(im, 160, 7, (255, 255, 255, 230), 8); d = ImageDraw.Draw(im)
    d.ellipse((-300, 1050, S + 300, 1900), fill=W)
    for (cx, cy, r) in ((470, 1080, 200), (470, 830, 140), (470, 640, 100)): d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=W, outline=(200, 214, 230), width=6)
    for y in (800, 860, 920): d.ellipse((455, y - 12, 485, y + 18), fill=INK)
    d.ellipse((430, 610, 450, 630), fill=INK); d.ellipse((490, 610, 510, 630), fill=INK); d.polygon([(470, 640), (560, 660), (470, 665)], fill=(240, 140, 40))
    d.rectangle((360, 700, 580, 740), fill=RED); d.rectangle((520, 700, 570, 820), fill=RED); d.rectangle((390, 470, 550, 560), fill=INK); d.rectangle((350, 550, 590, 575), fill=INK)
    w = haru(2.6, walk=0.0); im.alpha_composite(w, (1020 - w.width // 2, 1240 - w.height + 40)); d = ImageDraw.Draw(im)
    pill(d, 1012, 1240 - int(w.height * .83) - 30, 'HARU', 44)
    title(d, 260, INK, RED, GREEN, 230, False); brand(d, 1420, INK); return im
def k7():  # 50s vintage carol record sleeve
    im = Image.new('RGBA', (S, S), (230, 215, 190, 255)); d = ImageDraw.Draw(im)
    d.rectangle((80, 80, S - 80, S - 80), fill=RED)
    r = random.Random(8)
    for _ in range(70):
        x, y, s = r.uniform(100, S - 100), r.uniform(100, S - 100), r.uniform(10, 26); d.ellipse((x - s, y - s, x + s, y + s), fill=(240, 120, 120))
    d.ellipse((780, 640, 1460, 1320), fill=(20, 20, 26))
    for rr in range(320, 120, -26): d.ellipse((1120 - rr, 980 - rr, 1120 + rr, 980 + rr), outline=(48, 48, 58), width=3)
    d.ellipse((1000, 860, 1240, 1100), fill=GREEN); holly(d, 1120, 980, .55, 90)
    title(d, 360, CREAM, W, GOLD, 270); brand(d, 130, CREAM)
    st = haru(2.4, sticker=True, walk=0.0); im.alpha_composite(st, (470 - st.width // 2, S - 80 - st.height + 30)); return im
def k8():  # ugly-sweater knit with knitted title
    im = Image.new('RGBA', (S, S), GREEN + (255,)); d = ImageDraw.Draw(im)
    for y in range(0, S, 26):
        for x in range((y // 26 % 2) * 13, S, 26): d.arc((x - 13, y - 10, x + 13, y + 16), 200, 340, fill=(36, 108, 66), width=4)
    for band, col in ((100, RED), (1300, RED)):
        d.rectangle((0, band, S, band + 120), fill=col)
        for x in range(0, S, 100): d.regular_polygon((x + 50, band + 60, 36), 4, fill=W)
    d.rounded_rectangle((180, 300, 1320, 760), 40, fill=W)
    title(d, 530, GREEN, RED, GREEN, 230, False)
    for x in (260, 1240):
        for k in range(3): d.regular_polygon((x, 900 + k * 120, 40), 6, rotation=30, fill=W)
    hd = haru(3.4, head=True, sticker=True); im.alpha_composite(hd, (750 - hd.width // 2, 1040 - hd.height // 2)); d = ImageDraw.Draw(im)
    pill(d, 742, 1040 - hd.height // 2 + 10, 'HARU', 40); brand(d, 1460, W); return im

names = ['⑨ 리스(화환) + 큰 필기체', '⑩ 캔디케인 테두리', '⑪ 빨간 바탕 + 호랑가시 잎', '⑫ 큰 트리 + 별밤', '⑬ 벽난로 + 양말 (HARU 양말)', '⑭ 눈사람과 하루', '⑮ 50년대 캐롤 레코드 자켓', '16 어글리 스웨터 니트']
ims = [f() for f in (k1, k2, k3, k4, k5, k6, k7, k8)]
for i, im in enumerate(ims): im.convert('RGB').save(f'{OUTDIR}/pl04b_cover{i + 9}.png')
T = 520; G = 40; sheet = Image.new('RGB', (4 * T + 5 * G, 2 * (T + 90) + G), 'white'); dd = ImageDraw.Draw(sheet)
for i, im in enumerate(ims):
    x = G + (i % 4) * (T + G); y = G + (i // 4) * (T + 90)
    dd.text((x, y), names[i], font=font('NanumSquareRoundB.ttf', 30), fill=INK); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, y + 50))
sheet.save(f'{OUTDIR}/pl04b_covers_sheet.png'); print('ok')
