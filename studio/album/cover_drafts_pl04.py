"""Haru's Christmas Playlist (PLAY LIST 04) album cover drafts. python3 cover_drafts_pl04.py OUTDIR"""
import sys, math, json
from PIL import Image, ImageDraw, ImageFilter
OUTDIR = sys.argv[1]
sys.argv = [sys.argv[0], OUTDIR, 'xmas_santa', '04', '#D94040']
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch
SB = json.load(open('/home/user/lgh9766/playlists/vol04/storyboard.json'))
ch.OUTFITS['xmas_santa'] = dict(SB['segments'][5][2])      # sky-sleigh look: red coat, santa hat (same as the PL04 thumbnail)
import cover_drafts as cd
from cover_drafts import haru, text, font, INK, CREAM, S
RED = (217, 64, 64); GREEN = (46, 125, 79); GOLD = (242, 194, 48); NIGHT = (24, 32, 64); SNOW = (255, 255, 255)
TITLE = "HARU'S CHRISTMAS PLAYLIST"

def flakes(im, n=140, seed=4, col=(255, 255, 255, 200), rmax=7):
    import random; r = random.Random(seed); d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y, s = r.uniform(0, S), r.uniform(0, S), r.uniform(2, rmax); d.ellipse((x - s, y - s, x + s, y + s), fill=col)
