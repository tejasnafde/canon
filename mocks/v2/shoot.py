"""Retake the mock screenshots into shots/.
Run: /tmp/pwvenv/bin/python shoot.py   (Playwright, local Chromium, file:// URLs)."""
import pathlib, sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'shots'
OUT.mkdir(exist_ok=True)
PAGES = ['index', 'home', 'new-hire', 'catch-up', 'catch-up-sales', 'agent', 'paste', 'ask', 'decisions', 'decision', 'benchmark']
PHONE = ['home', 'catch-up']
only = sys.argv[1:]

def settle(page):
    page.evaluate('document.fonts.ready')
    page.wait_for_timeout(400)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Chromium.app/Contents/MacOS/Chromium')
    desk = browser.new_context(viewport={'width': 1280, 'height': 800}, device_scale_factor=1)
    phone = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True)
    for name in PAGES:
        if only and name not in only:
            continue
        url = (HERE / f'{name}.html').as_uri()
        pg = desk.new_page(); pg.goto(url, wait_until='domcontentloaded'); settle(pg)
        pg.screenshot(path=OUT / f'{name}.png')
        pg.screenshot(path=OUT / f'{name}-full.png', full_page=True)
        pg.close()
        if name in PHONE:
            pg = phone.new_page(); pg.goto(url, wait_until='domcontentloaded'); settle(pg)
            pg.screenshot(path=OUT / f'{name}-phone.png', full_page=True)
            pg.close()
        print('shot', name)
    browser.close()
