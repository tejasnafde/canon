"""Render data/discord/screens/*.html to PNG with Playwright (1280 wide, full page, 1.5x). Synthetic demo assets.

Usage: /tmp/pwvenv/bin/python data/discord/render_screens.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent / "screens"
CHROMIUM = "/Applications/Chromium.app/Contents/MacOS/Chromium"

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROMIUM)
    page = b.new_page(viewport={"width": 1280, "height": 560}, device_scale_factor=1.5)
    for html in sorted(HERE.glob("*.html")):
        page.goto(html.resolve().as_uri(), wait_until="domcontentloaded")
        page.screenshot(path=str(html.with_suffix(".png")), full_page=True)
        print(html.with_suffix(".png").name)
    b.close()
