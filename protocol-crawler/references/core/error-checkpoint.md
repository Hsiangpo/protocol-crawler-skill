# 错误处理与断点续跑

> 快速跳转：遇到什么问题就看哪一节
>
> | 场景                | 跳转章节                            |
> | ------------------- | ----------------------------------- |
> | 收到 4xx/5xx 状态码 | **一、HTTP 状态码处理矩阵**         |
> | 网络超时/连接失败   | **二、错误分类与处理 → 网络层错误** |
> | 被 429 限流         | **三、退避策略 → 429 专用策略**     |
> | 需要断点续跑        | **四、断点续跑**                    |
> | 处理分页逻辑        | **五、分页处理**                    |
> | 程序崩溃后恢复      | **五、分页处理 → 恢复脚本模板**     |

> 历史版本已合并：response-handling + pagination-checkpoint + checkpoint

---

## 一、HTTP 状态码处理矩阵

### 核心原则

- 遇到挑战/登录重定向时**立即停止**，要求人工处理后再继续
- 429/403/401 优先视为 fk 信号，不做"规避性"对抗
- 采用保守节奏：低并发、随机抖动、周期性长休息

### 状态码详解

| 状态码                   | 判定            | 处理策略                                  | 代码示例                    |
| ------------------------ | --------------- | ----------------------------------------- | --------------------------- |
| **200**                  | 正常            | 继续                                      | -                           |
| **200 但数据异常**       | 可能被识别为 pc | 检查 zw/qm，保存原始响应                  | 见下方                      |
| **301/302 → /challenge** | 触发验证        | **立即停止**，保存 progress，提示人工处理 | `raise ChallengeError`      |
| **301/302 → /login**     | 登录失效        | **停止**，保存 progress，重新登录         | `raise SessionExpiredError` |
| **400**                  | 请求参数错误    | 记录请求参数，检查 qm 算法                | 日志 + 跳过                 |
| **401**                  | 鉴权失败        | 检查 cookies/headers/权限                 | `raise AuthError`           |
| **403**                  | 权限/fk         | 降速或停止，检查请求合法性                | 见退避策略                  |
| **404**                  | 资源不存在      | 记录并跳过，不重试                        | `continue`                  |
| **429**                  | 限流            | **长退避或停止**，尊重 Retry-After        | 见 429 专用策略             |
| **500**                  | 服务端错误      | 有限重试（最多 3 次）                     | 指数退避                    |
| **502/503**              | 网关/服务不可用 | 检查是否触发 WAF，短暂退避后重试          | 指数退避                    |
| **504**                  | 网关超时        | 短暂退避后重试                            | 指数退避                    |

### 200 但数据异常判定

```python
def check_response_anomaly(resp: dict) -> bool:
    """检查 200 响应是否异常"""
    # 1. 空数据
    if not resp.get("data"):
        return True
    # 2. 数据结构变化
    if "expected_field" not in resp.get("data", {}):
        return True
    # 3. 明显的 fk 信号
    if resp.get("code") in [-1, -403, -429]:
        return True
    return False
```

---

## 二、错误分类与处理

### 网络层错误

| 错误类型          | 处理策略                    | 重试次数 |
| ----------------- | --------------------------- | -------- |
| `Timeout`         | 短暂退避后重试              | 3-5 次   |
| `ConnectionError` | 短暂退避后重试              | 3 次     |
| `ConnectionReset` | 可能触发 fk，检查请求频率   | 2 次     |
| `SSLError`        | 检查 TLS zw，尝试 curl_cffi | 1 次     |
| `ProxyError`      | 切换 dl 后重试              | 3 次     |

### 鉴权层错误

| 错误类型         | 处理策略               | 是否停止 |
| ---------------- | ---------------------- | -------- |
| 401 Unauthorized | 刷新 token / 重新登录  | 是       |
| 403 Forbidden    | 检查权限 / 降速        | 视情况   |
| Session 过期     | 重新获取 storage_state | 是       |
| Cookie 无效      | 重新登录获取           | 是       |

### fk 层错误

| 错误类型     | 处理策略             | 是否停止 |
| ------------ | -------------------- | -------- |
| 429 Too Many | 长退避（60s+）/ 停止 | 建议停止 |
| 触发 yzm     | 调用 2cc/cs 或停止   | 视配置   |
| IP 封禁      | 切换 dl / 停止       | 是       |
| 挑战页 (cf)  | 调用 cs 或停止       | 视配置   |

### 数据层错误

| 错误类型      | 处理策略               | 是否停止 |
| ------------- | ---------------------- | -------- |
| JSON 解析失败 | 保存原始响应，记录日志 | 否       |
| Schema 缺字段 | 记录版本漂移，降级处理 | 否       |
| 空列表        | 确认是否分页结束       | 否       |
| 数据格式变化  | 更新解析器，记录日志   | 否       |

