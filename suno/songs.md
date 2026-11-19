# Suno 곡 기록

"다음 곡"을 요청하면 이 기록을 보고 장르, 보컬, 주제가 겹치지 않게 다음 곡을 만들어요.

## 공통 규칙
- 장르나 시간대(아침, 저녁 등)로 채널을 나누지 않아요. 영상 제목은 CLAUDE.md의 '쓰임새 중심' 규칙을 따라요.
- 영어 팝송이고 가사는 반드시 넣어요. 긍정적인 내용만 쓰고, 곡 길이는 3분 이내예요.
- 히트곡 느낌은 내되, 카페나 공부, 일할 때 틀어도 자극적이지 않아야 해요. 고음은 괜찮지만 내지르면 안 돼요.
- 가사는 모두 새로 쓴 창작 가사예요. 실제 곡의 가사, 제목, 가수 이름은 쓰지 않아요.
- 곡을 줄 때 순서: **Title → 장르/BPM → Exclude → Styles → Lyrics → 곡 소개(멜론 앨범 소개 스타일)**. 각 항목은 Suno에 바로 붙여 넣을 수 있게 코드 블록으로 줘요.

**Styles 구성 (VOL.02부터)**: `곡별 장르 부분` + `공통 뒷부분`. 장르가 맨 앞에 와야 Suno가 장르 색을 살려요.

**공통 Styles (뒷부분)** (VOL.03 8번부터 맨 앞에 요즘 사운드 문구 추가)
```
modern polished production, contemporary 2020s sound, catchy but gentle melody, easy listening, warm feel-good vibe, positive, smooth relaxed vocals, mellow dynamics, consistent volume, background music friendly, full length song around 3 minutes
```

**Exclude**
```
belting, shouting, screaming, aggressive, loud drums, heavy bass, EDM drop, sudden loud parts, distortion, rock, rap, sad, dark, explicit lyrics
```
- 송랩 곡(VOL.03 18번처럼 사용자가 정한 자리)만 예외로 Exclude에서 `rap`을 빼고 Styles에 `melodic sing-song rap, soft relaxed flow, no aggressive delivery`를 넣어요. 나머지 곡은 계속 `rap`을 막아요.
- R&B, 멜로딕 힙합 곡은 `heavy bass`를 빼고 Styles에 `warm round bass`를 넣어요. `rap`은 항상 막아요(힙합은 비트만, 보컬은 노래).

## 타겟과 사운드 (확정)
- 타겟은 **20~30대**. 처음 듣자마자 요즘 노래 같아야 해요. 기준은 장르 이름이 아니라 **사운드가 요즘 것인지**예요(레트로 감성 장르도 요즘 사운드로는 가능).
- 옛날 녹음을 흉내 내는 스타일(60년대 모타운, 컨트리 밴조, 라이브 브라스 중심 등)은 쓰지 않아요.
- 아이돌 느낌은 **수록곡 같은 이지리스닝 계열**만. 비트가 세거나 내지르는 타이틀곡 스타일은 안 돼요. 특정 그룹, 곡 이름은 쓰지 않아요.
- 멜로디는 오래 들어도 좋게, 사운드는 요즘 것으로.

## 곡 주제 키워드
- 주제는 `suno/keywords.md`의 키워드를 참고해서 정하고, 쓴 키워드는 그 파일에 `✅ (곡명)`으로 표시해요.

## 가사 쓰는 기준 (VOL.03 14번부터, 한글 번역 자막과 함께 보여지는 가사)
1. **곡마다 전할 마음을 먼저 정해요**: 기쁨(작은 행운, 설렘) / 위로("오늘도 수고했어") / 공감("어, 이거 내 얘긴데") 중 하나.
2. **2030이 실제로 겪는 장면**으로 써요: 출근길, 퇴근 후, 자취방, 주말 늦잠, 친구와의 대화 등. 와닿지 않는 이국적 디테일(고유명사, 낯선 단어)은 줄여요.
3. **마음에 남는 한 줄**을 곡마다 하나 넣어요(번역했을 때 캡처해서 저장하고 싶은 문장. 예: "늦게 피어도 괜찮아, 결국 피니까").
4. **위로도 밝게 끝내요**: 슬픈 노래는 안 되지만, 지친 마음을 살짝 알아준 뒤 따뜻하게 마무리해요.
5. **한국어로 옮겨도 자연스러운 영어**로 써요: 영어 말장난에만 기대지 않고, 번역해도 뜻과 감정이 그대로 전해지게.

