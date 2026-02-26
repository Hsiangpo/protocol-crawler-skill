# pc 工程与交付规范

> 快速跳转：按需查阅，不需要通读
>
> | 场景                  | 跳转章节                             |
> | --------------------- | ------------------------------------ |
> | 初始化项目结构        | **一、项目目录结构规范**             |
> | 写代码 / 代码审查     | **二、编码规范**                     |
> | 写测试                | **三、测试规范**                     |
> | 调试保存文件          | **四、debug 目录规范**               |
> | 数据输出格式          | **五、输出规范**                     |
> | nx 完成写文档         | **六、JS nx 规范 + nx 参数文档模板** |
> | Git 提交 / .gitignore | **七、Git 规范**                     |
> | 日志 / 运行摘要       | **八、日志与可观测性**               |

## 一、项目目录结构规范

```
project/
├── docs/                          # 文档目录
│   ├── PRD.md                     # 需求文档
│   ├── TECH.md                    # 关键技术方案（确认解决后再写）
│   ├── INTERFACE.md               # 接口文档（如有前后端）
│   └── update.md                  # 版本更新日志
│
├── src/                           # 主程序源码（每文件 ≤1000 行，每函数 ≤200 行）
│   ├── core/                      # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── crawler.py             # 主 pc 类
│   │   ├── client.py              # HTTP 客户端封装
│   │   └── parser.py              # 响应解析器
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic / dataclass 定义
│   ├── utils/                     # 工具函数
│   │   ├── __init__.py
│   │   ├── checkpoint.py          # 断点续跑
│   │   ├── rate_limiter.py        # 限速器
│   │   └── logger.py              # 日志配置
│   └── config.py                  # 配置管理
│
├── js/                            # JS nx 相关（仅 pc 需要 nx 时使用）
│   ├── docs/                      # ⚠️ 必须：nx 完成后的参数文档
│   │   ├── w.md                   # w 参数 nx 文档
│   │   ├── sign.md                # sign 参数 nx 文档
│   │   └── {param}.md             # 每个参数单独一个文档
│   ├── analysis/                  # nx 分析文件
│   │   ├── {site}_sign.js         # qm 函数分析
│   │   └── {site}_encrypt.js      # 加密函数分析
│   ├── dist/                      # 复刻/补环境后的可执行 JS
│   │   └── {site}_sign.js         # 可直接 execjs 调用
│   └── tests/                     # JS nx 测试
│       ├── test_sign.py           # Python 侧测试
│       └── test_sign.js           # Node 侧测试
│
├── tests/                         # 系统测试（遵循 test-cases skill 规范）
│   ├── conftest.py                # pytest 配置
│   ├── test_crawler.py            # pc 核心功能测试
│   ├── test_parser.py             # 解析器测试
│   ├── test_checkpoint.py         # 断点续跑测试
│   └── {feature}-test-cases.md    # 测试用例文档（test-cases skill 格式）
│
├── debug/                         # 调试目录（git 忽略）— 人工排查用
│   └── {timestamp}/               # 按时间戳分目录
│       ├── logs/                  # 调试日志
│       │   └── {timestamp}.log
│       ├── images/                # 截图/yzm 图片
│       │   └── screenshot_001.png
│       ├── responses/             # 原始响应保存
│       │   └── response_001.json
│       └── notes.md               # 调试笔记
│
├── tmp/                           # 运行时临时缓存（git 忽略）— 程序自动产生
│   ├── responses/                 # 自动保存的异常响应（空数据/蜜罐检测）
│   ├── screenshots/               # DevTools 自动截图
│   └── analysis/                  # 分析中间产物
│
├── output/                        # 输出目录
│   ├── progress.json              # 断点进度文件
│   ├── data.jsonl                 # 输出数据（JSONL 格式）
│   └── {timestamp}/               # 多次运行时按时间戳存储
│       ├── data.jsonl
│       └── summary.json           # 运行摘要
│
├── .env                           # 凭据文件（git 忽略）
├── .env.example                   # 凭据模板（提交到 git）
├── .gitignore                     # Git 忽略规则
├── requirements.txt               # Python 依赖
├── pyproject.toml                 # 项目配置（可选）
└── README.md                      # 项目说明
```

