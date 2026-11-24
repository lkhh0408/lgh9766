"""DistroKid upload tutorial (Korean) -> tutorial.html; render to PDF with render_pdf.js."""
import os
D = os.path.dirname(os.path.abspath(__file__))
FS = 'file:///tmp/claude-0/-home-user-lgh9766/b52f1d6d-22f0-5bcd-a4bc-05ad7db7a50f/scratchpad/chimg/node_modules/@fontsource'

def img(n, cap='', w=100):
    return f'<figure><img src="img/{n:02d}.png" style="max-width:{w}%"><figcaption>{cap}</figcaption></figure>' if cap else f'<figure><img src="img/{n:02d}.png" style="max-width:{w}%"></figure>'

def table(rows, head=('항목', '입력')):
    h = ''.join(f'<th>{x}</th>' for x in head)
    b = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'

def tip(t, kind='tip'): return f'<div class="{kind}">{t}</div>'

S = []
S.append(f'''<section class="cover">
<div class="kicker">OPEN TO CLOSE · 음원 유통 가이드</div>
<h1>디스트로키드로<br>앨범 올리기</h1>
<p class="sub">Haru's Playlist 01을 올린 순서 그대로 정리했어요.<br>다음 앨범(02~)도 이 순서대로 따라 하면 돼요.</p>
<img class="cv" src="../../playlists/vol01/album/cover.jpg">
<div class="toc"><b>차례</b><ol>
<li>시작 전 준비물</li><li>요금제 고르기</li><li>계정 정보</li><li>앨범 정보</li><li>스포티파이 아티스트 선택</li>
<li>트랙 정보 (20곡 공통)</li><li>애플 뮤직 크레딧</li><li>추가 기능과 필수 체크박스</li><li>Mixea 마스터링</li>
<li>제출 완료 화면</li><li>가사 올리기</li><li>계정 메뉴와 프로필</li><li>마지막 점검 5가지와 다음 할 일</li></ol></div>
</section>''')

S.append('<section><h2><span>1</span>시작 전 준비물</h2>' + table([
    ['앨범 커버', '3000×3000 JPG. 매번 다른 디자인, 하루(Haru) 이름을 그림 속에 넣어요. 글자는 앨범 이름과 똑같이.'],
    ['곡 파일', 'WAV 20곡 (16비트 44.1kHz 이상). 01~04는 MP3를 WAV로 바꿔서 쓰고, 05부터는 Suno에서 WAV를 함께 받아요.'],
    ['가사', '곡마다 txt. [Verse], [Chorus] 같은 구간 이름은 빼고, 줄 끝 쉼표·마침표 없이, 줄 첫 글자는 대문자.'],
    ['앨범 이름', "<code>Haru's Playlist 0X</code> (예: Haru's Playlist 01)"],
    ['아티스트 이름', '<code>Open to Close</code>'],
    ['곡 순서', '유튜브 영상 순서 그대로 (파일 번호 = 트랙 번호)'],
    ['발매일', '금요일. 등록은 최소 2~3주 전(연말엔 더 일찍).'],
], ('준비물', '내용')) + tip('저장소의 <code>playlists/vol0X/album/</code> 폴더에 커버, 가사, 등록 정보(<code>release_info.txt</code>)를 모아 둬요.') + '</section>')

S.append('<section><h2><span>2</span>요금제 고르기</h2>' + img(1, '요금제 화면', 80) +
    tip('<b>Musician Plus (1년 $44.99)</b>를 골라요. 기본 Musician에는 <b>발매일 지정</b>이 없어서, 금요일 발매나 스포티파이 신곡 추천 신청(발매 7일 전)을 맞출 수 없어요.') +
    '<p>Ultimate($89.99)의 음원 교체, 고급 통계는 지금은 필요 없어요.</p></section>')

S.append('<section><h2><span>3</span>계정 정보</h2>' + img(2, '이름 입력', 70) + table([
    ['이름', '이름만 영어로, 여권과 같게 (예: Gildong)'],
    ['중간 이름', '비워 둬요'],
    ['성', '성만 영어로 (예: Hong)'],
    ['상호명', '사업자 등록이 없으면 비워 둬요 (Open to Close는 여기가 아니라 아티스트 이름 칸에)'],
]) + img(3, '약관 체크', 70) + '<p>두 개 모두 체크해요. 두 번째(최대 30% 공제)는 "이런 경우가 있다는 걸 이해했다"는 확인일 뿐이에요. 나중에 세금 정보(W-8BEN)를 내면 한국 기준으로 줄어들어요.</p></section>')

