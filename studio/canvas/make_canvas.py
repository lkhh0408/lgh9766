"""Spotify Canvas: silent 8 s vertical loops (1080x1920) cut from the video scenes, no text or logos.
usage: python3 make_canvas.py CANVAS_JSON OUTDIR <render_video args...>
CANVAS_JSON: [{"id": "18", "i": 17, "a": 60.0, "shift": -330}, ...]  (i = track index from 0, a = seconds into the song)
Each clip renders a+[-0.5, 8) and crossfades its last 0.5 s into the first frames, so the 8 s loop has no jump."""
import sys, os, json, subprocess
SRC = '/home/user/lgh9766/studio/shorts/make_frames.py'
CFG, OUT = sys.argv[1], sys.argv[2]
L, X = 8.0, 0.5
sys.argv = ['studio/render_video.py'] + sys.argv[3:] + ['--stills', '0']
src = open('/home/user/lgh9766/studio/render_video.py').read()
inject = f'''
_CFG=json.load(open({CFG!r}))
WIN=[(int((starts[c['i']]+c['a']-{X})*FPS), int((starts[c['i']]+c['a']+{L})*FPS), c) for c in _CFG]
STILLS=set(); [STILLS.update(range(a,b)) for a,b,_ in WIN]
LAST=max(b for _,b,_ in WIN); _BUF={{}}
'''
src = src.replace("STILLS = {int(float(v) * FPS) for v in args.stills.split(',')} if args.stills else None", inject)
src = src.replace("    if STILLS is not None and fi not in STILLS:", "    if fi >= LAST: break\n    if STILLS is not None and fi not in STILLS:")
hook = '''    if True:
        _a,_b,_c=next(w for w in WIN if w[0]<=fi<w[1])
        _fr=img.crop((CX-304,0,CX+304,1080)).resize((1080,1920),Image.LANCZOS); _sh=_c.get('shift',0)
        if _sh: _n=Image.new('RGB',(1080,1920),__import__('collections').Counter(_fr.crop((0,1916,1080,1920) if _sh>0 else (0,0,1080,4)).getdata()).most_common(1)[0][0]); _n.paste(_fr,(0,-_sh)); _fr=_n
        _BUF.setdefault(_c['id'],[]).append(_fr.convert('RGB')); continue
    frame = img.convert('RGBA'); dark_ui'''
src = src.replace("    frame = img.convert('RGBA'); dark_ui", hook)
finish = f'''
import numpy as _np
_X=int({X}*FPS); _L=int({L}*FPS)
for _id,_frs in _BUF.items():
    _p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',{OUT!r}+'/canvas_'+_id+'.mp4'],stdin=subprocess.PIPE)
    for _k in range(_L):
        _f=_np.asarray(_frs[_X+_k],dtype=_np.float32)
        if _k>=_L-_X:
            _w=(_k-(_L-_X)+1)/(_X+1); _f=_f*(1-_w)+_np.asarray(_frs[_k-(_L-_X)],dtype=_np.float32)*_w
        _p.stdin.write(_f.clip(0,255).astype(_np.uint8).tobytes())
    _p.stdin.close(); _p.wait()
print('canvas done', list(_BUF))
'''
src = src.replace("if ff: ff.stdin.close(); ff.wait()", "if ff: ff.stdin.close(); ff.wait()" + finish.replace('\n', '\n'))
__file__ = '/home/user/lgh9766/studio/render_video.py'
exec(compile(src, __file__, 'exec'))
