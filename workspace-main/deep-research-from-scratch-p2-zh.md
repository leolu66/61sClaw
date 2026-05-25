# Part 2：从零构建 Deep Research —— 搭建你的研究实验室

> 作者：Samyak | 2025年6月8日 | 阅读时间约12分钟
> 原文：https://medium.com/@samyakb/part-2-deep-research-from-scratch-2d8164c33999

---

欢迎回到 Deep Research 系列。在第一部分中，我们了解了什么是 *Deep Research*。现在，我们要**构建一个可运行的迷你版本**：一个能接收问题、通过 Tavily API 搜索网络、并用 Gemini 为你生成 Markdown 格式研究报告的工具。

![image-20260522171341581](E:\typora\images\image-20260522171341581.png)

如果你是 Python 新手，建议先快速了解一下 asyncio 的基础知识，以及什么是 `.env` 文件和 `load_dotenv` 包。

> *这是你的第一个 AI Agent 项目。我们会慢慢来，稳扎稳打。*

## 我们要构建什么

**想象一下：**

你提问：

> *"加速度测量对帕金森病的早期检测有效吗？"*

然后这个工具会回复：

- 一个详细的研究计划（要搜索什么）
- 在线搜索每个子项
- 总结搜索结果
- 生成一份格式美观的 Markdown 研究报告

全部通过一条命令完成。

## 前置条件

### 1. Python 3.10 或更新版本