## 곡 길이 (확정)
- 모든 곡은 **2분 40초 이상 ~ 3분 15초 미만**. 1분대, 2분 초반은 안 돼요.
- 공통 Styles 끝은 `full length song around 3 minutes`.
- 길이는 **가사 총 줄 수로만** 맞춰요. "후렴 3번 + 브리지" 같은 고정 뼈대는 쓰지 않아요(곡이 다 비슷해져요).
- **장르에 맞춰 가사 총 줄 수를 정해요** (실제 Suno 결과로 맞춘 기준, 2026-11-14). 너무 길면 지루해서 안 들어요.
  - 신나는 팝(아이돌, 일렉트로닉, 하우스): 약 40~42줄 / 중간(라틴, 힙합, 어쿠스틱): 약 38~40줄 / 느린 곡(R&B, 로파이): 약 28줄
  - 연주 구간([Intro], [Instrumental Break], [Instrumental Outro])은 하나에 약 20~30초가 늘어나서 **곡마다 최대 1개**만 넣어요.
  - 실제 결과: Snow on the Sill 32줄/인트로 1개 2:54(베드룸 팝 84), Humming on the 8:15 38줄/없음 2:52(인디 팝 96), Same Page 37줄/연주 없음 2:43, Fountain Square 42줄/없음 3:05, One More Page 30줄/2개 2:47, Encore Room 36줄/없음 2:11(짧음) → 42줄/인트로 2:40, Table for One 26줄/2개 3:17, Laptop Closed 38줄/2개 3:22, Highlight Reel 32줄/2개 3:28(김), Nothing Special 40줄/없음 3:24·3:08(칠 R&B 듀엣)
  - 살짝 긴 곡은 영상 만들 때 앞뒤 연주 부분을 잘라 3:15 안으로 맞출 수 있어요(자연스러운 페이드).

## 곡 구성 다양하게 (VOL.03 16번부터)
- 모든 곡을 벌스 → 프리코러스 → 코러스로 만들지 않아요. **바로 옆 곡끼리 구성이 겹치지 않게** 아래 유형을 섞어 써요.
  - A. 후렴 먼저: 후렴 → 벌스 → 후렴 → 벌스 → 후렴 (아이돌 팝, R&B 팝)
  - B. 포스트 코러스: 후렴 뒤에 [Post-Chorus] 짧은 반복 훅 (아이돌 팝, 칠 하우스)
  - C. 프리코러스 없음: 벌스 → 후렴 → 벌스 → 후렴 → 브리지 → 후렴 (로파이, 송랩)
  - E. 후렴구 반복형: 큰 후렴 없이 벌스마다 끝에 제목 문장 (어쿠스틱, 포크)
  - F. 중간 연주 구간: 후렴 → [Instrumental Break] → 마지막 후렴 (R&B, 하우스)
  - G. 듀엣 주고받기: 1절 한 사람, 2절 다른 사람, 후렴 같이, 브리지 한 줄씩 (듀엣)
  - H. AABA: A(벌스, 끝에 제목 문장) → A → B(분위기 전환) → A → 연주 마무리. 큰 후렴 없음
  - I. 반복 훅(루프)형: 짧은 훅 2줄이 계속 돌아오고 사이사이 벌스가 바뀜 (로파이)
  - J. 끝까지 주고받기: 처음부터 끝까지 두 사람이 한 줄씩 대화, 후렴 2번, 마지막은 다 같이 흥얼거리며 끝 (듀엣)
  - K. 후렴 2번 + 긴 연주 마무리: 벌스·후렴·벌스·후렴 후 브리지 없이 연주로 끝
- 곡마다 **뼈대(구간 순서)**가 바로 앞 2곡과 겹치지 않는지 확인하고 써요.
- VOL.03 계획: 16 = A+B, 17 = F, 18 = C, 19 = I(반복 훅), 20 = J(끝까지 주고받기)

## 가사 겹침 금지
- 곡끼리 **후렴 핵심 문장, 제목, 특징적인 표현**이 겹치지 않게 써요(이전 VOL 곡 제목 포함). 꼭 필요한 기본 단어(love, day 등)는 괜찮아요.
- 새 곡을 쓰기 전에 아래 '사용한 핵심 표현'을 확인하고, 쓴 뒤에 추가해요.

## 흐름 규칙 (환기)
- 바로 옆 곡끼리 장르, 보컬(남/여/듀엣)이 겹치지 않아요.
- 템포는 물결처럼: 느린 곡(85~92), 중간(95~105), 리듬감(108~115)을 번갈아요.
- 4~5곡마다 R&B나 멜로딕 힙합 같은 환기곡을 넣어요.
- 20곡 비율: 팝 계열 10, 가벼운 R&B/네오소울 4, 멜로딕 힙합(노래 보컬) 3, 포크/소울/컨트리 팝 등 3.

### VOL.02 흐름표
| # | 장르 | 보컬 |
|---|---|---|
| 1 | 시티팝 | 남 |
| 2 | 재즈 팝 | 여 |
| 3 | 인디 포크 | 듀엣 |
| 4 | 칠 R&B (환기) | 남 |
| 5 | 어쿠스틱 팝 | 여 |
| 6 | 레트로 소울 | 남 |
| 7 | 컨트리 팝 | 여 |
| 8 | 피아노 팝 | 남 |
| 9 | 멜로딕 힙합 (환기) | 여 |
| 10 | 보사 팝 | 남 |
| 11 | 네오소울 | 여 |
| 12 | 소프트 펑크 | 남 |
| 13 | 인디 팝 | 여 |
| 14 | 칠 R&B (환기) | 듀엣 |
| 15 | 레게 팝 | 남 |
| 16 | 멜로딕 힙합 (환기) | 남 |
| 17 | 라운지 디스코 | 여 |
| 18 | R&B | 여 |
| 19 | 어쿠스틱 포크 | 남 |
| 20 | 마무리 팝 | 듀엣 |

