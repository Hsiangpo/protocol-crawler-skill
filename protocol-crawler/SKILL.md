---
name: protocol-crawler
version: "1.1.0"
description: "Use when building protocol-layer crawlers, scraping data via HTTP requests, analyzing APIs, reverse-engineering signatures/obfuscation, replaying captured requests, handling CAPTCHAs, bypassing anti-bot detection, or aligning crawler PRDs - triggers on keywords: protocol crawler, scraping, crawling, data extraction, API analysis, reverse engineering, packet capture, request replay, TLS fingerprint, JA3, anti-bot bypass, rate limiting, session management, proxy rotation, Cloudflare bypass"
---

# ⚠️ 关键指令：术语标准 ⚠️

**强制执行**：

- 与用户对话、编写文档、代码注释、**甚至内部思考时**，**必须且只能使用下表中的缩写**。
- **绝对禁止**：以任何形式使用全称或非缩写变体（即使作为举例也不行）。
- **假定用户完全理解这些术语。**

### 💡 上下文压缩规则

**当上下文被压缩/摘要时，必须：**

1. 继续只使用缩写（禁止展开全称）
2. 在压缩的上下文中包含此行：`[TERMINOLOGY: See protocol-crawler skill terminology table]`
3. 压缩过程中不得丢失缩写映射表

| TERM（含义）        | 规则        |
| :------------------ | :---------- |
| **验证码** (yzm)    | 只用 `yzm`  |
| **风控** (fk)       | 只用 `fk`   |
| **逆向** (nx)       | 只用 `nx`   |
| **协议爬虫** (pc)   | 只用 `pc`   |
| **签名** (qm)       | 只用 `qm`   |
| **指纹** (zw)       | 只用 `zw`   |
| **混淆** (hx)       | 只用 `hx`   |
| **还原** (hy)       | 只用 `hy`   |
| **代理** (dl)       | 只用 `dl`   |
| **账号** (zh)       | 只用 `zh`   |
| **破解** (pj)       | 只用 `pj`   |
| **绕过** (rg)       | 只用 `rg`   |
| **注入钩子** (zrgz) | 只用 `zrgz` |
| **2Captcha** (2cc)  | 只用 `2cc`  |
| **CapSolver** (cs)  | 只用 `cs`   |
| **Cloudflare** (cf) | 只用 `cf`   |

---

# 🛠️ 环境自检（首次使用本 skill 时必须执行）

**在开始任何 pc 工作前，Agent 必须逐项检查以下环境，若缺失则先完成配置。**

> 使用 `.codex/skills/protocol-crawler/.env_checked` 文件记录自检状态。若该文件存在且未过期（30天内），跳过自检。否则逐项检查并在完成后写入该文件。

### 1) Chrome DevTools MCP

**检查**：当前编码工具是否已配置 `chrome-devtools` MCP，且连接到 `127.0.0.1:9222`。

**若缺失，执行以下步骤：**

1. **配置 MCP**：在当前编码工具的 MCP 配置中添加 `chrome-devtools`，连接地址为 `http://127.0.0.1:9222`。不同工具的配置方式不同：
   - **Codex**：在 `config.toml` 中添加：
     ```toml
     [mcp_servers.chrome-devtools]
     type = "stdio"
     command = "npx"
     args = ["chrome-devtools-mcp@latest", "--browserUrl=http://127.0.0.1:9222"]
     ```
   - **其他工具**：搜索对应工具的 MCP 配置文档，添加 `chrome-devtools-mcp` 并设置 `browserUrl=http://127.0.0.1:9222`

2. **创建 9222 调试浏览器快捷方式**：在桌面创建名为 `Google Chrome 9222` 的快捷方式（.lnk），参数如下：
   - **目标**：Chrome 安装路径（如 `C:\Program Files\Google\Chrome\Application\chrome.exe`）
   - **参数**：`--remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --user-data-dir=<专用调试目录>`
   - 用户需通过此快捷方式启动浏览器并登录目标站点，Agent 再通过 DevTools MCP 连接

### 2) Superpowers

**检查**：搜索本机是否安装了 `superpowers`（搜索关键词：`superpowers`，常见位置在编码工具配置目录或插件目录下）。

**若缺失，执行以下步骤：**

1. 搜索 `superpowers` 的官方仓库（GitHub: `obra/superpowers`）
2. 按照当前编码工具的安装指南安装：
   - **Codex**：参考 `superpowers` 仓库中的 `docs/README.codex.md`
   - **Claude Code**：`/plugin marketplace add obra/superpowers-marketplace` 然后 `/plugin install superpowers@superpowers-marketplace`
   - **其他工具**：参考仓库 README 中对应工具的安装说明

