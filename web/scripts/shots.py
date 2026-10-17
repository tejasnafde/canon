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
T = 90000
errors = []

with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/Applications/Chromium.app/Contents/MacOS/Chromium')
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}, reduced_motion='reduce')
    pg = ctx.new_page()
    pg.on('console', lambda m: m.type == 'error' and errors.append(f'{pg.url}: {m.text}'))
    pg.on('pageerror', lambda e: errors.append(f'{pg.url}: {e}'))

    def shot(name, full=False):
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / f'{name}{SUF}.png'), full_page=full)

    def settle():
        pg.wait_for_function("!document.querySelector('[aria-busy=true], [role=status][aria-label]')", timeout=T)

    pg.goto(BASE + '/'); pg.get_by_text('Next best actions').wait_for(timeout=T); settle(); shot('home'); shot('home-full', True)
    pg.get_by_role('radio', name='New hire').click(); pg.get_by_text('Since day one').first.wait_for(timeout=T)
    settle(); shot('home-newhire', True)

    pg.goto(BASE + '/ask'); pg.get_by_text('Decision timeline').wait_for(timeout=T); shot('ask')
    pg.get_by_role('button', name='annual recurring revenue').click()
    pg.get_by_text('Refused /').wait_for(timeout=T); shot('ask-refused')

    pg.goto(BASE + '/ingest'); pg.get_by_role('button', name='Ingest and reconcile').wait_for(); shot('ingest')
    pg.get_by_role('button', name='Ingest and reconcile').click()
    pg.get_by_label('Ingest progress').wait_for(); pg.wait_for_timeout(1500); shot('ingest-working')
    pg.get_by_text('Extracted and reconciled').or_(pg.get_by_text('Ingest failed')).wait_for(timeout=T); shot('ingest-result')

    pg.goto(BASE + '/agents'); pg.get_by_role('button', name='Call tool').click()
    pg.get_by_label('Raw tool response').or_(pg.get_by_text('The tool call failed')).wait_for(timeout=T); pg.wait_for_timeout(2500); shot('agents')
    pg.goto(BASE + '/'); pg.get_by_label('Latest agent block').wait_for(timeout=T); pg.get_by_text('Next best actions').wait_for(timeout=T); settle(); shot('home-block')

    pg.goto(BASE + '/decisions'); pg.get_by_role('link', name='Fridays').first.wait_for(timeout=T); shot('decisions')
    pg.get_by_role('link', name='Fridays').first.click(); pg.get_by_text('Verified quotes').wait_for(timeout=T); shot('decision')

    pg.goto(BASE + '/benchmark'); pg.get_by_text('By task').wait_for(timeout=T); shot('benchmark')
    pg.goto(BASE + '/about'); pg.get_by_text('The stack').wait_for(); shot('about')
    pg.goto(BASE + '/nope'); pg.get_by_text('Not on record.').wait_for(); shot('not-found')

    pg.goto(BASE + '/'); pg.get_by_text('Next best actions').wait_for(timeout=T); pg.keyboard.press('Control+k'); pg.get_by_placeholder('Search decisions').wait_for(); pg.keyboard.type('friday'); shot('command')

    dark = b.new_context(viewport={'width': 1280, 'height': 800}, reduced_motion='reduce')
    dark.add_init_script("localStorage.setItem('theme', 'dark')")
    pg = dark.new_page()
    pg.goto(BASE + '/'); pg.get_by_text('Next best actions').wait_for(timeout=T); settle(); shot('home-dark')

    phone = b.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
    pg = phone.new_page()
    pg.goto(BASE + '/'); pg.get_by_text('Next best actions').wait_for(timeout=T); settle(); shot('phone-home')
    b.close()

print('\n'.join(errors) or 'no console errors')