---

## 三、退避策略

### 基础退避（指数退避 + 抖动）

```python
import random
import time

def exponential_backoff(retry: int, base: float = 3.0, max_delay: float = 60.0) -> float:
    """计算退避时间"""
    delay = min(base * (2 ** retry), max_delay)
    jitter = random.uniform(0, delay * 0.3)  # 30% 抖动
    return delay + jitter

# 使用示例
for retry in range(5):
    try:
        response = make_request()
        break
    except RetryableError:
        delay = exponential_backoff(retry)
        logger.info(f"Retry {retry + 1}, waiting {delay:.2f}s")
        time.sleep(delay)
```

### 429 专用策略

```python
def handle_429(response) -> float:
    """处理 429 响应"""
    # 1. 优先使用 Retry-After 头
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        if retry_after.isdigit():
            return float(retry_after)
        else:
            # 可能是日期格式
            return 60.0  # 默认 60s

    # 2. 默认长退避
    return 60.0 + random.uniform(0, 30)  # 60-90s

# 处理流程
if response.status_code == 429:
    delay = handle_429(response)
    if delay > 300:  # 超过 5 分钟
        save_progress()  # 保存进度
        raise TooManyRequestsError("退避时间过长，停止运行")
    logger.warning(f"429 限流，等待 {delay:.0f}s")
    time.sleep(delay)
```

### 限速策略

| 场景          | 建议间隔    | 说明                   |
| ------------- | ----------- | ---------------------- |
| 每请求间隔    | 2-5s + 抖动 | `random.uniform(2, 5)` |
| 每 N 页长休息 | 10-60s      | 每 10-20 页休息一次    |
| zh 之间休息   | 20-120s     | 切换 zh 时             |
| 错误后退避    | 指数增长    | 从 3s 到 60s           |

---

## 四、断点续跑实现

### 设计原则

| 原则         | 说明                        |
| ------------ | --------------------------- |
| **两层去重** | 输出数据去重 + 进度游标去重 |
| **原子写入** | 先写临时文件再替换          |
| **及时落盘** | 每条/每批写入，不堆积内存   |
| **幂等处理** | 重复运行不产生重复数据      |

### 进度文件结构

```json
{
  "version": 1,
  "run_id": "2026-02-06_120000",
  "started_at": "2026-02-06T12:00:00Z",
  "tasks": {
    "task_001": {
      "cursor": "end_cursor_value",
      "page": 12,
      "offset": 240,
      "saved": 345,
      "has_next": true,
      "completed": false,
      "last_error": null,
      "retry_count": 0,
      "updated_at": "2026-02-06T12:30:00Z"
    },
    "task_002": {
      "cursor": null,
      "page": 25,
      "offset": 500,
      "saved": 500,
      "has_next": false,
      "completed": true,
      "last_error": null,
      "retry_count": 0,
      "updated_at": "2026-02-06T12:35:00Z"
    }
  }
}
```

### 原子写入实现

```python
from pathlib import Path
import json
import os

def atomic_write_json(path: Path, data: dict) -> None:
    """原子写入 JSON 文件"""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_path.replace(path)  # 原子替换
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()  # 清理临时文件
        raise

def atomic_append_jsonl(path: Path, item: dict) -> None:
    """原子追加 JSONL"""
    line = json.dumps(item, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())  # 强制落盘
```

### 完整断点续跑示例

