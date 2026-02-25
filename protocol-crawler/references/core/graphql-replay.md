# GraphQL 复现与分页（深度版）

## 说明

GraphQL 是一种通用的 API 查询语言和运行时，并非 Instagram 专有。只有在抓包中出现
`/graphql`、`operationName`、`doc_id/query_hash` 等特征时才需要使用本章；否则可跳过。

## 目标

可靠复现 GraphQL 请求，明确 `doc_id/query_hash`、`variables`、分页字段与鉴权头。

## GraphQL 常见形态

1) **Persisted Query**

- `POST /graphql` 或 `/api/graphql`
- body 里不含 query 文本，依赖 `doc_id`/`query_hash`

2) **Plain Query**

- body 包含 `query` 与 `variables`

## 必采字段

- `doc_id` / `query_hash` / `operationName`
- `variables`（JSON）
- `x-csrftoken` / `x-fb-lsd` / `authorization`
- `x-ig-app-id`（若目标站点需要）
- `fb_api_req_friendly_name`（便于定位）

## 复现要点

- `variables` 必须严格匹配结构（字段名、层级、类型）。
- 对 `variables` 做最小化序列化（去空格，稳定顺序）：`json.dumps(..., separators=(",", ":"))`。
- Content-Type 与 body 格式对齐：`application/x-www-form-urlencoded` 或 `application/json`。
- 需要 `Origin/Referer` 的站点必须对齐来源。
- 若是 batch GraphQL，需拆分为独立请求或保持 batch 顺序。

## 分页协议

常见字段：

- `page_info.end_cursor`
- `page_info.has_next_page`
- `next` / `next_page` / `next_token`
- `after` / `before` / `first` / `count` / `limit`

确认流程：

1. 抓包两次分页请求，确认游标变化。
2. 判断终止条件：`has_next_page=false` 或 `end_cursor=null`。
3. 若无 `page_info`，检查响应是否被限权或 headers/cookies 缺失。

## 复现模板示例（x-www-form-urlencoded）

```
doc_id=123456
fb_api_req_friendly_name=SomeQuery
variables={"first":12,"after":"<cursor>","id":"<user_id>"}
```

## 错误排查

- **400/GraphQL errors**：变量结构或类型不匹配。
- **403/302**：触发挑战/登录，停止并提示人工处理。
- **缺字段/空列表**：检查 headers/cookies/权限。

## 变量类型校验

- 若服务端对类型敏感，确保 `int/bool/string` 与原请求一致。
- 数组字段要保证顺序与结构一致。
