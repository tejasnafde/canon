"""Build the six Canon logo concepts and the contact sheet.

Usage: python build.py   (needs rsvg-convert and Pillow; reads wordmark.json)
Writes <concept>/{symbol,lockup,icon}.svg and concepts.png.
Symbols are drawn on a 64x64 grid. INK/ACCENT are swapped for the dark renders.
"""
import json, math, os, re, subprocess
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

PAPER, INK, ACCENT = "#f6f1e7", "#1c1a17", "#c8361e"
WM = json.load(open("wordmark.json"))
WM_D = re.sub(r"\d+\.\d+", lambda m: f"{float(m.group()):.2f}".rstrip("0").rstrip("."), WM["d"])


def arc(cx, cy, r, a0, a1):
    """Arc path from angle a0 to a1 (degrees, 0 = east, counterclockwise as on a clock face flipped)."""
    p = lambda a: (cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a)))
    (x0, y0), (x1, y1) = p(a0), p(a1)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{x0:.2f} {y0:.2f}A{r} {r} 0 {large} 0 {x1:.2f} {y1:.2f}"


def ring_segment(cx, cy, r0, r1, a0, a1):
    """Filled annular sector between radii r0<r1 and angles a0<a1 (degrees, ccw)."""
    p = lambda r, a: (cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a)))
    (ax, ay), (bx, by), (cx2, cy2), (dx, dy) = p(r1, a0), p(r1, a1), p(r0, a1), p(r0, a0)
    return (f"M{ax:.2f} {ay:.2f}A{r1} {r1} 0 0 0 {bx:.2f} {by:.2f}"
            f"L{cx2:.2f} {cy2:.2f}A{r0} {r0} 0 0 1 {dx:.2f} {dy:.2f}Z")


# Each concept: (slug, name, function(fg, accent, bg) -> SVG body on a 64 grid).
def record(fg, ac, bg):
    return (f'<rect x="8" y="10" width="6" height="44" fill="{fg}"/>'
            f'<rect x="20" y="10" width="36" height="7" fill="{fg}"/>'
            f'<rect x="20" y="28.5" width="36" height="7" fill="{fg}"/>'
            f'<rect x="20" y="47" width="22" height="7" fill="{fg}"/>'
            f'<rect x="47" y="44" width="13" height="13" fill="{ac}"/>')


def seal(fg, ac, bg):
    # 20-point stamp edge, C cut out of the middle
    pts = []
    for i in range(40):
        r = 29 if i % 2 == 0 else 25.5
        a = math.radians(i * 9)
        pts.append(f"{32 + r * math.cos(a):.2f} {32 + r * math.sin(a):.2f}")
    return (f'<mask id="m"><rect width="64" height="64" fill="#fff"/>'
            f'<path d="{arc(32, 32, 12, 45, 315)}" stroke="#000" stroke-width="7.5" fill="none"/></mask>'
            f'<path d="M{"L".join(pts)}Z" fill="{fg}" mask="url(#m)"/>')


def ribbon(fg, ac, bg):
    return (f'<path d="M10 6H54V58H10ZM15 11V53H49V11Z" fill="{fg}" fill-rule="evenodd"/>'
            f'<path d="M33 6H45V42L39 36L33 42Z" fill="{fg}"/>')


def stop(fg, ac, bg):
    return (f'<path d="{arc(30, 32, 20, 40, 320)}" stroke="{fg}" stroke-width="10" fill="none"/>'
            f'<rect x="49" y="42" width="10" height="10" fill="{ac}"/>')


def drift(fg, ac, bg):
    return (f'<rect x="6" y="18" width="52" height="9" fill="{fg}"/>'
            f'<rect x="6" y="37" width="24" height="9" fill="{fg}"/>'
            f'<rect x="35" y="43" width="23" height="9" fill="{ac}"/>')


def keystone(fg, ac, bg):
    # arch of voussoirs; the keystone is a wedge that stands proud of the ring
    spans = [(0, 36), (40, 75), (105, 140), (144, 180)]
    segs = [ring_segment(32, 50, 16, 30, a0, a1) for a0, a1 in spans] + [ring_segment(32, 50, 16, 37, 79, 101)]
    return "".join(f'<path d="{d}" fill="{fg}"/>' for d in segs)