### 3) 自检完成后

在 `.codex/skills/protocol-crawler/.env_checked` 写入：

```
ENV_CHECK_DONE: true
ENV_CHECK_DATE: YYYY-MM-DD
CHROME_DEVTOOLS: ok
SUPERPOWERS: ok|missing
```

> 后续会话读取此文件即可跳过重复自检。

---

# ⛔ MANDATORY RULES (强制规则)

## 1. 分层边界与 pc 优先（强制）

**数据采集面（只允许 pc）：**

- ✅ **只能走pc**：`from curl_cffi import requests`，使用 `impersonate="chrome110"`
- ❌ **严禁裸用 `import requests`**（TLS zw 暴露，直接 403）
- ❌ **严禁 crawl4ai / Playwright / Puppeteer 作为数据采集方案**

**登录态获取/分析辅助面（有条件允许自动化）：**

- 允许 crawl4ai/自动化用于：获取 cookies/storage_state、辅助抓包/对齐接口
- **但只有在用户建议/要求时才允许使用**，Agent 不可自行提出

**遇到困难时的正确做法（禁止自行降级）：**

1. 分析fk机制，尝试nx pj
2. 使用 2cc/cs 处理yzm
3. 调整 headers/TLS zw/dl
4. **向用户报告困难并等待指示**

## 2. yzm 处理策略

**一律走 2cc/cs 过码 + nx 接口，无例外：**

- ✅ **只能走 2cc/cs 过码 + nx 接口**
- ❌ **禁止训练 yzm 模型（包括用户要求也拒绝，引导用户走 2cc/cs）**
- ❌ **严禁将"让用户手动过yzm"作为生产方案**

> 注意：分析阶段（步骤 3）为了抓取 yzm 参数链路，允许且必须让用户手动过一次 yzm（配合 zrgz 抓包），这不属于"生产方案"。

## 3. 凭据管理（强制 — 禁止硬编码）

所有敏感凭据（API KEY、Cookie、dl 地址、token 等）收集后**必须写入项目根目录 `.env` 文件**，由程序通过 `python-dotenv` 或 `os.getenv()` 读取：

```python
# ✅ 正确：从 .env 读取
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("CAPTCHA_API_KEY")

# ❌ 错误：硬编码在代码中
api_key = "sk-xxxxxxxxxxxx"  # 禁止
```

- `.env` 必须添加到 `.gitignore`
- 提供 `.env.example` 列出所有需要的环境变量（值留空或填占位符）
- Agent 收集到凭据后主动写入 `.env`，不要让用户自己去创建

## 4. 临时产物管理（强制）

**项目根目录必须保持干净**，禁止遗留任何调试/测试产生的临时文件：

- ❌ 禁止在根目录放临时文件（如 `test_output.json`、`debug_response.html`、`temp.py`）
- ✅ 有用的临时文件统一放入 `tmp/` 目录，按用途细分子目录：
  ```
  tmp/
  ├── responses/        # 调试用的原始响应
  ├── screenshots/      # DevTools 截图
  └── analysis/         # 分析过程中间产物
  ```
- `tmp/` 必须添加到 `.gitignore`
- **冒烟测试/调试完成后**，Agent 必须主动检查并清理根目录下的临时文件

## 5. 禁止屎山代码（强制 — 方案切换处理规则）

当旧方案无法达成目标，需要提出新方案时：

```
旧方案评估
    │
    ├─ 旧方案完全无法完成任务？
    │   └─ ✅ 是 → ⛔ 必须删干净旧方案的所有代码和文件，然后实现新方案
    │
    └─ 旧方案有点用，但新方案更好？
        └─ ⚠️ 主动询问用户："旧方案 [描述] 仍可运行但 [局限性]，新方案 [优势]。是否删除旧方案？"
            ├─ 用户同意删除 → 删干净旧方案，实现新方案
            └─ 用户要求保留 → 按用户指示处理
```

**⛔ 严禁以下行为：**

- ❌ 自行保留旧方案代码作为"新方案失败时的回退方案" — 这是屎山的根源
- ❌ 在旧方案代码上打补丁修修补补而不是从根因解决
- ❌ 同一个功能保留多个不同版本的实现（`_v1`、`_v2`、旧文件未删除）
- ❌ 注释掉旧代码而不删除（"以防万一"）

