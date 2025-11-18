
# backend/ai_engine/capture_worker.py
from playwright.sync_api import sync_playwright
import os, sys, requests

def resolve_url(short_url):
    try:
        print(f"Resolving URL: {short_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }
        r = requests.head(short_url, headers=headers, allow_redirects=True, timeout=10)
        print(f"Final URL: {r.url}")
        return r.url
    except Exception as e:
        print(f"Error resolving URL: {str(e)}")
        return short_url

def capture_flipkart_image(page, url):
    """Handle Flipkart product pages"""
    page.goto(url)
    page.wait_for_selector('div._3kidJX img, ._2r_T1I')
    return page.query_selector('div._3kidJX img, ._2r_T1I')

def capture_amazon_image(page, url):
    """Handle Amazon product pages"""
    page.goto(url)
    page.wait_for_selector('#landingImage, #imgBlkFront')
    return page.query_selector('#landingImage, #imgBlkFront')

def main():
    if len(sys.argv) < 3:
        print("Usage: python capture_worker.py <url> <output_path>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    output_path = sys.argv[2]

    # Resolve short links
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
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720}  # Smaller viewport for faster loading
        )
        page = context.new_page()
        # Reduce timeouts to fail faster
        page.set_default_navigation_timeout(15000)  # 15s timeout
        page.set_default_timeout(10000)  # 10s timeout for other operations

        try:
            print(f"Navigating to URL: {url}")
            response = page.goto(url, wait_until="domcontentloaded")
            if not response.ok:
                print(f"Navigation failed with status: {response.status}")
                sys.exit(1)
            print("Page loaded successfully")
        except Exception as e:
            print(f"Failed to load page: {str(e)}")
            sys.exit(1)

        print("Searching for product image...")
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

        # Try specific handlers first
        try:
            if "flipkart.com" in url:
                img = capture_flipkart_image(page, url)
                if img:
                    img.screenshot(path=output_path)
                    browser.close()
                    sys.exit(0)
            elif "amazon" in url:
                img = capture_amazon_image(page, url)
                if img:
                    img.screenshot(path=output_path)
                    browser.close()
                    sys.exit(0)
        except Exception as e:
            print(f"Specific handler failed: {str(e)}, trying generic approach...")

        # Generic approach: Find largest visible image
        imgs = page.query_selector_all("img")
        biggest = None
        max_area = 0
        for img in imgs:
            try:
                box = img.bounding_box()
                if box and box["width"] > 100 and box["height"] > 100:  # Minimum size threshold
                    area = box["width"] * box["height"]
                    # Check if image is visible
                    is_visible = page.evaluate("""el => {
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && 
                               style.visibility !== 'hidden' && 
                               style.opacity !== '0'
                    }""", img)
                    if is_visible and area > max_area:
                        max_area = area
                        biggest = img
            except Exception:
                continue
                
        if biggest:
            biggest.screenshot(path=output_path)
            browser.close()
            sys.exit(0)
            
        print("No suitable product image found")
        browser.close()
        sys.exit(1)

if __name__ == '__main__':
    main()
