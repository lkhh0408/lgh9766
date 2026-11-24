"""4-panel comic cover (round 2, #8) with Haru's name in different places. python3 comic_name.py OUTDIR"""
from PIL import Image, ImageDraw
from cover_drafts import *
SKY = (143, 208, 255); SUN = (255, 214, 102); NAVY = (31, 35, 64)
g = 40; c = (S - 3 * g) // 2
def base(sub=None):
    im = Image.new('RGBA', (S, S), (255, 255, 255, 255)); d = ImageDraw.Draw(im)
    for k, col in enumerate([SUN, SKY, A, NAVY]):
        x, y = g + (k % 2) * (c + g), g + (k // 2) * (c + g); d.rectangle((x, y, x + c, y + c), fill=col, outline=INK, width=8)
    hd = haru(4.6, head=True); im.alpha_composite(hd, (g + c // 2 - hd.width // 2, g + c // 2 - hd.height // 2 + 30))
    w = haru(2.4, phase=2.2); im.alpha_composite(w, (2 * g + c + c // 2 - w.width // 2, g + c - w.height + 20))
    st = haru(2.6, flip=False); im.alpha_composite(st, (g + c // 2 - st.width // 2, 2 * g + 2 * c - st.height + 20))
    x0 = y0 = 2 * g + c
    text(d, (x0 + c // 2, y0 + c // 2 - 90), 'OPEN TO', font('Outfit-800.ttf', 96), CREAM, 'mm'); text(d, (x0 + c // 2, y0 + c // 2 + 10), 'CLOSE', font('Outfit-800.ttf', 96), CREAM, 'mm')
    text(d, (x0 + c // 2, y0 + c // 2 + 130), sub or f'PLAY LIST {NUM}', font('Outfit-800.ttf', 50 if not sub else 40), A, 'mm', sp=10)
    return im, d
def pill(d, cx, cy, s, fs, fill=(255, 255, 255), fg=INK):
    f = font('Outfit-800.ttf', fs); tw = d.textlength(s, font=f)
    d.rounded_rectangle((cx - tw / 2 - fs * .55, cy - fs * .75, cx + tw / 2 + fs * .55, cy + fs * .75), int(fs * .75), fill=fill, outline=INK, width=max(4, fs // 10))
    d.text((cx, cy), s, font=f, fill=fg, anchor='mm')
def vA():  # name tag above the big head (like the video)
    im, d = base(); pill(d, g + c // 2 - 10, g + 70, 'HARU', 50); return im
def vB():  # in the title panel
    im, d = base(f'PLAY LIST {NUM} · HARU'); return im
def vC():  # comic speech bubble in the walking panel
    im, d = base(); bx, by = 2 * g + 2 * c - 285, g + 24
    d.rounded_rectangle((bx, by, bx + 265, by + 110), 55, fill=(255, 255, 255), outline=INK, width=8)
    d.polygon([(bx + 60, by + 100), (bx + 20, by + 160), (bx + 110, by + 100)], fill=(255, 255, 255)); d.line((bx + 60, by + 104, bx + 20, by + 160, bx + 110, by + 104), fill=INK, width=8)
    d.text((bx + 132, by + 55), "I'M HARU!", font=font('Outfit-800.ttf', 42), fill=INK, anchor='mm'); return im
def vD():  # comic caption box in the corner of each picture panel
    im, d = base()
    for (x, y), s in zip([(g, g), (2 * g + c, g), (g, 2 * g + c)], ['HARU', 'HARU', 'HARU']):
        d.rectangle((x + 4, y + 4, x + 250, y + 84), fill=(255, 255, 255), outline=INK, width=6); d.text((x + 127, y + 44), s, font=font('Outfit-800.ttf', 46), fill=INK, anchor='mm')
    return im
def vE():  # one caption box, first panel only, with Korean name
    im, d = base(); x, y = g, g
    d.rectangle((x + 4, y + 4, x + 330, y + 120), fill=(255, 255, 255), outline=INK, width=6)
    d.text((x + 167, y + 46), 'HARU', font=font('Outfit-800.ttf', 50), fill=INK, anchor='mm'); d.text((x + 167, y + 96), '하루', font=font('NanumSquareRoundB.ttf', 34), fill=A, anchor='mm'); return im
names = ['A. 큰 얼굴 위 이름표', 'B. 제목 칸에 함께', 'C. 말풍선 "I\'M HARU!"', 'D. 그림 칸마다 이름 상자', 'E. 첫 칸에만 이름 상자']
ims = [vA(), vB(), vC(), vD(), vE()]
for i, im in enumerate(ims): im.convert('RGB').save(f'{OUT}/comic_name_{"ABCDE"[i]}.png')
T = 460; G = 36; sheet = Image.new('RGB', (5 * T + 6 * G, T + 120), 'white'); d = ImageDraw.Draw(sheet)
for i, im in enumerate(ims):
    x = G + i * (T + G); d.text((x, G), names[i], font=font('NanumSquareRoundB.ttf', 28), fill=INK); sheet.paste(im.convert('RGB').resize((T, T), Image.LANCZOS), (x, G + 46))
sheet.save(f'{OUT}/comic_name_sheet.png'); print('ok')
