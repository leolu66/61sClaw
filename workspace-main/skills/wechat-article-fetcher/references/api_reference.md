# 微信公众号文章获取 - API 参考

## 搜狗微信搜索接口

### 公众号搜索

```
GET https://weixin.sogou.com/weixin
```

参数：
- `type=1` - 公众号搜索
- `query` - 搜索关键词
- `page` - 页码

### 文章搜索

```
GET https://weixin.sogou.com/weixin
```

参数：
- `type=2` - 文章搜索
- `query` - 搜索关键词
- `page` - 页码

## 响应解析

### 公众号信息

```html
<li id="sogou_vr_...">
  <div class="txt-box">
    <p class="tit"><em>公众号名称</em></p>
    <p class="info">简介...</p>
    <label>微信号：xxx</label>
  </div>
</li>
```

### 文章信息

```html
<li id="sogou_vr_...">
  <div class="txt-box">
    <h3><a href="/link?url=...">文章标题</a></h3>
    <p class="txt-info">摘要...</p>
    <span class="s2"><script>document.write(timeConvert('时间戳'))</script></span>
    <a id="weixin_account">公众号名称</a>
  </div>
</li>
```

## 微信文章页面

### 文章详情页结构

- 标题：`.rich_media_title`
- 内容：`#js_content`
- 发布时间：页面JS变量 `s="YYYY-MM-DD"`

### 注意事项

1. 搜狗链接需要处理302跳转
2. 微信文章页面有反爬机制
3. 建议添加适当的请求间隔
