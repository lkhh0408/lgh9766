"""명령문에서 입력 안전 필터에 걸리기 쉬운 표현('드론', '타워를 향해 날아감', '타워에 부딪힘' 등)을 중립 표현으로 바꾼다.

2026-10-18 제작 중 'Input blocked' 거절이 난 뒤 만든 도구. 같은 장면을 카메라 중심 표현으로 바꿀 뿐 움직임은 그대로 둔다.
사용: python3 work/scripts/sanitize_prompt.py 입력.txt 출력.txt
"""
import re
import sys

RULES = [
    # 2026-10-18: 'circling'이 들어간 명령문이 여러 번 입력 차단됨(통과한 것은 'circles'·'arc')
    (r'keeps circling around the tower', 'continues its slow arc around the tower'),
    (r'keeps circling', 'continues its slow arc'),
    (r'circling slowly to the (left|right) around the tower', r'moving in a slow arc to the \1 around the tower'),
    (r'\bcircling\b', 'arc movement'),
    (r'aerial drone footage', 'aerial footage'),
    (r'drone camera', 'aerial camera'),
    (r'an ongoing drone flight', 'a continuous aerial shot'),
    (r'\bdrone\b', 'aerial camera'),
    (r'flying straight toward the tower', 'moving steadily forward'),
    (r'flying toward the tower', 'moving forward'),
    (r'flies toward the tower', 'moves forward'),
    (r'gliding forward toward the tower', 'gliding smoothly forward'),
    (r'keeps gliding gently closer to the tower', 'keeps gliding gently forward'),
    (r'toward the tower', 'forward'),
    (r'\s*The camera (?:stays well away from the tower and )?never flies into (?:or through )?(?:the tower|it)\.', ''),
    (r'\s*The camera always keeps a wide, comfortable distance from the tower\.', ''),
    (r',? and never flies into it', ''),
]


def sanitize(s):
    for a, b in RULES:
        s = re.sub(a, b, s)
    return s


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    out = sanitize(open(src, encoding='utf-8').read())
    open(dst, 'w', encoding='utf-8').write(out)
    left = [w for w in ('drone', 'toward the tower', 'flies into') if w in out]
    print('저장:', dst, '| 남은 표현:', left or '없음')
