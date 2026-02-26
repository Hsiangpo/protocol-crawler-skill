# pc 项目端到端示例

> 此目录提供一个**最小可运行**的 pc 项目骨架，展示完整交付物的结构和代码规范。
> Agent 在初始化新项目时可参考此示例的目录结构和代码风格。

## 示例项目结构

```
example-project/
├── docs/
│   └── PRD.md                     # 需求文档
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── crawler.py             # 主 pc 逻辑
│   │   └── client.py              # HTTP 客户端封装
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── checkpoint.py          # 断点续跑
│   │   └── rate_limiter.py        # 限速器
│   └── config.py                  # 配置管理
├── tests/
│   └── test_crawler.py            # 测试文件
├── output/                        # 输出目录
│   └── .gitkeep
├── debug/                         # 调试文件（已 gitignore）
├── tmp/                           # 临时文件（已 gitignore）
│   ├── responses/                 # 调试用原始响应
│   └── screenshots/               # DevTools 截图
├── .env                           # 凭据（已 gitignore）
├── .env.example                   # 凭据模板（提交到 git）
├── .gitignore
├── requirements.txt
└── main.py                        # 入口
```

### .env.example

```env
# 打码平台
CAPTCHA_API_KEY=
# dl
PROXY_URL=
# 其他凭据
```

## 关键代码片段

### 1. HTTP 客户端封装（src/core/client.py）

```python
"""HTTP 客户端封装 — 强制 curl_cffi + TLS zw"""

import random
import time
from curl_cffi import requests


class PCClient:
    """协议爬虫 HTTP 客户端"""

    def __init__(self, impersonate: str = "chrome110"):
        self.session = requests.Session(impersonate=impersonate)
        self.min_delay = 2.0
        self.max_delay = 5.0

    def get(self, url: str, **kwargs) -> requests.Response:
        """发送 GET 请求（自动限速）"""
        self._rate_limit()
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """发送 POST 请求（自动限速）"""
        self._rate_limit()
        return self.session.post(url, **kwargs)

    def _rate_limit(self):
        """限速：每请求间隔 2-5s 随机抖动"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def set_cookies(self, cookies: dict):
        """从浏览器导出的 cookies 设置到会话"""
        for name, value in cookies.items():
            self.session.cookies.set(name, value)

    def close(self):
        """关闭会话"""
        self.session.close()
```

### 2. 主 pc 逻辑（src/core/crawler.py）

