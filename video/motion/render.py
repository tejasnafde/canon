"""Render an HTML motion clip frame by frame to an H.264 mp4 at 1920x1080, 30 fps.

  /tmp/pwvenv/bin/python video/motion/render.py video/motion/title.html video/clips/clip-01-title.mp4

The page must define window.__duration (seconds), window.__seek(t) and window.__ready().
Every frame is a screenshot after seeking the paused GSAP timeline, so timing is exact.
"""
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

FPS, W, H = 30, 1920, 1080


def render(html: Path, out: Path):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/Applications/Chromium.app/Contents/MacOS/Chromium',
                              args=['--force-color-profile=srgb', '--allow-file-access-from-files'])
        pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        pg.on('pageerror', lambda e: print('page error:', e))
        pg.goto(html.resolve().as_uri())
        pg.wait_for_function('!!window.__ready', polling=100, timeout=15000)
        pg.evaluate('window.__ready()')  # fonts loaded; a page may build its timeline here
        pg.wait_for_function('!!(window.__duration && window.__seek)', polling=100, timeout=15000)
        pg.wait_for_timeout(300)
        dur = pg.evaluate('window.__duration')
        n = round(dur * FPS)
        ff = subprocess.Popen(
            ['/opt/homebrew/bin/ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS),
             '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
             '-r', str(FPS), '-movflags', '+faststart', str(out)],
            stdin=subprocess.PIPE)
        for i in range(n):
            pg.evaluate(f'window.__seek({i / FPS})')
            ff.stdin.write(pg.screenshot(type='png'))
        ff.stdin.close()
        ff.wait()
        b.close()
    print(f'{out.name}: {n} frames, {dur:.2f} s')


if __name__ == '__main__':
    render(Path(sys.argv[1]), Path(sys.argv[2]))
