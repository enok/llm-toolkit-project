#!/usr/bin/env python3
"""Gate a carousel before delivery: DOM type sizes, safe area, contrast, PDF text exactness.

Inputs
  --slides   HTML file: one <section class="slide"> per page (1080x1350), headline in <h1>,
             footer in an element with class "foot", diagrams as inline <svg> inside a
             "diagram" container, page counters in <span class="pg">.
  --pdf      The PDF rendered from that HTML (text is read with `pdftotext`).
  --source   Markdown with one section per slide: "## n/N <title>" followed by lines
             "Headline: ...", "Body: ...", "Footer: ...".
  --diagram-text N=TEXT   (repeatable) words that live only inside slide N's diagram, so
             the PDF multiset check accounts for them.
  --gradient-worst #RRGGBB  background to assume for text over a gradient (the lightest
             point of the gradient is the worst case for light text). Default #17203F.

Checks (any failure prints FAIL and the exit code is 1)
  - font size per role at 1080 px width: headline >= 64, body >= 36, footer >= 24, diagram >= 30;
    the last slide's disclosure line (footer text that is not a page counter) >= 32
  - every text node inside the 96 px safe area
  - WCAG contrast >= 4.5 against the effective background
  - SVG text not touching its node's edge
  - PDF text equals the source text token by token (exact multiset), page counts equal

Exit codes: 0 pass, 1 a check failed, 2 missing dependency or input.
"""
import argparse
import collections
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

JS = r"""
(gradientWorst) => {
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x)); return {r:p[0], g:p[1], b:p[2], a:p.length > 3 ? p[3] : 1}; };
  const hex = h => { const m = h.replace('#', ''); return {r:parseInt(m.slice(0,2),16), g:parseInt(m.slice(2,4),16), b:parseInt(m.slice(4,6),16), a:1}; };
  const out = [];
  [...document.querySelectorAll('.slide')].forEach((sl, si) => {
    const sr = sl.getBoundingClientRect();
    const walker = document.createTreeWalker(sl, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      const txt = n.textContent.trim(); if (!txt) continue;
      const el = n.parentElement, cs = getComputedStyle(el);
      const rg = document.createRange(); rg.selectNodeContents(n); const r = rg.getBoundingClientRect();
      const inSvg = !!el.closest('svg');
      const role = el.closest('h1') ? 'headline' : el.closest('.foot') ? 'footer' : inSvg ? 'diagram' : 'body';
      let fs = parseFloat(cs.fontSize), fg, bg;
      if (inSvg) {
        const svg = el.closest('svg'); fs = fs * svg.getScreenCTM().a;
        fg = parse(cs.fill) || parse(cs.color);
        const cx = parseFloat(el.getAttribute('x')), bb = el.getBBox(), cy = bb.y + bb.height / 2;
        const rects = [...svg.querySelectorAll('rect')].filter(rc => {
          const x=+rc.getAttribute('x'), y=+rc.getAttribute('y'), w=+rc.getAttribute('width'), h=+rc.getAttribute('height');
          return cx >= x && cx <= x+w && cy >= y && cy <= y+h; });
        const card = el.closest('.diagram') || svg.parentElement;
        const base = parse(getComputedStyle(card).backgroundColor) || hex(gradientWorst);
        bg = rects.length ? hex(rects[rects.length-1].getAttribute('fill')) : base;
        if (rects.length) {
          const rc = rects[rects.length-1];
          const x=+rc.getAttribute('x'), y=+rc.getAttribute('y'), w=+rc.getAttribute('width'), h=+rc.getAttribute('height');
          if (bb.x < x+6 || bb.x+bb.width > x+w-6 || bb.y < y+4 || bb.y+bb.height > y+h-4)
            out.push({slide: si+1, kind: 'svg-text-near-node-edge', txt});
        }
      } else {
        fg = parse(cs.color);
        let a = el; bg = null;
        while (a && a !== sl) { const b = parse(getComputedStyle(a).backgroundColor); if (b && b.a > 0.5) { bg = b; break; } a = a.parentElement; }
        if (!bg) bg = hex(gradientWorst);
      }
      out.push({slide: si+1, role, txt, fs, x: r.left-sr.left, y: r.top-sr.top, r: r.right-sr.left, b: r.bottom-sr.top, fg, bg});
    }
  });
  return out;
}
"""

FLOORS = {"headline": 64, "body": 36, "footer": 24, "diagram": 30}
fails = []


def fail(msg):
    fails.append(msg)
    print("FAIL", msg)


def lum(c):
    f = lambda v: (v / 255 / 12.92) if v / 255 <= 0.03928 else (((v / 255) + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c["r"]) + 0.7152 * f(c["g"]) + 0.0722 * f(c["b"])


def ratio(a, b):
    la, lb = lum(a), lum(b)
    if la < lb:
        la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)