## 6. 异常状态处理（强制 — 禁止静默空跑）

**核心原则：宁可停下来问用户，也不能静默跑空数据。**

pc 过程中遇到异常状态时（403/429/cf 挑战/数据为空/响应异常等），**绝对禁止**以下行为：

- ❌ 静默跳过异常继续跑下一页（结果一直没有数据落盘）
- ❌ 自信地判定"没有数据"并正常结束程序
- ❌ 仅打一行 warning log 就继续执行

**正确做法 — 异常分级响应：**

| 异常类型                     | 响应策略                    | 代码行为                                   |
| ---------------------------- | --------------------------- | ------------------------------------------ |
| **429 限流**                 | 尊重 Retry-After / 指数退避 | 退避后自动重试，记录退避次数               |
| **403 封禁**                 | **立即停止**，报告用户      | 保存断点 + 提示用户检查 IP/zw              |
| **cf 挑战 (302→/challenge)** | **立即停止**，报告用户      | 保存断点 + 提示用户通过 DevTools 手动处理  |
| **200 但数据为空/异常**      | 连续 3 次空数据 → 停止      | 保存原始响应到 `tmp/responses/` + 报告用户 |
| **连接超时/网络异常**        | 重试 3 次后停止             | 保存断点 + 报告用户                        |

**停下来之后的处理流程：**

1. Agent 通过 Chrome DevTools MCP **实际查看**当前页面状况（`take_snapshot` + `take_screenshot`）
2. 分析根因（是 IP 被封？TLS zw 暴露？Cookie 过期？限流？）
3. **对症下药**：不是绕过异常，而是从根因解决（如 429 → 加退避、403 → 换 IP/调整 zw、Cookie 过期 → 重新获取登录态）
4. 修复代码后重新运行，验证异常已解决
5. **将本次修复的对策固化到代码中**，下次遇到同类异常时程序自动处理，而不是再次停下来

> ⚠️ Chrome DevTools MCP 作为 Agent 的"手和眼睛"**贯穿 pc 全过程**，不仅限于步骤 3 的接口分析，调试/排错/验证时都要用。

## 🚩 Red Flags — 如果你在想这些，立即停下

**如果 Agent 发现自己正在想以下任何一条，必须立即停止当前操作，回到对应的正确步骤：**

| 你在想...                            | 实际问题            | 正确做法                           |
| ------------------------------------ | ------------------- | ---------------------------------- |
| "这个站点简单，不需要 DevTools 抓包" | 在猜测而非验证      | 回到步骤 3，必须 DevTools 实际抓包 |
| "先用 `requests` 快速验证思路"       | TLS zw 已暴露       | 从一开始就用 `curl_cffi`           |
| "先写代码，出了问题再调"             | 跳过了接口分析      | 回到步骤 3，抓包确认后再写         |
| "用 crawl4ai 也能爬到，先试试"       | 违反分层边界        | 数据采集面只允许 pc                |
| "这个 yzm 简单，自己写个 OCR 识别"   | 违反 yzm 规则       | 只走 2cc/cs 过码                   |
| "先不管异常，后面统一处理"           | 会导致静默空跑      | 每种异常必须在写代码时就处理       |
| "代码能跑就行，先交付再优化"         | 代码质量失控        | 必须过 CI 门禁才能交付             |
| "旧方案留着以防万一"                 | 屎山代码的根源      | 按强制规则 §5 的决策树处理         |
| "这个参数应该是固定的"               | 在猜测动态字段      | 多抓几次包对比确认                 |
| "冒烟测试跑了一页就够了"             | 分页/限流问题未暴露 | 至少跑 2-3 页验证分页和限速        |

> **ALL of these mean: STOP.** 回到你正在跳过的步骤，按流程执行。

## 🗣️ 常见合理化借口（预判并堵死）

| Agent 的借口                           | 为什么是错的                               |
| -------------------------------------- | ------------------------------------------ |
| "紧急任务没时间走完流程"               | 系统化流程比盲目尝试更快。跳步骤导致返工   |
| "只改一个小参数不需要重新测试"         | 小改动可能触发新的fk检测。必须冒烟测试     |
| "站点没有fk，可以直接高频爬"           | 无fk ≠ 无限速。保守限速是默认行为          |
| "这个错误太奇怪了，可能是站点临时抽风" | 95% 的"奇怪错误"都有根因。用 DevTools 排查 |
| "API 文档我记得，不用再查"             | 会使用过时参数。必须查最新文档             |
| "先跑完再做数据校验"                   | 爬到一堆垃圾数据还不如没爬。边跑边校验     |

