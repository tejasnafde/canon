# Canon brand: final mark ("The Ribbon")

A page outline with a bookmark ribbon: the company's place is kept, the ribbon marks what was decided.
Colours: paper `#f6f1e7`, ink `#1c1a17`, vermilion `#c8361e`.

The colour mark uses a vermilion ribbon. It ties the mark to the product's one accent (the colour Canon
uses for a blocked or drifted decision) and makes the ribbon read at a glance, even at 16px. The mono
and white versions stay for one-colour uses: print, embossing, dark backgrounds, and anywhere red would
mean "error".

| File | Use it for |
|---|---|
| `canon-lockup.svg` | Default logo: web header, README, deck title slide (light background) |
| `canon-lockup-white.svg` | Lockup on ink or photo backgrounds, dark deck slides |
| `canon-lockup-mono.svg` | One-colour print, fax-like or greyscale contexts |
| `canon-symbol.svg` | The mark alone, when "Canon" is already written nearby (nav bar, loading state) |
| `canon-symbol-mono.svg` / `-white.svg` | The mark alone, one colour, light or dark background |
| `canon-icon.svg` | App icon: paper mark on an ink rounded square |
| `png/canon-symbol*-<px>.png` | Raster symbol, 16 to 1024. The 16px file uses a redrawn small master |
| `png/canon-icon-512.png`, `-1024.png` | Store listings, slide thumbnails |
| `favicon.ico` | Browser tab (16, 32 hand-hinted on the pixel grid; 48) |
| `apple-touch-icon.png` | iOS home screen, 180px |
| `og-image.png` | Link previews (`og:image`, `twitter:image`), 1200x630 |
| `discord-avatar.png` | Canon bot avatar on Discord, 1024px |
| `../northwind/northwind-icon*` | Server icon for **Northwind Labs**, the made-up demo company. Not the Canon mark |

```html
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/canon-symbol.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:image" content="https://canon.tn07.dev/og-image.png">
```

Rebuild everything: `cd brand/final && python3 build.py` (needs `rsvg-convert` and Pillow).
The wordmark is Fraunces converted to a path (`../wordmark.json`), so no SVG needs the font.
