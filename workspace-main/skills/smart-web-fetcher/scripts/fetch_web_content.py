#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能网页内容抓取工具
自动选择web_fetch或playwright模式抓取网页内容
支持自动提取网页标题生成文件名
支持自动下载图片至本地 images/ 目录并替换引用地址
"""
import argparse
import sys
import os
import json
import time
import re
import hashlib
from pathlib import Path
import requests
from urllib.parse import urlparse, urljoin

# 修复Windows控制台中文输出
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 默认输出目录(相对于skill目录)
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "output"

# 合法图片扩展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico'}

# 图片下载请求超时(秒)
IMAGE_DOWNLOAD_TIMEOUT = 15


def sanitize_filename(title, max_length=200):
    """
    将标题转换为Windows兼容的文件名
    - 替换非法字符为 "-"
    - 去除首尾空格和点号
    - 截断过长的文件名
    """
    illegal_chars = r'[\\/:*?"<>|]'
    sanitized = re.sub(illegal_chars, '-', title)
    sanitized = re.sub(r'-+', '-', sanitized)
    sanitized = sanitized.strip('. ')
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('-').strip()
    return sanitized if sanitized else "untitled"


def extract_title_from_markdown(markdown_content):
    """从markdown内容中提取第一个h1标题"""
    if not markdown_content:
        return None
    lines = markdown_content.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('## '):
            return stripped[2:].strip()
        if stripped.startswith('#') and not stripped.startswith('## '):
            return stripped[1:].strip()
    return None


def is_data_url(url):
    """判断是否为data: URL"""
    url_stripped = url.strip()
    return url_stripped.startswith('data:') or url_stripped.startswith('data ')


def is_real_image_url(url):
    """判断URL是否为真实的图片URL(非empty、非data、非页面自身URL)"""
    url_stripped = url.strip()
    if not url_stripped:
        return False
    if is_data_url(url_stripped):
        return False
    # 排除页面自身的URL(有些wx文章会把文章链接作为img src)
    if '.html' in url_stripped or '/s/' in url_stripped:
        return False
    return True


def extract_image_urls_from_html(html_content, base_url=None):
    """
    从原始HTML中提取所有真实图片URL
    检测: src, data-src, data-croporisrc, data-cropx1 等
    返回: set of resolved URLs
    """
    urls = set()
    
    patterns = [
        r'src=["\']([^"\']+)["\']',
        r'data-src=["\']([^"\']+)["\']',
        r'data-croporisrc=["\']([^"\']+)["\']',
        r'data-cropx1=["\']([^"\']+)["\']',
        r'original-src=["\']([^"\']+)["\']',
        r'data-original-src=["\']([^"\']+)["\']',
        r'file=["\']([^"\']+)["\']',
        r'data-file=["\']([^"\']+)["\']',
    ]
    
    for pattern in patterns:
        for m in re.finditer(pattern, html_content, re.IGNORECASE):
            url = m.group(1).strip()
            if is_real_image_url(url):
                resolved = urljoin(base_url, url) if base_url else url
                urls.add(resolved)
    
    return urls


def extract_image_urls_from_markdown(content, base_url=None):
    """
    从markdown格式内容中提取图片URL
    返回: list of (original_text_fragment, resolved_url)
    """
    results = []
    
    # Markdown 图片: ![alt](url) 或 ![alt](url "title")
    for m in re.finditer(r'(!\[.*?\]\()([^)\s]+)([^)]*\))', content):
        url = m.group(2).strip()
        if is_real_image_url(url):
            resolved = urljoin(base_url, url) if base_url else url
            results.append((m.group(0), resolved))
    
    # HTML img 标签中的 src
    for m in re.finditer(r'(<img[^>]+src=)["\']([^"\']+)["\']', content, re.IGNORECASE):
        url = m.group(2).strip()
        if is_real_image_url(url):
            resolved = urljoin(base_url, url) if base_url else url
            results.append((m.group(0), resolved))
    
    # data-src
    for m in re.finditer(r'(data-src=)["\']([^"\']+)["\']', content, re.IGNORECASE):
        url = m.group(2).strip()
        if is_real_image_url(url):
            resolved = urljoin(base_url, url) if base_url else url
            results.append((m.group(0), resolved))
    
    # data-croporisrc
    for m in re.finditer(r'(data-croporisrc=)["\']([^"\']+)["\']', content, re.IGNORECASE):
        url = m.group(2).strip()
        if is_real_image_url(url):
            resolved = urljoin(base_url, url) if base_url else url
            results.append((m.group(0), resolved))
    
    return results


def download_image(url, images_dir, index, total):
    """
    下载单张图片
    返回: (local_filename, success)
    """
    try:
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
        
        # 从URL推断扩展名
        path_part = url.split('?')[0].split('#')[0]
        ext = Path(path_part).suffix.lower()
        if ext not in IMAGE_EXTENSIONS:
            ext = '.jpg'
        
        filename = f"{url_hash}{ext}"
        filepath = images_dir / filename
        
        if filepath.exists():
            print(f"  [{index}/{total}] ⏭️ 已存在: {filename}", file=sys.stderr)
            return filename, True
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': url,
        }
        resp = requests.get(url, headers=headers, timeout=IMAGE_DOWNLOAD_TIMEOUT, stream=True)
        resp.raise_for_status()
        
        # 根据Content-Type修正扩展名
        content_type = resp.headers.get('content-type', '')
        ct_to_ext = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
            'image/bmp': '.bmp',
            'image/x-icon': '.ico',
        }
        if content_type and not content_type.startswith('image/'):
            # 非图片内容不下载
            print(f"  [{index}/{total}] ⚠️ 非图片类型({content_type}): {url[:80]}...", file=sys.stderr)
            return None, False
        
        for ct, e in ct_to_ext.items():
            if content_type.startswith(ct) and e != ext:
                filename = f"{url_hash}{e}"
                filepath = images_dir / filename
                if filepath.exists():
                    print(f"  [{index}/{total}] ⏭️ 已存在: {filename}", file=sys.stderr)
                    return filename, True
                break
        
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        size_kb = filepath.stat().st_size / 1024
        print(f"  [{index}/{total}] ✅ {filename} ({size_kb:.1f} KB)", file=sys.stderr)
        return filename, True
    
    except requests.exceptions.Timeout:
        print(f"  [{index}/{total}] ⏰ 超时: {url[:80]}...", file=sys.stderr)
        return None, False
    except requests.exceptions.RequestException as e:
        print(f"  [{index}/{total}] ❌ 下载失败: {str(e)[:60]}", file=sys.stderr)
        return None, False
    except Exception as e:
        print(f"  [{index}/{total}] ❌ 未知错误: {str(e)[:60]}", file=sys.stderr)
        return None, False


def fix_lazy_images_in_html(html_content):
    """
    在markdownify转换前修复懒加载图片：
    将 <img src="data:..." data-src="https://real.jpg"> 
    替换为 <img src="https://real.jpg">
    否则 markdownify 只会生成 ![](data:...) 占位符
    返回: 修复后的html
    """
    def replace_src(match):
        tag = match.group(0)
        # 检查 src 是否是 data: 或空
        src_match = re.search(r'src=["\']([^"\']*)["\']', tag, re.IGNORECASE)
        src = src_match.group(1) if src_match else ''
        
        # 如果 src 已经是真实URL，不修改
        if src and not (src.startswith('data:') or len(src) < 10):
            return tag
        
        # 尝试从 data-src / data-croporisrc 获取真实URL
        for attr in ['data-src', 'data-croporisrc', 'data-original-src']:
            ds_match = re.search(attr + r'=["\']([^"\']+)["\']', tag, re.IGNORECASE)
            if ds_match and not ds_match.group(1).startswith('data:'):
                real_url = ds_match.group(1)
                # 替换 src 属性
                if src_match:
                    tag = tag[:src_match.start(1)] + real_url + tag[src_match.end(1):]
                else:
                    # 没有src属性,添加一个
                    tag = tag.replace('<img', '<img src="' + real_url + '"')
                return tag
                
        return tag
    
    # 匹配 <img ... > 标签
    return re.sub(r'<img[^>]+>', replace_src, html_content, flags=re.IGNORECASE)


def download_and_replace_images(content, output_dir, base_url=None, extra_image_urls=None):
    """
    从markdown内容中提取图片URL并下载替换
    extra_image_urls: 通过其他途径(如原始HTML)额外发现的图片URL
    """
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # 从markdown中提取常规图片URL
    md_image_urls = extract_image_urls_from_markdown(content, base_url)
    
    # 合并所有图片URL(去重)
    all_urls_set = set()
    for _, resolved_url in md_image_urls:
        all_urls_set.add(resolved_url)
    if extra_image_urls:
        for url in extra_image_urls:
            all_urls_set.add(url)
    
    all_urls = list(all_urls_set)
    
    if not all_urls:
        return content
    
    total = len(all_urls)
    print(f"🖼️ 发现 {total} 张图片,开始下载...", file=sys.stderr)
    
    # 下载所有图片
    url_download_map = {}
    for i, url in enumerate(all_urls, 1):
        filename, success = download_image(url, images_dir, i, total)
        if success:
            url_download_map[url] = filename
    
    if not url_download_map:
        print("⚠️ 没有成功下载任何图片", file=sys.stderr)
        return content
    
    print(f"📎 成功下载 {len(url_download_map)}/{total} 张图片,替换引用地址...", file=sys.stderr)
    
    # 替换引用: 从长到短排序避免部分匹配
    sorted_urls = sorted(url_download_map.keys(), key=len, reverse=True)
    
    for url in sorted_urls:
        local_path = f"images/{url_download_map[url]}"
        
        # 替换 markdown ![](url) 格式
        content = re.sub(
            re.escape(f']({url})'),
            f']({local_path})',
            content
        )
        # 替换 ![](url "title") 格式
        content = re.sub(
            re.escape(f']({url} "') + r'(.+?)"\)',
            lambda m, lp=local_path: f']({lp} "' + m.group(1) + '")',
            content
        )
        # 替换 <img src="url">
        content = re.sub(
            r'(<img[^>]+src=)["\']' + re.escape(url) + r'["\']',
            lambda m: m.group(1) + f'"{local_path}"',
            content
        )
        # 替换 data-src="url"
        content = re.sub(
            r'(data-src=)["\']' + re.escape(url) + r'["\']',
            lambda m: m.group(1) + f'"{local_path}"',
            content
        )
        # 替换 data-croporisrc="url"
        content = re.sub(
            r'(data-croporisrc=)["\']' + re.escape(url) + r'["\']',
            lambda m: m.group(1) + f'"{local_path}"',
            content
        )
    
    return content


def try_web_fetch(url, format_type='markdown'):
    """尝试使用web_fetch工具获取内容"""
    try:
        import subprocess
        result = subprocess.run(
            ['openclaw', 'web', 'fetch', url, '--format', format_type],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            content = result.stdout.strip()
            if content and len(content) > 100 and '反爬' not in content and '访问验证' not in content and '请输入验证码' not in content:
                title = extract_title_from_markdown(content)
                return True, content, title, set()
    except Exception as e:
        print(f"[web_fetch] 尝试失败: {str(e)}", file=sys.stderr)

    return False, None, None, set()


def fetch_with_playwright(url, format_type='markdown', wait_time=3, cookie=None, click_selector=None, scroll=False):
    """
    使用playwright抓取网页内容，同时返回页面标题和原始HTML中发现的图片URL
    返回: (success, content, title, extra_image_urls)
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 缺少playwright依赖，请先安装：pip install playwright && playwright install chromium", file=sys.stderr)
        return False, None, None, set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-web-security',
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )

            page = context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
            """)

            if cookie:
                parsed_url = urlparse(url)
                context.add_cookies([{
                    'name': k.strip(),
                    'value': v.strip(),
                    'domain': parsed_url.netloc,
                    'path': '/'
                } for k, v in [c.split('=', 1) for c in cookie.split(';')]])

            page.goto(url, timeout=30000)
            time.sleep(wait_time)

            if click_selector:
                try:
                    page.click(click_selector, timeout=5000)
                    time.sleep(1)
                except Exception as e:
                    print(f"⚠️ 点击元素失败: {str(e)}", file=sys.stderr)

            # 先用JS把所有懒加载图片的 src 替换成 data-src的真实地址
            extra_image_urls = page.evaluate("""() => {
                const urls = [];
                document.querySelectorAll('img[data-src], img[data-croporisrc], img[data-original-src]').forEach(img => {
                    const realSrc = img.getAttribute('data-src') || img.getAttribute('data-croporisrc') || img.getAttribute('data-original-src');
                    if (realSrc && !realSrc.startsWith('data:')) {
                        urls.push(realSrc);
                        img.setAttribute('src', realSrc);
                        img.removeAttribute('data-src');
                        img.removeAttribute('data-croporisrc');
                        img.removeAttribute('data-original-src');
                    }
                });
                document.querySelectorAll('img[src]').forEach(img => {
                    const src = img.getAttribute('src');
                    if (src && !src.startsWith('data:') && src.length > 10) {
                        urls.push(src);
                    }
                });
                return urls;
            }""")
            extra_image_urls = set(extra_image_urls)

            if scroll:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)

            page_title = page.title()
            html_content = page.content()
            
            browser.close()

            if format_type == 'html':
                return True, html_content, page_title, extra_image_urls
            elif format_type == 'text':
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
                return True, text, page_title, set()
            else:
                try:
                    import markdownify
                    markdown_content = markdownify.markdownify(html_content, heading_style="ATX")
                    return True, markdown_content, page_title, extra_image_urls
                except ImportError:
                    print("⚠️ 缺少markdownify依赖,返回HTML格式", file=sys.stderr)
                    return True, html_content, page_title, extra_image_urls

    except Exception as e:
        print(f"[playwright] 抓取失败: {str(e)}", file=sys.stderr)
        return False, None, None, set()


def main():
    parser = argparse.ArgumentParser(description='智能网页内容抓取工具')
    parser.add_argument('url', help='要抓取的网页URL')
    parser.add_argument('--mode', choices=['auto', 'web_fetch', 'playwright'], default='auto', help='抓取模式,默认auto自动选择')
    parser.add_argument('--format', choices=['markdown', 'text', 'html'], default='markdown', help='输出格式,默认markdown')
    parser.add_argument('-o', '--output', help='输出文件路径(指定完整路径),不指定则在--output-dir下按标题自动生成文件名')
    parser.add_argument('--output-dir', default=None,
                        help=f'输出目录(不指定-o时有效),默认: {DEFAULT_OUTPUT_DIR}')
    parser.add_argument('--wait', type=int, default=3, help='playwright模式下页面等待时间(秒),默认3秒')
    parser.add_argument('--cookie', help='请求Cookie,格式:"key1=value1; key2=value2"')
    parser.add_argument('--click-selector', help='页面加载后要点击的元素CSS选择器,用于关闭弹窗等')
    parser.add_argument('--scroll', action='store_true', help='是否自动滚动到底部加载全部内容')
    parser.add_argument('--no-images', action='store_true', help='不下载图片(仅提取文本)')

    args = parser.parse_args()

    print(f"🚀 开始抓取网页: {args.url}", file=sys.stderr)

    content = None
    title = None
    extra_image_urls = set()
    success = False

    if args.mode in ['auto', 'web_fetch']:
        if args.mode == 'web_fetch':
            print(f"🔧 使用web_fetch模式抓取", file=sys.stderr)
        else:
            print(f"🔧 尝试web_fetch模式...", file=sys.stderr)

        success, content, title, extra = try_web_fetch(args.url, args.format)
        extra_image_urls.update(extra)
        if success:
            print(f"✅ web_fetch模式抓取成功", file=sys.stderr)

    if not success and args.mode in ['auto', 'playwright']:
        if args.mode == 'playwright':
            print(f"🔧 使用playwright模式抓取", file=sys.stderr)
        else:
            print(f"🔧 web_fetch模式失败,切换到playwright模式...", file=sys.stderr)

        success, content, title, extra = fetch_with_playwright(
            args.url,
            args.format,
            args.wait,
            args.cookie,
            args.click_selector,
            args.scroll
        )
        extra_image_urls.update(extra)

        if success:
            print(f"✅ playwright模式抓取成功", file=sys.stderr)

    if not success:
        print(f"❌ 所有抓取方式均失败", file=sys.stderr)
        sys.exit(1)

    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        if title:
            safe_title = sanitize_filename(title)
            filename = f"{safe_title}.md"
        else:
            fallback = urlparse(args.url).path.rstrip('/').split('/')[-1] or "page"
            fallback = sanitize_filename(fallback)
            filename = f"{fallback}.md"

        output_path = output_dir / filename

    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # 下载图片并替换引用(非text/plain格式且未禁用)
    if args.format != 'text' and not args.no_images:
        base_url = args.url
        content = download_and_replace_images(content, output_dir, base_url, extra_image_urls)

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📝 结果已保存到: {output_path.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    main()
