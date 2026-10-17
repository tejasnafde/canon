"""Screenshot every route at 1280x800 into web/shots/ and exercise the main flows.

  /tmp/pwvenv/bin/python web/scripts/shots.py [base_url] [suffix]
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5173'
SUF = sys.argv[2] if len(sys.argv) > 2 else ''
OUT = Path(__file__).resolve().parent.parent / 'shots'
OUT.mkdir(exist_ok=True)
errors = []

with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/Applications/Chromium.app/Contents/MacOS/Chromium')
    pg = b.new_page(viewport={'width': 1280, 'height': 800})
    pg.on('console', lambda m: m.type == 'error' and errors.append(f'{pg.url}: {m.text}'))
    pg.on('pageerror', lambda e: errors.append(f'{pg.url}: {e}'))

    def shot(name, full=False):
        pg.screenshot(path=str(OUT / f'{name}{SUF}.png'), full_page=full)

    pg.goto(BASE + '/'); pg.wait_for_selector('.lede', timeout=60000); shot('home'); shot('home-full', True)
    pg.get_by_role('button', name='New hire').click(); pg.wait_for_selector('.people, .act', timeout=60000)
    pg.wait_for_timeout(500); pg.wait_for_function("!document.querySelector('[aria-busy=true]')", timeout=60000); shot('home-newhire', True)

    pg.goto(BASE + '/ask'); pg.wait_for_selector('.ans', timeout=60000); shot('ask')
    pg.get_by_role('button', name='annual recurring revenue', exact=False).click()
    pg.wait_for_selector('.refuse, .cite', timeout=60000); shot('ask-refused')

    pg.goto(BASE + '/ingest'); pg.wait_for_selector('.sample'); shot('ingest')
    pg.get_by_role('button', name='Ingest and reconcile').click()
    pg.wait_for_selector('.steps'); pg.wait_for_timeout(1500); shot('ingest-working')
    pg.wait_for_selector('.stats, .state.err', timeout=90000); shot('ingest-result')

    pg.goto(BASE + '/agents'); pg.wait_for_selector('.tools'); pg.get_by_role('button', name='Call tool').click()
    pg.wait_for_selector('.resp, .state.err', timeout=60000); pg.wait_for_timeout(2500); shot('agents')
    pg.goto(BASE + '/'); pg.wait_for_selector('.blockcard', timeout=60000); pg.wait_for_selector('.lede', timeout=60000); shot('home-block')

    pg.goto(BASE + '/decisions'); pg.wait_for_selector('.dlist a, .state', timeout=60000); shot('decisions')
    first = pg.locator('.dlist a', has_text='Fridays').first
    first.click(); pg.wait_for_selector('.stmt, .state.err', timeout=60000); shot('decision')

    pg.goto(BASE + '/benchmark'); pg.wait_for_selector('.kpis, .state.err', timeout=60000); shot('benchmark')
    pg.goto(BASE + '/about'); pg.wait_for_selector('table'); shot('about')

    pg.set_viewport_size({'width': 390, 'height': 844}); pg.goto(BASE + '/'); pg.wait_for_selector('.lede', timeout=60000); shot('phone-home')
    b.close()

print('\n'.join(errors) or 'no console errors')
