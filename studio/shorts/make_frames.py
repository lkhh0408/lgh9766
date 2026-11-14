# usage: python3 make_frames.py VOL <render_video args...>
import sys, os, json, subprocess
S='/tmp/claude-0/-home-user-lgh9766/b52f1d6d-22f0-5bcd-a4bc-05ad7db7a50f/scratchpad'
VOL=sys.argv[1]
sys.argv=['studio/render_video.py']+sys.argv[2:]+['--stills','0']
src=open('/home/user/lgh9766/studio/render_video.py').read()
inject='''
_CFG=json.load(open(S+'/shorts/shorts.json'))[VOL]['items']
WIN=[(int((starts[it['i']]+it['a'])*FPS), int((starts[it['i']]+it['b'])*FPS), it) for it in _CFG]
STILLS=set(); [STILLS.update(range(a,b)) for a,b,_ in WIN]
LAST=max(b for _,b,_ in WIN)
json.dump({it['id']:[starts[it['i']]+it['a'], starts[it['i']]+it['b']] for _,_,it in WIN}, open(S+'/shorts/out/win_'+VOL+'.json','w'))
_OV={it['id']:Image.open(S+'/shorts/ov_'+it['id']+'.png').convert('RGBA') for it in _CFG}
_PIPE={}
'''
src=src.replace("STILLS = {int(float(v) * FPS) for v in args.stills.split(',')} if args.stills else None", inject)
src=src.replace("    if STILLS is not None and fi not in STILLS:","    if fi >= LAST: break\n    if STILLS is not None and fi not in STILLS:")
hook='''    if True:
        _a,_b,_it=next(w for w in WIN if w[0]<=fi<w[1]); _id=_it['id']
        if _id not in _PIPE:
            _PIPE[_id]=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p',S+'/shorts/out/v_'+_id+'.mp4'],stdin=subprocess.PIPE)
        _fr=img.crop((CX-304,0,CX+304,1080)).resize((1080,1920),Image.LANCZOS).convert('RGBA'); _fr.alpha_composite(_OV[_id])
        _k = 1080 / 608; _d = ImageDraw.Draw(_fr); _ft = ImageFont.truetype(os.path.join(ASSETS, 'fonts', 'Outfit-800.ttf'), int(30 * _k))
        _tw = _d.textlength('HARU', font=_ft); _cx, _cy = 310 * _k, (484 - 4 * abs(math.cos(phase)) * walk) * _k
        _d.rounded_rectangle((_cx - _tw / 2 - 16 * _k, _cy - 22 * _k, _cx + _tw / 2 + 16 * _k, _cy + 22 * _k), int(22 * _k), fill=(255, 255, 255, 255), outline=(43, 37, 65, 255), width=int(3 * _k))
        _d.text((_cx - _tw / 2, _cy - 19 * _k), 'HARU', font=_ft, fill=(43, 37, 65, 255))
        _PIPE[_id].stdin.write(_fr.convert('RGB').tobytes()); continue
    frame = img.convert('RGBA'); dark_ui'''
src=src.replace("    frame = img.convert('RGBA'); dark_ui",hook)
src=src.replace("if ff: ff.stdin.close(); ff.wait()","for _p in _PIPE.values(): _p.stdin.close(); _p.wait()\nif ff: ff.stdin.close(); ff.wait()")
__file__='/home/user/lgh9766/studio/render_video.py'
exec(compile(src,__file__,'exec'))
