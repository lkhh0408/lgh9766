import sys, subprocess
S='/tmp/claude-0/-home-user-lgh9766/b52f1d6d-22f0-5bcd-a4bc-05ad7db7a50f/scratchpad'
sys.path.insert(0, S + '/vol02'); sys.path.insert(0, S + '/mobility')
import mob
ARGV = sys.argv[:]; sys.argv = sys.argv[:1]
import river_test as RT
mode, out = ARGV[1], ARGV[2]
fn, k, label = mob.MODES[mode]
RT.SPEED = 130 * k
L = RT.L
mob.O.clear(); mob.O.update(mob.OUTFITS[mode])
RT.ch.draw = lambda ctx, *a, **kw: fn(ctx, kw['t'], mob.OUTFITS[mode], L)
if mode in ('car', 'bus'): RT.dog = lambda *a, **kw: None
_ui = RT.R.ui
RT.R.ui = lambda im, title, col: _ui(im, f'TEST · {label}', col)
if out.endswith('.png'):
    RT.scene(float(ARGV[3])).save(out); sys.exit()
W, H, FPS = RT.W, RT.H, RT.FPS
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
for f in range(int(10 * FPS)): p.stdin.write(RT.scene(f / FPS).tobytes())
p.stdin.close(); p.wait(); print('done', out)
