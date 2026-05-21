DESIGN.md：又一个你必须知道的Markdown文件





















![cover_image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/rY5icXvTTrJ9QX7qbwI1uysEo99WbNy5tr96rUicGDaLUl8ANhBy0LeHMQnqvUAUuH5wgWcKOibD6p9qSFnmribDic3Nm6WDPRRrMYhaibTYiaZQSg/0?wx_fmt=jpeg)

# DESIGN.md：又一个你必须知道的Markdown文件

原创

winkrun
winkrun

[AI工程化](javascript:void(0);) 

*2026年4月27日 11:02*
*北京*

![]()

在小说阅读器读本章

去阅读

![]()

在小说阅读器中沉浸阅读

Google Stitch最近推出了一个简单的方法：DESIGN.md。一个Markdown文件，放在项目根目录，Claude、Cursor、Copilot这些AI助手都能直接读取。

## DESIGN.md是什么？

DESIGN.md是Google Stitch引入的新概念，一个纯文本的设计系统文档。AI助手读取后能生成一致的UI。

![图片](https://mmbiz.qpic.cn/mmbiz_png/rY5icXvTTrJ9nvXPDQRN01icKNEzeYNQtOGucgXCkyzN6gNt6Jaav3jxp9UDK1KwNTkmOPCictzU5OHUkNqvndWZQDqm4mpb1B0Q6tTalW7D38/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

这个文件里面有颜色调色板、字体规则、间距尺度、按钮样式、网格系统等基础设计规范。不需要Figma导出，也不需要JSON配置文件。

DESIGN.md文件遵循Stitch格式，包含9个核心部分：

1. **视觉主题和氛围** - 情绪、密度、设计哲学
2. **色彩调色板和角色** - 语义名称+十六进制值+功能角色
3. **排版规则** - 字体族、完整层级表
4. **组件样式** - 按钮、卡片、输入框、导航及其状态
5. **布局原则** - 间距尺度、网格、留白哲学
6. **深度和层次** - 阴影系统、表面层次
7. **该做和不该做** - 设计护栏和反模式
8. **响应式行为** - 断点、触摸目标、折叠策略
9. **AI助手提示指南** - 快速色彩参考、即用提示词

Markdown是大模型最擅长读取的格式，所以AI助手能直接理解你的UI应该长什么样。

```
---  
name: DevFocus Dark  
colors:  
  primary: "#2665fd"  
  secondary: "#475569"  
  surface: "#0b1326"  
  on-surface: "#dae2fd"  
  error: "#ffb4ab"  
typography:  
  body-md:  
    fontFamily: Inter  
    fontSize: 16px  
    fontWeight: 400  
rounded:  
  md: 8px  
---  
  
# Design System  
  
## Overview  
A focused, minimal dark interface for a developer productivity tool.  
Clean lines, low visual noise, high information density.  
  
## Colors  
- **Primary** (#2665fd): CTAs, active states, key interactive elements  
- **Secondary** (#475569): Supporting UI, chips, secondary actions  
- **Surface** (#0b1326): Page backgrounds  
- **On-surface** (#dae2fd): Primary text on dark backgrounds  
- **Error** (#ffb4ab): Validation errors, destructive actions  
  
## Typography  
- **Headlines**: Inter, semi-bold  
- **Body**: Inter, regular, 14–16px  
- **Labels**: Inter, medium, 12px, uppercase for section headers  
  
## Components  
- **Buttons**: Rounded (8px), primary uses brand blue fill  
- **Inputs**: 1px border, subtle surface-variant background  
- **Cards**: No elevation, relies on border and background contrast  
  
## Do's and Don'ts  
- Do use the primary color sparingly, only for the most important action  
- Don't mix rounded and sharp corners in the same view  
- Do maintain 4:1 contrast ratio for all text
```

## 现成的设计系统库

Awesome DESIGN.md 项目里已经有54个现成的设计系统，都是从真实产品中提取出来的。

![图片](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

Stripe、Vercel、Linear、Notion、Claude、Cursor、Warp等知名产品的设计都在里面。每个设计系统都包含DESIGN.md文件和两个预览文件，一个亮色主题一个暗色主题，方便查看实际效果。

## 一个快速生成DESIGN.md的工具

![]()

已关注

关注

重播    分享     赞

关闭

**观看更多**

更多

*退出全屏*

*切换到竖屏全屏**退出全屏*

AI工程化已关注

分享视频

，时长00:24

0/0

00:00/00:24

切换到横屏模式

继续播放

进度条，百分之0

[播放](javascript:;)

00:00

/

00:24

00:24

[倍速](javascript:;)

*全屏*

倍速播放中

[0.5倍](javascript:;)  [0.75倍](javascript:;)  [1.0倍](javascript:;)  [1.5倍](javascript:;)  [2.0倍](javascript:;)

[超清](javascript:;)  [流畅](javascript:;)

[![ 您的浏览器不支持 video 标签 ](https://mp.weixin.qq.com/s/6oYv51vp7Qg7DyK87Jdr0w?wxfrom=16)](https://mpvideo.qpic.cn/0b2esedgoaagteakiapiqzuvneodm6iqmzya.f10002.mp4?dis_k=308b1ff78a6012cbb97050c5fc96d7c7&dis_t=1778303012&play_scene=10120&auth_info=Tr6a5uglSmhRy+Kt6QEnb2hsMx9pMU9mHlE/PUdYUydxfw01RwhRJSZwYUFHaypPfGY=&auth_key=2598845f9fb1b5ee66156945cffa138c&vid=wxv_4490638385207312386&format_id=10002&support_redirect=0&mmversion=false)

继续观看

DESIGN.md：又一个你必须知道的Markdown文件

观看更多

转载

,

DESIGN.md：又一个你必须知道的Markdown文件

AI工程化已关注

分享点赞在看

已同步到看一看[写下你的评论](javascript:;)

 

[视频详情](javascript:;)

HyperDesign工具可以自动生成DESIGN.md文件。把Anthropic官网扔进去，16秒输出颜色、字体、间距规范，9秒生成结构化的DESIGN.md文件。

它不是简单的取色器，而是会分析设计语言。比如判断Anthropic的风格是克制的、学术的、借鉴印刷传统的。每个字号对应的行高字重都列得清清楚楚。

工具是开源的，以前大公司花几百万做的设计系统，现在25秒就能复制。

## 实际使用效果

一位开发者分享："把DESIGN.md放在Cursor项目根目录，Claude立刻开始尊重我的品牌token。终于，AI助手不再自己发明Tailwind样式了。"

另一位用户说："这对小团队和个人项目太重要了。设计一致性过去需要全职设计师或没人读的品牌指南。现在一个Markdown文件在仓库里，每个接触你代码的AI工具都知道你的品牌长什么样。"

DESIGN.md文件一般在几KB到20KB之间，可以直接喂给Claude等大模型。这个方法的优点是把设计当作大模型能原生解析的文本格式，而不是强迫AI去解释Figma导出文件。

Awesome DESIGN.md：https://github.com/VoltAgent/awesome-design-md

hyperbrowser：https://github.com/hyperbrowserai/hyperbrowser-app-examples

关注公众号回复“进群”入群讨论。

预览时标签不可点

![赞赏二维码]()**微信扫一扫赞赏作者**[喜欢作者](javascript:;)

关闭

**[0人付费](javascript:;)**

更多

正在加载...

正在加载...

关闭

更多

系统错误，请稍后重试

名称已清空

![赞赏二维码]()**微信扫一扫赞赏作者**

喜欢作者[其它金额](javascript:;)

赞赏后展示我的头像

作品

暂无作品

喜欢作者

其它金额

¥

最低赞赏 ¥0

确定

返回

**其它金额**

更多

赞赏金额

¥

最低赞赏 ¥0

1

2

3

4

5

6

7

8

9

0

.

领域技术 · 目录

#领域技术

上一篇Anthropic发布多Agent协作模式指南：5种架构与适用场景下一篇Tank OS：红帽首席工程师把OpenClaw打包成可启动的Linux设备

关闭

更多

#

搜索「」网络结果

关闭

**调整当前正文文字大小**

更多

100%

​

留言

暂无留言

1条留言

已无更多数据

[发消息](javascript:;)

写留言:

![]()

微信扫一扫  
关注该公众号

继续滑动看下一个

轻触阅读原文

![](http://mmbiz.qpic.cn/mmbiz_png/aaN2xdFqa4HHZgg9abQ55cSWZu23JrNMHD5SBdsYLURCtEcAfhyxNzG4boYKKWTUibhOx8wbupSOzFD1Dd0PFzw/0?wx_fmt=png)

AI工程化

向上滑动看下一个

当前内容可能存在未经审核的第三方商业营销信息，请确认是否继续访问。

[继续访问](javascript:)[取消](javascript:)

[微信公众平台广告规范指引](javacript:;)

[知道了](javascript:;)



![]()
微信扫一扫  
使用小程序

[取消](javascript:void(0);)
[允许](javascript:void(0);)

[取消](javascript:void(0);)
[允许](javascript:void(0);)

[取消](javascript:void(0);)
[允许](javascript:void(0);)

×
分析

![跳转二维码]()

![作者头像](http://mmbiz.qpic.cn/mmbiz_png/aaN2xdFqa4HHZgg9abQ55cSWZu23JrNMHD5SBdsYLURCtEcAfhyxNzG4boYKKWTUibhOx8wbupSOzFD1Dd0PFzw/0?wx_fmt=png)

微信扫一扫可打开此内容，  
使用完整服务

![](https://mmbiz.qpic.cn/mmbiz_png/aaN2xdFqa4HHZgg9abQ55cSWZu23JrNMHD5SBdsYLURCtEcAfhyxNzG4boYKKWTUibhOx8wbupSOzFD1Dd0PFzw/300?wx_fmt=png&wxfrom=18)

AI工程化

已关注

赞

分享

推荐

写留言

：
，
，
，
，
，
，
，
，
，
，
，
，
。
 
视频
小程序
赞
，轻点两下取消赞
在看
，轻点两下取消在看
分享
留言
收藏
听过
















可在「公众号 > 右上角  > 划线」找到划线过的内容

![划线引导图](https://res.wx.qq.com/op_res/opqv3ix6k9E4e64ZzO7uIqE3ZblwIojfmt7u70m59yS1ylFK-hTu6Ra8V_LaWQJ1P4OlUJPdXLfVBtrm3TwRrw)

我知道了

,

,

选择留言身份

该账号因违规无法跳转

**留言**

暂无留言

1条留言

已无更多数据

[发消息](javascript:;)

写留言:

关闭

更多

关闭

**领域技术**

详情

更多

正在加载

关闭

## 确认提交投诉

你可以补充投诉原因（选填）

确定