"""Record the demo screen clips from the live app into video/clips/clip-NN-<name>.mp4.

  /tmp/pwvenv/bin/python video/record.py                 # every clip
  /tmp/pwvenv/bin/python video/record.py agent paste     # only these
  CANON_BASE=http://localhost:5181 /tmp/pwvenv/bin/python video/record.py org

Frames come from the Chrome DevTools screencast (JPEG q92 at 1920x1080), not Playwright's
built-in 1 Mbit/s recorder, so small text stays sharp. Capture starts once the first page has
settled, so there is no dead time at the start. Each clip runs in a fresh browser context, which
gives it a fresh visitor workspace (localStorage `canon-ws`); the workspace is reset at the end.

Gemini cost: catch-up (2 briefings), agent (2 checks), paste (1 ingest), ask (3 questions).
Do not loop this script: each run spends those calls again.
"""
import base64
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = os.environ.get('CANON_BASE', 'https://canon.tn07.dev').rstrip('/')
CHROMIUM = '/Applications/Chromium.app/Contents/MacOS/Chromium'
FFMPEG = '/opt/homebrew/bin/ffmpeg'
OUT = Path(__file__).resolve().parent / 'clips'
W, H = 1920, 1080
T = 120_000
CPS = 12  # typing speed, characters per second

# A visible cursor: ink arrow with a paper outline, and a vermilion ring on click.
CURSOR_JS = """
(() => {
  const install = () => {
    if (document.getElementById('__cur')) return;
    const st = document.createElement('style');
    st.textContent = `
      #__cur{position:fixed;left:0;top:0;width:30px;height:30px;z-index:2147483647;pointer-events:none;
        transform:translate(var(--x,-100px),var(--y,-100px));will-change:transform}
      #__cur svg{display:block;filter:drop-shadow(0 2px 3px rgba(28,26,23,.28))}
      .__ring{position:fixed;z-index:2147483646;pointer-events:none;width:44px;height:44px;margin:-22px 0 0 -22px;
        border:2.5px solid #c8361e;border-radius:50%;animation:__ring .55s cubic-bezier(.2,.7,.3,1) forwards}
      @keyframes __ring{from{transform:scale(.3);opacity:.95}to{transform:scale(1.25);opacity:0}}`;
    document.head.appendChild(st);
    const c = document.createElement('div');
    c.id = '__cur';
    c.innerHTML = '<svg width="36" height="36" viewBox="0 0 30 30"><path d="M4 2.5 L4 24 L9.6 18.6 L13.4 27 L17 25.4 L13.3 17.2 L21 17.2 Z" fill="#1c1a17" stroke="#f6f1e7" stroke-width="1.8" stroke-linejoin="round"/></svg>';
    document.body.appendChild(c);
    const p = JSON.parse(sessionStorage.getItem('__cur') || 'null');
    if (p) { c.style.setProperty('--x', p[0] - 4 + 'px'); c.style.setProperty('--y', p[1] - 2 + 'px'); }
  };
  addEventListener('mousemove', e => {
    install();
    const c = document.getElementById('__cur');
    c.style.setProperty('--x', e.clientX - 4 + 'px');
    c.style.setProperty('--y', e.clientY - 2 + 'px');
    sessionStorage.setItem('__cur', JSON.stringify([e.clientX, e.clientY]));
  }, true);
  addEventListener('mousedown', e => {
    const r = document.createElement('div');
    r.className = '__ring'; r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
    document.body.appendChild(r); setTimeout(() => r.remove(), 700);
  }, true);
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', install); else install();
})();
"""

SCROLL_JS = """
([to, ms]) => new Promise(done => {
  const from = scrollY, d = Math.max(0, Math.min(to, document.documentElement.scrollHeight - innerHeight)) - from, t0 = performance.now();
  const ease = t => t < .5 ? 4*t*t*t : 1 - Math.pow(-2*t + 2, 3) / 2;
  const step = now => { const t = Math.min(1, (now - t0) / ms); scrollTo(0, from + d * ease(t)); t < 1 ? requestAnimationFrame(step) : done(); };
  requestAnimationFrame(step);
})
"""


