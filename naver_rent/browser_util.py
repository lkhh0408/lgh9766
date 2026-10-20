# -*- coding: utf-8 -*-
"""PC에 설치된 크롬(없으면 엣지)을 일반 창으로 띄우고 Playwright로 연결합니다.
Playwright가 직접 띄운 브라우저는 네이버가 막기 때문입니다."""
import os
import subprocess
import time
from pathlib import Path

DEBUG_PORT = 9222


def find_browser():
    env = os.environ
    candidates = []
    for base in (env.get("ProgramFiles"), env.get("ProgramFiles(x86)"), env.get("LocalAppData")):
        if base:
            candidates.append(Path(base) / "Google/Chrome/Application/chrome.exe")
    for base in (env.get("ProgramFiles(x86)"), env.get("ProgramFiles")):
        if base:
            candidates.append(Path(base) / "Microsoft/Edge/Application/msedge.exe")
    for c in candidates:
        if c.exists():
            return c
    return None


def launch_browser(here, start_url):
    exe = find_browser()
    if not exe:
        raise RuntimeError("크롬이나 엣지를 찾지 못했습니다.")
    profile = here / "browser_profile"
    profile.mkdir(exist_ok=True)
    print(f"브라우저 실행: {exe}", flush=True)
    return subprocess.Popen([
        str(exe),
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        start_url,
    ])


def connect(p):
    last = None
    for _ in range(30):
        try:
            return p.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")
        except Exception as e:
            last = e
            time.sleep(1)
    raise RuntimeError(f"브라우저에 연결하지 못했습니다: {last}")
