# 请求模板与复现指南

> 历史版本已合并：request-template + rest-json-replay

## 目标

将抓包结果整理成结构化模板，明确"固定字段 vs 动态字段"，为协议层复现提供稳定输入。

## 请求模板结构（建议）

```yaml
endpoint:
  method: POST
  url: https://api.example.com/v1/items
headers:
  static:
    accept: application/json
    content-type: application/x-www-form-urlencoded
  dynamic:
    authorization: Bearer <token>
    x-csrf-token: <csrf>
cookies:
  required:
    - sessionid
    - csrftoken
params:
  static:
    locale: en_US
  dynamic:
    cursor: <end_cursor>
body:
  static:
    page_size: 24
  dynamic:
    timestamp: <ts>
    qm: <qm>
pagination:
  cursor_field: end_cursor
  has_next_field: has_next_page
```

## 动态字段分类

| 类别       | 示例                                          | 来源          |
| ---------- | --------------------------------------------- | ------------- |
| **会话级** | sessionid, csrftoken, x-fb-lsd, authorization | Cookie/Header |
| **请求级** | timestamp, nonce, qm                          | JS计算        |
| **分页级** | cursor, page, offset                          | 响应提取      |

## 复现清单

- **Endpoint**：method + url + path 参数是否一致
- **Headers**：鉴权、CSRF、App-ID、Accept/Content-Type
- **Cookies**：登录态是否必须，domain/path 是否匹配
- **Body/Query**：字段结构、类型、序列化方式
- **排序与过滤**：是否有隐式默认值（如 sort=latest）
- **压缩/编码**：gzip/br、URL 编码规则

## 序列化一致性

- JSON 序列化：稳定字段顺序与紧凑格式  
  `json.dumps(obj, separators=(",", ":"), ensure_ascii=False)`
- 数字/布尔/空值类型必须一致
- 字符编码与 URL 编码需与浏览器一致

## 鉴权复现清单

- **Cookie 依赖**：确认是否必须带 `sessionid/csrftoken`
- **Header 依赖**：记录 `Authorization`、`X-CSRF-Token`、`X-IG-App-ID` 等
- **Origin/Referer**：部分站点强校验来源，需对齐页面来源
- **qm算法**：明确输入字段顺序、拼接方式、Hash/加密算法、盐值来源

## qm复现步骤

1. 抓取请求前后的 JS/参数计算逻辑（注意输入字段顺序）
2. 找到qm函数的输入集合（请求路径、body、时间戳、secret）
3. 在协议层复刻相同拼接与编码（URL 编码、JSON 序列化顺序）
4. 校验qm一致性（对比浏览器请求中的qm值）

## 复现验证步骤

1. 抓包两次请求，标出动态字段差异
2. 只保留"最小必需字段"
3. 用模板构造请求（优先通过 `httpx/requests`）
4. 比对响应结构是否一致（字段路径与数量一致）
5. 若数据缺失：补齐 headers/cookies，再检查序列化/qm
6. 记录可复用的"最小请求集"（必需字段）

## 常见踩坑

- Content-Type 不一致导致服务端解析失败
- Referer/Origin 缺失导致 403
- Cookies 未携带导致空数据或 401
- URL 编码规则不同导致qm失效

## 模板落地建议

- 保存为可复用结构（JSON/YAML），并标注动态字段来源
- 对每个字段写"来源说明"：cookie/header/body/query/JS 计算
- 对可选字段做开关，便于最小化请求

---

## 登录态管理

### 关键概念

| 类型                     | 说明                     |
| ------------------------ | ------------------------ |
| **Session Cookie**       | 决定当前会话是否已登录   |
| **CSRF Token**           | 部分站点要求在请求中携带 |
| **Refresh/Access Token** | 短期访问令牌与刷新令牌   |

### 失效信号

- 302 跳转到 `/login` 或 `/challenge`
- 401/403 响应
- 返回结构缺少登录态字段

### 处理流程

1. **请求前**：加载最新 `storage_state/cookies`
2. **请求中**：遇到失效信号立即停止并提示人工处理
3. **人工处理后**：重新保存 `storage_state`，再继续协议请求

### 注意事项

- 不要用自动化做登录验证 pj
- 保留"手动登录 → 保存状态 → 复用"的稳定链路
- 任何异常都要落日志，便于定位失效原因