def parse_source(md):
    parts = re.split(r"^## (\d+)/(\d+) ", md, flags=re.M)[1:]
    exp, total = {}, None
    for i in range(0, len(parts), 3):
        n, total, body = int(parts[i]), int(parts[i + 1]), parts[i + 2]
        def get(key):
            m = re.search(rf"^{key}: (.*)$", body, flags=re.M)
            return m.group(1).strip() if m else ""
        exp[n] = (get("Headline"), get("Body"), get("Footer"))
    return exp, total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slides", required=True, type=Path)
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--diagram-text", action="append", default=[], metavar="N=TEXT")
    ap.add_argument("--gradient-worst", default="#17203F")
    args = ap.parse_args()

    for p in (args.slides, args.pdf, args.source):
        if not p.exists():
            print(f"missing input: {p}", file=sys.stderr)
            return 2
    try:
        from playwright.sync_api import sync_playwright  # lazy: only this gate needs a browser
    except ImportError:
        print("playwright is not installed: pip install playwright && python -m playwright install chromium", file=sys.stderr)
        return 2

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(args.slides.resolve().as_uri())
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        pg.evaluate("() => { const e = document.querySelectorAll('.pg'); e.forEach((x, i) => x.textContent = `${i+1}/${e.length}`) }")
        items = pg.evaluate(JS, args.gradient_worst)
        fonts = pg.evaluate("() => [...new Set([...document.querySelectorAll('.slide *')].map(e => getComputedStyle(e).fontFamily.split(',')[0].replace(/\"/g, '')))]")
        b.close()

    last = max((it["slide"] for it in items), default=0)
    minfs = collections.defaultdict(lambda: 1e9)
    mincr, mincr_item = 1e9, None
    for it in items:
        if it.get("kind"):
            fail(f"slide {it['slide']}: {it['kind']} {it['txt']!r}")
            continue
        role = it["role"]
        minfs[role] = min(minfs[role], it["fs"])
        if role == "footer" and it["slide"] == last and not re.fullmatch(r"\d+/\d+", it["txt"]) and it["fs"] < 32:
            fail(f"last-slide disclosure < 32px: {it['txt'][:40]!r}")
        if it["fs"] < FLOORS[role] - 0.01:
            fail(f"slide {it['slide']} {role} font {it['fs']:.1f}px < {FLOORS[role]}: {it['txt'][:40]!r}")
        if it["x"] < 95.5 or it["r"] > 984.5 or it["y"] < 95.5 or it["b"] > 1254.5:
            fail(f"slide {it['slide']} outside 96px safe area: {it['txt'][:40]!r}")
        cr = ratio(it["fg"], it["bg"])
        if cr < mincr:
            mincr, mincr_item = cr, (it["slide"], it["txt"][:30])
        if cr < 4.5:
            fail(f"slide {it['slide']} contrast {cr:.2f} < 4.5: {it['txt'][:40]!r}")
    print("min font px by role:", {k: round(v, 1) for k, v in minfs.items()})
    if mincr_item:
        print(f"min text contrast: {mincr:.2f} at slide {mincr_item[0]} {mincr_item[1]!r}")
    print("font families used:", fonts)

    exp, total = parse_source(args.source.read_text(encoding="utf-8"))
    diag = {}
    for spec in args.diagram_text:
        n, _, text = spec.partition("=")
        diag[int(n)] = text
    norm = lambda s: unicodedata.normalize("NFKC", s)
    tok = lambda s: norm(s).split()
    if len(exp) != total:
        fail(f"source has {len(exp)} sections but declares {total} slides")
    try:
        text = subprocess.run(["pdftotext", "-enc", "UTF-8", str(args.pdf), "-"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"pdftotext not usable: {exc}", file=sys.stderr)
        return 2
    pages = [x for x in text.split("\f") if x.strip()]
    if len(pages) != len(exp):
        fail(f"pdf pages {len(pages)} vs source {len(exp)}")
    for n, (h, bd, ft) in exp.items():
        want = tok(h) + tok(bd) + tok(ft) + [f"{n}/{total}"] + tok(diag.get(n, ""))
        got = tok(pages[n - 1]) if n - 1 < len(pages) else []
        cw, cg = collections.Counter(want), collections.Counter(got)
        if cw != cg:
            fail(f"slide {n} PDF text mismatch: missing={dict(cw - cg)} extra={dict(cg - cw)}")
        dom = re.sub(r"\s+", " ", " ".join(norm(i["txt"]) for i in items if i["slide"] == n and i.get("role") not in (None, "diagram")))
        wantdom = " ".join(tok(h) + tok(bd) + tok(ft) + [f"{n}/{total}"])
        if dom.replace(" ", "") != wantdom.replace(" ", ""):
            fail(f"slide {n} HTML text order or content differs from the source")
    print("text check: pages", len(pages), "compared", len(exp))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
