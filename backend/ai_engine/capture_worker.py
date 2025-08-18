
# backend/ai_engine/capture_worker.py
from playwright.sync_api import sync_playwright
import os, sys, requests

def resolve_url(short_url):
    try:
        r = requests.get(short_url, allow_redirects=True, timeout=10)
        return r.url
    except Exception:
        return short_url

def main():
    if len(sys.argv) < 3:
        print("Usage: python capture_worker.py <url> <output_path>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    output_path = sys.argv[2]

    # Resolve Amazon short link
    url = resolve_url(url)
    print(f"Resolved URL: {url}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    selectors = [
        'img#landingImage',
        'img[data-old-hires]',
        'img[data-image]',
        'img.a-dynamic-image',
        '.image-gallery img',
        'img'
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_navigation_timeout(60000)  # 60s max

        page.goto(url, wait_until="domcontentloaded")

        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    box = el.bounding_box()
                    if box and box['width'] > 10 and box['height'] > 10:
                        el.screenshot(path=output_path)
                        browser.close()
                        sys.exit(0)
            except Exception:
                continue

        imgs = page.query_selector_all("img")
        biggest = None
        max_area = 0
        for img in imgs:
            try:
                box = img.bounding_box()
                if box:
                    area = box["width"] * box["height"]
                    if area > max_area:
                        max_area = area
                        biggest = img
            except Exception:
                continue

        if biggest:
            biggest.screenshot(path=output_path)
            browser.close()
            sys.exit(0)

        page.screenshot(path=output_path, full_page=True)
        browser.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
