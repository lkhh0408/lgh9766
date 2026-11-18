import sys, cairo
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/user/lgh9766/studio')
import character as ch
O = [
 ('1 크림 꽈배기 니트 · 빨강 털 귀마개 헤드폰', dict(top='#F3E6CF', bottom='#5A3A2E', phones='#D94040', phones_style='fluffy', prop='cocoa', scarf='#C0392B', knit=True, mitten='#C0392B')),
 ('2 초록 비니 · 빨강 니트 · 흰 털 헤드폰', dict(top='#D94040', bottom='#2F3E46', phones='#FFFFFF', phones_style='fluffy', prop='gift', hat='beanie', hat_color='#2E8B57', knit=True, mitten='#2E8B57')),
 ('3 산타 모자 · 빨강 코트 · 골드 헤드폰', dict(top='#C62E2E', bottom='#2B2B3A', phones='#F2C230', phones_style='retro', prop='cocoa', hat='santa', hat_color='#D94040', coat=True, mitten='#FFFFFF')),
 ('4 루돌프 머리띠 · 브라운 더플코트', dict(top='#9A6B47', bottom='#3E4A6B', phones='#F3E9D2', phones_style='retro', prop='gift', hat='antlers', hat_color='#D94040', coat=True, scarf='#2E8B57', mitten='#D94040')),
 ('5 그린 코트 · 빨강 비니 · 빨강 헤드폰', dict(top='#2E7D4F', bottom='#2B2B3A', phones='#D94040', phones_style='retro', prop='hot', hat='beanie', hat_color='#D94040', coat=True, scarf='#F3E6CF')),
 ('6 화이트 패딩 · 빨강 머플러 · 빨강 털 헤드폰', dict(top='#F7F7F7', bottom='#C62E2E', phones='#D94040', phones_style='fluffy', prop='cocoa', scarf='#D94040', mitten='#D94040')),
 ('7 버건디 니트 · 크림 비니 · 골드 헤드폰', dict(top='#7B1E3A', bottom='#3A3A46', phones='#F2C230', phones_style='retro', prop='hot', hat='beanie', hat_color='#F3E6CF', knit=True, scarf='#F2C230')),
 ('8 네이비 코트 · 흰 비니 · 실버 털 헤드폰', dict(top='#2C3E66', bottom='#1F2A44', phones='#DDE3EC', phones_style='fluffy', prop='cocoa', hat='beanie', hat_color='#FFFFFF', coat=True, scarf='#9BC4E2', mitten='#9BC4E2')),
]
W, H = 420, 640
f = ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf', 20) if __import__('os').path.exists('/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf') else ImageFont.truetype('/home/user/lgh9766/studio/assets/fonts/NanumSquareRoundB.ttf', 20)
sheet = Image.new('RGB', (4 * W, 2 * H), '#FFF8EE')
for i, (name, o) in enumerate(O):
    ch.OUTFITS['_x'] = o
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H - 60); c = cairo.Context(s)
    c.set_source_rgb(1, .97, .93); c.paint()
    c.translate(W / 2 - 20, H - 110); c.scale(1.6, 1.6)
    ch.draw(c, 0, 0, t=0.5, phase=0.9, walk=1.0, outfit='_x')
    s.flush(); im = Image.frombuffer('RGBA', (W, H - 60), bytes(s.get_data()), 'raw', 'BGRA', 0, 1).convert('RGB')
    x, y = (i % 4) * W, (i // 4) * H
    sheet.paste(im, (x, y + 50)); ImageDraw.Draw(sheet).text((x + 14, y + 14), name, fill='#1F2340', font=f)
sheet.save(sys.argv[1]); print('ok')