### VOL.03 흐름표 (파일 41~60, 6번부터 요즘 장르로 변경)
| # | 장르 | 보컬 | BPM |
|---|---|---|---|
| 1 | 선샤인 팝 | 여 | 104 |
| 2 | 포크 팝 (생성 후 올드하면 → 모던 어쿠스틱 팝) | 남 | 90 |
| 3 | 소프트 신스 팝 | 듀엣 | 110 |
| 4 | 네오소울 (환기, 생성 후 올드하면 → 칠 R&B) | 남 | 86 |
| 5 | 재즈 팝 (생성 후 올드하면 → 로파이 재즈 팝) | 여 | 100 |
| 6 | 베드룸 팝 | 남 | 88 |
| 7 | 소프트 일렉트로 팝 | 여 | 104 |
| 8 | 멜로딕 힙합 (환기, 소프트 트랩 비트) | 남 | 86 |
| 9 | 칠 하우스 팝 | 듀엣 | 114 |
| 10 | 포크트로니카 | 여 | 92 |
| 11 | 얼트 팝 | 남 | 108 |
| 12 | 얼터너티브 R&B (환기) | 여 | 90 |
| 13 | 라틴 팝 (소프트 레게톤 리듬) | 남 | 98 |
| 14 | 이지리스닝 걸그룹 팝 (Y2K, 가벼운 2-step 비트) | 여 | 112 |
| 15 | 멜로딕 힙합 (환기, 로파이) | 듀엣 | 86 |
| 16 | 이지리스닝 보이그룹 팝 | 남 | 108 |
| 17 | R&B 팝 | 여 | 94 |
| 18 | 송랩 (노래하듯 부드러운 멜로딕 랩) | 남 | 100 |
| 19 | 로파이 팝 | 여 | 90 |
| 20 | 모던 어쿠스틱 팝 (마무리) | 듀엣 | 98 |
| 21 | 인디 일렉트로닉 팝 (구성 K) | 남 | 110 |
| 22 | 칠 R&B (환기, 구성 H AABA) | 여 | 88 |
| 23 | 청량 이지리스닝 혼성 팝 (구성 A 후렴 먼저) | 듀엣 | 104 |
| 24 | 소프트 리퀴드 드럼앤베이스 팝 (구성 B 포스트 코러스) | 여 | 172 (하프타임 86) |
- "다음 곡"이면 번호를 이어서(25, 26 …) 그때그때 가장 좋은 곡을 만들어요(예비 곡 구분 없음). **올드한 장르, 옛날 녹음 느낌은 절대 안 돼요.** 기타가 중심인 팝(모던 기타 팝 등)도 올드하게 들려서 쓰지 않아요.
- VOL.03부터 컨트리, 브라스, 보사, 레게, 시티팝, 디스코 같은 옛날 느낌 장르는 빼고 요즘 장르(베드룸 팝, 칠 하우스, 얼트 R&B 등)를 넣어요. 리듬이 강한 장르도 `heavy bass`는 계속 막고 `warm round bass`, 부드러운 비트로 배경음악 느낌을 지켜요.

## 지금까지 만든 곡
| # | 제목 | 보컬 | 장르 | BPM | 한 줄 소개 |
|---|---|---|---|---|---|
| - | Good Side of the Street | - | - | - | (직접 만든 곡) |
| 01 | Golden Hour Coffee | 여성 | 어쿠스틱 팝 | 100 | 커튼 사이로 스며든 햇살과 커피 한 잔, 서두르지 않아도 괜찮은 아침에 건네는 다정한 인사 |
| 02 | Open the Window | 남성 | 소프트 인디 팝 | 96 | 걱정은 정리하지 않은 침대 위에 두고, 창문을 활짝 열어 새로운 하루를 들이는 아침의 노래 |
| 03 | Little Things | 여성 | 보사 팝 | 92 | 김 서린 거울 위의 미소, 오랜만에 찾은 양말 한 짝. 행복은 언제나 작은 것들 속에 숨어 있다 |

