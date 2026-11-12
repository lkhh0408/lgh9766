S='/tmp/claude-0/-home-user-lgh9766/b52f1d6d-22f0-5bcd-a4bc-05ad7db7a50f/scratchpad'
NM=f'file://{S}/chimg/node_modules/@fontsource'
def page(bg, stk, num, l1, l2, acc, acc_txt, song, style):
    def w(s): return sum(0.36 if c==' ' else (0.62 if c.isascii() else 0.93) for c in s)
    fs=int(min(150, 600/max(w(l1),w(l2))))
    y1=118; y2=y1+fs+28
    if style=='box':
        L2=f'<span class=hl style="background:{acc};color:{acc_txt};box-shadow:8px 8px 0 #1F2340">{l2}</span>'
        L1=f'<span style="color:#1F2340">{l1}</span>'
    elif style=='color':
        L1=f'<span style="color:#1F2340">{l1}</span>'; L2=f'<span style="color:{acc}">{l2}</span>'
    else: # under: underline marker
        L1=f'<span style="color:#1F2340">{l1}</span>'
        L2=f'<span style="color:#1F2340;background:linear-gradient(transparent 62%,{acc}88 62%)">{l2}</span>'
    return f'''<!doctype html><html><head><meta charset=utf-8>
<link rel=stylesheet href={NM}/outfit/800.css><link rel=stylesheet href={NM}/noto-sans-kr/900.css><link rel=stylesheet href={NM}/noto-sans-kr/700.css>
<style>html,body{{margin:0}}*{{box-sizing:border-box}}
.t{{position:relative;width:1280px;height:720px;overflow:hidden;font-family:'Noto Sans KR';font-weight:900}}
.kr{{letter-spacing:-6px;line-height:1;position:absolute;white-space:nowrap}}
.hl{{display:inline-block;padding:0 18px 10px 12px;transform:rotate(-2deg)}}
</style></head><body><div class=t>
<div style="position:absolute;inset:0;background:url(file://{bg}) center/cover"></div>
<div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(255,250,240,.96) 0,rgba(255,250,240,.9) 48%,rgba(255,250,240,0) 66%)"></div>
<div style="position:absolute;left:62px;top:48px;display:flex;align-items:center;gap:12px;font-family:Outfit;font-weight:800;font-size:30px;letter-spacing:5px;color:#1F2340">🎧 PLAY LIST <span style="background:{acc};color:{acc_txt};padding:2px 14px;border-radius:10px;letter-spacing:2px">{num}</span></div>
<div class=kr style="left:58px;top:{y1}px;font-size:{fs}px">{L1}</div>
<div class=kr style="left:62px;top:{y2}px;font-size:{fs}px">{L2}</div>
<div style="position:absolute;left:62px;top:572px;width:600px;height:96px;background:#1F2340;border-radius:20px;box-shadow:0 10px 26px rgba(31,35,64,.3);display:flex;align-items:center;gap:20px;padding:0 26px">
 <div style="width:56px;height:56px;border-radius:50%;background:{acc};display:flex;align-items:center;justify-content:center;flex:none"><div style="width:0;height:0;border-left:20px solid #fff;border-top:12px solid transparent;border-bottom:12px solid transparent;margin-left:5px"></div></div>
 <div style="flex:1;min-width:0"><div style="display:flex;justify-content:space-between;font-family:Outfit;font-weight:800;font-size:16px;letter-spacing:3px;color:#FFD9A0"><span>NOW PLAYING</span><span>TRACK 01 / 20</span></div>
 <div style="font-family:Outfit;font-weight:800;font-size:28px;color:#fff;margin-top:2px;white-space:nowrap">{song}</div>
 <div style="margin-top:8px;height:5px;border-radius:3px;background:rgba(255,255,255,.2);position:relative"><div style="width:34%;height:100%;border-radius:3px;background:linear-gradient(90deg,#FFB21A,{acc})"></div><div style="position:absolute;left:34%;top:-5px;width:15px;height:15px;margin-left:-7px;border-radius:50%;background:#fff"></div></div></div></div>
<img src="file://{stk}" style="position:absolute;right:-60px;top:20px;height:1000px"></div></body></html>'''
P1=dict(bg=f'{S}/pl01bg/thumb_bg.png',stk=f'{S}/vid/sticker_vol01.png',num='01',acc='#E0457B',acc_txt='#FFF6E0',song='Good Side of the Street')
P2=dict(bg=f'{S}/vol02/thumb_bg.png',stk=f'{S}/vid/sticker_vol02.png',num='02',acc='#2F5BEA',acc_txt='#FFF6E0',song='I Like Your Quiet')
D={'a':[(P1,'첫 곡부터','기분 맑음','box'),(P1,'듣자마자','창문 엶','box'),(P1,'커피가','더 맛있어짐','color'),(P1,'이어폰','빼기 싫어짐','box'),(P1,'1번 곡부터','반복 재생','under')],
   'b':[(P2,'발걸음이','박자 탐','box'),(P2,'볼륨','한 칸 더','box'),(P2,'한쪽만 끼려다','양쪽 다 낌','color'),(P2,'1번 트랙에서','바로 저장함','box'),(P2,'고개가','먼저 끄덕임','under')]}
for k,lst in D.items():
    for i,(p,l1,l2,st) in enumerate(lst,1):
        open(f'{S}/thumbs3/{k}{i}.html','w').write(page(p['bg'],p['stk'],p['num'],l1,l2,p['acc'],p['acc_txt'],p['song'],st))