CONCEPTS = [("record", "The Record", record), ("seal", "The Seal", seal), ("ribbon", "The Ribbon", ribbon),
            ("stop", "The Stop", stop), ("drift", "The Drift", drift), ("keystone", "Keystone", keystone)]


def svg(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w * 8}" height="{h * 8}">{body}</svg>\n'


def symbol(fn, fg=INK, ac=ACCENT, bg=PAPER):
    return svg(64, 64, fn(fg, ac, bg))


def lockup(fn, fg=INK, ac=ACCENT, bg=PAPER):
    k = 0.42  # cap height 42 on the 64 grid
    w = 64 + 16 + WM["width"] * k
    word = f'<path transform="translate(80 {32 - 50 * k:.2f}) scale({k})" d="{WM_D}" fill="{fg}"/>'
    return svg(round(w), 64, fn(fg, ac, bg) + word)


def icon(fn, dark=True):
    fg, bg = (PAPER, INK) if dark else (INK, PAPER)
    return svg(64, 64, f'<rect width="64" height="64" rx="14" fill="{bg}"/>'
                       f'<g transform="translate(13 13) scale(0.59375)">{fn(fg, ACCENT, bg)}</g>')


def png(svg_text, px):
    out = subprocess.run(["rsvg-convert", "-w", str(px)], input=svg_text.encode(), capture_output=True, check=True)
    return Image.open(BytesIO(out.stdout)).convert("RGBA")


def sheet():
    W, ROW, PAD = 1880, 250, 40
    img = Image.new("RGB", (W, 120 + ROW * len(CONCEPTS)), PAPER)
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia.ttf", 28)
    small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
    d.text((PAD, 30), "Canon - logo concepts", fill=INK, font=big)
    heads = [(PAD + 220, "symbol"), (PAD + 430, "dark"), (PAD + 640, "lockup"), (PAD + 1120, "app icon"),
             (PAD + 1290, "32 light / dark"), (PAD + 1450, "16 light / dark"), (PAD + 1610, "16 at 4x")]
    for x, t in heads:
        d.text((x, 80), t, fill="#8a8274", font=small)
    for i, (slug, name, fn) in enumerate(CONCEPTS):
        y = 110 + i * ROW
        d.line((PAD, y - 6, W - PAD, y - 6), fill="#ddd5c5")
        d.text((PAD, y + 80), f"{i + 1}. {name}", fill=INK, font=big)
        img.paste(png(symbol(fn), 180), (PAD + 220, y + 15), png(symbol(fn), 180))
        d.rectangle((PAD + 420, y + 5, PAD + 620, y + 205), fill=INK)
        dk = png(symbol(fn, PAPER, "#e0533a"), 180)
        img.paste(dk, (PAD + 430, y + 15), dk)
        lk = png(lockup(fn), 440)
        img.paste(lk, (PAD + 640, y + 105 - lk.height // 2), lk)
        ic = png(icon(fn), 150)
        img.paste(ic, (PAD + 1120, y + 30), ic)
        for j, (px, x0) in enumerate([(32, PAD + 1290), (16, PAD + 1450)]):
            d.rectangle((x0 + 60, y + 70, x0 + 120, y + 130), fill=INK)
            a, b = png(symbol(fn), px), png(symbol(fn, PAPER, "#e0533a"), px)
            img.paste(a, (x0 + 10, y + 100 - px // 2), a)
            img.paste(b, (x0 + 90 - px // 2, y + 100 - px // 2), b)
        z = png(symbol(fn), 16).resize((64, 64), Image.NEAREST)
        img.paste(z, (PAD + 1620, y + 68), z)
        zi = png(icon(fn), 16).resize((64, 64), Image.NEAREST)
        img.paste(zi, (PAD + 1700, y + 68), zi)
    img.save("concepts.png", optimize=True)


if __name__ == "__main__":
    for slug, _, fn in CONCEPTS:
        os.makedirs(slug, exist_ok=True)
        for kind, text in [("symbol", symbol(fn)), ("lockup", lockup(fn)), ("icon", icon(fn))]:
            open(f"{slug}/{kind}.svg", "w").write(text)
    sheet()