### 目录说明

| 目录      | 说明        | 规则                                                |
| --------- | ----------- | --------------------------------------------------- |
| `src/`    | 主程序源码  | 每文件 ≤1000 行，每函数 ≤200 行                     |
| `js/`     | nx 相关文件 | 分析放 `analysis/`，复刻放 `dist/`，测试放 `tests/` |
| `tests/`  | 系统测试    | 遵循 test-cases skill 规范                          |
| `debug/`  | 调试文件    | 人工排查用，按时间戳分目录，添加到 `.gitignore`     |
| `tmp/`    | 运行时缓存  | 程序自动产生（异常响应/截图），添加到 `.gitignore`  |
| `output/` | 输出数据    | 断点进度、JSONL 数据、运行摘要                      |
| `docs/`   | 项目文档    | PRD、TECH、INTERFACE、update                        |

---

## 二、编码规范

| 规则       | 要求                              |
| ---------- | --------------------------------- |
| 文件编码   | UTF-8                             |
| 注释语言   | 中文，禁止人称（如"帮你改了..."） |
| 单文件行数 | **≤1000 行**                      |
| 单函数行数 | **≤200 行**                       |
| 文件命名   | 禁止版本号后缀（如 `_v2`、`_v3`） |
| 同功能文件 | 只保留一份，删除废弃代码          |

### 代码清理规范

- 当方法 A 完全行不通，切换到方法 B 时，**必须删除方法 A 的代码和文件**
- 禁止保留废弃代码作为"回退方案"
- 同功能只保留当前可用的一份代码

---

## 三、测试规范

### 测试文件结构

```
tests/
├── conftest.py              # pytest 配置
├── test_{模块名}.py          # 模块测试
├── test_integration.py      # 集成测试（可选）
└── {feature}-test-cases.md  # 测试用例文档（test-cases skill 格式）
```

### 测试编写规则

| 规则     | 说明                       |
| -------- | -------------------------- |
| 文件命名 | `test_{模块名}.py`         |
| 函数命名 | `test_{功能描述}()`        |
| 单一职责 | 每个测试函数只测一个功能点 |
| 用例覆盖 | 包含正常用例和异常用例     |
| 断言验证 | 使用 assert 语句验证结果   |

> **若已安装 Superpowers**：编码遵循 `test-driven-development` skill 的 RED-GREEN-REFACTOR 流程。
> **若未安装**：按上述基本规则编写测试即可。

---

## 四、debug 目录规范

用于存放调试过程中的临时文件，**必须添加到 `.gitignore`**。

```
debug/
└── 2026-02-06_120000/           # 时间戳格式: YYYY-MM-DD_HHMMSS
    ├── logs/
    │   ├── debug.log            # 详细调试日志
    │   └── requests.log         # 请求/响应日志
    ├── images/
    │   ├── yzm_001.png          # yzm 截图
    │   └── screenshot_001.png   # 页面截图
    ├── responses/
    │   ├── api_response_001.json
    │   └── html_response_001.html
    └── notes.md                 # 调试笔记
```

### 使用规则

| 规则       | 说明                                |
| ---------- | ----------------------------------- |
| 时间戳目录 | 每次调试会话创建新目录              |
| 分类存储   | logs、images、responses 分开存放    |
| Git 忽略   | 整个 `debug/` 目录加入 `.gitignore` |
| 及时清理   | 问题解决后删除对应时间戳目录        |

---

## 五、output 目录规范

用于存放 pc 输出的数据和进度。

```
output/
├── progress.json            # 断点进度文件（原子写入）
├── data.jsonl               # 主输出数据（JSONL 格式）
├── errors.jsonl             # 错误记录（可选）
└── 2026-02-06_120000/       # 多次运行按时间戳分目录
    ├── data.jsonl
    ├── errors.jsonl
    └── summary.json         # 运行摘要
```

### 输出格式

| 格式  | 适用场景   | 说明                        |
| ----- | ---------- | --------------------------- |
| JSONL | 主数据输出 | 每行一条 JSON，支持流式写入 |
| JSON  | 进度/摘要  | 结构化配置或摘要信息        |
| CSV   | 表格数据   | 需要 Excel 打开时使用       |

