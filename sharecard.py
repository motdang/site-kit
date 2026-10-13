#!/usr/bin/env python3
"""Check a live page's link card the way Bluesky and Mastodon build it.

    python3 sharecard.py https://nanobotco.github.io/gargoyles/ [more urls]
    python3 sharecard.py --file urls.txt          # one url per line
    python3 sharecard.py --json ...               # one JSON object per url

Bluesky: asks cardyb.bsky.app, the service the Bluesky app uses, what it sees,
then fetches the image through it. Mastodon: fetches the page and the image
with a Mastodon server's User-Agent and reads the Open Graph tags, as a
Mastodon server does. Exit status 1 when any url has a problem.
"""
import argparse, io, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from html.parser import HTMLParser

MASTODON_UA = "http.rb/5.2.0 (Mastodon/4.3.0; +https://mastodon.social/)"
CARDYB = "https://cardyb.bsky.app/v1/extract?url="
RASTER = ("image/jpeg", "image/png", "image/webp", "image/gif")


class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.title, self._in_title = {}, "", False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            k = a.get("property") or a.get("name")
            if k and "content" in a:
                self.tags.setdefault(k.lower(), a["content"])
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "head":
            raise StopIteration

    def handle_data(self, d):
        if self._in_title:
            self.title += d


def get(url, ua, limit=12_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.headers.get("content-type", ""), r.geturl(), r.read(limit)


def get_bsky(url):
    """cardyb answers 403 for a while after a burst; wait and ask again."""
    for wait in (0, 20, 60):
        time.sleep(wait)
        try:
            return get(url, "sharecard.py")
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429):
                raise
    return get(url, "sharecard.py")


def size_of(data):
    try:
        from PIL import Image
        return Image.open(io.BytesIO(data)).size
    except Exception:
        return None


def check(url):
    out = {"url": url, "problems": [], "notes": []}
    p, n = out["problems"], out["notes"]

    # Mastodon
    try:
        st, ct, final, body = get(url, MASTODON_UA, 3_000_000)
    except Exception as e:
        p.append(f"page: {e}")
        return out
    if "html" not in ct:
        p.append(f"page served as {ct or 'no type'} to Mastodon")
        return out
    m = Meta()
    try:
        m.feed(body.decode("utf-8", "replace"))
    except StopIteration:
        pass
    t = m.tags
    out["title"] = t.get("og:title") or m.title.strip()
    if not t.get("og:title"):
        p.append("no og:title")
    if not t.get("og:description"):
        p.append("no og:description")
    img = t.get("og:image") or t.get("twitter:image")
    if not img:
        p.append("no og:image")
    else:
        if not re.match(r"https?://", img):
            p.append(f"og:image not absolute: {img}")
            img = urllib.parse.urljoin(final, img)
        out["image"] = img
        try:
            ist, ict, _, data = get(img, MASTODON_UA)
            if ict.split(";")[0] not in RASTER:
                p.append(f"og:image is {ict or 'no type'}, not a raster image")
            else:
                wh = size_of(data)
                out["size"] = wh
                if wh and (wh[0] < 600 or wh[0] / max(wh[1], 1) < 1.4):
                    p.append(f"og:image {wh[0]}×{wh[1]} — Mastodon shows a small square, not a wide card")
                if len(data) > 1_000_000:
                    n.append(f"og:image {len(data)//1024} KB")
        except Exception as e:
            p.append(f"og:image fetch: {e}")
    if t.get("twitter:card") != "summary_large_image":
        n.append("twitter:card not summary_large_image")
    if not t.get("og:image:alt"):
        n.append("no og:image:alt")

    # Bluesky
    try:
        _, _, _, raw = get_bsky(CARDYB + urllib.parse.quote(url, safe=""))
        b = json.loads(raw)
        if b.get("likely_type") not in ("html", ""):
            p.append(f"Bluesky reads it as {b.get('likely_type')}")
        if not b.get("image"):
            p.append("Bluesky card has no image")
        else:
            ist, ict, _, _ = get_bsky(b["image"])
            if not ict.startswith("image/"):
                p.append(f"Bluesky image proxy returned {ict}")
    except Exception as e:
        p.append(f"Bluesky: {e}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    urls = list(a.urls)
    if a.file:
        urls += [l.strip() for l in open(a.file) if l.strip() and not l.startswith("#")]
    bad = 0
    for u in urls:
        r = check(u)
        bad += bool(r["problems"])
        if a.json:
            print(json.dumps(r, ensure_ascii=False), flush=True)
        else:
            mark = "✗" if r["problems"] else "✓"
            print(f"{mark} {u}  " + " · ".join(r["problems"] + r["notes"]), flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