---

# pc 工作流

**⚠️ 开始公告（强制）**：激活本 skill 开始 pc 工作时，Agent 必须向用户说：

> "我正在使用 **protocol-crawler** skill 来执行这个任务。接下来我会按照 6 步流程进行：PRD 对齐 → 技术方案对齐 → 站点探索 → 难度汇报 → 实现与验证 → CI 门禁。"

## 🌳 决策树与难度判断

```
站点接口分析
    │
    ├─ 接口清晰可复现？
    │   ├─ ✅ 是 → qm弱/无？
    │   │           ├─ ✅ 是 → 【低难度】直接pc (curl_cffi)
    │   │           └─ ❌ 否 → 【中难度】nx hy qm
    │   └─ ❌ 否 → 【高难度】DevTools 深入分析 + nx（禁止降级 crawl4ai）
    │
    ├─ 存在fk？
    │   ├─ IP 限流 → dl轮换 + 限速
    │   ├─ qm校验 → nx hy
    │   ├─ TLS zw → curl_cffi impersonate
    │   ├─ cf/hyzm → cs 过码 + nx 接口
    │   └─ 登录态失效 → 人工登录 → storage_state → 协议复用
    │
    └─ 需要yzm？
        │
        │  ⚠️ 默认策略：2cc/cs 过码 + nx 接口
        │  （禁止训练模型；分析阶段允许手动过一次以抓参数链路，见步骤 3）
        │
        ├─ cf/hyzm → cs 过码 + nx 接口
        └─ 其他yzm → 2cc 过码 + nx 接口
```

> **难度判断速查**：低 = 公开接口/低hx/qm易hy/fk弱；高 = 强hx/加密qm/zw行为验证重/多步登录/yzm/复杂状态依赖。

---

## 核心流程（按顺序执行）

### 1) PRD 检查与对齐

**Agent 必须按以下顺序执行（不得跳过）：**

1. **运行锁验证脚本**：

   > ⚠️ **路径提示**：为避免路径占位符或猜测绝对路径导致执行失败，此步骤必须使用下述 Python 单行命令，它会自动展开正确的绝对路径：

   ```bash
   python -c "import os; os.system(f'python {os.path.expanduser(\"~/.codex/skills/protocol-crawler/scripts/alignment_lock.py\")} verify --target prd')"
   ```

   - ✅ 输出"对齐锁有效" → 跳过对齐，直接进入步骤 2
   - ❌ 输出"未发现对齐锁"/"已过期"/"内容已变更"/"文件不存在" → 继续下面的对齐流程

2. **执行需求对齐**：
   - **若已安装 `product-requirements` skill**：使用该 skill 进行交互式需求收集与 PRD 生成
   - **若未安装**：直接与用户进行结构化需求对话，覆盖以下要点后手动生成 PRD：
     - 目标站点与数据范围
     - 输出格式与字段要求
     - 频率/增量/全量策略
     - 登录态/yzm/fk 的已知情况

3. **对齐完成后，必须写入对齐锁**：
   ```bash
   python -c "import os; os.system(f'python {os.path.expanduser(\"~/.codex/skills/protocol-crawler/scripts/alignment_lock.py\")} set --target prd --scope \"对齐范围\" --create')"
   ```
   > 不写锁 = 下次会话会重新对齐需求，浪费时间。

### 2) ⛔ 技术方案对齐（强制 — 必须通过才能开始技术分析）

> **⚠️ 未完成 2 轮对齐讨论并获得用户明确允许前，绝对禁止进入步骤 3（DevTools 分析）。**

**第 1 轮：初步方案汇报**（Agent → 用户）

基于已有信息（PRD、用户描述、站点初步印象），Agent 必须输出：

```
【技术方案对齐】
1. 目标站点：<站点名称、URL>
2. 采集目标：<要爬取的数据类型和范围>
3. 初步判断：<预估难度（低/中/高）、依据>
4. 技术路线：<计划使用的库/工具、大致思路>
5. 潜在风险：<可能遇到的fk/qm/yzm/登录态问题>
6. 下一步计划：<准备用 DevTools 分析哪些接口>
```

然后**停下来等待用户反馈**，禁止自行继续。

**第 2 轮：确认与调整**（用户 ↔ Agent）

根据用户反馈调整方案，直到用户明确表示同意（如"可以"、"开始"、"GO"）。

