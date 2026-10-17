"""Screenshot every route at 1280x800 and 1920x1080 into web/shots/, after the data has loaded.

  VITE_API_TARGET=https://canon.tn07.dev npx vite --port 5181 &
  /tmp/pwvenv/bin/python web/scripts/shots.py [base_url]

<name>.png is the 1280x800 viewport, <name>-full.png the full page, <name>-1080.png the 1920x1080 viewport.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5181'
OUT = Path(__file__).resolve().parent.parent / 'shots'
OUT.mkdir(exist_ok=True)
T = 120000
errors = []

ROUTES = [
    ('home', '/', None),
    ('new-hire', '/new-hire', None),
    ('catch-up', '/catch-up', None),
    ('catch-up-sales', '/catch-up?role=sales', None),
    ('agent', '/agent', 'agent'),
    ('paste', '/paste', 'paste'),
    ('ask', '/ask', None),
    ('decisions', '/decisions', None),
    ('decision', '/decisions', 'decision'),
    ('benchmark', '/benchmark', None),
    ('not-found', '/nope', None),
]


def settle(pg):
    pg.wait_for_function("!document.querySelector('[aria-busy=true]')", timeout=T)
    pg.wait_for_load_state('networkidle', timeout=T)
    pg.wait_for_timeout(400)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/Applications/Chromium.app/Contents/MacOS/Chromium')
    for w, h, suf in ((1280, 800, ''), (1920, 1080, '-1080')):
        ctx = b.new_context(viewport={'width': w, 'height': h}, reduced_motion='reduce')
        pg = ctx.new_page()
        pg.on('console', lambda m: m.type == 'error' and errors.append(f'{pg.url}: {m.text}'))
        pg.on('pageerror', lambda e: errors.append(f'{pg.url}: {e}'))
        for name, path, flow in ROUTES:
            pg.goto(BASE + path)
            settle(pg)
            if flow == 'decision':
                pg.locator('table.rows a').first.click()
                settle(pg)
            if flow == 'paste':
                pg.get_by_role('button', name='Check this message').click()
                pg.wait_for_timeout(1500)
                if not suf:
                    pg.screenshot(path=str(OUT / 'paste-working.png'))
                pg.get_by_text('Done in').or_(pg.get_by_role('alert')).wait_for(timeout=T)
                settle(pg)
            pg.screenshot(path=str(OUT / f'{name}{suf}.png'))
            if not suf:
                pg.screenshot(path=str(OUT / f'{name}-full.png'), full_page=True)
            if flow == 'agent' and not suf:
                pg.get_by_role('button', name='Release a config change on Friday').click()
                pg.get_by_text('Called check_intent').or_(pg.get_by_text('did not run')).wait_for(timeout=T)
                pg.locator('.result').scroll_into_view_if_needed()
                pg.screenshot(path=str(OUT / 'agent-try.png'))
        if not suf:
            pg.goto(BASE + '/')
            settle(pg)
            pg.keyboard.press('Control+k')
            pg.get_by_placeholder('Search, or ask').wait_for()
            pg.keyboard.type('friday')
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / 'command.png'))
        ctx.close()
    phone = b.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
    pg = phone.new_page()
    pg.goto(BASE + '/')
    settle(pg)
    pg.screenshot(path=str(OUT / 'home-phone.png'), full_page=True)
    b.close()

print('\n'.join(errors) or 'no console errors')