## VOL.02
| # | 제목 | 보컬 | 장르 | BPM | 한 줄 소개 |
|---|---|---|---|---|---|
| 01 | Two Wheels, No Hurry | 남성 | 시티팝 | 98 | 강변을 따라 자전거 페달을 천천히 밟는 오후, 바람이 등을 밀어주는 날의 노래 |
| 02 | Blanket on the Grass | 여성 | 재즈 팝 | 104 | 체크무늬 담요 한 장과 친구들, 공원 잔디 위에서 열리는 작은 피크닉 |
| 03 | Harmony in the Passenger Seat | 듀엣 | 인디 포크 | 88 | 창문을 내리고 라디오 볼륨을 올린 드라이브, 조수석에서 맞춰 부르는 화음 |
| 04 | When the Streetlights Come On | 남성 | 칠 R&B | 94 | 가로등이 하나씩 켜지는 퇴근길, 오늘 하루를 다독이며 천천히 걷는 저녁 |
| 05 | Seashell in My Pocket | 여성 | 어쿠스틱 팝 | 110 | 바닷가에서 주운 조개껍데기 하나, 주머니 속에 넣어 온 파도 소리 같은 하루 |
| 06 | Green Lights All the Way | 남성 | 레트로 소울 | 100 | 신호등이 전부 초록불인 날, 작은 행운이 줄줄이 이어지는 기분 좋은 하루 |
| 07 | Tailgate Constellations | 여성 | 컨트리 팝 | 90 | 트럭 짐칸에 누워 별자리를 새로 지어 붙이는 시골 밤 |
| 08 | Middle C | 남성 | 피아노 팝 | 106 | 어른이 되어 처음 배우는 피아노, 서툰 손가락으로 완성한 첫 곡의 기쁨 |
| 09 | Headphones On | 여성 | 멜로딕 힙합 | 88 | 헤드폰을 쓰는 순간 붐비는 도시가 나만의 뮤직비디오가 되는 출근길 |
| 10 | Under the Awning | 남성 | 보사 팝 | 102 | 갑작스러운 소나기, 가게 차양 아래 모인 낯선 사람들과 함께 기다리는 무지개 |
| 11 | Oversized Sweater | 여성 | 네오소울 | 86 | 소매가 손등을 덮는 큰 스웨터와 차 한 잔, 나를 다정하게 안아주는 오후 |
| 12 | Roller Rink Saturday | 남성 | 소프트 펑크 | 112 | 디스코 볼 아래 롤러스케이트장, 넘어져도 웃으며 다시 일어나는 토요일 |
| 13 | Four Frames | 여성 | 인디 팝 | 96 | 친구들과 비좁은 포토부스에 들어가 찍은 네 컷, 우스운 표정까지 모두 보물 |
| 14 | Aisle Five | 듀엣 | 칠 R&B | 92 | 늦은 밤 마트 다섯 번째 통로, 시리얼 하나 고르며 주고받는 다정한 대화 |

## VOL.03
| # | 제목 | 보컬 | 장르 | BPM | 한 줄 소개 |
|---|---|---|---|---|---|
| 01 | Line Dried | 여성 | 선샤인 팝 | 104 | 햇볕에 바싹 마른 빨래처럼, 걱정까지 바람에 널어 말리는 가벼운 오후 |
| 02 | Balcony Tomatoes | 남성 | 포크 팝 | 90 | 작은 화분 몇 개로 시작한 베란다 텃밭, 처음 빨갛게 익은 토마토 하나의 기쁨 |
| 03 | Voice Note | 듀엣 | 소프트 신스 팝 | 110 | 바쁜 하루 사이사이 주고받는 음성 메시지, 목소리만으로 가까워지는 두 사람 |
| 04 | B-Side | 남성 | 네오소울 | 86 | 레코드 가게 구석에서 찾은 낡은 판, 아무도 몰랐던 뒷면의 노래가 오늘의 최애곡이 되는 오후 |
| 05 | Crossword in Pen | 여성 | 재즈 팝 | 100 | 틀려도 괜찮다며 볼펜으로 채워 가는 일요일 낱말 퍼즐, 자신감 한 스푼 넣은 아침 |
| 06 | Glow-in-the-Dark Stars | 남성 | 베드룸 팝 | 88 | 천장에 붙인 야광 별 스티커, 내 방이 작은 우주가 되는 밤 |
| 07 | Save Point | 여성 | 소프트 일렉트로 팝 | 104 | 게임 속 세이브 포인트처럼, 오늘의 좋은 순간들을 마음에 하나씩 저장하는 하루 |
| 08 | Do Not Disturb | 남성 | 멜로딕 힙합 (소프트 트랩) | 86 | 휴대폰을 방해금지 모드로 돌려두고, 오롯이 나에게만 집중하는 느긋한 오후 |
| 09 | Rooftop Hours | 듀엣 | 칠 하우스 팝 | 114 | 퇴근 후 옥상에 올라 노을이 질 때까지, 시간이 천천히 흐르는 두 사람의 저녁 |
| 10 | Day Trip Ticket | 여성 | 포크트로니카 | 92 | 충동적으로 끊은 기차표 한 장, 창밖 풍경을 따라 혼자 떠나는 당일치기 여행 |
| 11 | Fresh Cut | 남성 | 얼트 팝 | 108 | 미용실 문을 나서는 순간 달라 보이는 세상, 새 머리 하나로 충전되는 자신감 |
| 12 | Soft Reset | 여성 | 얼터너티브 R&B | 90 | 방을 치우고 초를 켜고 마스크팩을 붙이는 일요일 밤, 나를 다시 시작하는 작은 의식 (10번은 나중에) |
| 13 | Fountain Square | 남성 | 라틴 팝 (소프트 레게톤) | 98 | 해 질 녘 분수 광장, 누군가 틀어둔 스피커에 맞춰 모르는 사람들과 하나둘 춤추게 되는 저녁 |
| 14 | Same Page | 여성 | 이지리스닝 걸그룹 팝 (Y2K, 2-step) | 112 | 같은 순간 똑같은 문자를 보내는 단짝, 눈빛 반만 봐도 다 아는 사이 (공감) |
| 15 | Made It Home | 듀엣 | 멜로딕 힙합 (로파이) | 86 | 야근 끝난 밤 편의점 앞 컵라면 하나, 오늘도 버텨낸 서로를 다독이는 두 사람 (위로) |
| 16 | Laptop Closed | 남성 | 이지리스닝 보이그룹 팝 | 108 | 금요일 저녁 노트북을 덮는 순간 시작되는 주말, 일주일을 버틴 나에게 주는 해방감 (기쁨, 구성 A+B) |
| 17 | Highlight Reel | 여성 | R&B 팝 | 94 | 밤에 SNS를 넘기다 작아지는 순간, 내 비하인드를 남의 하이라이트와 비교하지 말자는 다독임 (공감·위로, 구성 F) |
| 18 | Porch Light | 남성 | 송랩 (멜로딕 랩) | 100 | 주말에 내려간 고향 집, 어디까지 가든 현관 불을 켜두고 기다리는 가족 (위로·기쁨, 구성 C) |
| 19 | One More Page | 여성 | 로파이 팝 | 90 | 비 오는 밤 책상 앞, 오늘 밤에 다 끝내지 않아도 괜찮다는 다독임 (위로, 구성 I) |
| 20 | Today Was Good | 듀엣 | 모던 어쿠스틱 팝 | 98 | 하루를 마치고 나란히 걷는 밤길, 완벽하진 않아도 좋은 날로 만든 오늘 (기쁨·위로, 마무리, 구성 J) |
| 21 | Say Yes | 남성 | 인디 일렉트로닉 팝 | 110 | 망설이던 일들에 "응"이라고 해 보기로 한 해, 제일 무서웠던 선택이 제일 좋았던 순간 (기쁨·용기, 구성 K) |
| 22 | Table for One | 여성 | 칠 R&B | 88 | 혼자 들어간 식당의 "한 명이요", 어색함 끝에 알게 된 혼자만의 시간의 다정함 (공감·위로, 구성 H AABA) |
| 23 | Encore Room | 듀엣 | 청량 이지리스닝 혼성 팝 | 104 | 금요일 밤 친구들과 간 노래방, 고음은 못 올라가도 다 같이 신나서 "한 곡만 더" (기쁨, 구성 A, 42줄로 수정) |
| 24 | Run Club | 여성 | 소프트 리퀴드 드럼앤베이스 팝 | 172 | 토요일 아침 러닝 크루, 처음 만난 사람들과 보폭을 맞춰 달리는 강변 (기쁨, 구성 B) |
| 25 | Dear Twenty | 남성 | 베드룸 R&B | 86 | 스무 살의 나에게 쓰는 편지, 계획한 길은 아니어도 결국 잘 지내고 있다는 다독임 (위로, 구성 K) |
| 26 | Out Loud | 여성 | 인디 팝 (신스) | 108 | 데려다주는 길 집 앞, 머릿속으로 백 번 한 말을 처음 소리 내 말하기 직전의 설렘 (설렘·공감, 구성 F) |
| 27 | Nothing Special | 듀엣 | 칠 R&B 감성 혼성 팝 | 96 | 오래 만난 연인의 평범한 저녁, 특별한 건 없어서 더 우리 같은 시간 (공감, 구성 G) |

