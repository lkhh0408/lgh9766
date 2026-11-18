"""PLAY LIST 04 draft sheet: six neighbourhoods, each with its ride and outfit. usage: python3 xmas_bg_drafts.py OUT_PREFIX"""
import sys, cairo
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch, xmas, xmas_rides as R
exec(open('/home/user/lgh9766/studio/concepts/xmas_outfits.py').read().split('W, H =')[0])  # O: the 8 outfit drafts
SEG = [  # scene, outfit index (1-based), label
    ('canal', 4, '01~04 아침 · 스케이트 · 얼어붙은 운하 마을 · 의상 4'),
    ('downtown', 7, '05~07 낮 · 트램 · 크리스마스 시내 · 의상 7'),
    ('park', 2, '08~10 오후 · 허스키 개썰매 · 눈 덮인 공원 언덕 · 의상 2'),
    ('market', 5, '11~14 노을 · 방울 마차 · 마켓 광장 · 의상 5'),
    ('lane', 6, '15~17 밤 · 걷기 · 주택가 골목 · 의상 6'),
    ('sky', 3, '18~20 밤 · 루돌프 하늘 썰매 · 밤하늘 · 의상 3')]
out = sys.argv[1]; tiles = []; T = 3.0
for k, oi, label in SEG:
    fn, m = xmas.SCENES[k]; ch.OUTFITS['_x'] = O[oi - 1][1]
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, xmas.W, xmas.H); c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    fn(c, m, 600.0, T)
    if k == 'canal': R.skate(c, 820, 930, T, '_x')
    elif k == 'downtown': R.tram(c, 820, 950, T, '_x')
    elif k == 'park': R.dogsled(c, 560, 930, T, '_x')
    elif k == 'market': R.carriage(c, 620, 930, T, '_x', lit=True)
    elif k == 'lane': R.haru(c, 820, 900, T, '_x', walk=1.0, phase=.9, scale=1.2)
    elif k == 'sky': R.sky_sleigh(c, 620, 470, T, '_x')
    s.flush(); im = Image.frombuffer('RGBA', (xmas.W, xmas.H), bytes(s.get_data()), 'raw', 'BGRA', 0, 1).convert('RGB')
    im.save(f'{out}_{k}.png'); tiles.append((label, im.resize((960, 540))))
f = ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf', 28)
sheet = Image.new('RGB', (1950, 3 * 600 + 10), 'white'); d = ImageDraw.Draw(sheet)
for i, (label, im) in enumerate(tiles):
    x, y = (i % 2) * 990, (i // 2) * 600 + 10; d.text((x + 6, y), label, fill='#1F2340', font=f); sheet.paste(im, (x, y + 50))
sheet.save(out + '.png'); print('ok')
