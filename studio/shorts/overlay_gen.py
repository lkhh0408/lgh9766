import json
S='/tmp/claude-0/-home-user-lgh9766/b52f1d6d-22f0-5bcd-a4bc-05ad7db7a50f/scratchpad'
NM=f'file://{S}/chimg/node_modules/@fontsource'
cfg=json.load(open(f'{S}/shorts/shorts.json'))
def w(s): return sum(0.33 if c==' ' else (0.6 if c.isascii() else 0.92) for c in s)
for v,c in cfg.items():
    acc=c['acc']
    for it in c['items']:
        L=it['lines']; fs=int(min(130, 940/max(w(l) for l in L)))
        lines=''.join(f'<div style="margin-top:{14 if k else 0}px">'+(f'<span class=hl>{l}</span>' if k==2 else l)+'</div>' for k,l in enumerate(L))
        song=it['song']; sfs=40 if len(song)<22 else 32
        h=f'''<!doctype html><html><head><meta charset=utf-8><link rel=stylesheet href={NM}/outfit/800.css><link rel=stylesheet href={NM}/noto-sans-kr/900.css>
<style>html,body{{margin:0;background:transparent}}*{{box-sizing:border-box}}
.t{{position:relative;width:1080px;height:1920px;overflow:hidden;font-family:'Noto Sans KR';font-weight:900}}
.hl{{display:inline-block;background:{acc};color:#FFF6E0;padding:0 18px 10px 14px;transform:rotate(-2deg);box-shadow:8px 8px 0 #1F2340}}
</style></head><body><div class=t>
<div style="position:absolute;left:0;right:0;top:0;height:800px;background:linear-gradient(rgba(255,250,240,.93) 62%,rgba(255,250,240,0))"></div>
<div style="position:absolute;left:70px;top:150px;font-family:Outfit;font-weight:800;font-size:30px;letter-spacing:5px;color:#1F2340">🎧 OPEN TO CLOSE · PLAY LIST {c['num']}</div>
<div style="position:absolute;left:66px;top:212px;font-size:{fs}px;letter-spacing:-5px;line-height:1.05;color:#1F2340">{lines}</div>
<div style="position:absolute;left:70px;top:1330px;width:800px;display:flex;align-items:center;gap:18px;background:#1F2340;border-radius:24px;padding:22px 28px;box-shadow:0 12px 30px rgba(31,35,64,.3)">
 <div style="width:64px;height:64px;border-radius:50%;background:{acc};display:flex;align-items:center;justify-content:center;flex:none"><div style="width:0;height:0;border-left:22px solid #fff;border-top:14px solid transparent;border-bottom:14px solid transparent;margin-left:6px"></div></div>
 <div style="flex:1;min-width:0"><div style="display:flex;justify-content:space-between;font-family:Outfit;font-weight:800;font-size:20px;letter-spacing:3px;color:#FFD9A0"><span>NOW PLAYING</span><span>PLAY LIST {c['num']}</span></div>
 <div style="font-family:Outfit;font-weight:800;font-size:{sfs}px;color:#fff;margin-top:4px;white-space:nowrap">{song}</div>
 <div style="margin-top:10px;height:6px;border-radius:3px;background:rgba(255,255,255,.2)"><div style="width:40%;height:100%;border-radius:3px;background:linear-gradient(90deg,#FFB21A,{acc})"></div></div></div></div>
<div style="position:absolute;left:70px;top:1490px;background:#fff;border:4px solid #1F2340;border-radius:999px;padding:12px 30px;font-size:40px;color:#1F2340;letter-spacing:-1px">▶ 1시간 전체 듣기</div>
</div></body></html>'''
        open(f'{S}/shorts/ov_{it["id"]}.html','w').write(h)
