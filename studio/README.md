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
| `--scenes` | 곡 폴더의 `scenes.json` | 곡별 장면 계획. 없으면 배경이 무작위로 이어져요 |
| `--stills` | - | `10,60,200`처럼 시간(초)을 주면 영상 대신 그 시점의 PNG만 저장해요. 전체 렌더링 전에 장면을 빠르게 확인할 때 써요 |

## 곡별 장면 (`scenes.json`)
가사에 맞춰 곡마다 걸어갈 거리를 정해요. 곡이 바뀌는 순간(헤드폰 탭) 캐릭터 바로 앞에서 다음 곡의 장면이 시작돼요. 예시는 `playlists/vol01/scenes.json`에 있어요.
```json
{"tracks": {
  "1": {"scenes": ["flowerhouses", "bakery", "avenue"], "signs": {"bakery": "BAKERY"}, "effects": []},
  "2": {"scenes": ["curtainhouses", "goldencafe"], "signs": {"goldencafe": "GOLDEN HOUR"}, "effects": ["golden", "birds"]}
}}
```
- `scenes`: 순서대로 반복되는 장면이에요. 하나에 약 8초씩 이어져요.
  - 동네: `flowerhouses`(창가 꽃 상자), `curtainhouses`(흔들리는 커튼), `openwindows`(활짝 열린 창), `neighbors`(창가에서 손 흔드는 이웃)
  - 가게: `bakery`(빵), `goldencafe` / `cornercoffee` / `terrace`(커피, 오렌지 의자)
  - 거리: `avenue`(가로수길), `crossing`(횡단보도, 신호등, 자전거), `pianohouse` / `downtown`(창문에서 음표가 흘러나오는 건물)
  - 기존 테마: `houses`, `shops`, `park`, `beach`, `forest`, `flowers`, `market`, `town`
- `signs`: 가게 간판 글자를 바꿔요.
- `effects`: `golden`(황금빛 햇살), `birds`(새 떼), `breeze`(바람에 날리는 잎사귀)

렌더링 시간은 영상 1분에 1분 남짓 걸려요. 1시간 영상이면 1시간 이상 걸려요.

## 파일 구성
- `render_video.py`: 오디오 연결, 장면 그리기, 영상 인코딩
- `character.py`: 마스코트. 얼굴, 안경, 머리 모양, 비율은 고정이고, `OUTFITS`에 의상(옷 색, 헤드폰 색, 소품)을 추가해서 갈아입혀요.
- `assets/`: 로고, Outfit 글꼴(SIL Open Font License, `assets/fonts/OFL.txt`)
