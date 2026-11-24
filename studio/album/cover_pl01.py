"""PLAY LIST 01 album cover (final): 4-panel comic + HARU name tag above the big head. 3000x3000.
python3 cover_pl01.py OUT.png"""
import sys
from PIL import Image, ImageDraw
sys.argv = [sys.argv[0], '.', 'vol01', '01', '#E0457B'] + sys.argv[1:]
from cover_drafts import haru, text, font, INK, CREAM, A, NUM
OUT = sys.argv[5]; K = 2; S = 1500 * K
SKY = (143, 208, 255); SUN = (255, 214, 102); NAVY = (31, 35, 64)
g = 40 * K; c = (S - 3 * g) // 2
im = Image.new('RGBA', (S, S), (255, 255, 255, 255)); d = ImageDraw.Draw(im)
for k, col in enumerate([SUN, SKY, A, NAVY]):
    x, y = g + (k % 2) * (c + g), g + (k // 2) * (c + g); d.rectangle((x, y, x + c, y + c), fill=col, outline=INK, width=8 * K)
hd = haru(4.6 * K, head=True); im.alpha_composite(hd, (g + c // 2 - hd.width // 2, g + c // 2 - hd.height // 2 + 30 * K))
w = haru(2.4 * K, phase=2.2); im.alpha_composite(w, (2 * g + c + c // 2 - w.width // 2, g + c - w.height + 20 * K))
st = haru(2.6 * K, flip=False); im.alpha_composite(st, (g + c // 2 - st.width // 2, 2 * g + 2 * c - st.height + 20 * K))
x0 = y0 = 2 * g + c
text(d, (x0 + c // 2, y0 + c // 2 - 90 * K), 'OPEN TO', font('Outfit-800.ttf', 96 * K), CREAM, 'mm'); text(d, (x0 + c // 2, y0 + c // 2 + 10 * K), 'CLOSE', font('Outfit-800.ttf', 96 * K), CREAM, 'mm')
text(d, (x0 + c // 2, y0 + c // 2 + 130 * K), f'PLAY LIST {NUM}', font('Outfit-800.ttf', 50 * K), A, 'mm', sp=10 * K)
fs = 50 * K; f = font('Outfit-800.ttf', fs); cx, cy = g + c // 2 - 10 * K, g + 70 * K; tw = d.textlength('HARU', font=f)
d.rounded_rectangle((cx - tw / 2 - fs * .55, cy - fs * .75, cx + tw / 2 + fs * .55, cy + fs * .75), int(fs * .75), fill=(255, 255, 255), outline=INK, width=fs // 10)
d.text((cx, cy), 'HARU', font=f, fill=INK, anchor='mm')
im.convert('RGB').save(OUT, quality=95); print(OUT, im.size)