곡별 Styles 뒷부분:
- 01: `female vocal, acoustic pop, warm acoustic guitar, soft percussion, light handclaps, 100 BPM`
- 02: `male vocal, soft indie pop, gentle clean electric guitar, acoustic guitar, light brushed drums, 96 BPM`
- V2-01: `male vocal, mellow city pop, smooth electric piano, clean funky guitar, soft bass, light drum groove, breezy, 98 BPM`
- V2-02: `female vocal, light jazz pop, bright upright piano, walking upright bass, brushed snare, finger snaps, playful, 104 BPM`
- V2-03: `indie folk, male and female duet vocals, warm acoustic guitar, soft harmonica, gentle stomp and clap, close harmonies, 88 BPM`
- V2-04: `chill R&B, male vocal, smooth falsetto touches, warm Rhodes electric piano, warm round bass, laid-back finger snaps, soft vinyl texture, 94 BPM`
- V2-05: `acoustic pop, female vocal, bright strummed acoustic guitar, upbeat ukulele, light tambourine, handclaps, sunny beach vibe, 110 BPM`
- V2-06: `retro soul, 60s Motown feel, male vocal, warm backing vocal choir, tambourine, clean jangly guitar, soft horn section, upright piano, 100 BPM`
- V2-07: `country pop, female vocal, warm acoustic guitar, soft banjo picking, gentle pedal steel, light brushed drums, porch-night feel, 90 BPM`
- V2-08: `piano pop, male vocal, bouncy bright piano chords, light pizzicato strings, soft bass, gentle drum groove, cheerful, 106 BPM`
- V2-09: `melodic hip hop, lo-fi boom bap beat, female sung vocals, no rap, jazzy electric piano, warm round bass, soft vinyl crackle, mellow head-nod groove, 88 BPM`
- V2-10: `bossa nova pop, male vocal, soft nylon string guitar, light rim-click percussion, gentle shaker, warm flute melody, soft upright bass, 102 BPM`
- V2-11: `neo soul, female vocal, silky warm tone, lush Rhodes chords, warm round bass, soft live drums with ghost notes, gentle guitar licks, cozy, 86 BPM`
- V2-12: `soft funk, male vocal, clean chicken-scratch guitar, warm round bass groove, light clavinet, soft horn stabs, tight but gentle drums, playful, 112 BPM`
- V2-13: `indie pop, female vocal, airy dreamy tone, shimmering clean electric guitar, soft synth pad, glockenspiel accents, light drum machine, 96 BPM`
- V2-14: `chill R&B, male and female duet vocals, smooth call and response, warm Rhodes, warm round bass, soft snaps and rimshot, dreamy guitar, late night glow, 92 BPM`
- V3-01: `sunshine pop, female vocal, bright clean electric guitar, bouncy bass, light handclaps, soft glockenspiel, airy backing vocals, 104 BPM`
- V3-02: `folk pop, male vocal, warm fingerpicked acoustic guitar, soft mandolin, gentle upright bass, light shaker, homey, 90 BPM`
- V3-03: `soft synth pop, male and female duet vocals, call and response, warm analog synth pads, gentle arpeggiator, soft bass, light electronic drums, dreamy but upbeat, 110 BPM`
- V3-04: `neo soul, male vocal, smooth warm tone, soft falsetto touches, lush Rhodes chords, warm round bass, laid-back live drums, gentle wah guitar, vinyl warmth, 86 BPM`
- V3-05: `jazz pop, female vocal, playful bright tone, swinging piano, walking upright bass, brushed drums, muted trumpet accents, finger snaps, cheeky and light, 100 BPM`
- V3-06: `bedroom pop, male vocal, soft intimate close-mic vocals, lo-fi warm clean guitar, mellow synth pad, soft drum machine, gentle bass, cozy, 88 BPM`
- V3-07: `soft electro pop, female vocal, clear bright tone, clean bouncy synth plucks, crisp light beat, soft sub bass, sparkling arpeggios, airy, 104 BPM`
- V3-08: `melodic hip hop, soft trap beat, male sung vocals, smooth autotune-free melodic singing, airy guitar loop, soft hi-hats, warm round bass, mellow 808, dreamy pads, 86 BPM` (Exclude에서 heavy bass 뺌)
- V3-09: `chill house pop, male and female duet vocals, smooth trade-off verses, soft four-on-the-floor beat, warm deep house chords, gentle plucked synths, soft round bass, airy vocal chops, sunset glow, 114 BPM`
- V3-11: `alt pop, male vocal, cool laid-back tone, punchy but soft drum groove, clean bright guitar riff, bouncy synth bass, quirky percussion, playful whistles, confident, 108 BPM`
- V3-12: `alternative R&B, female vocal, silky intimate tone, layered soft harmonies, minimal moody-warm keys, warm round bass, crisp gentle trap-soul drums, subtle guitar textures, late evening glow, 90 BPM` (Exclude에서 heavy bass 뺌)
- V3-10: `folktronica, female vocal, warm gentle tone, fingerpicked acoustic guitar, soft glitchy electronic textures, light electronic beat, warm sub bass, airy synth swells, travelling feel, 92 BPM`
- V3-13: `latin pop, soft reggaeton rhythm, male vocal, warm smooth tone, light dembow groove, nylon guitar riff, warm round bass, soft congas and shaker, breezy summer-evening feel, 98 BPM` (Exclude에서 heavy bass 뺌)
- V3-14: `easy listening K-pop style girl group pop, Y2K feel, female vocals with light group harmonies, airy breathy tone, soft UK garage 2-step beat, glossy synth plucks, warm round bass, dreamy pads, playful but calm, 112 BPM`
- V3-15: `melodic hip hop, lo-fi beat, male and female duet sung vocals, no rap, soft call and response, dusty warm keys, mellow jazzy guitar loop, warm round bass, soft vinyl texture, late night calm, 86 BPM` (Exclude에서 heavy bass 뺌)
- V3-16: `easy listening K-pop style boy group pop, male vocals with soft group harmonies, bright clean tone, groovy light funk guitar, bouncy synth bass, crisp gentle drums, catchy vocal post-chorus hook, fresh and upbeat but calm, 108 BPM`
- V3-17: `R&B pop, female vocal, warm silky tone, soft layered harmonies, smooth Rhodes and soft synth pads, warm round bass, crisp laid-back drums, gentle guitar licks, instrumental break with mellow keys solo, comforting late night mood, 94 BPM` (Exclude에서 heavy bass 뺌)
- V3-18: `melodic hip hop, male vocal, melodic sing-song rap verses, soft relaxed flow, no aggressive delivery, sung warm chorus, mellow guitar and soft keys, warm round bass, laid-back boom bap beat, nostalgic and warm, 100 BPM` (Exclude에서 rap, heavy bass 뺌)
- V3-19: `lo-fi pop, female vocal, soft breathy close-mic tone, dusty lo-fi drums, warm muted keys, mellow guitar loop, soft rain ambience, warm round bass, repeating hook, cozy study night, 90 BPM`
- V3-20: `modern acoustic pop, male and female duet vocals, alternating lines conversation, warm fingerpicked and strummed acoustic guitars, soft piano, light stomp and clap, warm round bass, gentle group humming outro, cozy night walk, 98 BPM`
- V3-21: `indie electronic pop, male vocal, warm airy tone, shimmering synth arpeggios, clean guitar plucks, punchy but soft electronic drums, warm round bass, uplifting and fresh, long instrumental outro with synth melody, 110 BPM`
- V3-22: `chill R&B, female vocal, smooth intimate tone, warm Rhodes chords, soft muted guitar, warm round bass, gentle laid-back drums, subtle strings, storytelling AABA form, cozy evening, instrumental outro, 88 BPM` (Exclude에서 heavy bass 뺌)
- V3-23: `fresh easy listening K-pop style co-ed duet pop, male and female vocals trading lines, bright airy tone, soft electronic beat, glossy synth plucks, warm round bass, playful group chant hook, clean modern sound, 104 BPM`
- V3-24: `soft liquid drum and bass pop, female vocal, airy breathy tone, gentle rolling breakbeat, half-time feel, warm sub bass kept soft, lush pads, shimmering keys, uplifting morning energy, post-chorus vocal hook, 172 BPM`
- V3-25: `bedroom R&B, male vocal, soft warm intimate tone, gentle falsetto, mellow electric piano, soft muted guitar, warm round bass, laid-back soft drums, late night letter mood, long instrumental outro with keys, 86 BPM` (Exclude에서 heavy bass 뺌)
- V3-26: `indie pop, female vocal, bright sweet airy tone, shimmering synth pads, bouncy plucked synths, soft punchy drums, warm round bass, fluttery heartbeat feel, short instrumental break with synth melody, 108 BPM`
- V3-27: `chill R&B flavored co-ed duet pop, male and female vocals trading verses, warm smooth tones, soft electric piano, mellow synth pads, warm round bass, gentle laid-back beat, cozy evening at home, 96 BPM`
- 03: `female vocal, bossa nova pop, nylon string guitar, soft ukulele, light shaker, gentle whistling melody, 92 BPM`

