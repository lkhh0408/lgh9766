import math, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sea2, mob
from sea2 import hx, lerp, shape, L, rrect
import character as ch
def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
OUTFIT = dict(top='#FF9F8A', bottom='#3E4A6B', shoe='#FFFFFF', phones='#FFD84A', phones_style='retro', helmet='#7ED6C4', helmet_stripe='#FFFFFF', detail='scarf', scarf='#2F3E6B')
FRAME = '#2F3E6B'   # navy bicycle
mob.O = OUTFIT

def bike_haru(c, t, ph, o, don, reach, press, sun, helmet_k):
    """mob.bike with extras: headphones don/reach, sunglasses (sun: 1 on the eyes, 0 pushed up on the helmet), helmet_k (0 off .. 1 on)"""
    pants, top = hx(o['bottom']), hx(o['top'])
    frame = hx(FRAME)
    rw, fw, cr = (-78, -42), (86, -42), (0, -40)
    ang = ph * 1.2
    mob.wheel(c, *rw, 40, ang, L); mob.wheel(c, *fw, 40, ang, L)
    sad, head_t, bar = (-22, -106), (56, -122), (46, -146)
    hip = (sad[0] + 2, sad[1] - 6)
    pb = (cr[0] + 18 * math.cos(ph + math.pi), cr[1] + 18 * math.sin(ph + math.pi))
    mob.leg_to(c, hip, pb, pants, L, True)
    c.set_line_width(7); c.set_source_rgb(*frame)
    mob.poly(c, [rw, cr, sad]); mob.poly(c, [rw, (sad[0] + 4, sad[1] + 8)]); mob.poly(c, [(sad[0] + 4, sad[1] + 8), head_t]); mob.poly(c, [cr, head_t]); mob.poly(c, [fw, head_t, bar])
    c.set_line_width(5); c.set_source_rgb(*L); mob.poly(c, [(bar[0] - 6, bar[1]), (bar[0] + 14, bar[1] - 4)])
    c.set_line_width(3); c.save(); c.translate(*sad); c.scale(1, .45); c.arc(0, 0, 18, 0, 2 * math.pi); c.restore(); shape(c, hx('#4A3F35'), L)
    c.arc(cr[0], cr[1], 11, 0, 2 * math.pi); shape(c, (.85, .87, .92), L)
    mob.cup(c, 82, -134, t, L, o)
    c.set_line_width(3); c.move_to(62, -140); c.line_to(104, -140); c.line_to(98, -112); c.line_to(68, -112); c.close_path(); shape(c, hx('#E3B778'), L)
    c.move_to(70, -128); c.line_to(98, -128); c.stroke()
    sh = (hip[0] + 6, hip[1] - 62)
    hxh, hyh = hip[0] + 18, hip[1] - 112
    # back hand: handlebar, or reaching for the headphone cup
    if reach > 0:
        _, _, _, _, _, cx_, cy_ = ch.phones_pose(hxh, hyh, 42, don)
        tgt = (bar[0] - 2 + (cx_ + 4 - bar[0] + 2) * reach, bar[1] + 2 + (cy_ + 4 - press * 2 - bar[1] - 2) * reach)
    else: tgt = (bar[0] - 2, bar[1] + 2)
    mob.arm_to(c, sh, tgt, top, L, True)
    c.save(); c.translate(hip[0], hip[1]); c.rotate(math.radians(10)); c.translate(-hip[0], -hip[1])
    mob.torso(c, hip, o, L, top)
    c.restore()
    pf = (cr[0] + 18 * math.cos(ph), cr[1] + 18 * math.sin(ph))
    mob.leg_to(c, hip, pf, pants, L, False)
    c.set_line_width(4); c.set_source_rgb(*L); mob.poly(c, [(cr[0] - 18 * math.cos(ph), cr[1] - 18 * math.sin(ph)), (pf[0], pf[1])])
    # head without helmet first, headphones at their ritual pose, then helmet dropping on
    o2 = dict(o); o2.pop('helmet', None)
    R = 42
    head_plain(c, hxh, hyh, t)
    ch._phones(c, 'retro', hxh, hyh, R, hx(o['phones']), L, don)
    gx, gy2 = hxh + 24, hyh + 4
    if sun > 0.001:   # round sunglasses over the round glasses, sliding up onto the helmet
        oy = -58 * (1 - sun)
        c.save(); c.translate(0, oy)
        c.arc(gx, gy2, 15, 0, 2 * math.pi); c.set_source_rgba(.13, .12, .2, .9); c.fill_preserve(); c.set_source_rgb(*L); c.set_line_width(4); c.stroke()
        c.set_line_width(4); c.move_to(gx - 15, gy2 - 2); c.line_to(hxh - 16, gy2 - 4); c.stroke()
        c.set_source_rgba(1, 1, 1, .8); c.set_line_width(3); c.arc(gx - 4, gy2 - 5, 6, math.pi * 1.1, math.pi * 1.6); c.stroke()
        c.restore()
    if helmet_k > 0.001:
        c.save(); c.translate(0, -70 * (1 - helmet_k)); mob.helmet(c, hxh, hyh, R, o, L); c.restore()
    if sun <= 0.001:   # sunglasses resting on top of the helmet (after the red light)
        c.save(); c.translate(hxh + 4, hyh - R - 22); c.rotate(-.1)
        c.arc(0, 0, 11, math.pi, 2 * math.pi); c.close_path(); c.set_source_rgba(.13, .12, .2, .95); c.fill_preserve(); c.set_source_rgb(*L); c.set_line_width(3); c.stroke()
        c.restore()
    mob.arm_to(c, sh, (bar[0] + 4, bar[1]), top, L, False)

