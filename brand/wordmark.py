"""Convert "Canon" set in Fraunces to one SVG path, so no SVG needs the font.

Usage: python wordmark.py <fontsource fraunces-latin-full-normal.woff2>
Writes wordmark.json {d, width}; units are cap height = 100, baseline at y=100.
Needs fonttools + brotli.
"""
import json, sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

f = instantiateVariableFont(TTFont(sys.argv[1]), {"wght": 560, "opsz": 72, "SOFT": 0, "WONK": 0})
gs, cmap = f.getGlyphSet(), f.getBestCmap()
s = 100 / f["OS/2"].sCapHeight
pen, x = SVGPathPen(gs), 0
for ch in "Canon":  # ponytail: default advances + light tracking, no GPOS kerning
    g = cmap[ord(ch)]
    gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x * s, 100)))
    x += gs[g].width + 10
json.dump({"d": pen.getCommands(), "width": round(x * s, 1)}, open("wordmark.json", "w"))