다음 곡 후보 방향: 남성 또는 듀엣 보컬, 칠 R&B, 재즈 팝, 잔잔한 시티팝, 피아노 팝, 인디 포크

## VOL.04 (크리스마스 편, 파일 61~80, 곡 순서 = 에너지 곡선, `playlists/vol04/PLAN.md`)
| # | 제목 | 보컬 | 장르 | BPM | 한 줄 소개 |
|---|---|---|---|---|---|
| 61 | Snow on the Sill | 여성 | 윈터 베드룸 팝 | 84 | 밤새 내린 첫눈, 단톡방에 쏟아지는 같은 사진과 아무도 안 밟은 길에 찍는 첫 발자국 (기쁨, 구성 E, 32줄+인트로 → 2:54) |
| 62 | Humming on the 8:15 | 남성 | 윈터 인디 팝 | 96 | 12월 아침 꽉 찬 지하철, 이어폰에서 새어 나온 캐롤을 다 같이 흥얼거리는 출근길 (공감, 구성 B, 38줄 → 2:52) |
| 63 | Cinnamon and You | 듀엣 | 어쿠스틱 팝 | 104 | 크리스마스 마켓 데이트, 김 오르는 컵과 이름이 틀린 진저브레드, 차가운 손을 놓지 못한 밤 (기쁨, 구성 G, 40줄) |