### 断点进度结构

```json
{
  "version": 1,
  "run_id": "2026-02-06_120000",
  "tasks": {
    "task_id": {
      "cursor": "end_cursor_value",
      "page": 12,
      "saved": 345,
      "has_next": true,
      "completed": false,
      "updated_at": "2026-02-06T12:00:00Z"
    }
  }
}
```

---

## 六、js/ 目录规范（nx 专用）

仅在 pc 需要 nx hy qm/加密时使用。

```
js/
├── docs/                        # ⚠️ 必须：nx 完成后的参数文档
│   ├── w.md                     # w 参数 nx 文档
│   ├── sign.md                  # sign 参数 nx 文档
│   └── {param}.md               # 每个参数单独一个文档
│
├── analysis/                    # nx 分析（解读源站 JS）
│   ├── {site}_sign_analysis.js  # qm 函数分析
│   ├── {site}_encrypt_notes.md  # 加密逻辑笔记
│   └── ast_dump.json            # AST 分析结果
│
├── dist/                        # 复刻后的可执行 JS
│   ├── {site}_sign.js           # 可 execjs/node 调用
│   └── {site}_token.js          # Token 生成
│
└── tests/                       # nx 测试
    ├── test_sign.py             # Python 侧调用测试
    ├── test_sign.js             # Node 侧单元测试
    └── test_cases.json          # 测试用例数据
```

### 命名规则

| 规则       | 说明                                        |
| ---------- | ------------------------------------------- |
| 文件名前缀 | 以站点名为前缀：`{site}_xxx.js`             |
| 分析文件   | 后缀 `_analysis.js` 或 `_notes.md`          |
| 可执行文件 | 放 `dist/` 目录                             |
| 参数文档   | 放 `docs/` 目录，以参数名命名：`{param}.md` |

### ⚠️ 参数 nx 文档规范（强制）

**每完成一个加密参数的 nx，必须在 `js/docs/` 下创建对应的 `{param}.md` 文档。**

完整的模板请严格参考：`templates/nx-param-doc.md`。

---

## 七、Git 与文档规范

### update.md 格式

```markdown
## v1.0.2 (2026-02-06)

### 新增

- 添加断点续跑功能

### 修改

- 优化请求频率控制逻辑

### 修复

- 修复分页参数计算错误
```

### TECH.md 编写规则

| 规则 | 说明                                   |
| ---- | -------------------------------------- |
| 时机 | 只写**关键破局技术**，确认解决后才写入 |
| 内容 | 接口 nx 方法、qm 算法 hy、fk pj 方案   |
| 格式 | 问题 → 分析 → 解决方案 → 验证结果      |

### .gitignore 模板

```
# 调试目录
debug/

# 输出目录（可选，看是否需要版本控制）
output/

# Python
__pycache__/
*.pyc
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp

# 系统文件
.DS_Store
Thumbs.db

# 敏感信息
.env
*.key
credentials.json
```

---

## 八、日志与可观测性

### 日志字段

| 字段          | 说明             |
| ------------- | ---------------- |
| `ts`          | UTC 时间戳       |
| `run_id`      | 单次运行唯一标识 |
| `task`        | 目标任务         |
| `endpoint`    | 请求地址         |
| `status`      | HTTP 状态码      |
| `duration_ms` | 请求耗时         |
| `retry`       | 当前重试次数     |
| `cursor/page` | 分页状态         |
| `items_count` | 本页条数         |
| `error_type`  | 错误分类         |

### 关键指标

- 成功率（200/总请求）
- 平均响应耗时 / P95
- 429/403/5xx 比例
- 每页条数分布
- 断点续跑次数

### 运行摘要

每次运行结束输出 summary.json：

```json
{
  "run_id": "2026-02-06_120000",
  "started_at": "2026-02-06T12:00:00Z",
  "finished_at": "2026-02-06T14:30:00Z",
  "total_items": 5678,
  "deduplicated": 5432,
  "failed": 12,
  "error_distribution": {
    "timeout": 5,
    "429": 3,
    "parse_error": 4
  },
  "last_cursor": "abc123",
  "completed": true
}
```
