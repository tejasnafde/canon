"""Round 2: six ribbon-family variants. Reuses round 1 helpers (../build.py).

Usage: cd brand/round2 && python build.py
Writes <variant>/{symbol,lockup,icon}.svg and concepts.png. 64x64 grid.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(HERE))  # round 1 build.py reads wordmark.json relative to brand/
sys.path.insert(0, os.getcwd())
import build as r1  # noqa: E402

os.chdir(HERE)


def notch(x0, x1, y_top, y_bot, depth):
    """Ribbon tail polygon: rectangle with a V cut of `depth` at the bottom."""
    xm = (x0 + x1) / 2
    return f"M{x0} {y_top}H{x1}V{y_bot}L{xm} {y_bot - depth}L{x0} {y_bot}Z"


def c_ring(cx, cy, r0, r1, a0, a1):
    """Annular sector over 180 degrees (round 1's ring_segment only does small arcs)."""
    p = lambda r, a: (cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a)))
    (ax, ay), (bx, by), (c2x, c2y), (dx, dy) = p(r1, a0), p(r1, a1), p(r0, a1), p(r0, a0)
    return (f"M{ax:.2f} {ay:.2f}A{r1} {r1} 0 1 0 {bx:.2f} {by:.2f}"
            f"L{c2x:.2f} {c2y:.2f}A{r0} {r0} 0 1 1 {dx:.2f} {dy:.2f}Z")


def c_page(fg, ac, bg):
    # an open C holds the ribbon in its mouth: the company's place, kept inside the name
    return (f'<path d="{c_ring(31, 32, 14.5, 25.5, 62, 298)}" fill="{fg}"/>'
            f'<path d="{notch(46, 58, 4, 60, 6)}" fill="{ac}"/>')


def stop_tail(fg, ac, bg):
    # page with ribbon; the part that sticks out past the page is the vermilion stop
    return (f'<path d="M8 4H48V50H8ZM13.5 9.5V44.5H42.5V9.5Z" fill="{fg}" fill-rule="evenodd"/>'
            f'<path d="M27 4H39V44.5H27Z" fill="{fg}"/>'
            f'<path d="{notch(27, 39, 50, 62, 6)}" fill="{ac}"/>')


def stack(fg, ac, bg):
    bars = "".join(f'<rect x="6" y="{y}" width="52" height="7" fill="{fg}"/>' for y in (8, 20, 32, 44))
    # ribbon tucked under the first page, hanging over the rest of the record
    return (bars + f'<path d="{notch(36, 49, 17, 62, 7)}" fill="{ac}" stroke="{bg}" stroke-width="3.5" paint-order="stroke"/>')



def volume(fg, ac, bg):
    # closed book: spine, cover, page block; the ribbon hangs out of the pages
    return (f'<rect x="8" y="4" width="8" height="36" fill="{fg}"/>'
            f'<rect x="19" y="4" width="37" height="36" fill="{fg}"/>'
            f'<rect x="11" y="43" width="42" height="5" fill="{fg}"/>'
            f'<path d="{notch(36, 47, 40, 62, 6)}" fill="{ac}"/>')


def drape(fg, ac, bg):
    # one ribbon draped over a page edge: front tail long, back tail short
    return (f'<path d="M8 60V26A20 20 0 0 1 48 26V48L42 42L36 48V26A8 8 0 0 0 20 26V60L14 54Z" fill="{fg}"/>')



def strands(fg, ac, bg):
    # two strands from one headband: ink for people, vermilion for agents
    return (f'<rect x="8" y="6" width="48" height="9" fill="{fg}"/>'
            f'<path d="{notch(16, 29, 15, 58, 7)}" fill="{fg}"/>'
            f'<path d="{notch(35, 48, 15, 48, 7)}" fill="{ac}"/>')


VARIANTS = [("kept-c", "The Kept C", c_page), ("stop-tail", "Stop Tail", stop_tail), ("stack", "The Stack", stack),
            ("volume", "The Volume", volume), ("drape", "The Drape", drape), ("strands", "Two Strands", strands),
            ("r1-ribbon", "R1 Ribbon", r1.ribbon)]

if __name__ == "__main__":
    for slug, _, fn in VARIANTS[:-1]:
        os.makedirs(slug, exist_ok=True)
        for kind, text in [("symbol", r1.symbol(fn)), ("lockup", r1.lockup(fn)), ("icon", r1.icon(fn))]:
            open(f"{slug}/{kind}.svg", "w").write(text)
    r1.CONCEPTS = VARIANTS
    r1.sheet("Canon - round 2, the ribbon family")