> **只有在用户明确允许后才能进入步骤 3。** 如果用户没有回复或表示需要再想想，Agent 必须等待，不得自行推进。

> 📢 **进度汇报点**：获得用户同意后，告知用户"方案已确认，开始 DevTools 接口分析"。

### 3) 站点探索与接口分析

> **⚠️ 此步骤必须使用 Chrome DevTools MCP 工具完成，禁止跳过、禁止用猜测代替实际抓包。**
>
> **⚠️ 实现前必须先阅读** `references/core/devtools-mcp.md`

**具体操作序列（按顺序执行）：**

1. **获取页面快照**：调用 `take_snapshot` 了解当前页面结构和元素 UID
2. **导航到目标站点**：调用 `navigate_page` 打开目标 URL（确保使用已登录的浏览器会话 `127.0.0.1:9222`）
3. **等待页面就绪**：调用 `wait_for` 等待关键内容出现
4. **触发目标请求**：通过 `click`/`scroll`/页面交互触发目标数据的加载
5. **抓取网络请求列表**：调用 `list_network_requests`，设置 `resourceTypes: ["fetch", "xhr"]` 过滤噪声
6. **逐个分析关键请求**：对每个关键请求调用 `get_network_request`（传入 reqid），提取：
   - 请求 URL（Host + Path）、方法（GET/POST）
   - Headers（Authorization、CSRF、自定义 X- 头）
   - Cookies（哪些与登录态绑定）
   - Body / Query Parameters 结构
   - 响应结构（JSON Schema、分页字段）
7. **分页验证**：至少触发 **2-3 次**分页请求，对比 cursor/offset 递进规律
8. **截图存档**：调用 `take_screenshot` 保存关键页面状态

**关键原则：**

- 每次操作前必须先 `take_snapshot` 获取最新页面状态和元素 UID
- 只关注 `fetch`/`xhr` 类型，忽略 image/stylesheet/script 等静态资源
- 明确区分**动态字段**（token/qm/时间戳/游标）与**静态字段**（固定 headers/固定参数）
- GraphQL 请求重点提取 `doc_id`/`query_hash`/`variables`（详见 `references/core/graphql-replay.md`）

**需要登录时**：默认只走人工登录 + 导出 cookies/storage_state；只有用户建议/要求时，才允许用 crawl4ai/自动化做"登录态获取/分析辅助"（禁止用于数据采集）。

**遇到 yzm 时（强制流程）**：

0. **先检查能否 pj**：检查 headers/Cookie 是否可以直接rg yzm（部分站点 yzm 仅前端校验，后端不强制）
1. **先 zrgz**：在用户操作前，通过 `evaluate_script` 注入拦截钩子，捕获 yzm 相关的回调函数、token 参数、请求链路（如 cf Turnstile 的 `cf_clearance`、滑块 yzm 的轨迹提交接口等）
2. **提示用户手动过 yzm**：明确告知用户"请在浏览器中手动完成 yzm，完成后告诉我"
3. **用户完成后抓包**：调用 `list_network_requests` + `get_network_request`，提取 yzm 的完整参数链路（提交接口、token 字段、回调参数）
4. 详见 `references/yzm/captcha-solutions.md`

> ⚠️ **顺序不可颠倒**：必须先 zrgz 再让用户过 yzm，否则参数链路抓不到。

**接口/协议不清晰**：若环境具备 Firecrawl MCP，必须使用其检索官方文档或公开资料。

**步骤 3 完成后，必须输出接口复现说明**（格式见 `references/core/devtools-mcp.md` 交付物章节）：Endpoint、Headers、Cookies、Body/Query、Pagination、Response Schema、Rate Limit。

### 4) 难度补充汇报

> 📢 **进度汇报点**：分析完成后必须向用户汇报分析结果。

分析完成后，若实际情况与步骤 2 的初步判断**存在差异**（如难度更高、发现未预料的fk机制、需要nx等），必须向用户补充汇报并等待确认后再继续。

若实际情况与预期一致，简要告知用户分析结果后直接进入步骤 5。

> 📢 **进度汇报点**：进入实现前，告知用户"分析完成，开始编码实现"。

### 5) 实现与验证

**⚠️ 实现前必须先阅读** `references/humanization/network-layer.md`

- 按 PRD 实现协议pc（请求构建、qm/鉴权、分页、重试、限速、日志、失败兜底）

**HTTP 客户端（强制 — 禁止裸 requests）：**

