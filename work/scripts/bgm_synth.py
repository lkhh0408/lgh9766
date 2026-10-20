"""영상용 배경음악(BGM)을 직접 합성한다. 무료(로컬 계산만 함), 외부 음원·샘플 없음(저작권 문제 없음).

곡: D장조, 72BPM, 화음 하나가 8박(약 6.67초). 패드(현악 느낌) + 베이스 + 피아노(분산화음·선율) + 종소리 + 새벽 반짝임.
영상 구간(새벽 → 낮 → 노을 → 해진 뒤 불빛 → 밤)에 맞춰 세기와 악기 구성이 바뀐다.

사용: python3 work/scripts/bgm_synth.py <출력.wav> [--seconds 97.5]
결과: 48kHz 스테레오 16비트 WAV(최고 -1dBFS로 맞춤). 음량 맞춤(loudnorm)과 영상 합치기는 ffmpeg로 따로 한다.
"""
import argparse
import wave

import numpy as np

SR = 48000
BPM = 72
BEAT = 60 / BPM
CHORD = 8 * BEAT  # 약 6.667초

# (패드 음들, 베이스) MIDI 번호. D장조
CHORDS = [
    ([57, 61, 64, 66, 69], 38),  # Dmaj9
    ([54, 57, 61, 62, 66], 47),  # Bm9
    ([54, 57, 59, 62, 66], 43),  # Gmaj9
    ([52, 57, 59, 64, 69], 45),  # Asus2
    ([57, 61, 62, 66, 69], 42),  # D/F#
    ([54, 59, 62, 66, 67], 43),  # Gmaj7
    ([54, 59, 62, 64, 66], 40),  # Em9
    ([52, 55, 57, 62, 64], 45),  # A7sus4
    ([57, 61, 64, 66, 69], 38),  # Dmaj9
    ([54, 57, 61, 64, 66], 42),  # F#m7
    ([54, 57, 59, 62, 66], 43),  # Gmaj9
    ([54, 57, 61, 62, 66], 47),  # Bm9 (노을)
    ([55, 59, 61, 62, 66], 43),  # Gmaj7#11 (해 질 녘)
    ([54, 59, 62, 64, 66], 40),  # Em9 (해진 뒤)
    ([57, 61, 64, 66, 69], 38),  # Dmaj9 (밤, 마무리)
]

# 영상 구간별 세기(0~1). (시각, 값) 사이를 부드럽게 잇는다
INTENSITY = [(0, 0.3), (16, 0.55), (42.5, 0.8), (50, 1.0), (60.4, 0.9), (75, 0.9), (84, 0.7), (92, 0.45), (97.5, 0.3)]


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def curve(points, t):
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)


def table(power, n_harm=16, size=4096):
    ph = np.arange(size) / size
    w = sum(np.sin(2 * np.pi * k * ph) / k ** power for k in range(1, n_harm + 1))
    return w / np.abs(w).max()


WARM, BRIGHT = table(2.0), table(1.1, n_harm=24)


