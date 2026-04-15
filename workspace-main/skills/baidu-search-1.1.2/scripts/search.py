import sys
import json
import requests
import os
import re
from datetime import datetime, timedelta

# Fix Windows console encoding for Chinese characters
if sys.platform == 'win32':
    import io
    # 强制使用 UTF-8 编码（无论是否是终端）
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def baidu_search(api_key, requestBody: dict):
    url = "https://qianfan.baidubce.com/v2/ai_search/web_search"

    headers = {
        "Authorization": "Bearer %s" % api_key,
        "X-Appbuilder-From": "openclaw",
        "Content-Type": "application/json"
    }

    # 使用POST方法发送JSON数据
    response = requests.post(url, json=requestBody, headers=headers)
    response.raise_for_status()
    results = response.json()
    if "code" in results:
        raise Exception(results["message"])
    datas = results["references"]
    keys_to_remove = {"snippet"}
    for item in datas:
        for key in keys_to_remove:
            if key in item:
                del item[key]
    return datas


if __name__ == "__main__":
    # 支持从命令行参数、文件路径或 stdin 读取 JSON
    query = None
    
    if len(sys.argv) >= 2:
        arg = sys.argv[1]
        # 检查是否是文件路径（以 .json 结尾或文件存在）
        if arg.endswith('.json') or os.path.isfile(arg):
            try:
                with open(arg, 'r', encoding='utf-8') as f:
                    query = f.read()
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # 兼容旧方式：从命令行参数直接读取 JSON
            query = arg
    else:
        # 从 stdin 读取
        query = sys.stdin.read()
    
    if not query:
        print("Error: No input provided. Usage: python search.py <json_string|json_file>")
        sys.exit(1)
    
    parse_data = {}
    try:
        parse_data = json.loads(query)
        print(f"success parse request body: {parse_data}", file=sys.stderr)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        sys.exit(1)

    if "query" not in parse_data:
        print("Error: query must be present in request body.")
        sys.exit(1)
    count = 10
    search_filter = {}
    if "count" in parse_data:
        count = int(parse_data["count"])
        if count <= 0:
            count = 10
        elif count > 50:
            count = 50
    current_time = datetime.now()
    end_date = (current_time + timedelta(days=1)).strftime("%Y-%m-%d")
    pattern = r'\d{4}-\d{2}-\d{2}to\d{4}-\d{2}-\d{2}'
    if "freshness" in parse_data:
        if parse_data["freshness"] in ["pd", "pw", "pm", "py"]:
            if parse_data["freshness"] == "pd":
                start_date = (current_time - timedelta(days=1)).strftime("%Y-%m-%d")
            if parse_data["freshness"] == "pw":
                start_date = (current_time - timedelta(days=6)).strftime("%Y-%m-%d")
            if parse_data["freshness"] == "pm":
                start_date = (current_time - timedelta(days=30)).strftime("%Y-%m-%d")
            if parse_data["freshness"] == "py":
                start_date = (current_time - timedelta(days=364)).strftime("%Y-%m-%d")
            search_filter = {"range": {"page_time": {"gte": start_date, "lt": end_date}}}
        elif re.match(pattern, parse_data["freshness"]):
            start_date = parse_data["freshness"].split("to")[0]
            end_date = parse_data["freshness"].split("to")[1]
            search_filter = {"range": {"page_time": {"gte": start_date, "lt": end_date}}}
        else:
            print(f"Error: freshness ({parse_data['freshness']}) must be pd, pw, pm, py, or match {pattern}.")
            sys.exit(1)

    # We will pass these via env vars for security
    api_key = os.getenv("BAIDU_API_KEY")

    if not api_key:
        print("Error: BAIDU_API_KEY must be set in environment.")
        sys.exit(1)

    request_body = {
        "messages": [
            {
                "content": parse_data["query"],
                "role": "user"
            }
        ],
        "search_source": "baidu_search_v2",
        "resource_type_filter": [{"type": "web", "top_k": count}],
        "search_filter": search_filter
    }
    try:
        print(f"Calling baidu_search with request body...", file=sys.stderr)
        results = baidu_search(api_key, request_body)
        print(f"Got {len(results)} results", file=sys.stderr)
        output = json.dumps(results, indent=2, ensure_ascii=False)
        print(output)
        sys.stdout.flush()
    except Exception as e:
        print(f"Error in baidu_search: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