곡별 Styles 앞부분:
- V4-61: `bedroom pop, female vocal, soft breathy close-mic vocals, warm clean electric guitar, mellow Rhodes, soft celesta and sleigh bell accents, gentle drum machine, soft bass, cozy first snow morning, 84 BPM`
- V4-62: `indie pop, male vocal, warm friendly tone, jangly clean electric guitar, bouncy bass, light tambourine and sleigh bells, crisp soft drums, glockenspiel hook, cozy city winter morning, 96 BPM`
- V4-63: `acoustic pop, male and female duet vocals, sweet trade-off verses, close harmonies in the chorus, bright strummed acoustic guitar, warm upright bass, light brushed drums, sleigh bells and soft glockenspiel, gentle handclaps, Christmas market warmth, 104 BPM`

사용한 핵심 표현 (VOL.04):
- 61 Snow on the Sill: snow on the sill, the group chat woke up early, footprints by the door, a window and a warm cup, counting down to twenty-five
- 62 Humming on the 8:15: humming on the 8:15, the same tune, squeezed in tight, Santa hat barista, December's riding with us, nine to five
- 63 Cinnamon and You: cinnamon and you, colder than mine so I didn't let it go, glass star, gingerbread hearts, one more lap around the square

## 사용한 핵심 표현 (VOL.03)
- 01 Line Dried: line dried, sun kissed, hung up all my worries, brand new day, pegs, basket, billowing sails
- 02 Balcony Tomatoes: little by little(⚠ VOL.01 곡 제목과 겹침), good things grow, turning red, watering can
- 03 Voice Note: little red dot, your ordinary sings, ten seconds long, press and hold
- 04 B-Side: flip it over, gold on the B-side, never made it to the radio, crates, needle
- 05 Crossword in Pen: in pen, seven down / twelve across, ink smudge, eraser
- 06 Glow-in-the-Dark Stars: little galaxy, telescope, constellation, hum of the radio(⚠ radio 반복)
- 07 Save Point: save point, click, checkpoint, loading, level up, song on the radio(⚠ radio 반복)
- 08 Do Not Disturb: do not disturb, moon on my screen, notifications, unread, airplane mode, recharge
- 09 Rooftop Hours: rooftop hours, pink to purple, city hums below, string lights, shoes kicked off, stay till the sky turns
- 11 Fresh Cut: fresh cut, barber chair, mirror, neck feels the breeze, walking taller, new me same heart
- 12 Soft Reset: soft reset, candle, sheet mask, fresh pillowcase, lavender, starting over gently
- 10 Day Trip Ticket: day trip ticket, one-way morning, fields rolling by, platform, tunnel, solo, back by midnight
- 13 Fountain Square: fountain square, meet me by the water, coins in the fountain, one more song, old couple dancing, sway till the speakers stop
- 14 Same Page: same page, same text same time, half a look, finish my sentence, typing at once, you get me
- 15 Made It Home: made it home, didn't win today, cup noodles, corner store light, last bus, one more day done
- 16 Laptop Closed: laptop closed, friday evening, held it all week, let it go, weekend starts now, no alarm
- 17 Highlight Reel: highlight reel, behind-the-scenes, scrolling at 2am, filters, my own timeline, put the phone down
- 18 Porch Light: porch light on, hometown, three hours on the highway, did you eat, same corner same jokes, eat well sleep well
- 19 One More Page: one more page, one more sip, tea gone cold, desk lamp, you don't have to finish it all tonight, half a chapter
- 20 Today Was Good: today was good, not every day is perfect, we made this one good, walking you home, see you tomorrow
- 21 Say Yes: say yes, scariest yes, signed up, solo trip, said hi first, maybe turned into yes
- 22 Table for One: table for one, just me tonight, good company, I just forgot, window seat, dessert for myself
- 23 Encore Room: encore room, nobody hits the high note, everybody sings, tambourine, mic passed around, last song for real
- 24 Run Club: run club, saturday 7am, same pace, we run to feel alive, breathing in time, high five at the finish
- 25 Dear Twenty: dear twenty, not the way you planned, you'll find your way, the ones who stay, you did okay
- 26 Out Loud: out loud, a hundred times inside my head, walking you home, porch steps, three little words, don't go in yet
- 27 Nothing Special: nothing special, that's what makes it ours, shared blanket, fell asleep on the show, delivery at the door, same old couch

