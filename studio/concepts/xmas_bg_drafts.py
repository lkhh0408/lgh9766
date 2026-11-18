import sys, cairo
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/user/lgh9766/studio'); sys.path.insert(0, '/home/user/lgh9766/studio/concepts')
import character as ch, xmas
exec(open('/home/user/lgh9766/studio/concepts/xmas_outfits.py').read().split('W, H =')[0])  # O list
OF = {k: O[i][1] for k, i in (('canal', 0), ('downtown', 6), ('park', 1), ('market', 3), ('lane', 7), ('sky', 2))}
LABEL = {'canal': '01~04 아침 · 스케이트 · 얼어붙은 운하 마을', 'downtown': '05~07 낮 · 트램 · 크리스마스 시내', 'park': '08~10 오후 · 눈썰매 · 눈 덮인 공원 언덕',
         'market': '11~14 노을 · 방울 마차 · 마켓 광장', 'lane': '15~17 밤 · 걷기 · 주택가 골목', 'sky': '18~20 밤 · 루돌프 하늘 썰매 · 밤하늘'}
out = sys.argv[1]; tiles = []
for k, (fn, m) in xmas.SCENES.items():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, xmas.W, xmas.H); c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    fn(c, m, 600.0, 3.0)
    ch.OUTFITS['_x'] = OF[k]
    gy = {'canal': 900, 'downtown': 900, 'park': xmas.GY, 'market': 880, 'lane': 880, 'sky': 600}[k]
    c.save(); c.translate(820, gy); c.scale(1.25, 1.25); ch.draw(c, 0, 0, 3.0, outfit='_x', walk=0.6, phase=0.9); c.restore()
    s.flush(); im = Image.frombuffer('RGBA', (xmas.W, xmas.H), bytes(s.get_data()), 'raw', 'BGRA', 0, 1).convert('RGB')
    im.save(f'{out}_{k}.png'); tiles.append((k, im.resize((960, 540))))
f = ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf', 30)
sheet = Image.new('RGB', (1950, 3 * 600 + 10), 'white'); d = ImageDraw.Draw(sheet)
for i, (k, im) in enumerate(tiles):
    x, y = (i % 2) * 990, (i // 2) * 600 + 10; d.text((x + 6, y), LABEL[k], fill='#1F2340', font=f); sheet.paste(im, (x, y + 50))
sheet.save(out + '.png'); print('ok')