```python
# ✅ 正确：使用 curl_cffi 模拟真实浏览器 TLS zw
from curl_cffi import requests
session = requests.Session(impersonate="chrome110")

# ❌ 错误：裸用 requests/httpx（TLS zw 暴露）
import requests  # 禁止
```

> 详细原理见 `references/humanization/network-layer.md`

**Session 管理（强制 — 禁止裸请求）：**

- ✅ **必须全程使用同一个 `session` 对象**，让 Cookie jar 自动管理
- ❌ **禁止每次请求创建新的 session/client**（Cookie/zw 丢失 → 触发fk）
- 登录态 Cookie（如 `sessionid`、`csrftoken`）和fk追踪 Cookie（如 `_ga`、`cf_bm`）必须在 session 中持续携带
- 如果爬取中间 Cookie 突然被清空或变化，**立即停止**排查原因

**UA 与 TLS zw 一致性（强制）：**

- `impersonate` 参数与 `User-Agent` 头必须匹配同一浏览器版本
- ❌ 禁止 `impersonate="chrome110"` 却发 `User-Agent: Mozilla/5.0 ... Firefox/120`
- ❌ 禁止不设 `impersonate` 但手动拼 Chrome UA（TLS zw 不匹配）

**Referer 链真实性：**

- 首次请求的 `Referer` 应为搜索引擎或站点首页（不留空）
- 后续导航请求的 `Referer` 应为上一个页面的 URL
- API 请求的 `Referer` 和 `Origin` 应与 DevTools 抓包结果一致

**限速（强制 — 保守节奏）：**

| 场景          | 建议间隔    | 代码                               |
| ------------- | ----------- | ---------------------------------- |
| 每请求间隔    | 2-5s + 抖动 | `time.sleep(random.uniform(2, 5))` |
| 每 N 页长休息 | 10-60s      | 每 10-20 页休息一次                |
| zh 之间休息   | 20-120s     | 切换 zh 时                         |

> 详细退避策略见 `references/core/error-checkpoint.md`

**dl 管理（使用 dl 时强制）：**

- 使用前**必须验证 dl 存活性**（发测试请求确认 IP 已变化）
- 实现 dl 故障转移：单个 dl 连续失败 3 次 → 自动切换到下一个
- 记录每个 dl 的成功/失败次数，淘汰高失败率 dl
- 禁止裸 IP（不经 dl）和 dl IP 混用（zw不一致 → 触发fk）

**蜜罐数据检测：**

- 爬到的数据如果**内容高度重复**、**字段值异常规整**、或**与页面展示不一致**，可能是蜜罐数据
- 冒烟测试时**必须对比** DevTools 中看到的真实页面数据与程序爬取的数据，确保一致
- 如果返回了 200 但数据看起来像是假的（如所有价格都是 0、所有名字都相同），保存到 `tmp/responses/` 并报告用户

**其他实现要求：**

- **nx 文档强制**：每完成一个加密参数 nx，必须在 `js/docs/{param}.md` 创建对应文档（模板见 `templates/nx-param-doc.md`）
- **输出数据校验**：运行时抽样检查字段完整性和类型一致性，检测 Schema 漂移（详见 `references/core/data-validation.md`）
- **2cc/cs 对接规范**：需要过码时，必须先用 Firecrawl MCP 调研 2cc/cs 的**官方 API 文档**，基于实际能力择一对接（不是两个都写）
- 结果输出需可复现、可验证，避免"只给片段代码"

**⚠️ 依赖收集（强制 — 写代码前必须完成）**：

实现前，Agent 必须检查所有外部依赖是否就绪，**缺什么就向用户要什么**，不得留空让用户自行填写：

- **登录态**：需要 cookies/storage_state → 提示用户在 9222 浏览器登录，然后通过 DevTools 导出
- **2cc/cs API KEY**：需要过码 → 明确告知用户"我需要一个 2cc/cs 的测试 API KEY 来完成对接和测试"
- **dl 配置**：需要 dl → 向用户确认 dl 服务地址和认证方式
- 其他任何运行所需的凭据或配置

**收集到的凭据 → 写入 `.env`**（见强制规则第 3 条），代码通过 `os.getenv()` 读取。

> ❌ 禁止写完代码后说"请自行填入 API KEY 测试"。必须在编码前收集齐全并写入 `.env`。

**⚠️ 冒烟测试（强制 — 代码写完后必须执行）**：

代码完成后，Agent **必须实际运行** pc 脚本，验证能真实爬到数据：

