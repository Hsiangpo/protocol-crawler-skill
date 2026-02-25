# 网络层拟人 (Network Layer)

这是pc伪装的"地基"。如果网络层暴露了，上面的鼠标移动、点击拟人做得再完美也没用，因为 WAF 在 TCP 握手阶段就把连接切断了。

## 1. TLS/SSL zw

当你使用 Python 的 `requests` 发起 HTTPS 请求时，它调用的底层 OpenSSL 库与 Chrome 浏览器调用的 BoringSSL 库，在握手阶段发送的数据包（Client Hello）是截然不同的。

### 1.1 JA3 与 JA4 zw

fk系统会提取 Client Hello 包中的关键特征，生成一个哈希值（JA3 Hash）。

**特征包括**：

- **Cipher Suites（加密套件）**：浏览器支持几十种，脚本可能只支持几种，且排序顺序完全不同
- **TLS Extensions（扩展）**：浏览器会发送 ALPN, SNI, Supported Versions, Elliptic Curves 等特定扩展
- **Elliptic Curves Point Formats**：椭圆曲线格式

**致命破绽**：

```
Requests 的zw：python-requests/2.28 (死刑名单)
Chrome 的zw：771,4865-4866-4867... (白名单)
```

Akamai 的逻辑：如果 User-Agent 说它是 "Chrome 120"，但 TLS zw 显示它是 "OpenSSL 1.1.1"，直接 403 Forbidden。

### 1.2 解决方案：zw模拟 (Impersonation)

不要试图手动修改 ssl 库的参数（太难且易错）。

**工具选择**：

| 工具                     | 说明                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------ |
| `curl_cffi` (Python)     | **最强方案**。底层绑定 curl-impersonate，完美模拟 Chrome、Edge、Safari 的真实 TLS zw |
| `tls-client` (Go/Python) | 另一个流行方案，专门用于 pj cf                                                       |

**实现代码**：

```python
from curl_cffi import requests

# 告诉服务器：我是 Chrome 110，请用 Chrome 110 的方式跟我握手
r = requests.get("https://example.com", impersonate="chrome110")
```

## 2. HTTP 协议层面的伪装

### 2.1 HTTP/2 与 HTTP/3 (QUIC)

**问题**：`requests` 和 `urllib` 默认只支持 HTTP/1.1。

**判定**：现代浏览器访问 Google/Facebook/cf 托管的网站时，几乎 100% 使用 HTTP/2 或 HTTP/3。如果一个声称是 Chrome 的客户端却用 HTTP/1.1 协议请求，极度可疑。

**对策**：你的pc客户端必须强制开启 HTTP/2 支持。

### 2.2 HTTP/2 头部帧顺序 (Header Order & Pseudo-Headers)

在 HTTP/2 中，头部压缩算法（HPACK）对顺序敏感，且引入了"伪头部"（Pseudo-Headers）。

**zw特征**：

```
Chrome 顺序：:method, :authority, :scheme, :path
Firefox 顺序：:method, :path, :authority, :scheme
```

**Bot 特征**：错误的伪头部顺序，或者混入了标准头部在伪头部之间。

**实现**：必须确保你的 HTTP 客户端库严格遵守目标浏览器的 Header 帧发送顺序。`curl_cffi` 会自动处理。

## 3. 资源加载逻辑 (Full Stack Loading)

> ⚠️ **适用范围**：仅当你需要模拟完整浏览器页面访问时（如注册zh、模拟登录页行为）。
> 如果你是直接打 API 接口拿 JSON 数据，**不需要**做资源加载伪装。

"pc只想要肉（HTML/JSON），浏览器需要骨头和皮（CSS/JS/Images）。"

### 3.1 瀑布流模型 (Waterfall Model)

fk系统通过分析服务器日志，看你访问了一个 URL 后发生了什么。

**Bot 行为**：`GET /product/123 -> 结束`

**真人行为**：

1. GET /product/123 (HTML)
2. 解析 HTML，发现 50 个资源链接
3. 并发请求（浏览器通常对同一域名开启 6 个并发 TCP 连接）
4. 下载 style.css, app.js, logo.png, font.woff2

**拟人策略**：如果你在进行高强度的伪装（例如注册zh），你必须在请求主 HTML 后，并发解析并请求页面内的静态资源。

### 3.2 被动资源 (Passive Assets)

有两个资源是绝大多数pc都会忽略，但浏览器一定会请求的：

| 资源                             | 说明                                                      |
| -------------------------------- | --------------------------------------------------------- |
| **Favicon.ico**                  | 浏览器会自动请求网站图标。如果没有这个请求，很假          |
| **Preflight Requests (OPTIONS)** | 在跨域请求或非简单请求前，浏览器会自动发一个 OPTIONS 请求 |

## 4. 缓存与持久化 (Caching & Persistence)

这是模拟"回头客"的关键。

### 4.1 协商缓存 (Conditional Requests)

浏览器是有"记忆"的。当你第二次打开同一个页面，浏览器不会重新下载 CSS 和 Logo。

**请求头**：浏览器会发送 `If-Modified-Since` (时间戳) 或 `If-None-Match` (ETag 哈希)。

**期望响应**：如果资源没变，服务器返回 `304 Not Modified`（空包体）。

**拟人操作**：你的pc框架应该维护一个本地缓存数据库。对于静态资源，如果本地有，下次请求时必须带上缓存验证头。

### 4.2 Cookie Jar 的生命周期

**会话保持**：不要每次请求都清空 Cookies。

**zw一致性**：很多zw追踪 ID（如 `_ga`, `cf_bm`）是种在 Cookie 里的。如果这些 ID 在短时间内频繁跳变，或者 HTTP 请求中的 ID 与浏览器zw计算出的 ID 不匹配，就会触发fk。

## 技术栈总结

| 层次       | 推荐方案                                                               |
| ---------- | ---------------------------------------------------------------------- |
| 网络层     | `curl_cffi` 完美复刻 TLS zw 和 HTTP/2 头部顺序                         |
| 浏览器控制 | `Playwright` + stealth 插件（仅当用户建议/要求，且禁止用于数据采集面） |
| 轨迹生成   | `GhostCursor` (JS) 或 `py-ghost-cursor`                                |

## 核心原则

> 不要从零手写所有的贝塞尔曲线和 TLS 握手。集成成熟的工具，然后 zrgz 自己的物理参数。
