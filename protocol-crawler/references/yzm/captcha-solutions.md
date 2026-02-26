# yzm 处理策略

## ⚠️ 核心原则

**一律走 2cc/cs 过码 + nx 接口，无例外。**

- ❌ 禁止训练 yzm 模型
- ❌ 禁止将"让用户手动过 yzm"作为生产方案
- ✅ 分析阶段允许让用户手动过一次（配合 zrgz 抓参数链路）

---

## yzm 类型与方案速查

| 类型              | 推荐平台 | nx 要点                           |
| :---------------- | :------- | :-------------------------------- |
| 图形 yzm          | 2cc      | nx 图片获取接口 + yzm 提交接口    |
| 滑块 yzm          | 2cc      | nx 背景/滑块图获取 + 轨迹提交接口 |
| 点选 yzm          | 2cc      | nx 图片获取 + 坐标提交接口        |
| reCAPTCHA v2/v3   | 2cc/cs   | nx sitekey、callback 参数         |
| cf/hyzm/Turnstile | cs       | nx cf_clearance、zrgz 回调        |
| 短信 yzm          | —        | 无法自动化，提示用户人工处理      |
| 邮箱 yzm          | —        | IMAP 读取，需要邮箱权限           |

## 打码平台

| 平台    | 官网          | 适用场景                             |
| :------ | :------------ | :----------------------------------- |
| **2cc** | 2captcha.com  | 通用首选（图形/滑块/点选/reCAPTCHA） |
| **cs**  | capsolver.com | 高难度（cf/hyzm/Turnstile/环境检测） |

---

## 决策流程

```
遇到 yzm
    │
    ├─ 能否 rg？（检查 headers/Cookie 直接跳过）
    │   └─ ✅ rg 成功 → 无需处理
    │
    ├─ cf/hyzm/Turnstile？
    │   └─ cs 过码 + nx 接口
    │
    └─ 其他 yzm？
        └─ 2cc 过码 + nx 接口
```

---

## nx 工作流

### 1. 分析 yzm 参数链路（分析阶段）

> 此步骤在 SKILL.md 步骤 3（站点探索）中执行。

1. **先检查能否 rg**：检查 headers/Cookie 是否可以直接 rg yzm
2. **zrgz**：通过 `evaluate_script` 注入拦截钩子，捕获 yzm 回调函数、token 参数
3. **提示用户手动过 yzm**：告知用户"请在浏览器中手动完成 yzm，完成后告诉我"
4. **抓包**：调用 `list_network_requests` + `get_network_request`，提取：
   - yzm 图片/参数的获取接口
   - yzm 答案的提交接口
   - 验证结果返回的接口
   - 所有关联的 token/callback 参数

> ⚠️ **顺序不可颠倒**：必须先 zrgz 再让用户过 yzm，否则参数链路抓不到。

### 2. 调研打码平台 API（实现阶段）

**⚠️ 强制**：对接前必须用 Firecrawl MCP 查阅 2cc/cs 的**官方 API 文档**，基于目标 yzm 类型择一对接。

- 2cc 文档：`https://2captcha.com/2captcha-api`
- cs 文档：`https://docs.capsolver.com/`

不要凭记忆写 API 调用代码，必须参考最新文档。

### 3. 对接代码示例

> ⚠️ **以下代码仅展示对接结构（提交任务 → 轮询结果的模式），实际参数名、接口地址、任务类型以官方最新文档为准。直接复制可能因 API 版本变更而失败。**
>
> 💡 **关于 HTTP 库**：过码平台 API 请求属于**第三方服务对接**，不属于"数据采集面"，因此不受 SKILL.md "禁止裸 requests" 限制。示例中使用 `httpx` 是合理的。

**2cc 示例（图形 yzm）**：

```python
import httpx
import time

def solve_captcha_2cc(image_base64: str, api_key: str) -> str:
    """通过 2cc 识别图形 yzm"""
    # 提交任务
    resp = httpx.post("http://2captcha.com/in.php", data={
        "key": api_key,
        "method": "base64",
        "body": image_base64,
        "json": 1
    }).json()
    task_id = resp["request"]

    # 轮询结果
    for _ in range(30):
        time.sleep(3)
        result = httpx.get(
            f"http://2captcha.com/res.php?key={api_key}&action=get&id={task_id}&json=1"
        ).json()
        if result["status"] == 1:
            return result["request"]
    raise Exception("yzm 超时")
```

**cs 示例（cf Turnstile）**：

```python
import httpx
import time

def solve_turnstile_cs(site_key: str, page_url: str, api_key: str) -> str:
    """通过 cs 解决 cf Turnstile"""
    # 创建任务
    resp = httpx.post("https://api.capsolver.com/createTask", json={
        "clientKey": api_key,
        "task": {
            "type": "AntiTurnstileTaskProxyLess",
            "websiteURL": page_url,
            "websiteKey": site_key,
        }
    }).json()
    task_id = resp["taskId"]

    # 轮询结果
    for _ in range(60):
        time.sleep(3)
        result = httpx.post("https://api.capsolver.com/getTaskResult", json={
            "clientKey": api_key,
            "taskId": task_id
        }).json()
        if result["status"] == "ready":
            return result["solution"]["token"]
    raise Exception("yzm 超时")
```

### 4. 协议复现提交

```python
def submit_captcha(session, captcha_answer: str, captcha_id: str):
    """用 nx 到的接口参数提交 yzm 答案"""
    return session.post("https://target.com/api/verify", json={
        "captcha_id": captcha_id,
        "answer": captcha_answer,
        # ... 其他 nx 到的必要参数
    })
```

---

## 注意事项

- **API KEY**：对接前必须向用户要测试 KEY，不得留空让用户自行填写
- **择一对接**：根据 yzm 类型选一个平台即可，不需要两个都写
- **⚠️ 官方文档优先**：上方代码示例仅展示对接结构。实现时**必须先用 Firecrawl MCP 抓取官方最新 API 文档**，以官方文档中的参数名、接口地址、任务类型为准
- **版本风险**：打码平台 API 更新频繁，示例中的字段名（如 `method`、`type`、`taskId`）可能已变更
