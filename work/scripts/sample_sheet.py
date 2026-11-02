"""계절 샘플 이미지를 계절별로 모아 한 장(2열)으로 붙인다. 무료. 한글 글꼴이 없어 이름표는 영어로 단다.
사용: python3 work/scripts/sample_sheet.py <샘플폴더> <출력폴더>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

SEASON = {'봄': 'Spring', '여름': 'Summer', '가을': 'Autumn', '겨울': 'Winter'}
VIEW = {'원경': 'far', '접근': 'approach', '중경': 'mid', '타워': 'tower', '전망대': 'deck'}
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 34)


def label(name):
    s, v = name.split('_')[0], name.split('_')[1]
    return f'{SEASON[s[:-1]]} {s[-1]} · {VIEW.get(v, v)}'


def main():
    src, out = sys.argv[1], sys.argv[2]
    names = sorted(f[:-4] for f in os.listdir(src) if f.endswith('.png'))
    for s in SEASON:
        group = [n for n in names if n.startswith(s)]
        if not group:
            continue
        ims = [Image.open(os.path.join(src, n + '.png')).convert('RGB') for n in group]
        w, h = ims[0].size
        rows = (len(ims) + 1) // 2
        sheet = Image.new('RGB', (2 * w + 12, rows * (h + 12)), (16, 16, 16))
        for i, (n, im) in enumerate(zip(group, ims)):
            x, y = (i % 2) * (w + 12), (i // 2) * (h + 12)
            sheet.paste(im.resize((w, h)), (x, y))
            d = ImageDraw.Draw(sheet)
            d.rectangle([x, y, x + 470, y + 50], fill=(0, 0, 0))
            d.text((x + 12, y + 6), label(n), font=FONT, fill=(255, 230, 120))
        p = os.path.join(out, f'{s}.jpg')
        sheet.save(p, quality=90)
        print(p, len(group), '장', sheet.size)


if __name__ == '__main__':
    main()