```python
"""主 pc 逻辑 — 包含分页、重试、断点续跑"""

import json
import logging
import random
import time
from pathlib import Path
from typing import Optional

from .client import PCClient

logger = logging.getLogger(__name__)


class Crawler:
    """协议爬虫主类"""

    def __init__(self, output_dir: str = "output", checkpoint_file: str = "checkpoint.json"):
        self.client = PCClient()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.checkpoint_file = Path(checkpoint_file)
        self.results = []
        self._empty_count = 0  # 连续空数据计数器
        self._max_retries = 3  # 429 最大重试次数

    def run(self, start_cursor: Optional[str] = None):
        """执行爬取（支持断点续跑）"""
        cursor = start_cursor or self._load_checkpoint()
        page = 0

        try:
            while True:
                page += 1
                logger.info(f"正在爬取第 {page} 页，cursor={cursor}")

                # 发送请求
                data = self._fetch_page(cursor)
                if data is None:
                    break

                # 解析并存储数据
                items = self._parse_items(data)
                self._save_items(items)
                logger.info(f"第 {page} 页获取 {len(items)} 条数据")

                # 检查分页
                cursor = self._get_next_cursor(data)
                if cursor is None:
                    logger.info("已到最后一页")
                    break

                # 保存断点
                self._save_checkpoint(cursor)

                # 每 10 页长休息
                if page % 10 == 0:
                    rest = random.uniform(10, 30)
                    logger.info(f"每 10 页长休息 {rest:.1f}s")
                    time.sleep(rest)

        except KeyboardInterrupt:
            logger.warning("用户中断，保存断点")
            if cursor:
                self._save_checkpoint(cursor)
        except Exception as e:
            logger.error(f"爬取异常：{e}，保存断点")
            if cursor:
                self._save_checkpoint(cursor)
            raise

        logger.info(f"爬取完成，共 {len(self.results)} 条数据")

    def _fetch_page(self, cursor: Optional[str]) -> Optional[dict]:
        """请求单页数据（需按实际接口修改）"""
        params = {"limit": 20}
        if cursor:
            params["cursor"] = cursor

        resp = self.client.get(
            "https://api.example.com/data",
            params=params,
            headers={
                "Accept": "application/json",
                # 其他 headers 按 DevTools 抓包结果填写
            }
        )

        if resp.status_code == 200:
            data = resp.json()
            # 空数据检测：连续 3 次空数据则停止
            items = data.get("items", [])
            if not items:
                self._empty_count += 1
                if self._empty_count >= 3:
                    logger.error("连续 3 次空数据，停止爬取，等待用户排查")
                    self._save_checkpoint(cursor)
                    return None  # 触发停止
                logger.warning(f"本页数据为空（连续第 {self._empty_count} 次）")
            else:
                self._empty_count = 0
            return data
        elif resp.status_code == 429:
            # 429 限流：指数退避（带最大重试次数）
            for attempt in range(1, self._max_retries + 1):
                retry_after = int(resp.headers.get("Retry-After", 60)) * attempt
                logger.warning(f"429 限流，第 {attempt} 次退避 {retry_after}s")
                time.sleep(retry_after)
                resp = self.client.get(
                    "https://api.example.com/data",
                    params=params,
                    headers={"Accept": "application/json"}
                )
                if resp.status_code != 429:
                    break
            if resp.status_code == 429:
                logger.error(f"429 限流 {self._max_retries} 次仍未恢复，停止爬取")
                self._save_checkpoint(cursor)
                return None
            return self._fetch_page(cursor)  # 用新 resp 重走解析逻辑
        elif resp.status_code == 403:
            # 403 封禁：立即停止，不要重试
            logger.error("403 被封禁，停止爬取，等待用户检查 IP/zw")
            self._save_checkpoint(cursor)
            return None
        elif resp.status_code == 302 and "/challenge" in resp.headers.get("Location", ""):
            # cf 挑战：立即停止
            logger.error("cf 挑战，停止爬取，等待用户通过 DevTools 处理")
            self._save_checkpoint(cursor)
            return None
        else:
            logger.error(f"请求失败：{resp.status_code}")
            return None

    def _parse_items(self, data: dict) -> list:
        """解析响应数据（需按实际响应结构修改）"""
        return data.get("items", [])

    def _get_next_cursor(self, data: dict) -> Optional[str]:
        """提取下一页游标（需按实际分页逻辑修改）"""
        return data.get("next_cursor")

    def _save_items(self, items: list):
        """追加写入 JSONL"""
        output_file = self.output_dir / "data.jsonl"
        with open(output_file, "a", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        self.results.extend(items)

    def _save_checkpoint(self, cursor: str):
        """保存断点"""
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump({"cursor": cursor, "count": len(self.results)}, f)

    def _load_checkpoint(self) -> Optional[str]:
        """加载断点"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"从断点恢复：cursor={data['cursor']}, 已爬取 {data['count']} 条")
                return data["cursor"]
        return None

    def close(self):
        """清理资源"""
        self.client.close()
```

### 3. 入口文件（main.py）

```python
"""pc 项目入口"""

import os
import logging
from dotenv import load_dotenv
from src.core.crawler import Crawler

# 加载 .env 凭据
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("crawler.log", encoding="utf-8"),
    ]
)


def main():
    crawler = Crawler(output_dir="output")
    try:
        crawler.run()
    finally:
        crawler.close()


if __name__ == "__main__":
    main()
```

### 4. 输出格式（output/data.jsonl）

```jsonl
{"id": "12345", "title": "示例标题", "content": "正文内容...", "created_at": "2026-01-01T00:00:00Z"}
{"id": "12346", "title": "另一条数据", "content": "更多内容...", "created_at": "2026-01-02T00:00:00Z"}
```

### 5. 最小可运行自检（examples/smoke_test.py）

```bash
python examples/smoke_test.py
```

预期输出：

```text
SMOKE PASS: 写入 4 条数据，分页与重试逻辑验证通过
```

## 交付物检查清单

Agent 在交付前核对：

- [ ] 使用 `curl_cffi`，未使用裸 `requests`
- [ ] 限速 2-5s + 抖动
- [ ] 断点续跑功能可用
- [ ] 输出为 JSONL 格式
- [ ] 冒烟测试通过（实际跑了 2-3 页真实数据）
- [ ] CI 门禁通过：`python <skill目录>/scripts/ci_gate.py .`
- [ ] 凭据在 `.env` 中，有 `.env.example`，`.env` 已加入 `.gitignore`
- [ ] 根目录无临时文件，`tmp/` 已加入 `.gitignore`
- [ ] 异常处理完善（403 停止、429 退避、空数据检测）
- [ ] nx 参数有对应文档（如果有的话）
