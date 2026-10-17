"""Build the final Canon "Ribbon" mark, its exports, and the Northwind demo icon.

Usage: cd brand/final && python build.py   (needs rsvg-convert and Pillow; reads ../wordmark.json)
"""
import json, os, re, subprocess
from io import BytesIO
from PIL import Image

PAPER, INK, ACCENT, ACCENT_DARK = "#f6f1e7", "#1c1a17", "#c8361e", "#e0533a"
WM = json.load(open("../wordmark.json"))
WM_D = re.sub(r"\d+\.\d+", lambda m: f"{float(m.group()):.2f}".rstrip("0").rstrip("."), WM["d"])

# Master geometry on a 64 grid. Every edge sits on an even unit, so 32px renders land on whole pixels.
# Page is close to A-series (40 x 56); stroke 6 matches the stem weight of the Fraunces wordmark.
# Ribbon hangs from the top edge, right of centre, with a 4-unit gap to the inner right edge.
# Notch: 12 wide, 6 deep (90 degrees), so the V lands on whole pixels at 32px.
MAIN = dict(x0=12, y0=4, x1=52, y1=60, s=6, rx0=30, rx1=42, ry=42, notch=6)
# 16px master: same mark redrawn on a 4-unit grid (1 unit = 1px at 16) so it hints crisply.
SMALL = dict(x0=12, y0=4, x1=52, y1=60, s=4, rx0=28, rx1=44, ry=44, notch=8)


def mark(fg, rib, g=MAIN):
    x0, y0, x1, y1, s = g["x0"], g["y0"], g["x1"], g["y1"], g["s"]
    rx0, rx1, ry, n = g["rx0"], g["rx1"], g["ry"], g["notch"]
    page = f"M{x0} {y0}H{x1}V{y1}H{x0}ZM{x0 + s} {y0 + s}V{y1 - s}H{x1 - s}V{y0 + s}Z"
    ribbon = f"M{rx0} {y0}H{rx1}V{ry}L{(rx0 + rx1) / 2:g} {ry - n}L{rx0} {ry}Z"
    return f'<path d="{page}" fill="{fg}" fill-rule="evenodd"/><path d="{ribbon}" fill="{rib}"/>'


def svg(w, h, body, scale=8):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w * scale}" height="{h * scale}">{body}</svg>\n'


def symbol(fg, rib, g=MAIN):
    return svg(64, 64, mark(fg, rib, g))


def lockup(fg, rib):
    k = 0.40  # cap height 40 on the 64 grid; sits on the page's optical centre
    w = 64 + 14 + WM["width"] * k + 4
    word = f'<path transform="translate(78 {32 - 50 * k:.2f}) scale({k})" d="{WM_D}" fill="{fg}"/>'
    return svg(round(w), 64, mark(fg, rib) + word)


def icon(rib=PAPER):
    # Symbol at 80% inside a rx=14 rounded square; corners stay inside the circle a Discord crop keeps.
    return svg(64, 64, f'<rect width="64" height="64" rx="14" fill="{INK}"/>'
                       f'<g transform="translate(6.4 6.4) scale(0.8)">{mark(PAPER, rib)}</g>')


