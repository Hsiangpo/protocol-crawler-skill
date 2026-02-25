# {param} 参数 nx 文档模板

> **使用说明**：复制此模板到 `js/docs/{param}.md`，将 `{param}` 替换为实际参数名

---

## 基本信息

| 属性     | 值                                   |
| -------- | ------------------------------------ |
| 参数名   | `{param}`                            |
| 用途     | 请求qm / 设备zw / token / ...        |
| 所在请求 | `POST /api/xxx`                      |
| 请求位置 | Header / Query / Body / Cookie       |
| 必需     | 是 / 否                              |
| 生成时机 | 页面加载时 / 每次请求时 / 首次访问时 |
| 有效期   | 单次 / N秒 / 永久                    |
| nx 难度  | 低 / 中 / 高                         |
| 完成日期 | YYYY-MM-DD                           |

---

## 参数结构

描述参数的格式（如 Base64、JSON、加密字符串、HEX 等）

### 原始值示例

```
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 解码/解析后结构

```json
{
  "timestamp": 1707200000,
  "device_id": "xxx-xxx-xxx",
  "qm": "abc123...",
  "version": "1.0"
}
```

### 字段说明

| 字段        | 类型   | 说明         |
| ----------- | ------ | ------------ |
| `timestamp` | number | 毫秒级时间戳 |
| `device_id` | string | 设备唯一标识 |
| `qm`        | string | 数据qm       |
| `version`   | string | 版本号       |

---

## nx 链路（调用链追踪）

### 完整调用链（从下往上追踪）

```
最终参数: {param}
         ↑
    ┌────┴────┐
    │ encode() │  ← Base64/Hex 编码
    └────┬────┘
         ↑
    ┌────┴────────┐
    │ encrypt()   │  ← 加密函数
    └────┬────────┘
         ↑
    ┌────┴────────────┐
    │ generateSign()  │  ← qm 生成
    └────┬────────────┘
         ↑
    ┌────┴─────────────┐
    │ buildPayload()   │  ← 构建待qm数据
    └────┬─────────────┘
         ↑
    ┌────┴────────────────┐
    │ collectDeviceInfo() │  ← 设备信息收集
    └────┬────────────────┘
         ↑
    ┌────┴─────────────┐
    │ getFingerprint() │  ← zw 获取
    └──────────────────┘
```

### 关键函数定位

| 序号 | 函数名              | 文件位置          | 行号  | 作用         |
| ---- | ------------------- | ----------------- | ----- | ------------ |
| 1    | `encryptParams`     | `app.xxxxx.js`    | 12345 | 最终加密入口 |
| 2    | `generateSign`      | `app.xxxxx.js`    | 11234 | qm 生成      |
| 3    | `buildPayload`      | `common.xxxxx.js` | 5678  | 构建载荷     |
| 4    | `collectDeviceInfo` | `utils.xxxxx.js`  | 890   | 设备信息     |
| 5    | `getFingerprint`    | `fp.xxxxx.js`     | 123   | zw 获取      |

### 断点定位技巧

如何找到入口：

1. 全局搜索参数名 `{param}`
2. XHR 断点拦截请求
3. 调用栈回溯

---

## 详细分析

### 1. 入口函数

**位置**: `app.xxxxx.js:12345`

```javascript
// 原始代码（可能经过 hx）
function _0x1234(data) {
  var _0x5678 = _0xabcd(data);
  return _0xef01(_0x5678);
}
```

**hy 后**:

```javascript
function encryptParams(data) {
  var sign = generateSign(data);
  return base64Encode(sign);
}
```

**分析**：

- 接收原始请求数据
- 调用 `generateSign` 生成qm
- 结果 Base64 编码后返回

---

### 2. qm 生成函数

**位置**: `app.xxxxx.js:11234`

```javascript
// hy 后
function generateSign(payload) {
  var timestamp = Date.now();
  var str = JSON.stringify(payload) + timestamp + SECRET_KEY;
  return md5(str);
}
```

**分析**：

- 序列化 payload 为 JSON 字符串
- 拼接时间戳和密钥
- MD5 计算qm

**关键点**：

- 时间戳精度：毫秒
- 密钥来源：硬编码 / 动态获取

---

### 3. 依赖的环境变量/常量

| 变量名                | 值/来源       | 获取方式       | 说明               |
| --------------------- | ------------- | -------------- | ------------------ |
| `SECRET_KEY`          | `"abc123xxx"` | 硬编码         | JS 中直接搜索      |
| `window.deviceId`     | 动态生成      | `localStorage` | 首次访问生成并存储 |
| `navigator.userAgent` | 浏览器 UA     | 环境变量       | 需要补环境         |
| `screen.width`        | 屏幕宽度      | 环境变量       | 需要补环境         |

### 4. 加密算法识别

| 算法   | 特征        | 确认方法        |
| ------ | ----------- | --------------- |
| MD5    | 32 位 HEX   | 对比输出长度    |
| SHA256 | 64 位 HEX   | 对比输出长度    |
| AES    | Base64 输出 | 查找 `CryptoJS` |
| 自定义 | -           | 详细分析逻辑    |

---

## 复刻实现

### Python 实现

```python
# js/dist/{site}_{param}.py
import hashlib
import time
import base64
import json