```python
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from typing import Optional

@dataclass
class TaskProgress:
    cursor: Optional[str] = None
    page: int = 0
    offset: int = 0
    saved: int = 0
    has_next: bool = True
    completed: bool = False
    last_error: Optional[str] = None
    retry_count: int = 0
    updated_at: str = ""

class CheckpointManager:
    def __init__(self, progress_path: Path):
        self.path = progress_path
        self.data = self._load()

    def _load(self) -> dict:
        """加载进度文件"""
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"version": 1, "tasks": {}}

    def get_task(self, task_id: str) -> TaskProgress:
        """获取任务进度"""
        task_data = self.data.get("tasks", {}).get(task_id, {})
        return TaskProgress(**task_data) if task_data else TaskProgress()

    def update_task(self, task_id: str, progress: TaskProgress) -> None:
        """更新任务进度"""
        progress.updated_at = datetime.utcnow().isoformat() + "Z"
        self.data.setdefault("tasks", {})[task_id] = asdict(progress)
        atomic_write_json(self.path, self.data)

    def mark_completed(self, task_id: str) -> None:
        """标记任务完成"""
        progress = self.get_task(task_id)
        progress.has_next = False
        progress.completed = True
        self.update_task(task_id, progress)

# 使用示例
def crawl_with_checkpoint(task_id: str, output_path: Path, progress_path: Path):
    checkpoint = CheckpointManager(progress_path)
    progress = checkpoint.get_task(task_id)

    # 已经完成则跳过
    if progress.completed:
        print(f"Task {task_id} already completed")
        return

    # 从断点继续
    cursor = progress.cursor
    page = progress.page or 1

    while True:
        try:
            # 请求数据
            data = fetch_page(cursor=cursor, page=page)

            # 写入数据
            for item in data["items"]:
                atomic_append_jsonl(output_path, item)

            # 更新进度
            progress.cursor = data.get("next_cursor")
            progress.page = page
            progress.saved += len(data["items"])
            progress.has_next = data.get("has_next", False)
            checkpoint.update_task(task_id, progress)

            # 检查终止条件
            if not progress.has_next:
                checkpoint.mark_completed(task_id)
                break

            cursor = progress.cursor
            page += 1

            # 限速
            time.sleep(random.uniform(2, 5))

        except (RateLimitError, ChallengeError) as e:
            # 保存进度后停止
            progress.last_error = str(e)
            checkpoint.update_task(task_id, progress)
            raise

        except RetryableError as e:
            progress.retry_count += 1
            if progress.retry_count > 5:
                progress.last_error = str(e)
                checkpoint.update_task(task_id, progress)
                raise
            time.sleep(exponential_backoff(progress.retry_count))
```

### JSONL 去重

```python
def load_existing_ids(jsonl_path: Path) -> set:
    """加载已存在的 ID 集合"""
    ids = set()
    if jsonl_path.exists():
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    ids.add(item.get("id"))
    return ids

def write_with_dedup(jsonl_path: Path, items: list, existing_ids: set) -> int:
    """去重写入"""
    count = 0
    for item in items:
        item_id = item.get("id")
        if item_id and item_id not in existing_ids:
            atomic_append_jsonl(jsonl_path, item)
            existing_ids.add(item_id)
            count += 1
    return count
```

---

## 五、分页模式

### 常见分页类型

| 模式           | 请求参数                      | 终止条件                               |
| -------------- | ----------------------------- | -------------------------------------- |
| **Cursor**     | `after/end_cursor/next_token` | `has_next_page=false` 或 `cursor=null` |
| **Offset**     | `offset` + `limit`            | 返回条数 < limit 或达到 total          |
| **Page**       | `page` + `page_size`          | 空列表或达到 total_pages               |
| **Time-based** | `start_time/end_time`         | 时间窗口遍历完成                       |
| **ID-based**   | `min_id/max_id/since_id`      | 无新 ID 或 ID 不再变化                 |

### 终止条件与防死循环

```python
def is_pagination_done(
    response: dict,
    last_cursor: Optional[str],
    consecutive_same: int
) -> tuple[bool, str]:
    """判断分页是否结束"""

    # 1. 明确的结束标志
    if not response.get("has_next_page", True):
        return True, "has_next_page=false"

    # 2. cursor 为空
    current_cursor = response.get("end_cursor") or response.get("next_token")
    if not current_cursor:
        return True, "cursor is empty"

    # 3. cursor 重复（防死循环）
    if current_cursor == last_cursor:
        if consecutive_same >= 3:
            return True, "cursor repeated 3 times"

    # 4. 空数据
    if not response.get("data", []):
        return True, "empty data"

    return False, ""
```

---

## 六、错误恢复清单

### 恢复检查点

| 情况             | 处理                                  |
| ---------------- | ------------------------------------- |
| 网络错误         | 重试若干次，失败后停止并保留 progress |
| 429/挑战页       | 立即停止，保留 progress，等待人工处理 |
| 登录过期         | 停止，保留 progress，提示重新登录     |
| 响应缺失分页字段 | 可能是鉴权不足或字段路径变更          |
| 程序崩溃         | 重启后从 progress 恢复                |

### 恢复脚本模板

```python
def resume_crawl(progress_path: Path) -> None:
    """恢复爬取"""
    checkpoint = CheckpointManager(progress_path)

    for task_id in checkpoint.list_incomplete_tasks():
        progress = checkpoint.get_task(task_id)

        # 清除错误状态
        progress.last_error = None
        progress.retry_count = 0

        print(f"Resuming task {task_id} from cursor={progress.cursor}, page={progress.page}")

        try:
            crawl_with_checkpoint(task_id, output_path, progress_path)
        except Exception as e:
            print(f"Task {task_id} failed: {e}")
            continue
```
