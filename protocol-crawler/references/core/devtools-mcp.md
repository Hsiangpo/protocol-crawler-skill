# Chrome DevTools MCP 接口分析（深度版）

## 目标

用 Chrome DevTools MCP 获取可复现的接口请求模板，明确鉴权、分页与fk特征，为协议层复现打基础。

## 基本原则

- 先在已登录会话里抓包，避免匿名流量与登录流量混到一起。
- 只抓 `fetch`/`xhr`/`document`/`graphql` 等关键请求，降低噪声。
- 捕获“触发条件 → 请求 → 响应 → 下一页请求”的完整链路。
- 明确动态字段（token/qm/时间戳/游标）与静态字段（固定 headers/固定参数）。

## 操作清单

### 1) 打开目标页面并稳定环境

- 保证是“已登录”浏览器上下文。
- 开启 `Preserve log`、关闭缓存（Disable cache）。
- 过滤资源类型：优先只看 `Fetch/XHR`。
- 若页面有懒加载，准备触发滚动/点击。
- 如页面有 Service Worker，考虑临时 bypass（避免缓存影响）。

### 2) 识别关键接口

- 在 Network 中寻找“列表页/详情页/分页请求”。
- 观察同一接口多次请求的差异：通常变化点是 `cursor/offset/page` 与 `token/ts`。
- 记录：
  - 接口域名与路径（Host + Path）
  - 方法（GET/POST）
  - Content-Type（JSON / x-www-form-urlencoded / multipart）
  - Headers（Authorization、X-CSRF、X-IG-App-ID、X-FB-LSD 等）
  - Cookies（哪些是必要的，是否与登录态绑定）
  - Initiator（触发来源：scroll/click/initial load）
  - Timing（是否存在排队/限流）

### 3) 复制并标准化请求模板

- 使用 “Copy as cURL” 或 “Copy request headers” 形成可复现模板。
- 将模板拆成结构化字段（见 `request-replay.md`）。
- 标记动态字段：
  - 时间戳、nonce、qm
  - 游标（cursor）/偏移（offset）/页号（page）
  - Session/CSRF Token（可能随会话更新）
- 若请求为 batch 或 multiplex，需拆分每个 operation。

### 4) GraphQL 特殊处理

- GraphQL 通常是 `POST /graphql` 或 `/api/graphql`。
- 重点提取：
  - `doc_id` / `query_hash` / `operationName`
  - `variables` JSON（注意 `after`/`first`/`count` 字段）
  - 头部 `x-fb-lsd` / `x-csrftoken` / `x-ig-app-id`
- 关注 `fb_api_req_friendly_name` 或类似字段用于定位 query。
- 记录分页字段：`end_cursor`、`has_next_page`、`page_info`。
- 详见：`graphql-replay.md`

### 5) 响应结构与分页确认

- 用两次连续请求对比响应：
  - 列表是否按分页参数变化
  - 是否存在 `page_info`/`next`/`cursor`
  - 响应字段是否缺失（需提高权限或补充 headers）
- 明确边界：
  - 空列表/`has_next_page=false` 的终止条件
  - 最大页/最大条数限制

### 6) fk与限流信号

- 关注响应码与重定向：
  - 302 → `/challenge` / `/login`：需要停止并提示人工处理
  - 429：限流，必须保守退避
  - 403/401：鉴权或 session 失效
- 详见：`error-checkpoint.md`

## 采样策略（降低误判）

- 至少捕获 2–3 次分页请求，验证 cursor/offset 的递进规律。
- 对比响应里的 `page_info` 与 UI 变化，避免抓到非目标接口。
- 若接口返回压缩内容，确保工具能显示解压后的正文。

## 排错提示

- 响应无数据但无报错：通常是 headers/cookies 缺失。
- 同接口多次请求返回不同 schema：可能是 A/B 试验或权限差异。
- 抓不到接口：触发方式可能是 scroll 触底或点击某个 tab。

## 交付物（对齐文档）

输出一份接口“复现说明”：

- **Endpoint**：Host + Path + Method
- **Headers**：必需/可选 + 动态字段说明
- **Cookies**：必需与否
- **Body/Query**：结构化模板 + 动态字段
- **Pagination**：字段名与终止条件
- **Response Schema**：关键字段路径
- **Rate Limit**：已有信号、默认策略
