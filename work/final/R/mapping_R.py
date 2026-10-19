"""승인본 기준 본편(R)의 원본 이미지 001~137 ↔ 영상 시각 대응표를 만든다. 무료(로컬 계산만 함).

입력: 완성본 옆의 <완성본>.edit.json(finish.py가 씀, 조각별 영상 시각), 예전 대응표(제외·색 참조 판단과 이유).
출력: work/final/R/이미지_시간_대응표.csv (이미지,구간,영상시작초,영상끝초,쓰임)

구간 배정(원본 이미지의 시간대·내용 → 영상 구간)
  001~013 S1      승인본 1단계(새벽→아침, 타워 선회 후 전진 활공)
  014~031 BR      잇는 조각(맑은 낮 전진·상승 → 하늘로 들기 → 내려오며 032 구도에 닿음)
  032~050 MID     승인 중간 시험(032에서 접근 → 전망대 선회, 끝 4초 감속)
  051~099 X       오후(물러나며 상승, 낮 → 늦은 오후)
  100~110 Y1      노을 첫 조각(늦은 오후 → 해가 지평선에 닿음)
  111~121 Y2      노을 연장(해진 직후, 불빛이 켜짐)
  122~137 Z       밤(도시 불빛, 계속 물러남)
같은 구간 안에서는 이미지 번호 순서대로 그 구간의 시간을 고르게 나눈다(원본 이미지가 영상의 그 순간과 같은 구도라는 뜻은 아님).
예전 대응표에서 '제외'(중복·역방향·배치 차이 등)와 '색 참조'로 판단한 이미지는 그 판단과 이유를 그대로 둔다.

사용: python3 work/final/R/mapping_R.py <완성본.mp4>
"""
import csv
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OLD = os.path.join(ROOT, 'work/final/plan/이미지_시간_대응표.csv')
OUT = os.path.join(ROOT, 'work/final/R/이미지_시간_대응표.csv')

GROUPS = [  # (첫 이미지, 끝 이미지, 구간 이름, edit.json 조각 label들, 설명)
    (1, 13, 'S1', ['S1'], '승인본 1단계: 008c_clean(새벽색 보정·정비 팔 제거)을 첫 장면으로 Omni 4K 8초 + 연장 8초'),
    (14, 31, 'BR', ['BR_up', 'BR_sky', 'BR_sky2', 'BR_sky3', 'BR_down'],
     '잇는 조각: 낮 전진·상승 → 하늘로 들었다가 내려오며 032 구도(중간 시험 첫 장면)에 닿음. 원본의 접근 경로는 따르지 않음'),
    (32, 50, 'MID', ['MID'], '승인 중간 시험: 032 원본을 첫 장면으로 접근 → 전망대 선회(4K 8초 + 연장 8초), 끝 4초 감속'),
    (51, 99, 'X', ['X1', 'X2'], '오후: 전망대 앞에서 물러나며 상승, 낮 → 늦은 오후. 원본의 내려다보기·선회 구도는 따르지 않음'),
    (100, 110, 'Y1', ['Y1'], '노을 첫 조각: 물러나며 천천히 돌고, 해가 왼쪽 지평선으로 내려감'),
    (111, 121, 'Y2', ['Y2'], '노을 연장: 해진 직후, 도시 불빛과 타워 조명이 켜짐'),
    (122, 137, 'Z', ['Z'], '밤: 도시 불빛 속에서 계속 물러남'),
]


def spans(edit_json):
    """label별 (시작초, 끝초). 같은 label 조각이 여러 개면 처음~끝."""
    d = json.load(open(edit_json, encoding='utf-8'))
    out = {}
    for p in d['segments']:
        a, b = p['film_start_s'], p['film_end_s']
        lab = p['label']
        s, e = out.get(lab, (a, b))
        out[lab] = (min(s, a), max(e, b))
    return out


def main():
    film = sys.argv[1]
    sp = spans(os.path.splitext(film)[0] + '.edit.json')
    old = {int(r['이미지']): r for r in csv.DictReader(open(OLD, encoding='utf-8'))}
    rows = []
    for first, last, name, labels, desc in GROUPS:
        t0 = min(sp[l][0] for l in labels)
        t1 = max(sp[l][1] for l in labels)
        n = last - first + 1
        for k, img in enumerate(range(first, last + 1)):
            a = t0 + (t1 - t0) * k / n
            b = t0 + (t1 - t0) * (k + 1) / n
            note = old.get(img, {}).get('쓰임', '')
            if note.startswith('제외') or note.startswith('색 참조'):
                use = note.split(' 화면에 나오지 않음')[0].rstrip('.') + '. 화면에 나오지 않음'
            elif img == 8:
                use = '시작 키프레임: 008c_clean으로 만든 승인본 1단계의 첫 장면(영상 0초)'
            elif img == 32:
                use = '중간 시험의 첫 장면(032 원본을 Omni 첫 장면으로 사용). 잇는 조각이 이 장면에서 끝나도록 끝 장면으로도 지정'
            else:
                ref = note.split(':', 1)[1].strip() if ':' in note else note
                use = f'내용 참조: {ref}' if ref else '내용 참조'
            if img == 8:  # 시작 장면은 영상 첫 프레임
                a, b = 0.0, 1 / 24
            rows.append({'이미지': f'{img:03d}', '구간': name, '영상시작초': f'{a:.2f}', '영상끝초': f'{b:.2f}',
                         '쓰임': f'{use} | 구간: {desc}'})
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['이미지', '구간', '영상시작초', '영상끝초', '쓰임'])
        w.writeheader()
        w.writerows(rows)
    kinds = {'제외': 0, '색 참조': 0, '내용 참조': 0, '시작·끝 장면': 0}
    for r in rows:
        u = r['쓰임']
        k = '제외' if u.startswith('제외') else '색 참조' if u.startswith('색 참조') else '내용 참조' if u.startswith('내용') else '시작·끝 장면'
        kinds[k] += 1
    print(f'저장: {OUT} ({len(rows)}장) ' + ', '.join(f'{k} {v}' for k, v in kinds.items()))


if __name__ == '__main__':
    main()
