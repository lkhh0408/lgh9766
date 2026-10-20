# -*- coding: utf-8 -*-
"""
네이버페이 부동산(fin.land.naver.com) 데이터 주소 확인용 프로그램

브라우저에서 단지 → 매물 목록 → 매물 하나를 클릭하는 동안
사이트가 주고받는 데이터를 api_log.txt 에 기록합니다.
"""
import json
import sys
from pathlib import Path

START_URL = "https://fin.land.naver.com/"
MAX_BODY = 6000
SKIP_HEADERS = {"cookie", "set-cookie"}


def main():
    from playwright.sync_api import sync_playwright

    log_path = Path(__file__).resolve().parent / "api_log.txt"
    out = open(log_path, "w", encoding="utf-8")
    count = [0]

    def on_response(resp):
        url = resp.url
        if "land.naver.com" not in url:
            return
        ctype = resp.headers.get("content-type", "")
        if "json" not in ctype:
            return
        req = resp.request
        try:
            body = resp.text()
        except Exception:
            body = "(읽기 실패)"
        entry = {
            "method": req.method,
            "url": url,
            "status": resp.status,
            "request_headers": {k: v for k, v in req.headers.items() if k.lower() not in SKIP_HEADERS},
            "post_data": req.post_data,
            "response": body[:MAX_BODY],
        }
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")
        out.flush()
        count[0] += 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="ko-KR", viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.on("response", on_response)
        page.goto(START_URL, wait_until="domcontentloaded", timeout=60000)

        print("", flush=True)
        print("=" * 60)
        print("열린 크롬 창에서 아래 순서대로 클릭해 주세요.")
        print(" 1. 검색창에 '운정' 같은 아파트 이름을 넣고 단지 하나를 엽니다")
        print("    (예: 운정신도시 아이파크, 힐스테이트 운정 등)")
        print(" 2. 그 단지의 '매물' 목록을 엽니다 (전세/월세 선택해 보면 더 좋습니다)")
        print(" 3. 매물 하나를 클릭해서 중개사 정보(전화번호)가 보이게 합니다")
        print(" 4. 지도 화면도 한 번 열어 운정중앙역 근처를 움직여 봅니다")
        print("다 했으면 이 검은 창을 클릭하고 Enter 키를 누르세요.")
        print("=" * 60, flush=True)
        input()

        browser.close()
    out.close()
    print(f"기록 {count[0]}건 저장: {log_path}")
    print("이 api_log.txt 파일을 채팅에 첨부해서 보내주세요.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        print("")
        print("오류가 발생했습니다. 위 내용을 복사해서 보내주세요.")
        sys.exit(1)