def head_plain(c, hx_, hy_, t):
    R = 42; SKIN, HAIR = ch.SKIN, ch.HAIR
    c.set_line_width(4); c.arc(hx_, hy_, R, 0, 2 * math.pi); shape(c, SKIN, L)
    c.save(); c.arc(hx_, hy_, R + 1, 0, 2 * math.pi); c.clip()
    c.move_to(hx_ + R + 4, hy_ - 12); c.curve_to(hx_ + 20, hy_ - 22, hx_ - 6, hy_ - 16, hx_ - 12, hy_ - 4)
    c.line_to(hx_ - 14, hy_ + 30); c.line_to(hx_ - R - 6, hy_ + 30); c.line_to(hx_ - R - 6, hy_ - R - 6); c.line_to(hx_ + R + 6, hy_ - R - 6); c.close_path()
    c.set_source_rgb(*HAIR); c.fill(); c.restore()
    c.set_source_rgb(*L); c.set_line_width(4); c.arc(hx_, hy_, R, 0, 2 * math.pi); c.stroke()
    gx, gy2 = hx_ + 24, hy_ + 4
    c.set_line_width(4); c.move_to(gx - 14, gy2 - 2); c.line_to(hx_ - 16, gy2 - 4); c.stroke()
    c.arc(gx, gy2, 14, 0, 2 * math.pi); c.set_source_rgba(1, 1, 1, .45); c.fill_preserve(); c.set_source_rgb(*L); c.stroke()
    if (t % 4.0) < 0.12: c.move_to(gx - 2, gy2 + 1); c.line_to(gx + 6, gy2 + 1); c.stroke()
    else: c.arc(gx + 2, gy2 + 1, 3.6, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(1, .45, .55, .45); c.arc(gx + 4, gy2 + 22, 7, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*L); c.set_line_width(3); c.arc(hx_ + 30, hy_ + 26, 6, math.radians(10), math.radians(120)); c.stroke()

def bubble(c, x, y, a):
    if a < .02: return
    c.save(); c.translate(x, y); c.push_group(); rrect(c, -44, -32, 88, 64, 18); shape(c, (1, 1, 1), L)
    c.move_to(-12, -16); c.line_to(18, 0); c.line_to(-12, 16); c.close_path(); c.set_source_rgb(*hx('#FF2D87')); c.fill()
    c.pop_group_to_source(); c.paint_with_alpha(a); c.restore()

