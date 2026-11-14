"""PLAY LIST 03 draft: Haru on a bicycle along a seaside road. Outfit options + day/sunset/night."""
import math, random, sys
import cairo
sys.path.insert(0, '/home/user/lgh9766/studio'); sys.path.insert(0, '/home/user/lgh9766/studio/mobility')
import mob
W, H = 1920, 1080
hx, lerp, shape = mob.hexc, mob.lerp, mob._shape
L = hx('#2B2541')
GY = 860   # road line

SKIES = {'day': ('#7EC8FF', '#E3F4FF', '#4FB3E8', '#9EDCF5'),
         'dusk': ('#6E6AC8', '#FFB38A', '#5E7FC8', '#F2A58C'),
         'night': ('#141A3A', '#3B3168', '#1E2A55', '#334477')}

def scene(c, mode, scroll=0.0, t=1.0):
    st, sb, sea_far, sea_near = (hx(v) for v in SKIES[mode])
    night = mode == 'night'
    g = cairo.LinearGradient(0, 0, 0, 640); g.add_color_stop_rgb(0, *st); g.add_color_stop_rgb(1, *sb); c.rectangle(0, 0, W, 640); c.set_source(g); c.fill()
    r = random.Random(2)
    if night:
        for _ in range(140): c.arc(r.uniform(0, W), r.uniform(0, 480), r.uniform(1, 2.4), 0, 6.3); c.set_source_rgba(1, 1, 1, r.uniform(.4, 1)); c.fill()
        c.arc(1500, 170, 46, 0, 6.3); c.set_source_rgb(1, .97, .85); c.fill()
    elif mode == 'dusk':
        c.arc(1250, 600, 90, math.pi, 2 * math.pi); c.set_source_rgb(1, .78, .45); c.fill()
    else:
        c.arc(1560, 150, 60, 0, 6.3); c.set_source_rgb(1, .93, .6); c.fill()
    if not night:
        for cx, cy, s in ((260, 180, 1), (900, 120, .8), (1400, 260, .7)):
            for dx, dy, rr in ((0, 0, 34), (40, -14, 42), (82, 0, 30)): c.arc(cx + dx * s, cy + dy * s, rr * s, 0, 6.3)
            shape(c, (1, 1, 1) if mode == 'day' else hx('#FFD9C7'), L)
    # sea
    g = cairo.LinearGradient(0, 600, 0, 780); g.add_color_stop_rgb(0, *sea_far); g.add_color_stop_rgb(1, *sea_near); c.rectangle(0, 600, W, 180); c.set_source(g); c.fill()
    if mode == 'dusk':   # sun path on the water
        for k in range(7): c.rectangle(1190 + k * 6 - 20, 612 + k * 22, 120 - k * 12, 6); c.set_source_rgba(1, .85, .55, .8); c.fill()
    if night:
        for k in range(6): c.rectangle(1460 + (k % 2) * 10, 620 + k * 24, 80 - k * 8, 5); c.set_source_rgba(1, .97, .8, .6); c.fill()
    c.set_line_width(3); c.set_source_rgba(1, 1, 1, .7)
    for k in range(26):
        wx = (k * 157 - scroll * .3) % (W + 200) - 100; wy = 640 + (k * 37) % 120
        c.move_to(wx, wy); c.curve_to(wx + 12, wy - 8, wx + 24, wy - 8, wx + 36, wy); c.stroke()
    # far island + lighthouse
    c.move_to(80, 610); c.curve_to(200, 540, 380, 545, 480, 610); c.close_path(); shape(c, lerp(hx('#8FBF9A'), hx('#2E3B55'), .7 if night else 0), L)
    lx = 330
    c.move_to(lx - 22, 600); c.line_to(lx - 14, 470); c.line_to(lx + 14, 470); c.line_to(lx + 22, 600); c.close_path(); shape(c, (1, 1, 1), L)
    for k in range(3): c.rectangle(lx - 18 + k * 2, 500 + k * 32, 36 - k * 4, 14); c.set_source_rgb(*hx('#FF6B5B')); c.fill()
    c.rectangle(lx - 18, 448, 36, 22); shape(c, hx('#FFE27A') if night else hx('#DDF1FF'), L)
    c.move_to(lx - 22, 448); c.line_to(lx, 430); c.line_to(lx + 22, 448); c.close_path(); shape(c, hx('#FF6B5B'), L)
    if night:
        c.move_to(lx, 459); c.line_to(lx + 520, 400); c.line_to(lx + 520, 520); c.close_path(); c.set_source_rgba(1, .95, .6, .18); c.fill()
    # sailboat
    bx = 1000 - scroll * .1
    c.move_to(bx - 40, 680); c.line_to(bx + 40, 680); c.line_to(bx + 28, 696); c.line_to(bx - 28, 696); c.close_path(); shape(c, (1, 1, 1), L)
    c.move_to(bx, 676); c.line_to(bx, 610); c.line_to(bx + 34, 670); c.close_path(); shape(c, hx('#FFC857'), L)
    # beach strip
    c.move_to(0, 780); c.curve_to(500, 770, 1300, 790, W, 776); c.line_to(W, 800); c.line_to(0, 800); c.close_path(); shape(c, lerp(hx('#F7E2B5'), hx('#4A4766'), .6 if night else 0), L)
    # beach parasols + seaside cafe (scrolling)
    for k in range(4):
        px = (k * 620 + 120 - scroll) % (W + 600) - 300
        if k % 2 == 0:
            c.set_line_width(4); c.set_source_rgb(*L); c.move_to(px, 790); c.line_to(px, 712); c.stroke()
            c.move_to(px - 60, 724); c.curve_to(px - 50, 680, px + 50, 680, px + 60, 724); c.close_path(); shape(c, hx(['#FF7A6B', '#7ED6C4'][k // 2 % 2]), L)
        else:
            c.rectangle(px - 90, 700, 180, 96); shape(c, hx('#FFF3D6') if not night else hx('#FFE9A8'), L)
            c.move_to(px - 104, 700); c.line_to(px + 104, 700); c.line_to(px + 90, 670); c.line_to(px - 90, 670); c.close_path(); shape(c, hx('#2F5BEA'), L)
            for j in range(6): c.rectangle(px - 90 + j * 30, 700, 15, 14); c.set_source_rgb(1, 1, 1); c.fill()
            c.select_font_face('Outfit', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(22); c.set_source_rgb(*L); c.move_to(px - 62, 760); c.show_text('SEA CAFE')
    # guardrail + road
    c.rectangle(0, 800, W, 60); c.set_source_rgb(*lerp(hx('#CFE8F2'), hx('#3D4A5E'), .8 if night else 0)); c.fill()
    c.set_line_width(5); c.set_source_rgb(*L); c.move_to(0, 810); c.line_to(W, 810); c.stroke()
    c.set_source_rgb(*hx('#FFFFFF') if not night else hx('#AAB0C8')); c.set_line_width(8); c.move_to(0, 822); c.line_to(W, 822); c.stroke()
    for k in range(30):
        px = (k * 80 - scroll) % (W + 80) - 40; c.set_line_width(4); c.set_source_rgb(*L); c.move_to(px, 810); c.line_to(px, 860); c.stroke()
    c.rectangle(0, GY, W, H - GY); shape(c, lerp(hx('#C9C6D6'), hx('#4E4C66'), .8 if night else 0), L)
    c.set_line_width(6); c.set_source_rgba(1, 1, 1, .8)
    for k in range(12):
        px = (k * 220 - scroll * 1.2) % (W + 220) - 110; c.move_to(px, 950); c.line_to(px + 100, 950); c.stroke()
    # street lamps at night
    for k in range(3):
        px = (k * 760 + 400 - scroll) % (W + 400) - 200
        c.set_line_width(5); c.set_source_rgb(*L); c.move_to(px, 860); c.line_to(px, 690); c.curve_to(px, 670, px + 20, 664, px + 36, 668); c.stroke()
        c.arc(px + 40, 676, 12, 0, 6.3); shape(c, hx('#FFE27A') if night else hx('#F2F2F2'), L)
        if night: c.arc(px + 40, 690, 70, 0, 6.3); c.set_source_rgba(1, .9, .5, .18); c.fill()
    # seagulls
    if not night:
        c.set_line_width(3); c.set_source_rgb(*L)
        for bx2, by2 in ((600, 300), (660, 330), (1100, 240)):
            c.move_to(bx2 - 14, by2); c.curve_to(bx2 - 6, by2 - 10, bx2, by2 - 4, bx2, by2); c.curve_to(bx2, by2 - 4, bx2 + 6, by2 - 10, bx2 + 14, by2); c.stroke()

def haru_bike(c, x, o, t=1.0, s=1.0):
    mob.O = o
    c.save(); c.translate(x, GY); c.scale(s, s); mob.bike(c, t, o, L); c.restore()

def surf(fn):
    sf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(sf)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND); fn(c); return sf

BASE = dict(bottom='#3E4A6B', shoe='#FFFFFF', phones_style='retro')
OPTS = [
    ('1. 코랄 니트 + 네이비 머플러', '레몬 헤드폰 · 민트 안전모', dict(BASE, top='#FF9F8A', phones='#FFD84A', helmet='#7ED6C4', helmet_stripe='#FFFFFF', detail='scarf', scarf='#2F3E6B')),
    ('2. 라벤더 바람막이', '오렌지 헤드폰 · 화이트 안전모 · 크로스백', dict(BASE, top='#B9A4FF', phones='#FF8A3D', helmet='#FFFFFF', helmet_stripe='#B9A4FF', detail='reflect', bag='crossbody', bag_color='#FFD84A', strap='#2B2541')),
    ('3. 그린 가디건 + 머스터드 머플러', '크림 헤드폰 · 버터 안전모', dict(BASE, top='#3F8F6B', bottom='#F3E9D2', phones='#F3E9D2', helmet='#FFD84A', helmet_stripe='#3F8F6B', detail='scarf', scarf='#E9A23B')),
]
if __name__ == '__main__':
    OUT = sys.argv[1]
    outfit_panels = [surf(lambda c, o=o: (c.translate(960 - 900 * 2.0, 560 - 740 * 2.0), c.scale(2.0, 2.0), scene(c, 'day', 300), haru_bike(c, 900, o, s=1.15))) for _, _, o in OPTS]
    time_panels = [surf(lambda c, m=m: (scene(c, m, 900 + i * 400), haru_bike(c, 900, OPTS[0][2], t=1.4 + i, s=1.15))) for i, m in enumerate(('day', 'dusk', 'night'))]
    for i, p in enumerate(outfit_panels + time_panels): p.write_to_png(OUT.replace('.png', f'_{i}.png'))
    sw, sh, pad = 620, 349, 30
    sheet = cairo.ImageSurface(cairo.FORMAT_RGB24, pad * 4 + sw * 3, 1060); c = cairo.Context(sheet)
    c.set_source_rgb(*hx('#FAF8F2')); c.paint()
    c.select_font_face('NanumSquareRound', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    c.set_font_size(34); c.set_source_rgb(*L); c.move_to(pad, 56); c.show_text('PLAY LIST 03 시안 · 바닷가 자전거')
    c.set_font_size(24); c.move_to(pad, 104); c.show_text('의상 3가지 (가까이 보기)')
    for i, ((a, b, _), p) in enumerate(zip(OPTS, outfit_panels)):
        x = pad + i * (sw + pad); y = 120
        c.save(); c.translate(x, y); c.scale(sw / W, sh / H); c.set_source_surface(p, 0, 0); c.paint(); c.restore()
        c.set_font_size(22); c.set_source_rgb(*L); c.move_to(x, y + sh + 32); c.show_text(a)
        c.set_font_size(18); c.set_source_rgb(.4, .4, .5); c.move_to(x, y + sh + 60); c.show_text(b)
    c.set_font_size(24); c.set_source_rgb(*L); c.move_to(pad, 600); c.show_text('배경: 해안도로의 낮 → 노을 → 밤 (의상 1 기준)')
    for i, (lab, p) in enumerate(zip(('낮: 바다, 파라솔, 해변 카페, 갈매기', '노을: 바다 위 해 길', '밤: 등대 불빛, 가로등'), time_panels)):
        x = pad + i * (sw + pad); y = 616
        c.save(); c.translate(x, y); c.scale(sw / W, sh / H); c.set_source_surface(p, 0, 0); c.paint(); c.restore()
        c.set_font_size(20); c.set_source_rgb(*L); c.move_to(x, y + sh + 32); c.show_text(lab)
    sheet.write_to_png(OUT)