## K팝 테스트 (한국어 가사)
| 번호 | 제목 | 보컬 | 장르 | BPM | 내용 |
|---|---|---|---|---|---|
| K-TEST-01 | 오늘부터 다르게 | 여자(걸그룹 느낌) | 아이돌 이지리스닝 K팝 | 102 | 오래된 친구와 걷던 밤, 친구에서 연인이 되는 순간 (기쁨) |
| K-TEST-02 | It's a Date | 남자(보이그룹 느낌) | 청량 신스팝 K팝 | 116 | 첫 데이트 전날 밤, 기다리던 답장 (기쁨, 후렴으로 시작) |
| K-TEST-03 | 알람 없는 아침 | 여자 솔로 | K-R&B | 84 | 알람 없이 눈뜬 날, 아무것도 안 해도 괜찮은 하루 (위로, AABA) |
| K-TEST-04 | 새벽 두 시 수다 | 여자(걸그룹 느낌) | 2-step 개러지 K팝 | 128 | 퇴근 후 친구 집 앞, 새벽까지 이어지는 수다 (공감, 반복 훅) |
- Styles: `K-pop girl group easy listening, bright soft female vocals, Korean lyrics with a short English hook, airy synth pads, soft plucked synths, clean modern drums, warm round bass, light groove, night walk butterflies, 102 BPM`
- 사용한 핵심 표현: 친구라는 말로는 부족해, Walk with me tonight, 가로등 아래 그림자, 반 줄까, 한 바퀴만 더 걷자
- Styles 02: `K-pop boy group easy listening, fresh clear male vocals, Korean lyrics with a short English hook, bright synth pop, sparkling synths, crisp modern drums, warm round bass, light bouncy groove, late night butterflies before a first date, 116 BPM`
- Styles 03: `K-R&B, soft female solo vocal, Korean lyrics, warm intimate tone, soft electric piano, mellow synth pads, warm round bass, slow laid-back groove, lazy sunny morning, 84 BPM`
- Styles 04: `K-pop girl group easy listening, light airy female vocals, Korean lyrics with a short English hook, soft modern 2-step garage beat, shuffling hi-hats, airy synth chords, warm round bass, late night city friends, 128 BPM`
- 사용한 핵심 표현 02: it's a date, 내일 몇 시에 볼까, 읽음 표시, 쓰다 지운 말, 내일 봐 세 글자
- 사용한 핵심 표현 03: 알람 없이 눈을 뜬 아침, 오늘의 나는 이걸로 충분해, take it slow, 내일의 나는 내일 걱정할게
- 사용한 핵심 표현 04: 새벽 두 시, talk all night, 우리만 아는 농담, 편의점 봉지, 나쁘지 않은 어른