class Screencast:
    """Collect DevTools screencast frames with their timestamps, then encode a 30 fps H.264 mp4."""

    def __init__(self, pg: Page):
        self.pg = pg
        self.frames: list[tuple[float, bytes]] = []
        self.cdp = pg.context.new_cdp_session(pg)
        self.cdp.on('Page.screencastFrame', self._frame)

    def _frame(self, f):
        self.frames.append((f['metadata']['timestamp'], base64.b64decode(f['data'])))
        try:
            self.cdp.send('Page.screencastFrameAck', {'sessionId': f['sessionId']})
        except Exception:
            pass

    def start(self):
        self.cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 92, 'maxWidth': W, 'maxHeight': H, 'everyNthFrame': 1})
        self.pg.wait_for_timeout(300)

    def stop(self, out: Path):
        end = time.time()
        self.pg.wait_for_timeout(200)
        self.cdp.send('Page.stopScreencast')
        if not self.frames:
            raise RuntimeError('no frames captured')
        tmp = Path(tempfile.mkdtemp(prefix='canon-clip-'))
        lines = []
        for i, (ts, data) in enumerate(self.frames):
            (tmp / f'{i:05d}.jpg').write_bytes(data)
            nxt = self.frames[i + 1][0] if i + 1 < len(self.frames) else max(end, ts + 0.5)
            lines += [f"file '{i:05d}.jpg'", f'duration {max(nxt - ts, 0.001):.4f}']
        lines.append(f"file '{len(self.frames) - 1:05d}.jpg'")
        (tmp / 'list.txt').write_text('\n'.join(lines) + '\n')
        subprocess.run(
            [FFMPEG, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(tmp / 'list.txt'),
             '-vf', f'fps=30,scale={W}:{H}:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-preset', 'medium',
             '-crf', '17', '-movflags', '+faststart', str(out)],
            check=True,
        )
        shutil.rmtree(tmp)
        dur = self.frames[-1][0] - self.frames[0][0]
        print(f'  {out.name}: {len(self.frames)} frames, about {dur:.1f} s')


