# 代理（dl）管理

## 何时需要 dl

- IP 被封禁（403 Forbidden 持续出现）
- 地理位置限制（目标站点仅对特定地区开放）
- 大规模采集需要 IP 轮换以分散fk压力

## dl 类型选择

| 类型                         | 适用场景                   | 优点               | 缺点               |
| ---------------------------- | -------------------------- | ------------------ | ------------------ |
| **住宅 dl (Residential)**    | 高fk站点、需要真实 IP 归属 | 最接近真实用户 IP  | 价格高、速度不稳定 |
| **数据中心 dl (Datacenter)** | 低fk站点、大量请求         | 速度快、稳定、便宜 | 易被识别为 dl      |
| **移动 dl (Mobile)**         | 最高fk站点                 | 最难被封           | 最贵、速度最慢     |
| **ISP dl**                   | 中高fk站点                 | 兼顾速度和真实性   | 价格中等           |

> **决策简化**：默认选住宅 dl。若预算有限且目标站点fk不强，可用数据中心 dl。

## dl 存活校验

```python
from curl_cffi import requests

def check_proxy(proxy_url: str, timeout: int = 10) -> bool:
    """校验 dl 是否存活"""
    try:
        resp = requests.get(
            "https://httpbin.org/ip",
            proxies={"https": proxy_url},
            timeout=timeout,
            impersonate="chrome110"
        )
        return resp.status_code == 200
    except Exception:
        return False
```

## dl 轮换策略

### 轮换器实现

```python
import random
from typing import List

class ProxyRotator:
    """dl 轮换器（失败淘汰 + 随机选择）"""

    def __init__(self, proxies: List[str], max_failures: int = 3):
        self.proxies = proxies
        self.failed_counts: dict[str, int] = {}
        self.max_failures = max_failures

    def get_proxy(self) -> str:
        """获取一个可用 dl"""
        available = [
            p for p in self.proxies
            if self.failed_counts.get(p, 0) < self.max_failures
        ]
        if not available:
            raise RuntimeError("所有 dl 均已失效，停止运行并报告用户")
        return random.choice(available)

    def report_failure(self, proxy: str) -> None:
        """报告 dl 失败"""
        self.failed_counts[proxy] = self.failed_counts.get(proxy, 0) + 1

    def report_success(self, proxy: str) -> None:
        """报告 dl 成功（重置失败计数）"""
        self.failed_counts[proxy] = 0

    @property
    def active_count(self) -> int:
        """当前可用 dl 数量"""
        return sum(
            1 for p in self.proxies
            if self.failed_counts.get(p, 0) < self.max_failures
        )
```

### 切换时机

| 触发条件      | 动作               |
| ------------- | ------------------ |
| 403 连续 2 次 | 切换 dl            |
| 429 限流      | 切换 dl + 退避     |
| 连接超时 3 次 | 标记失效，切换 dl  |
| 每 N 个请求   | 预防性轮换（可选） |

## dl 配置规范

dl 地址必须写入 `.env`，代码通过 `os.getenv()` 读取：

```env
# .env
PROXY_URL=http://user:pass@proxy.example.com:8080
# 多个 dl 用逗号分隔
PROXY_POOL=http://p1:8080,http://p2:8080,http://p3:8080
```

```python
import os

proxy_pool = os.getenv("PROXY_POOL", "").split(",")
proxy_pool = [p.strip() for p in proxy_pool if p.strip()]
```

## 注意事项

- dl 需要在使用前做存活校验，淘汰不可用节点
- 住宅 dl 的 IP 可能被回收复用，注意 Cookie/Session 一致性
- 部分站点检测 dl 头（`X-Forwarded-For`、`Via`），确保 dl 不泄露这些头
- dl 失败后切换新 dl 时，Session/Cookie 状态需同步考虑