def icon_px(n):
    # Hand-hinted 16 and 32px icons, drawn on their own pixel grid so every edge is whole.
    g = {16: (3, 4, 2, 12, 14, 1, 6, 10, 9, 2), 32: (7, 8, 5, 24, 27, 2, 14, 20, 19, 3)}[n]
    rx, x0, y0, x1, y1, s, r0, r1, ry, nt = g
    body = (f'<rect width="{n}" height="{n}" rx="{rx}" fill="{INK}"/>'
            f'<path d="M{x0} {y0}H{x1}V{y1}H{x0}ZM{x0 + s} {y0 + s}V{y1 - s}H{x1 - s}V{y0 + s}Z" '
            f'fill="{PAPER}" fill-rule="evenodd"/>'
            f'<path d="M{r0} {y0}H{r1}V{ry}L{(r0 + r1) / 2:g} {ry - nt}L{r0} {ry}Z" fill="{PAPER}"/>')
    return svg(n, n, body, 512 // n)


def og():
    lk = lockup(INK, ACCENT)
    inner = re.search(r'viewBox="0 0 (\d+) 64"[^>]*>(.*)</svg>', lk, re.S)
    lw = int(inner.group(1))
    k = 3.0
    x = (1200 - lw * k) / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">'
            f'<rect width="1200" height="630" fill="{PAPER}"/>'
            f'<g transform="translate({x:.1f} 150) scale({k})">{inner.group(2)}</g>'
            f'<text x="600" y="440" text-anchor="middle" font-family="Georgia" font-size="34" fill="{INK}">'
            f'The shared memory of a company, for its people and its AI agents.</text>'
            f'<text x="600" y="540" text-anchor="middle" font-family="Helvetica" font-size="24" '
            f'letter-spacing="2" fill="#8a8274">canon.tn07.dev</text></svg>\n')


def northwind(px=64):
    # Northwind Labs (fictional demo company): an N drawn as a delivery route, start stop hollow,
    # end stop solid. Mark kept inside the inscribed circle so a round crop never clips it.
    teal, sea, sand = "#0e4a55", "#ffffff", "#f2c46d"
    return svg(64, 64,
               f'<rect width="64" height="64" fill="{teal}"/>'
               f'<path d="M20 44V20L44 44V20" stroke="{sea}" stroke-width="6" fill="none" '
               f'stroke-linecap="round" stroke-linejoin="round"/>'
               f'<circle cx="20" cy="44" r="5" fill="{teal}" stroke="{sea}" stroke-width="3"/>'
               f'<circle cx="44" cy="20" r="5.5" fill="{sand}"/>', 16)


def png(svg_text, px, h=None):
    args = ["rsvg-convert", "-w", str(px)] + (["-h", str(h)] if h else [])
    out = subprocess.run(args, input=svg_text.encode(), capture_output=True, check=True)
    return Image.open(BytesIO(out.stdout)).convert("RGBA")


if __name__ == "__main__":
    files = {
        "canon-symbol.svg": symbol(INK, ACCENT),
        "canon-symbol-mono.svg": symbol(INK, INK),
        "canon-symbol-white.svg": symbol(PAPER, PAPER),
        "canon-lockup.svg": lockup(INK, ACCENT),
        "canon-lockup-mono.svg": lockup(INK, INK),
        "canon-lockup-white.svg": lockup(PAPER, PAPER),
        "canon-icon.svg": icon(),
    }
    for name, text in files.items():
        open(name, "w").write(text)
    os.makedirs("png", exist_ok=True)
    for px in [16, 32, 48, 64, 128, 180, 192, 256, 512, 1024]:
        for name, fg, rib in [("canon-symbol", INK, ACCENT), ("canon-symbol-mono", INK, INK),
                              ("canon-symbol-white", PAPER, PAPER)]:
            png(symbol(fg, rib, SMALL if px == 16 else MAIN), px).save(f"png/{name}-{px}.png", optimize=True)
    for px in [512, 1024]:
        png(icon(), px).save(f"png/canon-icon-{px}.png", optimize=True)
    png(icon(), 1024).save("discord-avatar.png", optimize=True)
    png(icon(), 180).save("apple-touch-icon.png", optimize=True)
    ico = [png(icon_px(16), 16), png(icon_px(32), 32), png(icon(), 48)]
    ico[2].save("favicon.ico", sizes=[(48, 48), (32, 32), (16, 16)], append_images=ico[:2])
    png(og(), 1200, 630).convert("RGB").save("og-image.png", optimize=True)
    nw = northwind()
    open("../northwind/northwind-icon.svg", "w").write(nw)
    for px in [512, 1024]:
        png(nw, px).save(f"../northwind/northwind-icon-{px}.png", optimize=True)
