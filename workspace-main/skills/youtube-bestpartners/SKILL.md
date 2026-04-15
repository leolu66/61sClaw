# YouTube 最佳拍档频道视频获取工具

获取 YouTube 频道"最佳拍档"(@bestpartners)的最新视频信息，包括标题、时间、简介和链接。

## 功能特点

- 自动检查 VPN 状态，如未启动则自动启动 Clash for Windows
- 获取视频标题、时长、发布时间、观看次数和链接
- 输出为 Markdown 表格格式
- 结果同时保存到本地文件

## 使用方法

### 方式一：直接运行脚本

```bash
# 使用配置文件中的输出目录
python scripts/fetch_videos.py

# 指定输出目录（覆盖配置）
python scripts/fetch_videos.py --output-dir D:\\anthropic\\bestpartner
```

### 方式二：通过 Claude Code Skill 调用

在 Claude Code 中输入：
```
获取最佳拍档最新视频
```
或
```
获取 YouTube 最佳拍档频道视频
```

## 输出格式

脚本会输出 Markdown 格式的视频列表：

| 序号 | 视频标题 | 时长 | 发布时间 | 观看次数 | 链接 |
|------|---------|------|---------|---------|------|

- **视频标题**：保留原始完整内容（包含标签，通过 `|` 分隔）
- **观看次数**：只显示数字，去掉"次观看"后缀

过滤规则

- **时长过滤**：自动过滤少于 2 分钟的短视频（YouTube Shorts/广告）
- **日期过滤**：只显示 7 天以内的视频

注意：视频简介需要 JavaScript 渲染，当前版本暂不支持获取。如需查看简介，请点击链接访问视频页面。

## 文件保存位置

本技能需要保存到**外部固定目录**，通过 `config.json` 配置输出路径。

### 配置文件

`config.json`（位于技能目录）：

```json
{
  "output_dir": "D:\\anthropic\\bestpartner",
  "shared_output_dir": "D:\\anthropic\\bestpartner"
}
```

**当前配置**：
- 输出目录：`D:\anthropic\\bestpartner`
- 文件名格式：`bestpartners_videos_YYYY-MM-DD.md`

### 修改保存位置

如需修改保存位置，编辑 `config.json` 中的 `output_dir` 字段。

## 依赖

- Python 3.7+
- requests
- beautifulsoup4

## 配置

- **VPN 路径**：`D:\Users\luzhe\AppData\Local\Programs\Clash for Windows\Clash for Windows.exe`
- **代理地址**：`http://127.0.0.1:7890`
- **频道地址**：https://www.youtube.com/@bestpartners/videos

## 注意事项

1. 确保 Clash for Windows 已正确安装
2. 确保代理端口 7890 可用
3. 首次运行可能需要安装依赖（requests、beautifulsoup4）

## 频道信息

- **频道名称**：最佳拍档 (Best Partners)
- **频道地址**：https://www.youtube.com/@bestpartners
- **内容类型**：人工智能、科技资讯、科普知识
