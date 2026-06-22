"""抓取微信公众号文章 - 精确提取文章内容区域的图片"""
import asyncio, re, os, hashlib, aiohttp
from pathlib import Path
from urllib.parse import urljoin
from playwright.async_api import async_playwright

async def fetch_wechat_article(url: str, output_dir: str = None):
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'output'
    else:
        output_dir = Path(output_dir)
    
    img_dir = output_dir / 'images'
    img_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(3000)

        # Wait for lazy images to load
        await page.evaluate("""
            document.querySelectorAll('img[data-src]').forEach(img => {
                img.src = img.getAttribute('data-src');
            });
        """)
        await page.wait_for_timeout(2000)

        # Get article title
        title_el = await page.query_selector('#activity-name')
        article_title = await title_el.inner_text() if title_el else '微信文章'

        # Target article content area
        content_el = await page.query_selector('#js_content')
        if not content_el:
            content_el = await page.query_selector('.rich_media_content')

        # Extract markdown from article content
        if content_el:
            # Get inner text preserving structure
            md_lines = [f'# {article_title}\n']
            
            # Walk through child elements
            children = await content_el.query_selector_all('*')
            
            # Build text content with proper structure
            # First get HTML
            html = await content_el.inner_html()
        else:
            html = await page.content()
            md_lines = [f'# {article_title}\n']

        # Find all images in content area
        imgs = await content_el.query_selector_all('img') if content_el else []
        print(f'Found {len(imgs)} images in article content area')

        img_urls = []
        for i, img in enumerate(imgs):
            src = await img.get_attribute('data-src') or await img.get_attribute('src') or ''
            if not src or src.startswith('data:'):
                # Only skip data URIs, not SVG or other formats
                if src.startswith('data:'):
                    print(f'  [{i}] SKIP data URI')
                    continue

            # Skip WeChat emoji images (very small icon-like paths)
            if 'mmbiz_emoji' in src.lower() or 'icon' in src.lower() and 'emoji' in src.lower():
                print(f'  [{i}] SKIP emoji: {src[:80]}')
                continue

            img_urls.append((i, src))
            print(f'  [{i}] DETECT: {src[:100]}')

        # Download images
        img_map = {}
        for idx, src in img_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {'Referer': 'https://mp.weixin.qq.com/'}
                    async with session.get(src, headers=headers, timeout=15) as resp:
                        if resp.status != 200:
                            print(f'  [{idx}] FAIL HTTP {resp.status}')
                            continue
                        content = await resp.read()
                        
                        # Determine extension
                        ct = resp.headers.get('Content-Type', '')
                        if 'png' in ct:
                            ext = 'png'
                        elif 'jpeg' in ct or 'jpg' in ct:
                            ext = 'jpg'
                        elif 'webp' in ct:
                            ext = 'webp'
                        elif 'gif' in ct:
                            ext = 'gif'
                        elif 'svg' in ct:
                            ext = 'svg'
                        else:
                            ext = src.split('?')[0].split('.')[-1].lower()
                            if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'):
                                ext = 'jpg'

                        # Use hash-based filename for wechat images (CDN URLs have no meaningful name)
                        fname = f'wechat_img_{idx}_{hashlib.md5(content[:1024]).hexdigest()[:8]}.{ext}'
                        fpath = img_dir / fname
                        fpath.write_bytes(content)
                        img_map[src] = f'images/{fname}'
                        print(f'  [{idx}] OK {fname} ({len(content)} bytes)')
            except Exception as e:
                print(f'  [{idx}] ERROR: {e}')

        print(f'\nDownloaded {len(img_map)} article images')

        # Convert HTML to markdown (simple approach for wechat articles)
        def html_to_md(html_text, img_map):
            """Convert wechat article HTML to markdown"""
            # Replace image tags first
            def replace_img(m):
                src = m.group(1)
                local = img_map.get(src, src)
                return f'\n\n![文章配图]({local})\n\n'
            
            html_text = re.sub(r'<img[^>]+?data-src="([^"]+)"[^>]*/?>', replace_img, html_text)
            html_text = re.sub(r'<img[^>]+?src="([^"]+)"[^>]*/?>', replace_img, html_text)
            
            # Handle text formatting
            html_text = html_text.replace('<strong>', '**').replace('</strong>', '**')
            html_text = html_text.replace('<em>', '*').replace('</em>', '*')
            html_text = html_text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
            
            # Handle paragraphs
            html_text = re.sub(r'<p[^>]*>', '\n\n', html_text)
            html_text = re.sub(r'</p>', '', html_text)
            
            # Handle section headers
            html_text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', html_text)
            html_text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', html_text)
            html_text = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', html_text)
            
            # Handle spans
            html_text = re.sub(r'<span[^>]*>', '', html_text)
            html_text = re.sub(r'</span>', '', html_text)
            
            # Handle sections/divs
            html_text = re.sub(r'<section[^>]*>', '\n', html_text)
            html_text = re.sub(r'</section>', '\n', html_text)
            html_text = re.sub(r'<div[^>]*>', '\n', html_text)
            html_text = re.sub(r'</div>', '', html_text)
            
            # Remove remaining HTML tags
            html_text = re.sub(r'<[^>]+>', '', html_text)
            
            # Clean up multiple blank lines
            html_text = re.sub(r'\n{3,}', '\n\n', html_text)
            
            # Decode HTML entities
            html_text = html_text.replace('&nbsp;', ' ')
            html_text = html_text.replace('&amp;', '&')
            html_text = html_text.replace('&lt;', '<')
            html_text = html_text.replace('&gt;', '>')
            html_text = html_text.replace('&quot;', '"')
            html_text = html_text.replace('&mdash;', '—')
            html_text = html_text.replace('&ldquo;', '"')
            html_text = html_text.replace('&rdquo;', '"')
            
            return html_text.strip()

        md_content = html_to_md(html, img_map)
        md_content = f'# {article_title}\n\n> 来源: {url}\n\n{md_content}'

        # Save markdown
        safe_title = re.sub(r'[\\/:*?"<>|]', '-', article_title)[:100]
        md_path = output_dir / f'{safe_title}.md'
        md_path.write_text(md_content, encoding='utf-8')
        print(f'\nSaved: {md_path}')

        await browser.close()
        return str(md_path)

if __name__ == '__main__':
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://mp.weixin.qq.com/s/ViHLk2Kp30_2Oj0h_ZNVSA'
    output = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(fetch_wechat_article(url, output))