class Director:
    """Human-paced cursor, typing and scrolling on one page."""

    def __init__(self, pg: Page):
        self.pg = pg
        self.x, self.y = W * 0.62, H * 0.55

    def hold(self, s: float):
        self.pg.wait_for_timeout(int(s * 1000))

    def glide(self, x: float, y: float, s: float | None = None):
        dist = math.hypot(x - self.x, y - self.y)
        s = s if s is not None else min(1.1, 0.35 + dist / 1800)
        n = max(2, int(s * 60))
        x0, y0 = self.x, self.y
        for i in range(1, n + 1):
            t = i / n
            e = 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2
            self.pg.mouse.move(x0 + (x - x0) * e, y0 + (y - y0) * e)
            self.pg.wait_for_timeout(16)
        self.x, self.y = x, y

    def scroll(self, y: float, s: float = 1.2):
        self.pg.evaluate(SCROLL_JS, [y, int(s * 1000)])

    def scroll_to(self, loc, top: int = 140, s: float = 1.2):
        """Bring loc to `top` px from the viewport top."""
        box = loc.bounding_box()
        y = self.pg.evaluate('scrollY') + box['y'] - top
        self.scroll(y, s)

    def ensure_visible(self, loc, margin: int = 120):
        box = loc.bounding_box()
        if box['y'] < margin or box['y'] + box['height'] > H - margin:
            self.scroll_to(loc, top=min(260, max(margin, (H - box['height']) // 2)))

    def point(self, loc, fx: float = 0.5, fy: float = 0.5, s: float | None = None):
        self.ensure_visible(loc)
        box = loc.bounding_box()
        self.glide(box['x'] + box['width'] * fx, box['y'] + box['height'] * fy, s)

    def click(self, loc, fx: float = 0.5, fy: float = 0.5):
        self.point(loc, fx, fy)
        self.hold(0.25)
        self.pg.mouse.down()
        self.pg.wait_for_timeout(70)
        self.pg.mouse.up()

    def type(self, loc, text: str, clear: bool = True):
        self.click(loc, 0.3, 0.5)
        if clear:
            self.hold(0.3)
            self.pg.keyboard.press('Meta+a')
            self.pg.keyboard.press('Backspace')
            self.hold(0.4)
        self.pg.keyboard.type(text, delay=int(1000 / CPS))

    def read(self, loc, s: float = 1.6):
        """Run the cursor along a line of text, as if reading it."""
        self.ensure_visible(loc)
        box = loc.bounding_box()
        y = box['y'] + min(box['height'] * 0.5, 30)
        self.glide(box['x'] + 10, y)
        self.glide(box['x'] + box['width'] * 0.92, y + min(box['height'] * 0.4, 60), s)


def settle(pg: Page, extra: float = 0.4):
    pg.wait_for_function("!document.querySelector('[aria-busy=true]')", timeout=T)
    pg.wait_for_load_state('networkidle', timeout=T)
    pg.wait_for_timeout(int(extra * 1000))


def warm(pg: Page):
    """Wake Cloud Run before the first clip so nothing waits on a cold start."""
    for path in ('/api/stats', '/api/decisions', '/api/eval'):
        pg.request.get(BASE + path, timeout=T)


# ---- clips ---------------------------------------------------------------------------------


def clip_02_home(pg: Page, d: Director):
    pg.goto(BASE + '/')
    settle(pg)
    yield
    d.hold(1.5)
    d.read(pg.locator('h1'), 2.4)
    d.hold(0.8)
    d.point(pg.locator('.figures'), 0.5, 0.4)
    d.hold(1.5)
    d.scroll_to(pg.get_by_role('heading', name='Pick a story'), 120, 1.4)
    d.hold(0.6)
    for li in pg.locator('.stories > li').all()[:5]:
        d.point(li, 0.25, 0.35)
        d.hold(1.3)
    d.hold(1.0)


def clip_03_new_hire(pg: Page, d: Director):
    pg.goto(BASE + '/new-hire')
    settle(pg)
    yield
    d.hold(1.5)
    d.read(pg.locator('h1'), 1.4)
    d.hold(1.0)
    must = pg.get_by_role('heading', name='5 things you must know')
    d.scroll_to(must, 110, 1.4)
    d.hold(1.0)
    items = must.locator('xpath=following::ol[1]/li | following::ul[1]/li').all()[:5]
    for li in items:
        d.point(li, 0.12, 0.3)
        d.hold(1.6)
    ask = pg.get_by_role('heading', name='People to ask')
    d.scroll_to(ask, 110, 1.4)
    d.hold(1.2)
    for li in ask.locator('xpath=following::li').all()[:3]:
        d.point(li, 0.2, 0.4)
        d.hold(1.2)
    left = pg.get_by_role('heading', name='People who left')
    if left.count():
        d.scroll_to(left, 160, 1.2)
        d.hold(2.0)
    d.hold(0.8)


def _catch_up_read(pg: Page, d: Director):
    pg.wait_for_timeout(300)  # let the new role's request start before waiting on it
    pg.locator('.summary').first.wait_for(timeout=T)
    settle(pg)
    d.hold(0.6)
    summary = pg.locator('.summary').first
    if summary.count():
        d.scroll_to(summary, 160, 1.2)
        d.read(summary, 3.0)
        d.hold(1.5)
    todo = pg.locator('ol.todo > li')
    if todo.count():
        d.scroll_to(todo.first, 180, 1.2)
        d.hold(0.8)
        for li in todo.all()[:3]:
            d.point(li, 0.4, 0.35)
            d.hold(1.4)
        u = todo.first.locator('.u')
        if u.count():
            d.point(u)
            d.hold(2.2)


def clip_04_catch_up(pg: Page, d: Director):
    pg.goto(BASE + '/catch-up')
    settle(pg)
    yield
    d.hold(1.2)
    d.click(pg.get_by_role('button', name='Engineer', exact=True))
    _catch_up_read(pg, d)
    d.scroll(0, 1.2)
    d.hold(0.6)
    d.click(pg.get_by_role('button', name='Sales', exact=True))
    _catch_up_read(pg, d)
    d.hold(1.0)


AGENT_INTENT = 'Add a cron job that deploys the dispatch service to production every Friday at 15:00'


def clip_05_agent(pg: Page, d: Director):
    pg.goto(BASE + '/agent')
    settle(pg)
    yield
    d.hold(1.5)
    for li in pg.locator('ol.steps > li').all():
        d.point(li, 0.15, 0.3)
        d.hold(1.4)
    d.point(pg.locator('.verdict .word'), 0.4, 0.5)
    d.hold(1.2)
    d.read(pg.locator('.verdict .rule'), 2.2)
    d.hold(1.5)
    term = pg.locator('.term')
    d.scroll_to(term, 120, 1.6)
    d.hold(1.0)
    for st in term.locator('.step').all():
        d.ensure_visible(st, 90)
        d.point(st, 0.06, 0.25)
        d.hold(1.6)
    d.scroll_to(pg.get_by_role('heading', name='Try it yourself'), 110, 1.4)
    d.hold(0.8)
    d.type(pg.get_by_label('An action an agent wants to take'), AGENT_INTENT)
    d.hold(0.8)
    d.click(pg.get_by_role('button', name='Check it'))
    pg.locator('.result').get_by_text('Called check_intent').or_(pg.get_by_text('did not run')).first.wait_for(timeout=T)
    d.hold(0.4)
    res = pg.locator('.result').last
    d.ensure_visible(res, 160)
    d.point(res, 0.12, 0.2)
    d.hold(1.0)
    d.read(res, 2.4)
    d.hold(2.5)


def clip_06_paste(pg: Page, d: Director):
    pg.goto(BASE + '/paste')
    settle(pg)
    yield
    d.hold(1.5)
    d.click(pg.get_by_role('button', name='Friday deploy job'))
    d.hold(1.0)
    d.read(pg.locator('textarea'), 2.4)
    d.hold(0.6)
    d.click(pg.get_by_role('button', name='Check this message'))
    d.hold(0.8)
    busy = pg.locator('[aria-busy=true]').first
    if busy.count():
        d.scroll_to(pg.locator('.progress'), 200, 1.0)
    pg.get_by_text('Done in').or_(pg.get_by_role('alert')).first.wait_for(timeout=T)
    settle(pg, 0.3)
    d.hold(1.2)
    d.scroll_to(pg.locator('.progress'), 120, 1.0)
    d.hold(1.0)
    for f in pg.locator('.flag').all():
        d.ensure_visible(f, 100)
        for side in f.locator('.vs > div').all():
            d.point(side, 0.2, 0.3)
            d.hold(1.8)
        if not f.locator('.vs').count():
            d.point(f, 0.15, 0.3)
            d.hold(2.0)
    und = pg.locator('aside.understood')
    if und.count():
        d.point(und, 0.2, 0.2)
        d.hold(2.0)
    d.scroll(pg.evaluate('document.documentElement.scrollHeight'), 2.2)
    d.hold(2.0)


ASK_FRIDAY = 'Why do we not deploy on Fridays?'


def clip_08_ask(pg: Page, d: Director):
    pg.goto(BASE + '/ask')
    settle(pg)
    yield
    d.hold(1.2)
    d.type(pg.get_by_label('Your question'), ASK_FRIDAY)
    d.hold(0.6)
    d.click(pg.get_by_role('button', name='Ask', exact=True))
    d.hold(0.8)
    settle(pg, 0.3)
    d.hold(1.0)
    ans = pg.locator('.answer')
    d.point(ans, 0.1, 0.1)
    d.read(ans.locator('p, .ans').first, 3.0)
    d.hold(1.5)
    cites = pg.locator('ol.cites > li')
    for li in cites.all()[:3]:
        d.point(li, 0.2, 0.4)
        d.hold(1.3)
    tl = pg.locator('ul.tl')
    if tl.count():
        d.point(tl, 0.2, 0.2)
        d.hold(1.2)
        for li in tl.locator('li').all()[:4]:
            d.point(li, 0.3, 0.4)
            d.hold(0.9)
    refusal = pg.get_by_role('heading', name='When Canon does not know')
    d.scroll_to(refusal, 200, 1.4)
    d.point(refusal, 0.2, 0.5)
    d.hold(1.0)
    d.read(refusal.locator('xpath=following::*[contains(@class,"ans")][1]'), 2.6)
    d.hold(2.5)


def clip_09_decisions(pg: Page, d: Director):
    pg.goto(BASE + '/decisions')
    settle(pg)
    yield
    d.hold(1.5)
    d.scroll(380, 1.6)
    d.hold(1.0)
    d.scroll(0, 1.2)
    friday = pg.locator('table.rows a').filter(has_text='Friday').first
    d.click(friday)
    settle(pg)
    d.hold(1.8)
    d.read(pg.locator('h1'), 2.4)
    d.hold(1.0)
    d.scroll(520, 1.8)
    d.hold(2.0)
    d.scroll(1100, 1.8)
    d.hold(2.0)
    d.scroll(0, 1.2)
    d.click(pg.locator('header nav a, nav a').filter(has_text='People').first)
    settle(pg)
    if pg.get_by_role('heading', name='Not on record.').count():
        print('  /org is not deployed on', BASE, '- people part skipped')
        d.hold(1.0)
        return
    d.hold(1.8)
    d.scroll(300, 1.4)
    d.hold(1.2)
    mei = pg.locator('.org a').filter(has_text='Mei Tan')  # the owner of the Friday decision
    person = mei.first if mei.count() else pg.locator('.org .lvl-head > .who a').first
    d.click(person)
    settle(pg)
    d.hold(1.8)
    d.scroll(450, 1.6)
    d.hold(2.5)


def clip_11_benchmark(pg: Page, d: Director):
    pg.goto(BASE + '/benchmark')
    settle(pg)
    yield
    d.hold(1.5)
    d.read(pg.locator('h1'), 1.2)
    d.hold(1.0)
    total = pg.evaluate('document.documentElement.scrollHeight') - H
    y = 0
    while y < total:
        y = min(total, y + 420)
        d.scroll(y, 1.8)
        d.hold(2.2)
    d.hold(1.0)


CLIPS = {
    'home': ('02', clip_02_home),
    'new-hire': ('03', clip_03_new_hire),
    'catch-up': ('04', clip_04_catch_up),
    'agent': ('05', clip_05_agent),
    'paste': ('06', clip_06_paste),
    'ask': ('08', clip_08_ask),
    'decisions': ('09', clip_09_decisions),
    'benchmark': ('11', clip_11_benchmark),
}


def record(browser, name: str):
    num, fn = CLIPS[name]
    out = OUT / f'clip-{num}-{name}.mp4'
    ctx = browser.new_context(viewport={'width': W, 'height': H}, device_scale_factor=1)
    ctx.add_init_script(CURSOR_JS)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: print('  page error:', e))
    d = Director(pg)
    try:
        steps = fn(pg, d)
        next(steps)  # page is ready: start capturing here, so the clip has no dead start
        pg.mouse.move(d.x, d.y)
        cast = Screencast(pg)
        cast.start()
        for _ in steps:
            pass
        cast.stop(out)
    finally:
        ws = pg.evaluate("localStorage.getItem('canon-ws')")
        if ws:
            pg.request.post(BASE + '/api/workspace/reset', headers={'X-Canon-Workspace': ws})
        ctx.close()


def main():
    names = sys.argv[1:] or list(CLIPS)
    unknown = [n for n in names if n not in CLIPS]
    if unknown:
        raise SystemExit(f'unknown clip {unknown}; choose from {list(CLIPS)}')
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROMIUM, args=['--hide-scrollbars', '--force-color-profile=srgb'])
        warm(b.new_page())
        for n in names:
            print('recording', n)
            record(b, n)
        b.close()


if __name__ == '__main__':
    main()
