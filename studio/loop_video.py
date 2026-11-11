"""Repeat a finished video N times back to back (no re-rendering, so picture and sound stay identical).

    python studio/loop_video.py vol01.mp4 -n 3 -o vol01_3h.mp4
"""
import argparse, os, subprocess, tempfile

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('video'); ap.add_argument('-n', '--times', type=int, default=2, help='how many times to play it')
ap.add_argument('-o', '--out', required=True)
args = ap.parse_args()

with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
    for _ in range(args.times): f.write("file '%s'\n" % os.path.abspath(args.video).replace("'", r"'\''"))
    lst = f.name
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                '-c', 'copy', '-movflags', '+faststart', args.out], check=True)
os.remove(lst)
print('done:', args.out)
