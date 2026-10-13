# site-kit

Small pieces that travel between the sites, the way `search-core` and `fleet.py` do.
Copy the two files into a project, include the CSS, import the function.

## bands — full-bleed parallax sections

A photograph that holds still while the page scrolls over it, with type on top.

```python
from bands import band
html = band("images/pai/canyon.jpg", kicker="Pai",
            head="Six hundred kilometres of this",
            line="Chiang Mai out, Pai, Mae Hong Son, home.",
            credit='Somebody · <a href="...">CC BY-SA 4.0</a>',
            href="legs/", cta="Every leg", cls="right tall")
```

Variants: `right` (type to the right, tint mirrored), `tall`, `short`. A band with
`big=` prints a single huge figure with a caption under it, which is the form to use
for one measured number.

The host page supplies `--ink`, `--accent`, `--display` and `--body`; everything else
is in `bands.css`.

### The four layers

1. the photograph — `background-attachment: fixed`, which is the whole trick
2. `::before` — a gradient scrim, heaviest where the type sits
3. `::after` — a flat brand tint on `mix-blend-mode: multiply`
4. the type

Both pseudo-elements sit at negative `z-index` under an `isolation: isolate` parent,
so they cannot escape the band.

### Things that cost a rebuild

- **`background-attachment: fixed` sizes the image to the VIEWPORT, not the element.**
  So use landscape pictures. A portrait one gets cropped to a letterbox of its middle.
- **Mobile Safari has never supported it,** and it forces a repaint every scroll frame.
  The stylesheet switches it off for `(pointer:coarse)` and `(prefers-reduced-motion)`,
  where it falls back to a plain cover image that still looks right.
- **Pick the pictures by hand.** A search for a place name returns plenty that is
  correctly licensed, accurate and useless — a highway sign, an airport apron, a museum
  knife. A band is the largest thing on the page. It gets a named shortlist.
- **A band is a heading.** Printing the same words as an `<h2>` under it gives the page
  two identical headings.
- **The credit belongs on the band,** not in a colophon. A borrowed photograph carries
  its licence wherever it is shown.

### A trap that is not about bands but bites the same layouts

A CSS grid `gap` over `background: var(--ink)` draws bright hairlines in dark mode,
because `--ink` is the light colour there. Give the cells their own borders instead.

## Built for

First used on [the Mae Hong Son Loop](https://nanobotco.github.io/mae-hong-son-loop/),
56 bands across 40 pages.

## sharecard — the link card Mastodon and Bluesky will show

```
python3 sharecard.py https://nanobotco.github.io/gargoyles/
python3 sharecard.py --file urls.txt
```

Asks `cardyb.bsky.app`, the service the Bluesky app builds cards with, and fetches the
page and its image with a Mastodon server's User-Agent. ✓ means both get a title, a
description and a wide raster image. Exit status 1 on any ✗.

What has failed it:

- **A relative `og:image`.** Browsers resolve it; Bluesky does not.
- **A portrait `og:image`.** Both show it as a small square beside the text.
- **A bot gate.** Bluesky's fetcher sends a Chrome string from AWS. motdang.net's
  data-centre redirect caught it until `classify.js` named `Bluesky Cardyb`.
- **Bursts.** cardyb answers 403 for a minute after ~10 parallel asks; the script waits
  and retries.
