#!/usr/bin/env python3
"""Per-frame motion / light / style curves for the final film.
Streams 960x540 frames from ffmpeg (no big temp files), computes DIS optical
flow between consecutive frames, fits a similarity model (pan x/y, zoom,
rotation), and logs brightness / Lab colour / sharpness / motion-compensated
residual. Output: CSV, one row per frame pair (i-1 -> i)."""
import sys, subprocess, csv, math
import numpy as np
import cv2

cv2.setNumThreads(2)
src, out = sys.argv[1], sys.argv[2]
W, H = 960, 540
FW, FH = 480, 270  # flow resolution (half of analysis res), flow rescaled to 960 px units

cmd = ["ffmpeg", "-v", "error", "-threads", "2", "-i", src, "-vf",
       f"scale={W}:{H}:flags=area", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)

dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)

# grid for model fit (flow res), skip 6% borders
ys, xs = np.mgrid[0:FH:6, 0:FW:6]
m = (xs > FW * 0.06) & (xs < FW * 0.94) & (ys > FH * 0.06) & (ys < FH * 0.94)
xs, ys = xs[m].astype(np.float64), ys[m].astype(np.float64)
cx, cy = (FW - 1) / 2.0, (FH - 1) / 2.0
X, Y = (xs - cx), (ys - cy)
# similarity: u = tx + a*X - b*Y ; v = ty + b*X + a*Y
A = np.zeros((2 * len(X), 4))
A[0::2, 0] = 1; A[0::2, 2] = X; A[0::2, 3] = -Y
A[1::2, 1] = 1; A[1::2, 2] = Y; A[1::2, 3] = X
yi, xi = ys.astype(int), xs.astype(int)

fields = ["frame", "t", "pan_x_pctW", "pan_y_pctW", "speed_pctW", "dir_deg",
          "zoom_pct", "rot_deg", "fit_resid_pctW", "mag_med_pctW", "mag_p90_pctW",
          "L", "a", "b", "dL", "dE_mean", "absdiff", "mc_resid", "sharp", "dsharp_rel",
          "sat", "inlier_frac"]
f = open(out, "w", newline="")
wr = csv.writer(f); wr.writerow(fields)

prev_g = prev_small = None
prev_lab = prev_sharp = None
prev_bgr = None
i = -1
nbytes = W * H * 3
while True:
    buf = p.stdout.read(nbytes)
    if len(buf) < nbytes:
        break
    i += 1
    bgr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[..., 0].mean() * 100 / 255
    a = lab[..., 1].mean() - 128
    b = lab[..., 2].mean() - 128
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    sharp = float(cv2.Laplacian(g, cv2.CV_32F, ksize=3).var())
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    sat = float(hsv[..., 1].mean())
    small = cv2.resize(g, (FW, FH), interpolation=cv2.INTER_AREA)
    row = None
    if prev_small is not None:
        flow = dis.calc(prev_small, small, None)  # prev -> cur
        U = flow[yi, xi, 0].astype(np.float64); V = flow[yi, xi, 1].astype(np.float64)
        bvec = np.empty(2 * len(U)); bvec[0::2] = U; bvec[1::2] = V
        # robust: 2-pass trimmed LS
        sol = np.linalg.lstsq(A, bvec, rcond=None)[0]
        r = (A @ sol - bvec).reshape(-1, 2); rn = np.hypot(r[:, 0], r[:, 1])
        thr = max(np.percentile(rn, 70), 0.05)
        keep = np.repeat(rn <= thr, 2)
        sol = np.linalg.lstsq(A[keep], bvec[keep], rcond=None)[0]
        r = (A @ sol - bvec).reshape(-1, 2); rn = np.hypot(r[:, 0], r[:, 1])
        inl = float((rn <= max(thr, 0.3)).mean())
        tx, ty, aa, bb = sol
        s = FW / 100.0  # px per %W at flow res
        panx, pany = tx / s, ty / s
        speed = math.hypot(panx, pany)
        ddeg = math.degrees(math.atan2(-pany, panx))  # image-content motion direction (up positive)
        zoom = aa * 100.0  # % scale change per frame
        rot = math.degrees(bb)
        mag = np.hypot(U, V) / s
        # motion-compensated residual at 960 res
        fl = cv2.resize(flow, (W, H)) * (W / FW)
        gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
        # backward warp: cur(x) ~ prev(x - flow)? flow maps prev->cur; approximate cur->prev by -flow
        warped = cv2.remap(prev_g, gx - fl[..., 0], gy - fl[..., 1], cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_REPLICATE)
        bd = 24
        mc = float(np.abs(warped[bd:-bd, bd:-bd].astype(np.float32) - g[bd:-bd, bd:-bd].astype(np.float32)).mean())
        ad = float(np.abs(prev_g.astype(np.float32) - g.astype(np.float32)).mean())
        dE = math.sqrt((L - prev_lab[0]) ** 2 + (a - prev_lab[1]) ** 2 + (b - prev_lab[2]) ** 2)
        row = [i, round(i / 24.0, 4), round(panx, 4), round(pany, 4), round(speed, 4), round(ddeg, 1),
               round(zoom, 4), round(rot, 4), round(float(np.median(rn)) / s, 4),
               round(float(np.median(mag)), 4), round(float(np.percentile(mag, 90)), 4),
               round(L, 3), round(a, 3), round(b, 3), round(L - prev_lab[0], 3), round(dE, 3),
               round(ad, 3), round(mc, 3), round(sharp, 2), round(sharp / max(prev_sharp, 1e-6) - 1, 4),
               round(sat, 2), round(inl, 3)]
    else:
        row = [i, 0.0] + [""] * 9 + [round(L, 3), round(a, 3), round(b, 3)] + [""] * 4 + [round(sharp, 2), "", round(sat, 2), ""]
    wr.writerow(row)
    prev_small, prev_g, prev_lab, prev_sharp = small, g, (L, a, b), sharp
    if i % 200 == 0:
        print(i, flush=True)
f.close()
p.wait()
print("frames", i + 1)