def pad_note(f0, dur, bright, rng):
    """세 겹(±6센트)의 파형표 합성, 느린 떨림, 밝기는 두 파형표를 섞어 조절."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for k, cents in enumerate((-6, 0, 6)):
        f = f0 * 2 ** (cents / 1200) * (1 + 0.0015 * np.sin(2 * np.pi * (0.18 + 0.05 * k) * t + rng.uniform(0, 6.28)))
        ph = np.cumsum(f) / SR + rng.uniform(0, 1)
        idx = (ph * 4096).astype(np.int64) % 4096
        s = WARM[idx] * (1 - bright) + BRIGHT[idx] * bright
        pan = (-0.5, 0.0, 0.5)[k]
        out[:, 0] += s * np.sqrt((1 - pan) / 2)
        out[:, 1] += s * np.sqrt((1 + pan) / 2)
    return out / 3


def env_adsr(n, attack, release):
    e = np.ones(n)
    a = min(int(attack * SR), n)
    r = min(int(release * SR), n - a)
    e[:a] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    if r > 0:
        e[n - r:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, r))
    return e


def piano_note(m, vel, dur=3.5):
    """약간 어긋난 배음(현의 비조화성)과 높은 배음이 빨리 사라지는 감쇠로 만든 피아노 비슷한 소리."""
    f0 = midi_hz(m)
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 15):
        fk = k * f0 * np.sqrt(1 + 0.0004 * k * k)
        if fk > 16000:
            break
        s += np.sin(2 * np.pi * fk * t) * (1 / k ** 1.15) * np.exp(-t * (0.8 + 0.3 * k))
    att = np.minimum(t / 0.006, 1)
    rel = env_adsr(n, 0, 0.3)
    return s * att * rel * vel * 0.35


def bell_note(m, vel, dur=3.0):
    f0 = midi_hz(m)
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for ratio, amp, dec in ((1, 1, 1.2), (2.76, 0.45, 2.2), (5.40, 0.22, 3.5), (8.93, 0.1, 5.0)):
        s += amp * np.sin(2 * np.pi * f0 * ratio * t) * np.exp(-t * dec)
    return s * np.minimum(t / 0.003, 1) * env_adsr(n, 0, 0.2) * vel * 0.18


def add(buf, start, sig, pan=0.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    if sig.ndim == 1:
        sig = np.stack([sig * np.sqrt((1 - pan) / 2), sig * np.sqrt((1 + pan) / 2)], 1)
    if i < 0:  # 사람 손 같은 박자 흔들림으로 0초보다 조금 앞서면 앞을 잘라냄
        sig, i = sig[-i:], 0
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def reverb(x, seconds=3.2, seed=7):
    """지수 감쇠 잡음으로 만든 스테레오 잔향(좌우 다른 잡음). FFT 합성곱."""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 6.9 / seconds)
        k = 5  # 아주 높은 고역만 조금 줄임(부드러운 잔향)
        ir = np.convolve(ir, np.ones(k) / k, mode='same')
        ir[: int(0.02 * SR)] = 0  # 20ms 앞 지연
        ir /= np.sqrt((ir ** 2).sum())
        size = 1 << int(np.ceil(np.log2(len(x) + n)))
        y = np.fft.irfft(np.fft.rfft(x[:, ch], size) * np.fft.rfft(ir, size), size)[: len(x)]
        out[:, ch] = y
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--seconds', type=float, default=97.5)
    a = ap.parse_args()
    total = a.seconds
    rng = np.random.default_rng(83)
    n = int(total * SR)
    pad = np.zeros((n, 2))
    bass = np.zeros((n, 2))
    keys = np.zeros((n, 2))
    bells = np.zeros((n, 2))

    for ci, (notes, root) in enumerate(CHORDS):
        start = ci * CHORD
        if start >= total:
            break
        dur = CHORD + 3.0  # 다음 화음과 3초 겹쳐 부드럽게 넘어감
        inten = float(curve(INTENSITY, start + CHORD / 2))
        bright = 0.25 + 0.5 * inten
        for m in notes:
            s = pad_note(midi_hz(m), dur, bright, rng)
            s *= env_adsr(len(s), 2.8, 3.2)[:, None]
            add(pad, start, s * 0.11)
        # 공기층: 한 옥타브 위 밝은 패드를 아주 작게(곡 전체)
        for m in notes[1::2]:
            s = pad_note(midi_hz(m + 12), dur, 0.9, rng)
            s *= env_adsr(len(s), 3.0, 3.2)[:, None]
            add(pad, start, s * 0.03)
        # 새벽 반짝임: 두 옥타브 위, 아주 작게(처음 20초)
        if start < 20:
            for m in notes[2:]:
                s = pad_note(midi_hz(m + 24), dur, 0.1, rng)
                s *= env_adsr(len(s), 3.0, 3.0)[:, None]
                add(pad, start, s * 0.025 * (1 - start / 20))
        # 베이스: 새벽 끝(약 13초)부터 밤 마무리 전까지
        if 13 <= start < 93:
            f = midi_hz(root)
            m = int(dur * SR)
            t = np.arange(m) / SR
            s = (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * env_adsr(m, 1.6, 2.5)
            add(bass, start, s * 0.10 * inten)

        # 피아노
        tones = sorted(notes)
        if start < 13:  # 새벽: 드문드문 높은 음
            for b in (0, 3, 6):
                m = tones[(ci + b) % len(tones)] + 12
                add(keys, start + b * BEAT + rng.uniform(-0.01, 0.01), piano_note(m, 0.3), rng.uniform(-0.3, 0.3))
        elif start < 73:  # 낮: 8분음표 분산화음. 화음마다 모양을 바꿔 같은 반복을 피함
            up = [x + 12 for x in tones]
            shapes = [up + up[3:0:-1], [up[0], up[2], up[4], up[2]] * 2, [up[0], up[1], up[3], up[4], up[3], up[1], up[2], up[4]],
                      up[::-1] + up[1:4]]
            seq = shapes[ci % 4]
            for i in range(16):
                if ci < 4 and i % 2 == 1:  # 처음 다리 구간은 4분음표로 여유 있게
                    continue
                vel = (0.2 + 0.25 * inten) * (1.0 if i % 4 == 0 else 0.72) * rng.uniform(0.9, 1.05)
                add(keys, start + i * BEAT / 2 + rng.uniform(-0.008, 0.008), piano_note(seq[i % len(seq)], vel, 2.5), (i % 8 - 3.5) / 8)
            # 낮 절정(약 40~60초): 위 성부에 긴 음 선율
            top = {6: [(78, 0, 4), (76, 4, 4)], 7: [(74, 0, 4), (76, 4, 4)], 8: [(78, 0, 2), (81, 2, 2), (78, 4, 4)]}.get(ci, [])
            for m, b, ln in top:
                add(keys, start + b * BEAT, piano_note(m, 0.32, 2.5 + ln * BEAT), -0.15)
        elif start < 93:  # 노을·해진 뒤: 짧은 선율 + 여린 분산화음
            melody = {11: [(78, 0, 2), (76, 2, 1), (74, 3, 1), (73, 4, 2), (74, 6, 2)],
                      12: [(71, 0, 2), (73, 2, 1), (74, 3, 1), (78, 4, 3), (76, 7, 1)],
                      13: [(74, 0, 2), (71, 2, 2), (69, 4, 4)]}.get(ci, [])
            for m, b, ln in melody:
                add(keys, start + b * BEAT + rng.uniform(-0.01, 0.01), piano_note(m, 0.42, 2.5 + ln * BEAT), 0.1)
            for i in range(0, 16, 2):
                add(keys, start + i * BEAT / 2, piano_note(tones[(i // 2) % 5] + 12, 0.14, 2.5), (i - 8) / 16)
        else:  # 밤 마무리: 마지막 음 몇 개
            for b, m in ((0, 66), (2, 69), (4, 73)):
                add(keys, start + b * BEAT, piano_note(m, 0.25, 4.0), 0.0)

    # 종소리: 해진 뒤 불빛이 켜지는 구간(84~97초), 점점 많아졌다가 줄어듦
    t = 84.0
    while t < total - 1.5:
        dens = float(np.interp(t, [84, 90, 92, 97.5], [0.6, 1.6, 1.2, 0.3]))
        ci = min(int(t // CHORD), len(CHORDS) - 1)
        m = rng.choice(CHORDS[ci][0]) + 24
        add(bells, t, bell_note(int(m), rng.uniform(0.6, 1.0)), rng.uniform(-0.7, 0.7))
        t += rng.exponential(1 / dens) + 0.15

    dry = pad + bass + keys * 0.9 + bells
    wet = reverb(pad * 0.4 + keys * 0.55 + bells * 0.7 + bass * 0.05)
    mix = dry * 0.75 + wet * 0.45
    tt = np.arange(n) / SR
    mix *= (10 ** ((curve(INTENSITY, tt) - 1) * 6 / 20))[:, None]  # 큰 흐름의 세기: 새벽·밤은 약 4dB 여리게
    fade = np.minimum(tt / 3.0, 1) * np.clip((total - tt) / 5.0, 0, 1)  # 처음 3초 나타남, 끝 5초 사라짐
    mix *= fade[:, None]
    mix -= mix.mean(0)
    peak = np.abs(mix).max()
    mix *= 10 ** (-1 / 20) / peak  # 최고 -1dBFS
    pcm = np.clip(np.round(mix * 32767 + rng.uniform(-0.5, 0.5, mix.shape)), -32768, 32767).astype('<i2')
    with wave.open(a.out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{a.out}: {total}초, 48kHz 스테레오, 원래 최고값 {peak:.3f} → -1dBFS로 맞춤')


if __name__ == '__main__':
    main()
