# 微信公众号后台接口 - API 参考

## 接口原理

wechat-article-exporter 使用的核心原理：

1. 用户扫码登录公众号后台 (mp.weixin.qq.com)
2. 利用后台"新建图文消息"页面的搜索功能
3. 调用内部接口搜索其他公众号
4. 获取文章列表和详情

## 核心接口

### 1. 搜索公众号

```
GET https://mp.weixin.qq.com/cgi-bin/searchbiz
```

参数：
- `action`: search_biz
- `token`: 登录后的 token
- `lang`: zh_CN
- `f`: json
- `ajax`: 1
- `query`: 搜索关键词
- `begin`: 起始位置
- `count`: 返回数量

响应：
```json
{
  "base_resp": {"ret": 0, "err_msg": ""},
  "list": [
    {
      "fakeid": "公众号内部ID",
      "nickname": "公众号名称",
      "alias": "微信号",
      "signature": "公众号介绍",
      "round_head_img": "头像URL"
    }
  ],
  "total": 100
}
```

### 2. 获取文章列表

```
GET https://mp.weixin.qq.com/cgi-bin/appmsg
```

参数：
- `action`: list_ex
- `token`: 登录后的 token
- `fakeid`: 公众号的 fakeid
- `query`: 搜索关键词（可选）
- `begin`: 起始位置
- `count`: 返回数量
- `type`: 9 (图文消息)

响应：
```json
{
  "base_resp": {"ret": 0, "err_msg": ""},
  "app_msg_list": [
    {
      "aid": "文章ID",
      "title": "文章标题",
      "digest": "摘要",
      "link": "文章链接",
      "create_time": 1705312800,
      "cover": "封面图URL",
      "copyright_stat": 11  // 11=原创
    }
  ],
  "total": 100
}
```

## 获取凭证步骤

### 1. 登录公众号后台

访问 https://mp.weixin.qq.com

### 2. 获取 Cookie

1. 按 F12 打开开发者工具
2. 切换到 Network（网络）标签
3. 刷新页面
4. 找到任意请求，复制 Request Headers 中的 Cookie

### 3. 获取 Token

Token 在 URL 中，例如：
```
https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=1234567890
```

token 值为 `1234567890`

## 注意事项

- Cookie 和 Token 会过期，通常几小时后需要重新获取
- 频繁请求可能触发反爬机制
- 建议添加适当的请求间隔
