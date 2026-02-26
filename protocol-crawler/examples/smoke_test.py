#!/usr/bin/env python3
"""pc 示例最小自检脚本。"""

from __future__ import annotations

import json
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class MockResponse:
    """模拟 HTTP 响应对象。"""

    status_code: int
    payload: Dict[str, Any]
    headers: Dict[str, str]

    def json(self) -> Dict[str, Any]:
        return self.payload


class MockClient:
    """模拟客户端：第一页成功，第二页先 429 再成功，第三页成功结束。"""

    def __init__(self) -> None:
        self.calls = 0
        self.cursor_attempts: Dict[Optional[str], int] = {}

    def get(self, _url: str, params: Optional[Dict[str, Any]] = None, **_kwargs: Any) -> MockResponse:
        self.calls += 1
        cursor = (params or {}).get("cursor")
        self.cursor_attempts[cursor] = self.cursor_attempts.get(cursor, 0) + 1

        if cursor is None:
            return MockResponse(
                status_code=200,
                payload={
                    "items": [{"id": 1}, {"id": 2}],
                    "next_cursor": "c1",
                },
                headers={},
            )

        if cursor == "c1" and self.cursor_attempts[cursor] == 1:
            return MockResponse(
                status_code=429,
                payload={},
                headers={"Retry-After": "1"},
            )

        if cursor == "c1":
            return MockResponse(
                status_code=200,
                payload={
                    "items": [{"id": 3}],
                    "next_cursor": "c2",
                },
                headers={},
            )

        if cursor == "c2":
            return MockResponse(
                status_code=200,
                payload={
                    "items": [{"id": 4}],
                    "next_cursor": None,
                },
                headers={},
            )

        return MockResponse(status_code=404, payload={}, headers={})

    def close(self) -> None:
        """保持与真实客户端接口一致。"""


class DemoCrawler:
    """最小可运行爬虫，覆盖分页、429 重试、输出与断点写入。"""

    def __init__(self, output_dir: Path, checkpoint_file: Path) -> None:
        self.client = MockClient()
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = checkpoint_file
        self.results = []
        self.max_retries = 3

    def run(self) -> None:
        cursor: Optional[str] = None
        while True:
            data = self._fetch_page(cursor)
            if data is None:
                break

            items = data.get("items", [])
            self._save_items(items)

            cursor = data.get("next_cursor")
            if cursor is None:
                break
            self._save_checkpoint(cursor)

    def _fetch_page(self, cursor: Optional[str]) -> Optional[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": 20}
        if cursor:
            params["cursor"] = cursor

        resp = self.client.get("https://api.example.com/data", params=params)
        if resp.status_code == 200:
            return resp.json()

        if resp.status_code == 429:
            for attempt in range(1, self.max_retries + 1):
                retry_after = int(resp.headers.get("Retry-After", "1")) * attempt
                time.sleep(retry_after * 0.01)
                resp = self.client.get("https://api.example.com/data", params=params)
                if resp.status_code != 429:
                    break
            if resp.status_code == 429:
                return None
            return resp.json()

        return None

    def _save_items(self, items: list[Dict[str, Any]]) -> None:
        output_file = self.output_dir / "data.jsonl"
        with output_file.open("a", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        self.results.extend(items)

    def _save_checkpoint(self, cursor: str) -> None:
        with self.checkpoint_file.open("w", encoding="utf-8") as f:
            json.dump({"cursor": cursor, "count": len(self.results)}, f, ensure_ascii=False)


def assert_smoke_result(output_dir: Path, checkpoint_file: Path) -> None:
    """校验最小自检结果。"""
    data_file = output_dir / "data.jsonl"
    if not data_file.exists():
        raise RuntimeError("缺少 data.jsonl 输出文件")

    lines = [line.strip() for line in data_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 4:
        raise RuntimeError(f"输出条数异常，期望 4 条，实际 {len(lines)} 条")

    if not checkpoint_file.exists():
        raise RuntimeError("缺少 checkpoint.json 文件")

    checkpoint = json.loads(checkpoint_file.read_text(encoding="utf-8"))
    if checkpoint.get("cursor") != "c2":
        raise RuntimeError(f"断点游标异常，期望 c2，实际 {checkpoint.get('cursor')}")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="pc-smoke-") as tmp_dir:
        root = Path(tmp_dir)
        output_dir = root / "output"
        checkpoint_file = root / "checkpoint.json"

        crawler = DemoCrawler(output_dir=output_dir, checkpoint_file=checkpoint_file)
        crawler.run()
        crawler.client.close()
        assert_smoke_result(output_dir, checkpoint_file)

    print("SMOKE PASS: 写入 4 条数据，分页与重试逻辑验证通过")


if __name__ == "__main__":
    main()