S.append('<section><h2><span>4</span>앨범 정보</h2>' + img(4, '스트리밍 서비스 · 곡 수 · 소셜 미디어 팩', 90) + table([
    ['스트리밍 서비스', '체크된 그대로 (Snapchat, Roblox는 안 해도 돼요)'],
    ['곡 수', '20곡'],
    ['소셜 미디어 팩', '<b class="no">❌ 체크하지 않아요</b>'],
    ['기존에 발매된 앨범인가요?', '아니요'],
]) + tip('<b>소셜 미디어 팩 = 유튜브 콘텐츠 ID.</b> 켜면 우리 유튜브 영상과 쇼츠, 출처를 남기고 쓰는 다른 사람 영상에도 저작권 신고가 걸려요. 절대 켜지 않아요.', 'warn') +
    img(5, '아티스트 · 발매일 · 음반사 · 언어 · 장르', 80) + table([
    ['Ultimate 업그레이드', '"아니요, 괜찮습니다"'],
    ['아티스트/밴드 이름', '<code>Open to Close</code>'],
    ['발매일', '금요일 날짜 (01은 <code>2026-12-11</code>)'],
    ['음반사', '<code>Open to Close</code> (비우면 DistroKid.com으로 나가요)'],
    ['앨범 판매가', '$9.99 그대로'],
    ['언어', 'English'],
    ['주요 장르 / 보조 장르', 'Pop / 비워 둠'],
]) + img(12, '발매 시간 · 사전 주문', 85) + table([
    ['국가별 발매 시간', '첫 번째(기본값): 청취자 시간대 기준 오전 12:00 → 나라마다 금요일 0시에 열려요'],
    ['사전 주문', '아니요'],
]) + tip('12:00 AM = 자정(0시). 12:00 PM은 낮 12시라 고르지 않아요.') +
    img(6, '앨범 표지 · AI 아트워크 · 앨범 제목', 85) + table([
    ['앨범 표지', '커버 JPG 업로드'],
    ['이 아트워크는 대부분 AI가 생성했나요?', '<b>네</b> (AI가 그린 그림이면 네, 사진 보정에만 썼으면 아니요)'],
    ['앨범 제목', "<code>Haru's Playlist 0X</code>"],
]) + '</section>')

S.append('<section><h2><span>5</span>스포티파이 아티스트 선택</h2>' + img(11, '이미 등록된 아티스트인가요?', 85) +
    tip('<b>"이번이 본인의 첫 Open to Close Spotify 발매입니다"</b>를 골라요. 목록의 "Open To Close (Summer 2021)"는 다른 사람이에요. 다음 앨범부터는 우리 프로필이 목록에 나오니 그걸 고르면 돼요.') +
    '<p>스포티파이에서 같은 이름이 두 개 검색되니, 유튜브 설명란에 우리 링크를 직접 걸어 둬요.</p></section>')

S.append('<section><h2><span>6</span>트랙 정보 (20곡 공통)</h2><p>곡 제목과 오디오 파일만 곡마다 바뀌고, 나머지는 20곡 모두 같아요.</p>' + img(7, '곡 제목 · 버전 · 오디오 파일', 80) + table([
    ['곡 제목', '제목만 (번호, 곡 길이, 연도 넣지 않기). 예: <code>Good Side of the Street</code>'],
    ['피처링 아티스트', '아니요'],
    ['버전 정보', '아니요, 일반 버전'],
    ['ISRC', '비워 둠 (자동 생성)'],
    ['오디오 파일', '같은 번호의 WAV'],
    ['Dolby Atmos', '아니요'],
    ['자작곡 / 커버 곡', '원곡입니다'],
]) + img(8, '작곡가 · Explicit · AI · 미리 듣기 · 판매가', 80) + table([
    ['작곡가/작사가의 본명', '"작곡 및 작사" + 본인 실명(영어) → <b>"앨범의 모든 트랙에 복사하기"</b>'],
    ['Explicit / Radio Edit', '아니요 / 아니요'],
    ['연주곡인가요?', '가사가 포함된 곡입니다'],
    ['AI 생성 음악·보컬·가사', '<b>네</b>'],
    ['미리 듣기 시작 시간', '스트리밍 서비스 측에서 설정'],
    ['트랙 판매가', '$0.99 그대로'],
]) + '<div class="two">' + img(13, 'AI 부분 선택') + img(14, '아티스트 유형') + '</div>' + table([
    ['가사 / 작곡 / 모든 오디오', '✅ ✅ ✅'],
    ['오디오 일부', '체크 안 함'],
    ['Apply these selections to all songs', '✅ (20곡에 한 번에 적용)'],
    ['인간 아티스트인가요, AI 페르소나인가요?', '<b>인간 아티스트 또는 그룹</b> (Open to Close는 사람이 운영하는 이름, 하루(Haru)는 마스코트)'],
]) + '</section>')