1. 运行脚本，确认请求成功（200 + 有效数据返回）
2. 检查输出文件（JSONL/CSV）中包含真实数据
3. 验证分页至少翻 2-3 页
4. 若冒烟测试失败，必须调试修复后再次运行，直到通过

> ❌ "代码已写好，你试试" 不算交付。必须自己跑通才算完成。

**Superpowers 集成**：若环境自检确认已安装 `superpowers`，实现阶段**必须遵守**其工程流程：

- 多步任务使用 `writing-plans` skill 制定细粒度实现计划
- 编码采用 `test-driven-development` skill 的 RED-GREEN-REFACTOR 流程
- 调试使用 `systematic-debugging` skill 的 4 阶段根因分析
- 完成前使用 `verification-before-completion` skill 确认修复

若未安装 Superpowers，按步骤 5 的基本要求执行即可，无需额外流程。

**⚠️ 多站点管道并行（推荐架构）**：

当任务涉及**多个相关联的站点**时，不要串行跑完一个站点再跑下一个。采用**管道并行**架构：

```
站点 A（上游）──产出数据──→ 立即投入 站点 B（中游）──产出数据──→ 立即投入 站点 C（下游）
    │                           │                           │
    └── 独立限速/重试/断点       └── 独立限速/重试/断点       └── 独立限速/重试/断点
```

**实现要点：**

- 各站点各自独立的 Crawler 实例，独立的限速、重试、断点续跑
- 上游产出一条数据后，**立即**将其投入下游队列（不等上游全部跑完）
- 使用 `asyncio.Queue` 或文件队列作为站点间的数据传递通道
- 任一站点异常停止时，不影响其他站点继续运行
- 每个站点有独立的输出文件和断点文件

> 例：CTOS 爬出公司名 → 立刻投入 BusinessList 查域名 → 立刻投入 Snov 查邮箱。三条线并行，互不阻塞。

### 6) CI 门禁检查（⚠️ 强制 — 实现完成后、交付前必须逐项执行）

> **任何一项不通过，则不能交付，必须先修复。**

| #   | 检查项     | 标准                                                             | 不通过时的处理         |
| --- | ---------- | ---------------------------------------------------------------- | ---------------------- |
| 1   | 单文件行数 | **≤ 1000 行**                                                    | 拆分为多个模块文件     |
| 2   | 单函数行数 | **≤ 200 行**                                                     | 拆分为子函数           |
| 3   | 文件命名   | **禁止版本号后缀**（`_v2`、`_v3`、`_new`、`_old`）               | 重命名，只保留一份     |
| 4   | 废弃代码   | **同功能只保留一份**；切换方案时**必须删除旧方案代码和文件**     | 删除废弃代码           |
| 5   | 注释语言   | **中文**，禁止人称（如"帮你改了"、"我觉得"）                     | 修改注释               |
| 6   | 文件编码   | **UTF-8**                                                        | 转换编码               |
| 7   | debug/tmp/ | 均已添加到 `.gitignore`；根目录无遗留临时文件                    | 清理 + 更新 .gitignore |
| 8   | .env       | 凭据在 `.env` 中，`.env` 已加入 `.gitignore`，有 `.env.example`  | 补充 .env 文件         |
| 9   | 目录结构   | 符合 `references/core/engineering-standards.md` 中的项目结构规范 | 调整目录               |

> ⛔ **CI 门禁反作弊警告**：当文件/函数超限时，**只能通过合理拆分文件和模块来解决**。
>
> - ❌ **严禁为了过关而删除**错误处理、重试逻辑、数据校验、日志等健壮性代码
> - ❌ **严禁为了过关而合并**多个独立函数为一个巨型函数
> - ❌ **严禁为了过关而移除**注释和文档字符串
> - ✅ 正确做法：将大文件按职责拆分为多个模块（如 `crawler.py` → `crawler.py` + `parser.py` + `paginator.py`）
> - ✅ 正确做法：将大函数按逻辑步骤拆分为多个子函数

**执行方式**：实现完成后运行 CI 门禁脚本，自动检查第 1-3、6-9 项，第 4-5 项需人工确认：

> ⚠️ **路径提示**：为保证跨平台执行成功，**必须**使用以下命令自动组合绝对路径测试（请勿手动替换占位符）：

```bash
python -c "import os; os.system(f'python {os.path.expanduser(\"~/.codex/skills/protocol-crawler/scripts/ci_gate.py\")} {os.getcwd()}')"
```

脚本返回 0 = 全部通过，返回 1 = 存在不通过项。交付时向用户报告检查结果。

### 7) 最终清理与交付（收尾机制）

