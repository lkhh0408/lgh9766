"""Window cover (round 2, #4) with Haru's name in different places. python3 window_name.py OUTDIR"""
from PIL import Image, ImageDraw
from cover_drafts import *
SKY = (143, 208, 255); SUN = (255, 214, 102)
def base():
    im = Image.new('RGBA', (S, S), (240, 226, 200, 255)); d = ImageDraw.Draw(im)
    d.rectangle((250, 200, 1250, 1200), fill=SKY); d.ellipse((850, 300, 1100, 550), fill=SUN)
    for x, y, r in [(420, 420, 90), (520, 400, 110), (620, 430, 80)]: d.ellipse((x - r, y - r * .6, x + r, y + r * .6), fill=(255, 255, 255))
    d.rectangle((250, 960, 1250, 1200), fill=(200, 196, 210)); w = haru(2.9); im.alpha_composite(w, (750 - w.width // 2, 1060 - w.height + 46))
    d.rectangle((250, 200, 1250, 1200), outline=(255, 255, 255), width=40); d.rectangle((200, 1200, 1300, 1260), fill=(255, 255, 255))
    return im, d
def pill(d, cx, cy, s, fs, fill=(255, 255, 255), fg=INK):
    f = font('Outfit-800.ttf', fs); tw = d.textlength(s, font=f)
    d.rounded_rectangle((cx - tw / 2 - fs * .55, cy - fs * .75, cx + tw / 2 + fs * .55, cy + fs * .75), int(fs * .75), fill=fill, outline=INK, width=max(4, fs // 10))
    d.text((cx, cy), s, font=f, fill=fg, anchor='mm')
def title(d, sub=f'PLAY LIST {NUM}'):
    text(d, (S // 2, 1360), 'OPEN TO CLOSE', font('Outfit-800.ttf', 100), INK, 'mm', sp=12); text(d, (S // 2, 1450), sub, font('Outfit-800.ttf', 50), A, 'mm', sp=18)
def vA():  # name tag above the head, like the video
    im, d = base(); pill(d, 742, 262, 'HARU', 46); title(d); return im
def vB():  # in the subtitle line
    im, d = base(); title(d, f'PLAY LIST {NUM}  ·  HARU'); return im
def vC():  # a little plate hanging on the window
    im, d = base(); d.line((520, 1265, 520, 1300), fill=INK, width=6); d.line((980, 1265, 980, 1300), fill=INK, width=6)
    d.rounded_rectangle((410, 1290, 1090, 1400), 24, fill=A, outline=INK, width=6)
    text(d, (750, 1346), "HARU'S WINDOW", font('Outfit-800.ttf', 50), CREAM, 'mm', sp=8)
    text(d, (S // 2, 110), 'OPEN TO CLOSE', font('Outfit-800.ttf', 96), INK, 'mm', sp=12)
    text(d, (S // 2, 1460), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 44), A, 'mm', sp=16); return im
def vD():  # sticker-style name label on the window corner
    im, d = base(); t = Image.new('RGBA', (430, 170)); td = ImageDraw.Draw(t)
    td.rounded_rectangle((6, 6, 424, 164), 40, fill=A, outline=(255, 255, 255), width=12)
    td.text((215, 70), 'HARU', font=font('Outfit-800.ttf', 76), fill=CREAM, anchor='mm'); td.text((215, 128), '하루', font=font('NanumSquareRoundB.ttf', 40), fill=CREAM, anchor='mm')
    t = t.rotate(-8, expand=True, resample=Image.BICUBIC); im.alpha_composite(t, (980, 130)); title(d); return im
names = ['A. 머리 위 이름표 (영상과 같음)', 'B. 제목 줄에 함께', 'C. 창문 아래 명패', 'D. 창문 모서리 스티커']
ims = [vA(), vB(), vC(), vD()]
for i, im in enumerate(ims): im.convert('RGB').save(f'{OUT}/win_name_{"ABCD"[i]}.png')
T = 560; G = 40; sheet = Image.new('RGB', (4 * T + 5 * G, T + 130), 'white'); d = ImageDraw.Draw(sheet)
for i, im in enumerate(ims):
    x = G + i * (T + G); d.text((x, G), names[i], font=font('NanumSquareRoundB.ttf', 30), fill=INK); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, G + 50))
sheet.save(f'{OUT}/win_name_sheet.png'); print('ok')