S.append('<section><h2><span>7</span>애플 뮤직 크레딧 (필수)</h2>' + img(15, 'Apple Music 추가 요구 사항 · 추가 기능', 80) + img(17, '연주자 · 프로듀서 입력 칸', 55) + table([
    ['연주자', '역할 <b>노래 &amp; 보컬</b> / 이름 <code>Open to Close</code> → "모든 트랙에 복사하기"'],
    ['프로듀서', '역할 <b>총괄 프로듀서</b> / 이름 본인 실명(영어) → 모든 트랙에 복사'],
], ('칸', '입력')) + img(25, '역할 목록: "노래 & 보컬"은 색소폰, 쉐이커 바로 아래 (영어 알파벳 순서)', 35) +
    tip('"백그라운드 보컬", "보컬 반주"는 코러스·화음용이라 고르지 않아요.') + '</section>')

S.append('<section><h2><span>8</span>추가 기능과 필수 체크박스</h2>' + table([
    ['레거시 남기기 ($49)', '안 함. 앨범이 쌓이면 나중에 생각'],
    ['디스커버리 팩', '안 함'],
    ['음원 사이트 맥시마이저', '안 함'],
    ['DistroVid', '안 함 (유튜브는 직접 올려요)'],
    ['라우드니스 정규화', '안 함 (Suno 곡은 이미 충분히 크고, 잡음 위험)'],
    ['소셜 미디어 팩', '<b class="no">❌ 절대 안 함</b>'],
], ('기능', '선택')) + '<p>합계가 <b>$0.00</b>인지 확인해요.</p>' + img(29, '필수 체크박스 5개 모두 체크', 85) + '</section>')

S.append('<section><h2><span>9</span>Mixea 마스터링</h2>' + img(30, '마스터링 판매 화면', 60) +
    tip('<b>"원본 버전을 사용하세요 ($0)"</b>를 골라요. Suno 곡은 이미 마스터링돼 있고, 원본이 MP3라 24비트로 바꿔도 음질은 그대로예요. 자동 마스터링은 고음이 거칠어지거나 잡음이 생길 수 있어요.') + '</section>')

S.append('<section><h2><span>10</span>제출 완료 화면</h2>' + img(31, '제출 완료', 85) +
    '<ul><li>발매일과 스포티파이 공개 시간(12:00 AM)이 맞는지 확인해요.</li><li><b>HyperFollow 링크</b>를 복사해 둬요. 01: <code>https://distrokid.com/hyperfollow/opentoclose/harus-playlist-01</code></li><li>발매일에 유튜브 설명란과 고정 댓글에 넣어요.</li></ul></section>')

S.append('<section><h2><span>11</span>가사 올리기</h2>' + img(32, '가사 업로드 화면', 80) +
    '<ul><li>같은 번호 가사 파일 내용을 그대로 붙여 넣어요.</li><li>음원 사이트는 <b>Basic (무료)</b>. Lyric Blaster($21.99/년)는 안 사요. 스포티파이 가사는 발매 후 Musixmatch에 무료로 등록해요.</li><li>약관 체크 → 가사 저장하기</li></ul>' +
    img(34, '저장 후 상태: 노란 물음표 = 확인 중, 초록 체크 = 완료, 회색 = 아직 안 넣음', 70) +
    tip('<b>싱크 가사</b>는 노래를 틀고 줄마다 스페이스바를 직접 눌러 맞추는 방식이라 시간이 많이 걸려요. 애플 뮤직에만 보이는 선택 기능이라 건너뛰어도 돼요.') + '</section>')

S.append('<section><h2><span>12</span>계정 메뉴와 프로필</h2>' + img(36, '계정 메뉴', 35) + table([
    ['지급 수단', '<b>첫 출금 때</b> 정해요. 수익은 Bank 탭에 쌓여요. 페이팔 추천(영어 실명 일치). 이때 세금 정보(W-8BEN)도 함께 내요.'],
    ['개인 프로필', '선택. 아래처럼 채워요.'],
    ['나머지', '친구 추천·신용카드·영수증·커버 곡 라이선스는 그대로'],
], ('메뉴', '할 일')) + '<div class="two">' + img(37, '프로필 1') + img(38, '프로필 2') + '</div>' + table([
    ['이름', '<code>Open to Close</code>'],
    ['소개 문구', 'Music for your day, from open to close 🎧 / Every playlist is a new trip with Haru (하루). / Playlists on YouTube: youtube.com/@OpentoClose_day'],
    ['거주 도시', '비워 둠'],
    ['프로필 사진', '유튜브 채널 프로필과 같은 이미지 (<code>branding/profile_800.png</code>)'],
    ['SNS', 'YouTube만 (<code>https://youtube.com/@OpentoClose_day</code>), 없는 계정 칸은 비움'],
    ['좋아하는 장르', '팝, R&amp;B/소울, 댄스'],
    ['영향을 준 아티스트', '비워 둠'],
]) + '</section>')

