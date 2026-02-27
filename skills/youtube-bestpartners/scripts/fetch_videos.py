#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 YouTube 频道"最佳拍档"的最新视频信息
"""

import subprocess
import sys
import time
import json
import re
from datetime import datetime

# 设置 UTF-8 编码
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 尝试导入所需的库
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("正在安装必要的依赖...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests", "beautifulsoup4"])
    import requests
    from bs4 import BeautifulSoup

# VPN 和频道配置
VPN_EXECUTABLE = r"D:\Users\luzhe\AppData\Local\Programs\Clash for Windows\Clash for Windows.exe"
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@bestpartners/videos"
YOUTUBE_CHANNEL_API = "https://www.youtube.com/@bestpartners"

# 输出配置
OUTPUT_DIR = r"D:\anthropic\bestpartner"


def check_vpn_status():
    """检查 Clash for Windows 是否正在运行"""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Clash for Windows.exe"],
            capture_output=True, text=True, encoding='utf-8', errors='ignore'
        )
        return "Clash for Windows.exe" in result.stdout
    except Exception as e:
        print(f"检查 VPN 状态时出错: {e}")
        return False


def start_vpn():
    """启动 Clash for Windows VPN"""
    try:
        print("正在启动 VPN...")
        subprocess.Popen([VPN_EXECUTABLE], shell=True)
        print("VPN 启动命令已发送，等待 10 秒让 VPN 完全启动...")
        time.sleep(10)
        return check_vpn_status()
    except Exception as e:
        print(f"启动 VPN 时出错: {e}")
        return False


def ensure_vpn():
    """确保 VPN 已启动"""
    if check_vpn_status():
        print("VPN 已在运行中。")
        return True
    else:
        print("VPN 未运行，需要启动。")
        return start_vpn()


def extract_video_info_from_scripts(soup):
    """从页面脚本中提取视频信息"""
    videos = []

    # 查找包含 ytInitialData 的脚本
    scripts = soup.find_all('script')
    for script in scripts:
        text = script.string if script.string else ""

        # 查找 ytInitialData
        if 'ytInitialData' in text:
            try:
                # 提取 JSON 数据
                match = re.search(r'var ytInitialData = ({.+?});', text)
                if match:
                    data = json.loads(match.group(1))

                    # 导航到视频列表
                    tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
                    for tab in tabs:
                        tab_renderer = tab.get('tabRenderer', {})
                        content = tab_renderer.get('content', {})
                        rich_grid = content.get('richGridRenderer', {})
                        contents = rich_grid.get('contents', [])

                        for item in contents:
                            video_item = item.get('richItemRenderer', {}).get('content', {}).get('videoRenderer', {})
                            if not video_item:
                                continue

                            # 提取视频信息
                            video_id = video_item.get('videoId', '')
                            title_runs = video_item.get('title', {}).get('runs', [])
                            title = ''.join([run.get('text', '') for run in title_runs])

                            # 获取时长
                            length_text = video_item.get('lengthText', {}).get('simpleText', 'N/A')

                            # 获取发布时间
                            published_time = video_item.get('publishedTimeText', {}).get('simpleText', 'N/A')

                            # 获取观看次数
                            view_count_text = video_item.get('viewCountText', {}).get('simpleText', 'N/A')

                            # 获取缩略图（最大的）
                            thumbnails = video_item.get('thumbnail', {}).get('thumbnails', [])
                            thumbnail_url = thumbnails[-1].get('url', '') if thumbnails else ''

                            # 尝试获取详细统计信息
                            detailed_metadata = video_item.get('detailedMetadataSnippets', [])
                            description = ""
                            if detailed_metadata:
                                snippet_text = detailed_metadata[0].get('snippetText', {}).get('runs', [])
                                description = ''.join([run.get('text', '') for run in snippet_text])

                            # 过滤短视频（少于2分钟的可能是 Shorts/广告）
                            duration_seconds = parse_duration_to_seconds(length_text)
                            if duration_seconds < 120:  # 少于2分钟跳过
                                continue

                            if video_id and title:
                                videos.append({
                                    'video_id': video_id,
                                    'title': title,
                                    'duration': length_text,
                                    'upload_time': published_time,
                                    'views': view_count_text,
                                    'thumbnail': thumbnail_url,
                                    'description': description[:150] + "..." if len(description) > 150 else description
                                })
            except Exception as e:
                print(f"解析 ytInitialData 时出错: {e}")
                continue

    return videos


def fetch_videos_with_requests():
    """使用 requests 获取 YouTube 视频信息"""
    print(f"\n正在访问频道: {YOUTUBE_CHANNEL_URL}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    try:
        # 创建 session 并设置代理
        session = requests.Session()
        session.proxies = {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
        }

        response = session.get(YOUTUBE_CHANNEL_URL, headers=headers, timeout=60)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # 从脚本中提取视频信息
        videos = extract_video_info_from_scripts(soup)

        if not videos:
            print("未找到视频信息，尝试备用方法...")
            # 尝试从页面元数据中查找
            videos = extract_from_meta(soup)

        return videos

    except Exception as e:
        print(f"获取视频时出错: {e}")
        import traceback
        traceback.print_exc()
        return []


def extract_from_meta(soup):
    """备用方法：从 meta 标签提取视频信息"""
    videos = []

    # 查找视频链接
    video_links = soup.find_all('a', href=re.compile(r'/watch\?v='))
    seen_ids = set()

    for link in video_links[:20]:
        href = link.get('href', '')
        match = re.search(r'watch\?v=([a-zA-Z0-9_-]+)', href)
        if match:
            video_id = match.group(1)
            if video_id in seen_ids:
                continue
            seen_ids.add(video_id)

            # 获取标题
            title_elem = link.find('span', {'id': 'video-title'})
            title = title_elem.get('title', '') if title_elem else link.get_text(strip=True)

            if title and video_id:
                videos.append({
                    'video_id': video_id,
                    'title': title,
                    'duration': 'N/A',
                    'upload_time': 'N/A',
                    'views': 'N/A',
                    'thumbnail': f'https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg',
                    'description': '点击链接查看详情'
                })

    return videos


def parse_duration_to_seconds(duration_str):
    """将时长字符串转换为秒数
    支持格式: 1:17, 15:21, 1:23:45
    """
    if not duration_str or duration_str == 'N/A':
        return 0

    parts = str(duration_str).strip().split(':')
    try:
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, IndexError):
        pass
    return 0


def clean_views(views_str):
    """清理观看次数，去掉'次观看'后缀"""
    if not views_str or views_str == 'N/A':
        return 'N/A'
    # 去掉 "次观看" 或 "views" 后缀
    views_str = str(views_str).strip()
    views_str = views_str.replace('次观看', '').replace('views', '').replace('view', '').strip()
    return views_str


def parse_upload_time_to_days(upload_time_str):
    """解析发布时间，转换为天数
    支持格式: 5分钟前, 3小时前, 1天前, 2周前, 1个月前, 1年前
    返回: 天数 (整数), 如果无法解析返回 None
    """
    if not upload_time_str or upload_time_str == 'N/A':
        return None

    upload_time_str = str(upload_time_str).strip().lower()

    # 提取数字
    import re
    match = re.search(r'(\d+)', upload_time_str)
    if not match:
        # 处理 "昨天"、"今天" 等特殊词汇
        if '今天' in upload_time_str or '刚刚' in upload_time_str:
            return 0
        if '昨天' in upload_time_str:
            return 1
        return None

    num = int(match.group(1))

    # 根据单位计算天数
    if '分钟' in upload_time_str or 'minute' in upload_time_str:
        return 0
    elif '小时' in upload_time_str or 'hour' in upload_time_str:
        return 0
    elif '天' in upload_time_str or 'day' in upload_time_str:
        return num
    elif '周' in upload_time_str or '星期' in upload_time_str or 'week' in upload_time_str:
        return num * 7
    elif '月' in upload_time_str or 'month' in upload_time_str:
        return num * 30
    elif '年' in upload_time_str or 'year' in upload_time_str:
        return num * 365

    return None


def filter_videos_by_date(videos, max_days=7):
    """过滤视频，只保留指定天数内的视频"""
    filtered = []
    for video in videos:
        days = parse_upload_time_to_days(video.get('upload_time'))
        if days is not None and days <= max_days:
            filtered.append(video)
    return filtered


def format_output(videos):
    """将视频列表格式化为 Markdown 表格"""
    if not videos:
        return "未获取到任何视频信息。请检查网络连接或 VPN 状态。"

    # 构建 Markdown 表格
    output = []
    output.append("# 最佳拍档 (Best Partners) 最新视频\n")
    output.append(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.append(f"频道链接: [{YOUTUBE_CHANNEL_URL}]({YOUTUBE_CHANNEL_URL})\n\n")

    output.append("| 序号 | 视频标题 | 时长 | 发布时间 | 观看次数 | 链接 |")
    output.append("|------|---------|------|---------|---------|------|")

    for idx, video in enumerate(videos[:15], 1):  # 显示前15个视频
        # 处理标题中的管道符，避免破坏表格
        title = video['title'].replace('|', '\\|').replace('\n', ' ').strip()

        duration = str(video.get('duration', 'N/A')).replace('|', '\\|')
        upload_time = str(video.get('upload_time', 'N/A')).replace('|', '\\|')
        # 清理观看次数
        views = clean_views(video.get('views', 'N/A')).replace('|', '\\|')

        video_id = video.get('video_id', '')
        full_link = f"https://www.youtube.com/watch?v={video_id}" if video_id else "N/A"

        output.append(f"| {idx} | {title} | {duration} | {upload_time} | {views} | [观看]({full_link}) |")

    return "\n".join(output)


def main():
    """主函数"""
    print("=" * 60)
    print("YouTube 最佳拍档频道视频获取工具")
    print("=" * 60)

    # 确保 VPN 已启动
    if not ensure_vpn():
        print("\n错误: 无法启动 VPN，无法访问 YouTube。")
        sys.exit(1)

    print("\n" + "=" * 60)

    # 获取视频
    videos = fetch_videos_with_requests()

    if videos:
        # 过滤7天内的视频
        original_count = len(videos)
        videos = filter_videos_by_date(videos, max_days=7)
        filtered_count = len(videos)
        if filtered_count < original_count:
            print(f"已过滤: 仅保留7天内的视频 ({filtered_count}/{original_count})")

        # 格式化输出
        output = format_output(videos)
        print("\n" + "=" * 60)
        print("获取完成！结果如下：")
        print("=" * 60 + "\n")
        print(output)

        # 同时保存到文件，文件名带日期后缀
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        date_str = datetime.now().strftime('%Y-%m-%d')
        output_filename = f"bestpartners_videos_{date_str}.md"
        output_file = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n\n结果已保存到: {output_file}")
    else:
        print("\n未能获取到视频信息，请检查网络连接或 VPN 状态。")


if __name__ == "__main__":
    main()
