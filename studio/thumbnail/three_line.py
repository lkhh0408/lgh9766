S='/tmp/claude-0/-home-user-lgh9766/b52f1d6d-22f0-5bcd-a4bc-05ad7db7a50f/scratchpad'
exec(open(f'{S}/thumbs3/gen.py').read().split("D={")[0])
def page3(p, lines, hi):
    def w(s): return sum(0.33 if c==' ' else (0.6 if c.isascii() else 0.92) for c in s)
    top, bottom, gap = 104, 552, 14
    fs = int(min(170, 610/max(w(l) for l in lines), (bottom-top-gap*(len(lines)-1))/len(lines)/1.04))
    used = len(lines)*fs*1.04+gap*(len(lines)-1); y = top + (bottom-top-used)/2
    body=''
    for i,l in enumerate(lines):
        if i==hi: t=f'<span class=hl style="background:{p["acc"]};color:#FFF6E0;box-shadow:8px 8px 0 #1F2340">{l}</span>'
        else: t=f'<span style="color:#1F2340">{l}</span>'
        body+=f'<div class=kr style="left:{58 if i!=hi else 62}px;top:{y:.0f}px;font-size:{fs}px">{t}</div>'
        y+=fs*1.04+gap
    h=page(p['bg'],p['stk'],p['num'],'X','Y',p['acc'],p['acc_txt'],p['song'],'box')
    a=h.index('<div class=kr'); b=h.index('<div style="position:absolute;left:62px;top:572px')
    return h[:a]+body+h[b:]
D=[('a1',P1,['듣자마자','커피가','더 맛있어짐'],2),('a2',P1,['한 곡만','들으려다','20곡 다 들음'],2),
   ('a3',P1,['평범한','출근길이','영화 됨'],2),('a4',P1,['커피 식는 줄','모르고','듣게 됨'],1),
   ('b1',P2,['들으면','발걸음이','박자 탐'],2),('b2',P2,['내 산책이','뮤직비디오','됨'],1),
   ('b3',P2,['한 정거장','더 걷게','되는 노래'],1),('b4',P2,['걷다가','나도 모르게','리듬 탐'],2)]
for n,p,l,hi in D: open(f'{n}.html','w').write(page3(p,l,hi))