S.append('<section><h2><span>13</span>마지막 점검 5가지와 다음 할 일</h2><div class="check"><ol>'
    '<li><b>발매일</b>이 금요일 날짜인지 (ASAP이면 바로 발매돼요)</li>'
    '<li><b>소셜 미디어 팩</b>이 꺼져 있는지</li>'
    '<li><b>스포티파이 아티스트</b>를 맞게 골랐는지 (01은 "첫 발매", 다음부터는 우리 프로필)</li>'
    '<li><b>곡 제목과 WAV 파일</b>이 번호마다 맞는지</li>'
    '<li><b>AI 크레딧</b>(가사·작곡·모든 오디오)이 20곡 모두 적용됐는지</li></ol></div>'
    + table([
    ['스포티파이 등록 메일이 오면', 'Spotify for Artists에서 프로필 등록 + 신곡 추천 1곡 신청 (발매 7일 전까지, 01은 12/4)'],
    ['발매일', '유튜브 설명란·고정 댓글에 HyperFollow 링크'],
    ['발매 후', 'Musixmatch에 가사 등록 (스포티파이 가사)'],
    ['첫 출금 때', '지급 수단 + 세금 정보(W-8BEN)'],
], ('언제', '할 일')) + '</section>')

css = f'''@font-face{{font-family:N;src:url({FS}/noto-sans-kr/files/noto-sans-kr-korean-400-normal.woff2)}}
@font-face{{font-family:N;font-weight:900;src:url({FS}/noto-sans-kr/files/noto-sans-kr-korean-900-normal.woff2)}}
@font-face{{font-family:O;font-weight:800;src:url({FS}/outfit/files/outfit-latin-800-normal.woff2)}}
@page{{size:A4;margin:16mm 15mm}}
body{{font-family:N,sans-serif;color:#1F2340;font-size:10.5pt;line-height:1.6;margin:0}}
section{{break-before:page}} section.cover{{break-before:auto;text-align:center;padding-top:10mm}}
.kicker{{font-family:O;letter-spacing:3px;color:#E0457B;font-size:10pt}}
h1{{font-weight:900;font-size:30pt;line-height:1.2;margin:6mm 0 4mm}} .sub{{color:#555}}
.cv{{width:62mm;border-radius:6px;box-shadow:0 4px 14px rgba(0,0,0,.18);margin:6mm 0}}
.toc{{text-align:left;background:#FFF6E0;border-radius:8px;padding:4mm 8mm;margin:0 18mm}} .toc ol{{columns:2;margin:2mm 0 0;padding-left:5mm}}
h2{{font-weight:900;font-size:17pt;margin:0 0 4mm;display:flex;align-items:center;gap:3mm}}
h2 span{{font-family:O;background:#E0457B;color:#fff;border-radius:50%;width:9mm;height:9mm;display:inline-flex;align-items:center;justify-content:center;font-size:13pt}}
figure{{margin:3mm 0;text-align:center;break-inside:avoid}} figure img{{border:1px solid #ddd;border-radius:4px;max-height:118mm;width:auto}}
figcaption{{font-size:8.5pt;color:#777;margin-top:1mm}}
table{{width:100%;border-collapse:collapse;margin:3mm 0;break-inside:avoid;font-size:9.8pt}}
th{{background:#1F2340;color:#fff;text-align:left;padding:2mm 3mm}} td{{border-bottom:1px solid #e5e5e5;padding:1.8mm 3mm;vertical-align:top}}
td:first-child{{width:34%;font-weight:900}}
code{{background:#F1F1F5;border-radius:3px;padding:0 1.2mm;font-size:9.5pt}}
.tip{{background:#EAF4FF;border-left:4px solid #2F5BEA;padding:3mm 4mm;border-radius:4px;margin:3mm 0;break-inside:avoid}}
.warn{{background:#FFECEF;border-left:4px solid #E0457B;padding:3mm 4mm;border-radius:4px;margin:3mm 0;break-inside:avoid}}
.no{{color:#C62E2E}} .two{{display:flex;gap:4mm;align-items:flex-start}} .two figure{{flex:1}} .two img{{max-width:100%}}
.check{{background:#FFF6E0;border-radius:8px;padding:3mm 6mm;font-size:11pt}}'''
open(os.path.join(D, 'tutorial.html'), 'w', encoding='utf-8').write(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>디스트로키드 앨범 올리기</title><style>{css}</style></head><body>{"".join(S)}</body></html>')
print('ok')
