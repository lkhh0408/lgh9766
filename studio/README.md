# Open to Close 영상 제작 도구

곡 폴더를 넣으면, 안경 쓴 캐릭터가 여러 테마의 거리를 걸어가는 1080p 영상을 만들어요.

- 하늘은 영상 길이에 맞춰 아침에서 밤으로 천천히 바뀌어요.
- 배경은 주택가, 상점가, 공원, 바닷가, 숲, 꽃밭, 시장, 도심 8가지 테마가 무작위로 이어져요.
- 곡이 끝나면 캐릭터가 멈춰 헤드폰을 톡 누르고, ▶ 말풍선이 뜬 뒤 다음 곡이 시작돼요. 곡 사이 공백은 기본 1.5초예요.
- 화면에는 로고, `TRACK 0X`와 곡 제목, 재생 바가 표시돼요.
- 모든 곡의 음량은 YouTube 기준(-14 LUFS)으로 맞춰요.

## 준비
```bash
sudo apt install ffmpeg            # Mac: brew install ffmpeg
pip install -r studio/requirements.txt
```

## 사용법
곡 파일 이름을 `번호.제목.mp3` 형식으로 만들어 한 폴더에 넣어요. 번호 순서대로 재생되고, 제목이 그대로 화면에 표시돼요.
```
songs/morning-vol1/
  1.Good Side of the Street.mp3
  2.Golden Hour Coffee.mp3
  3.Open the Window.mp3
```
```bash
python studio/render_video.py songs/morning-vol1 -o morning-vol1.mp4
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--gap` | `1.5` | 곡 사이 공백(초) |
| `--seed` | `21` | 배경 순서와 배치. 영상마다 바꾸면 매번 다른 거리를 걸어가요 |

렌더링 시간은 영상 1분에 1분 남짓 걸려요. 1시간 영상이면 1시간 이상 걸려요.

## 파일 구성
- `render_video.py`: 오디오 연결, 장면 그리기, 영상 인코딩
- `character.py`: 마스코트. 얼굴, 안경, 머리 모양, 비율은 고정이고, `OUTFITS`에 의상(옷 색, 헤드폰 색, 소품)을 추가해서 갈아입혀요.
- `assets/`: 로고, Outfit 글꼴(SIL Open Font License, `assets/fonts/OFL.txt`)
