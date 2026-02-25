# 数据校验与漂移检测

## 目标

保证输出数据的结构一致性、字段完整性、类型正确性，并及时发现 schema 漂移。

---

## 一、数据校验维度

| 维度           | 检查内容                       |
| -------------- | ------------------------------ |
| **字段完整性** | 必填字段是否缺失               |
| **类型一致性** | int/bool/string 统一           |
| **逻辑一致性** | 时间戳与 ID 对应、分页排序稳定 |
| **重复检测**   | 同一 ID 只保留一条             |

---

## 二、Schema 漂移是什么

Schema 漂移是指接口返回字段或结构发生变化，例如：

- 字段新增
- 字段删除
- 层级调整
- 类型变化

### 是否常见？

任何网站都可能发生，尤其是：

- 持续迭代中的产品
- A/B 测试环境
- 多版本共存的场景

---

## 三、漂移检测策略

### 基线快照

保存关键接口的响应结构（字段路径 + 类型）作为基线。

### 运行时校验

抽样检查字段完整性与类型一致性。

### 差异检测

- 字段缺失 → 告警
- 字段新增 → 记录

---

## 四、漂移处理策略

| 漂移程度 | 表现                  | 处理策略               |
| -------- | --------------------- | ---------------------- |
| **轻微** | 新增字段              | 允许扩展并记录         |
| **中等** | 字段缺失              | 降级处理并提示用户     |
| **严重** | 结构重排/关键字段消失 | **停止并重新对齐接口** |

---

## 五、采样比对

- 每 N 页抽样对比 UI 与接口数据
- 比对数量与关键字段（id/time/url）
- 发现偏差时暂停并复核请求模板

---

## 六、回归检查流程

1. 复现请求并保存最新响应结构
2. 对比基线差异
3. 更新解析逻辑与数据验证规则
4. 验证输出是否符合 PRD

---

## 七、落盘规范

| 格式         | 用途                               |
| ------------ | ---------------------------------- |
| **JSONL**    | "原子记录"，便于流式写入和断点续跑 |
| **CSV**      | 便于查看的副本                     |
| **原始响应** | 可选，用于回溯问题                 |

---

## 八、实现建议

```python
from dataclasses import dataclass
from typing import Any, Dict, Set

@dataclass
class SchemaValidator:
    baseline: Dict[str, type]  # 字段路径 -> 类型

    def validate(self, data: Dict[str, Any]) -> list[str]:
        errors = []
        for field, expected_type in self.baseline.items():
            value = self._get_nested(data, field)
            if value is None:
                errors.append(f"Missing field: {field}")
            elif not isinstance(value, expected_type):
                errors.append(f"Type mismatch: {field} (expected {expected_type}, got {type(value)})")
        return errors

    def detect_drift(self, data: Dict[str, Any]) -> tuple[Set[str], Set[str]]:
        current_fields = set(self._flatten_keys(data))
        baseline_fields = set(self.baseline.keys())
        new_fields = current_fields - baseline_fields
        missing_fields = baseline_fields - current_fields
        return new_fields, missing_fields

    def _get_nested(self, data: dict, path: str) -> Any:
        keys = path.split('.')
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                return None
        return data

    def _flatten_keys(self, data: dict, prefix: str = '') -> list[str]:
        keys = []
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.append(full_key)
            if isinstance(v, dict):
                keys.extend(self._flatten_keys(v, full_key))
        return keys
```