SECRET_KEY = "abc123xxx"

def generate_param(data: dict, device_id: str) -> str:
    """
    生成 {param} 参数

    Args:
        data: 请求数据
        device_id: 设备 ID

    Returns:
        str: 加密后的参数值
    """
    timestamp = str(int(time.time() * 1000))
    payload = json.dumps(data, separators=(',', ':')) + timestamp + SECRET_KEY
    qm = hashlib.md5(payload.encode()).hexdigest()
    return base64.b64encode(qm.encode()).decode()

# 使用示例
if __name__ == "__main__":
    result = generate_param({"user_id": "123"}, "device-001")
    print(f"生成结果: {result}")
```

### JavaScript 实现（Node.js）

```javascript
// js/dist/{site}_{param}.js
const crypto = require("crypto");

const SECRET_KEY = "abc123xxx";

/**
 * 生成 {param} 参数
 * @param {Object} data - 请求数据
 * @param {string} deviceId - 设备 ID
 * @returns {string} 加密后的参数值
 */
function generateParam(data, deviceId) {
  const timestamp = Date.now().toString();
  const payload = JSON.stringify(data) + timestamp + SECRET_KEY;
  const qm = crypto.createHash("md5").update(payload).digest("hex");
  return Buffer.from(qm).toString("base64");
}

module.exports = { generateParam };

// 测试
if (require.main === module) {
  const result = generateParam({ user_id: "123" }, "device-001");
  console.log("生成结果:", result);
}
```

### execjs 调用方式

```python
import execjs

# 加载 JS 文件
with open("js/dist/{site}_{param}.js", "r", encoding="utf-8") as f:
    js_code = f.read()

ctx = execjs.compile(js_code)
result = ctx.call("generateParam", {"user_id": "123"}, "device-001")
print(f"结果: {result}")
```

---

## 测试验证

### 测试用例

| 编号 | 输入数据   | 时间戳        | 预期输出    | 实际输出    | 结果 |
| ---- | ---------- | ------------- | ----------- | ----------- | ---- |
| 1    | `{"id":1}` | 1707200000000 | `abc123...` | `abc123...` | ✅   |
| 2    | `{"id":2}` | 1707200001000 | `def456...` | `def456...` | ✅   |
| 3    | `空对象`   | -             | `xxx...`    | `xxx...`    | ✅   |
| 4    | `特殊字符` | -             | `yyy...`    | `yyy...`    | ✅   |

### 验证方法

1. **浏览器对比**：
   - 在目标站点控制台执行原函数
   - 获取正确输出值
   - 对比复刻结果

2. **请求验证**：
   - 使用复刻参数发起实际请求
   - 确认请求成功（200 + 正确数据）

3. **边界测试**：
   - 空数据
   - 特殊字符
   - 超长数据

---

## 常见问题与解决

### 问题 1：时间戳不匹配

**现象**：复刻结果与浏览器不一致

**原因**：时间戳精度不同（秒 vs 毫秒）

**解决**：

```python
# 毫秒
timestamp = int(time.time() * 1000)
# 秒
timestamp = int(time.time())
```

### 问题 2：JSON 序列化差异

**现象**：qm 不一致

**原因**：Python 和 JS 的 JSON 序列化格式不同

**解决**：

```python
# 使用最紧凑格式，无空格
json.dumps(data, separators=(',', ':'), sort_keys=True)
```

### 问题 3：编码问题

**现象**：中文内容 qm 不一致

**解决**：统一使用 UTF-8 编码

---

## 注意事项

- [ ] 确认时间戳精度（毫秒/秒）
- [ ] 确认 JSON 序列化格式
- [ ] 确认字符编码（UTF-8）
- [ ] 测试特殊字符处理
- [ ] 测试空值/null 处理
- [ ] 确认密钥是否会变化
- [ ] 确认是否有时效性检查

---

## 参考资料

| 类型         | 路径                                     |
| ------------ | ---------------------------------------- |
| 原始 JS 分析 | `js/analysis/{site}_{param}_analysis.js` |
| 可执行文件   | `js/dist/{site}_{param}.js`              |
| Python 实现  | `js/dist/{site}_{param}.py`              |
| 测试文件     | `js/tests/test_{param}.py`               |
| 测试用例     | `js/tests/test_cases_{param}.json`       |

---

## 更新记录

| 日期       | 更新内容           | 作者 |
| ---------- | ------------------ | ---- |
| YYYY-MM-DD | 初始版本           | -    |
| YYYY-MM-DD | 修复时间戳精度问题 | -    |