检查版本：`python --version`。如果未安装 Python，[在此下载](https://www.python.org/downloads/)。

### 2. Git + GitHub 账号

我们会把代码推送到 GitHub。从[这里](https://git-scm.com/)安装 Git，并在 [GitHub](https://github.com/) 上注册账号。

### 3. 终端

- **Windows**：按 `Win + R`，输入 `cmd`，回车
- **Linux/macOS**：按 `Ctrl + Alt + T`

## 第 1 步：创建项目

打开终端，输入：

```bash
mkdir deep-research-toy
cd deep-research-toy
```

## 第 2 步：目录结构

在文件夹内创建：

```
deep-research-toy/
├── main.py
├── .env
├── requirements.txt
├── .gitignore
```

> *可以右键 > "新建文件"，或者使用 VS Code / 记事本。*

## 第 3 步：添加 API 密钥

前往：

- Gemini API：https://ai.google.dev/gemini-api/docs/api-key
- Tavily API：https://app.tavily.com/

然后在 `.env` 文件中填入：

```
GOOGLE_GENERATIVE_AI_API_KEY=你的_gemini_api_key
TAVILY_API_KEY=你的_tavily_api_key
```

## 第 4 步：定义依赖并创建虚拟环境

### 创建虚拟环境

以下命令在 **Windows 和 Linux** 上通用：

```bash
python -m venv venv
```

### 激活虚拟环境

**Windows（命令提示符）：**

```cmd
venv\Scripts\activate
```

**Windows（PowerShell）：**

```powershell
venv\Scripts\Activate.ps1
```

> ⚠️ *如果激活被阻止，可能需要修改 PowerShell 执行策略。*

**Linux/macOS：**

```bash
source venv/bin/activate
```

### 创建 `requirements.txt`

```
annotated-types==0.7.0
anyio==4.9.0
cachetools==5.5.2
certifi==2025.4.26
charset-normalizer==3.4.2
click==8.2.1
fastapi==0.115.12
google-ai-generativelanguage==0.6.15
google-api-core==2.24.2
google-api-python-client==2.170.0
google-auth==2.40.2
google-auth-httplib2==0.2.0
google-generativeai==0.8.5
googleapis-common-protos==1.70.0
grpcio==1.71.0
grpcio-status==1.71.0
h11==0.16.0
httpcore==1.0.9
httplib2==0.22.0
httpx==0.28.1
idna==3.10
proto-plus==1.26.1
protobuf==5.29.5
pyasn1==0.6.1
pyasn1_modules==0.4.2
pydantic==2.11.5
pydantic_core==2.33.2
pyparsing==3.2.3
python-dotenv==1.1.0
regex==2024.11.6
requests==2.32.3
rsa==4.9.1
sniffio==1.3.1
starlette==0.46.2
tavily-python==0.7.3
tenacity==9.1.2
tiktoken==0.9.0
tqdm==4.67.1
typing-inspection==0.4.1
typing_extensions==4.13.2
uritemplate==4.1.1
urllib3==2.4.0
uvicorn==0.34.3
```

然后用以下命令安装：

```bash
pip install -r requirements.txt
```

> ❗ *如果提示找不到 pip，尝试 `python -m pip install -r requirements.txt`。*

## 第 5 步：添加 .gitignore

完整的 Python `.gitignore`——确保 `.env`、`venv/`、`__pycache__/` 等不必要的文件不会推送到 GitHub。

## 第 6 步：编写并运行代码

创建 `main.py`，写入以下代码：

```python
import google.generativeai as genai
import google.api_core.exceptions
from tavily import TavilyClient
import os
from dotenv import load_dotenv
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_GENERATIVE_AI_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

thinking_model = genai.GenerativeModel("gemini-1.5-flash")
task_model = genai.GenerativeModel("gemini-1.5-flash")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(20),
    retry=retry_if_exception_type(google.api_core.exceptions.ResourceExhausted)
)
async def generate_plan(query):
    planning_prompt = f"""
    Create a structured research plan for the topic: {query}. Return valid JSON only, without any additional text, code fences, or markdown:
    {{
      "plan": "Overall research plan description",
      "subtasks": [
        {{
          "subtask": "Description of subtask 1",
          "search_query": "Specific search query for subtask 1"
        }},
        {{
          "subtask": "Description of subtask 2",
          "search_query": "Specific search query for subtask 2"
        }}
      ]
    }}
    Ensure the response is valid JSON with at least two subtasks, each with a non-empty search_query relevant to the topic.
    """
    planning_response = thinking_model.generate_content(planning_prompt)
    return json.loads(planning_response.text)

async def test_stream_research(query):
    print("Starting research for:", query)

    # Step 1: Generate plan
    try:
        plan = await generate_plan(query)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON parsing error: {e}")
        plan = {
            "plan": f"Default plan for {query}",
            "subtasks": [{"subtask": "Default subtask", "search_query": query}]
        }
    print(f"Planning: {json.dumps(plan, indent=2)}")

    # Step 2: Perform web search
    search_results = []
    for subtask in plan["subtasks"]:
        search_query = subtask["search_query"]
        try:
            results = tavily.search(query=search_query, max_results=5)
            search_results.append({
                "search_query": search_query,
                "subtask": subtask["subtask"],
                "results": results["results"]
            })
            print(f"Search Results for '{search_query}': {json.dumps(results['results'], indent=2)}")
        except Exception as e:
            print(f"Error searching '{search_query}': {str(e)}")

    # Step 3: Generate report
    search_summary = "\n".join([
        f"Subtask: {item['subtask']}\nSearch Query: {item['search_query']}\nResults:\n" +
        "\n".join([f"- {result['title']}: {result['content']}" for result in item["results"]])
        for item in search_results
    ])

    report_prompt = f"""
    Generate a comprehensive research report on {query} in markdown format. Use the following data:
    ## Research Plan
    {json.dumps(plan, indent=2)}
    ## Search Results
    {search_summary}
    Structure the report with:
    - An introduction summarizing the topic and plan
    - Sections for each subtask with summarized findings and citations
    - A conclusion synthesizing key insights
    Include citations in the format [Source: Title, URL].
    """
    try:
        for chunk in task_model.generate_content(report_prompt, stream=True):
            print(chunk.text)
    except google.api_core.exceptions.ResourceExhausted as e:
        print(f"Quota exceeded during report generation: {e}")

if __name__ == "__main__":
    asyncio.run(test_stream_research("effectiveness of accelerometry in early detection of Parkinson's disease"))
```

## 运行结果

运行后你会看到类似这样的输出：

```
Starting research for: effectiveness of accelerometry in early detection of Parkinson's disease
JSON parsing error: Expecting value: line 1 column 1 (char 0)
Planning: {
  "plan": "Default plan for effectiveness of accelerometry in early detection of Parkinson's disease",
  "subtasks": [
    { "subtask": "Default subtask", "search_query": "effectiveness of accelerometry in early detection of Parkinson's disease" }
  ]
}
```

然后 Tavily 会返回 5 条相关学术搜索结果（来自 NCBI、ResearchGate、MDPI、Nature 等），最后 Gemini 会生成一份 Markdown 格式的研究报告，包含引言、子任务分析、结论等结构。

---

> *注：文章中的完整报告输出在抓取时被截断，实际运行代码将生成完整输出。*
