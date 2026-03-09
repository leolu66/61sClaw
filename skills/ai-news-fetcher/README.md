# News Spider - 可配置新闻采集机器人

基于 YAML 配置的通用新闻采集框架，支持 XPath/CSS/Regex 多种提取方式，便于新增站点和维护。

## 项目结构

```
news-spider/
├── spider/                 # 核心代码
│   ├── __init__.py
│   ├── config_loader.py    # 配置加载器
│   ├── extractors.py       # 字段提取器
│   ├── engine.py           # 采集引擎
│   ├── monitor.py          # 监控告警
│   └── storage.py          # 数据存储
├── site-configs/           # 站点配置
│   ├── _template.yaml      # 配置模板
│   ├── jiqizhixin.yaml     # 机器之心
│   └── qbitai.yaml         # 量子位
├── tests/                  # 测试
├── logs/                   # 日志
├── spider_cli.py           # 命令行工具
└── main.py                 # 主入口
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 创建站点配置

复制模板创建新站点配置：

```bash
cp site-configs/_template.yaml site-configs/mynews.yaml
```

编辑配置，填写目标网站的 XPath/CSS 选择器。

### 3. 测试配置

```bash
# 测试单个站点
python spider_cli.py test jiqizhixin --url "https://www.jiqizhixin.com/articles"

# 测试特定字段
python spider_cli.py test jiqizhixin --field title --url "https://..."
```

### 4. 运行采集

```bash
# 采集所有站点
python main.py

# 采集指定站点
python main.py --site jiqizhixin

# 指定输出格式
python main.py --output json --file news.json
```

## 配置说明

详见 `site-configs/_template.yaml` 中的注释。

## 添加新站点流程

1. 复制 `site-configs/_template.yaml` 为 `{sitename}.yaml`
2. 使用浏览器开发者工具获取 XPath/CSS 选择器
3. 使用 `python spider_cli.py test {sitename}` 验证配置
4. 调整配置直到所有字段提取正常
5. 启用站点 `enabled: true`

## 网站改版处理

当目标网站改版时：

1. 复制旧配置为备份：`cp jiqizhixin.yaml jiqizhixin-v1.yaml`
2. 修改原配置中的选择器
3. 升级 `config_version` 字段
4. 重新测试验证

## License

MIT
