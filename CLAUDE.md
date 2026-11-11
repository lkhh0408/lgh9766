# Open to Close 작업 규칙

YouTube 음악 채널 **Open to Close** (@OpentoClose_day) 작업 저장소예요. 사용자와는 한국어로 대화해요.

## 절대 규칙
- **음질: 지지직거리는 소리, 잡음은 절대 안 돼요.**
  - 음량은 `studio/render_video.py`의 방식(곡마다 고정 게인으로 -14 LUFS, -1.5 dB 리미터, 24비트 믹스)만 써요. ffmpeg `loudnorm`의 실시간(dynamic) 모드는 고음역 잡음을 만들어서 쓰지 않아요.
  - 영상 오디오는 AAC 384kbps `-aac_coder twoloop`. 기본 AAC 설정이나 낮은 비트레이트로 바꾸지 않아요.
  - 오디오 처리 방식을 바꿨다면, 원본 MP3와 비교해서 추가된 잡음을 측정한 뒤에 보내요.
- **캐릭터는 고정**: 얼굴, 동그란 안경, 단발 머리, 비율은 바꾸지 않아요. 옷, 헤드폰, 소품만 영상마다 바꿔요 (`studio/character.py`의 `OUTFITS`).
- **후킹 우선**: 제목, 썸네일, 설명은 장르나 시간대(아침 팝송 등)로 한정하지 않고, 클릭하고 싶게 만드는 후킹이 기준이에요.

## 작업 방식
- 사용자는 MP3를 GitHub에 `번호.제목.mp3`로 올리고, 가사는 채팅에 `번호. 제목` + `[Verse]`/`[Chorus]` 구간 표시와 함께 붙여넣어요. 가사는 `playlists/volXX/lyrics/번호.제목.txt`로 저장해요.
- 영상: 가사 타이밍(`studio/align_lyrics.py`) → 스토리보드(`playlists/volXX/storyboard.json`, 가사 한 줄마다 장면) → 미리보기(`--stills`) → 렌더링. 자세한 건 `studio/README.md`, `docs/OpenToClose_process_guide.pdf`.
- 곡 사이 1.5초: 캐릭터가 멈춰 헤드폰을 탭하고 ▶ 말풍선, 화면 표시는 `TRACK 0X`와 곡 제목.
- 작업 방식이 새로 생기거나 바뀌면 사용자가 이해하기 쉽게 프로세스(단계, 프로그램, 하는 일)를 함께 설명해요.
- Suno 곡 요청("다음 곡")은 `suno/songs.md`의 규칙을 따르고, 곡마다 Title, Styles, Exclude, Lyrics, 곡 소개(멜론 앨범 소개 스타일)를 줘요.
