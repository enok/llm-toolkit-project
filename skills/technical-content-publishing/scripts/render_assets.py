#!/usr/bin/env python3
"""slides: HTML -> <slug>-carousel.pdf + slide-NN.png (1080x1350)  |  cover: HTML -> cover.png (1600x900)
Usage: render_assets.py slides <src.html> <outdir> <slug>   |   render_assets.py cover <src.html> <outdir>"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def main() -> int:
    mode, src, out = sys.argv[1], Path(sys.argv[2]).resolve(), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    w, h = (1080, 1350) if mode == "slides" else (1600, 900)
    with sync_playwright() as p:
        browser = p.chromium.launch()  # containers without a sandbox: args=["--no-sandbox"]
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        page.goto(src.as_uri()); page.wait_for_load_state("networkidle"); page.evaluate("document.fonts.ready")
        if mode == "slides":
            page.evaluate("""() => { const pg = document.querySelectorAll('.pg'); pg.forEach((e, i) => e.textContent = `${i + 1}/${pg.length}`); }""")
            bad = page.evaluate("""() => [...document.querySelectorAll('.slide')]
              .map((s, i) => ({slide: i + 1, over: s.scrollHeight > s.clientHeight + 1 || s.scrollWidth > s.clientWidth + 1}))
              .filter(x => x.over)""")
            if bad:
                print("OVERFLOW on slides:", [b["slide"] for b in bad]); return 1
            page.pdf(path=str(out / f"{sys.argv[4]}-carousel.pdf"), width=f"{w}px", height=f"{h}px",
                     print_background=True, prefer_css_page_size=True)
            for i, el in enumerate(page.query_selector_all(".slide"), 1):
                el.screenshot(path=str(out / f"slide-{i:02d}.png"))
        else:
            page.screenshot(path=str(out / "cover.png"), clip={"x": 0, "y": 0, "width": w, "height": h})
        browser.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