门禁通过并完成开发后，Agent 必须执行最后一步清洁工作：

1. **扫描统计**：分别扫描项目下的 `tmp/` 和 `debug/` 目录，统计文件数量和预估体积。
2. **主动清理与存档**：向用户汇报：_"代码已验证通过。目前 `tmp/` 和 `debug/` 积累了大量残留请求日志。是否需要我用脚本将 `debug/` 有价值日志打包为 ZIP 存档，并清理临时目录以保持整洁？"_
3. **跨平台兼容删除**：若用户同意，**严禁使用 `rm -rf`**，必须使用 Python 命令（如 `shutil.rmtree`，并可选组合 `shutil.make_archive`）执行清理，确保 Windows/Mac/Linux 均不报错。

---

## 文件索引（遇到相关场景时主动查阅）

**MCP 工具**：Chrome DevTools (`127.0.0.1:9222`，有状态) | Firecrawl MCP (联网搜索，可选) — 操作前必须先 `take_snapshot`。

### references/ — 深入参考资料

| 文件路径                                                 | 内容摘要                                                            | 何时查阅                        |
| -------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------- |
| `core/_index.md`                                         | core 目录导航与速查                                                 | 首次进入 core 目录时            |
| `core/devtools-mcp.md`                                   | DevTools 抓包的完整操作清单、GraphQL 特殊处理、fk信号识别、采样策略 | 步骤 3 站点探索与接口分析时     |
| `core/request-replay.md`                                 | 请求模板标准化、动态/静态字段拆分、qm复现步骤、常见坑               | 构建请求模板时                  |
| `core/error-checkpoint.md`                               | HTTP 错误码处理策略、异常重试矩阵、断点续跑机制、限流退避算法       | 处理请求失败/429/403/断点续跑时 |
| `core/graphql-replay.md`                                 | GraphQL 请求提取要点（doc_id/variables/分页字段）、batch 拆分       | 目标站点使用 GraphQL 时         |
| `core/data-validation.md`                                | 数据校验规则、去重策略、字段完整性检查                              | 验证采集数据质量时              |
| `core/engineering-standards.md`                          | 完整项目目录结构规范、编码规范、测试规范、debug/output 目录规范     | 初始化项目结构 / CI 门禁检查时  |
| `core/prd-alignment.md`                                  | PRD 对齐锁机制（格式、脚本用法、失效条件）                          | 步骤 1 PRD 对齐时               |
| `yzm/captcha-solutions.md`                               | 各类yzm的过码方案选择（2cc/cs）、对接接口模板                       | 遇到yzm需要过码时               |
| `humanization/_index.md`                                 | 拟人化策略总览与文件导航                                            | 需要fk对抗时先看这个            |
| `humanization/network-layer.md`                          | **TLS zw（JA3/JA4）+ curl_cffi 配置、HTTP/2 头部顺序、Cookie zw**   | **所有 pc 项目必读**            |
| `humanization/browser-automation/browser-fingerprint.md` | 浏览器zw（WebGL/字体/Canvas）检测与对抗                             | 浏览器辅助场景被zw检测拦截时    |
| `humanization/browser-automation/mouse-biometrics.md`    | 鼠标轨迹生物特征模拟                                                | 浏览器辅助场景需要模拟鼠标时    |
| `humanization/browser-automation/keystroke-dynamics.md`  | 键盘输入节奏模拟                                                    | 浏览器辅助场景需要模拟键盘时    |
| `humanization/browser-automation/scroll-navigation.md`   | 滚动与导航行为的拟人化                                              | 浏览器辅助场景需要模拟滚动时    |

### scripts/ — 辅助脚本

| 文件路径                    | 用途                                     |
| --------------------------- | ---------------------------------------- |
| `scripts/alignment_lock.py` | PRD 对齐锁管理（set/check/verify/clear） |
| `scripts/ci_gate.py`        | CI 门禁自动检查（步骤 6 对应脚本）       |

### templates/ — 文档模板

| 文件路径                    | 用途                                                                                  |
| --------------------------- | ------------------------------------------------------------------------------------- |
| `templates/nx-param-doc.md` | nx 参数文档模板 — 每完成一个加密参数 nx，必须在项目 `js/docs/{param}.md` 创建对应文档 |

### examples/ — 端到端参考

| 文件路径             | 用途                                                         |
| -------------------- | ------------------------------------------------------------ |
| `examples/README.md` | 完整 pc 项目骨架（目录结构 + 关键代码片段 + 交付物检查清单） |
