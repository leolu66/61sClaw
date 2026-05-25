# Part 2: Deep Research from Scratch — Setting Up Your Research Lab

> Author: Samyak | Jun 8, 2025 | 12 min read
> Source: https://medium.com/@samyakb/part-2-deep-research-from-scratch-2d8164c33999

---

Welcome back to the Deep Research series. In Part 1, we understood what *Deep Research* is. Now, we'll **build a working mini version**: a tool that takes a question, searches the web using Tavily API, and writes a Markdown research report for you using Gemini.

![Part 2 Banner](https://miro.medium.com/v2/resize:fit:700/1*sRwoJVK0ctgOZfXmtN1LLw.jpeg)

If you are new to python consider watching a quick crash course on asyncio and reading up on what .env files are and the load_dotenv package.

> *This is your first AI agent project. We'll move slowly and deliberately.*

## What We're Building

**Imagine this:**

You ask:

> *"Is accelerometry effective for early detection of Parkinson's?"*

And this tool replies with:

- A detailed plan (what to search for).
- Searches each thing online.
- Summarizes the results.
- Generates a nicely formatted Markdown research report.

All in one command.

## Prerequisites

### 1. Python 3.10 or newer

Check with: `python --version`. If you don't have Python installed, [download it here](https://www.python.org/downloads/).

### 2. Git + GitHub account

We'll push our code to GitHub. Install Git from [here](https://git-scm.com/) and create an account on [GitHub](https://github.com/).

### 3. A terminal

- **Windows**: Press `Win + R`, type `cmd`, hit Enter.
- **Linux/macOS**: Press `Ctrl + Alt + T`.

## Step 1: Create the Project

Open your terminal and type:

```bash
mkdir deep-research-toy
cd deep-research-toy
```

## Step 2: Folder structure

Inside your folder, create:

```
deep-research-toy/
├── main.py
├── .env
├── requirements.txt
├── .gitignore
```

> *You can right-click > "New File" or use VS Code or Notepad.*

## Step 3: Add Your API Keys

Go to:

- Gemini API: [https://ai.google.dev/gemini-api/docs/api-key](https://ai.google.dev/gemini-api/docs/api-key)
- Tavily API: [https://app.tavily.com/](https://app.tavily.com/)

Now paste into `.env` like this:

```
GOOGLE_GENERATIVE_AI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

## Step 4: Define Dependencies and Virtual Environment

### Create a virtual environment

This command works the same on **both Windows and Linux**:

```bash
python -m venv venv
```

### Activate the virtual environment

**On Windows (Command Prompt):**

```cmd
venv\Scripts\activate
```

**On Windows (PowerShell):**

```powershell
venv\Scripts\Activate.ps1
```

> ⚠️ *You might need to change PowerShell execution policies if activation is blocked.*

**On Linux/macOS:**

```bash
source venv/bin/activate
```

### Create `requirements.txt`

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

Now install these with:

```bash
pip install -r requirements.txt
```

> ❗ *If you get pip not found, try `python -m pip install -r requirements.txt`.*

## Step 5: Add .gitignore

A comprehensive Python `.gitignore` — ensures `.env`, `venv/`, `__pycache__/`, and other unnecessary files don't get pushed to GitHub.

## Step 6: Write and Run the Code

Create `main.py` with the following code:

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

Now run this code. You'll see output like this:

```
Starting research for: effectiveness of accelerometry in early detection of Parkinson's disease
JSON parsing error: Expecting value: line 1 column 1 (char 0)
Planning: {
  "plan": "Default plan for effectiveness of accelerometry in early detection of Parkinson's disease",
  "subtasks": [
    {
      "subtask": "Default subtask",
      "search_query": "effectiveness of accelerometry in early detection of Parkinson's disease"
    }
  ]
}
Search Results for 'effectiveness of accelerometry in early detection of Parkinson's disease': [
  {
    "title": "Detecting Parkinson's Disease from Wrist-Worn Accelerometry in the U.K ...",
    "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7999802/",
    "content": "Parkinson's disease (PD) is a chronic movement disorder that produces a variety of characteristic movement abnormalities. The ubiquity of wrist-worn accelerometry suggests a possible sensor modality for early detection of PD symptoms and subsequent tracking of PD symptom severity.",
    "score": 0.85538095,
    "raw_content": null
  },
  {
    "title": "(PDF) Detection of Parkinson's Disease Using Wrist ... - ResearchGate",
    "url": "https://www.researchgate.net/publication/365713993_Detection_of_Parkinson's_Disease_Using_Wrist_Accelerometer_Data_and_Passive_Monitoring",
    "content": "In this study, we use a dataset consisting of one-week wrist-worn accelerometry data collected from individuals with Parkinson's disease and healthy elderlies for early detection of the disease.",
    "score": 0.84858394,
    "raw_content": null
  },
  {
    "title": "Detection of Parkinson's Disease Using Wrist Accelerometer Data and ...",
    "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9738242/",
    "content": "The contributions of this study are listed as follows: (1) Early detection of PD using wrist accelerometer and passive monitoring, (2) using the document-of-word feature engineering approach ...",
    "score": 0.77731717,
    "raw_content": null
  },
  {
    "title": "Parkinson's Disease Tremor Detection in the Wild Using ... - MDPI",
    "url": "https://www.mdpi.com/1424-8220/20/20/5817",
    "content": "Continuous in-home monitoring of Parkinson's Disease (PD) symptoms might allow improvements in assessment of disease progression and treatment effects.",
    "score": 0.62742686,
    "raw_content": null
  },
  {
    "title": "Application of single wrist-wearable accelerometry for ... - Nature",
    "url": "https://www.nature.com/articles/s41746-023-00937-1",
    "content": "Advanced stages of Parkinson's disease (PD) are characterized by the presence of motor complications...",
    "score": 0.52130115,
    "raw_content": null
  }
]

# Research Report: Effectiveness of Accelerometry in Early Detection of Parkinson's Disease

## Introduction
This report investigates the effectiveness of accelerometry in the early detection of Parkinson's Disease (PD). The research plan focused on analyzing existing literature examining the use of wrist-worn accelerometers to identify characteristic movement abnormalities associated with PD. This approach leverages the readily available technology of wearable accelerometers for potential non-invasive, continuous monitoring and early diagnosis.

The following sections summarize findings from relevant studies.

## Subtask: Effectiveness of Accelerometry in Early Detection of Parkinson's Disease
This subtask examined studies exploring the application of accelerometry for early PD detection. The research indicates promising potential, though challenges remain. Several studies highlight the ability of wrist-worn accelerometers to capture movement data indicative of PD. This data, after appropriate feature extraction and machine learning, can be used to differentiate between individuals with PD and healthy controls.

---

*(Note: The article was partially truncated during fetch — the report output continues beyond this point.)*
