# Suno 곡 기록

"다음 곡"을 요청하면 이 기록을 보고 장르, 보컬, 주제가 겹치지 않게 다음 곡을 만들어요.

## 공통 규칙
- 장르나 시간대(아침, 저녁 등)로 채널을 나누지 않아요. 영상 제목은 CLAUDE.md의 '쓰임새 중심' 규칙을 따라요.
- 영어 팝송이고 가사는 반드시 넣어요. 긍정적인 내용만 쓰고, 곡 길이는 3분 이내예요.
- 히트곡 느낌은 내되, 카페나 공부, 일할 때 틀어도 자극적이지 않아야 해요. 고음은 괜찮지만 내지르면 안 돼요.
- 가사는 모두 새로 쓴 창작 가사예요. 실제 곡의 가사, 제목, 가수 이름은 쓰지 않아요.
- 곡마다 Title, 장르, BPM, Styles, Exclude, Lyrics, 곡 소개(멜론 앨범 소개 스타일)를 함께 만들어요.

**Styles 구성 (VOL.02부터)**: `곡별 장르 부분` + `공통 뒷부분`. 장르가 맨 앞에 와야 Suno가 장르 색을 살려요.

**공통 Styles (뒷부분)**
```
catchy but gentle melody, easy listening, warm feel-good vibe, positive, smooth relaxed vocals, mellow dynamics, consistent volume, background music friendly, short song under 3 minutes
```

**Exclude**
```
belting, shouting, screaming, aggressive, loud drums, heavy bass, EDM drop, sudden loud parts, distortion, rock, rap, sad, dark, explicit lyrics
```
- R&B, 멜로딕 힙합 곡은 `heavy bass`를 빼고 Styles에 `warm round bass`를 넣어요. `rap`은 항상 막아요(힙합은 비트만, 보컬은 노래).

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
| 2 | 포크 팝 | 남 | 90 |
| 3 | 소프트 신스 팝 | 듀엣 | 110 |
| 4 | 네오소울 (환기) | 남 | 86 |
| 5 | 재즈 팝 | 여 | 100 |
| 6 | 베드룸 팝 | 남 | 88 |
| 7 | 아프로팝 | 여 | 104 |
| 8 | 멜로딕 힙합 (환기, 소프트 트랩 비트) | 남 | 86 |
| 9 | 칠 하우스 팝 | 듀엣 | 114 |
| 10 | 드림 팝 | 여 | 92 |
| 11 | 얼트 팝 | 남 | 108 |
| 12 | 얼터너티브 R&B (환기) | 여 | 90 |
| 13 | 라틴 팝 (소프트 레게톤 리듬) | 남 | 98 |
| 14 | Y2K 팝 (소프트 2-step 비트) | 여 | 112 |
| 15 | 멜로딕 힙합 (환기, 로파이) | 듀엣 | 86 |
| 16 | 인디 팝 | 남 | 108 |
| 17 | R&B 팝 | 여 | 94 |
| 18 | 소프트 아마피아노 | 남 | 110 |
| 19 | 로파이 팝 | 여 | 90 |
| 20 | 모던 어쿠스틱 팝 (마무리) | 듀엣 | 98 |
- VOL.03부터 컨트리, 브라스, 보사, 레게, 시티팝, 디스코 같은 옛날 느낌 장르는 빼고 요즘 장르(베드룸 팝, 아프로팝, 칠 하우스, 얼트 R&B, 아마피아노 등)를 넣어요. 리듬이 강한 장르도 `heavy bass`는 계속 막고 `warm round bass`, 부드러운 비트로 배경음악 느낌을 지켜요.

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
| 07 | Market Colors | 여성 | 아프로팝 | 104 | 망고와 꽃무늬 천이 가득한 주말 시장, 골목마다 리듬이 흐르는 산책 |

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
- V3-07: `afropop, female vocal, warm sunny tone, smooth afrobeats groove, soft shaker and light congas, clean highlife guitar licks, warm round bass, gentle synth pads, breezy, 104 BPM`
- 03: `female vocal, bossa nova pop, nylon string guitar, soft ukulele, light shaker, gentle whistling melody, 92 BPM`

다음 곡 후보 방향: 남성 또는 듀엣 보컬, 칠 R&B, 재즈 팝, 잔잔한 시티팝, 피아노 팝, 인디 포크
