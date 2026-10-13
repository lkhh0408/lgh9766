"""클립의 실제 마지막 프레임을 무손실 PNG로 저장(다음 클립의 시작 프레임으로 사용).

사용: python3 work/scripts/last_frame.py <클립.mp4> <출력.png>
"""
import sys
import cv2

cap = cv2.VideoCapture(sys.argv[1])
last = None
while True:
    ok, f = cap.read()
    if not ok:
        break
    last = f
cv2.imwrite(sys.argv[2], last)
print(sys.argv[2], last.shape)
