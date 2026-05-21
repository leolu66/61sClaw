# 运营商新闻智能采集系统 - 完整技术方案

**版本**: v3.0  
**日期**: 2026-04-30  
**状态**: 设计方案

---

## 目录

1. [项目概述](#1-项目概述)
2. [核心架构](#2-核心架构)
3. [Bootstrap机制](#3-bootstrap机制)
4. [ReAct主流程](#4-react主流程)
5. [模块详细设计](#5-模块详细设计)
6. [数据模型](#6-数据模型)
7. [技术实现](#7-技术实现)
8. [演进路线](#8-演进路线)
9. [风险与对策](#9-风险与对策)

---

## 1. 项目概述

### 1.1 项目背景

当前运营商新闻采集存在以下问题：
- **任务规划粗放**: 缺乏系统性的任务分解策略
- **来源配置僵化**: 硬编码爬虫规则，难以适应网站变化
- **采集策略单一**: 无法根据反爬强度自适应调整
- **数据质量参差**: 缺乏多维度的质量评估体系
- **重复建设**: 每次查询都从零开始分析

### 1.2 设计目标

构建一个**智能化、自适应、可进化**的运营商新闻采集系统：

| 目标 | 具体指标 |
|-----|---------|
| **智能化** | 自动任务分解、自适应采集策略、智能质量评估 |
| **高效率** | 任务规划<1秒、采集完成<5分钟、报告生成<30秒 |
| **高质量** | 数据完整度>90%、去重准确率>95%、交叉验证覆盖率>80% |
| **可进化** | 知识库日更新、模板持续优化、来源自动发现 |

### 1.3 核心创新点

1. **Bootstrap预加载机制**: 预先构建领域知识库，避免重复分析
2. **ReAct循环架构**: 每个模块都具备反思和自适应能力
3. **分层任务分解**: 支持3层递归分解，100任务上限
4. **自适应采集**: 从HTTP到Playwright的5级策略自动升级
5. **多维度质量评估**: 完整性/可信度/相关性/时效性/丰富度

---

## 2. 核心架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         运营商新闻智能采集系统                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Bootstrap 层 (预加载)                         │   │
│  │                                                                     │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │   │ 运营商    │  │ 高管     │  │ 关键词   │  │ 任务     │           │   │
│  │   │ 知识库    │  │ 数据库   │  │ 图谱     │  │ 模板库   │           │   │
│  │   │          │  │          │  │          │  │          │           │   │
│  │   │ • 官网   │  │ • 职务   │  │ • 业务词 │  │ • 日常   │           │   │
│  │   │ • 别名   │  │ • 别名   │  │ • 事件词 │  │ • 财报   │           │   │
│  │   │ • 热点   │  │ • 话题   │  │ • 关联   │  │ • 应急   │           │   │
│  │   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │   │
│  │        └─────────────┴─────────────┴─────────────┘                  │   │
│  │                      ↓ (每日自动更新)                                │   │
│  │              ┌─────────────────────────┐                            │   │
│  │              │    bootstrap/kb.yaml    │                            │   │
│  │              └─────────────────────────┘                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ↓ 知识注入                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ReAct 主流程层 (运行时)                          │   │
│  │                                                                     │   │
│  │   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │   │
│  │   │   M1 任务   │     │   M2 采集   │     │   M3 存储   │          │   │
│  │   │    分解     │ ──→ │    引擎     │ ──→ │    管理     │          │   │
│  │   │             │     │             │     │             │          │   │
│  │   │ Thought     │     │ Thought     │     │ Thought     │          │   │
│  │   │ Action      │     │ Action      │     │ Action      │          │   │
│  │   │ Observe     │     │ Observe     │     │ Observe     │          │   │
│  │   │ Reflect     │     │ Reflect     │     │ Reflect     │          │   │
│  │   │ [Adapt]     │     │ [Adapt]     │     │ [Adapt]     │          │   │
│  │   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘          │   │
│  │          │                   │                   │                 │   │
│  │          └───────────────────┴───────────────────┘                 │   │
│  │                              ↓                                    │   │
│  │   ┌─────────────────────────────────────────────────────────┐    │   │
│  │   │                      M4 报告汇编                         │    │   │
│  │   │  • 智能摘要  • 交叉验证  • 模板渲染  • 多格式输出        │    │   │
│  │   └─────────────────────────────────────────────────────────┘    │   │
│  │                              ↓                                    │   │
│  │   ┌─────────────────────────────────────────────────────────┐    │   │
│  │   │                      全局反思                            │    │   │
│  │   │  评估整体质量 → 决定是否重试某模块 → 输出最终报告        │    │   │
│  │   └─────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      全局约束层                                      │   │
│  │   max_depth=3  max_tasks=100  max_duration=600s  max_memory=500MB   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 架构设计原则

| 原则 | 说明 |
|-----|------|
| **分层解耦** | Bootstrap层与ReAct层分离，知识库可独立更新 |
| **循环反馈** | 每个模块具备完整的ReAct循环，支持自适应调整 |
| **约束优先** | 全局约束在所有模块生效，防止资源耗尽 |
| **渐进增强** | 从模板匹配到动态分解的渐进式降级策略 |

---

## 3. Bootstrap机制

### 3.1 设计目标

- **消除重复分析**: 预置领域知识，避免每次查询都从零开始
- **提升响应速度**: 模板匹配替代动态分析，任务规划<1秒
- **保障数据质量**: 预验证的来源配置，稳定可靠的采集
- **支持持续进化**: 知识库日更新，跟随领域变化

### 3.2 知识库结构

```yaml
# bootstrap/knowledge_base.yaml

version: "2026.04.30"
last_updated: "2026-04-30T08:00:00+08:00"
update_frequency: "daily"

# ============ 1. 运营商档案 ============
operators:
  中国移动:
    name: "中国移动"
    aliases: ["中移动", "China Mobile", "CMCC", "中国移动通信"]
    stock_code: "600941.SH / 0941.HK"
    
    official_sites:
      - name: "官网新闻中心"
        url: "https://www.10086.cn/aboutus/news/"
        news_url: "https://www.10086.cn/aboutus/news/"
        encoding: "utf-8"
        selectors:
          list: ".news-list li"
          title: "h3"
          date: ".date"
          link: "a"
        priority: 5
        update_frequency: "daily"
        
      - name: "投资者关系"
        url: "https://www.chinamobileltd.com/tc/investors/press.php"
        priority: 5
        
    official_wechat: ["中国移动", "中国移动研究院", "中移智库"]
    official_weibo: "@中国移动"
    
    business_tags: ["5G", "算力网络", "移动云", "物联网", "AI"]
    recent_focus: ["5G-A商用", "AI大模型", "低空经济网络"]
    
  中国电信:
    name: "中国电信"
    aliases: ["中电信", "China Telecom"]
    stock_code: "601728.SH / 0728.HK"
    
    official_sites:
      - name: "官网新闻"
        url: "https://www.chinatelecom.com.cn/news/"
        priority: 5
        
    official_wechat: ["中国电信", "天翼云", "中国电信研究院"]
    business_tags: ["天翼云", "5G", "卫星通信", "量子通信", "AI"]
    recent_focus: ["天翼云出海", "手机直连卫星", "量子城域网"]
    
  中国联通:
    name: "中国联通"
    aliases: ["中联通", "China Unicom", "联通"]
    stock_code: "600050.SH / 0762.HK"
    
    official_sites:
      - name: "官网新闻"
        url: "https://www.chinaunicom.com.cn/news/"
        priority: 5
        
    official_wechat: ["中国联通", "联通研究院"]
    business_tags: ["5G", "联通云", "大数据", "工业互联网"]
    recent_focus: ["5G-A商用", "车联网", "元景大模型"]
    
  中国铁塔:
    name: "中国铁塔"
    aliases: ["中铁塔", "China Tower"]
    stock_code: "00788.HK"
    
    official_sites:
      - name: "官网新闻"
        url: "http://www.chinatowercom.cn/news/"
        priority: 4
        
    official_wechat: ["中国铁塔"]
    business_tags: ["基站建设", "共享铁塔", "新能源", "视联网"]
    recent_focus: ["新能源业务", "视联网", "铁塔智算"]

# ============ 2. 高管数据库 ============
executives:
  中国移动:
    - name: "杨杰"
      position: "董事长、党组书记"
      level: "集团领导"
      responsibilities: ["战略规划", "全面管理", "党建工作"]
      name_aliases: ["杨董事长", "杨书记", "杨董"]
      recent_topics: ["5G-A", "AI+", "算力网络", "新质生产力"]
      
    - name: "何飚"
      position: "总经理、党组副书记"
      level: "集团领导"
      responsibilities: ["日常经营", "市场运营", "客户服务"]
      name_aliases: ["何总", "何总经理"]
      recent_topics: ["客户服务", "网络建设", "数字化转型"]
      
    - name: "李慧镝"
      position: "副总经理、党组成员"
      level: "集团领导"
      responsibilities: ["技术", "研发", "网络"]
      name_aliases: ["李总"]
      recent_topics: ["5G技术", "6G研发", "算力网络"]
      
  中国电信:
    - name: "柯瑞文"
      position: "董事长、党组书记"
      level: "集团领导"
      responsibilities: ["战略规划", "全面管理"]
      name_aliases: ["柯董事长", "柯书记", "柯董"]
      recent_topics: ["云改数转", "卫星通信", "AI赋能"]
      
    - name: "邵广禄"
      position: "总经理、党组副书记"
      level: "集团领导"
      responsibilities: ["日常经营", "云网运营"]
      name_aliases: ["邵总"]
      recent_topics: ["天翼云", "数字化转型", "量子通信"]
      
    - name: "刘桂清"
      position: "副总经理、党组成员"
      level: "集团领导"
      responsibilities: ["政企客户", "产业数字化"]
      name_aliases: ["刘总"]
      recent_topics: ["工业互联网", "智慧城市", "数字政府"]
      
  中国联通:
    - name: "陈忠岳"
      position: "董事长、党组书记"
      level: "集团领导"
      responsibilities: ["战略规划", "全面管理"]
      name_aliases: ["陈董事长", "陈书记"]
      recent_topics: ["5G-A", "车联网", "元景大模型"]
      
    - name: "简勤"
      position: "总经理、党组副书记"
      level: "集团领导"
      responsibilities: ["日常经营", "市场运营"]
      name_aliases: ["简总"]
      recent_topics: ["公众市场", "产品创新", "渠道转型"]
      
  中国铁塔:
    - name: "张志勇"
      position: "董事长、党委书记"
      level: "集团领导"
      name_aliases: ["张董事长"]
      recent_topics: ["新能源", "视联网", "智算中心"]

# ============ 3. 关键词图谱 ============
keyword_graph:
  core_keywords: ["中国移动", "中国电信", "中国联通", "中国铁塔"]
  
  # 业务关键词（技术领域）
  business_keywords:
    network:
      - keyword: "5G-A"
        aliases: ["5G-Advanced", "5.5G", "5G Advanced"]
        related: ["万兆网络", "通感一体", "无源物联", "网络智能化"]
        priority: 5
        
      - keyword: "6G"
        aliases: ["第六代移动通信", "6G研发"]
        related: ["太赫兹", "智能超表面", "RIS", "空天地一体化"]
        priority: 4
        
      - keyword: "算力网络"
        aliases: ["CFN", "Compute First Networking", "算网"]
        related: ["东数西算", "智算中心", "算力调度", "算力交易"]
        priority: 5
        
      - keyword: "卫星通信"
        aliases: ["手机直连卫星", "天通卫星", "卫星互联网"]
        related: ["低轨卫星", "NTN", "非地面网络", "天地一体"]
        priority: 5
        
      - keyword: "低空经济"
        aliases: ["低空网络", "无人机通信", "低空智联网"]
        related: ["eVTOL", "空域管理", "低空监管", "无人机管控"]
        priority: 4
        
      - keyword: "光网络"
        aliases: ["全光网", "千兆光网", "万兆光网", "FTTR"]
        related: ["50G PON", "400G光传输", "光纤入户"]
        priority: 3
        
    technology:
      - keyword: "AI"
        aliases: ["人工智能", "大模型", "AI+", "AI赋能"]
        related: ["九天大模型", "TeleAI", "元景大模型", "行业大模型"]
        priority: 5
        
      - keyword: "大模型"
        aliases: ["LLM", "基础模型", "Foundation Model"]
        related: ["语料库", "模型训练", "模型推理", "MaaS"]
        priority: 5
        
      - keyword: "物联网"
        aliases: ["IoT", "万物互联", "Internet of Things"]
        related: ["NB-IoT", "Cat.1", "RedCap", "无源物联"]
        priority: 4
        
      - keyword: "边缘计算"
        aliases: ["MEC", "Multi-access Edge Computing"]
        related: ["边缘云", "边缘AI", "边缘智能"]
        priority: 3
        
      - keyword: "区块链"
        aliases: ["Blockchain", "分布式账本"]
        related: ["BSN", "联盟链", "数字藏品"]
        priority: 2
        
      - keyword: "数字孪生"
        aliases: ["Digital Twin"]
        related: ["元宇宙", "虚实融合", "三维可视化"]
        priority: 3
        
      - keyword: "量子通信"
        aliases: ["量子密钥", "QKD", "Quantum Key Distribution"]
        related: ["量子计算", "国盾量子", "量子城域网"]
        priority: 4
        
    service:
      - keyword: "云服务"
        aliases: ["云计算", "公有云", "私有云", "混合云"]
        related: ["天翼云", "移动云", "联通云", "IaaS", "PaaS", "SaaS"]
        priority: 5
        
      - keyword: "大数据"
        aliases: ["Big Data", "数据要素", "数据资产"]
        related: ["数据分析", "数据治理", "数据安全", "数据交易"]
        priority: 4
        
      - keyword: "数据中心"
        aliases: ["IDC", "Internet Data Center", "智算中心"]
        related: ["服务器", "存储", "液冷", "绿色数据中心"]
        priority: 4
        
      - keyword: "CDN"
        aliases: ["内容分发网络", "Content Delivery Network"]
        related: ["边缘节点", "加速", "流媒体"]
        priority: 3
        
      - keyword: "安全服务"
        aliases: ["网络安全", "信息安全", "数据安全"]
        related: ["态势感知", "威胁情报", "零信任", "等保"]
        priority: 4
        
    terminal:
      - keyword: "5G手机"
        aliases: ["5G终端", "5G套餐"]
        related: ["5G换机", "5G渗透率", "5G用户"]
        priority: 3
        
      - keyword: "云手机"
        aliases: ["Cloud Phone", "云终端"]
        related: ["云电脑", "云Pad", "算力终端"]
        priority: 3
        
      - keyword: "智能家居"
        aliases: ["智慧家庭", "家庭IoT"]
        related: ["智能音箱", "智能门锁", "全屋智能"]
        priority: 3
        
      - keyword: "车联网"
        aliases: ["V2X", "车路协同", "智能网联汽车"]
        related: ["自动驾驶", "5G车联网", "C-V2X"]
        priority: 4
        
    emerging:
      - keyword: "低空经济"
        aliases: ["低空产业", "低空飞行"]
        related: ["无人机物流", "低空旅游", "城市空中交通"]
        priority: 4
        
      - keyword: "卫星互联网"
        aliases: ["低轨卫星", "星座互联网", "Starlink"]
        related: ["卫星组网", "星间链路", "卫星地面站"]
        priority: 4
        
      - keyword: "6G"
        aliases: ["6G愿景", "6G标准"]
        related: ["6G研发", "6G试验", "6G商用"]
        priority: 3

  # 事件关键词
  event_keywords:
    financial:
      - keyword: "财报"
        patterns: ["年报", "半年报", "季报", "业绩发布", "财务报告"]
        seasonality: "quarterly"
        months: [3, 4, 8, 10]  # 财报季月份
        priority: 5
        
      - keyword: "营收"
        aliases: ["营业收入", "收入"]
        related: ["净利润", "利润", "EBITDA", "ARPU"]
        priority: 4
        
      - keyword: "投资"
        patterns: ["战略投资", "股权投资", "资本开支", "CAPEX"]
        related: ["并购", "收购", "入股", "增资"]
        priority: 4
        
      - keyword: "派息"
        aliases: ["分红", "股息", "利润分配"]
        related: ["股东回报", "股息率"]
        priority: 3
        
    conference:
      - keyword: "合作伙伴大会"
        aliases: ["生态大会", "开发者大会", "创新大会"]
        typical_months: [3, 6, 9, 11]
        priority: 5
        
      - keyword: "展会"
        aliases: ["MWC", "PT展", "通信展", "信息通信展"]
        related: ["世界移动通信大会", "中国国际信息通信展览会"]
        priority: 4
        
      - keyword: "峰会"
        aliases: ["论坛", "研讨会", "圆桌"]
        related: ["行业峰会", "技术峰会", "产业峰会"]
        priority: 3
        
    cooperation:
      - keyword: "战略合作"
        patterns: ["战略协议", "战略签约", "全面合作"]
        related: ["合作协议", "合作备忘录", "MOU"]
        priority: 5
        
      - keyword: "签约"
        aliases: ["签署协议", "达成合作", "强强联合"]
        related: ["合作伙伴", "生态伙伴", "产业链合作"]
        priority: 4
        
      - keyword: "共建"
        patterns: ["联合建设", "共同推进", "协同创新"]
        related: ["联合实验室", "创新中心", "产业联盟"]
        priority: 3
        
    policy:
      - keyword: "政策"
        patterns: ["监管政策", "行业政策", "产业政策"]
        related: ["工信部", "通管局", "政策解读"]
        priority: 4
        
      - keyword: "牌照"
        aliases: ["许可证", "经营许可"]
        related: ["5G牌照", "频率许可", "业务许可"]
        priority: 4
        
      - keyword: "频谱"
        aliases: ["频率", "频段", "频谱资源"]
        related: ["频谱分配", "频率重耕", "毫米波"]
        priority: 3
        
    social:
      - keyword: "社会责任"
        aliases: ["ESG", "可持续发展", "企业社会责任"]
        related: ["环境", "社会", "治理", "双碳"]
        priority: 3
        
      - keyword: "乡村振兴"
        aliases: ["数字乡村", "农村信息化", "电信普遍服务"]
        related: ["农村网络", "农业数字化", "惠农服务"]
        priority: 3
        
      - keyword: "应急通信"
        aliases: ["重保", "重大保障", "通信保障"]
        related: ["抢险救灾", "应急保障", "通信畅通"]
        priority: 4

  # 关键词关联关系
  relations:
    # 技术协同
    - source: "5G-A"
      target: "算力网络"
      strength: 0.85
      type: "技术协同"
      description: "5G-A网络为算力网络提供低时延传输"
      
    - source: "AI"
      target: "大模型"
      strength: 0.95
      type: "包含关系"
      
    - source: "低空经济"
      target: "5G-A"
      strength: 0.80
      type: "应用场景"
      description: "低空经济依赖5G-A的通感一体能力"
      
    - source: "卫星通信"
      target: "6G"
      strength: 0.75
      type: "技术演进"
      description: "6G将实现空天地一体化融合"
      
    # 业务融合
    - source: "AI"
      target: "云服务"
      strength: 0.90
      type: "业务融合"
      description: "AI能力通过云服务对外提供"
      
    - source: "大数据"
      target: "AI"
      strength: 0.85
      type: "数据支撑"
      
    - source: "物联网"
      target: "5G-A"
      strength: 0.80
      type: "应用场景"
      
    # 事件关联
    - source: "财报"
      target: "营收"
      strength: 0.90
      type: "包含关系"
      
    - source: "合作伙伴大会"
      target: "战略合作"
      strength: 0.85
      type: "场景关联"

# ============ 4. 来源配置库 ============
sources:
  # 官方来源
  cm_official_news:
    id: "cm_official_news"
    name: "中国移动-官网新闻"
    type: "official"
    operator: "中国移动"
    url: "https://www.10086.cn/aboutus/news/"
    priority: 5
    selectors:
      list_container: ".news-list"
      item: "li"
      title: "h3"
      date: ".date"
      link: "a"
      content: ".content-detail"
    encoding: "utf-8"
    enabled: true
    
  ct_official_news:
    id: "ct_official_news"
    name: "中国电信-官网新闻"
    type: "official"
    operator: "中国电信"
    url: "https://www.chinatelecom.com.cn/news/"
    priority: 5
    enabled: true
    
  cu_official_news:
    id: "cu_official_news"
    name: "中国联通-官网新闻"
    type: "official"
    operator: "中国联通"
    url: "https://www.chinaunicom.com.cn/news/"
    priority: 5
    enabled: true
    
  tower_official_news:
    id: "tower_official_news"
    name: "中国铁塔-官网新闻"
    type: "official"
    operator: "中国铁塔"
    url: "http://www.chinatowercom.cn/news/"
    priority: 4
    enabled: true
    
  # 行业媒体
  c114:
    id: "c114"
    name: "C114通信网"
    type: "industry"
    url: "https://www.c114.com.cn"
    news_url: "https://www.c114.com.cn/news/roll.asp"
    priority: 4
    selectors:
      list_container: "div.news_list"
      item: "a"
      title: "text"
      link: "href"
    encoding: "gbk"
    enabled: true
    anti_spider_level: 2
    
  cnii:
    id: "cnii"
    name: "中国信息产业网"
    type: "industry"
    url: "https://www.cnii.com.cn"
    priority: 3
    enabled: true
    
  cww:
    id: "cww"
    name: "通信世界网"
    type: "industry"
    url: "https://www.cww.net.cn"
    priority: 3
    enabled: true
    
  # 央媒/财经
  xinhua_telecom:
    id: "xinhua_telecom"
    name: "新华社-通信"
    type: "media"
    url: "http://www.news.cn/tech/"
    priority: 4
    enabled: true
    
  sina_finance:
    id: "sina_finance"
    name: "新浪财经-通信"
    type: "finance"
    url: "https://finance.sina.com.cn/stock/hkstock/ggscyd/"
    priority: 2
    enabled: true

# ============ 5. 任务模板库 ============
task_templates:
  operator_daily_monitor:
    id: "operator_daily_monitor"
    name: "运营商日常新闻监测"
    description: "监测指定运营商的官网和行业媒体新闻，适合日常信息收集"
    applicable_scenarios: ["日常监测", "定期汇报", "信息跟踪"]
    
    trigger_conditions:
      keywords: ["最新", "最近", "今天", "本周", "新闻", "动态"]
      required_entities: ["operator"]
      forbidden_keywords: ["财报", "业绩", "年报"]  # 财报季用专用模板
      
    task_structure:
      level_1:
        type: "by_source_type"
        description: "按来源类型分解"
        children:
          - source_type: "official"
            priority: 5
            max_items: 10
            description: "官网新闻（最高优先级）"
          - source_type: "industry"
            priority: 3
            max_items: 15
            description: "行业媒体报道"
          - source_type: "media"
            priority: 3
            max_items: 8
            description: "央媒报道"
            
      level_2:
        type: "by_keyword_group"
        description: "按关键词组进一步细分"
        groups:
          - name: "business"
            keywords: ["业务动态", "服务升级", "产品发布"]
          - name: "technology"
            keywords: ["技术创新", "网络建设", "研发投入"]
          - name: "cooperation"
            keywords: ["合作", "签约", "生态"]
            
    parameters:
      - name: "operator"
        type: "str"
        required: true
        description: "目标运营商"
        options: ["中国移动", "中国电信", "中国联通", "中国铁塔"]
        
      - name: "days"
        type: "int"
        required: false
        default: 7
        description: "查询天数"
        min: 1
        max: 30
        
      - name: "focus_areas"
        type: "List[str]"
        required: false
        default: []
        description: "关注领域"
        
    expected_output: "结构化新闻列表，按优先级排序，包含分类统计"
    
    quality_criteria:
      min_items: 5
      coverage_requirements:
        official: 0.3  # 至少30%来自官方
        industry: 0.4
        
  financial_report_focus:
    id: "financial_report_focus"
    name: "财报季深度追踪"
    description: "财报发布期间的全方位信息采集，包括官方财报、分析师解读、市场反应"
    applicable_scenarios: ["财报季", "业绩分析", "投资研究"]
    
    trigger_conditions:
      keywords: ["财报", "年报", "半年报", "季报", "业绩", "营收", "利润", "EBITDA"]
      time_sensitive: true
      priority_boost: 2
      
    task_structure:
      level_1:
        type: "by_operator"
        description: "覆盖所有运营商"
        all_operators: true
        
      level_2:
        type: "by_content_type"
        description: "按内容类型分解"
        children:
          - type: "official_report"
            priority: 5
            max_items: 5
            description: "官方财报/业绩公告"
            sources: ["official"]
            
          - type: "analyst_review"
            priority: 4
            max_items: 10
            description: "分析师解读/研报"
            sources: ["finance_media", "research"]
            
          - type: "market_reaction"
            priority: 3
            max_items: 8
            description: "市场反应/股价表现"
            sources: ["finance_platform"]
            
          - type: "industry_impact"
            priority: 3
            max_items: 8
            description: "行业影响分析"
            sources: ["industry_media"]
            
    parameters:
      - name: "quarter"
        type: "str"
        required: true
        description: "财报季度"
        options: ["Q1", "Q2", "Q3", "Q4", "annual"]
        
      - name: "year"
        type: "int"
        required: true
        description: "年份"
        
    expected_output: "财报综合分析报告，包含对比分析、趋势解读、市场反应"
    
    special_handling:
      cross_verify: true  # 需要交叉验证
      alert_on_missing: ["official_report"]  # 缺少官方报告时告警
      
  executive_tracking:
    id: "executive_tracking"
    name: "高管动态追踪"
    description: "追踪指定高管的公开活动、发言、署名文章等"
    applicable_scenarios: ["高管监测", "领导动态", "重要人物跟踪"]
    
    trigger_conditions:
      keywords: ["董事长", "总经理", "CEO", "总裁", "高管", "领导"]
      required_entities: ["executive_name"]
      
    task_structure:
      level_1:
        type: "by_search_engine"
        description: "多搜索引擎并行"
        engines: ["brave", "bing"]
        keyword_patterns:
          - "{executive_name} {operator}"
          - "{executive_name} 讲话"
          - "{executive_name} 署名文章"
          - "{executive_name_alias} {operator}"
          
      level_2:
        type: "by_content_type"
        description: "按内容类型"
        children:
          - type: "speech"
            priority: 5
            keywords: ["讲话", "发言", "致辞", "演讲"]
          - type: "article"
            priority: 4
            keywords: ["署名文章", "撰文", "发表"]
          - type: "activity"
            priority: 4
            keywords: ["调研", "考察", "出席", "会见"]
          - type: "interview"
            priority: 3
            keywords: ["采访", "专访", "对话"]
            
    parameters:
      - name: "executive_name"
        type: "str"
        required: true
        description: "高管姓名"
        
      - name: "operator"
        type: "str"
        required: true
        description: "所属运营商"
        
      - name: "days"
        type: "int"
        required: false
        default: 30
        description: "查询天数"
        
    expected_output: "高管动态时间线，按类型分类"
    
  tech_trend_tracking:
    id: "tech_trend_tracking"
    name: "技术热点追踪"
    description: "追踪特定技术领域的最新进展，支持跨运营商对比"
    applicable_scenarios: ["技术调研", "趋势分析", "竞品对比"]
    
    trigger_conditions:
      keywords: ["AI", "5G-A", "6G", "低空", "卫星", "量子", "大模型", "算力网络"]
      required_entities: ["tech_keyword"]
      
    task_structure:
      level_1:
        type: "by_operator"
        description: "跨运营商对比"
        all_operators: true
        
      level_2:
        type: "by_content_depth"
        description: "按内容深度"
        children:
          - type: "announcement"
            priority: 5
            keywords: ["发布", "推出", "商用", "上线"]
            description: "官方发布/ announcements"
          - type: "deployment"
            priority: 4
            keywords: ["部署", "建设", "开通", "覆盖"]
            description: "部署进展"
          - type: "pilot_project"
            priority: 3
            keywords: ["试点", "试验", "验证", "测试"]
            description: "试点项目"
          - type: "rd_progress"
            priority: 3
            keywords: ["研发", "突破", "专利", "标准"]
            description: "研发进展"
            
    parameters:
      - name: "tech_keyword"
        type: "str"
        required: true
        description: "技术关键词"
        
      - name: "operators"
        type: "List[str]"
        required: false
        default: ["all"]
        description: "目标运营商列表"
        
    expected_output: "技术热点追踪报告，含跨运营商对比"
    
    special_handling:
      cross_operator_compare: true
      timeline_view: true
      
  emergency_response:
    id: "emergency_response"
    name: "重大事件应急响应"
    description: "针对突发事件的快速信息采集，60秒内完成初步扫描"
    applicable_scenarios: ["突发事件", "故障通报", "安全事件", "舆情监测"]
    
    trigger_conditions:
      keywords: ["故障", "事故", "中断", " outage", "安全事件", "网络攻击", "数据泄露"]
      urgency: "high"
      priority_boost: 3
      
    task_structure:
      level_1:
        type: "parallel_search"
        description: "全来源并行搜索"
        timeout: 60
        sources: "all_enabled"
        max_concurrent: 10
        
    parameters:
      - name: "event_keyword"
        type: "str"
        required: true
        description: "事件关键词"
        
      - name: "affected_operator"
        type: "str"
        required: false
        default: "unknown"
        description: "受影响运营商"
        
    expected_output: "事件快报，按时间线排序，标注信息来源可信度"
    
    special_handling:
      fast_mode: true
      credibility_highlight: true
      auto_refresh: true  # 支持自动刷新

# ============ 6. 事件类型配置 ============
event_types:
  breaking_news:
    name: "突发新闻"
    keywords: ["突发", "紧急", "刚刚", "最新"]
    priority: 5
    template_id: "emergency_response"
    requires_cross_verify: true
    alert_threshold: 1
    
  product_launch:
    name: "产品发布"
    keywords: ["发布", "推出", "上市", "商用"]
    priority: 4
    template_id: "tech_trend_tracking"
    
  partnership:
    name: "战略合作"
    keywords: ["战略合作", "签约", "合作", "共建"]
    priority: 4
    template_id: "operator_daily_monitor"
    requires_cross_verify: true
    
  executive_change:
    name: "人事变动"
    keywords: ["任命", "调任", "离职", "履新", "辞职"]
    priority: 5
    template_id: "executive_tracking"
    requires_cross_verify: true

---

## 4. ReAct主流程

### 4.1 主控循环

```python
class MasterController:
    """主控器 - 协调Bootstrap和ReAct流程"""
    
    def __init__(self):
        self.bootstrap = BootstrapEngine()
        self.knowledge_base = None
        self.constraints = GlobalConstraints(
            max_depth=3,
            max_tasks=100,
            max_duration=600,
            max_memory=500*1024*1024
        )
        
    async def initialize(self):
        """系统初始化 - 加载Bootstrap知识库"""
        self.knowledge_base = await self.bootstrap.bootstrap()
        
    async def process(self, query: UserQuery) -> SystemResult:
        """
        主处理流程
        """
        start_time = time.time()
        self.state = ExecutionState(start_time=start_time)
        
        try:
            # M1: 任务分解（带ReAct）
            plan_result = await self._execute_module(
                'planner',
                self._plan_tasks,
                query
            )
            
            if not plan_result.success:
                return self._create_error_result('planning', plan_result)
            
            # M2: 采集执行（带ReAct）
            collection_result = await self._execute_module(
                'collector',
                self._collect_data,
                plan_result.output
            )
            
            # M3: 存储管理（带ReAct）
            storage_result = await self._execute_module(
                'storage',
                self._store_data,
                collection_result.items
            )
            
            # M4: 报告汇编（带ReAct）
            report_result = await self._execute_module(
                'assembler',
                self._assemble_report,
                storage_result.processed_items,
                query
            )
            
            # 全局反思
            global_reflection = self._global_reflect(
                plan_result, collection_result, 
                storage_result, report_result
            )
            
            return SystemResult(
                success=True,
                report=report_result.output,
                statistics=self._generate_statistics(),
                global_reflection=global_reflection,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return SystemResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _execute_module(self, name: str, executor, *args) -> ModuleResult:
        """执行模块，带ReAct循环"""
        # 检查约束
        if not self._check_constraints():
            return ModuleResult(
                success=False, 
                error=f"约束违反: {self._get_constraint_violation()}"
            )
        
        # 执行
        try:
            output = await executor(*args)
            return ModuleResult(success=True, output=output)
        except Exception as e:
            return ModuleResult(success=False, error=str(e))
```

### 4.2 全局约束检查

```python
class GlobalConstraints:
    """全局约束"""
    
    max_depth: int = 3              # 任务分解最大深度
    max_tasks: int = 100            # 子任务数量上限
    max_duration: float = 600       # 总耗时上限（秒）
    max_memory: int = 524288000     # 内存上限（500MB）
    max_retries: int = 3            # 单任务最大重试
    min_quality_score: float = 0.6  # 数据质量及格线


def check_constraints(state: ExecutionState, constraints: GlobalConstraints) -> ConstraintCheck:
    """检查全局约束"""
    violations = []
    
    # 时间约束
    elapsed = time.time() - state.start_time
    if elapsed > constraints.max_duration:
        violations.append(ConstraintViolation(
            type='time',
            message=f"超时: {elapsed:.0f}s > {constraints.max_duration}s"
        ))
    
    # 任务数约束
    if state.task_count > constraints.max_tasks:
        violations.append(ConstraintViolation(
            type='task_count',
            message=f"任务过多: {state.task_count} > {constraints.max_tasks}"
        ))
    
    # 内存约束
    memory = psutil.Process().memory_info().rss
    if memory > constraints.max_memory:
        violations.append(ConstraintViolation(
            type='memory',
            message=f"内存超限: {memory/1024/1024:.0f}MB > {constraints.max_memory/1024/1024:.0f}MB"
        ))
    
    # 深度约束
    if state.current_depth > constraints.max_depth:
        violations.append(ConstraintViolation(
            type='depth',
            message=f"深度超限: {state.current_depth} > {constraints.max_depth}"
        ))
    
    return ConstraintCheck(
        passed=len(violations) == 0,
        violations=violations
    )
```

---

## 5. 模块详细设计

### 5.1 M1: 任务分解模块

#### 5.1.1 核心设计

```python
class TaskPlanner:
    """任务规划器 - Bootstrap感知 + ReAct循环"""
    
    def __init__(self, knowledge_base: BootstrapKnowledgeBase):
        self.kb = knowledge_base
        self.max_depth = 3
        self.max_tasks = 100
        
    async def plan(self, query: UserQuery) -> TaskTree:
        """
        ReAct循环: Thought → Action → Observe → Reflect → (Adapt)
        """
        # === Thought: 分析查询，决定策略 ===
        thought = self._think(query)
        
        # 尝试模板匹配
        template_match = self._match_template(query)
        
        if template_match and template_match.confidence > 0.8:
            # Action: 使用模板实例化
            task_tree = self._instantiate_template(template_match.template, query)
        else:
            # Action: 动态分解
            task_tree = await self._dynamic_decompose(query)
        
        # === Observe: 观察生成的任务树 ===
        observations = self._observe_tree(task_tree)
        
        # === Reflect: 反思任务合理性 ===
        reflection = self._reflect(task_tree, observations)
        
        # Adapt: 根据反思调整
        if reflection.needs_adjustment:
            task_tree = await self._adjust_tree(task_tree, reflection)
        
        return task_tree
    
    def _think(self, query: UserQuery) -> Thought:
        """思考阶段: 分析查询特征"""
        considerations = []
        
        # 分析运营商
        detected_operators = self._detect_operators(query.text)
        considerations.append(f"检测到运营商: {detected_operators}")
        
        # 分析时间范围
        date_range = self._parse_date_range(query.text)
        considerations.append(f"时间范围: {date_range}")
        
        # 分析关键词
        keywords = self._extract_keywords(query.text)
        considerations.append(f"关键词: {keywords}")
        
        # 判断场景
        scenario = self._detect_scenario(query.text)
        considerations.append(f"场景判断: {scenario}")
        
        return Thought(
            reasoning="\n".join(considerations),
            detected_operators=detected_operators,
            date_range=date_range,
            keywords=keywords,
            scenario=scenario
        )
    
    def _match_template(self, query: UserQuery) -> Optional[TemplateMatch]:
        """匹配最佳模板"""
        matches = []
        
        for template in self.kb.task_templates.templates.values():
            score = 0.0
            reasons = []
            
            # 关键词匹配
            for kw in template.trigger_conditions.keywords:
                if kw in query.text:
                    score += 0.3
                    reasons.append(f"触发词: {kw}")
            
            # 实体匹配
            if template.trigger_conditions.required_entities:
                for entity in template.trigger_conditions.required_entities:
                    if self._has_entity(query, entity):
                        score += 0.4
                        reasons.append(f"实体: {entity}")
            
            # 排除词检查
            if template.trigger_conditions.forbidden_keywords:
                for kw in template.trigger_conditions.forbidden_keywords:
                    if kw in query.text:
                        score -= 0.5
                        reasons.append(f"排除词: {kw}")
            
            if score > 0.5:
                matches.append(TemplateMatch(
                    template=template,
                    confidence=min(score, 1.0),
                    reasons=reasons
                ))
        
        if matches:
            matches.sort(key=lambda x: x.confidence, reverse=True)
            return matches[0]
        
        return None
    
    async def _dynamic_decompose(self, query: UserQuery) -> TaskTree:
        """动态任务分解"""
        root = TaskNode(
            id="root",
            level=0,
            type="root",
            description=query.text
        )
        
        # L1: 按运营商分解
        operators = self._detect_operators(query.text) or ["中国移动", "中国电信", "中国联通", "中国铁塔"]
        for op in operators[:4]:  # 最多4个运营商
            if len(root.children) >= 20:  # 单节点限制
                break
            child = self._create_operator_node(op, root)
            root.children.append(child)
        
        # L2: 按来源分解
        for child in root.children:
            await self._decompose_by_source(child, query)
        
        # L3: 按关键词细化
        for child in root.children:
            for grandchild in child.children:
                await self._decompose_by_keywords(grandchild, query)
        
        return TaskTree(root=root)
    
    def _reflect(self, tree: TaskTree, observations: TreeObservations) -> Reflection:
        """反思任务树质量"""
        issues = []
        suggestions = []
        
        # 检查任务分布
        if observations.task_by_level.get(1, 0) > 4:
            issues.append("L1任务过多")
            suggestions.append("考虑合并相似运营商查询")
        
        # 检查来源覆盖
        source_types = set()
        def collect_sources(node):
            if node.source_type:
                source_types.add(node.source_type)
            for child in node.children:
                collect_sources(child)
        collect_sources(tree.root)
        
        if 'official' not in source_types:
            issues.append("缺少官方来源")
            suggestions.append("添加官网新闻采集任务")
        
        # 检查关键词覆盖
        all_keywords = set()
        def collect_keywords(node):
            all_keywords.update(node.keywords)
            for child in node.children:
                collect_keywords(child)
        collect_keywords(tree.root)
        
        core_kw_coverage = len(
            all_keywords & set(self.kb.keyword_graph.core_keywords)
        ) / len(self.kb.keyword_graph.core_keywords)
        
        if core_kw_coverage < 0.5:
            issues.append("核心关键词覆盖不足")
            suggestions.append("扩展关键词列表")
        
        # 预估耗时
        estimated_duration = observations.task_count * 3  # 平均每任务3秒
        if estimated_duration > 300:
            issues.append("预估耗时过长")
            suggestions.append("减少低优先级任务或增加并发")
        
        return Reflection(
            success=len(issues) == 0,
            issues=issues,
            suggestions=suggestions,
            needs_adjustment=len(issues) > 0,
            confidence=1.0 - len(issues) * 0.15
        )
```

#### 5.1.2 任务树结构

```yaml
# 任务树示例
task_tree:
  root:
    id: "root"
    level: 0
    type: "root"
    description: "查询中国移动最近AI方面的新闻"
    
    children:
      - id: "op_cm"
        level: 1
        type: "operator"
        operator: "中国移动"
        keywords: ["中国移动", "中移动", "China Mobile"]
        
        children:
          - id: "cm_official"
            level: 2
            type: "source"
            source_type: "official"
            source_id: "cm_official_news"
            priority: 5
            
            children:
              - id: "cm_official_ai"
                level: 3
                type: "concrete"
                keywords: ["中国移动", "AI", "人工智能", "大模型", "九天大模型"]
                url: "https://www.10086.cn/aboutus/news/"
                
              - id: "cm_official_cloud"
                level: 3
                type: "concrete"
                keywords: ["中国移动", "移动云", "云服务", "算力"]
                
          - id: "cm_industry"
            level: 2
            type: "source"
            source_type: "industry"
            
            children:
              - id: "cm_c114_ai"
                level: 3
                type: "concrete"
                source_id: "c114"
                keywords: ["中国移动", "AI", "人工智能"]
                
          - id: "cm_search"
            level: 2
            type: "source"
            source_type: "search"
            
            children:
              - id: "cm_brave_ai"
                level: 3
                type: "concrete"
                engine: "brave"
                keywords: ["中国移动", "AI", "杨杰"]  # 注入高管名
                
  stats:
    total_tasks: 12
    max_depth: 3
    by_level: {0: 1, 1: 1, 2: 3, 3: 7}
    by_source: {official: 2, industry: 1, search: 4}
    estimated_duration: "36秒"
    
  reflection:
    confidence: 0.88
    issues: []
    suggestions: ["可考虑增加中国铁塔对比"]
```

### 5.2 M2: 采集引擎模块

#### 5.2.1 自适应采集策略

```python
class AdaptiveCollectionEngine:
    """自适应采集引擎 - 5级策略自动升级"""
    
    STRATEGIES = {
        'level_1_basic': {
            'name': '基础HTTP',
            'tools': ['requests'],
            'features': ['static_ua'],
            'use_when': '简单站点，无反爬',
        },
        'level_2_standard': {
            'name': '标准爬虫',
            'tools': ['requests', 'bs4'],
            'features': ['ua_rotation', 'random_delay', 'cookie_persist'],
            'use_when': '一般站点，基础反爬',
        },
        'level_3_advanced': {
            'name': '高级爬虫',
            'tools': ['requests', 'bs4', 'proxy_pool'],
            'features': ['ua_rotation', 'request_fingerprint', 'proxy_rotation', 
                        'retry_backoff', 'session_management'],
            'use_when': '较强反爬',
        },
        'level_4_playwright': {
            'name': '浏览器模拟',
            'tools': ['playwright'],
            'features': ['real_browser', 'js_execution', 'human_like_behavior',
                        'stealth_mode', 'viewport_rotation'],
            'use_when': '重度反爬，需JS渲染',
        },
        'level_5_intelligent': {
            'name': '智能对抗',
            'tools': ['playwright', 'ml_detection'],
            'features': ['all_level4', 'captcha_solving', 'behavior_learning',
                        'fingerprint_randomization', 'residential_proxy'],
            'use_when': '极端反爬',
        },
    }
    
    async def collect(self, task: TaskNode) -> CollectionResult:
        """
        ReAct循环采集
        """
        # Thought: 选择初始策略
        thought = self._think_strategy(task)
        strategy = thought.suggested_strategy
        
        # Action → Observe → Reflect 循环
        for attempt in range(3):
            try:
                result = await self._execute(task, strategy)
                observations = self._observe(result)
                reflection = self._reflect(observations)
                
                if reflection.success:
                    return CollectionResult(
                        success=True,
                        items=result.items,
                        strategy_used=strategy,
                        attempt_count=attempt + 1
                    )
                
                if reflection.needs_escalation:
                    strategy = self._escalate_strategy(strategy)
                    continue
                    
            except AntiSpiderDetected as e:
                strategy = self._escalate_strategy(strategy, reason=str(e))
                continue
                
            except Exception as e:
                if attempt == 2:
                    return CollectionResult(
                        success=False,
                        error=str(e),
                        strategy_used=strategy
                    )
        
        return CollectionResult(success=False, error="Max retries exceeded")
    
    def _think_strategy(self, task: TaskNode) -> StrategyThought:
        """思考采集策略"""
        considerations = []
        
        # 分析来源
        source_config = self.kb.sources.get(task.source_id)
        if source_config:
            anti_spider_level = source_config.get('anti_spider_level', 1)
            considerations.append(f"来源反爬等级: {anti_spider_level}")
            
            if anti_spider_level >= 3:
                suggested = 'level_4_playwright'
            elif anti_spider_level >= 2:
                suggested = 'level_3_advanced'
            else:
                suggested = 'level_2_standard'
        else:
            suggested = 'level_2_standard'
            considerations.append("未知来源，使用保守策略")
        
        # 分析任务特征
        if task.priority >= 5:
            considerations.append("高优先级任务，允许使用高级策略")
        
        return StrategyThought(
            reasoning="\n".join(considerations),
            suggested_strategy=suggested,
            confidence=0.8 if source_config else 0.6
        )
    
    def _observe(self, result: RawResult) -> CollectionObservations:
        """观察采集结果"""
        observations = CollectionObservations()
        
        # 反爬信号
        if result.status_code in [403, 429, 503]:
            observations.antispider_detected = True
            observations.block_type = result.status_code
            
        if 'captcha' in result.content.lower() or '验证' in result.content:
            observations.captcha_detected = True
            observations.antispider_detected = True
        
        # 内容质量
        if result.items:
            observations.item_count = len(result.items)
            observations.avg_content_length = sum(
                len(item.content) for item in result.items
            ) / len(result.items)
            
            incomplete = sum(
                1 for item in result.items
                if len(item.content) < 50 or not item.title
            )
            observations.incomplete_ratio = incomplete / len(result.items)
        
        return observations
    
    def _reflect(self, observations: CollectionObservations) -> CollectionReflection:
        """反思采集结果"""
        if observations.antispider_detected:
            return CollectionReflection(
                success=False,
                needs_escalation=True,
                reason="检测到反爬机制"
            )
        
        if observations.item_count == 0:
            return CollectionReflection(
                success=False,
                needs_escalation=False,
                reason="未获取数据，可能结构变化"
            )
        
        if observations.incomplete_ratio > 0.5:
            return CollectionReflection(
                success=False,
                needs_escalation=True,
                reason="内容不完整率过高"
            )
        
        return CollectionReflection(success=True)
```

#### 5.2.2 质量评估体系

```python
class QualityAssessor:
    """多维度质量评估"""
    
    DIMENSIONS = {
        'completeness': 0.25,   # 完整性
        'credibility': 0.25,    # 可信度
        'relevance': 0.20,      # 相关性
        'freshness': 0.15,      # 时效性
        'richness': 0.15,       # 丰富度
    }
    
    def assess(self, item: NewsItem) -> QualityScore:
        """评估单条新闻质量"""
        scores = {}
        
        # 1. 完整性 (25%)
        completeness_checks = [
            (item.title and 10 <= len(item.title) <= 100, 0.3),
            (item.content and len(item.content) >= 100, 0.3),
            (item.published_at is not None, 0.2),
            (item.source_name is not None, 0.2),
        ]
        scores['completeness'] = sum(
            weight for check, weight in completeness_checks if check
        )
        
        # 2. 可信度 (25%)
        source_scores = {
            '中国移动官网': 1.0,
            '中国电信官网': 1.0,
            'C114通信网': 0.8,
            '通信世界网': 0.8,
            '新浪财经': 0.6,
            '百度新闻': 0.5,
        }
        scores['credibility'] = source_scores.get(item.source_name, 0.4)
        
        # 3. 相关性 (20%)
        if item.keywords:
            matches = sum(
                1 for kw in item.keywords
                if kw in item.title or kw in item.content[:500]
            )
            scores['relevance'] = min(1.0, matches / 3)
        else:
            scores['relevance'] = 0.5
        
        # 4. 时效性 (15%)
        if item.published_at:
            days_old = (datetime.now() - item.published_at).days
            if days_old <= 1:
                scores['freshness'] = 1.0
            elif days_old <= 3:
                scores['freshness'] = 0.8
            elif days_old <= 7:
                scores['freshness'] = 0.6
            elif days_old <= 30:
                scores['freshness'] = 0.4
            else:
                scores['freshness'] = 0.2
        else:
            scores['freshness'] = 0.0
        
        # 5. 丰富度 (15%)
        richness_features = [
            (len(item.content) >= 500, 0.2),
            (item.has_image, 0.1),
            ('。' in item.content, 0.1),
            (any(c.isdigit() for c in item.content), 0.1),
            (len(item.content) >= 1000, 0.2),
        ]
        scores['richness'] = sum(
            weight for check, weight in richness_features if check
        )
        
        # 综合得分
        overall = sum(
            scores[dim] * weight 
            for dim, weight in self.DIMENSIONS.items()
        )
        
        return QualityScore(
            overall=overall,
            dimensions=scores,
            passed=overall >= 0.6
        )
```

### 5.3 M3: 存储管理模块

```python
class StorageManager:
    """存储管理器 - 带ReAct循环"""
    
    async def store(self, items: List[NewsItem]) -> StorageResult:
        """
        ReAct: Thought → Action → Observe → Reflect
        """
        # Thought: 分析数据特征
        thought = self._think_storage(items)
        
        # Action: 执行存储流程
        # 1. 保存原始数据
        raw_path = await self._save_raw(items)
        
        # 2. 标准化
        normalized = self._normalize(items)
        
        # 3. 去重
        deduped = self._deduplicate(normalized)
        
        # 4. 保存处理后数据
        processed_path = await self._save_processed(deduped)
        
        # 5. 构建索引
        index = self._build_index(deduped)
        
        # Observe: 观察存储结果
        observations = StorageObservations(
            raw_count=len(items),
            normalized_count=len(normalized),
            deduped_count=len(deduped),
            duplicate_rate=(len(normalized) - len(deduped)) / len(normalized) if normalized else 0,
            storage_paths={'raw': raw_path, 'processed': processed_path}
        )
        
        # Reflect: 反思存储质量
        reflection = self._reflect_storage(observations)
        
        if reflection.needs_reprocess:
            deduped = await self._reprocess(normalized, reflection)
        
        return StorageResult(
            success=True,
            processed_items=deduped,
            observations=observations,
            reflection=reflection
        )
    
    def _deduplicate(self, items: List[NewsItem]) -> List[NewsItem]:
        """智能去重 - SimHash + 语义相似度"""
        # 1. URL精确去重
        url_map = {}
        for item in items:
            if item.url not in url_map:
                url_map[item.url] = item
        
        unique_by_url = list(url_map.values())
        
        # 2. SimHash相似去重
        simhash_index = SimHashIndex()
        deduped = []
        
        for item in unique_by_url:
            hash_val = simhash(item.title + item.content[:200])
            similar = simhash_index.get_similar(hash_val, threshold=3)
            
            if similar:
                # 合并或选择最佳
                best = self._select_best([item] + similar)
                simhash_index.update(hash_val, best)
            else:
                simhash_index.add(hash_val, item)
                deduped.append(item)
        
        return deduped
```

### 5.4 M4: 报告汇编模块

```python
class ReportAssembler:
    """报告汇编器 - 带ReAct循环"""
    
    async def assemble(
        self, 
        items: List[NewsItem], 
        query: UserQuery
    ) -> Report:
        """
        ReAct: Thought → Action → Observe → Reflect
        """
        # Thought: 分析数据，选择报告结构
        thought = self._think_report_structure(items, query)
        
        # Action: 生成报告
        # 1. 智能摘要
        summaries = self._generate_summaries(items)
        
        # 2. 交叉验证
        verification = self._cross_verify(items)
        
        # 3. 分类聚合
        grouped = self._group_by_category(items)
        
        # 4. 按模板渲染
        draft = self._render_template(
            items, summaries, verification, grouped,
            thought.suggested_template
        )
        
        # Observe: 观察报告质量
        observations = ReportObservations(
            coverage=self._check_coverage(draft, items),
            balance=self._check_operator_balance(draft),
            redundancy=self._check_redundancy(draft),
            readability=self._assess_readability(draft)
        )
        
        # Reflect: 反思报告质量
        reflection = self._reflect_report(draft, observations)
        
        # Adapt: 优化报告
        if reflection.needs_improvement:
            draft = await self._improve_report(draft, reflection)
        
        return Report(
            content=draft,
            quality_observations=observations,
            reflection=reflection
        )
    
    def _cross_verify(self, items: List[NewsItem]) -> VerificationResult:
        """交叉验证 - 识别信息冲突"""
        # 按事件分组
        event_groups = self._group_by_event(items)
        
        verifications = []
        for event_id, event_items in event_groups.items():
            if len(event_items) < 2:
                continue
            
            # 检查关键信息一致性
            inconsistencies = []
            
            # 时间一致性
            dates = [item.published_at for item in event_items if item.published_at]
            if dates and max(dates) - min(dates) > timedelta(days=1):
                inconsistencies.append("发布时间差异超过1天")
            
            # 内容一致性（简单版本）
            contents = [item.content[:100] for item in event_items]
            similarity = self._calculate_similarity(contents)
            if similarity < 0.5:
                inconsistencies.append("内容描述差异较大")
            
            verifications.append(EventVerification(
                event_id=event_id,
                item_count=len(event_items),
                sources=[item.source_name for item in event_items],
                inconsistencies=inconsistencies,
                confidence=1.0 - len(inconsistencies) * 0.3
            ))
        
        return VerificationResult(verifications=verifications)

---

## 6. 数据模型

### 6.1 核心数据类

```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

# ============ 基础枚举 ============

class SourceType(Enum):
    OFFICIAL = "official"       # 官方渠道
    INDUSTRY = "industry"       # 行业媒体
    MEDIA = "media"             # 央媒
    FINANCE = "finance"         # 财经平台
    SEARCH = "search"           # 搜索引擎
    SOCIAL = "social"           # 社交媒体

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class NewsCategory(Enum):
    BUSINESS = "业务动态"
    TECHNOLOGY = "技术创新"
    COOPERATION = "战略合作"
    FINANCIAL = "财务数据"
    POLICY = "政策公告"
    SOCIAL = "社会责任"

# ============ Bootstrap 数据模型 ============

@dataclass
class OperatorProfile:
    """运营商档案"""
    name: str
    aliases: List[str]
    english_name: str
    stock_code: str
    official_sites: List['OfficialSite']
    official_wechat: List[str]
    official_weibo: Optional[str]
    business_tags: List[str]
    recent_focus: List[str]

@dataclass
class OfficialSite:
    """官方网站配置"""
    name: str
    url: str
    news_url: str
    encoding: str
    selectors: Dict[str, str]
    priority: int
    update_frequency: str

@dataclass
class ExecutiveInfo:
    """高管信息"""
    name: str
    position: str
    operator: str
    level: str
    responsibilities: List[str]
    name_aliases: List[str]
    recent_topics: List[str]

@dataclass
class KeywordNode:
    """关键词节点"""
    keyword: str
    aliases: List[str]
    related: List[str]
    priority: int
    category: str

@dataclass
class TaskTemplate:
    """任务模板"""
    id: str
    name: str
    description: str
    applicable_scenarios: List[str]
    trigger_conditions: Dict[str, Any]
    task_structure: Dict[str, Any]
    parameters: List['TemplateParam']
    expected_output: str

@dataclass
class TemplateParam:
    """模板参数"""
    name: str
    type: str
    required: bool
    default: Any = None
    description: str = ""
    options: Optional[List[str]] = None

@dataclass
class SourceConfig:
    """来源配置"""
    id: str
    name: str
    type: SourceType
    url: str
    priority: int
    selectors: Optional[Dict[str, str]]
    encoding: str = "utf-8"
    enabled: bool = True
    anti_spider_level: int = 1

@dataclass
class BootstrapKnowledgeBase:
    """Bootstrap知识库"""
    version: str
    last_updated: datetime
    update_frequency: str
    operators: Dict[str, OperatorProfile]
    executives: Dict[str, List[ExecutiveInfo]]
    keyword_graph: 'KeywordGraph'
    sources: Dict[str, SourceConfig]
    task_templates: 'TaskTemplateLibrary'
    event_types: Dict[str, 'EventTypeConfig']

# ============ 运行时数据模型 ============

@dataclass
class UserQuery:
    """用户查询"""
    text: str
    operators: Optional[List[str]] = None
    date_range: Optional[Dict[str, str]] = None
    focus_areas: Optional[List[str]] = None
    output_format: str = "markdown"

@dataclass
class TaskNode:
    """任务树节点"""
    id: str
    level: int
    parent_id: Optional[str]
    type: str
    description: str
    
    # 执行相关
    operator: Optional[str] = None
    source_type: Optional[SourceType] = None
    source_id: Optional[str] = None
    keywords: List[str] = None
    url: Optional[str] = None
    priority: int = 3
    status: TaskStatus = TaskStatus.PENDING
    
    # ReAct相关
    thought: Optional[str] = None
    reflection: Optional['Reflection'] = None
    
    # 树结构
    children: List['TaskNode'] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.children is None:
            self.children = []

@dataclass
class TaskTree:
    """任务树"""
    root: TaskNode
    stats: Optional['TreeStats'] = None
    reflection: Optional['Reflection'] = None

@dataclass
class NewsItem:
    """新闻条目"""
    # 基础信息
    id: str
    title: str
    url: str
    content: str
    summary: Optional[str] = None
    
    # 时间
    published_at: Optional[datetime] = None
    collected_at: datetime = None
    
    # 来源
    source_name: str = ""
    source_type: SourceType = SourceType.INDUSTRY
    source_url: Optional[str] = None
    
    # 分类
    operators: List[str] = None
    categories: List[str] = None
    keywords: List[str] = None
    
    # 质量
    quality_score: Optional['QualityScore'] = None
    credibility_score: float = 0.0
    
    # 去重
    content_hash: Optional[str] = None
    similar_to: List[str] = None
    
    def __post_init__(self):
        if self.collected_at is None:
            self.collected_at = datetime.now()
        if self.operators is None:
            self.operators = []
        if self.categories is None:
            self.categories = []
        if self.keywords is None:
            self.keywords = []
        if self.similar_to is None:
            self.similar_to = []

@dataclass
class QualityScore:
    """质量评分"""
    overall: float
    dimensions: Dict[str, float]
    passed: bool

@dataclass
class CollectionResult:
    """采集结果"""
    success: bool
    task_id: str
    items: List[NewsItem]
    strategy_used: str = ""
    attempt_count: int = 1
    error: Optional[str] = None

@dataclass
class StorageResult:
    """存储结果"""
    success: bool
    processed_items: List[NewsItem]
    observations: 'StorageObservations'
    reflection: 'Reflection'
    error: Optional[str] = None

@dataclass
class Report:
    """报告"""
    content: str
    quality_observations: 'ReportObservations'
    reflection: 'Reflection'
    metadata: Dict[str, Any] = None

@dataclass
class SystemResult:
    """系统结果"""
    success: bool
    report: Optional[Report] = None
    statistics: Optional[Dict[str, Any]] = None
    global_reflection: Optional['Reflection'] = None
    execution_time: float = 0.0
    error: Optional[str] = None

# ============ ReAct 相关模型 ============

@dataclass
class Thought:
    """思考过程"""
    reasoning: str
    confidence: float = 0.8
    metadata: Dict[str, Any] = None

@dataclass
class Reflection:
    """反思结果"""
    success: bool
    issues: List[str] = None
    suggestions: List[str] = None
    needs_adjustment: bool = False
    confidence: float = 0.8
    action: str = "complete"  # complete | adapt | retry | abort
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.suggestions is None:
            self.suggestions = []

@dataclass
class TreeStats:
    """任务树统计"""
    total_tasks: int
    max_depth: int
    by_level: Dict[int, int]
    by_source: Dict[str, int]
    estimated_duration: float

---

## 7. 技术实现

### 7.1 技术栈

| 层级 | 技术选型 | 说明 |
|-----|---------|------|
| **语言** | Python 3.11+ | 主开发语言 |
| **异步** | asyncio + aiohttp | 高并发采集 |
| **爬虫** | requests / playwright | 自适应策略 |
| **解析** | BeautifulSoup4 / lxml | HTML解析 |
| **去重** | simhash / minhash | 相似度计算 |
| **存储** | JSON文件 + 可选SQLite | 本地存储 |
| **配置** | YAML | 知识库配置 |
| **日志** | loguru | 结构化日志 |

### 7.2 目录结构

```
telecom-news-fetcher/
├── SKILL.md                      # 技能文档
├── PROPOSAL.md                   # 本方案文档
├── README.md                     # 使用说明
├── requirements.txt              # 依赖
├── pyproject.toml               # 项目配置
│
├── bootstrap/                    # Bootstrap知识库
│   ├── __init__.py
│   ├── engine.py                # Bootstrap引擎
│   ├── updater.py               # 知识库更新器
│   ├── discover.py              # 知识发现
│   ├── extract.py               # 信息提取
│   └── data/                    # 数据文件
│       ├── knowledge_base.yaml   # 主知识库
│       ├── operators.yaml        # 运营商配置
│       ├── executives.yaml       # 高管数据库
│       ├── keywords.yaml         # 关键词图谱
│       ├── sources.yaml          # 来源配置
│       └── templates.yaml        # 任务模板
│
├── src/                         # 源代码
│   ├── __init__.py
│   ├── main.py                  # 主入口
│   ├── config.py                # 配置管理
│   │
│   ├── bootstrap/               # Bootstrap模块
│   │   ├── __init__.py
│   │   ├── loader.py            # 知识库加载
│   │   └── validator.py         # 配置验证
│   │
│   ├── planner/                 # M1: 任务分解
│   │   ├── __init__.py
│   │   ├── planner.py           # 主规划器
│   │   ├── template_matcher.py  # 模板匹配
│   │   ├── decomposer.py        # 动态分解
│   │   └── reflector.py         # 反思器
│   │
│   ├── collector/               # M2: 采集引擎
│   │   ├── __init__.py
│   │   ├── engine.py            # 采集引擎
│   │   ├── strategy.py          # 策略管理
│   │   ├── request_manager.py   # 请求管理
│   │   ├── spiders/             # 爬虫集合
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # 基础爬虫
│   │   │   ├── c114.py          # C114爬虫
│   │   │   ├── official.py      # 官网爬虫
│   │   │   └── ...
│   │   └── apis/                # API集合
│   │       ├── __init__.py
│   │       ├── brave_search.py  # Brave搜索
│   │       └── bing_search.py   # Bing搜索
│   │
│   ├── storage/                 # M3: 存储管理
│   │   ├── __init__.py
│   │   ├── manager.py           # 存储管理器
│   │   ├── normalizer.py        # 数据标准化
│   │   ├── deduplicator.py      # 去重器
│   │   └── indexer.py           # 索引器
│   │
│   ├── assembler/               # M4: 报告汇编
│   │   ├── __init__.py
│   │   ├── assembler.py         # 汇编器
│   │   ├── summarizer.py        # 摘要生成
│   │   ├── verifier.py          # 交叉验证
│   │   └── templates/           # 报告模板
│   │       ├── daily_digest.md
│   │       ├── financial_report.md
│   │       └── executive_tracking.md
│   │
│   └── common/                  # 公共模块
│       ├── __init__.py
│       ├── models.py            # 数据模型
│       ├── react.py             # ReAct基类
│       ├── quality.py           # 质量评估
│       └── utils.py             # 工具函数
│
├── data/                        # 数据目录
│   ├── raw/                     # 原始数据
│   ├── processed/               # 处理后数据
│   ├── index/                   # 索引文件
│   └── archive/                 # 归档数据
│
├── output/                      # 报告输出
│
└── tests/                       # 测试
    ├── __init__.py
    ├── test_bootstrap.py
    ├── test_planner.py
    ├── test_collector.py
    └── test_integration.py
```

### 7.3 核心流程伪代码

```python
# ============ 主流程 ============

async def main():
    # 1. 初始化Bootstrap
    bootstrap = BootstrapEngine()
    kb = await bootstrap.bootstrap()
    
    # 2. 创建主控器
    controller = MasterController(kb)
    
    # 3. 处理查询
    query = UserQuery(text="查一下中国移动最近AI方面的新闻")
    result = await controller.process(query)
    
    # 4. 输出结果
    if result.success:
        print(result.report.content)
    else:
        print(f"Error: {result.error}")


# ============ ReAct模块基类 ============

class ReActModule:
    """ReAct模块基类"""
    
    async def execute(self, input_data) -> ModuleResult:
        # Thought
        thought = self.think(input_data)
        
        # Action
        try:
            output = await self.act(thought)
        except Exception as e:
            return ModuleResult(success=False, error=str(e))
        
        # Observe
        observations = self.observe(output)
        
        # Reflect
        reflection = self.reflect(observations)
        
        # Adapt (如果需要)
        if reflection.needs_adjustment:
            output = await self.adapt(output, reflection)
        
        return ModuleResult(
            success=reflection.success,
            output=output,
            reflection=reflection
        )
    
    def think(self, input_data) -> Thought:
        raise NotImplementedError
    
    async def act(self, thought: Thought):
        raise NotImplementedError
    
    def observe(self, output) -> Observations:
        raise NotImplementedError
    
    def reflect(self, observations: Observations) -> Reflection:
        raise NotImplementedError
    
    async def adapt(self, output, reflection: Reflection):
        raise NotImplementedError
```

---

## 8. 演进路线

### Phase 1: 基础框架 (2周)

**目标**: 搭建Bootstrap + ReAct基础框架，实现核心流程跑通

| 任务 | 工期 | 交付物 |
|-----|------|--------|
| Bootstrap知识库设计 | 3天 | knowledge_base.yaml v1 |
| ReAct模块基类 | 2天 | react.py + 基类实现 |
| M1任务分解模块 | 3天 | planner.py + 2个模板 |
| M2采集引擎基础 | 4天 | engine.py + 2个爬虫 |
| 集成测试 | 2天 | 端到端流程跑通 |

**验收标准**:
- 支持"查询XX运营商最近新闻"基础查询
- 任务规划<1秒
- 采集完成<2分钟
- 报告正确生成

### Phase 2: 能力增强 (3周)

**目标**: 完善Bootstrap更新机制，增强采集策略

| 任务 | 工期 | 交付物 |
|-----|------|--------|
| Bootstrap自动更新 | 5天 | updater.py + 定时任务 |
| 自适应采集策略 | 5天 | 5级策略 + Playwright支持 |
| 质量评估体系 | 4天 | QualityAssessor + 5维度评分 |
| 模板库扩展 | 4天 | 5个完整模板 |
| 性能优化 | 3天 | 并发优化 + 缓存机制 |

**验收标准**:
- 知识库日更新自动化
- 反爬自动升级成功率>80%
- 数据质量评分准确率>85%

### Phase 3: 智能化 (3周)

**目标**: 引入LLM辅助，提升智能水平

| 任务 | 工期 | 交付物 |
|-----|------|--------|
| LLM辅助摘要 | 5天 | 智能摘要生成 |
| 话题聚类 | 5天 | 自动话题发现 |
| 情感分析 | 4天 | 舆情倾向分析 |
| 预测性Bootstrap | 4天 | 热点预测 + 预加载 |
| 个性化学习 | 4天 | 用户偏好学习 |

**验收标准**:
- 摘要质量人工评分>4/5
- 话题聚类准确率>80%
- 预测命中率>60%

### Phase 4: 平台化 (长期)

**目标**: 产品化，支持多场景

- Web管理界面
- API服务化
- 多行业扩展（电力、石油等）
- 可视化仪表盘
- 告警与推送

---

## 9. 风险与对策

| 风险 | 可能性 | 影响 | 对策 |
|-----|--------|------|------|
| **网站结构变化** | 高 | 中 | Bootstrap定期更新 + 结构变化检测 |
| **反爬升级** | 中 | 中 | 5级自适应策略 + 人工介入机制 |
| **数据质量不达标** | 中 | 高 | 多维度质量评估 + 人工审核流程 |
| **性能不达标** | 低 | 中 | 并发优化 + 缓存 + 降级策略 |
| **知识库过时** | 中 | 中 | 自动更新 + 过期提醒 |
| **依赖服务不稳定** | 中 | 低 | 多源备份 + 本地缓存 |

---

## 附录

### A. 术语表

| 术语 | 说明 |
|-----|------|
| **Bootstrap** | 系统启动时预加载的领域知识库 |
| **ReAct** | Reasoning + Acting 循环架构 |
| **SimHash** | 局部敏感哈希算法，用于文本去重 |
| **Playwright** | 自动化浏览器测试工具，用于模拟真实用户 |
| **ARPU** | 每用户平均收入 (Average Revenue Per User) |

### B. 参考资料

1. ReAct论文: "ReAct: Synergizing Reasoning and Acting in Language Models"
2. SimHash算法: "Detecting Near-Duplicates for Web Crawling"
3. 运营商官网: 中国移动、中国电信、中国联通、中国铁塔
4. 行业媒体: C114通信网、通信世界网、中国信息产业网

---

**文档版本**: v3.0  
**最后更新**: 2026-04-30  
**作者**: OpenClaw Assistant