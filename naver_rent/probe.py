# -*- coding: utf-8 -*-
"""
네이버 부동산 데이터 주소 확인용 프로그램

PC에 설치된 크롬(없으면 엣지)을 일반 창으로 띄우고 그 창에 연결해서,
사용자가 단지 → 매물 목록 → 매물 하나를 클릭하는 동안
사이트가 주고받는 데이터를 api_log.txt 에 기록합니다.
"""
import json
import sys
from pathlib import Path

from browser_util import connect, launch_browser

START_URL = "https://land.naver.com/"
MAX_BODY = 6000
SKIP_HEADERS = {"cookie", "set-cookie"}


def main():
    from playwright.sync_api import sync_playwright

    here = Path(__file__).resolve().parent
    log_path = here / "api_log.txt"
    out = open(log_path, "w", encoding="utf-8")
    count = [0]

    def on_response(resp):
        url = resp.url
        if "naver.com" not in url:
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

    def on_page(page):
        page.on("framenavigated",
                lambda f: f == page.main_frame and out.write(
                    json.dumps({"page": f.url}, ensure_ascii=False) + "\n"))

    proc = launch_browser(here, START_URL)
    with sync_playwright() as p:
        browser = connect(p)
        context = browser.contexts[0]
        context.on("response", on_response)
        context.on("page", on_page)
        for pg in context.pages:
            on_page(pg)

        print("", flush=True)
        print("=" * 60)
        print("열린 브라우저 창에서 아래 순서대로 클릭해 주세요.")
        print(" 1. 네이버 부동산에서 운정의 아파트 단지 하나를 엽니다")
        print(" 2. 그 단지의 '매물' 목록을 엽니다 (전세/월세 선택해 보면 더 좋습니다)")
        print(" 3. 매물 하나를 클릭해서 중개사 정보(전화번호)가 보이게 합니다")
        print(" 4. 지도에서 운정중앙역 근처를 한 번 움직여 봅니다")
        print("다 했으면 이 검은 창을 클릭하고 Enter 키를 누르세요.")
        print("=" * 60, flush=True)
        input()
        browser.close()
    out.close()
    try:
        proc.terminate()
    except Exception:
        pass
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
