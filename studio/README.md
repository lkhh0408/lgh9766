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
| `--scenes` | 곡 폴더의 `storyboard.json` | 곡별 스토리보드. 없으면 배경이 무작위로 이어져요 |
| `--stills` | - | `10,60,200`처럼 시간(초)을 주면 영상 대신 그 시점의 PNG만 저장해요. 전체 렌더링 전에 장면을 빠르게 확인할 때 써요 |

## 작업 프로세스 (한 편 만들기)
```
① 곡과 가사 준비     songs 폴더에 "번호.제목.mp3", lyrics 폴더에 같은 이름의 "번호.제목.txt"
        ↓
② 가사 타이밍 찾기   python studio/align_lyrics.py <songs> <lyrics> -o playlists/volXX/timing
                    → AI가 노래를 듣고 가사 한 줄 한 줄이 몇 초에 나오는지 찾아요 (곡당 약 1분)
        ↓
③ 스토리보드 쓰기    playlists/volXX/storyboard.json
                    → 곡마다 하늘색, 기본 거리, "어떤 가사에 어떤 장면" 을 적어요
        ↓
④ 미리보기          python studio/render_video.py <songs> --scenes <storyboard> -o p.mp4 --stills 10,60,120
                    → 몇 장만 그려서 장면을 빠르게 확인
        ↓
⑤ 영상 렌더링       python studio/render_video.py <songs> --scenes <storyboard> -o volXX.mp4
```

## 스토리보드 (`storyboard.json`)
가사가 나오는 순간, 그 가사의 장면이 캐릭터 앞에 나타나요. 예시는 `playlists/vol01/storyboard.json`이에요.
```json
{"tracks": {"1": {
  "sky": ["#6FD3E8", "#E3FFF2"],
  "palette": ["#2EC4A6", "#FF8A3D"],
  "scenes": ["flowerhouses", "avenue", "shops"],
  "signs": {"shops": "FLOWERS"},
  "effects": [],
  "chorus": {"banner": "ON THE GOOD SIDE OF THE STREET", "lights": true},
  "beats": [
    {"line": "watering the flowers", "piece": "waterer"},
    {"line": "bicycle bell", "piece": "cyclist", "react": "note"},
    {"line": "summer leaves", "effect": "breeze", "dur": 12}
  ]
}}}
```
- `sky`: 그 곡의 하늘색 (위, 아래). 밤이 되면 자연스럽게 어두워져요.
- `palette`: 가게 차양, 지붕 같은 포인트 색.
- `scenes`: 장면 사이를 채우는 기본 거리. 하나에 약 8초씩 반복돼요.
  `flowerhouses` `curtainhouses` `openwindows` `neighbors` `bakery` `goldencafe` `cornercoffee` `terrace` `avenue` `crossing` `pianohouse` `downtown` `houses` `shops` `park` `beach` `forest` `flowers` `market` `town`
- `signs`: 기본 거리 가게의 간판 글자.
- `effects`: 곡 전체에 거는 효과. `golden`(황금빛), `birds`(새 떼), `breeze`(날리는 잎사귀)
- `chorus`: 후렴이 나오는 동안 거리 위에 전구 줄(`lights`), 후렴 시작마다 현수막(`banner`).
- `beats`: 가사 한 줄(`line`, 일부만 써도 돼요)에 맞춰 일어나는 일.
  - `piece`: 등장하는 장면 (`studio/props.py`)
    `sign`(거리 표지판) `waterer`(꽃에 물 주는 이웃) `baker`(손 흔드는 빵집 주인) `tall_trees`(키 큰 가로수) `cyclist`(벨 울리며 지나가는 자전거) `rooftop`(옥상 저녁 식사) `pianist`(2층 피아노) `terrace` / `sip_terrace`(카페 테라스 손님) `friend_window`(창가에서 손 흔드는 친구) `neighbors_wave`(손 흔드는 이웃들) `kettle_window`(노래하는 주전자) `golden_neon`(네온 간판) `note_door`(문에 붙는 메모) `alarm_window`(울리는 알람 시계) `sneaker_shop`(운동화 가게) `windows_open`(창문이 하나씩 열리는 건물) `corner_lady`(카운터에서 인사하는 점원) `banner`(현수막)
  - `sign` / `text`: 간판이나 표지판 글자
  - `react`: 캐릭터 반응 말풍선 `heart` `note` `sun`
  - `effect` + `dur`: 그 가사부터 몇 초 동안 효과 켜기
  - `all: true`: 같은 가사가 나올 때마다 반복 (후렴용), `nth: 2`: 두 번째로 나올 때만

렌더링 시간은 영상 1분에 1분 남짓 걸려요. 1시간 영상이면 1시간 이상 걸려요.

## 파일 구성
- `render_video.py`: 오디오 연결, 장면 그리기, 영상 인코딩
- `align_lyrics.py`: 가사 타이밍 찾기 (faster-whisper 음성 인식, 처음 실행할 때 모델을 내려받아요)
- `props.py`: 가사 장면 소품과 동네 사람들
- `character.py`: 마스코트. 얼굴, 안경, 머리 모양, 비율은 고정이고, `OUTFITS`에 의상(옷 색, 헤드폰 색, 소품)을 추가해서 갈아입혀요.
- `assets/`: 로고, Outfit 글꼴(SIL Open Font License, `assets/fonts/OFL.txt`)