def pill(d, cx, cy, s, fs, fill=SNOW, fg=INK):
    f = font('Outfit-800.ttf', fs); tw = d.textlength(s, font=f)
    d.rounded_rectangle((cx - tw / 2 - fs * .55, cy - fs * .75, cx + tw / 2 + fs * .55, cy + fs * .75), int(fs * .75), fill=fill, outline=INK, width=max(4, fs // 10))
    d.text((cx, cy), s, font=f, fill=fg, anchor='mm')
def titles(d, y, c1=INK, c2=RED, s1=100, s2=50):
    text(d, (S // 2, y), 'OPEN TO CLOSE', font('Outfit-800.ttf', s1), c1, 'mm', sp=12)
    text(d, (S // 2, y + s1 * .95), TITLE, font('Outfit-800.ttf', s2), c2, 'mm', sp=12)

def c1():  # snow globe
    im = Image.new('RGBA', (S, S), NIGHT + (255,)); flakes(im, 90, 1, (255, 255, 255, 120), 5); d = ImageDraw.Draw(im)
    cx, cy, R = 750, 640, 470
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(205, 232, 255))
    g = Image.new('RGBA', (S, S)); gd = ImageDraw.Draw(g); gd.ellipse((cx - R, cy + 180, cx + R, cy + R + 200), fill=SNOW)
    m = Image.new('L', (S, S)); ImageDraw.Draw(m).ellipse((cx - R, cy - R, cx + R, cy + R), fill=255); im.paste(g, (0, 0), Image.composite(g, Image.new('RGBA', (S, S)), m))
    w = haru(2.8, walk=0.0); im.alpha_composite(w, (cx - w.width // 2, cy + 260 - w.height + 40))
    flakes(im, 0); fl = Image.new('RGBA', (S, S)); flakes(fl, 60, 7, (255, 255, 255, 230), 8); im.paste(fl, (0, 0), Image.composite(fl, Image.new('RGBA', (S, S)), m))
    d = ImageDraw.Draw(im); d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=SNOW, width=14)
    d.arc((cx - R + 60, cy - R + 60, cx + R - 60, cy + R - 60), 200, 250, fill=(255, 255, 255, 200), width=18)
    d.polygon([(cx - 380, cy + 400), (cx + 380, cy + 400), (cx + 460, cy + 600), (cx - 460, cy + 600)], fill=RED)
    d.rectangle((cx - 470, cy + 600, cx + 470, cy + 650), fill=(150, 40, 40))
    d.rounded_rectangle((cx - 150, cy + 455, cx + 150, cy + 545), 14, fill=GOLD); text(d, (cx, cy + 500), 'HARU', font('Outfit-800.ttf', 58), INK, 'mm', sp=8)
    titles(d, 1370, SNOW, GOLD, 88, 46); return im
def c2():  # ornament ball with name tag
    im = Image.new('RGBA', (S, S), GREEN + (255,)); d = ImageDraw.Draw(im)
    for x in range(0, S, 60): d.line((x, 0, x - 400, S), fill=(52, 136, 88), width=14)
    d.line((750, 0, 750, 230), fill=GOLD, width=10); d.rounded_rectangle((680, 220, 820, 300), 16, fill=GOLD)
    d.ellipse((330, 280, 1170, 1120), fill=RED)
    for y in (560, 840): d.arc((330, y - 140, 1170, y + 140), 10, 170, fill=GOLD, width=16)
    d.ellipse((430, 360, 620, 470), fill=(255, 140, 140))
    hd = haru(5.2, head=True); im.alpha_composite(hd, (750 - hd.width // 2, 720 - hd.height // 2))
    tg = Image.new('RGBA', (360, 160)); td = ImageDraw.Draw(tg); td.rounded_rectangle((0, 0, 359, 159), 20, fill=CREAM, outline=INK, width=8)
    td.ellipse((24, 66, 52, 94), fill=GREEN); td.text((200, 80), 'HARU', font=font('Outfit-800.ttf', 74), fill=RED, anchor='mm')
    tg = tg.rotate(-14, expand=True, resample=Image.BICUBIC); im.alpha_composite(tg, (1000, 1010)); d = ImageDraw.Draw(im)
    d.line((1080, 1020, 1060, 960), fill=GOLD, width=6)
    titles(d, 1330, SNOW, GOLD, 100, 50); return im
def c3():  # advent door (links to the video's scene changes)
    im = Image.new('RGBA', (S, S), (184, 50, 58, 255)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((300, 180, 1200, 1180), 30, fill=(140, 30, 40))
    d.rectangle((330, 210, 1170, 1150), fill=(214, 232, 255)); flakes(im, 0)
    w = haru(3.0, walk=0.0); im.alpha_composite(w, (750 - w.width // 2, 1150 - w.height + 46)); d = ImageDraw.Draw(im)
    d.polygon([(330, 210), (180, 280), (180, 1080), (330, 1150)], fill=(200, 60, 66)); d.rounded_rectangle((200, 520, 300, 840), 20, outline=GOLD, width=10)
    d.polygon([(1170, 210), (1320, 280), (1320, 1080), (1170, 1150)], fill=(200, 60, 66)); d.rounded_rectangle((1200, 520, 1300, 840), 20, outline=GOLD, width=10)
    pill(d, 742, 300, 'HARU', 50)
    titles(d, 1320, CREAM, GOLD, 100, 50); return im
def c4():  # vintage postcard
    im = Image.new('RGBA', (S, S), (244, 234, 214, 255)); d = ImageDraw.Draw(im)
    d.rectangle((60, 60, S - 60, S - 60), outline=RED, width=16); d.rectangle((90, 90, S - 90, S - 90), outline=GREEN, width=8)
    d.rectangle((140, 140, 960, 1060), fill=(36, 52, 96)); flakes(im, 0)
    sub = Image.new('RGBA', (820, 920), (36, 52, 96, 255)); flakes_l = ImageDraw.Draw(sub)
    import random; r = random.Random(3)
    for _ in range(80):
        x, y, s = r.uniform(0, 820), r.uniform(0, 920), r.uniform(3, 8); flakes_l.ellipse((x - s, y - s, x + s, y + s), fill=SNOW)
    flakes_l.rectangle((0, 760, 820, 920), fill=SNOW); w = haru(2.6, walk=0.0); sub.alpha_composite(w, (410 - w.width // 2, 800 - w.height + 40))
    im.alpha_composite(sub, (140, 140)); d = ImageDraw.Draw(im)
    d.rectangle((1080, 160, 1340, 460), fill=RED); d.rectangle((1100, 180, 1320, 440), fill=CREAM)
    hd = haru(1.8, head=True); im.alpha_composite(hd, (1210 - hd.width // 2, 310 - hd.height // 2)); d = ImageDraw.Draw(im)
    for k in range(4): d.line((1040, 560 + k * 110, 1360, 560 + k * 110), fill=(180, 160, 130), width=4)
    text(d, (1030, 520), 'From. HARU', font('Pacifico-Regular.ttf', 50), RED)
    text(d, (S // 2, 1180), 'OPEN TO CLOSE', font('Outfit-800.ttf', 110), INK, 'mm', sp=12)
    text(d, (S // 2, 1290), TITLE, font('Outfit-800.ttf', 54), RED, 'mm', sp=12); return im
def c5():  # knit sweater pattern + badge
    im = Image.new('RGBA', (S, S), RED + (255,)); d = ImageDraw.Draw(im)
    for band in (130, 1290):
        d.rectangle((0, band, S, band + 110), fill=CREAM)
        for x in range(0, S, 80):
            d.polygon([(x, band + 55), (x + 40, band + 15), (x + 80, band + 55), (x + 40, band + 95)], fill=GREEN)
    for y in range(300, 1250, 90):
        for x in range((y // 90 % 2) * 45, S, 90): d.text((x, y), '✳', font=font('NanumSquareRoundB.ttf', 30), fill=(235, 120, 120), anchor='mm')
    d.ellipse((390, 330, 1110, 1050), fill=CREAM, outline=INK, width=12)
    hd = haru(5.0, head=True); im.alpha_composite(hd, (750 - hd.width // 2, 700 - hd.height // 2)); d = ImageDraw.Draw(im)
    pill(d, 742, 292, 'HARU', 46)
    d.rounded_rectangle((260, 1080, 1240, 1270), 30, fill=INK)
    text(d, (S // 2, 1135), 'OPEN TO CLOSE', font('Outfit-800.ttf', 92), CREAM, 'mm', sp=10)
    text(d, (S // 2, 1225), TITLE, font('Outfit-800.ttf', 48), GOLD, 'mm', sp=10); return im
def c6():  # gift box with tag
    im = Image.new('RGBA', (S, S), (240, 230, 214, 255)); flakes(im, 70, 2, (255, 255, 255, 255), 9); d = ImageDraw.Draw(im)
    d.rectangle((300, 600, 1200, 1250), fill=RED); d.rectangle((260, 500, 1240, 640), fill=(196, 46, 46))
    d.rectangle((700, 500, 800, 1250), fill=GOLD); d.rectangle((260, 545, 1240, 600), fill=GOLD)
    d.ellipse((560, 380, 750, 520), outline=GOLD, width=34); d.ellipse((750, 380, 940, 520), outline=GOLD, width=34)
    hd = haru(3.6, head=True, sticker=True); im.alpha_composite(hd, (750 - hd.width // 2, 330 - hd.height // 2)); d = ImageDraw.Draw(im)
    tg = Image.new('RGBA', (420, 220)); td = ImageDraw.Draw(tg); td.rounded_rectangle((0, 0, 419, 219), 24, fill=CREAM, outline=INK, width=8)
    td.text((210, 70), 'To. you', font=font('Pacifico-Regular.ttf', 56), fill=INK, anchor='mm'); td.text((210, 150), 'From. HARU', font=font('Pacifico-Regular.ttf', 56), fill=RED, anchor='mm')
    im.alpha_composite(tg.rotate(8, expand=True, resample=Image.BICUBIC), (880, 760)); d = ImageDraw.Draw(im)
    titles(d, 1340, INK, RED, 100, 50); return im
def c7():  # big moon night walk, name tag
    im = Image.new('RGBA', (S, S), NIGHT + (255,)); flakes(im, 160, 9, (255, 255, 255, 220), 6); d = ImageDraw.Draw(im)
    d.ellipse((300, 150, 1200, 1050), fill=(255, 236, 170))
    for x, h in [(0, 260), (220, 330), (520, 280), (900, 340), (1180, 300)]:
        d.rectangle((x, 1150 - h, x + 250, 1150), fill=(40, 52, 92))
        for wy in range(1150 - h + 40, 1130, 80):
            for wx in (x + 50, x + 150): d.rectangle((wx, wy, wx + 40, wy + 40), fill=GOLD)
    d.rectangle((0, 1150, S, S), fill=SNOW)
    w = haru(3.2); im.alpha_composite(w, (750 - w.width // 2, 1180 - w.height + 46)); d = ImageDraw.Draw(im)
    pill(d, 742, 1180 - int(w.height * .83) - 45, 'HARU', 46)
    titles(d, 1300, NIGHT, RED, 96, 48); return im
def c8():  # tree with Haru as the star view: tree + Haru beside, name on tree-skirt sign
    im = Image.new('RGBA', (S, S), (250, 244, 232, 255)); d = ImageDraw.Draw(im)
    for k, (w_, y) in enumerate([(300, 300), (420, 520), (540, 740), (660, 960)]):
        d.polygon([(560, y - 220), (560 - w_ // 2, y + 60), (560 + w_ // 2, y + 60)], fill=GREEN)
    d.rectangle((520, 1020, 600, 1120), fill=(120, 80, 50)); d.regular_polygon((560, 70, 70), 5, rotation=-90, fill=GOLD)
    import random; r = random.Random(5)
    for _ in range(26):
        y = r.uniform(180, 1000); half = (y - 80) * .33; x = 560 + r.uniform(-half, half); c = r.choice([RED, GOLD, (90, 160, 230), SNOW])
        d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=c)
    st = haru(3.4, sticker=True); im.alpha_composite(st, (1110 - st.width // 2, 1150 - st.height + 80)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((380, 1110, 740, 1200), 20, fill=RED); text(d, (560, 1155), 'HARU', font('Outfit-800.ttf', 60), CREAM, 'mm', sp=10)
    titles(d, 1300, INK, RED, 100, 50); return im

names = ['① 스노우볼', '② 트리 장식볼 + 이름 태그', '③ 어드벤트 캘린더 문 (영상 연결)', '④ 빈티지 크리스마스 엽서', '⑤ 니트 스웨터 무늬 + 배지', '⑥ 선물 상자 + From. HARU', '⑦ 보름달 밤 눈길', '⑧ 크리스마스 트리 + 이름 팻말']
ims = [f() for f in (c1, c2, c3, c4, c5, c6, c7, c8)]
for i, im in enumerate(ims): im.convert('RGB').save(f'{OUTDIR}/pl04_cover{i + 1}.png')
T = 520; G = 40; sheet = Image.new('RGB', (4 * T + 5 * G, 2 * (T + 90) + G), 'white'); d = ImageDraw.Draw(sheet)
for i, im in enumerate(ims):
    x = G + (i % 4) * (T + G); y = G + (i // 4) * (T + 90)
    d.text((x, y), names[i], font=font('NanumSquareRoundB.ttf', 30), fill=INK); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, y + 50))
sheet.save(f'{OUTDIR}/pl04_covers_sheet.png'); print('ok')
