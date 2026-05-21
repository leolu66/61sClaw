"""检查微信文章中的实际图片"""
import sys
from playwright.sync_api import sync_playwright

URL = "https://mp.weixin.qq.com/s/TmfRrr80PQLKaje3Bjas5A"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0",
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN"
    )
    page = context.new_page()
    page.add_init_script("""Object.defineProperty(navigator,"webdriver",{get:()=>undefined})""")
    page.goto(URL, timeout=30000)
    page.wait_for_timeout(5000)

    # Scroll multiple times to trigger lazy loading
    for _ in range(5):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

    # Get all image sources from HTML
    result = page.evaluate("""() => {
        const imgs = document.querySelectorAll('img');
        return Array.from(imgs).map(img => ({
            src: img.currentSrc || img.src || '',
            data_src: img.getAttribute('data-src') || '',
            data_croporisrc: img.getAttribute('data-croporisrc') || '',
            width: img.naturalWidth || img.width,
            height: img.naturalHeight || img.height,
            alt: (img.alt || '').substring(0, 50)
        }));
    }""")

    total = len(result)
    data_urls = [i for i in result if i["src"].startswith("data:")]
    real_urls = [i for i in result if not i["src"].startswith("data:")]
    
    print(f"Total <img> tags: {total}")
    print(f"Data URLs (placeholders): {len(data_urls)}")
    print(f"Real image URLs: {len(real_urls)}")
    print()

    # Also check data-src attributes that might have real URLs
    data_src_imgs = [i for i in result if i["data_src"] and not i["data_src"].startswith("data:")]
    print(f"Images with real data-src: {len(data_src_imgs)}")
    
    print("\n--- Real src images ---")
    for img in real_urls:
        sz = f"({img['width']}x{img['height']})" if img['width'] > 0 else "(lazy)"
        print(f"  [{sz}] {img['src'][:120]}")
    
    print("\n--- Images with real data-src ---")
    for img in data_src_imgs:
        if img['src'].startswith('data:'):
            print(f"  data-src={img['data_src'][:120]}  alt={img['alt']}")

    browser.close()
